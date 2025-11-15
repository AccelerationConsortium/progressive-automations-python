import time
import json
import os
import RPi.GPIO as GPIO

# Calibration data
LOWEST_HEIGHT = 23.7  # inches
HIGHEST_HEIGHT = 54.5  # inches
UP_RATE = 0.54  # inches per second
DOWN_RATE = 0.55  # inches per second

STATE_FILE = "lifter_state.json"

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

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {
        "total_up_time": 0.0,
        "last_position": None
    }

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def move_to_height(target_height, current_height):
    state = load_state()
    if not (LOWEST_HEIGHT <= target_height <= HIGHEST_HEIGHT):
        raise ValueError(f"Target height {target_height}'' is out of range.")
    delta = target_height - current_height
    if abs(delta) < 0.01:
        print(f"Already at {target_height}'' (within tolerance). No movement needed.")
        return
    if delta > 0:
        # Move up
        up_time = delta / UP_RATE
        print(f"Moving UP for {up_time:.1f} seconds to reach {target_height}''...")
        release_up()
        input("Press Enter to move UP...")
        press_up()
        time.sleep(up_time)
        release_up()
        state["total_up_time"] += up_time
    else:
        # Move down
        down_time = abs(delta) / DOWN_RATE
        print(f"Moving DOWN for {down_time:.1f} seconds to reach {target_height}''...")
        release_down()
        input("Press Enter to move DOWN...")
        press_down()
        time.sleep(down_time)
        release_down()
        # Do not update total_up_time for down movement
    state["last_position"] = target_height
    save_state(state)
    print(f"Arrived at {target_height}'' (approximate). State saved.")

if __name__ == "__main__":
    try:
        current = float(input(f"Enter current height in inches ({LOWEST_HEIGHT}-{HIGHEST_HEIGHT}): "))
        target = float(input(f"Enter target height in inches ({LOWEST_HEIGHT}-{HIGHEST_HEIGHT}): "))
        move_to_height(target, current)
    finally:
        release_up()
        release_down()
        GPIO.cleanup()
