import streamlit as st
import sys
import os
import copy

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from xrp_track import trace_transactions, build_graph, visualize_graph, get_transaction
import matplotlib.pyplot as plt  # Needed for graph
import datetime  # For parsing dates

import io
from PIL import Image
from utils.db_utils import add_or_update_tag  # For tag management
import yaml
from streamlit_authenticator import Authenticate
import reportlab
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Login setup
# Direct access to st.secrets
# Make mutable copies of secrets
credentials = {
    "usernames": {
        username: {
            "email": user["email"],
            "failed_login_attempts": user.get("failed_login_attempts", 0),
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "logged_in": user.get("logged_in", False),
            "password": user["password"],
            "roles": user.get("roles", [])
        } for username, user in st.secrets["credentials"]["usernames"].items()
    }
}
cookie = {
    "expiry_days": st.secrets["cookie"]["expiry_days"],
    "key": st.secrets["cookie"]["key"],
    "name": st.secrets["cookie"]["name"]
}
pre_authorized = {
    "emails": list(st.secrets["pre-authorized"]["emails"])
}
authenticator = Authenticate(
    credentials,
    cookie['name'],
    cookie['key'],
    cookie['expiry_days'],
    pre_authorized  # Use the copied pre_authorized
)
name, authentication_status, username = authenticator.login('Login', 'main')
if authentication_status:
    # Main UI here
    st.title('XRP Transaction Tracker')

    # Inputs
    account = st.text_input('Starting Account (optional if TX ID provided)')
    tx_id = st.text_input('Transaction ID (optional)')
    start = st.text_input('Start Date (YYYY-MM-DDTHH:MM:SS, optional)')
    end = st.text_input('End Date (YYYY-MM-DDTHH:MM:SS, optional)')
    depth = st.number_input('Max Depth', min_value=1, max_value=5, value=3)

    if st.button('Trace Transactions'):
        if not account and not tx_id:
            st.error('Please provide either an account or a transaction ID.')
        else:
            node_levels = {}
            alerts = []
            if tx_id:
                txn_data = get_transaction(tx_id)
                initial_account = txn_data.get('Account', '')
                transactions = [txn_data]
                if 'Destination' in txn_data:
                    node_levels[initial_account] = 0
                    node_levels[txn_data['Destination']] = 1
                    traced = set([initial_account])
                    start_datetime = datetime.datetime.strptime(start, '%Y-%m-%dT%H:%M:%S') if start else None
                    end_datetime = datetime.datetime.strptime(end, '%Y-%m-%dT%H:%M:%S') if end else None
                    transactions.extend(trace_transactions(txn_data['Destination'], start_datetime, end_datetime, depth=1, max_depth=depth, traced=traced, node_levels=node_levels, alerts=alerts))
            else:
                initial_account = account
                start_datetime = datetime.datetime.strptime(start, '%Y-%m-%dT%H:%M:%S') if start else None
                end_datetime = datetime.datetime.strptime(end, '%Y-%m-%dT%H:%M:%S') if end else None
                node_levels[initial_account] = 0
                transactions = trace_transactions(account, start_datetime, end_datetime, max_depth=depth, node_levels=node_levels, alerts=alerts)
            
            G = build_graph(transactions, node_levels)
            
            # Generate graph image
            fig = plt.figure(figsize=(10, 10))
            visualize_graph(G, node_levels, filename=None)  # Modify visualize to not save but use fig
            # Note: Need to adjust visualize_graph to draw on provided fig or return image
            # For now, assume it saves to 'xrp_transaction_graph.png'
            visualize_graph(G, node_levels)
            img = Image.open('xrp_transaction_graph.png')
            st.image(img, caption='Transaction Graph')
            
            if alerts:
                st.subheader('Alerts')
                for alert in alerts:
                    st.write(alert)
            else:
                st.write('No alerts detected.') 

    st.subheader('Manage Tags')
    address = st.text_input('Address to Tag')
    label = st.text_input('Label')
    tag_type = st.selectbox('Type', ['exchange', 'mixer', 'other'])
    notes = st.text_area('Notes')
    if st.button('Add/Update Tag'):
        if address and label:
            add_or_update_tag(address, label, tag_type, notes)
            st.success(f'Tag for {address} added/updated!')
        else:
            st.error('Address and Label are required.') 

    if st.button('Generate PDF Report'):
        pdf_buffer = generate_pdf_report(G, node_levels, alerts, transactions)
        st.download_button('Download PDF Report', pdf_buffer, file_name='xrp_trace_report.pdf', mime='application/pdf')
    authenticator.logout('Logout', 'sidebar')
elif authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status is None:
    st.warning('Please enter your username and password')

def generate_pdf_report(G, node_levels, alerts, transactions):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(100, 750, 'XRP Transaction Trace Report')
    # Add summary, alerts, etc.
    c.drawString(100, 700, 'Forensic Summary: Identified exchanges and mixers.')
    for i, alert in enumerate(alerts):
        c.drawString(100, 650 - i*20, alert)
    # Add graph image (save temp and draw)
    img_buf = visualize_graph(G, node_levels, filename=None)
    if img_buf:
        img = Image.open(img_buf)
        img.save('temp_graph.png')
        c.drawImage('temp_graph.png', 100, 300, width=400, height=300)
    c.save()
    buffer.seek(0)
    return buffer 