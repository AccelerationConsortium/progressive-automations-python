# test_up.py
import time
import RPi.GPIO as GPIO

UP_PIN = 17  # BCM numbering, physical pin 11

GPIO.setmode(GPIO.BCM)

def release_up():
    # High-impedance: "button not pressed"
    GPIO.setup(UP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_OFF)

def press_up():
    # Drive low: "button pressed"
    GPIO.setup(UP_PIN, GPIO.OUT, initial=GPIO.LOW)

try:
    # Make sure we're released at start
    release_up()
    print("Ready. Desk should NOT move yet.")
    
    input("Press Enter to move UP for 2 seconds...")

    print("Moving UP...")
    press_up()
    time.sleep(2.0)   # adjust if you want a shorter/longer test
    release_up()
    print("Released UP. Test finished.")

finally:
    # Ensure we leave the line released
    release_up()
    GPIO.cleanup()
