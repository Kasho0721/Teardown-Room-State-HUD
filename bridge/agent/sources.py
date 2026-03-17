from __future__ import annotations

import logging
import os
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agent.models import RoomState
from agent.parser import parse_hud_text

logger = logging.getLogger(__name__)


@dataclass
class SourceReadResult:
    state: RoomState
    source_name: str
    source_type: str
    details: dict[str, Any] = field(default_factory=dict)
    raw: str = ""
    read_at: int = field(default_factory=lambda: int(time.time()))


class HudSource:
    source_name = "unknown"
    source_type = "unknown"

    def read(self, previous: RoomState | None = None) -> SourceReadResult:
        raise NotImplementedError


class FileHudSource(HudSource):
    source_name = "file"
    source_type = "hud_text"

    def __init__(self, path: str) -> None:
        self.path = Path(path)

    def read(self, previous: RoomState | None = None) -> SourceReadResult:
        if not self.path.exists():
            raise FileNotFoundError(f"HUD source file not found: {self.path}")

        raw = self.path.read_text(encoding="utf-8")
        state = parse_hud_text(raw, previous=previous)
        return SourceReadResult(
            state=state,
            source_name=self.source_name,
            source_type=self.source_type,
            details={"path": str(self.path.resolve())},
            raw=raw,
        )


