from __future__ import annotations

import json
import logging
import uuid

from agent.runtime_paths import config_path

logger = logging.getLogger(__name__)
CONFIG_PATH = config_path()


def _config_summary(data: dict) -> dict:
    return {
        'clientId': data.get('clientId', ''),
        'roomLabel': data.get('roomLabel', ''),
        'roomCode': data.get('roomCode', ''),
        'cloudEndpoint': data.get('cloudEndpoint', ''),
        'pollInterval': data.get('pollInterval'),
        'uploadInterval': data.get('uploadInterval'),
    }


def load_local_config() -> dict:
    logger.info('Loading local config from %s', CONFIG_PATH)
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
            if isinstance(data, dict):
                logger.info('Loaded local config: %s', _config_summary(data))
                return data
            logger.warning('Local config is not a dict, path=%s type=%s', CONFIG_PATH, type(data).__name__)
        except Exception:
            logger.exception('Failed to load local config from %s', CONFIG_PATH)
    data = {
        'clientId': uuid.uuid4().hex,
        'roomLabel': '',
        'roomCode': '',
        'cloudEndpoint': 'http://your-cloud-center:18080/report',
        'pollInterval': 0.2,
        'uploadInterval': 1.0,
    }
    logger.info('Using default local config: %s', _config_summary(data))
    save_local_config(data)
    return data


def save_local_config(data: dict) -> dict:
    logger.info('Saving local config to %s', CONFIG_PATH)
    merged = load_local_config() if CONFIG_PATH.exists() else {}
    merged.update({k: v for k, v in data.items() if v is not None})
    if not merged.get('clientId'):
        merged['clientId'] = uuid.uuid4().hex
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding='utf-8')
    logger.info('Saved local config: %s', _config_summary(merged))
    return merged
