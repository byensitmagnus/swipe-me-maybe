# source: ai; ai_generated: (C)
"""Local-only dashboard. Run: python3 app.py [--demo] [--no-browser]."""
from __future__ import annotations

import argparse
import copy
import json
import math
import os
from pathlib import Path
import secrets
import tempfile
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from bridge import Bridge
from core import Runner, SafetyStop, matches, selector_for, validate_config
from demo import DemoDevice, config as demo_config

ROOT = Path(__file__).resolve().parent


class Busy(SafetyStop):
    pass


def load_local(path: Path) -> dict:
    try:
        result = json.loads(path.read_text('utf-8'))
        return result if isinstance(result, dict) else {}
    except (OSError, ValueError):
        return {}


def save_local(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix='.write-')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class Controller:
    def __init__(self, state_dir: str | Path, demo: bool = False):
        self.directory = Path(state_dir)
        self.demo = demo
        self.settings = {} if demo else load_local(self.directory / 'device.local.json')
        self.config = demo_config() if demo else load_local(self.directory / 'selectors.local.json')
        self.device = DemoDevice() if demo else None
        self.operation = threading.Lock()
        self.state_lock = threading.Lock()
        self.stop = threading.Event()
        self.worker = None
        self.inspection = None
        self.inspection_id = ''
        self.result = dict(status='idle', reason='Ingen session startet.', attempts=0, observed_next=0)
        if self.device:
            self.device.cancelled = self.stop.is_set

    def state(self) -> dict:
        with self.state_lock:
            try:
                validate_config(self.config)
                ready = True
            except SafetyStop:
                ready = False
            return dict(demo=self.demo, connected=bool(self.device and self.device.session_id),
                        busy=self.operation.locked(), config_ready=ready,
                        calibrated_feed=bool(self.config.get('feed')),
                        bundle_id=self.config.get('bundle_id', ''),
                        device=copy.deepcopy(self.settings), run=copy.deepcopy(self.result))

    def _progress(self, result):
        with self.state_lock:
            self.result = dict(result)

    def _require_device(self):
        if not self.device or not self.device.session_id:
            raise SafetyStop('Forbind iPhonen først.')
        return self.device

    def _inspect(self) -> dict:
        snapshot = self._require_device().snapshot()
        self.inspection = snapshot
        self.inspection_id = secrets.token_urlsafe(16)
        return dict(inspection_id=self.inspection_id, bundle_id=snapshot['bundle_id'],
                    buttons=snapshot['buttons'], input_count=len(snapshot['fields']),
                    alert=snapshot['alert'], locked=snapshot['locked'])

    def _calibrate(self, role: str, data: dict) -> dict:
        if not self.inspection or data.get('inspection_id') != self.inspection_id:
            raise SafetyStop('Aflæs den aktuelle skærm igen før kalibrering.')
        current = self._require_device().snapshot()
        for key in ('bundle_id', 'buttons', 'fields', 'alert', 'locked'):
            if current[key] != self.inspection[key]:
                raise SafetyStop('Skærmen er ændret siden aflæsningen. Aflæs igen.')
        if current['locked'] is not False or current['alert'] is not False:
            raise SafetyStop('Luk dialoger og lås telefonen op først.')
        if 'hinge' not in current['bundle_id'].lower():
            raise SafetyStop('V1 er afgrænset til Hinge. Åbn Hinge manuelt først.')
        buttons = current['buttons']

        def select(key: str, selected=False):
            index = data.get(key)
            if type(index) is not int or not 0 <= index < len(buttons):
                raise SafetyStop('Vælg en knap fra den seneste aflæsning.')
            return selector_for(buttons[index], selected)

        candidate = copy.deepcopy(self.config)
        if role == 'feed':
            if current['fields']:
                raise SafetyStop('Start på profilsiden uden åbne inputfelter.')
            marker, like = select('marker', True), select('like')
            if marker == like or sum(matches(b, marker) for b in buttons) != 1:
                raise SafetyStop('Discover-markøren skal være entydig og forskellig fra hjertet.')
            candidate = dict(bundle_id=current['bundle_id'], feed=marker, like=like,
                             feed_buttons=buttons, device_udid=self.settings.get('udid', ''))
        elif role == 'send':
            if not candidate.get('feed') or candidate.get('bundle_id') != current['bundle_id']:
                raise SafetyStop('Kalibrér profilsiden i samme app først.')
            if data.get('empty_confirmed') is not True:
                raise SafetyStop('Bekræft, at kommentarfeltet er tomt. Ryd enhver kladde manuelt.')
            candidate.update(send=select('send'), send_buttons=buttons, empty_fields=current['fields'])
            validate_config(candidate)
        else:
            raise SafetyStop('Ukendt kalibreringstrin.')
        if not self.demo:
            save_local(self.directory / 'selectors.local.json', candidate)
        with self.state_lock:
            self.config = candidate
        self.device.expected_bundle = candidate['bundle_id']
        self.inspection = None
        return dict(ok=True, stage=role)

    def _connect(self, data: dict) -> dict:
        if self.demo:
            raise SafetyStop('Demoen kan ikke forbindes til en rigtig telefon. Start uden --demo.')
        if self.device and self.device.session_id:
            raise SafetyStop('Telefonen er allerede forbundet. Afbryd først for at skifte enhed.')
        settings = data.get('device')
        if not isinstance(settings, dict):
            raise SafetyStop('Indtast telefonens opsætning.')
        exact_bundle = settings.get('wda_bundle_id_exact')
        settings = {k: settings.get(k, '').strip() for k in
                    ('udid', 'team_id', 'wda_bundle_id', 'platform_version', 'connection_mode')
                    if isinstance(settings.get(k, ''), str)}
        if type(exact_bundle) is bool:
            settings['wda_bundle_id_exact'] = exact_bundle
        elif (self.settings.get('wda_bundle_id_exact') is True
              and self.settings.get('udid') == settings.get('udid')
              and self.settings.get('wda_bundle_id') == settings.get('wda_bundle_id')):
            settings['wda_bundle_id_exact'] = True
        device = Bridge()
        device.connect(settings)
        device.cancelled = self.stop.is_set
        if self.config.get('device_udid') != settings.get('udid'):
            self.config = {}
        device.expected_bundle = self.config.get('bundle_id')
        self.device, self.settings = device, settings
        save_local(self.directory / 'device.local.json', settings)
        self.inspection = None
        return dict(ok=True)

    def _start(self, data: dict) -> dict:
        self._require_device()
        validate_config(self.config)
        likes, seconds = data.get('max_likes', 5), data.get('max_seconds', 120)
        if data.get('acknowledged') is not True:
            raise SafetyStop('Bekræft live-tilstand og kontorisikoen først.')
        if type(likes) is not int or not 1 <= likes <= 25:
            raise SafetyStop('Antallet skal være et helt tal mellem 1 og 25.')
        if type(seconds) not in (int, float) or not math.isfinite(seconds) or not 1 <= seconds <= 600:
            raise SafetyStop('Varigheden skal være mellem 1 og 600 sekunder.')
        self.stop.clear()
        self._progress(dict(status='running', reason='Starter session.', attempts=0, observed_next=0))
        runner = Runner(self.device, copy.deepcopy(self.config), self.stop,
                        pause=.05 if self.demo else .5, progress=self._progress)
        self.device.cancelled = lambda: self.stop.is_set() or time.monotonic() >= runner.deadline

        def work():
            try:
                runner.run(live=True, acknowledged=True, max_likes=likes, max_seconds=seconds)
            except Exception:
                self._progress(dict(status='stopped', reason='Sessionen kunne ikke startes.', attempts=0, observed_next=0))
            finally:
                self.operation.release()

        self.worker = threading.Thread(target=work, daemon=True, name='bounded-session')
        self.worker.start()
        return dict(ok=True)

    def action(self, path: str, data: dict) -> dict:
        if path == '/api/stop':
            self.stop.set()
            return dict(ok=True, note='Stop anmodet. Et igangværende klik kan ikke trækkes tilbage.')
        if not self.operation.acquire(blocking=False):
            raise Busy('En handling er allerede i gang. Stop sessionen først.')
        handed_to_worker = False
        try:
            if path == '/api/start':
                result = self._start(data)
                handed_to_worker = True
                return result
            if path == '/api/connect':
                return self._connect(data)
            if path == '/api/disconnect':
                self.stop.set()
                if self.device:
                    self.device.close()
                self.device = None
                return dict(ok=True)
            if path == '/api/inspect':
                return self._inspect()
            if path.startswith('/api/calibrate/'):
                return self._calibrate(path.rsplit('/', 1)[1], data)
            if path == '/api/preview':
                self.stop.clear()
                return Runner(self._require_device(), self.config, self.stop,
                              progress=self._progress).run()
            raise SafetyStop('Ukendt handling.')
        finally:
            if not handed_to_worker:
                self.operation.release()


