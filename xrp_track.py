import numpy as np
import requests
import networkx as nx
import matplotlib.pyplot as plt
import time
from datetime import datetime
import random
import argparse  # Add this import for command-line args
import json  # For loading tags
import io # For in-memory image buffer
from utils.db_utils import load_tags  # New: Load from SQLite
import reportlab
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Add known exchanges (expand this list based on public data; addresses are examples and should be verified)
KNOWN_EXCHANGES = {
    "rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh": "Binance",
    "r9KXXTBM4e3AQ9J1z2DdHNFFwyW1BQhtPQ": "Kraken",
    "rLHzPsX6oXkzU2qL12kHCH8G8cn5WSmpJr": "Coinbase",
    # Add more known exchange addresses here (e.g., from public lists or user's forensic data)
    # Mixer examples: "rChangeNowTemp": "ChangeNow"  # Placeholder; use real patterns if available
}

# New: Known or suspected mixers (expand with patterns or known addresses)
SUSPECTED_MIXERS = set()  # Will populate dynamically

# Load known tags (after imports)
try:
    KNOWN_TAGS = load_tags()
except Exception as e:
    print(f"Error loading tags from DB: {e}")
    KNOWN_TAGS = {}

# Function to fetch transactions for a given account with retry on rate limiting and 504 errors
def get_transactions(account, marker=None, limit=200, retries=5, timeout=10):
    url = f"https://api.xrpscan.com/api/v1/account/{account}/transactions?origin=xrp-transaction-tracker"
    params = {'marker': marker, 'limit': limit} if marker else {'limit': limit}
    attempt = 0
    while attempt < retries:
        try:
            response = requests.get(url, params=params, timeout=timeout)
            if response.status_code == 429:
                print("Rate limit hit, sleeping for 60 seconds...")
                time.sleep(60)
            else:
                response.raise_for_status()
                return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 504:
                print(f"504 error, retrying... ({attempt + 1}/{retries})")
                time.sleep(30)
                attempt += 1
            else:
                raise e
    raise Exception("Max retries exceeded")

# Recursive function to fetch all transactions for an account within a date range
def fetch_all_transactions(account, start_datetime, end_datetime, depth=1, max_depth=2, limit=200):
    transactions = []
    marker = None
    while True:
        data = get_transactions(account, marker, limit)
        for txn in data['transactions']:
            txn_date = datetime.strptime(txn['date'], '%Y-%m-%dT%H:%M:%S.%fZ')
            if (start_datetime is None or start_datetime <= txn_date) and (end_datetime is None or txn_date <= end_datetime):
                transactions.append(txn)
        if 'marker' in data and depth < max_depth:
            marker = data['marker']
        else:
            break
    return transactions

# New function for heuristic detection
def detect_heuristics(transactions, account, alerts):
    # Simple mixer detection: high number of incoming txns to this account
    incoming_count = sum(1 for txn in transactions if txn.get('Destination') == account)
    if incoming_count > 10:  # Arbitrary threshold for suspicion
        SUSPECTED_MIXERS.add(account)
        alert_msg = f"HEURISTIC ALERT: Account {account} suspected as mixer (high incoming txns: {incoming_count})"
        print(alert_msg)
        alerts.append(alert_msg)
    
    # Simple clustering note: log if multiple destinations share common sources (basic, expand later)
    destinations = set(txn.get('Destination') for txn in transactions if 'Destination' in txn)
    if len(destinations) > 5:  # Example threshold
        print(f"CLUSTER NOTE: Account {account} connects to {len(destinations)} destinations - potential cluster")

