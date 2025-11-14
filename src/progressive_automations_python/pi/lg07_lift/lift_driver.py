# lift_driver.py
#
# Low-level driver for controlling the LG-07 lifting column
# using Raspberry Pi GPIO pins connected to a relay board.
#
# Each relay simulates a button press on the FLTCON remote.
# Relays are assumed to be ACTIVE-LOW:
#   GPIO LOW  -> relay ON  -> button pressed
#   GPIO HIGH -> relay OFF -> button released

import time
import threading
import RPi.GPIO as GPIO

# Default GPIO pin assignments (BCM numbering)
PIN_UP = 17
PIN_DOWN = 27

_initialized = False
_lock = threading.Lock()


def _init_gpio():
    """Initialize GPIO pins once."""
    global _initialized
    if _initialized:
        return

    GPIO.setmode(GPIO.BCM)  # use BCM numbering (GPIO17 = pin 11)
    GPIO.setup(PIN_UP, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(PIN_DOWN, GPIO.OUT, initial=GPIO.HIGH)

    _initialized = True


def _release_all():
    """Release all relays (set all GPIO HIGH)."""
    GPIO.output(PIN_UP, GPIO.HIGH)
    GPIO.output(PIN_DOWN, GPIO.HIGH)


def press_up(seconds: float):
    """
    Press the UP button for a given number of seconds.
    """
    _init_gpio()
    with _lock:
        _release_all()
        GPIO.output(PIN_UP, GPIO.LOW)
        time.sleep(seconds)
        _release_all()


def press_down(seconds: float):
    """
    Press the DOWN button for a given number of seconds.
    """
    _init_gpio()
    with _lock:
        _release_all()
        GPIO.output(PIN_DOWN, GPIO.LOW)
        time.sleep(seconds)
        _release_all()


def nudge(direction: str, seconds: float = 0.2):
    """
    Move UP or DOWN for a small time increment.
    """
    direction = direction.lower()
    if direction not in ("up", "down"):
        raise ValueError("direction must be 'up' or 'down'")

    if seconds <= 0:
        raise ValueError("seconds must be > 0")

    if direction == "up":
        press_up(seconds)
    else:
        press_down(seconds)


def emergency_stop():
    """
    Immediately release all relays.
    """
    if not _initialized:
        return
    with _lock:
        _release_all()


def cleanup():
    """
    Cleanup GPIO state. Call this when shutting down the script.
    """
    if _initialized:
        emergency_stop()
        GPIO.cleanup()
    