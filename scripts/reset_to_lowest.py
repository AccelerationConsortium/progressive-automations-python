import time
import RPi.GPIO as GPIO

DOWN_PIN = 27  # BCM numbering, physical pin 13

GPIO.setmode(GPIO.BCM)

def release_down():
    # High-impedance: "button not pressed"
    GPIO.setup(DOWN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_OFF)

def press_down():
    # Drive low: "button pressed"
    GPIO.setup(DOWN_PIN, GPIO.OUT, initial=GPIO.LOW)

try:
    # This script is intended to move the desk from MAX height to MIN height.
    # Ensure the desk is at the highest position before running.
    release_down()
    print("Ready. Desk should be at MAX height. It will now move to MIN height.")

    input("Press Enter to move all the way DOWN (about 56 seconds from max height)...")

    print("Moving DOWN to lowest position...")
    press_down()
    time.sleep(56.0)   # 56s: calibrated for max to min travel (30.8" at 0.55 in/s)
    release_down()
    print("Released DOWN. Lifter should now be at lowest position.")

finally:
    # Ensure we leave the line released
    release_down()
    GPIO.cleanup()
