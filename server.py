from __future__ import annotations
import json
import logging
import os
import socket
import threading
import time
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import build_info
from urllib.parse import parse_qs, urlparse
from game import WORLD
from adventure_recovery import Recovery, proof_matches
RECOVERY = Recovery(WORLD)

def recovery():
    global RECOVERY
    if RECOVERY.world is not WORLD:
        RECOVERY = Recovery(WORLD)
    return RECOVERY
ROOT = Path(__file__).resolve().parent
STATIC = ROOT / 'static'
SIMULATION_LAST_TICK = None

def accepts_gzip(value):
    qualities = {}
    for entry in value.lower().split(','):
        coding, *parameters = entry.strip().split(';')
        quality = 1.0
        for parameter in parameters:
            if parameter.strip().startswith('q='):
                try:
                    quality = float(parameter.strip()[2:])
                except ValueError:
                    quality = 0.0
        qualities[coding] = quality if 0 <= quality <= 1 else 0.0
    return qualities.get('gzip', qualities.get('*', 0)) > 0

class DualStackThreadingHTTPServer(ThreadingHTTPServer):
    """Serve both IPv4 and IPv6 localhost clients from one listener."""
    address_family = socket.AF_INET6

    def server_bind(self) -> None:
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        super().server_bind()

class Handler(BaseHTTPRequestHandler):
    server_version = 'Gauntlet/0.1'

    def log_message(self, fmt: str, *args) -> None:
        print('%s - %s' % (self.address_string(), fmt % args))

    def log_request(self, code='-', size='-') -> None:
        if str(code) == '200' and urlparse(self.path).path in ('/api/state', '/api/action', '/healthz'):
            return
        self.log_message('"%s %s %s" %s %s', self.command, urlparse(self.path).path, self.request_version, str(code), str(size))

    def _send(self, status: int, body: dict | str | bytes, content_type: str='application/json; charset=utf-8') -> None:
        raw = body if isinstance(body, bytes) else body.encode('utf-8') if isinstance(body, str) else json.dumps(body).encode('utf-8')
        compressible = content_type.startswith(('text/', 'application/json'))
        encoded = False
        if compressible and len(raw) >= 1024 and accepts_gzip(self.headers.get('Accept-Encoding', '')):
            packed = __import__('gzip').compress(raw, compresslevel=1, mtime=0)
            if len(packed) < len(raw):
                raw = packed
                encoded = True
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(raw)))
        if compressible:
            self.send_header('Vary', 'Accept-Encoding')
        if encoded:
            self.send_header('Content-Encoding', 'gzip')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(raw)

    def _body(self) -> dict:
        size = int(self.headers.get('Content-Length', '0'))
        limit = 2000000 if self.path == '/api/adventure/import-preview' else 16384
        if not 0 <= size <= limit:
            raise ValueError('Request too large.')
        payload = json.loads(self.rfile.read(size) or b'{}')
        if not isinstance(payload, dict):
            raise ValueError('Request body must be an object.')
        return payload

    def _error(self, message: str, status: int=400) -> None:
        self._send(status, {'error': message})

    def _authorize_session(self, code, pid, proof=None):
        room = WORLD.rooms.get(str(code).upper())
        p = (room or {}).get('players', {}).get(pid)
        if p and (not proof_matches(proof, p.get('recoveryProof'))):
            raise ValueError('Private character recovery proof required. Use Continue or your private recovery link.')

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == '/api/build':
            return self._send(200, build_info.view())
        if parsed.path == '/api/diagnostics':
            query = parse_qs(parsed.query)
            try:
                self._authorize_session(query.get('room', [''])[0], query.get('player', [''])[0], self.headers.get('X-Gauntlet-Recovery'))
            except ValueError as error:
                return self._error(str(error), 403)
            member = WORLD.rooms.get(query.get('room', [''])[0].upper(), {}).get('players', {}).get(query.get('player', [''])[0])
            if not member:
                return self._error('Room or player not found.', 404)
            return self._send(200, dict(build=build_info.view(), metrics=WORLD.metrics.view()))
        if parsed.path == '/healthz':
            healthy = SIMULATION_LAST_TICK is None or time.monotonic() - SIMULATION_LAST_TICK < 5
            return self._send(200 if healthy else 503, {'ok': healthy})
        host_header = self.headers.get('Host', '')
        if host_header.lower().startswith('localhost:'):
            port = host_header.rsplit(':', 1)[-1]
            self.send_response(308)
            self.send_header('Location', f'http://127.0.0.1:{port}{self.path}')
            self.send_header('Content-Length', '0')
            self.end_headers()
            return
        if parsed.path == '/':
            return self._file('index.html', 'text/html; charset=utf-8')
        if parsed.path in ('/input-transport.js', '/adventure-skills.js', '/front-menu.js', '/opening.js', '/chapter.js', '/campaign.js', '/campaign-recap.js', '/state-cache.js', '/ascended-sprites.js', '/region-sprites.js', '/combat-visuals.js', '/travel-map.js', '/release-visuals.js', '/room-design-data.js', '/room-designs.js', '/ascended-summons.js'):
            return self._file(parsed.path.lstrip('/'), 'text/javascript; charset=utf-8')
        if parsed.path in ('/music.js', '/audio-routing.js', '/diagnostics.js', '/app.js', '/recovery.js', '/feedback.js', '/adventure.js', '/adventure-sprites.js', '/dungeon-sprites.js', '/camera.js', '/world-scenery.js', '/audio.js', '/coordination.js', '/progression.js', '/town-sprites.js', '/combat-environment.js', '/ability-animations.js', '/projectile-animations.js', '/movement.js', '/equipment-comparison.js', '/style.css'):
            name = parsed.path.lstrip('/')
            mime = 'text/javascript; charset=utf-8' if name.endswith('.js') else 'text/css; charset=utf-8'
            return self._file(name, mime)
        if parsed.path.startswith('/music/'):
            name = parsed.path.lstrip('/')
            asset = (STATIC / name).resolve()
            if not asset.is_relative_to((STATIC / 'music').resolve()) or asset.suffix.lower() not in ('.wav', '.json'):
                return self._error('Not found.', 404)
            return self._file(name, 'audio/wav' if asset.suffix.lower() == '.wav' else 'application/json')
        if parsed.path.startswith('/audio/'):
            name = parsed.path.lstrip('/')
            asset = (STATIC / name).resolve()
            if not asset.is_relative_to((STATIC / 'audio').resolve()) or asset.suffix.lower() != '.wav':
                return self._error('Not found.', 404)
            return self._file(name, 'audio/wav')
        if parsed.path.startswith('/sprites/'):
            name = parsed.path.lstrip('/')
            asset = (STATIC / name).resolve()
            if not asset.is_relative_to((STATIC / 'sprites').resolve()) or asset.suffix.lower() not in ('.png', '.json'):
                return self._error('Not found.', 404)
            mime = 'image/png' if asset.suffix.lower() == '.png' else 'application/json; charset=utf-8'
            return self._file(name, mime)
        if parsed.path in ('/api/state', '/api/stats'):
            query = parse_qs(parsed.query)
            try:
                self._authorize_session(query.get('room', [''])[0], query.get('player', [''])[0], self.headers.get('X-Gauntlet-Recovery'))
                args = (query.get('room', [''])[0], query.get('player', [''])[0])
                if parsed.path == '/api/state':
                    state = WORLD.state(*args, include_catalog=query.get('catalog', [''])[0] != build_info.SERVER, known_skill_revision=query.get('heroSkills', [''])[0] or None)
                    state['catalogVersion'] = build_info.SERVER
                else:
                    state = WORLD.run_stats(*args)
            except ValueError as error:
                return self._error(str(error), 404)
            return self._send(200, state)
        if parsed.path == '/api/cloud/config':
            return self._send(200, WORLD.storage.cloud.public_config() if WORLD.storage else {'configured': False})
        return self._error('Not found.', 404)

    def _file(self, name: str, mime: str) -> None:
        path = STATIC / name
        if not path.is_file():
            return self._error('Client file not found.', 404)
        self._send(200, path.read_bytes(), mime)

    def do_POST(self) -> None:
        try:
            payload = self._body()
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            return self._error('Invalid request body.')
        try:
            if self.path == '/api/new-run':
                code, pid = __import__('session_flow').create(WORLD, payload, build_info.INSTANCE)
                return self._send(201, recovery().session(code, pid))
            if self.path == '/api/party/join':
                code, pid = __import__('session_flow').join(WORLD, payload)
                return self._send(201, recovery().session(code, pid))
            if self.path == '/api/rooms':
                name = str(payload.get('name', 'Player')).strip()[:18] or 'Player'
                code, player_id = WORLD.create_room(name)
                WORLD.rooms[code]['players'][player_id]['strictSession'] = True
                return self._send(201, recovery().session(code, player_id))
            if self.path == '/api/join':
                name = str(payload.get('name', 'Player')).strip()[:18] or 'Player'
                code, player_id = WORLD.join_room(str(payload.get('room', '')), name)
                WORLD.rooms[code]['players'][player_id]['strictSession'] = True
                return self._send(201, recovery().session(code, player_id))
            if self.path in ('/api/adventure/summary', '/api/adventure/export'):
                self._authorize_session(payload.get('room'), payload.get('player'), payload.get('recovery') or self.headers.get('X-Gauntlet-Recovery'))
                return self._send(200, recovery().read(payload, export=self.path.endswith('export')))
            if self.path == '/api/adventure/import-preview':
                return self._send(200, recovery().preview(payload.get('document')))
            if self.path == '/api/adventure/import':
                return self._send(201, recovery().commit(payload))
            if self.path in ('/api/adventure/slots', '/api/adventure/backup-preview'):
                return self._send(200, recovery().slots(payload, preview=self.path.endswith('backup-preview')))
            if self.path == '/api/adventure/invite':
                return self._send(200, recovery().guest_invite(payload))
            if self.path == '/api/adventure/roster':
                self._authorize_session(payload.get('room'), payload.get('player'), payload.get('recovery') or self.headers.get('X-Gauntlet-Recovery'))
                with WORLD.lock:
                    room, p = WORLD.adventure_access(payload.get('room', ''), payload.get('player', ''))
                    return self._send(200, [dict(characterId=c['characterId'], name=c['name'], hero=c['class']) for c in room['players'].values() if not c.get('bot')])
            if self.path.startswith('/api/cloud/'):
                if not WORLD.storage:
                    raise ValueError('Cloud storage is not configured.')
                cloud = WORLD.storage.cloud
                token = self.headers.get('Authorization', '').removeprefix('Bearer ')
                if self.path == '/api/cloud/claim':
                    result = cloud.claim(WORLD, payload, token)
                elif self.path == '/api/cloud/worlds':
                    result = cloud.worlds(token)
                elif self.path == '/api/cloud/preview':
                    actor = cloud.actor(token)
                    wid = str(__import__('uuid').UUID(str(payload.get('worldId', ''))))
                    record = cloud.rpc('gauntlet_load_world', p_actor=actor, p_world=wid)
                    result = recovery().preview(record['record']['backup'])
                elif self.path == '/api/cloud/load':
                    result = cloud.load(recovery(), token, payload.get('worldId', ''), as_copy=payload.get('copy') is True)
                else:
                    raise ValueError('Unknown cloud operation.')
                return self._send(200, result)
            if self.path == '/api/action':
                self._authorize_session(payload.get('room'), payload.get('player'), payload.get('recovery') or self.headers.get('X-Gauntlet-Recovery'))
                WORLD.action(str(payload.get('room', '')), str(payload.get('player', '')), payload)
                return self._send(200, {'ok': True})
        except ValueError as error:
            return self._error(str(error))
        return self._error('Not found.', 404)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def _simulation_loop(stop_event=None) -> None:
    global SIMULATION_LAST_TICK
    SIMULATION_LAST_TICK = time.monotonic()
    deadline = time.monotonic()
    while stop_event is None or not stop_event.is_set():
        try:
            WORLD.tick()
            SIMULATION_LAST_TICK = time.monotonic()
        except Exception:
            logging.exception('Unexpected simulation loop failure; retrying next tick')
        deadline += 0.05
        if deadline < time.monotonic() - 0.1:
            deadline = time.monotonic()
        wait = max(0, deadline - time.monotonic())
        if stop_event is None:
            time.sleep(wait)
        else:
            stop_event.wait(wait)

def main() -> None:
    host = os.environ.get('HOST', '::')
    port = int(os.environ.get('PORT', '8000'))
    server_class = DualStackThreadingHTTPServer if ':' in host else ThreadingHTTPServer
    server = server_class((host, port), Handler)
    threading.Thread(target=_simulation_loop, daemon=True).start()
    print(f'The Gauntlet listening on port {port} (open http://localhost:{port} on this computer)')
    print('Press Ctrl+C to stop.')
    server.serve_forever()
if __name__ == '__main__':
    main()
