import unittest
from unittest.mock import patch
from bridge import Bridge
from core import SafetyStop, validate_config
from demo import config


class WindowsSessionTests(unittest.TestCase):
    def settings(self, **kwargs):
        return dict(udid='synthetic-phone', connection_mode='windows-preinstalled',
                    platform_version='26.6', wda_bundle_id='local.test.WebDriverAgentRunner', **kwargs)

    def test_windows_uses_preinstalled_wda_without_xcode_signing(self):
        driver = Bridge()
        with patch.object(driver, 'request', return_value={'sessionId': 'synthetic'}) as request:
            driver.connect(self.settings(team_id='ABC1234567'))
        caps = request.call_args.args[2]['capabilities']['alwaysMatch']
        self.assertTrue(caps.get('appium:usePreinstalledWDA'))
        self.assertEqual(caps['appium:platformVersion'], '26.6')
        self.assertNotIn('appium:xcodeOrgId', caps)
        self.assertNotIn('appium:updatedWDABundleIdSuffix', caps)

    def test_windows_uses_exact_installed_bundle_without_appending_suffix(self):
        settings = self.settings()
        settings['wda_bundle_id'] = 'local.test.WebDriverAgentRunner.xctrunner.synthetic'
        settings['wda_bundle_id_exact'] = True
        driver = Bridge()
        with patch.object(driver, 'request', return_value={'sessionId': 'synthetic'}) as request:
            driver.connect(settings)
        caps = request.call_args.args[2]['capabilities']['alwaysMatch']
        self.assertEqual(caps['appium:updatedWDABundleId'], settings['wda_bundle_id'])
        self.assertEqual(caps.get('appium:updatedWDABundleIdSuffix'), '')

    def test_missing_windows_prerequisites_rejected_before_session(self):
        for key, value in [('platform_version', ''), ('platform_version', '17.7'),
                           ('platform_version', 'unknown'), ('wda_bundle_id', '')]:
            with self.subTest(key=key, value=value):
                settings = self.settings()
                settings[key] = value
                driver = Bridge()
                with patch.object(driver, 'request') as request:
                    with self.assertRaises(SafetyStop):
                        driver.connect(settings)
                    request.assert_not_called()

    def test_unknown_mode_rejected(self):
        settings = self.settings()
        settings['connection_mode'] = 'unknown'
        with patch.object(Bridge, 'request') as request:
            with self.assertRaises(SafetyStop):
                Bridge().connect(settings)
            request.assert_not_called()

    def test_priority_send_from_screenshot_is_not_ordinary_like(self):
        for label in ['Send prioriteret synes godt om', 'Send Priority Like']:
            with self.subTest(label=label):
                settings = config()
                settings['send'] = {'name': label}
                settings['send_buttons'] = [{'name': label}]
                with self.assertRaises(SafetyStop):
                    validate_config(settings)
