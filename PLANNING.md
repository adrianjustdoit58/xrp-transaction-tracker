# XRP Transaction Tracker Planning

## Project Scope
Build an open-source Python tool to trace and visualize XRP transaction paths (e.g., for theft investigations), starting from a wallet address. Focus on automation via XRPSCAN API, with alerts for known exchanges/mixers. Expandable to clustering/tagging inspired by Bitcoin tools, but adapted for XRP's account model. MVP: CLI with tracing/graphing/alerts. Future: Web UI, shared tagging DB.

## Architecture
- Core: Python scripts for API fetching, recursion, graphing (using requests, networkx, matplotlib).
- Data: Local JSON for known addresses/tags; optional SQLite for caching/traces.
- Extensions: Heuristics (e.g., pattern detection for mixers); user-tagging system.
- Constraints: Public API only (rate limits); ethical data handling; no real-time (historical tracing).

## File Layout
- `xrp_track.py`: Main script.
- `utils/`: Helpers (e.g., api_utils.py).
- `data/`: JSON files (e.g., known_addresses.json).
- `tests/`: Pytest files.
- `docs/`: Additional guides if needed.
- `PLANNING.md`, `TASK.md`, `README.md`.

## Milestones
- M1 (MVP): Refine tracing/visualization/alerts (current state).
- M2: Add basic tagging/clustering (e.g., load from JSON; simple patterns like multi-hop detection).
- M3: Testing & Reliability (add pytest suite).
- M4: UI Extensions (Streamlit web app for interactive graphs).
- M5: Community Features (shared DB for tags, if pursued). 

## Project Status
All milestones (M1-M5) completed as of 2024-10-12. Project is now ready for forensic use with CLI, UI, testing, tagging DB, and planned enhancements for police accessibility. 