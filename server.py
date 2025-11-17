"""FastAPI receiver & dashboard for Personal Input Tracker."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List
import os
import sqlite3
import json

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates

APP = FastAPI(title="Input Tracker Server")
DB_PATH = Path(os.getenv("TRACKER_DB_PATH", "tracker.db"))
TEMPLATES = Jinja2Templates(directory="templates")
security = HTTPBasic()


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                type TEXT,
                data TEXT,
                window TEXT,
                position TEXT,
                delta TEXT,
                format TEXT,
                raw_json TEXT
            )
            """
        )
        conn.commit()


def save_events(events: Iterable[dict]) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.executemany(
            """
            INSERT INTO events(timestamp, type, data, window, position, delta, format, raw_json)
            VALUES(:timestamp, :type, :data, :window, :position, :delta, :format, :raw_json)
            """,
            [
                {
                    "timestamp": event.get("timestamp"),
                    "type": event.get("type"),
                    "data": event.get("data"),
                    "window": event.get("window"),
                    "position": event.get("position"),
                    "delta": event.get("delta"),
                    "format": event.get("format"),
                    "raw_json": json.dumps(event),
                }
                for event in events
            ],
        )
        conn.commit()


def fetch_events(limit: int = 100) -> List[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM events ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def require_auth(credentials: HTTPBasicCredentials = Depends(security)) -> None:
    username = os.getenv("TRACKER_DASH_USER")
    password = os.getenv("TRACKER_DASH_PASS")
    if not username:
        return
    correct = credentials.username == username and credentials.password == password
    if not correct:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


@APP.on_event("startup")
def on_startup() -> None:
    init_db()


@APP.post("/api/input")
async def ingest(payload: dict) -> JSONResponse:
    events = payload.get("events")
    if not isinstance(events, list):
        raise HTTPException(status_code=400, detail="Missing events list")
    save_events(events)
    return JSONResponse({"status": "ok", "received": len(events)})


@APP.get("/api/events")
async def api_events(limit: int = 100) -> List[dict]:
    return fetch_events(limit)


@APP.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, _: None = Depends(require_auth)) -> HTMLResponse:
    return TEMPLATES.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(APP, host="0.0.0.0", port=8000)
