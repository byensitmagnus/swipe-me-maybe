# source: ai; ai_generated: (C)
"""Optional browser QA: pip install playwright; PLAYWRIGHT_CHROMIUM_EXECUTABLE optional."""
import os
from pathlib import Path
import sys
import tempfile
import threading
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import make_server
from playwright.sync_api import sync_playwright, expect

with tempfile.TemporaryDirectory() as directory:
    output = Path(os.environ.get('BROWSER_SMOKE_OUTPUT', directory))
    output.mkdir(parents=True, exist_ok=True)
    server = make_server(port=0, state_dir=directory, demo=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f'http://127.0.0.1:{server.server_port}'
    try:
        with sync_playwright() as p:
            executable = os.environ.get('PLAYWRIGHT_CHROMIUM_EXECUTABLE')
            browser = p.chromium.launch(headless=True, **({'executable_path': executable} if executable else {}))
            page = browser.new_page(viewport={'width': 1152, 'height': 1000})
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(url)
            expect(page.locator('#demo-banner')).to_be_visible()
            page.locator('#preview').click()
            expect(page.locator('#notice')).to_contain_text('Ingen knapper blev trykket')
            page.locator('#max-likes').fill('2')
            page.locator('#ack').check()
            page.locator('#start').click()
            expect(page.locator('#run-status')).to_have_text('Afsluttet', timeout=10000)
            expect(page.locator('#attempts')).to_have_text('2')
            expect(page.locator('#observed')).to_have_text('2')
            # Public documentation assets: capture only the clearly labeled offline demo.
            page.screenshot(path=str(output / 'demo-desktop.png'), full_page=True)
            page.set_viewport_size({'width': 390, 'height': 844})
            page.screenshot(path=str(output / 'demo-mobile.png'), full_page=True)
            page.set_viewport_size({'width': 1152, 'height': 1000})
            # Same UI with manually calibrated synthetic screens. Still no iPhone.
            server.controller.demo = False
            server.controller.config = {}
            page.reload()
            expect(page.locator('#calibration')).to_be_visible()
            page.locator('#inspect').click()
            expect(page.locator('#inspection-info')).to_contain_text('2 synlige knapper')
            page.locator('#marker').select_option('0')
            page.locator('#like').select_option('1')
            page.locator('#save-feed').click()
            expect(page.locator('#notice')).to_contain_text('Profilside gemt')
            server.controller.device.screen = 'send'
            page.locator('#inspect').click()
            expect(page.locator('#inspection-info')).to_contain_text('1 inputfelter')
            page.locator('#send').select_option('0')
            page.locator('#empty-confirmed').check()
            page.locator('#save-send').click()
            expect(page.locator('#notice')).to_contain_text('Kalibrering gemt')
            server.controller.device.screen = 'feed'
            page.locator('#preview').click()
            expect(page.locator('#notice')).to_contain_text('Kontrol OK')
            page.locator('#max-likes').fill('25')
            page.locator('#ack').check()
            page.locator('#start').click()
            page.locator('#stop').click()
            expect(page.locator('#run-status')).to_have_text('Stoppet', timeout=10000)
            assert int(page.locator('#attempts').inner_text()) < 25
            page.screenshot(path=str(output / 'iphone-assistant-desktop.png'), full_page=True)
            page.set_viewport_size({'width': 390, 'height': 844})
            page.screenshot(path=str(output / 'iphone-assistant-mobile.png'), full_page=True)
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'Horizontal mobile overflow'
            assert not errors, errors
            print('PASS: demo; preview zero writes; two cycles; full manual calibration; stop; mobile width; zero JS exceptions.')
            browser.close()
    finally:
        server.controller.stop.set()
        server.shutdown()
        server.server_close()
        thread.join()
