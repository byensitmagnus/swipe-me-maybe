# source: ai; ai_generated: (C)
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
try:
    import bridge
except ImportError:
    bridge = None

XML = '''<AppiumAUT><XCUIElementTypeApplication visible="true">
<XCUIElementTypeStatusBar visible="true"><XCUIElementTypeStaticText visible="true" label="CLOCK"/></XCUIElementTypeStatusBar>
<XCUIElementTypeStaticText visible="true" label="SYNTHETIC PROFILE"/>
<XCUIElementTypeButton type="XCUIElementTypeButton" visible="true" enabled="true" name="Like" label="Like"/>
<XCUIElementTypeButton type="XCUIElementTypeButton" visible="false" enabled="true" name="Hidden"/>
</XCUIElementTypeApplication></AppiumAUT>'''

class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(bridge, 'Bridge implementation is not present yet')
    def test_visible_buttons_only(self):
        parsed = bridge.parse_source(XML, b'session-key')
        self.assertEqual([b['name'] for b in parsed['buttons']], ['Like'])
    def test_clock_does_not_change_profile_fingerprint(self):
        a = bridge.parse_source(XML, b'k')
        b = bridge.parse_source(XML.replace('CLOCK', '11:00'), b'k')
        self.assertEqual(a['fingerprint'], b['fingerprint'])
    def test_new_profile_changes_fingerprint(self):
        a = bridge.parse_source(XML, b'k')
        b = bridge.parse_source(XML.replace('SYNTHETIC PROFILE', 'NEXT PROFILE'), b'k')
        self.assertNotEqual(a['fingerprint'], b['fingerprint'])
    def test_fingerprint_is_session_scoped(self):
        self.assertNotEqual(bridge.parse_source(XML, b'a')['fingerprint'],
                            bridge.parse_source(XML, b'b')['fingerprint'])
    def test_no_content_is_not_a_profile(self):
        self.assertEqual(bridge.parse_source('<AppiumAUT/>', b'k')['fingerprint'], '')
    def test_doctype_rejected(self):
        with self.assertRaises(Exception):
            bridge.parse_source('<!DOCTYPE x><AppiumAUT/>', b'k')
    def test_alert_detected(self):
        xml = XML.replace('</AppiumAUT>', '<XCUIElementTypeAlert visible="true"/></AppiumAUT>')
        self.assertTrue(bridge.parse_source(xml, b'k')['alert'])
    def test_disabled_button_not_actionable(self):
        self.assertEqual(bridge.parse_source(XML.replace('enabled="true"', 'enabled="false"'), b'k')['buttons'], [])
    def test_only_local_server_accepted(self):
        for url in ('http://example.com:4723', 'http://127.0.0.1.evil:4723',
                    'http://127.0.0.1:4723@evil.com', 'file:///tmp/x'):
            with self.subTest(url=url), self.assertRaises(Exception):
                bridge.Bridge(url)
    def test_valid_loopback_url(self):
        self.assertEqual(bridge.Bridge('http://127.0.0.1:4723').base_url,
                         'http://127.0.0.1:4723')
    def test_hides_profile_data_in_http_errors_and_no_retry(self):
        calls = []
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                calls.append(self.path)
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b'{"value":{"error":"unknown error","message":"PRIVATE PROFILE TEXT"}}')
            def log_message(self, *args):
                pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            driver = bridge.Bridge(f'http://127.0.0.1:{server.server_port}')
            with self.assertRaises(Exception) as result:
                driver.request('POST', '/session', {})
            self.assertNotIn('PRIVATE', str(result.exception))
            self.assertEqual(calls, ['/session'])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
    def test_connect_sends_safe_capabilities(self):
        driver = bridge.Bridge()
        calls = []
        def request(method, path, body=None, timeout=None):
            calls.append((method, path, body))
            return {'sessionId': 'test-session'}
        driver.request = request
        driver.connect({'udid': 'test-phone', 'team_id': 'ABC1234567',
                        'wda_bundle_id': 'test.local.WebDriverAgentRunner'})
        caps = calls[0][2]['capabilities']['alwaysMatch']
        self.assertFalse(caps['appium:autoLaunch'])
        self.assertTrue(caps['appium:noReset'])
        self.assertTrue(caps['appium:disableAutomaticScreenshots'])
        self.assertFalse(caps['appium:autoAcceptAlerts'])
        self.assertNotIn('appium:app', caps)
    def test_connect_without_udid_fails_before_network(self):
        with self.assertRaises(Exception):
            bridge.Bridge().connect({})

if __name__ == '__main__':
    unittest.main()

class AdditionalBridgeTests(unittest.TestCase):
    def test_stop_while_resolving_target_prevents_dispatch(self):
        driver = bridge.Bridge()
        driver.session_id = 'session'
        driver.expected_bundle = 'test.hinge'
        stop = threading.Event()
        driver.cancelled = stop.is_set
        writes = []
        def request(method, path, body=None, timeout=None):
            if path.endswith('/elements'):
                return [{'element-6066-11e4-a52e-4f735466cecf': 'button'}]
            writes.append(path)
        def execute(name):
            if name == 'isLocked':
                return False
            stop.set()
            return {'bundleId': 'test.hinge'}
        driver.request, driver.execute = request, execute
        with self.assertRaises(Exception):
            driver.click({'name': 'Send Like'})
        self.assertEqual(writes, [])
    def test_redirect_cannot_forward_request_to_another_server(self):
        calls = []
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                calls.append(self.path)
                self.send_response(307)
                self.send_header('Location', '/unexpected')
                self.end_headers()
            def log_message(self, *args):
                pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with self.assertRaises(Exception):
                bridge.Bridge(f'http://127.0.0.1:{server.server_port}').request('POST', '/session', {})
            self.assertEqual(calls, ['/session'])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
