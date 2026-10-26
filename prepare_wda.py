# source: ai; ai_generated: (C)
"""Package an unsigned, public iPhone WDA .app as an IPA for owner signing."""
from __future__ import annotations

import argparse
from pathlib import Path
import plistlib
import stat
import zipfile

MACHO = (b'\xcf\xfa\xed\xfe', b'\xfe\xed\xfa\xcf', b'\xca\xfe\xba\xbe', b'\xbe\xba\xfe\xca',
         b'\xca\xfe\xba\xbf', b'\xbf\xba\xfe\xca')


def package_wda(source: Path, output: Path) -> int:
    source, output = Path(source), Path(output)
    if output.exists():
        raise FileExistsError('IPA-filen findes allerede og bliver ikke overskrevet.')
    if source.is_symlink() or not source.is_dir() or source.suffix != '.app':
        raise ValueError('Vælg den offentlige, usignerede WebDriverAgent .app-mappe.')
    files = []
    for path in sorted(source.rglob('*')):
        if path.is_symlink():
            raise ValueError('Symbolske links accepteres ikke i denne WDA-pakke.')
        if path.is_file():
            if path.suffix.lower() in ('.mobileprovision', '.p12', '.key', '.cer', '.pem', '.crt', '.pfx'):
                raise ValueError('Brug den usignerede pakke uden profiler eller certifikater.')
            files.append(path)
    info = plistlib.loads((source / 'Info.plist').read_bytes())
    executable = info.get('CFBundleExecutable')
    if (not isinstance(executable, str) or not executable or executable in ('.', '..')
            or '/' in executable or '\\' in executable or ':' in executable
            or 'iPhoneOS' not in info.get('CFBundleSupportedPlatforms', [])):
        raise ValueError('Pakken er ikke en gyldig iPhone-app.')
    if not (source / executable).is_file():
        raise ValueError('WDA-programfilen mangler.')
    output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    created = False
    try:
        with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
            created = True
            for path in files:
                data = path.read_bytes()
                entry = zipfile.ZipInfo('Payload/' + source.name + '/' + path.relative_to(source).as_posix())
                entry.create_system = 3
                permissions = 0o755 if data[:4] in MACHO else 0o644
                entry.external_attr = (stat.S_IFREG | permissions) << 16
                entry.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(entry, data)
        with zipfile.ZipFile(output) as archive:
            if archive.testzip() is not None:
                raise ValueError('IPA-integritetskontrollen fejlede.')
    except Exception:
        if created:
            output.unlink(missing_ok=True)
        raise
    return len(files)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parent / '.local/WebDriverAgent.ipa')
    args = parser.parse_args()
    try:
        count = package_wda(args.source, args.output)
    except (OSError, ValueError, plistlib.InvalidFileException) as error:
        parser.exit(1, f'{error}\n')
    print(f'IPA klargjort: {count} filer. Appen er ikke signeret eller installeret.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
