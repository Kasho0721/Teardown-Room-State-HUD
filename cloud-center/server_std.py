import json
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from socketserver import ThreadingMixIn
from threading import Lock
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).resolve().parent
DASHBOARD_FILE = BASE_DIR / 'dashboard.html'
DATA_DIR = BASE_DIR / 'data'
STATE_FILE = DATA_DIR / 'rooms.json'
DATA_DIR.mkdir(parents=True, exist_ok=True)


STALE_AFTER_SECONDS = 15
OFFLINE_AFTER_SECONDS = 30
ADMIN_TOKEN = os.getenv('ADMIN_TOKEN', 'change-me-admin-token')


class Store(object):
    def __init__(self, path):
        self.path = path
        self.lock = Lock()
        self.rooms = {}
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                self.rooms = json.loads(self.path.read_text(encoding='utf-8'))
            except Exception:
                self.rooms = {}

    def _save(self):
        self.path.write_text(json.dumps(self.rooms, ensure_ascii=False, indent=2), encoding='utf-8')

    def upsert(self, payload):
        now_ts = int(time.time())
        reporter_id = str(payload.get('reporterId', '')).strip()
        if not reporter_id:
            raise ValueError('reporterId is required')
        reporter_name = str(payload.get('reporterName', '')).strip()
        if not reporter_name:
            raise ValueError('reporterName is required')

        with self.lock:
            prev = self.rooms.get(reporter_id, {})
            uptime = int(payload.get('uptimeSeconds') or 0)
            last_update = int(payload.get('lastUpdate') or 0)
            prev_uptime = int(prev.get('uptimeSeconds') or 0)
            prev_last_update = int(prev.get('lastUpdate') or 0)
            heartbeat_changed = uptime > 0 and last_update > 0 and (uptime != prev_uptime or last_update != prev_last_update)
            item = {
                'reporterId': reporter_id,
                'reporterName': reporter_name,
                'roomLabel': str(payload.get('roomLabel') or reporter_name),
                'roomCode': str(payload.get('roomCode') or ''),
                'hostName': str(payload.get('hostName') or ''),
                'playerCount': int(payload.get('playerCount') or 0),
                'maxPlayers': int(payload.get('maxPlayers') or 0),
                'players': list(payload.get('players') or []),
                'uptimeSeconds': uptime,
                'lastUpdate': last_update,
                'sequence': int(payload.get('sequence') or 0),
                'online': bool(payload.get('online', False)),
                'stale': bool(payload.get('stale', False)),
                'offline': bool(payload.get('offline', False)),
                'offlineReason': str(payload.get('offlineReason') or ''),
                'source': str(payload.get('source') or 'bridge'),
                'reportedAt': now_ts,
                '_prevUptime': prev_uptime,
                '_prevLastUpdate': prev_last_update,
                '_heartbeatChangedAt': now_ts if heartbeat_changed else int(prev.get('_heartbeatChangedAt') or 0),
                'changed': self._changed(prev, payload),
            }
            self.rooms[reporter_id] = item
            self._save()
            return item

    def _changed(self, prev, payload):
        if not prev:
            return True
        keys = ['hostName', 'playerCount', 'maxPlayers', 'players', 'sequence', 'online', 'stale', 'offline', 'offlineReason']
        return any(prev.get(k) != payload.get(k) for k in keys)

    def _with_server_side_status(self, item):
        """规则：心跳变化后维持在线；连续 30 秒没有新变化才离线。"""
        out = dict(item)
        now_ts = int(time.time())
        uptime = int(out.get('uptimeSeconds', 0) or 0)
        last_update = int(out.get('lastUpdate', 0) or 0)
        reported_at = int(out.get('reportedAt', 0) or 0)
        heartbeat_changed_at = int(out.get('_heartbeatChangedAt', 0) or 0)

        if uptime <= 0 or last_update <= 0:
            out['online'] = False
            out['stale'] = False
            out['offline'] = True
            out['offlineReason'] = 'no heartbeat'
            return out

        if reported_at and now_ts - reported_at > OFFLINE_AFTER_SECONDS:
            out['online'] = False
            out['stale'] = False
            out['offline'] = True
            out['offlineReason'] = 'report timeout'
            return out

        if heartbeat_changed_at and now_ts - heartbeat_changed_at <= OFFLINE_AFTER_SECONDS:
            out['online'] = True
            out['stale'] = False
            out['offline'] = False
            out['offlineReason'] = ''
            return out

        out['online'] = False
        out['stale'] = False
        out['offline'] = True
        out['offlineReason'] = 'heartbeat stopped'
        return out

    def all_rooms(self):
        with self.lock:
            rooms = [self._with_server_side_status(item) for item in self.rooms.values()]
            return sorted(rooms, key=lambda x: (not x.get('online', False), x.get('reporterName', '')))

    def get_room(self, reporter_id):
        with self.lock:
            item = self.rooms.get(reporter_id)
            if not item:
                return None
            return self._with_server_side_status(item)

    def delete_room(self, reporter_id):
        with self.lock:
            if reporter_id in self.rooms:
                deleted = self.rooms.pop(reporter_id)
                self._save()
                return deleted
            return None

    def cleanup_test_rooms(self):
        with self.lock:
            removed = []
            keys = list(self.rooms.keys())
            for reporter_id in keys:
                item = self.rooms.get(reporter_id, {})
                name = str(item.get('reporterName') or '')
                label = str(item.get('roomLabel') or '')
                if reporter_id in ('probe', 'local-test', 'test', 'demo') or name in ('Probe', 'LocalTest', 'Test', 'Demo') or label in ('Probe', 'LocalTest 房间', 'Test', 'Demo'):
                    removed.append(self.rooms.pop(reporter_id))
            if removed:
                self._save()
            return removed