# Modify trace_transactions to check for exchanges and collect alerts
def trace_transactions(account, start_datetime, end_datetime, depth=0, max_depth=2, traced=set(), node_levels={}, alerts=[]):
    if depth > max_depth or account in traced:
        return []

    print(f"Tracing transactions for account {account} at depth {depth}")

    traced.add(account)
    transactions = fetch_all_transactions(account, start_datetime, end_datetime, depth, max_depth)
    
    detect_heuristics(transactions, account, alerts)  # Call new heuristic function
    
    all_transactions = []

    for txn in transactions:
        if 'Destination' in txn and 'Amount' in txn:  # Check if 'Destination' and 'Amount' fields exist
            destination = txn['Destination']
            tag = KNOWN_TAGS.get(destination, None)
            if tag:
                alert_msg = f"TAG ALERT: Transfer to tagged {tag['label']} ({destination}) from {account} - Notes: {tag.get('notes', '')}"
                print(alert_msg)
                alerts.append(alert_msg)
                # Override heuristic if conflict (e.g., tagged as legit but heuristic suspects mixer)
                if 'type' in tag and tag['type'] != 'mixer' and destination in SUSPECTED_MIXERS:
                    SUSPECTED_MIXERS.remove(destination)
                    alerts.append(f"TAG OVERRIDE: {destination} tagged as {tag['label']}, removing mixer suspicion")
            if destination in KNOWN_EXCHANGES:
                alert_msg = f"ALERT: Transfer of {txn['Amount']['value']} drops to known exchange {KNOWN_EXCHANGES[destination]} ({destination}) from {account}"
                print(alert_msg)
                alerts.append(alert_msg)
            if destination in SUSPECTED_MIXERS:
                alert_msg = f"ALERT: Transfer to suspected mixer {destination} from {account}"
                print(alert_msg)
                alerts.append(alert_msg)
            if destination not in traced:
                all_transactions.append(txn)
                node_levels[destination] = depth + 1
                all_transactions.extend(trace_transactions(destination, start_datetime, end_datetime, depth + 1, max_depth, traced, node_levels, alerts))

    return all_transactions

# Create a graph from transactions
def build_graph(transactions, node_levels):
    G = nx.DiGraph()
    for txn in transactions:
        source = txn['Account']
        if 'Destination' in txn and 'Amount' in txn:  # Ensure 'Destination' and 'Amount' fields exist
            destination = txn['Destination']
            amount = txn['Amount']['value']
            G.add_edge(source, destination, weight=float(amount) / 1_000_000)  # Convert from drops to XRP
            if source not in node_levels:
                node_levels[source] = 0  # Original wallet level
            # Set the subset_key attribute for each node
            G.nodes[source]['subset_key'] = node_levels[source]
            G.nodes[destination]['subset_key'] = node_levels[destination]
            # Flag if it's a known exchange or suspected mixer
            G.nodes[destination]['is_exchange'] = destination in KNOWN_EXCHANGES
            G.nodes[destination]['is_mixer'] = destination in SUSPECTED_MIXERS
            # Flag tags
            tag = KNOWN_TAGS.get(destination, None)
            if tag:
                G.nodes[destination]['tag_label'] = tag['label']
                G.nodes[destination]['is_tagged'] = True
    return G

def format_wallet_address(address):
    return f"{address[:4]}...{address[-4:]}"

# Visualize the graph
def visualize_graph(G, node_levels, scale_factor=3.0, filename="graph.png"):
    if not G.nodes:
        print("No nodes in graph, skipping visualization.")
        return None
    pos = {}
    level_nodes = {}
    max_depth = max(node_levels.values()) if node_levels else 0

    # Group nodes by levels
    for node, level in node_levels.items():
        if level not in level_nodes:
            level_nodes[level] = []
        level_nodes[level].append(node)

    # Sort nodes at each level by descending transaction amount
    for level, nodes in level_nodes.items():
        if level == 0:
            pos[nodes[0]] = (0, 0)
        else:
            nodes.sort(key=lambda node: sum([G.edges[edge]['weight'] for edge in G.in_edges(node)]), reverse=True)
            for i, node in enumerate(nodes):
                pos[node] = (level, -i)

    # Perturb node positions slightly to avoid overlapping edges
    for node in pos:
        x, y = pos[node]
        pos[node] = (x + random.uniform(-0.05, 0.05), y + random.uniform(-0.05, 0.05))

    plt.figure(figsize=(30, 30))

    color_map = []
    for node in G:
        if G.nodes[node].get('is_tagged', False):
            color_map.append('purple')  # Police-flagged tags in purple
        elif G.nodes[node].get('is_exchange', False):
            color_map.append('red')  # Highlight exchanges in red
        elif G.nodes[node].get('is_mixer', False):
            color_map.append('orange')  # Highlight suspected mixers in orange
        else:
            level = node_levels[node]
            gray_value = 1 - (level / max(node_levels.values())) * 0.8  # Shades of gray
            color_map.append((gray_value, gray_value, gray_value))

    edge_weights = [G.edges[edge]['weight'] for edge in G.edges]
    sorted_weights = sorted(edge_weights)
    if not sorted_weights:
        edge_color_map = ['#084960'] * len(G.edges)  # Default color if no weights
    else:
        quantiles = np.percentile(sorted_weights, [25, 50, 75])
        edge_color_map = []
        for edge in G.edges:
            weight = G.edges[edge]['weight']
            if weight <= quantiles[0]:
                edge_color_map.append('#084960')
            elif weight <= quantiles[1]:
                edge_color_map.append('#016E93')
            elif weight <= quantiles[2]:
                edge_color_map.append('#4897B4')
            else:
                edge_color_map.append('#B0D8E9')

    labels = {node: f"{format_wallet_address(node)} {G.nodes[node].get('tag_label', '')}" for node in G.nodes}  # Add tag to label
    nx.draw(G, pos, with_labels=True, labels=labels, node_size=200, node_color=color_map, font_size=10, font_weight='bold', edge_color=edge_color_map)
    edge_labels = {edge: f"{G.edges[edge]['weight']:,} XRP" for edge in G.edges}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    if filename:
        plt.savefig(filename)
        print(f"Graph saved as {filename}")
    else:
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        return buf
    plt.close()

