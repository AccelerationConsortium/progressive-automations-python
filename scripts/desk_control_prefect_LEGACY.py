import time
import json
import os
from datetime import datetime, timedelta
from prefect import flow, task
from prefect.logging import get_run_logger
import RPi.GPIO as GPIO
from constants import UP_PIN, DOWN_PIN

# Calibration data
LOWEST_HEIGHT = 23.7  # inches
HIGHEST_HEIGHT = 54.5  # inches
UP_RATE = 0.54  # inches per second
DOWN_RATE = 0.55  # inches per second

STATE_FILE = "lifter_state.json"
DUTY_CYCLE_PERIOD = 1200  # 20 minutes in seconds
DUTY_CYCLE_MAX_ON_TIME = 120  # 2 minutes in seconds (10% of 20 minutes)
DUTY_CYCLE_PERCENTAGE = 0.10  # 10% duty cycle
MAX_CONTINUOUS_RUNTIME = 30  # Maximum continuous movement time in seconds

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
        "usage_periods": []  # List of [start_timestamp, end_timestamp, duration] entries
    }

@task
def save_state(state):
    """Save state to JSON file"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

@task
def clean_old_usage_periods(state):
    """Remove usage periods older than the duty cycle period"""
    current_time = time.time()
    cutoff_time = current_time - DUTY_CYCLE_PERIOD
    
    # Keep only periods that end after the cutoff time
    state["usage_periods"] = [
        period for period in state["usage_periods"] 
        if period[1] > cutoff_time  # period[1] is end_timestamp
    ]
    return state

@task
def get_current_duty_cycle_usage(state):
    """Calculate current duty cycle usage in the sliding window"""
    clean_old_usage_periods(state)
    current_time = time.time()
    
    total_usage = 0.0
    for start_time, end_time, duration in state["usage_periods"]:
        # Only count usage that's within the duty cycle period
        window_start = current_time - DUTY_CYCLE_PERIOD
        
        # Adjust start and end times to the current window
        effective_start = max(start_time, window_start)
        effective_end = min(end_time, current_time)
        
        if effective_end > effective_start:
            total_usage += effective_end - effective_start
    
    return total_usage

@task
def get_remaining_duty_time(state):
    """Get remaining duty cycle time in seconds"""
    current_usage = get_current_duty_cycle_usage(state)
    return max(0, DUTY_CYCLE_MAX_ON_TIME - current_usage)

@task
def record_usage_period(state, start_time, end_time, duration):
    """Record a usage period in the duty cycle tracking"""
    state["usage_periods"].append([start_time, end_time, duration])
    return state

@task
def check_timing_limits(state, required_time):
    """Check if the movement is within duty cycle limits using sliding window"""
    logger = get_run_logger()
    
    # Clean old periods and get current usage
    state = clean_old_usage_periods(state)
    current_usage = get_current_duty_cycle_usage(state)
    
    # Check continuous runtime limit
    if required_time > MAX_CONTINUOUS_RUNTIME:
        raise ValueError(f"Movement duration {required_time:.1f}s exceeds maximum continuous runtime of {MAX_CONTINUOUS_RUNTIME}s")
    
    # Check if adding this movement would exceed the duty cycle limit
    if current_usage + required_time > DUTY_CYCLE_MAX_ON_TIME:
        remaining_time = DUTY_CYCLE_MAX_ON_TIME - current_usage
        raise ValueError(f"Movement would exceed {DUTY_CYCLE_PERCENTAGE*100:.0f}% duty cycle limit. Current usage: {current_usage:.1f}s, Remaining: {remaining_time:.1f}s in {DUTY_CYCLE_PERIOD}s window")
    
    logger.info(f"Duty cycle OK: {current_usage:.1f}s + {required_time:.1f}s <= {DUTY_CYCLE_MAX_ON_TIME}s ({DUTY_CYCLE_PERCENTAGE*100:.0f}% of {DUTY_CYCLE_PERIOD}s)")
    return True, state

@task
def move_up(up_time):
    """Execute upward movement for specified time with duty cycle tracking"""
    logger = get_run_logger()
    logger.info(f"Moving UP for {up_time:.1f} seconds...")
    
    release_up()
    start_time = time.time()
    press_up()
    time.sleep(up_time)
    release_up()
    end_time = time.time()
    actual_duration = end_time - start_time
    
    logger.info(f"UP movement completed: {actual_duration:.1f}s actual")
    return start_time, end_time, actual_duration

@task
def move_down(down_time):
    """Execute downward movement for specified time with duty cycle tracking"""
    logger = get_run_logger()
    logger.info(f"Moving DOWN for {down_time:.1f} seconds...")
    
    release_down()
    start_time = time.time()
    press_down()
    time.sleep(down_time)
    release_down()
    end_time = time.time()
    actual_duration = end_time - start_time
    
    logger.info(f"DOWN movement completed: {actual_duration:.1f}s actual")
    return start_time, end_time, actual_duration

@flow
def move_to_height_flow(target_height: float, current_height: float):
    """Main flow to move desk to target height with safety checks"""
    logger = get_run_logger()
    
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
            logger.info(f"Already at {target_height}'' (within tolerance). No movement needed.")
            return
        
        if delta > 0:
            # Moving up
            up_time = delta / UP_RATE
            
            # Check timing limits
            is_valid, updated_state = check_timing_limits(state, up_time)
            state = updated_state
            
            # Execute movement and get actual timing
            start_time, end_time, actual_duration = move_up(up_time)
            
            # Record the usage period and update state
            state = record_usage_period(state, start_time, end_time, actual_duration)
            state["total_up_time"] += actual_duration
        else:
            # Moving down
            down_time = abs(delta) / DOWN_RATE
            
            # Check timing limits
            is_valid, updated_state = check_timing_limits(state, down_time)
            state = updated_state
            
            # Execute movement and get actual timing
            start_time, end_time, actual_duration = move_down(down_time)
            
            # Record the usage period (down time counts toward duty cycle but not total_up_time)
            state = record_usage_period(state, start_time, end_time, actual_duration)
        
        # Update position and save state
        state["last_position"] = target_height
        save_state(state)
        
        # Get current duty cycle info for logging
        current_usage = get_current_duty_cycle_usage(state)
        remaining_time = get_remaining_duty_time(state)
        
        logger.info(f"Arrived at {target_height}'' (approximate). State saved.")
        logger.info(f"Duty cycle usage: {current_usage:.1f}s / {DUTY_CYCLE_MAX_ON_TIME}s ({current_usage/DUTY_CYCLE_MAX_ON_TIME*100:.1f}%)")
        logger.info(f"Remaining duty time: {remaining_time:.1f}s")
        logger.info(f"Total up time: {state['total_up_time']:.1f}s")
        
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
            cron="39 4 * * *",  # Run daily at 11:39 PM Toronto time (4:39 AM UTC)
        )
        print("Deployment created! Run 'prefect worker start --pool default-agent-pool' to execute scheduled flows.")
    elif len(sys.argv) > 1 and sys.argv[1] == "test":
        custom_test_sequence()
    else:
        desk_control_cli()