# XRP Transaction Tracker

## Overview
This is an open-source Python tool for tracing and visualizing XRP transaction paths using the XRPSCAN API. It supports recursive tracing, graph visualization with NetworkX and Matplotlib, alerts for known exchanges/mixers, basic heuristics, and tagging. A Streamlit web UI provides an interactive interface. Built for educational and investigative purposes (e.g., tracking transaction flows), but always verify results and respect API terms.

**Version: MVP with UI (Milestone M4)** - Includes CLI tracing, graph gen, alerts, heuristics, tagging from JSON, and interactive Streamlit app.

## Features
- Trace transactions from an account or TX ID with depth limit.
- Date filtering (optional).
- Detect suspected mixers via heuristics (e.g., high incoming txns).
- Alerts for known exchanges and tagged addresses.
- Graph visualization with colored nodes (exchanges red, mixers orange, tagged purple) and weighted edges.
- Interactive Streamlit UI for inputs and results display.
- Unit tests with pytest.

## Setup
1. Clone the repo: `git clone https://github.com/yourusername/xrp-transaction-tracker.git` (replace with actual URL).
2. Install dependencies: `pip3 install -r requirements.txt` (includes numpy, requests, networkx, matplotlib, pytest, streamlit).
3. (Optional) Add known tags to `data/known_tags.json` (format: {"address": {"label": "Name", "type": "exchange/mixer", "notes": "Details"}}).

## Usage
### CLI
Run `python3 xrp_track.py --account <ADDRESS> --depth 3 --start 2023-01-01T00:00:00 --end 2023-12-31T23:59:59` or `--tx_id <TX_ID>`.
- Generates `xrp_transaction_graph.png` and prints alerts.
- Use `--test_mode` for example data.

### Web UI
Run `streamlit run app.py`.
- Enter account/TX ID, dates, depth.
- Click 'Trace Transactions' to view graph and alerts in browser.

## Testing
Run `PYTHONPATH=. pytest tests/` to execute unit tests for key functions.

## Privacy Note
This tool does not store or share personal data. Any user-provided addresses or extracted info (e.g., from private PDFs/Excels) should not be committed to the public repo. Sensitive files are ignored via `.gitignore`. Always anonymize data before sharing.

## Limitations
- Relies on public XRPSCAN API (rate limits apply; script handles retries).
- Heuristics are basic; not foolproof for mixer/clustering detection.
- Graphs may need tuning for large traces.

## Contributing
See PLANNING.md for milestones. Follow Git rules: Use branches, commit format like `[CORE] Add feature`. No personal data in PRs.

## License
MIT (see LICENSE).

## Forensic Use
This tool is designed for investigators to trace XRP paths, identify exchanges for KYC/freezing, and generate PDF reports. Access via web URL with login—no install needed.
### Quick-Start for Investigators
1. Visit [APP URL].
2. Login with provided credentials.
3. Enter address/TX ID and trace.
4. Export PDF for case files.

 
