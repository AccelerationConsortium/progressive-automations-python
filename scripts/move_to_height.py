import time
import RPi.GPIO as GPIO

# Calibration data
LOWEST_HEIGHT = 23.7  # inches
HIGHEST_HEIGHT = 54.5  # inches
UP_RATE = 0.54  # inches per second (from calibration)

UP_PIN = 17   # BCM numbering, physical pin 11
DOWN_PIN = 27 # BCM numbering, physical pin 13

GPIO.setmode(GPIO.BCM)

def release_up():
    GPIO.setup(UP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_OFF)

def press_up():
    GPIO.setup(UP_PIN, GPIO.OUT, initial=GPIO.LOW)

def release_down():
    GPIO.setup(DOWN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_OFF)

def press_down():
    GPIO.setup(DOWN_PIN, GPIO.OUT, initial=GPIO.LOW)

def move_to_height(target_height):
    if not (LOWEST_HEIGHT <= target_height <= HIGHEST_HEIGHT):
        raise ValueError(f"Target height {target_height}'' is out of range.")
    # Step 1: Reset to lowest
    print(f"Resetting to lowest position ({LOWEST_HEIGHT})...")
    release_down()
    input("Press Enter to move all the way DOWN (about 56 seconds from max height)...")
    press_down()
    time.sleep(56.0)
    release_down()
    print("At lowest position.")
    # Step 2: Move up for calculated time
    delta = target_height - LOWEST_HEIGHT
    up_time = delta / UP_RATE
    print(f"Moving UP for {up_time:.1f} seconds to reach {target_height}''...")
    release_up()
    input("Press Enter to move UP...")
    press_up()
    time.sleep(up_time)
    release_up()
    print(f"Arrived at {target_height}'' (approximate).")

if __name__ == "__main__":
    try:
        target = float(input(f"Enter target height in inches ({LOWEST_HEIGHT}-{HIGHEST_HEIGHT}): "))
        move_to_height(target)
    finally:
        release_up()
        release_down()
        GPIO.cleanup()
