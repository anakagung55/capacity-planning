# Capacity Planning — Run & Recovery Guide

This document explains how to restart the Streamlit app, replace API keys/tokens, and recover if the server goes down. Follow these steps to bring the app back online quickly.

## Purpose

When the server is restarted or an API key / token needs replacing, this guide shows the exact commands and locations to update so the Streamlit app runs again.

## Prerequisites

- Python 3.10+ installed
- Git (optional)
- Access to the repository and ability to modify environment variables or Streamlit secrets
- A terminal (PowerShell on Windows, bash on Linux)

Files and folders referenced in this guide:

- `app.py` — main Streamlit application
- `requirements.txt` — Python dependencies
- `data/` — CSV data files used by the app
- `scripts/` — helper scripts (e.g., `extract_clockify.py`, `jira.py`)

## Quick start (Windows)

1. Open PowerShell and navigate to the project root.

2. (Optional) Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```powershell
pip install -r requirements.txt
```

4. Run the Streamlit app locally:

```powershell
streamlit run app.py
```

The app should open in your browser at http://localhost:8501 by default.

## How the token / API key is used (flow)

- The Streamlit UI in `app.py` calls helper scripts in `scripts/` to fetch external data.
- Those helper scripts typically read an API key from an environment variable or Streamlit secrets and then call external APIs (Clockify, JIRA, etc.).
- The fetched data is saved/merged into `data/` CSVs and displayed in the dashboard.

## Replacing an API key / token

Choose one of the approaches below depending on how the app reads secrets.

1) Environment variable (temporary for current session):

PowerShell (temporary, lasts for session):

```powershell
#$ replace YOUR_NEW_KEY with the new token
$env:API_KEY = "YOUR_NEW_KEY"
streamlit run app.py
```

To make the environment variable permanent for the current user (Windows), use `setx`:

```powershell
setx API_KEY "YOUR_NEW_KEY"
# Close and reopen terminals to pick up the new value
```

2) Streamlit secrets (recommended for deployed Streamlit apps):

Create or edit `.streamlit/secrets.toml` in the project root (create `.streamlit/` if missing):

```toml
API_KEY = "YOUR_NEW_KEY"
```

Then re-run the app:

```powershell
streamlit run app.py
```

Inside your code you can access secrets via `st.secrets["API_KEY"]` or via `os.environ.get('API_KEY')` depending on implementation.

3) Directly in code (least secure — only for quick testing):

Open the script that uses the key, e.g., `scripts/extract_clockify.py`, and replace the placeholder token. Commit/rollback changes as needed.

## Restarting the Streamlit app (if it's running as a foreground process)

If you started Streamlit in a terminal, stop it with Ctrl+C and start it again:

```powershell
# Stop: Ctrl+C in the running terminal
# Start again
streamlit run app.py
```

## Running the app as a background process (Windows tips)

- If you run Streamlit in a long-running PowerShell, consider running it inside a terminal multiplexer or use a Windows service wrapper (e.g., NSSM) to keep it running.
- For quick background running you can start it in a new detached PowerShell window.

## If the server is down — recovery checklist

1. Check whether the machine is reachable (RDP / SSH / remote desktop).
2. Open a terminal on the machine and check if Streamlit is running. If you launched it manually, there will be a terminal session with `streamlit run`.
3. If nothing is running, start a terminal and run `streamlit run app.py` to get real-time logs.
4. Look at the terminal logs for stack traces or authentication errors — these usually indicate expired or invalid tokens.
5. Fix the token using the methods above and restart the app.
6. Verify the dashboard loads and the CSV files in `data/` look populated.

## Troubleshooting

- Authentication errors: confirm the API key value and where the code expects it (environment vs secrets).
- Missing dependencies: re-run `pip install -r requirements.txt`.
- Data missing or empty: check `data/` CSV files and re-run the extraction scripts in `scripts/` if needed.

## Example: Replace Clockify token and re-run extraction

1. Update `API_KEY` via environment or `.streamlit/secrets.toml`.
2. Run the extraction script manually to repopulate data (example):

```powershell
# from project root
python scripts/extract_clockify.py
# then re-run the Streamlit app
streamlit run app.py
```

## Notes & Safety

- Never commit real API tokens into git. Use environment variables or `secrets.toml`.
- Keep a backup of important data files before running destructive scripts.

---

If you want, I can also:

- add a `.streamlit/secrets.example.toml` template,
- add a small `scripts/run_local.ps1` helper that sets env vars and runs the app,
- or update the app to prefer `st.secrets` and fallback to `os.environ`.

If you'd like any of those, tell me which and I'll add it.
