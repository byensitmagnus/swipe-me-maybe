# source: ai; ai_generated: (C)
import json
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch
try:
    import app
except ImportError:
    app = None


class AppTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(app, 'Dashboard implementation is not present yet')
        self.tmp = tempfile.TemporaryDirectory()
        self.server = app.make_server(port=0, state_dir=self.tmp.name, demo=True)
        self.controller = self.server.controller
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f'http://127.0.0.1:{self.server.server_port}'
    def tearDown(self):
        if app is not None and hasattr(self, 'server'):
            self.controller.stop.set()
            self.server.shutdown()
            self.server.server_close()
            self.thread.join()
            self.tmp.cleanup()
    def req(self, path, body=None, token=True, origin=None):
        headers = {}
        if token:
            headers['X-Local-Token'] = self.server.token
        if origin:
            headers['Origin'] = origin
        data = None if body is None else json.dumps(body).encode()
        if data is not None:
            headers['Content-Type'] = 'application/json'
        with urllib.request.urlopen(urllib.request.Request(self.url + path, data=data, headers=headers), timeout=5) as result:
            return result.read()
    def test_page_has_no_external_scripts(self):
        page = self.req('/').decode()
        self.assertIn('dashboard.js', page)
        self.assertNotIn('https://cdn', page)
    def test_state_requires_token(self):
        with self.assertRaises(urllib.error.HTTPError) as result:
            self.req('/api/state', token=False)
        self.assertEqual(result.exception.code, 403)
    def test_cross_origin_is_blocked(self):
        with self.assertRaises(urllib.error.HTTPError) as result:
            self.req('/api/stop', {}, origin='https://evil.example')
        self.assertEqual(result.exception.code, 403)
    def test_unknown_host_is_blocked(self):
        request = urllib.request.Request(self.url + '/', headers={'Host': 'evil.example'})
        with self.assertRaises(urllib.error.HTTPError) as result:
            urllib.request.urlopen(request)
        self.assertEqual(result.exception.code, 403)
    def test_demo_is_explicit_and_preview_does_not_click(self):
        state = json.loads(self.req('/api/state'))
        self.assertTrue(state['demo'])
        result = json.loads(self.req('/api/preview', {}))
        self.assertEqual(result['attempts'], 0)
        self.assertEqual(self.controller.device.clicks, [])
    def test_run_needs_explicit_acknowledgement(self):
        with self.assertRaises(urllib.error.HTTPError) as result:
            self.req('/api/start', {'max_likes': 1, 'max_seconds': 10})
        self.assertEqual(result.exception.code, 400)
        self.assertEqual(self.controller.device.clicks, [])
    def test_api_runs_exactly_two_complete_cycles(self):
        self.req('/api/start', {'acknowledged': True, 'max_likes': 2, 'max_seconds': 10})
        end = time.monotonic() + 4
        while time.monotonic() < end:
            state = json.loads(self.req('/api/state'))
            if not state['busy']:
                break
            time.sleep(.02)
        self.assertEqual(state['run']['observed_next'], 2)
        self.assertEqual(self.controller.device.clicks, ['Like', 'Send Like'] * 2)
    def test_inspection_has_no_profile_content_or_field_values(self):
        result = json.loads(self.req('/api/inspect', {}))
        self.assertIn('buttons', result)
        self.assertNotIn('fingerprint', result)
        self.assertNotIn('fields', result)
    def test_invalid_limits_fail_before_start(self):
        with self.assertRaises(urllib.error.HTTPError):
            self.req('/api/start', {'acknowledged': True, 'max_likes': 500, 'max_seconds': 10})
        self.assertEqual(self.controller.device.clicks, [])
    def test_stop_is_available_while_busy(self):
        self.req('/api/start', {'acknowledged': True, 'max_likes': 25, 'max_seconds': 10})
        self.req('/api/stop', {})
        time.sleep(.15)
        state = json.loads(self.req('/api/state'))
        self.assertEqual(state['run']['status'], 'stopped')
        self.assertLess(state['run']['attempts'], 25)
    def test_second_session_is_rejected(self):
        self.req('/api/start', {'acknowledged': True, 'max_likes': 25, 'max_seconds': 10})
        with self.assertRaises(urllib.error.HTTPError) as result:
            self.req('/api/start', {'acknowledged': True, 'max_likes': 1, 'max_seconds': 10})
        self.assertEqual(result.exception.code, 409)
    def test_stale_calibration_rejected(self):
        with self.assertRaises(urllib.error.HTTPError):
            self.req('/api/calibrate/feed', {'inspection_id': 'stale', 'marker': 0, 'like': 1})
    def test_full_manual_calibration_round_trip(self):
        # Use demonstration device, but exercise the real calibration and persistence path.
        self.controller.demo = False
        inspected = json.loads(self.req('/api/inspect', {}))
        self.req('/api/calibrate/feed', {'inspection_id': inspected['inspection_id'], 'marker': 0, 'like': 1})
        self.controller.device.screen = 'send'
        inspected = json.loads(self.req('/api/inspect', {}))
        with self.assertRaises(urllib.error.HTTPError):
            self.req('/api/calibrate/send', {'inspection_id': inspected['inspection_id'], 'send': 0})
        self.req('/api/calibrate/send', {'inspection_id': inspected['inspection_id'], 'send': 0, 'empty_confirmed': True})
        self.assertTrue(json.loads(self.req('/api/state'))['config_ready'])
        self.controller.device.screen = 'feed'
        self.assertEqual(json.loads(self.req('/api/preview', {}))['next_action'], 'feed')
    def test_private_files_not_served(self):
        with self.assertRaises(urllib.error.HTTPError) as result:
            self.req('/device.local.json')
        self.assertEqual(result.exception.code, 404)

    def test_saved_exact_wda_id_survives_browser_connect_form(self):
        self.controller.demo = False
        self.controller.device = None
        settings = dict(udid='synthetic-phone', connection_mode='windows-preinstalled',
                        platform_version='26.6', wda_bundle_id='local.test.WDA.synthetic')
        self.controller.settings = dict(settings, wda_bundle_id_exact=True)
        with patch('bridge.Bridge.request', return_value={'sessionId': 'synthetic'}):
            self.req('/api/connect', {'device': settings})
        self.assertIs(self.controller.settings.get('wda_bundle_id_exact'), True)

if __name__ == '__main__':
    unittest.main()