class XmlSavegameSource(HudSource):
    source_name = "savegame_xml"
    source_type = "registry_xml"

    FIELD_ALIASES = {
        "hostName": ("hostName", "hostname"),
        "playerCount": ("playerCount", "playercount"),
        "maxPlayers": ("maxPlayers", "maxplayers"),
        "players": ("players",),
        "startedAt": ("startedAt", "startedat"),
        "uptimeSeconds": ("uptimeSeconds", "uptimeseconds"),
        "lastUpdate": ("lastUpdate", "lastupdate"),
        "sequence": ("sequence",),
        "changedAt": ("changedAt", "changedat"),
        "emittedAt": ("emittedAt", "emittedat"),
        "hudText": ("hudText", "hudtext"),
        "snapshot": ("snapshot",),
    }

    def __init__(self, path: str, registry_prefix: str = "savegame.mod.serverhud") -> None:
        self.path = Path(path)
        self.registry_prefix = registry_prefix

    def read(self, previous: RoomState | None = None) -> SourceReadResult:
        if not self.path.exists():
            raise FileNotFoundError(f"Teardown savegame.xml not found: {self.path}")

        xml_text = self.path.read_text(encoding="utf-8", errors="ignore")
        values = self._extract_registry_values(xml_text)
        if not values:
            raise ValueError(f"Registry path not found in savegame.xml: {self.registry_prefix}")

        state = self._build_state(values, previous=previous)
        return SourceReadResult(
            state=state,
            source_name=self.source_name,
            source_type=self.source_type,
            details={
                "path": str(self.path),
                "registryPrefix": self.registry_prefix,
            },
            raw=values.get("snapshot") or values.get("hudText") or "",
        )

    def _build_state(self, values: dict[str, str], previous: RoomState | None = None) -> RoomState:
        previous = previous or RoomState()
        now_ts = int(time.time())

        def get_value(name: str, default: str = "") -> str:
            for alias in self.FIELD_ALIASES.get(name, (name,)):
                if alias in values:
                    return values.get(alias, default)
            return default

        def as_int(name: str, default: int) -> int:
            raw = get_value(name, "")
            try:
                return int(str(raw).strip())
            except (TypeError, ValueError):
                return default

        players_raw = get_value("players", "")
        players = [item.strip() for item in players_raw.split("|") if item.strip()]

        uptime = as_int("uptimeSeconds", previous.uptimeSeconds)
        started_at = as_int("startedAt", previous.startedAt)
        if started_at <= 0 and uptime >= 0:
            started_at = now_ts - uptime

        state = RoomState(
            hostName=get_value("hostName", previous.hostName),
            playerCount=as_int("playerCount", previous.playerCount),
            maxPlayers=as_int("maxPlayers", previous.maxPlayers),
            players=players if players_raw != "" else list(previous.players),
            startedAt=started_at,
            uptimeSeconds=uptime,
            lastUpdate=as_int("lastUpdate", now_ts),
            sequence=as_int("sequence", previous.sequence),
            changedAt=as_int("changedAt", previous.changedAt),
            emittedAt=as_int("emittedAt", previous.emittedAt),
            snapshot=get_value("snapshot", previous.snapshot),
        )

        if state.playerCount <= 0 and state.players:
            state.playerCount = len(state.players)
        if state.maxPlayers < state.playerCount:
            state.maxPlayers = state.playerCount
        return state

    def _extract_registry_values(self, xml_text: str) -> dict[str, str]:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            values = self._extract_serverhud_block_regex(xml_text)
            if values:
                return values
            raise ValueError("Invalid savegame.xml and no serverhud block could be recovered")

        values = self._extract_prefixed_values(root)
        if values:
            return values
        values = self._extract_nested_values(root)
        if values:
            return values
        return self._extract_serverhud_block_regex(xml_text)

    def _extract_prefixed_values(self, root: ET.Element) -> dict[str, str]:
        values: dict[str, str] = {}
        prefix = self.registry_prefix + "."
        target_keys = self._target_keys()

        for elem in root.iter():
            attrs = {str(k): str(v) for k, v in elem.attrib.items()}
            candidates = [
                attrs.get("name", ""),
                attrs.get("key", ""),
                attrs.get("path", ""),
                attrs.get("id", ""),
                (elem.text or "").strip(),
            ]
            full_key = next((item.strip() for item in candidates if item and item.strip().startswith(prefix)), "")
            if not full_key:
                continue

            key_name = full_key[len(prefix) :]
            if key_name not in target_keys:
                continue
            values[key_name] = self._node_value(elem)
        return values

    def _extract_nested_values(self, root: ET.Element) -> dict[str, str]:
        for branch in root.iter():
            tag = branch.tag.lower() if isinstance(branch.tag, str) else ""
            if tag == "builtin-serverhud-clean":
                direct = branch.find("serverhud")
                if direct is not None:
                    branch_values = self._collect_branch_values(direct)
                    if branch_values:
                        return branch_values

        values = self._extract_path_based_nested_values(root)
        if values:
            return values

        for branch_name in ("serverhud", "builtin-serverhud"):
            for branch in root.iter(branch_name):
                direct = branch.find("serverhud") if branch_name == "builtin-serverhud" else branch
                if direct is None:
                    continue
                branch_values = self._collect_branch_values(direct)
                if branch_values:
                    return branch_values
        return {}

    def _extract_path_based_nested_values(self, root: ET.Element) -> dict[str, str]:
        path_parts = self.registry_prefix.split(".")
        candidate_branches = [root]

        for part in path_parts:
            next_branches: list[ET.Element] = []
            for branch in candidate_branches:
                next_branches.extend(list(branch.findall(part)))
            if next_branches:
                candidate_branches = next_branches
                continue

            fallback_branches: list[ET.Element] = []
            for branch in candidate_branches:
                fallback_branches.extend(list(branch.iter(part)))
            if not fallback_branches:
                return {}
            candidate_branches = fallback_branches

        for branch in candidate_branches:
            values = self._collect_branch_values(branch)
            if values:
                return values
        return {}

    def _collect_branch_values(self, branch: ET.Element) -> dict[str, str]:
        values: dict[str, str] = {}
        for key in self._target_keys():
            node = branch.find(key)
            if node is None:
                continue
            values[key] = self._node_value(node)
        return values

    def _target_keys(self) -> set[str]:
        keys: set[str] = set()
        for aliases in self.FIELD_ALIASES.values():
            keys.update(aliases)
        return keys

    def _node_value(self, node: ET.Element) -> str:
        value = node.attrib.get("value", "")
        if value:
            return value

        text = (node.text or "").strip()
        if text:
            return text

        for child in node:
            child_text = (child.text or "").strip()
            if child_text:
                return child_text
        return ""

    def _extract_serverhud_block_regex(self, xml_text: str) -> dict[str, str]:
        block_match = re.search(r"<builtin-serverhud-clean>.*?<serverhud>(.*?)</serverhud>.*?</builtin-serverhud-clean>", xml_text, re.S | re.I)
        if not block_match:
            block_match = re.search(r"<builtin-serverhud>.*?<serverhud>(.*?)</serverhud>.*?</builtin-serverhud>", xml_text, re.S | re.I)
        if not block_match:
            block_match = re.search(r"<serverhud>(.*?)</serverhud>", xml_text, re.S | re.I)
        if not block_match:
            return {}

        block = block_match.group(1)
        values: dict[str, str] = {}
        for key in self._target_keys():
            pattern = rf"<{re.escape(key)}\s+value=\"(.*?)\"\s*/>"
            match = re.search(pattern, block, re.S | re.I)
            if match:
                values[key] = match.group(1)
        return values


class CompositeHudSource(HudSource):
    source_name = "composite"
    source_type = "priority"

    def __init__(self, *sources: HudSource) -> None:
        self.sources = [source for source in sources if source is not None]
        self.last_error = ""

    def read(self, previous: RoomState | None = None) -> SourceReadResult:
        errors: list[str] = []
        for source in self.sources:
            try:
                result = source.read(previous=previous)
                self.last_error = ""
                return result
            except Exception as exc:
                errors.append(f"{source.source_name}: {exc}")

        self.last_error = " | ".join(errors)
        raise RuntimeError(self.last_error or "No HUD source configured")


def default_savegame_xml_path() -> str:
    env_value = os.getenv("TEARDOWN_SAVEGAME_XML") or os.getenv("SAVEGAME_XML_PATH")
    if env_value:
        return env_value

    local_appdata = os.getenv("LOCALAPPDATA", "").strip()
    if local_appdata:
        return str(Path(local_appdata) / "Teardown" / "savegame.xml")

    return r"C:\Users\Kasho\AppData\Local\Teardown\savegame.xml"
