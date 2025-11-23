Here you go — versi Inggris yang lebih ringkas, clean, dan tetap profesional.

⸻

Personal Input Tracker & Logger

A transparent, permission-based desktop assistant that records keyboard and mouse input, stores it locally, and optionally sends batches to a custom webhook/server for dashboards and auditing.

⚠️ Ethics & Privacy — Use this tool only on devices/accounts you own or have written permission to monitor. This app is not stealthy; the GUI is always visible and shows an ethics warning at startup.

⸻

Key Features
	•	Real-time keyboard & mouse capture using pynput
	•	Full metadata: UTC timestamp, active window title, cursor position, scroll delta
	•	Sensitive-window filtering by keywords (password/login/auth/etc.)
	•	Local JSONL logging + batch HTTP upload to a webhook
	•	Queueing & retry system with offline cache
	•	Modern tkinter GUI + optional tray controls (start/pause, stats, open log folder)
	•	Debug mode for terminal event output
	•	Optional periodic screenshots (mss / pyautogui)
	•	Central config via config.json
	•	Lightweight FastAPI server + HTML dashboard + SQLite
	•	PyInstaller packaging instructions for Windows/macOS/Linux

⸻

Requirements
	•	Python 3.10+
	•	GUI-enabled OS (required by pynput & pyautogui)

⸻

Installation

python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt


⸻

Configuration

A config.json file is generated on first run. Example:

{
  "webhook_url": "http://127.0.0.1:8000/api/input",
  "send_interval_seconds": 5,
  "batch_size": 25,
  "log_dir": "logs",
  "enable_screenshots": false,
  "screenshot_interval_seconds": 120,
  "debug_mode": false,
  "tray_enabled": true,
  "pending_cache_file": "pending_events.jsonl",
  "screenshot_format": "png",
  "sensitive_title_keywords": ["password", "login", "auth", "credential"],
  "ethics_acknowledged": false
}


⸻

Running the Desktop App

source .venv/bin/activate
python main.py

Main controls: Start/Pause, Open Logs, Exit

Debug Mode

Enable "debug_mode": true to print events in the terminal.

Screenshots

Set "enable_screenshots": true to capture periodic screenshots.

⸻

FastAPI Server

Start the server:

uvicorn server:APP --reload --host 0.0.0.0 --port 8000

Optional env vars:
	•	TRACKER_DASH_USER / TRACKER_DASH_PASS — enable Basic Auth
	•	DB_PATH — custom SQLite path

Endpoints:
	•	POST /api/input — receive { "events": [...] }
	•	GET /api/events?limit=50 — recent events
	•	GET / — auto-refresh dashboard

⸻

Packaging (PyInstaller)

pyinstaller --onefile --windowed --name InputTracker main.py

Include config.json, requirements.txt, and README when distributing.

⸻

Project Structure

main.py
config.py
logger.py
sender.py
screenshot.py
storage.py
utils.py
gui.py
server.py
templates/


⸻

Troubleshooting
	•	Enable debug mode for detailed logs
	•	Local events stored in logs/events.jsonl
	•	Pending queue stored in logs/pending_events.jsonl

⸻