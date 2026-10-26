# ---
# source: ai
# ai_generated: "(C)"
# ---
"""Local, deterministic two-button runner. No device/network imports here."""
from __future__ import annotations

import json
import math
import re
import threading
import time
from typing import Callable, Protocol


class SafetyStop(Exception):
    """An expected stop; messages deliberately contain no profile data."""


class Device(Protocol):
    def snapshot(self) -> dict: ...
    def click(self, selector: dict, allow_multiple: bool = False) -> None: ...


def matches(button: dict, selector: dict) -> bool:
    return bool(selector) and all(button.get(k, '') == v for k, v in selector.items())


def control_key(button: dict) -> str:
    return json.dumps([button.get(k, '') for k in ('type', 'name', 'label')], ensure_ascii=False)


def fields_key(fields: list) -> str:
    return json.dumps(sorted((json.dumps(f, sort_keys=True) for f in fields)))


def selector_for(button: dict, selected: bool = False) -> dict:
    attribute = 'name' if button.get('name') else 'label'
    if not button.get(attribute):
        raise SafetyStop('Knappen mangler et stabilt navn. V1 bruger ikke koordinater.')
    result = {attribute: button[attribute]}
    if selected and button.get('value'):
        result['value'] = button['value']
    return result


def _literal(value: str) -> str:
    if "'" not in value:
        return "'" + value + "'"
    if '"' not in value:
        return '"' + value + '"'
    return 'concat(' + ',"\'",'.join("'" + part + "'" for part in value.split("'")) + ')'


def xpath(selector: dict) -> str:
    predicates = ["@visible='true'", "@enabled='true'"]
    for key, value in selector.items():
        if key not in ('name', 'label', 'value') or not isinstance(value, str):
            raise SafetyStop('Ugyldig knapvælger.')
        predicates.append('@' + key + '=' + _literal(value))
    return '//XCUIElementTypeButton[' + ' and '.join(predicates) + ']'


def validate_config(config: dict) -> None:
    required = ('bundle_id', 'feed', 'like', 'send', 'feed_buttons', 'send_buttons', 'empty_fields')
    if not isinstance(config, dict) or not all(k in config for k in required):
        raise SafetyStop('Kalibrér både profilsiden og Send Like-skærmen først.')
    if not isinstance(config['bundle_id'], str) or not re.fullmatch(r'[\w.-]{3,200}', config['bundle_id']):
        raise SafetyStop('Ugyldigt app-id.')
    for role in ('feed', 'like', 'send'):
        selector = config[role]
        if not isinstance(selector, dict) or not ('name' in selector or 'label' in selector):
            raise SafetyStop('Alle tre markører skal have et præcist navn.')
        if any(k not in ('name', 'label', 'value') or not isinstance(v, str)
               or not v or len(v) > 300 for k, v in selector.items()):
            raise SafetyStop('Ugyldig knapkalibrering.')
    prohibited = r'rose|boost|subscrib|køb|purchase|upgrade|besked|message|super.?like|priorit|\bbuy\b'
    for role in ('like', 'send'):
        if re.search(prohibited, ' '.join(config[role].values()), re.IGNORECASE):
            raise SafetyStop('Roser, beskeder og køb må ikke vælges som mål.')
    if config['like'] == config['send'] or config['feed'] == config['like']:
        raise SafetyStop('Vælg forskellige knapper til de forskellige trin.')
    for key in ('feed_buttons', 'send_buttons', 'empty_fields'):
        if not isinstance(config[key], list) or any(not isinstance(x, dict) for x in config[key]):
            raise SafetyStop('Ugyldig skærmkalibrering.')
    for role, baseline in (('feed', 'feed_buttons'), ('like', 'feed_buttons'), ('send', 'send_buttons')):
        count = sum(matches(b, config[role]) for b in config[baseline])
        if count < 1 or (role != 'like' and count != 1):
            raise SafetyStop('Kalibreringen har manglende eller flertydige knapper.')


def classify(snapshot: dict, config: dict) -> str:
    if snapshot.get('locked') is not False:
        raise SafetyStop('Telefonen er låst, eller låsestatus kunne ikke bekræftes.')
    if snapshot.get('bundle_id') != config['bundle_id']:
        raise SafetyStop('En anden app er aktiv. Åbn Hinge manuelt igen.')
    if snapshot.get('alert') is not False:
        raise SafetyStop('En dialog eller systemadvarsel er åben.')
    buttons = snapshot['buttons']
    sends = [b for b in buttons if matches(b, config['send'])]
    feeds = [b for b in buttons if matches(b, config['feed'])]
    likes = [b for b in buttons if matches(b, config['like'])]
    if sends:
        if len(sends) != 1:
            raise SafetyStop('Send-knappen er flertydig.')
        state, baseline = 'send', config['send_buttons']
        if fields_key(snapshot['fields']) != fields_key(config['empty_fields']):
            raise SafetyStop('Kommentarfeltet eller inputfelterne er ændret. Ingen besked sendes.')
    elif len(feeds) == 1 and likes and snapshot.get('fingerprint'):
        state, baseline = 'feed', config['feed_buttons']
        if snapshot['fields']:
            raise SafetyStop('Uventet inputfelt på profilsiden.')
    else:
        raise SafetyStop('Ukendt skærm, like-loft eller ændrede knapper. Ingen flere klik.')
    known = {control_key(b) for b in baseline}
    if any(control_key(b) not in known for b in buttons):
        raise SafetyStop('Skærmen har en ny knap eller popup. Kontrollér den manuelt.')
    return state


