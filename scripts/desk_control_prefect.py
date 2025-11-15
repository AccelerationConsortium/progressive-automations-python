import time
import json
import os
from datetime import datetime, timedelta
from prefect import flow, task
import RPi.GPIO as GPIO

# Calibration data
LOWEST_HEIGHT = 23.7  # inches
HIGHEST_HEIGHT = 54.5  # inches
UP_RATE = 0.54  # inches per second
DOWN_RATE = 0.55  # inches per second

STATE_FILE = "lifter_state.json"
MAX_USAGE_TIME = 120  # 2 minutes in seconds
RESET_WINDOW = 1200   # 20 minutes in seconds

UP_PIN = 17   # BCM numbering, physical pin 11
DOWN_PIN = 27 # BCM numbering, physical pin 13

GPIO.setmode(GPIO.BCM)

@task
def setup_gpio():
    """Initialize GPIO settings"""
    GPIO.setmode(GPIO.BCM)

@task
def release_up():
    """Set UP pin to high-impedance state"""
    GPIO.setup(UP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_OFF)

@task
def press_up():
    """Set UP pin to drive low (button pressed)"""
    GPIO.setup(UP_PIN, GPIO.OUT, initial=GPIO.LOW)

@task
def release_down():
    """Set DOWN pin to high-impedance state"""
    GPIO.setup(DOWN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_OFF)

@task
def press_down():
    """Set DOWN pin to drive low (button pressed)"""
    GPIO.setup(DOWN_PIN, GPIO.OUT, initial=GPIO.LOW)

@task
def cleanup_gpio():
    """Clean up GPIO resources"""
    release_up()
    release_down()
    GPIO.cleanup()

@task
def load_state():
    """Load the current state from JSON file"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {
        "total_up_time": 0.0,
        "last_position": None,
        "last_reset_time": datetime.now().isoformat(),
        "current_window_usage": 0.0
    }

@task
def save_state(state):
    """Save state to JSON file"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

@task
def check_timing_limits(state, required_time):
    """Check if the movement is within timing limits"""
    current_time = datetime.now()
    last_reset = datetime.fromisoformat(state["last_reset_time"])
    
    # Check if 20-minute window has passed
    if (current_time - last_reset).total_seconds() >= RESET_WINDOW:
        # Reset the usage window
        state["last_reset_time"] = current_time.isoformat()
        state["current_window_usage"] = 0.0
        return True, state
    
    # Check if adding this movement would exceed the 2-minute limit
    if state["current_window_usage"] + required_time > MAX_USAGE_TIME:
        remaining_time = MAX_USAGE_TIME - state["current_window_usage"]
        raise ValueError(f"Movement would exceed 2-minute limit. Remaining time: {remaining_time:.1f}s")
    
    return True, state

@task
def move_up(up_time):
    """Execute upward movement for specified time"""
    print(f"Moving UP for {up_time:.1f} seconds...")
    release_up()
    # Removed input() for automated execution
    press_up()
    time.sleep(up_time)
    release_up()

@task
def move_down(down_time):
    """Execute downward movement for specified time"""
    print(f"Moving DOWN for {down_time:.1f} seconds...")
    release_down()
    # Removed input() for automated execution
    press_down()
    time.sleep(down_time)
    release_down()

#@flow
@task
def move_to_height_flow(target_height: float, current_height: float):
    """Main flow to move desk to target height with safety checks"""
    
    # Validate height range
    if not (LOWEST_HEIGHT <= target_height <= HIGHEST_HEIGHT):
        raise ValueError(f"Target height {target_height}'' is out of range.")
    
    # Setup GPIO
    setup_gpio()
    
    try:
        # Load current state
        state = load_state()
        
        # Calculate movement requirements
        delta = target_height - current_height
        if abs(delta) < 0.01:
            print(f"Already at {target_height}'' (within tolerance). No movement needed.")
            return
        
        if delta > 0:
            # Moving up
            up_time = delta / UP_RATE
            
            # Check timing limits
            check_timing_limits(state, up_time)
            
            # Execute movement
            move_up(up_time)
            
            # Update state
            state["total_up_time"] += up_time
            state["current_window_usage"] += up_time
        else:
            # Moving down
            down_time = abs(delta) / DOWN_RATE
            
            # Check timing limits
            check_timing_limits(state, down_time)
            
            # Execute movement
            move_down(down_time)
            
            # Update state (down time counts toward window usage but not total_up_time)
            state["current_window_usage"] += down_time
        
        # Update position and save state
        state["last_position"] = target_height
        save_state(state)
        
        print(f"Arrived at {target_height}'' (approximate). State saved.")
        print(f"Window usage: {state['current_window_usage']:.1f}s / {MAX_USAGE_TIME}s")
        print(f"Total up time: {state['total_up_time']:.1f}s")
        
    finally:
        # Always clean up GPIO
        cleanup_gpio()

@flow
def custom_test_sequence():
    """Custom flow: Start at lowest, move up 0.5 inches, rest 10 seconds, move down 0.5 inches"""
    start_height = LOWEST_HEIGHT
    up_target = start_height + 0.5
    
    print("Starting custom test sequence...")
    print(f"Starting at: {start_height}\"")
    print(f"Will move to: {up_target}\"")
    print(f"Then rest for 10 seconds")
    print(f"Then return to: {start_height}\"")
    
    # Phase 1: Move up 0.5 inches
    print("\n--- Phase 1: Moving UP 0.5 inches ---")
    move_to_height_flow(up_target, start_height)
    
    # Phase 2: Rest for 10 seconds
    print("\n--- Phase 2: Resting for 10 seconds ---")
    time.sleep(10)
    print("Rest complete.")
    
    # Phase 3: Move down 0.5 inches (back to lowest)
    print("\n--- Phase 3: Moving DOWN 0.5 inches ---")
    move_to_height_flow(start_height, up_target)
    
    print("\nCustom test sequence complete!")

@flow
def desk_control_cli():
    """CLI interface for desk control"""
    try:
        current = float(input(f"Enter current height in inches ({LOWEST_HEIGHT}-{HIGHEST_HEIGHT}): "))
        target = float(input(f"Enter target height in inches ({LOWEST_HEIGHT}-{HIGHEST_HEIGHT}): "))
        move_to_height_flow(target, current)
    except ValueError as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("\nOperation cancelled.")

if __name__ == "__main__":
    import sys
    from prefect import flow
    
    if len(sys.argv) > 1 and sys.argv[1] == "deploy":
        # Deploy the custom test sequence to run at scheduled times
        custom_test_sequence.from_source(
            source=".",
            entrypoint="scripts/desk_control_prefect.py:custom_test_sequence",
        ).deploy(
            name="desk-lifter-test-sequence-1139pm-toronto",
            work_pool_name="default-agent-pool",
            #cron="39 4 * * *",  # Run daily at 11:39 PM Toronto time (4:39 AM UTC)
        )
        print("Deployment created! Run 'prefect worker start --pool default-agent-pool' to execute scheduled flows.")
    elif len(sys.argv) > 1 and sys.argv[1] == "test":
        custom_test_sequence()
    else:
        desk_control_cli()