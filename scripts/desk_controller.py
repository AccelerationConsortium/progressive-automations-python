"""
High-level desk controller with height management and safety checks.

Combines movement control and duty cycle management to provide safe desk operations.
Handles height calculations, movement planning, and state management.
"""

from typing import Optional
from duty_cycle import (
    load_state, save_state, check_duty_cycle_limits, 
    record_usage_period, get_duty_cycle_status
)
from movement_control import setup_gpio, cleanup_gpio, move_up, move_down

# Calibration data
LOWEST_HEIGHT = 23.7  # inches
HIGHEST_HEIGHT = 54.5  # inches
UP_RATE = 0.54  # inches per second
DOWN_RATE = 0.55  # inches per second


def move_to_height(target_height: float, current_height: Optional[float] = None) -> dict:
    """
    Move desk to target height with safety checks and duty cycle enforcement
    
    Args:
        target_height: Desired height in inches
        current_height: Current height in inches (if None, uses last known position)
        
    Returns:
        dict with movement results and status information
    """
    # Validate height range
    if not (LOWEST_HEIGHT <= target_height <= HIGHEST_HEIGHT):
        raise ValueError(f"Target height {target_height}'' is out of range [{LOWEST_HEIGHT}-{HIGHEST_HEIGHT}].")
    
    # Setup GPIO
    setup_gpio()
    
    try:
        # Load current state
        state = load_state()
        
        # Determine current height
        if current_height is None:
            if state["last_position"] is None:
                raise ValueError("No current height provided and no last known position in state file.")
            current_height = state["last_position"]
        
        # Calculate movement requirements
        delta = target_height - current_height
        if abs(delta) < 0.01:
            print(f"Already at {target_height}'' (within tolerance). No movement needed.")
            return {
                "success": True,
                "movement": "none",
                "message": f"Already at target height {target_height}''",
                "duty_cycle": get_duty_cycle_status(state)
            }
        
        if delta > 0:
            # Moving up
            required_time = delta / UP_RATE
            direction = "up"
            
            # Check duty cycle limits
            is_valid, updated_state, message = check_duty_cycle_limits(state, required_time)
            state = updated_state
            
            if not is_valid:
                raise ValueError(message)
            
            print(message)
            
            # Execute movement and get actual timing
            start_time, end_time, actual_duration = move_up(required_time)
            
            # Record the usage period and update state
            state = record_usage_period(state, start_time, end_time, actual_duration)
            state["total_up_time"] += actual_duration
        else:
            # Moving down
            required_time = abs(delta) / DOWN_RATE
            direction = "down"
            
            # Check duty cycle limits
            is_valid, updated_state, message = check_duty_cycle_limits(state, required_time)
            state = updated_state
            
            if not is_valid:
                raise ValueError(message)
                
            print(message)
            
            # Execute movement and get actual timing
            start_time, end_time, actual_duration = move_down(required_time)
            
            # Record the usage period (down time counts toward duty cycle but not total_up_time)
            state = record_usage_period(state, start_time, end_time, actual_duration)
        
        # Update position and save state
        state["last_position"] = target_height
        save_state(state)
        
        # Get final duty cycle info
        duty_status = get_duty_cycle_status(state)
        
        print(f"Arrived at {target_height}'' (approximate). State saved.")
        print(f"Duty cycle usage: {duty_status['current_usage']:.1f}s / {duty_status['max_usage']}s ({duty_status['percentage_used']:.1f}%)")
        print(f"Remaining duty time: {duty_status['remaining_time']:.1f}s")
        print(f"Total up time: {state['total_up_time']:.1f}s")
        
        return {
            "success": True,
            "movement": direction,
            "start_height": current_height,
            "end_height": target_height,
            "distance": abs(delta),
            "duration": actual_duration,
            "duty_cycle": duty_status,
            "total_up_time": state["total_up_time"]
        }
        
    except Exception as e:
        print(f"Error during movement: {e}")
        return {
            "success": False,
            "error": str(e),
            "duty_cycle": get_duty_cycle_status(load_state())
        }
        
    finally:
        # Always clean up GPIO
        cleanup_gpio()


def test_sequence(movement_distance: float = 0.5, rest_time: float = 10.0) -> dict:
    """
    Execute a test sequence: move up, rest, move down
    
    Args:
        movement_distance: Distance to move in inches
        rest_time: Time to rest between movements in seconds
        
    Returns:
        dict with test results
    """
    start_height = LOWEST_HEIGHT
    up_target = start_height + movement_distance
    
    print("Starting test sequence...")
    print(f"Starting at: {start_height}\"")
    print(f"Will move to: {up_target}\"")
    print(f"Then rest for {rest_time} seconds")
    print(f"Then return to: {start_height}\"")
    
    results = []
    
    # Phase 1: Move up
    print(f"\n--- Phase 1: Moving UP {movement_distance} inches ---")
    result1 = move_to_height(up_target, start_height)
    results.append(result1)
    
    if not result1["success"]:
        return {"success": False, "phase": 1, "error": result1["error"]}
    
    # Phase 2: Rest
    print(f"\n--- Phase 2: Resting for {rest_time} seconds ---")
    import time
    time.sleep(rest_time)
    print("Rest complete.")
    
    # Phase 3: Move down
    print(f"\n--- Phase 3: Moving DOWN {movement_distance} inches ---")
    result2 = move_to_height(start_height, up_target)
    results.append(result2)
    
    if not result2["success"]:
        return {"success": False, "phase": 3, "error": result2["error"]}
    
    print("\nTest sequence complete!")
    
    return {
        "success": True,
        "results": results,
        "total_duration": sum(r.get("duration", 0) for r in results if r["success"]),
        "final_duty_cycle": results[-1]["duty_cycle"] if results else None
    }


def cli_interface():
    """Command-line interface for desk control"""
    try:
        current = float(input(f"Enter current height in inches ({LOWEST_HEIGHT}-{HIGHEST_HEIGHT}): "))
        target = float(input(f"Enter target height in inches ({LOWEST_HEIGHT}-{HIGHEST_HEIGHT}): "))
        result = move_to_height(target, current)
        
        if result["success"]:
            print("Movement completed successfully!")
        else:
            print(f"Movement failed: {result['error']}")
            
    except ValueError as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("\nOperation cancelled.")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_sequence()
    else:
        cli_interface()