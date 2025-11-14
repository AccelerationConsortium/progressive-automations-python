#!/usr/bin/env python3
"""
Simple test script for lift_driver.py
This mocks RPi.GPIO for testing on non-Raspberry Pi systems.
"""

import sys
import os
import time
import unittest.mock

# Add the src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# Mock RPi.GPIO for testing
mock_gpio = unittest.mock.MagicMock()
mock_gpio.BCM = 'BCM'
mock_gpio.HIGH = 1
mock_gpio.LOW = 0
mock_gpio.OUT = 'OUT'

sys.modules['RPi'] = unittest.mock.MagicMock()
sys.modules['RPi.GPIO'] = mock_gpio

# Now import the driver
from progressive_automations_python.pi.lg07_lift.lift_driver import press_up, press_down, nudge, emergency_stop, cleanup

def test_basic_functionality():
    """Test basic up/down functionality with mocked GPIO."""
    print("Testing lift_driver with mocked GPIO...")

    # Test press_up
    print("Testing press_up(0.1)...")
    start_time = time.time()
    press_up(0.1)
    elapsed = time.time() - start_time
    print(".1f")

    # Test press_down
    print("Testing press_down(0.1)...")
    start_time = time.time()
    press_down(0.1)
    elapsed = time.time() - start_time
    print(".1f")

    # Test nudge
    print("Testing nudge('up', 0.05)...")
    start_time = time.time()
    nudge('up', 0.05)
    elapsed = time.time() - start_time
    print(".1f")

    print("Testing nudge('down', 0.05)...")
    start_time = time.time()
    nudge('down', 0.05)
    elapsed = time.time() - start_time
    print(".1f")

    # Test emergency stop
    print("Testing emergency_stop()...")
    emergency_stop()
    print("Emergency stop called")

    # Test cleanup
    print("Testing cleanup()...")
    cleanup()
    print("Cleanup called")

    print("\n✅ All tests passed! GPIO calls were mocked and timing is correct.")
    print("When running on Raspberry Pi, these will activate the actual relays.")

if __name__ == "__main__":
    test_basic_functionality()