"""
High-level desk controller with height management and safety checks.

Combines movement control and duty cycle management to provide safe desk operations.
Handles height calculations, movement planning, and state management.
"""

from typing import Optional
from duty_cycle import (
    check_movement_against_duty_cycle,
    record_usage_period, 
    get_duty_cycle_status,
    get_current_duty_cycle_usage,
    show_duty_cycle_status,
    load_state, 
    save_state,
    DUTY_CYCLE_MAX_ON_TIME,
    DUTY_CYCLE_PERIOD
)
from movement_control import setup_gpio, cleanup_gpio, move_up, move_down


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
    
    # Calculate max possible movement within height range [23.7-54.5]
    height_range_max = 54.5 - 23.7  # 30.8 inches max movement
    max_single_movement = height_range_max / 4.8  # 6.4 seconds
    
    # Estimate how many max movements are possible
    movements_possible = int(remaining_capacity / max_single_movement) if remaining_capacity > 0 else 0
    
    # Generate recommendations
    recommendations = []
    if remaining_capacity < 10:
        recommendations.append("⚠️ Very low duty cycle remaining - consider waiting")
    elif remaining_capacity < 30:
        recommendations.append("⚠️ Low duty cycle remaining - use small movements only")
    elif percentage_used > 80:
        recommendations.append("⚠️ High duty cycle usage - plan movements carefully")
    else:
        recommendations.append("✅ Good duty cycle capacity available")
    
    if movements_possible == 0:
        recommendations.append("❌ No large movements possible - only small adjustments")
    elif movements_possible < 3:
        recommendations.append(f"⚠️ Only ~{movements_possible} large movements possible")
    else:
        recommendations.append(f"✅ ~{movements_possible} large movements possible")
    
    # Display status
    print(f"Current usage: {current_usage:.1f}s / {DUTY_CYCLE_MAX_ON_TIME}s ({percentage_used:.1f}%)")
    print(f"Remaining capacity: {remaining_capacity:.1f}s")
    print(f"Current position: {current_position}\"")
    print(f"Max single movement: {max_single_movement:.1f}s (within height range)")
    print(f"Estimated large movements possible: {movements_possible}")
    print()
    print("Recommendations:")
    for rec in recommendations:
        print(f"  {rec}")
    print()
    
    return {
        "current_usage": current_usage,
        "remaining_capacity": remaining_capacity,
        "percentage_used": percentage_used,
        "max_single_movement": max_single_movement,
        "movements_possible": movements_possible,
        "current_position": current_position,
        "window_period": DUTY_CYCLE_PERIOD,
        "recommendations": recommendations
    }


def generate_safe_movement_suggestions(max_movements: int = 5) -> list:
    """
    Generate safe movement suggestions based on current duty cycle status.
    
    Args:
        max_movements: Maximum number of movements to suggest
        
    Returns:
        list: List of suggested movements within safety limits
    """
    status = check_duty_cycle_status_before_execution()
    
    current_pos = status["current_position"]
    remaining_capacity = status["remaining_capacity"]
    max_single_time = status["max_single_movement"]
    
    suggestions = []
    
    if remaining_capacity < 5:
        # Only tiny movements
        suggestions.append({
            "id": "tiny_up",
            "description": f"Tiny up movement: {current_pos}\" → {current_pos + 1:.1f}\" (0.2s)",
            "target_height": current_pos + 1.0,
            "current_height": current_pos,
            "enabled": True
        })
        suggestions.append({
            "id": "tiny_down", 
            "description": f"Tiny down movement: {current_pos}\" → {current_pos - 1:.1f}\" (0.2s)",
            "target_height": current_pos - 1.0,
            "current_height": current_pos,
            "enabled": True
        })
    elif remaining_capacity < 15:
        # Small movements only
        for i in range(min(max_movements, 3)):
            up_target = min(current_pos + 5, 54.0)
            down_target = max(current_pos - 5, 24.0)
            
            suggestions.append({
                "id": f"small_movement_{i+1}",
                "description": f"Small movement: {current_pos}\" → {up_target}\" (1.0s)",
                "target_height": up_target,
                "current_height": current_pos,
                "enabled": True
            })
            current_pos = up_target
    else:
        # Can do larger movements
        positions = [30.0, 45.0, 35.0, 50.0, 25.0, 40.0]
        
        for i in range(min(max_movements, len(positions))):
            target = positions[i]
            if 23.7 <= target <= 54.5:  # Within safe range
                estimated_time = abs(target - current_pos) / 4.8
                
                if estimated_time <= remaining_capacity:
                    suggestions.append({
                        "id": f"suggested_move_{i+1}",
                        "description": f"Suggested movement: {current_pos:.1f}\" → {target}\" ({estimated_time:.1f}s)",
                        "target_height": target,
                        "current_height": current_pos,
                        "enabled": True
                    })
                    current_pos = target
                    remaining_capacity -= estimated_time
    
    return suggestions

try:
    from constants import LOWEST_HEIGHT, HIGHEST_HEIGHT, UP_RATE, DOWN_RATE