class Runner:
    """One explicitly started session. Never repeats an uncertain write."""
    def __init__(self, device: Device, config: dict, stop: threading.Event,
                 pause: float = .5, transition_seconds: float = 12,
                 progress: Callable[[dict], None] | None = None):
        self.device, self.config, self.stop = device, config, stop
        self.pause, self.transition_seconds = pause, transition_seconds
        self.progress = progress or (lambda _: None)
        self.deadline = 0.0
        self.result = dict(status='idle', reason='', attempts=0, observed_next=0)

    def _emit(self) -> None:
        self.progress(dict(self.result))

    def _guard(self) -> None:
        if self.stop.is_set():
            raise SafetyStop('Stoppet af dig. Et allerede afsendt klik kan ikke trækkes tilbage.')
        if time.monotonic() >= self.deadline:
            raise SafetyStop('Sessionens tidsgrænse er nået.')

    def _read(self) -> tuple[dict, str]:
        self._guard()
        snapshot = self.device.snapshot()
        self._guard()
        return snapshot, classify(snapshot, self.config)

    def _click(self, role: str, expected: str) -> dict:
        snapshot, state = self._read()  # Fresh guard directly before every click.
        if state != expected:
            raise SafetyStop('Skærmen skiftede før klikket. Stoppet uden at gætte.')
        self._guard()
        if role == 'send':
            self.result['attempts'] += 1  # Includes an uncertain/failed dispatch.
            self._emit()
        self.device.click(self.config[role], allow_multiple=(role == 'like'))
        self._guard()
        return snapshot

    def _wait(self, expected: str, previous: str, old_fingerprint: str) -> None:
        end = min(self.deadline, time.monotonic() + self.transition_seconds)
        stable = None
        while time.monotonic() < end:
            snapshot, state = self._read()
            if state == expected:
                if expected == 'send':
                    return
                fingerprint = snapshot['fingerprint']
                if fingerprint != old_fingerprint:
                    if stable == fingerprint:
                        return  # Two successive, unchanged new-feed observations.
                    stable = fingerprint
                else:
                    stable = None
            elif state != previous:
                raise SafetyStop('Uventet skærmskift.')
            else:
                stable = None
                if expected == 'send' and snapshot['fingerprint'] != old_fingerprint:
                    raise SafetyStop('Profilsiden skiftede uden den forventede send-dialog.')
            self.stop.wait(self.pause)
        raise SafetyStop('Ingen bekræftet overgang til næste skærm. Sidste klik gentages ikke.')

    def run(self, *, live: bool = False, acknowledged: bool = False,
            max_likes: int = 5, max_seconds: float = 120) -> dict:
        validate_config(self.config)
        if type(max_likes) is not int or not 1 <= max_likes <= 25:
            raise SafetyStop('Vælg et helt antal mellem 1 og 25 send-forsøg.')
        if (type(max_seconds) not in (int, float) or not math.isfinite(max_seconds)
                or not 1 <= max_seconds <= 600):
            raise SafetyStop('Vælg en varighed mellem 1 og 600 sekunder.')
        if live and acknowledged is not True:
            raise SafetyStop('Live-tilstand kræver din udtrykkelige accept.')
        self.deadline = time.monotonic() + max_seconds
        self.result = dict(status='running', reason='', attempts=0, observed_next=0)
        self._emit()
        try:
            _, state = self._read()
            if not live:
                self.result.update(status='finished', reason='preview', next_action=state)
            else:
                if state != 'feed':
                    raise SafetyStop('Start på Discover-profilsiden, ikke i en åben send-dialog.')
                for _ in range(max_likes):
                    before = self._click('like', 'feed')
                    self._wait('send', 'feed', before['fingerprint'])
                    self._click('send', 'send')
                    self._wait('feed', 'send', before['fingerprint'])
                    self.result['observed_next'] += 1
                    self._emit()
                    self.stop.wait(self.pause)
                self.result.update(status='finished', reason='Antalsgrænsen er nået.')
        except SafetyStop as exc:
            self.result.update(status='stopped', reason=str(exc))
        except Exception:
            # Never expose raw WebDriver responses or auto-retry a possibly sent like.
            self.result.update(status='stopped', reason=(
                'Forbindelses- eller driverfejl. Sidste klik kan være udført; det gentages ikke.'))
        self._emit()
        return dict(self.result)
