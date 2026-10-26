# source: ai; ai_generated: (C)
"""Explicit offline demonstration mode; no real person or device data."""

def button(name, value=''):
    return dict(type='XCUIElementTypeButton', name=name, label=name, value=value)


def config():
    return dict(bundle_id='demo.hinge', feed=dict(name='Discover', value='1'),
                like=dict(name='Like'), send=dict(name='Send Like'),
                feed_buttons=[button('Discover', '1'), button('Like')],
                send_buttons=[button('Send Like'), button('Cancel')],
                empty_fields=[dict(name='comment', value='Add a comment')])


class DemoDevice:
    def __init__(self):
        self.session_id = 'offline-demo'
        self.expected_bundle = 'demo.hinge'
        self.screen = 'feed'
        self.index = 0
        self.clicks = []
        self.cancelled = lambda: False

    def snapshot(self):
        cfg = config()
        return dict(bundle_id='demo.hinge', locked=False, alert=False,
                    buttons=cfg['feed_buttons' if self.screen == 'feed' else 'send_buttons'],
                    fields=[] if self.screen == 'feed' else cfg['empty_fields'],
                    fingerprint=f'synthetic-{self.index}')

    def click(self, selector, allow_multiple=False):
        from core import SafetyStop
        if self.cancelled():
            raise SafetyStop('Stoppet før klikket.')
        name = selector['name']
        if self.screen == 'feed' and name == 'Like':
            self.screen = 'send'
        elif self.screen == 'send' and name == 'Send Like':
            self.screen = 'feed'
            self.index += 1
        else:
            raise SafetyStop('Demoen modtog en uventet handling.')
        self.clicks.append(name)

    def close(self):
        self.session_id = None