except ImportError:
    # Fallback values if constants not available
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
            
            # Check duty cycle limits using the new function
            check_result = check_movement_against_duty_cycle(target_height, current_height, UP_RATE, DOWN_RATE)
            
            if not check_result["allowed"]:
                raise ValueError(check_result["error"])
            
            print(f"Duty cycle OK: {check_result['current_usage']:.1f}s + {check_result['estimated_duration']:.1f}s <= {DUTY_CYCLE_MAX_ON_TIME}s")
            
            # Execute movement and get actual timing
            start_time, end_time, actual_duration = move_up(required_time)
            
            # Record the usage period and update state
            state = record_usage_period(state, start_time, end_time, actual_duration)
            state["total_up_time"] += actual_duration
        else:
            # Moving down
            required_time = abs(delta) / DOWN_RATE
            direction = "down"
            
            # Check duty cycle limits using the new function
            check_result = check_movement_against_duty_cycle(target_height, current_height, UP_RATE, DOWN_RATE)
            
            if not check_result["allowed"]:
                raise ValueError(check_result["error"])
                
            print(f"Duty cycle OK: {check_result['current_usage']:.1f}s + {check_result['estimated_duration']:.1f}s <= {DUTY_CYCLE_MAX_ON_TIME}s")
            
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


def load_movement_configs(config_file: str = "movement_configs.json") -> list:
    """Load movement configurations from JSON file"""
    import json
    import os
    
    print(f"Loading movement configurations from {config_file}")
    
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configuration file {config_file} not found")
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    # Filter for enabled movements only
    enabled_movements = [m for m in config.get("movements", []) if m.get("enabled", True)]
    
    print(f"Found {len(enabled_movements)} enabled movements")
    return enabled_movements


def validate_movement_config(movement: dict) -> dict:
    """Validate a movement configuration before execution"""
    movement_id = movement.get("id", "unknown")
    target_height = movement["target_height"]
    current_height = movement.get("current_height")
    
    print(f"Validating movement {movement_id}: {current_height}\" → {target_height}\"")
    
    # Check duty cycle limits
    check_result = check_movement_against_duty_cycle(target_height, current_height)
    
    if not check_result["allowed"]:
        error_msg = f"Movement {movement_id} rejected: {check_result['error']}"
        print(f"❌ {error_msg}")
        raise ValueError(error_msg)
    
    print(f"✅ Movement {movement_id} validated: {check_result['estimated_duration']:.1f}s, {check_result['movement_type']}")
    return check_result


def execute_movement_config(movement: dict) -> dict:
    """Execute a movement from configuration"""
    movement_id = movement.get("id", "unknown")
    target_height = movement["target_height"]
    current_height = movement.get("current_height")
    
    print(f"Executing configured movement {movement_id}: {movement.get('description', '')}")
    
    result = move_to_height(target_height, current_height)
    
    if result["success"]:
        print(f"✅ Movement {movement_id} completed: {result['duration']:.1f}s, final height: {result['end_height']}\"")
    else:
        print(f"❌ Movement {movement_id} failed: {result['error']}")
        raise ValueError(result["error"])
    
    return result


def execute_custom_movements(config_file: str = "movement_configs.json") -> dict:
    """Execute custom movements from configuration file"""
    print("=== CUSTOM MOVEMENTS EXECUTION ===")
    
    # ALWAYS check duty cycle status before execution
    duty_status = check_duty_cycle_status_before_execution()
    
    # If very low capacity, warn and potentially abort
    if duty_status["remaining_capacity"] < 1.0:
        print("❌ EXECUTION ABORTED: Insufficient duty cycle capacity remaining")
        return {
            "success": False, 
            "error": "Insufficient duty cycle capacity",
            "duty_status": duty_status
        }
    
    # Load movement configurations
    print("Loading movement configurations from movement_configs.json")
    movements = load_movement_configs(config_file)
    
    if not movements:
        print("⚠️ No enabled movements found in configuration")
        return {"success": False, "error": "No movements to execute"}
    
    results = []
    
    for movement in movements:
        movement_id = movement.get("id", "unknown")
        print(f"\nProcessing movement: {movement_id}")
        
        try:
            # Validate movement first
            validation_result = validate_movement_config(movement)
            
            # Execute the movement if validation passed
            execution_result = execute_movement_config(movement)
            
            results.append({
                "movement_id": movement_id,
                "success": True,
                "validation": validation_result,
                "execution": execution_result
            })
            
        except Exception as e:
            print(f"❌ Movement {movement_id} failed: {str(e)}")
            results.append({
                "movement_id": movement_id,
                "success": False,
                "error": str(e)
            })
            # Continue with remaining movements
    
    successful_movements = [r for r in results if r["success"]]
    failed_movements = [r for r in results if not r["success"]]
    
    print(f"\n=== EXECUTION SUMMARY ===")
    print(f"Total movements: {len(results)}")
    print(f"Successful: {len(successful_movements)}")
    print(f"Failed: {len(failed_movements)}")
    
    # Show final duty cycle status
    print(f"\n=== FINAL DUTY CYCLE STATUS ===")
    final_status = check_duty_cycle_status_before_execution()
    
    return {
        "success": len(failed_movements) == 0,
        "total_movements": len(results),
        "successful": len(successful_movements),
        "failed": len(failed_movements),
        "results": results,
        "initial_duty_status": duty_status,
        "final_duty_status": final_status
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