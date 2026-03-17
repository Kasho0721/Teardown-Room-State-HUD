from __future__ import annotations

import logging
import threading
import time

from agent.config import Settings
from agent.models import StateStore
from agent.sources import CompositeHudSource, FileHudSource, HudSource, XmlSavegameSource
from agent.uploader import CloudUploader

logger = logging.getLogger(__name__)


class AgentService:
    def __init__(self, settings: Settings, source: HudSource | None = None) -> None:
        self.settings = settings
        self.source = source or CompositeHudSource(
            XmlSavegameSource(settings.savegame_xml_path),
            FileHudSource(settings.hud_source_file),
        )
        self.store = StateStore()
        self.uploader = CloudUploader(settings.cloud_endpoint)
        self._stop_event = threading.Event()
        self._threads: list[threading.Thread] = []
        self._last_heartbeat_value: tuple[int, int] | None = None
        self._heartbeat_started = False
        self._last_heartbeat_change_at = 0
        self._game_closed = False

    def start(self) -> None:
        self._threads.append(threading.Thread(target=self._poll_loop, name='poll-loop', daemon=True))
        if self.uploader.enabled:
            self._threads.append(threading.Thread(target=self._upload_loop, name='upload-loop', daemon=True))
        for thread in self._threads:
            thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        for thread in self._threads:
            thread.join(timeout=1)

    def get_status(self) -> dict:
        state = self.store.get_state()
        now_ts = int(time.time())
        uptime = int(state.uptimeSeconds or 0)
        last_update = int(state.lastUpdate or 0)
        current_heartbeat = (uptime, last_update)

        online = False
        offline = True
        reason = 'no heartbeat'

        if uptime > 0 and last_update > 0:
            if self._last_heartbeat_value is None:
                self._last_heartbeat_value = current_heartbeat
                self._heartbeat_started = False
                self._last_heartbeat_change_at = 0
                reason = 'waiting for heartbeat'
            elif current_heartbeat != self._last_heartbeat_value:
                self._last_heartbeat_value = current_heartbeat
                self._heartbeat_started = True
                self._last_heartbeat_change_at = now_ts
                online = True
                offline = False
                reason = ''
            elif self._heartbeat_started and self._last_heartbeat_change_at and now_ts - self._last_heartbeat_change_at <= self.settings.offline_after_seconds:
                online = True
                offline = False
                reason = ''
            elif self._heartbeat_started:
                reason = 'heartbeat stopped'
            else:
                reason = 'waiting for heartbeat'
        else:
            self._last_heartbeat_value = None
            self._heartbeat_started = False
            self._last_heartbeat_change_at = 0

        return {
            'hostName': state.hostName,
            'playerCount': state.playerCount,
            'maxPlayers': state.maxPlayers,
            'players': state.players,
            'uptimeSeconds': state.uptimeSeconds,
            'lastUpdate': state.lastUpdate,
            'sequence': state.sequence,
            'online': online,
            'stale': False,
            'offline': offline,
            'offlineReason': reason,
            'roomLabel': self.settings.room_label,
            'roomCode': self.settings.room_code,
            'clientId': self.settings.client_id,
            'cloudEndpoint': self.settings.cloud_endpoint,
        }

    def get_health(self) -> dict:
        return self.get_status()

    def get_bridge_status(self) -> dict:
        return self.get_status()

    def _poll_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                previous = self.store.get_state()
                result = self.source.read(previous=previous)
                self.store.update_state(result.state)
                self.store.set_source_status(
                    True,
                    raw=result.raw,
                    name=result.source_name,
                    source_type=result.source_type,
                    details=result.details,
                    success_at=result.read_at,
                    changed=(result.state.lastUpdate != previous.lastUpdate or result.state.uptimeSeconds != previous.uptimeSeconds),
                )
                self._game_closed = False
            except Exception as exc:
                logger.warning('Polling failed: %s', exc)
                self._game_closed = True
                from agent.models import RoomState
                self.store.update_state(RoomState())
            self._stop_event.wait(self.settings.poll_interval)

    def _upload_loop(self) -> None:
        while not self._stop_event.is_set():
            now_ts = int(time.time())
            state = self.store.get_state()
            status = self.get_status()
            room_code = self.settings.room_code or ''
            ok, error = self.uploader.upload(status, state, self.settings.client_id, self.settings.room_label, room_code)
            self.store.set_upload_status(ok, at=now_ts, error=error)
            self._stop_event.wait(self.settings.upload_interval)
