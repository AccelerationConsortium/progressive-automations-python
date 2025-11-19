"""
Dummy conftest.py for progressive_automations_python.

If you don't know what this is for, just leave it empty.
Read more about conftest.py under:
- https://docs.pytest.org/en/stable/fixture.html
- https://docs.pytest.org/en/stable/writing_plugins.html
"""

import sys
import types

# Provide a minimal RPi.GPIO mock ONLY when running under pytest
# This ensures the mock is never activated outside of test execution
if 'pytest' in sys.modules or '_pytest' in sys.modules:
    rpi = types.ModuleType('RPi')
    gpio = types.ModuleType('RPi.GPIO')

    def _noop(*args, **kwargs):
        return None

    gpio.setmode = _noop
    gpio.setup = _noop
    gpio.cleanup = _noop
    gpio.input = lambda *args, **kwargs: 0
    gpio.output = _noop
    gpio.add_event_detect = _noop
    gpio.remove_event_detect = _noop

    # common constants
    gpio.BOARD = 10
    gpio.BCM = 11
    gpio.IN = 0
    gpio.OUT = 1
    gpio.PUD_UP = 2
    gpio.PUD_OFF = 20
    gpio.LOW = 0

    # register modules so `import RPi.GPIO as GPIO` works
    sys.modules['RPi'] = rpi
    sys.modules['RPi.GPIO'] = gpio

# import pytest
