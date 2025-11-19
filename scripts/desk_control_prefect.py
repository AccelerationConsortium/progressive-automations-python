import time
import json
import os
from datetime import datetime, timedelta
from collections import deque
from prefect import flow, task
from prefect.logging import get_run_logger
import RPi.GPIO as GPIO
from constants import (
    LOWEST_HEIGHT,
    HIGHEST_HEIGHT,
    UP_RATE,
    DOWN_RATE,
    STATE_FILE,
    DUTY_CYCLE_PERIOD,
    DUTY_CYCLE_MAX_ON_TIME,
    MAX_CONTINUOUS_RUNTIME,
    DUTY_CYCLE_PERCENTAGE,
    UP_PIN,
    DOWN_PIN
)



# Global queue to track ON periods (start_time, end_time)
on_periods_queue = deque()

GPIO.setmode(GPIO.BCM)

@task
def clean_old_periods():
    """Remove ON periods outside the 20-minute duty cycle window"""
    current_time = time.time()
    while on_periods_queue and on_periods_queue[0][1] < current_time - DUTY_CYCLE_PERIOD:
        on_periods_queue.popleft()

@task
def get_current_usage():
    """Get current duty cycle usage in seconds"""
    clean_old_periods()
    return sum(end - start for start, end in on_periods_queue)

@task
def get_remaining_duty_time():
    """Get remaining duty cycle time in seconds"""
    current_usage = get_current_usage()
    return max(0, DUTY_CYCLE_MAX_ON_TIME - current_usage)

@task
def can_run_for_duration(duration):
    """Check if we can run for the specified duration without exceeding duty cycle"""
    return get_remaining_duty_time() >= duration

@task
def record_on_period(start_time, end_time):
    """Record an ON period in the duty cycle queue"""
    on_periods_queue.append((start_time, end_time))

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
def check_timing_limits(required_time):
    """Check if the movement is within duty cycle limits using queue"""
    logger = get_run_logger()
    
    # Check continuous runtime limit
    if required_time > MAX_CONTINUOUS_RUNTIME:
        raise ValueError(f"Movement duration {required_time:.1f}s exceeds maximum continuous runtime of {MAX_CONTINUOUS_RUNTIME}s")
    
    # Check duty cycle
    remaining_time = get_remaining_duty_time()
    
    if remaining_time >= required_time:
        logger.info(f"Duty cycle OK: {remaining_time:.1f}s remaining, requesting {required_time:.1f}s")
        logger.info(f"Continuous runtime OK: {required_time:.1f}s <= {MAX_CONTINUOUS_RUNTIME}s limit")
        return True
    else:
        wait_time = required_time - remaining_time
        raise ValueError(f"Movement would exceed duty cycle limit. Need to wait {wait_time:.1f}s more")

@task
def wait_for_duty_cycle(required_duration):
    """Wait until duty cycle allows for the required duration"""
    logger = get_run_logger()
    
    while True:
        remaining = get_remaining_duty_time()
        if remaining >= required_duration:
            logger.info(f"Duty cycle ready: {remaining:.1f}s available")
            break
        
        wait_time = required_duration - remaining
        logger.info(f"Waiting {wait_time:.1f}s for duty cycle...")
        time.sleep(min(wait_time, 30))  # Check every 30s max

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
    
    # Record the actual ON period
    record_on_period(start_time, end_time)
    logger.info(f"UP movement completed: {end_time - start_time:.1f}s actual")

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
    
    # Record the actual ON period
    record_on_period(start_time, end_time)
    logger.info(f"DOWN movement completed: {end_time - start_time:.1f}s actual")

@task
def move_with_chunking(direction: str, total_time: float, rest_between_chunks: float = 2.0):
    """Move in chunks if total time exceeds continuous runtime limit"""
    logger = get_run_logger()
    
    if total_time <= MAX_CONTINUOUS_RUNTIME:
        # Single movement is fine
        if direction.lower() == "up":
            move_up(total_time)
        else:
            move_down(total_time)
        return
    
    # Break into chunks
    chunks = []
    remaining = total_time
    
    while remaining > 0:
        chunk_size = min(remaining, MAX_CONTINUOUS_RUNTIME)
        chunks.append(chunk_size)
        remaining -= chunk_size
    
    logger.info(f"Breaking {total_time:.1f}s movement into {len(chunks)} chunks: {[f'{c:.1f}s' for c in chunks]}")
    
    for i, chunk_time in enumerate(chunks):
        logger.info(f"Executing chunk {i+1}/{len(chunks)}: {chunk_time:.1f}s")
        
        # Check duty cycle before each chunk
        check_timing_limits(chunk_time)
        
        # Execute chunk
        if direction.lower() == "up":
            move_up(chunk_time)
        else:
            move_down(chunk_time)
        
        # Rest between chunks (except after last chunk)
        if i < len(chunks) - 1:
            logger.info(f"Resting {rest_between_chunks:.1f}s between chunks...")
            time.sleep(rest_between_chunks)

#@flow
@task
def move_to_height_flow(target_height: float, current_height: float):
    """Main flow to move desk to target height with queue-based duty cycle enforcement"""
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
            
            # Use chunking for long movements
            move_with_chunking("up", up_time)
            
            # Update state
            state["total_up_time"] += up_time
        else:
            # Moving down
            down_time = abs(delta) / DOWN_RATE
            
            # Use chunking for long movements
            move_with_chunking("down", down_time)
        
        # Update position and save state
        state["last_position"] = target_height
        save_state(state)
        
        current_usage = get_current_usage()
        remaining_duty = get_remaining_duty_time()
        
        logger.info(f"Arrived at {target_height}'' (approximate). State saved.")
        logger.info(f"Current duty cycle usage: {current_usage:.1f}s / {MAX_ON_TIME}s")
        logger.info(f"Remaining duty time: {remaining_duty:.1f}s")
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
            #cron="39 4 * * *",  # Run daily at 11:39 PM Toronto time (4:39 AM UTC)
        )
        print("Deployment created! Run 'prefect worker start --pool default-agent-pool' to execute scheduled flows.")
    elif len(sys.argv) > 1 and sys.argv[1] == "test":
        custom_test_sequence()
    else:
        desk_control_cli()