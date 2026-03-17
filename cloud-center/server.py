from __future__ import annotations

import json
import time
from pathlib import Path
from threading import Lock
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


DATA_DIR = Path(__file__).resolve().parent / "data"
STATE_FILE = DATA_DIR / "rooms.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class ReportPayload(BaseModel):
    reporterId: str = Field(..., min_length=1)
    reporterName: str = Field(..., min_length=1)
    roomLabel: str = ""
    hostName: str = ""
    playerCount: int = 0
    maxPlayers: int = 0
    players: list[str] = Field(default_factory=list)
    uptimeSeconds: int = 0
    lastUpdate: int = 0
    sequence: int = 0
    online: bool = False
    stale: bool = False
    offline: bool = False
    idleSeconds: int | None = None
    offlineReason: str = ""
    source: str = "bridge"


class StateStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.lock = Lock()
        self.rooms: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self.rooms = {}
            return
        try:
            self.rooms = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            self.rooms = {}

    def _save(self) -> None:
        self.path.write_text(json.dumps(self.rooms, ensure_ascii=False, indent=2), encoding="utf-8")

    def upsert(self, payload: ReportPayload) -> dict[str, Any]:
        now_ts = int(time.time())
        with self.lock:
            previous = self.rooms.get(payload.reporterId, {})
            item = {
                "reporterId": payload.reporterId,
                "reporterName": payload.reporterName,
                "roomLabel": payload.roomLabel or payload.reporterName,
                "hostName": payload.hostName,
                "playerCount": payload.playerCount,
                "maxPlayers": payload.maxPlayers,
                "players": payload.players,
                "uptimeSeconds": payload.uptimeSeconds,
                "lastUpdate": payload.lastUpdate,
                "sequence": payload.sequence,
                "online": payload.online,
                "stale": payload.stale,
                "offline": payload.offline,
                "idleSeconds": payload.idleSeconds,
                "offlineReason": payload.offlineReason,
                "source": payload.source,
                "reportedAt": now_ts,
                "changed": self._changed(previous, payload),
            }
            self.rooms[payload.reporterId] = item
            self._save()
            return item

    def _changed(self, previous: dict[str, Any], payload: ReportPayload) -> bool:
        if not previous:
            return True
        keys = [
            "hostName",
            "playerCount",
            "maxPlayers",
            "players",
            "sequence",
            "online",
            "stale",
            "offline",
            "offlineReason",
        ]
        current = payload.model_dump()
        return any(previous.get(key) != current.get(key) for key in keys)

    def all_rooms(self) -> list[dict[str, Any]]:
        with self.lock:
            return sorted(self.rooms.values(), key=lambda x: (not x.get("online", False), x.get("reporterName", "")))

    def get_room(self, reporter_id: str):
        with self.lock:
            return self.rooms.get(reporter_id)


store = StateStore(STATE_FILE)
app = FastAPI(title="Teardown Room Center")


@app.get("/")
def root() -> dict[str, Any]:
    return {"service": "teardown-room-center", "endpoints": ["/health", "/report", "/rooms", "/rooms/{reporterId}"]}


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "rooms": len(store.all_rooms())}


@app.post("/report")
def report(payload: ReportPayload) -> dict[str, Any]:
    item = store.upsert(payload)
    return {"ok": True, "room": item}


@app.get("/rooms")
def rooms() -> dict[str, Any]:
    return {"ok": True, "rooms": store.all_rooms()}


@app.get("/rooms/{reporter_id}")
def room(reporter_id: str) -> dict[str, Any]:
    item = store.get_room(reporter_id)
    if not item:
        raise HTTPException(status_code=404, detail="room not found")
    return {"ok": True, "room": item}