class Handler(BaseHTTPRequestHandler):
    server_version = 'LocalAssistant/0.1'

    def log_message(self, *args):
        pass  # No request/body/profile logging.

    def reply(self, status: int, body, content_type='application/json; charset=utf-8'):
        if isinstance(body, dict):
            body = json.dumps(body, ensure_ascii=False).encode('utf-8')
        elif isinstance(body, str):
            body = body.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        self.end_headers()
        self.wfile.write(body)

    def authorized(self, api=False):
        expected = f'127.0.0.1:{self.server.server_port}'
        if self.headers.get('Host') != expected:
            self.reply(403, {'error': 'Brug kontrolpanelets lokale 127.0.0.1-adresse.'})
            return False
        origin = self.headers.get('Origin')
        if (origin and origin != 'http://' + expected) or self.headers.get('Sec-Fetch-Site') == 'cross-site':
            self.reply(403, {'error': 'Forespørgsler fra andre hjemmesider er blokeret.'})
            return False
        if api and not secrets.compare_digest(self.headers.get('X-Local-Token', ''), self.server.token):
            self.reply(403, {'error': 'Genindlæs kontrolpanelet for at få en lokal session.'})
            return False
        return True

    def do_GET(self):
        if not self.authorized(self.path.startswith('/api/')):
            return
        if self.path == '/api/state':
            self.reply(200, self.server.controller.state())
            return
        static = {'/': ('dashboard.html', 'text/html; charset=utf-8'),
                  '/dashboard.js': ('dashboard.js', 'text/javascript; charset=utf-8'),
                  '/style.css': ('style.css', 'text/css; charset=utf-8')}
        if self.path not in static:
            self.reply(404, {'error': 'Ikke fundet.'})
            return
        filename, kind = static[self.path]
        body = (ROOT / filename).read_text('utf-8')
        if self.path == '/':
            body = body.replace('__LOCAL_TOKEN__', self.server.token)
        self.reply(200, body, kind)

    def do_POST(self):
        if not self.authorized(api=True):
            return
        try:
            if self.headers.get_content_type() != 'application/json':
                raise SafetyStop('Forventede JSON-data.')
            length = int(self.headers.get('Content-Length', '-1'))
            if not 0 < length <= 32768:
                raise SafetyStop('Ugyldig requeststørrelse.')
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise SafetyStop('Forventede et JSON-objekt.')
            result = self.server.controller.action(self.path, data)
            self.reply(200, result)
        except Busy as exc:
            self.reply(409, {'error': str(exc)})
        except SafetyStop as exc:
            self.reply(400, {'error': str(exc)})
        except (ValueError, TypeError, KeyError):
            self.reply(400, {'error': 'Ugyldige data. Kontrollér formularen.'})
        except Exception:
            self.reply(500, {'error': 'Lokal fejl. Sessionen er ikke automatisk gentaget.'})


def make_server(port: int = 8765, state_dir: str | Path = ROOT / '.local', demo=False):
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.token = secrets.token_urlsafe(32)
    server.controller = Controller(state_dir, demo)
    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true', help='Offline demonstration. Ingen iPhone-adgang.')
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    server = make_server(port=args.port, demo=args.demo)
    url = f'http://127.0.0.1:{server.server_port}'
    print(('DEMO — ingen telefon eller rigtige likes.\n' if args.demo else 'Kun lokal adgang. Live kræver eksplicit start.\n') + url)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nStopper. Et allerede sendt like kan ikke trækkes tilbage.')
    finally:
        controller = server.controller
        controller.stop.set()
        if controller.worker:
            controller.worker.join(timeout=25)
        if controller.device and controller.operation.acquire(blocking=False):
            try:
                controller.device.close()
            except Exception:
                pass
            finally:
                controller.operation.release()
        server.server_close()


if __name__ == '__main__':
    main()
