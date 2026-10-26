# source: ai; ai_generated: (C)
"""Contract tests over real HTTP with a synthetic Appium server, NOT a real iPhone."""
import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from xml.sax.saxutils import escape
from app import Controller
from bridge import Bridge


class WireTests(unittest.TestCase):
    def setUp(self):
        self.screen = 'feed'
        self.profile = 0
        self.clicks = []
        self.fail_send = False
        outer = self
        class WireHandler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def send_value(self, value, status=200):
                body = json.dumps({'value': value}).encode()
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            def do_GET(self):
                if not self.path.endswith('/source'):
                    return self.send_value({'error': 'unknown command'}, 404)
                if outer.screen == 'feed':
                    controls = '<XCUIElementTypeButton type="XCUIElementTypeButton" visible="true" enabled="true" name="Discover" value="1"/><XCUIElementTypeButton type="XCUIElementTypeButton" visible="true" enabled="true" name="Like"/>'
                    fields = ''
                else:
                    controls = '<XCUIElementTypeButton type="XCUIElementTypeButton" visible="true" enabled="true" name="Send Like"/><XCUIElementTypeButton type="XCUIElementTypeButton" visible="true" enabled="true" name="Cancel"/>'
                    fields = '<XCUIElementTypeTextField type="XCUIElementTypeTextField" visible="true" name="comment" value="Add a comment"/>'
                self.send_value(f'<AppiumAUT><XCUIElementTypeApplication visible="true"><XCUIElementTypeStaticText visible="true" label="Synthetic {outer.profile}"/>{controls}{fields}</XCUIElementTypeApplication></AppiumAUT>')
            def do_POST(self):
                data = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                if self.path == '/session':
                    self.send_value({'sessionId': 'wire-session', 'capabilities': data['capabilities']['alwaysMatch']})
                elif self.path.endswith('/execute/sync'):
                    if data['script'] == 'mobile: isLocked':
                        self.send_value(False)
                    elif data['script'] == 'mobile: activeAppInfo':
                        self.send_value({'bundleId': 'wire.hinge'})
                    else:
                        self.send_value({'error': 'unknown command'}, 404)
                elif self.path.endswith('/elements'):
                    if "@name='Send Like'" in data['value']:
                        target = 'send'
                    elif "@name='Like'" in data['value']:
                        target = 'like'
                    else:
                        return self.send_value([])
                    self.send_value([{'element-6066-11e4-a52e-4f735466cecf': target}])
                elif self.path.endswith('/element/like/click'):
                    outer.clicks.append('like')
                    outer.screen = 'send'
                    self.send_value(None)
                elif self.path.endswith('/element/send/click'):
                    outer.clicks.append('send')
                    if outer.fail_send:
                        self.send_value({'error': 'unknown error', 'message': 'DO NOT LEAK'}, 500)
                    else:
                        outer.screen = 'feed'
                        outer.profile += 1
                        self.send_value(None)
                else:
                    self.send_value({'error': 'unknown command'}, 404)
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), WireHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.tmp = tempfile.TemporaryDirectory()
        self.controller = Controller(self.tmp.name)
        self.driver = Bridge(f'http://127.0.0.1:{self.server.server_port}')
        self.driver.connect({'udid': 'wire-phone'})
        self.controller.device = self.driver
        inspected = self.controller.action('/api/inspect', {})
        self.controller.action('/api/calibrate/feed', {'inspection_id': inspected['inspection_id'], 'marker': 0, 'like': 1})
        self.screen = 'send'  # Manual user action during calibration.
        inspected = self.controller.action('/api/inspect', {})
        self.controller.action('/api/calibrate/send', {'inspection_id': inspected['inspection_id'], 'send': 0, 'empty_confirmed': True})
        self.screen = 'feed'
    def tearDown(self):
        self.controller.stop.set()
        if self.controller.worker:
            self.controller.worker.join(timeout=5)
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.tmp.cleanup()
    def test_real_transport_calibration_preview_and_two_cycles(self):
        result = self.controller.action('/api/preview', {})
        self.assertEqual(result['next_action'], 'feed')
        self.assertEqual(self.clicks, [])
        self.controller.action('/api/start', {'acknowledged': True, 'max_likes': 2, 'max_seconds': 20})
        self.controller.worker.join(timeout=10)
        self.assertFalse(self.controller.worker.is_alive())
        result = self.controller.state()['run']
        self.assertEqual(result['status'], 'finished')
        self.assertEqual(result['observed_next'], 2)
        self.assertEqual(self.clicks, ['like', 'send', 'like', 'send'])
    def test_http_send_failure_never_retried(self):
        self.fail_send = True
        self.controller.action('/api/start', {'acknowledged': True, 'max_likes': 3, 'max_seconds': 20})
        self.controller.worker.join(timeout=10)
        result = self.controller.state()['run']
        self.assertEqual(result['status'], 'stopped')
        self.assertEqual(result['attempts'], 1)
        self.assertEqual(result['observed_next'], 0)
        self.assertNotIn('DO NOT LEAK', result['reason'])
        self.assertEqual(self.clicks, ['like', 'send'])
