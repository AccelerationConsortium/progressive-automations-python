"""
High-level desk controller with height management and safety checks.

Combines movement control and duty cycle management to provide safe desk operations.
Handles height calculations, movement planning, and state management.
"""

from typing import Optional
from progressive_automations_python.config import (
    DUTY_CYCLE_MAX_ON_TIME,
    DUTY_CYCLE_PERIOD,
    LOWEST_HEIGHT,
    HIGHEST_HEIGHT,
    UP_RATE,
    DOWN_RATE
)
from progressive_automations_python.duty_cycle import (
    check_movement_against_duty_cycle,
    record_usage_period, 
    get_duty_cycle_status,
    get_current_duty_cycle_usage,
    show_duty_cycle_status,
    load_state, 
    save_state
)
from progressive_automations_python.movement_control import setup_gpio, cleanup_gpio, move_up, move_down


def check_duty_cycle_status_before_execution() -> dict:
    """
    Check current duty cycle status before executing movements.
    Returns comprehensive status information for decision making.
    
    Returns:
        dict: {
            "current_usage": float,     # Seconds used in current window
            "remaining_capacity": float, # Seconds remaining
            "percentage_used": float,   # Percentage of duty cycle used
            "max_single_movement": float, # Max movement time within height limits
            "movements_possible": int,   # Est. number of max movements possible
            "current_position": float,  # Current desk position
            "window_period": int,       # Duty cycle window (1200s)
            "recommendations": list     # Usage recommendations
        }
    """
    print("=== PRE-EXECUTION DUTY CYCLE STATUS CHECK ===")
    
    state = load_state()
    current_usage = get_current_duty_cycle_usage(state)
    remaining_capacity = DUTY_CYCLE_MAX_ON_TIME - current_usage
    percentage_used = (current_usage / DUTY_CYCLE_MAX_ON_TIME) * 100
    current_position = state.get("last_position", 24.0)
    
    # Calculate max possible movement within height range
    height_range_max = HIGHEST_HEIGHT - LOWEST_HEIGHT
    # Average rate for max movement estimation
    avg_rate = (UP_RATE + DOWN_RATE) / 2
    max_single_movement = height_range_max / avg_rate
    
    # Estimate how many max movements are possible
    movements_possible = int(remaining_capacity / max_single_movement) if remaining_capacity > 0 else 0
    
    # Display status
    print(f"Current usage: {current_usage:.1f}s / {DUTY_CYCLE_MAX_ON_TIME}s ({percentage_used:.1f}%)")
    print(f"Remaining capacity: {remaining_capacity:.1f}s")
    print(f"Current position: {current_position}\"")
    print(f"Max single movement: {max_single_movement:.1f}s (within height range)")
    print(f"Estimated large movements possible: {movements_possible}")
    print()
    
    return {
        "current_usage": current_usage,
        "remaining_capacity": remaining_capacity,
        "percentage_used": percentage_used,
        "max_single_movement": max_single_movement,
        "movements_possible": movements_possible,
        "current_position": current_position,
        "window_period": DUTY_CYCLE_PERIOD
    }


def move_to_height(target_height: float) -> dict:
    """
    Move desk to target height with safety checks and duty cycle enforcement
    
    Args:
        target_height: Desired height in inches
        
    Returns:
        dict with movement results and status information
    """
    # Validate height range
    if not (LOWEST_HEIGHT <= target_height <= HIGHEST_HEIGHT):
        raise ValueError(f"Target height {target_height}'' is out of range [{LOWEST_HEIGHT}-{HIGHEST_HEIGHT}].")
    
    # Setup GPIO
    setup_gpio()
    
    # Load current state
    state = load_state()
    
    # Get current height from state
    if state["last_position"] is None:
        cleanup_gpio()
        raise ValueError("No last known position in state file. Initialize position first.")
    
    current_height = state["last_position"]
    
    # Calculate movement requirements
    delta = target_height - current_height
    if abs(delta) < 0.01:
        cleanup_gpio()
        print(f"Already at {target_height}'' (within tolerance). No movement needed.")
        return {
            "success": True,
            "movement": "none",
            "message": f"Already at target height {target_height}''",
            "duty_cycle": get_duty_cycle_status(state)
        }
    
    # Determine direction and calculate time
    direction = "up" if delta > 0 else "down"
    rate = UP_RATE if delta > 0 else DOWN_RATE
    required_time = abs(delta) / rate
    
    # Check duty cycle limits
    check_result = check_movement_against_duty_cycle(target_height, current_height, UP_RATE, DOWN_RATE)
    
    if not check_result["allowed"]:
        cleanup_gpio()
        raise ValueError(check_result["error"])
    
    print(f"Duty cycle OK: {check_result['current_usage']:.1f}s + {check_result['estimated_duration']:.1f}s <= {DUTY_CYCLE_MAX_ON_TIME}s")
    
    # Execute movement
    move_func = move_up if delta > 0 else move_down
    start_time, end_time, actual_duration = move_func(required_time)
    
    # Record the usage period and update state
    state = record_usage_period(state, start_time, end_time, actual_duration)
    if delta > 0:
        state["total_up_time"] += actual_duration
    
    # Update position and save state
    state["last_position"] = target_height
    save_state(state)
    
    # Get final duty cycle info
    duty_status = get_duty_cycle_status(state)
    
    print(f"Arrived at {target_height}'' (approximate). State saved.")
    print(f"Duty cycle usage: {duty_status['current_usage']:.1f}s / {duty_status['max_usage']}s ({duty_status['percentage_used']:.1f}%)")
    print(f"Remaining duty time: {duty_status['remaining_time']:.1f}s")
    print(f"Total up time: {state['total_up_time']:.1f}s")
    
    # Always clean up GPIO
    cleanup_gpio()
    
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