STORE = Store(STATE_FILE)


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _is_admin(self):
        token = self.headers.get('X-Admin-Token', '')
        return token == ADMIN_TOKEN

    def _send_html(self, code, text):
        body = text.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        if path == '/':
            if DASHBOARD_FILE.exists():
                html = DASHBOARD_FILE.read_text(encoding='utf-8').replace('__ADMIN_ENABLED__', 'true' if query.get('admin', ['0'])[0] == '1' else 'false')
                return self._send_html(200, html)
            return self._send_json(200, {'service': 'teardown-room-center', 'endpoints': ['/health', '/report', '/rooms', '/rooms/<reporterId>']})
        if path == '/health':
            return self._send_json(200, {'ok': True, 'rooms': len(STORE.all_rooms())})
        if path == '/rooms':
            return self._send_json(200, {'ok': True, 'rooms': STORE.all_rooms()})
        if path.startswith('/rooms/'):
            reporter_id = path.split('/rooms/', 1)[1]
            item = STORE.get_room(reporter_id)
            if not item:
                return self._send_json(404, {'ok': False, 'detail': 'room not found'})
            return self._send_json(200, {'ok': True, 'room': item})
        return self._send_json(404, {'ok': False, 'detail': 'not found'})

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            length = int(self.headers.get('Content-Length', '0'))
            raw = self.rfile.read(length).decode('utf-8')
            payload = json.loads(raw or '{}')
        except Exception:
            payload = {}

        if path == '/report':
            try:
                item = STORE.upsert(payload)
                return self._send_json(200, {'ok': True, 'room': item})
            except ValueError as exc:
                return self._send_json(400, {'ok': False, 'detail': str(exc)})
            except Exception as exc:
                return self._send_json(500, {'ok': False, 'detail': str(exc)})

        if path == '/admin/cleanup-test':
            if not self._is_admin():
                return self._send_json(403, {'ok': False, 'detail': 'forbidden'})
            removed = STORE.cleanup_test_rooms()
            return self._send_json(200, {'ok': True, 'removed': removed, 'count': len(removed)})

        if path == '/admin/delete-room':
            if not self._is_admin():
                return self._send_json(403, {'ok': False, 'detail': 'forbidden'})
            reporter_id = str(payload.get('reporterId') or '').strip()
            if not reporter_id:
                return self._send_json(400, {'ok': False, 'detail': 'reporterId is required'})
            deleted = STORE.delete_room(reporter_id)
            if not deleted:
                return self._send_json(404, {'ok': False, 'detail': 'room not found'})
            return self._send_json(200, {'ok': True, 'deleted': deleted})

        return self._send_json(404, {'ok': False, 'detail': 'not found'})

    def log_message(self, format, *args):
        return


if __name__ == '__main__':
    server = ThreadingHTTPServer(('0.0.0.0', 18080), Handler)
    server.serve_forever()
