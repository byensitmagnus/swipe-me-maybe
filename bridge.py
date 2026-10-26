# source: ai; ai_generated: (C)
"""Minimal W3C/Appium transport. Only loopback; never retry a write."""
from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import socket
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from core import SafetyStop, xpath

MAX_BODY = 8 * 1024 * 1024


def parse_source(source: str, key: bytes) -> dict:
    if not isinstance(source, str) or len(source.encode('utf-8')) > MAX_BODY:
        raise SafetyStop('Skærmdata er ugyldige eller for store.')
    if '<!DOCTYPE' in source.upper() or '<!ENTITY' in source.upper():
        raise SafetyStop('Uventet XML-format.')
    try:
        root = ET.fromstring(source)
    except ET.ParseError:
        raise SafetyStop('Skærmens struktur kunne ikke læses.') from None
    buttons, fields, profile = [], [], []
    alert = False

    def walk(node, hidden=False):
        nonlocal alert
        kind = node.get('type', node.tag)
        hidden = hidden or node.get('visible') == 'false'
        if hidden or kind == 'XCUIElementTypeStatusBar':
            return
        visible = node.get('visible') == 'true'
        if visible and kind in ('XCUIElementTypeAlert', 'XCUIElementTypeSheet'):
            alert = True
        if visible and kind == 'XCUIElementTypeButton':
            if node.get('enabled') == 'true':
                buttons.append(dict(type=kind, **{k: node.get(k, '') for k in ('name', 'label', 'value')}))
            return  # Button titles do not identify the next profile.
        if visible and kind in ('XCUIElementTypeTextField', 'XCUIElementTypeTextView',
                                'XCUIElementTypeSecureTextField', 'XCUIElementTypeSearchField'):
            fields.append(dict(type=kind, **{k: node.get(k, '') for k in ('name', 'label', 'value')}))
            return
        if visible and kind in ('XCUIElementTypeStaticText', 'XCUIElementTypeImage'):
            content = [node.get(k, '') for k in ('name', 'label', 'value')]
            if any(content):
                profile.append([kind, *content])
        for child in node:
            walk(child, hidden)

    walk(root)
    digest = hmac.new(key, json.dumps(profile, ensure_ascii=False).encode(), hashlib.sha256).hexdigest() if profile else ''
    return dict(buttons=buttons, fields=fields, alert=alert, fingerprint=digest)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Bridge:
    def __init__(self, base_url: str = 'http://127.0.0.1:4723'):
        try:
            parsed = urllib.parse.urlsplit(base_url)
            valid = (parsed.scheme == 'http' and parsed.hostname in ('127.0.0.1', 'localhost', '::1')
                     and parsed.username is None and parsed.password is None
                     and not parsed.query and not parsed.fragment and parsed.path in ('', '/'))
            port = parsed.port
        except (ValueError, TypeError):
            valid = False
        if not valid or (port is not None and not 1 <= port <= 65535):
            raise SafetyStop('Appium skal køre på en lokal http-adresse uden sti eller login.')
        self.base_url = base_url.rstrip('/')
        self.session_id = None
        self.expected_bundle = None
        self.cancelled = lambda: False
        self.key = secrets.token_bytes(32)
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def request(self, method: str, path: str, body=None, timeout: float | None = None):
        if not path.startswith('/') or path.startswith('//'):
            raise SafetyStop('Ugyldig driversti.')
        data = None if body is None else json.dumps(body).encode('utf-8')
        req = urllib.request.Request(self.base_url + path, data=data, method=method,
                                     headers={'Content-Type': 'application/json; charset=utf-8'})
        try:
            with self.opener.open(req, timeout=timeout or 20) as response:
                raw = response.read(MAX_BODY + 1)
            if len(raw) > MAX_BODY:
                raise SafetyStop('Driversvaret er for stort.')
            payload = json.loads(raw)
            value = payload.get('value', payload)
            if isinstance(value, dict) and value.get('error'):
                raise SafetyStop('Appium afviste handlingen. Kontrollér driveren lokalt.')
            return value
        except urllib.error.HTTPError as exc:
            status = exc.code
            exc.close()
            raise SafetyStop(f'Appium returnerede HTTP {status}. Ingen automatisk gentagelse.') from None
        except (urllib.error.URLError, socket.timeout, TimeoutError, OSError, ValueError):
            raise SafetyStop('Ingen gyldig forbindelse til Appium. Sidste handling gentages ikke.') from None

    def connect(self, settings: dict) -> None:
        if self.session_id:
            raise SafetyStop('Driveren er allerede forbundet.')
        udid = settings.get('udid', '')
        if not isinstance(udid, str) or not re.fullmatch(r'[A-Za-z0-9-]{5,80}', udid):
            raise SafetyStop('Indtast din iPhones UDID fra Xcode først.')
        caps = {'platformName': 'iOS', 'appium:automationName': 'XCUITest',
                'appium:udid': udid, 'appium:noReset': True, 'appium:autoLaunch': False,
                'appium:shouldTerminateApp': False, 'appium:newCommandTimeout': 0,
                'appium:autoAcceptAlerts': False, 'appium:autoDismissAlerts': False,
                'appium:disableAutomaticScreenshots': True, 'appium:skipLogCapture': True,
                'appium:printPageSourceOnFindFailure': False, 'appium:waitForIdleTimeout': 1}
        mode = settings.get('connection_mode', 'mac')
        if mode not in ('mac', 'windows-preinstalled'):
            raise SafetyStop('Ukendt forbindelsestype.')
        version = settings.get('platform_version', '').strip()
        if mode == 'windows-preinstalled':
            if not re.fullmatch(r'\d+(?:\.\d+){0,2}', version) or int(version.split('.')[0]) < 18:
                raise SafetyStop('Windows kræver en angivet iOS-version på mindst 18.')
            if not settings.get('wda_bundle_id', '').strip():
                raise SafetyStop('Windows kræver bundle-id for den signerede, installerede WebDriverAgent.')
            caps['appium:usePreinstalledWDA'] = True
            if settings.get('wda_bundle_id_exact') is True:
                caps['appium:updatedWDABundleIdSuffix'] = ''
        team = settings.get('team_id', '').strip() if mode == 'mac' else ''
        bundle = settings.get('wda_bundle_id', '').strip()
        if team:
            if not re.fullmatch('[A-Z0-9]{10}', team):
                raise SafetyStop('Apple Team ID skal være 10 store bogstaver/tal.')
            caps.update({'appium:xcodeOrgId': team, 'appium:xcodeSigningId': 'Apple Development'})
        if bundle:
            if not re.fullmatch(r'[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+', bundle):
                raise SafetyStop('Ugyldigt WebDriverAgent bundle-id.')
            caps['appium:updatedWDABundleId'] = bundle
        if settings.get('platform_version'):
            caps['appium:platformVersion'] = settings['platform_version']
        value = self.request('POST', '/session', {'capabilities': {'alwaysMatch': caps, 'firstMatch': [{}]}}, timeout=180)
        if not isinstance(value, dict) or not value.get('sessionId'):
            raise SafetyStop('Appium oprettede ikke en brugbar session.')
        self.session_id = str(value['sessionId'])

    def _path(self, suffix: str) -> str:
        if not self.session_id:
            raise SafetyStop('Forbind telefonen først.')
        return '/session/' + urllib.parse.quote(self.session_id, safe='') + suffix

    def execute(self, name: str):
        return self.request('POST', self._path('/execute/sync'), {'script': 'mobile: ' + name, 'args': [{}]})

    def _app(self) -> str:
        value = self.execute('activeAppInfo')
        if not isinstance(value, dict) or not value.get('bundleId'):
            raise SafetyStop('Kunne ikke afgøre hvilken app der er åben.')
        return value['bundleId']

    def snapshot(self) -> dict:
        locked = self.execute('isLocked')
        if locked is not False:
            raise SafetyStop('Lås iPhonen op manuelt først.')
        app = self._app()
        parsed = parse_source(self.request('GET', self._path('/source')), self.key)
        if self._app() != app or self.execute('isLocked') is not False:
            raise SafetyStop('Appen eller låsestatus skiftede under aflæsningen.')
        return dict(parsed, bundle_id=app, locked=False)

    def click(self, selector: dict, allow_multiple: bool = False) -> None:
        if not self.expected_bundle:
            raise SafetyStop('Appen er ikke kalibreret.')
        elements = self.request('POST', self._path('/elements'), {'using': 'xpath', 'value': xpath(selector)})
        if not isinstance(elements, list) or not elements or (len(elements) != 1 and not allow_multiple):
            raise SafetyStop('Knappen kunne ikke findes entydigt. Intet klik sendt.')
        element = elements[0].get('element-6066-11e4-a52e-4f735466cecf')
        if not isinstance(element, str) or not element:
            raise SafetyStop('Driveren returnerede en ugyldig knap.')
        if self.execute('isLocked') is not False or self._app() != self.expected_bundle:
            raise SafetyStop('Appen eller låsen skiftede inden klikket.')
        if self.cancelled():
            raise SafetyStop('Stop eller tidsgrænse nået før klikket. Intet nyt klik sendt.')
        self.request('POST', self._path('/element/' + urllib.parse.quote(element, safe='') + '/click'), {})

    def close(self) -> None:
        if self.session_id:
            try:
                self.request('DELETE', self._path(''), timeout=10)
            finally:
                self.session_id = None
