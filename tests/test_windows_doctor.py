# source: ai; ai_generated: (C)
import json
import subprocess
import unittest
from unittest.mock import patch

try:
    import windows_doctor
except ImportError:
    windows_doctor = None


class WindowsDoctorTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(windows_doctor, 'Windows prerequisite check is missing')

    def command(self, *args, **kwargs):
        if args == ('--version',):
            return '3.8.0'
        if args == ('driver', 'list', '--installed', '--json'):
            return json.dumps({'xcuitest': {'version': '12.20.0'}})
        if args[:2] == ('driver', 'run'):
            if '--json' not in args:
                return 'list-real-devices successfully ran'
            return json.dumps({'output': [
                '[Lister] 1 unique device (1 entry via usbmux, connection=wired).',
                'PRIVATE-DEVICE-ID']})
        raise RuntimeError('Unavailable command (including Xcode)')

    def test_windows_software_does_not_require_xcode(self):
        with patch.object(windows_doctor, 'command', side_effect=self.command):
            result = windows_doctor.check(software_only=True)
        self.assertTrue(result['ok'])
        self.assertEqual([c['key'] for c in result['checks']], ['appium', 'xcuitest'])
        self.assertFalse(result['device_ready'])

    def test_usb_presence_does_not_claim_wda_or_tunnel_ready(self):
        with patch.object(windows_doctor, 'command', side_effect=self.command):
            result = windows_doctor.check()
        self.assertTrue(result['ok'])
        self.assertFalse(result['device_ready'])
        self.assertEqual(result['checks'][-1]['key'], 'usb')
        self.assertNotIn('PRIVATE', json.dumps(result))

    def test_device_count_logging_is_available_to_private_parser(self):
        def run(args, **kwargs):
            if 'list-real-devices' in args and kwargs['env'].get('APPIUM_IOS_REMOTEXPC_LOG_LEVEL') == 'error':
                output = '{"output": []}'
            else:
                output = self.command(*args[1:])
            return subprocess.CompletedProcess(args, 0, output, '')
        with patch.object(windows_doctor.subprocess, 'run', side_effect=run):
            result = windows_doctor.check()
        self.assertTrue(result['ok'])
        self.assertNotIn('PRIVATE', json.dumps(result))

    def test_no_usb_device_is_actionable_failure(self):
        def command(*args, **kwargs):
            if args[:2] == ('driver', 'run'):
                return json.dumps({'output': ['[Lister] 0 unique devices (0 entries via usbmux, connection=wired).']})
            return self.command(*args, **kwargs)
        with patch.object(windows_doctor, 'command', side_effect=command):
            result = windows_doctor.check()
        self.assertFalse(result['ok'])
        self.assertIn('USB', result['checks'][-1]['message'])

    def test_missing_driver_does_not_report_success(self):
        def command(*args, **kwargs):
            return '{}' if args[:2] == ('driver', 'list') else self.command(*args, **kwargs)
        with patch.object(windows_doctor, 'command', side_effect=command):
            result = windows_doctor.check(software_only=True)
        self.assertFalse(result['ok'])

    def test_incompatible_or_unknown_driver_is_not_software_ready(self):
        for version in ['10.0.0', '12.19.0', '13.0.0', 'unknown']:
            def command(*args, **kwargs):
                if args[:2] == ('driver', 'list'):
                    return json.dumps({'xcuitest': {'version': version}})
                return self.command(*args, **kwargs)
            with self.subTest(version=version), patch.object(
                    windows_doctor, 'command', side_effect=command):
                result = windows_doctor.check(software_only=True)
            self.assertFalse(result['ok'])
            self.assertIn('12.20', result['checks'][-1]['message'])

    def test_failed_or_unknown_discovery_never_exposes_raw_output(self):
        for output in ['PRIVATE-DEVICE-ID', RuntimeError('PRIVATE-DEVICE-ID'),
                       subprocess.TimeoutExpired('PRIVATE-DEVICE-ID', 35)]:
            def command(*args, **kwargs):
                if args[:2] == ('driver', 'run'):
                    if isinstance(output, Exception):
                        raise output
                    return output
                return self.command(*args, **kwargs)
            with self.subTest(output=type(output).__name__), patch.object(
                    windows_doctor, 'command', side_effect=command):
                result = windows_doctor.check()
            self.assertFalse(result['ok'])
            self.assertNotIn('PRIVATE', json.dumps(result))


if __name__ == '__main__':
    unittest.main()
