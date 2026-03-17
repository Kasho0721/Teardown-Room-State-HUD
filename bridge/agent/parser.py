from __future__ import annotations

import time
from typing import Iterable

from agent.models import RoomState


HEADER = "TDSTAT"


def _clean_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _to_map(lines: Iterable[str]) -> dict[str, str]:
    data: dict[str, str] = {}
    for line in lines:
        if line.upper() == HEADER:
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip().upper()] = value.strip()
    return data


def parse_hud_text(text: str, previous: RoomState | None = None, now_ts: int | None = None) -> RoomState:
    previous = previous or RoomState()
    now_ts = now_ts or int(time.time())
    lines = _clean_lines(text)
    data = _to_map(lines)

    host_name = data.get("HOST", previous.hostName)

    player_count = previous.playerCount
    max_players = previous.maxPlayers
    count_raw = data.get("COUNT", "")
    if "/" in count_raw:
        left, right = count_raw.split("/", 1)
        try:
            player_count = int(left.strip())
        except ValueError:
            pass
        try:
            max_players = int(right.strip())
        except ValueError:
            pass

    players = previous.players
    if "PLAYERS" in data:
        players = [item.strip() for item in data["PLAYERS"].split("|") if item.strip()]
        if not data["PLAYERS"].strip():
            players = []

    if players and "COUNT" not in data:
        player_count = len(players)

    uptime = previous.uptimeSeconds
    if "UPTIME" in data:
        try:
            uptime = int(data["UPTIME"])
        except ValueError:
            pass

    started_at = previous.startedAt
    if uptime >= 0:
        started_at = now_ts - uptime

    return RoomState(
        hostName=host_name,
        playerCount=player_count,
        maxPlayers=max_players,
        players=players,
        startedAt=started_at,
        uptimeSeconds=uptime,
        lastUpdate=now_ts,
    )
