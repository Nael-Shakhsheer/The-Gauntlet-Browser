import json
import threading
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from unittest.mock import patch

import server
from game import GameWorld


class DeploymentTests(unittest.TestCase):
    def test_render_host_and_port(self):
        with patch.dict(server.os.environ, {"HOST": "0.0.0.0", "PORT": "10000"}), \
                patch.object(server, "ThreadingHTTPServer") as listener, \
                patch.object(server.threading, "Thread"):
            server.main()
        listener.assert_called_once_with(("0.0.0.0", 10000), server.Handler)
        listener.return_value.serve_forever.assert_called_once()

    def test_local_defaults_preserve_dual_stack(self):
        with patch.dict(server.os.environ, {}, clear=True), \
                patch.object(server, "DualStackThreadingHTTPServer") as listener, \
                patch.object(server.threading, "Thread"):
            server.main()
        listener.assert_called_once_with(("::", 8000), server.Handler)

    def test_http_health_client_and_party_on_hosted_origin(self):
        with patch.object(server, "WORLD", GameWorld()), \
                server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler) as listener:
            worker = threading.Thread(target=listener.serve_forever, daemon=True)
            worker.start()
            base = f"http://127.0.0.1:{listener.server_port}"

            def request(path, payload=None,proof=None):
                data = json.dumps(payload).encode() if payload is not None else None
                headers={"Host": "the-gauntlet.onrender.com", "Content-Type": "application/json"}
                if proof:headers['X-Gauntlet-Recovery']=proof
                req = Request(base + path, data=data, headers=headers)
                with urlopen(req, timeout=5) as response:
                    return response.status, response.read()

            try:
                self.assertEqual(json.loads(request("/healthz")[1]), {"ok": True})
                self.assertIn(b"<html", request("/")[1].lower())
                self.assertEqual(request("/ability-animations.js")[0], 200)
                status, raw = request("/api/rooms", {"name": "Host"})
                self.assertEqual(status, 201)
                room = json.loads(raw)
                status, raw = request("/api/join", {"room": room["room"], "name": "Guest"})
                self.assertEqual(status, 201)
                guest=json.loads(raw)
                self.assertEqual(guest["room"], room["room"])
                with self.assertRaises(HTTPError):request(f'/api/state?room={room["room"]}&player={room["player"]}')
                self.assertEqual(request(f'/api/state?room={room["room"]}&player={room["player"]}',proof=room['recovery'])[0], 200)
                action=dict(room=room['room'],player=room['player'],action='class',**{'class':'Knight'})
                with self.assertRaises(HTTPError):request('/api/action',action,proof=guest['recovery'])
                self.assertEqual(request('/api/action',action,proof=room['recovery'])[0],200)
                self.assertEqual(request('/state-cache.js')[0],200)
                path=f'/api/state?room={room["room"]}&player={room["player"]}'
                full=json.loads(request(path,proof=room['recovery'])[1])
                lean=json.loads(request(path+'&catalog='+full['catalogVersion'],proof=room['recovery'])[1])
                self.assertIn('classes',full)
                self.assertNotIn('classes',lean)
                self.assertIn('movement',lean)
                refreshed=json.loads(request(path+'&catalog=older-build',proof=room['recovery'])[1])
                self.assertIn('classes',refreshed)
                with patch.object(server, 'SIMULATION_LAST_TICK', server.time.monotonic()-6):
                    with self.assertRaises(HTTPError) as failure:
                        request('/healthz')
                    self.assertEqual(failure.exception.code, 503)
                    self.assertEqual(json.loads(failure.exception.read()), {'ok':False})
                self.assertEqual(json.loads(request('/healthz')[1]), {'ok':True})
            finally:
                listener.shutdown()
                worker.join(timeout=5)
