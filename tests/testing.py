"""
Testing utilities for desk lifter control.

These functions are for testing and troubleshooting only, not production use.
"""

import json
import os
from typing import Optional
from progressive_automations_python.config import LOWEST_HEIGHT
from progressive_automations_python.desk_controller import move_to_height, check_duty_cycle_status_before_execution
from progressive_automations_python.duty_cycle import check_movement_against_duty_cycle


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
    result1 = move_to_height(up_target)
    results.append(result1)
    
    if not result1["success"]:
        return {"success": False, "phase": 1, "error": result1.get("error", "Unknown error")}
    
    # Phase 2: Rest
    print(f"\n--- Phase 2: Resting for {rest_time} seconds ---")
    import time
    time.sleep(rest_time)
    print("Rest complete.")
    
    # Phase 3: Move down
    print(f"\n--- Phase 3: Moving DOWN {movement_distance} inches ---")
    result2 = move_to_height(start_height)
    results.append(result2)
    
    if not result2["success"]:
        return {"success": False, "phase": 3, "error": result2.get("error", "Unknown error")}
    
    print("\nTest sequence complete!")
    
    return {
        "success": True,
        "results": results,
        "total_duration": sum(r.get("duration", 0) for r in results if r["success"]),
        "final_duty_cycle": results[-1]["duty_cycle"] if results else None
    }


def load_movement_configs(config_file: str = "movement_configs.json") -> list:
    """Load movement configurations from JSON file"""
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
    
    print(f"Executing configured movement {movement_id}: {movement.get('description', '')}")
    
    result = move_to_height(target_height)
    
    if result["success"]:
        print(f"✅ Movement {movement_id} completed: {result['duration']:.1f}s, final height: {result['end_height']}\"")
    else:
        print(f"❌ Movement {movement_id} failed")
        raise ValueError("Movement failed")
    
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
