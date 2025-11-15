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
    # Make sure we're released at start
    release_down()
    print("Ready. Desk should NOT move yet.")
    
    input("Press Enter to move DOWN for 2 seconds...")

    print("Moving DOWN...")
    press_down()
    time.sleep(2.0)   # adjust if you want a shorter/longer test
    release_down()
    print("Released DOWN. Test finished.")

finally:
    # Ensure we leave the line released
    release_down()
    GPIO.cleanup()
