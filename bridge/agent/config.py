from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from agent.local_config import load_local_config
from agent.sources import default_savegame_xml_path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Settings:
    agent_port: int
    poll_interval: float
    upload_interval: float
    hud_source_file: str
    savegame_xml_path: str
    cloud_endpoint: str
    room_label: str
    room_code: str
    client_id: str
    agent_name: str
    stale_after_seconds: int
    offline_after_seconds: int
    preferred_mod_tag: str

    @staticmethod
    def from_env() -> 'Settings':
        local = load_local_config()
        settings = Settings(
            agent_port=int(os.getenv('AGENT_PORT', '8787')),
            poll_interval=float(os.getenv('POLL_INTERVAL', '2.0')),
            upload_interval=float(os.getenv('UPLOAD_INTERVAL', '2.0')),
            hud_source_file=os.getenv('HUD_SOURCE_FILE', 'sample_hud.txt'),
            savegame_xml_path=default_savegame_xml_path(),
            cloud_endpoint=os.getenv('CLOUD_ENDPOINT', local.get('cloudEndpoint', '')).strip(),
            room_label=os.getenv('ROOM_LABEL', local.get('roomLabel', '')).strip(),
            room_code=os.getenv('ROOM_CODE', local.get('roomCode', '')).strip(),
            client_id=local.get('clientId', ''),
            agent_name=os.getenv('AGENT_NAME', 'teardown-room-agent'),
            stale_after_seconds=int(os.getenv('STALE_AFTER_SECONDS', '15')),
            offline_after_seconds=int(os.getenv('OFFLINE_AFTER_SECONDS', '30')),
            preferred_mod_tag=os.getenv('PREFERRED_MOD_TAG', 'serverhud-clean').strip().lower(),
        )
        logger.info(
            'Resolved settings: agent_port=%s cloud_endpoint=%s room_label=%s room_code=%s client_id=%s savegame_xml_path=%s hud_source_file=%s',
            settings.agent_port,
            settings.cloud_endpoint,
            settings.room_label,
            settings.room_code,
            settings.client_id,
            settings.savegame_xml_path,
            settings.hud_source_file,
        )
        return settings


settings = Settings.from_env()
