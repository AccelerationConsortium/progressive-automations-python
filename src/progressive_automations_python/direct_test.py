#!/usr/bin/env python3
"""
Direct GPIO test script - bypasses import issues
"""
import time
import RPi.GPIO as GPIO

# Pin definitions
UP_PIN = 18
DOWN_PIN = 17

def setup_gpio():
    GPIO.setmode(GPIO.BCM)

def press_up():
    print("Setting UP pin (18) to HIGH")
    GPIO.setup(UP_PIN, GPIO.OUT, initial=GPIO.LOW)

def release_up():
    print("Setting UP pin (18) to high-impedance")
    GPIO.setup(UP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_OFF)

def press_down():
    print("Setting DOWN pin (17) to HIGH")
    GPIO.setup(DOWN_PIN, GPIO.OUT, initial=GPIO.LOW)

def release_down():
    print("Setting DOWN pin (17) to high-impedance")
    GPIO.setup(DOWN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_OFF)

def cleanup_gpio():
    release_up()
    release_down()
    GPIO.cleanup()

if __name__ == "__main__":
    print("Starting direct GPIO test...")
    setup_gpio()
    
    try:
        print("Testing UP movement for 2 seconds...")
        release_up()
        time.sleep(0.1)
        press_up()
        time.sleep(2.0)
        release_up()
        print("UP test complete")
        
        time.sleep(1.0)
        
        print("Testing DOWN movement for 2 seconds...")
        release_down()
        time.sleep(0.1)
        press_down()
        time.sleep(2.0)
        release_down()
        print("DOWN test complete")
        
    except KeyboardInterrupt:
        print("Test interrupted")
    finally:
        cleanup_gpio()
        print("GPIO cleaned up")