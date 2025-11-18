"""
GPIO-based movement control for the desk lifter.

Handles low-level GPIO operations, pin management, and movement execution.
Provides safe pin control with proper initialization and cleanup.
"""

import time
from typing import Tuple

try:
    import RPi.GPIO as GPIO
    from constants import UP_PIN, DOWN_PIN
except ImportError:
    # For testing without actual GPIO hardware
    class MockGPIO:
        BCM = "BCM"
        OUT = "OUT" 
        IN = "IN"
        LOW = 0
        HIGH = 1
        PUD_OFF = "PUD_OFF"
        
        @staticmethod
        def setmode(mode): pass
        @staticmethod  
        def setup(pin, mode, **kwargs): pass
        @staticmethod
        def cleanup(): pass
        
    GPIO = MockGPIO()
    # Use default pins if constants not available (match constants.py)
    UP_PIN = 18
    DOWN_PIN = 17


def setup_gpio() -> None:
    """Initialize GPIO settings"""
    GPIO.setmode(GPIO.BCM)


def release_up() -> None:
    """Set UP pin to high-impedance state"""
    GPIO.setup(UP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_OFF)


def press_up() -> None:
    """Set UP pin to drive low (button pressed)"""
    GPIO.setup(UP_PIN, GPIO.OUT, initial=GPIO.LOW)


def release_down() -> None:
    """Set DOWN pin to high-impedance state"""
    GPIO.setup(DOWN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_OFF)


def press_down() -> None:
    """Set DOWN pin to drive low (button pressed)"""
    GPIO.setup(DOWN_PIN, GPIO.OUT, initial=GPIO.LOW)


def cleanup_gpio() -> None:
    """Clean up GPIO resources"""
    release_up()
    release_down()
    GPIO.cleanup()


def move_up(up_time: float) -> Tuple[float, float, float]:
    """
    Execute upward movement for specified time
    
    Returns:
        (start_time, end_time, actual_duration)
    """
    print(f"Moving UP for {up_time:.1f} seconds...")
    
    release_up()
    start_time = time.time()
    press_up()
    time.sleep(up_time)
    release_up()
    end_time = time.time()
    actual_duration = end_time - start_time
    
    print(f"UP movement completed: {actual_duration:.1f}s actual")
    return start_time, end_time, actual_duration


def move_down(down_time: float) -> Tuple[float, float, float]:
    """
    Execute downward movement for specified time
    
    Returns:
        (start_time, end_time, actual_duration)
    """
    print(f"Moving DOWN for {down_time:.1f} seconds...")
    
    release_down()
    start_time = time.time()
    press_down()
    time.sleep(down_time)
    release_down()
    end_time = time.time()
    actual_duration = end_time - start_time
    
    print(f"DOWN movement completed: {actual_duration:.1f}s actual")
    return start_time, end_time, actual_duration