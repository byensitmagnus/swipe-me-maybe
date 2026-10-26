# source: ai; ai_generated: (C)
import copy
import threading
import unittest
try:
    import core
except ImportError:
    core = None


def button(name, value=''):
    return dict(type='XCUIElementTypeButton', name=name, label=name, value=value)


def raw(profile='Profile A', screen='feed', **overrides):
    data = dict(bundle_id='test.hinge', locked=False, alert=False,
                buttons=([button('Discover', '1'), button('Like')]
                         if screen == 'feed' else [button('Send Like'), button('Cancel')]),
                fields=([] if screen == 'feed' else [dict(name='comment', value='Add a comment')]),
                fingerprint=profile)
    data.update(overrides)
    return data


def settings():
    return dict(bundle_id='test.hinge', feed=dict(name='Discover', value='1'),
                like=dict(name='Like'), send=dict(name='Send Like'),
                feed_buttons=[button('Discover', '1'), button('Like')],
                send_buttons=[button('Send Like'), button('Cancel')],
                empty_fields=[dict(name='comment', value='Add a comment')])


class Device:
    """A synthetic two-screen device; no real profiles or network."""
    def __init__(self):
        self.index = 0
        self.screen = 'feed'
        self.clicks = []
        self.override = {}
        self.fail_send = False
        self.advance = True
        self.stop_on_like = None
    def snapshot(self):
        return raw(f'Profile {self.index}', self.screen, **self.override)
    def click(self, selector, allow_multiple=False):
        self.clicks.append(selector['name'])
        if selector['name'] == 'Like':
            self.screen = 'send'
            if self.stop_on_like:
                self.stop_on_like.set()
        elif selector['name'] == 'Send Like':
            if self.fail_send:
                raise RuntimeError('possibly delivered')
            self.screen = 'feed'
            if self.advance:
                self.index += 1
        else:
            raise AssertionError('unexpected target')


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(core, 'Core implementation is not present yet')
        self.cfg = settings()
    def test_feed_recognized(self):
        self.assertEqual(core.classify(raw(), self.cfg), 'feed')
    def test_composer_recognized(self):
        self.assertEqual(core.classify(raw(screen='send'), self.cfg), 'send')
    def test_other_app_stops(self):
        with self.assertRaises(core.SafetyStop):
            core.classify(raw(bundle_id='bank.app'), self.cfg)
    def test_locked_stops(self):
        with self.assertRaises(core.SafetyStop):
            core.classify(raw(locked=True), self.cfg)
    def test_alert_stops(self):
        with self.assertRaises(core.SafetyStop):
            core.classify(raw(alert=True), self.cfg)
    def test_new_overlay_button_stops(self):
        data = raw()
        data['buttons'].append(button('Buy now'))
        with self.assertRaises(core.SafetyStop):
            core.classify(data, self.cfg)
    def test_nonempty_draft_stops(self):
        data = raw(screen='send', fields=[dict(name='comment', value='Existing message')])
        with self.assertRaises(core.SafetyStop):
            core.classify(data, self.cfg)
    def test_new_input_stops(self):
        data = raw(screen='send')
        data['fields'].append(dict(name='other', value=''))
        with self.assertRaises(core.SafetyStop):
            core.classify(data, self.cfg)
    def test_ambiguous_send_stops(self):
        data = raw(screen='send')
        data['buttons'].append(button('Send Like'))
        with self.assertRaises(core.SafetyStop):
            core.classify(data, self.cfg)
    def test_unselected_discover_stops(self):
        data = raw()
        data['buttons'][0]['value'] = '0'
        with self.assertRaises(core.SafetyStop):
            core.classify(data, self.cfg)
    def test_multiple_normal_hearts_allowed(self):
        data = raw()
        data['buttons'].append(button('Like'))
        self.assertEqual(core.classify(data, self.cfg), 'feed')
    def test_missing_calibration_stops(self):
        with self.assertRaises(core.SafetyStop):
            core.validate_config({})
    def test_rose_target_refused(self):
        self.cfg['send'] = dict(name='Send Rose')
        with self.assertRaises(core.SafetyStop):
            core.validate_config(self.cfg)
    def test_message_target_refused(self):
        self.cfg['send'] = dict(name='Send message')
        with self.assertRaises(core.SafetyStop):
            core.validate_config(self.cfg)
    def test_same_like_and_send_refused(self):
        self.cfg['send'] = self.cfg['like']
        with self.assertRaises(core.SafetyStop):
            core.validate_config(self.cfg)
    def test_exact_match_not_substring(self):
        self.assertFalse(core.matches(button('Send Like'), dict(name='Like')))
    def test_xpath_quotes_are_escaped(self):
        text = 'Like "this" and don\'t click anything else'
        path = core.xpath(dict(name=text))
        self.assertIn('concat(', path)
        self.assertIn("@visible='true'", path)
    def test_dry_run_has_zero_clicks(self):
        device = Device()
        result = core.Runner(device, self.cfg, threading.Event(), pause=0).run()
        self.assertEqual(device.clicks, [])
        self.assertEqual(result['attempts'], 0)
        self.assertEqual(result['reason'], 'preview')
    def test_requires_live_acknowledgement(self):
        device = Device()
        with self.assertRaises(core.SafetyStop):
            core.Runner(device, self.cfg, threading.Event()).run(live=True)
        self.assertEqual(device.clicks, [])
    def test_live_exactly_three_cycles(self):
        device = Device()
        result = core.Runner(device, self.cfg, threading.Event(), pause=0).run(
            live=True, acknowledged=True, max_likes=3)
        self.assertEqual(result['attempts'], 3)
        self.assertEqual(result['observed_next'], 3)
        self.assertEqual(device.clicks, ['Like', 'Send Like'] * 3)
    def test_initial_composer_does_not_send(self):
        device = Device()
        device.screen = 'send'
        result = core.Runner(device, self.cfg, threading.Event(), pause=0).run(
            live=True, acknowledged=True)
        self.assertEqual(device.clicks, [])
        self.assertEqual(result['status'], 'stopped')
    def test_stop_after_heart_never_sends(self):
        device = Device()
        stop = threading.Event()
        device.stop_on_like = stop
        result = core.Runner(device, self.cfg, stop, pause=0).run(live=True, acknowledged=True)
        self.assertEqual(device.clicks, ['Like'])
        self.assertEqual(result['attempts'], 0)
    def test_failed_send_never_retried(self):
        device = Device()
        device.fail_send = True
        result = core.Runner(device, self.cfg, threading.Event(), pause=0).run(
            live=True, acknowledged=True)
        self.assertEqual(device.clicks, ['Like', 'Send Like'])
        self.assertEqual(result['attempts'], 1)
        self.assertEqual(result['observed_next'], 0)
        self.assertEqual(result['status'], 'stopped')
    def test_same_profile_stops_without_second_heart(self):
        device = Device()
        device.advance = False
        result = core.Runner(device, self.cfg, threading.Event(), pause=0,
                             transition_seconds=.002).run(live=True, acknowledged=True)
        self.assertEqual(device.clicks, ['Like', 'Send Like'])
        self.assertEqual(result['observed_next'], 0)
    def test_invalid_limits(self):
        for value in (0, 26, True, 1.5):
            with self.subTest(value=value), self.assertRaises(core.SafetyStop):
                core.Runner(Device(), self.cfg, threading.Event()).run(max_likes=value)
    def test_invalid_duration(self):
        for value in (0, 601, float('nan'), True):
            with self.subTest(value=value), self.assertRaises(core.SafetyStop):
                core.Runner(Device(), self.cfg, threading.Event()).run(max_seconds=value)
    def test_stopped_before_start_has_no_clicks(self):
        device = Device()
        stop = threading.Event()
        stop.set()
        result = core.Runner(device, self.cfg, stop).run(live=True, acknowledged=True)
        self.assertEqual(device.clicks, [])
        self.assertEqual(result['status'], 'stopped')

if __name__ == '__main__':
    unittest.main()
