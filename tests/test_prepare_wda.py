# source: ai; ai_generated: (C)
from pathlib import Path
import plistlib
import stat
import tempfile
import unittest
import zipfile
from unittest.mock import patch

try:
    from prepare_wda import package_wda
except ImportError:
    package_wda = None


class PrepareWdaTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(package_wda, 'Unsigned WDA packaging is missing')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.app = self.root / 'SyntheticRunner.app'
        self.app.mkdir()
        (self.app / 'Info.plist').write_bytes(plistlib.dumps({
            'CFBundleExecutable': 'SyntheticRunner',
            'CFBundleSupportedPlatforms': ['iPhoneOS']}))
        (self.app / 'SyntheticRunner').write_bytes(b'\xcf\xfa\xed\xfeSYNTHETIC')
        self.output = self.root / 'public-test.ipa'

    def test_packages_payload_and_preserves_executable_permission(self):
        package_wda(self.app, self.output)
        with zipfile.ZipFile(self.output) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(set(archive.namelist()), {
                'Payload/SyntheticRunner.app/Info.plist',
                'Payload/SyntheticRunner.app/SyntheticRunner'})
            entry = archive.getinfo('Payload/SyntheticRunner.app/SyntheticRunner')
            self.assertTrue((entry.external_attr >> 16) & stat.S_IXUSR)

    def test_refuses_existing_output_without_overwriting(self):
        self.output.write_bytes(b'EXISTING OWNER FILE')
        with self.assertRaises(FileExistsError):
            package_wda(self.app, self.output)
        self.assertEqual(self.output.read_bytes(), b'EXISTING OWNER FILE')

    def test_refuses_provisioned_input_before_writing_output(self):
        for name in ['embedded.mobileprovision', 'signing.pem', 'signing.crt', 'signing.pfx']:
            with self.subTest(name=name):
                marker = self.app / name
                output = self.root / (name + '.ipa')
                marker.write_bytes(b'SYNTHETIC MARKER')
                try:
                    with self.assertRaises(ValueError):
                        package_wda(self.app, output)
                    self.assertFalse(output.exists())
                finally:
                    marker.unlink()

    def test_refuses_executable_path_outside_bundle(self):
        (self.app / 'Info.plist').write_bytes(plistlib.dumps({
            'CFBundleExecutable': '../outside', 'CFBundleSupportedPlatforms': ['iPhoneOS']}))
        with self.assertRaises(ValueError):
            package_wda(self.app, self.output)
        self.assertFalse(self.output.exists())

    def test_refuses_windows_drive_relative_executable(self):
        (self.app / 'Info.plist').write_bytes(plistlib.dumps({
            'CFBundleExecutable': 'D:outside', 'CFBundleSupportedPlatforms': ['iPhoneOS']}))
        # Model an existing external file without touching another drive.
        with patch.object(Path, 'is_file', return_value=True):
            with self.assertRaises(ValueError):
                package_wda(self.app, self.output)
        self.assertFalse(self.output.exists())
