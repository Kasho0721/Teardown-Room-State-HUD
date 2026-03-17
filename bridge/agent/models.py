from __future__ import annotations

from dataclasses import asdict, dataclass, field
from threading import Lock
from typing import Any


@dataclass
class RoomState:
    hostName: str = ""
    playerCount: int = 0
    maxPlayers: int = 0
    players: list[str] = field(default_factory=list)
    startedAt: int = 0
    uptimeSeconds: int = 0
    lastUpdate: int = 0
    sequence: int = 0
    changedAt: int = 0
    emittedAt: int = 0
    snapshot: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class StateStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._state = RoomState()
        self._source_ok = False
        self._source_error = ""
        self._source_name = ""
        self._source_type = ""
        self._source_details: dict[str, Any] = {}
        self._last_source_raw = ""
        self._last_source_success_at = 0
        self._last_change_seen_at = 0
        self._last_upload_at = 0
        self._last_upload_ok = False
        self._last_upload_error = ""

    def get_state(self) -> RoomState:
        with self._lock:
            return RoomState(**self._state.to_dict())

    def update_state(self, state: RoomState) -> None:
        with self._lock:
            self._state = state

    def set_source_status(
        self,
        ok: bool,
        error: str = "",
        raw: str = "",
        name: str = "",
        source_type: str = "",
        details: dict[str, Any] | None = None,
        success_at: int = 0,
        changed: bool = False,
    ) -> None:
        with self._lock:
            self._source_ok = ok
            self._source_error = error
            if name:
                self._source_name = name
            if source_type:
                self._source_type = source_type
            if details is not None:
                self._source_details = details
            if raw:
                self._last_source_raw = raw
            if success_at:
                self._last_source_success_at = success_at
                if changed:
                    self._last_change_seen_at = success_at

    def set_upload_status(self, ok: bool, at: int, error: str = "") -> None:
        with self._lock:
            self._last_upload_ok = ok
            self._last_upload_at = at
            self._last_upload_error = error

    def diagnostics(self) -> dict[str, Any]:
        with self._lock:
            return {
                "source": {
                    "ok": self._source_ok,
                    "active": self._source_name,
                    "type": self._source_type,
                    "details": dict(self._source_details),
                    "error": self._source_error,
                    "lastRaw": self._last_source_raw,
                    "lastSuccessAt": self._last_source_success_at,
                    "lastChangeSeenAt": self._last_change_seen_at,
                },
                "upload": {
                    "ok": self._last_upload_ok,
                    "lastAt": self._last_upload_at,
                    "error": self._last_upload_error,
                },
            }
