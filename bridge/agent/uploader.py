from __future__ import annotations

import socket
import time

import requests

from agent.models import RoomState


class CloudUploader:
    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint.strip()
        self._last_online = None  # 记录上次上报的在线状态
        self._last_reported_at = 0  # 上次上报时间

    @property
    def enabled(self) -> bool:
        return bool(self.endpoint)

    def upload(self, status: dict, state: RoomState, client_id: str, room_label: str, room_code: str = '') -> tuple[bool, str]:
        if not self.enabled:
            return True, 'upload disabled'

        now = int(time.time())
        is_online = status.get('online', False)
        offline_reason = status.get('offlineReason', '')

        # 构建 payload
        if is_online and not offline_reason:
            # 游戏在线
            host_name = status.get('hostName', state.hostName) or room_label or 'Unknown'
            payload = {
                'reporterId': client_id,
                'reporterName': room_label or host_name,
                'roomLabel': room_label or host_name,
                'roomCode': room_code,
                'hostName': host_name,
                'playerCount': status.get('playerCount', state.playerCount),
                'maxPlayers': status.get('maxPlayers', state.maxPlayers),
                'players': status.get('players', state.players),
                'uptimeSeconds': status.get('uptimeSeconds', state.uptimeSeconds),
                'lastUpdate': status.get('lastUpdate', state.lastUpdate),
                'sequence': status.get('sequence', state.sequence),
                'online': True,
                'stale': False,
                'offline': False,
                'offlineReason': '',
                'source': 'bridge@' + socket.gethostname(),
                'reportedAt': now,
            }
        else:
            # 游戏离线
            payload = {
                'reporterId': client_id,
                'reporterName': room_label or 'Unknown',
                'roomLabel': room_label or 'Unknown',
                'roomCode': room_code,
                'hostName': '',
                'playerCount': 0,
                'maxPlayers': 0,
                'players': [],
                'uptimeSeconds': 0,
                'lastUpdate': 0,
                'sequence': 0,
                'online': False,
                'stale': False,
                'offline': True,
                'offlineReason': offline_reason or 'game not running',
                'source': 'bridge@' + socket.gethostname(),
                'reportedAt': now,
            }

        # 主动管理状态：状态变化立即上报，或者每10秒报一次心跳
        should_upload = False
        if self._last_online != is_online:
            # 状态变化了，立即上报
            should_upload = True
        elif now - self._last_reported_at >= 10:
            # 超过10秒没上报，报个心跳
            should_upload = True

        if not should_upload:
            return True, f'status unchanged ({is_online}), skipped'

        self._last_online = is_online
        self._last_reported_at = now

        try:
            session = requests.Session()
            session.trust_env = False
            resp = session.post(self.endpoint, json=payload, timeout=5)
            if 200 <= resp.status_code < 300:
                return True, ''
            return False, 'HTTP %s: %s' % (resp.status_code, resp.text[:200])
        except Exception as exc:
            return False, str(exc)