# New helper function for single txn fetch
def get_transaction(tx_id, retries=5, timeout=10):
    url = f"https://api.xrpscan.com/api/v1/transaction/{tx_id}?origin=xrp-transaction-tracker"
    attempt = 0
    while attempt < retries:
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 429:
                print("Rate limit hit, sleeping for 60 seconds...")
                time.sleep(60)
            else:
                response.raise_for_status()
                return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 504:
                print(f"504 error, retrying... ({attempt + 1}/{retries})")
                time.sleep(30)
                attempt += 1
            else:
                raise e
    raise Exception("Max retries exceeded")

# Main function
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trace XRP transactions and visualize flow.")
    parser.add_argument("--account", help="Starting XRP wallet address")
    parser.add_argument("--tx_id", help="Specific transaction ID to trace from (optional; overrides account for single txn)")
    parser.add_argument("--start", help="Start date (YYYY-MM-DDTHH:MM:SS) (optional)")
    parser.add_argument("--end", help="End date (YYYY-MM-DDTHH:MM:SS) (optional)")
    parser.add_argument("--depth", type=int, default=3, help="Max recursion depth for tracing")
    parser.add_argument("--test_mode", action="store_true", help="Run in test mode with example data")
    args = parser.parse_args()

    if args.test_mode:
        print("Running in test mode with updated example data...")
        args.account = "rFSFPSFUEEH7GN2H3K6nDjCQRVchuJbwpa"  # Default for test
        args.start = "2023-07-15T00:00:00"
        args.end = "2023-07-15T23:59:59"

    if not args.account and not args.tx_id:
        parser.error("Either --account or --tx_id is required")

    start_datetime = datetime.strptime(args.start, '%Y-%m-%dT%H:%M:%S') if args.start else None
    end_datetime = datetime.strptime(args.end, '%Y-%m-%dT%H:%M:%S') if args.end else None
    max_depth = args.depth

    node_levels = {}
    alerts = []  # List to collect alerts

    if args.tx_id:
        # New: Fetch single txn and trace from there
        print(f"Tracing from transaction ID: {args.tx_id}")
        txn_data = get_transaction(args.tx_id)
        initial_account = txn_data.get('Account', '')
        # For single txn, wrap in list for consistency
        transactions = [txn_data]
        if 'Destination' in txn_data:
            node_levels[initial_account] = 0
            node_levels[txn_data['Destination']] = 1
            traced = set([initial_account])
            transactions.extend(trace_transactions(txn_data['Destination'], start_datetime, end_datetime, depth=1, max_depth=max_depth, traced=traced, node_levels=node_levels, alerts=alerts))
    else:
        initial_account = args.account
        node_levels[initial_account] = 0  # Level of the initial account
        transactions = trace_transactions(initial_account, start_datetime, end_datetime, max_depth=max_depth, node_levels=node_levels, alerts=alerts)
    
    G = build_graph(transactions, node_levels)
    visualize_graph(G, node_levels, scale_factor=3.0, filename="xrp_transaction_graph.png")  # Adjust the scale_factor to increase spacing
    generate_pdf_report_cli(transactions, alerts, "xrp_trace_report.pdf")

    # Print summary of alerts
    if alerts:
        print("\nSummary of Alerts:")
        for alert in alerts:
            print(alert)
    else:
        print("\nNo known exchanges detected in the traced path.")

def generate_pdf_report_cli(transactions, alerts, filename):
    c = canvas.Canvas(filename, pagesize=letter)
    c.drawString(100, 750, 'XRP Transaction Trace Report (CLI)')
    for i, alert in enumerate(alerts):
        c.drawString(100, 700 - i*20, alert)
    c.save()
    print(f"PDF report saved as {filename}")
