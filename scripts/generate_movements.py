#!/usr/bin/env python3
"""
Generate movement configurations based on current duty cycle status.

This utility checks the current duty cycle usage and generates appropriate
movement configurations that will demonstrate both successful movements
and duty cycle limit protection.
"""

import json
from desk_controller import check_duty_cycle_status_before_execution, generate_safe_movement_suggestions

def generate_duty_cycle_test_config(output_file: str = "movement_configs.json"):
    """
    Generate movement configurations that will test duty cycle limits.
    
    Creates movements that:
    1. Respect the 30-second continuous runtime limit
    2. Use available capacity efficiently  
    3. Demonstrate successful movements within limits
    4. Show duty cycle protection when limits are exceeded
    """
    
    print("=== GENERATING MOVEMENT CONFIGS BASED ON CURRENT DUTY CYCLE ===")
    
    # Check current status
    status = check_duty_cycle_status_before_execution()
    
    remaining = status["remaining_capacity"]
    current_pos = status["current_position"]
    max_movement_time = status["max_single_movement"]
    
    # IMPORTANT: Respect 30-second continuous runtime limit
    MAX_CONTINUOUS_TIME = 30.0
    max_safe_distance = MAX_CONTINUOUS_TIME * 4.8  # 144 inches
    
    # But also respect height range [23.7-54.5]
    max_range_distance = 54.5 - 23.7  # 30.8 inches
    practical_max_distance = min(max_safe_distance, max_range_distance)  # 30.8 inches
    practical_max_time = practical_max_distance / 4.8  # 6.4 seconds
    
    print(f"Max distance by continuous runtime: {max_safe_distance:.1f} inches ({MAX_CONTINUOUS_TIME}s)")
    print(f"Max distance by height range: {max_range_distance:.1f} inches")
    print(f"Practical max distance: {practical_max_distance:.1f} inches ({practical_max_time:.1f}s)")
    
    # Calculate how many practical movements we can do
    full_movements_possible = int(remaining / practical_max_time)
    
    movements = []
    
    if remaining < 5:
        print("Very low capacity - generating minimal movements")
        movements = [
            {
                "id": "minimal_test",
                "description": f"Minimal movement due to low capacity ({remaining:.1f}s remaining)",
                "target_height": min(current_pos + 2.0, 54.0),
                "current_height": current_pos,
                "enabled": True
            }
        ]
    else:
        print(f"Generating {full_movements_possible + 2} movements to test duty cycle limits")
        
        # Generate movements that respect both limits
        pos = current_pos
        
        for i in range(full_movements_possible):
            # Alternate between small and medium movements within safe range
            if i % 2 == 0:
                # Medium movement up (within 30.8 inch limit)
                distance = min(15.0, 54.0 - pos)  # 15 inches = 3.1s
                target = min(54.0, pos + distance)
            else:
                # Medium movement down
                distance = min(15.0, pos - 24.0)  # 15 inches = 3.1s
                target = max(24.0, pos - distance)
            
            actual_distance = abs(target - pos)
            time_est = actual_distance / 4.8
            
            movements.append({
                "id": f"success_move_{i+1:02d}",
                "description": f"SUCCESS: {pos:.1f}→{target:.1f}\" ({actual_distance:.1f}in = {time_est:.1f}s)",
                "target_height": target,
                "current_height": pos,
                "enabled": True
            })
            pos = target
        
        # Add movements that should fail due to duty cycle (not continuous runtime)
        # These will be small enough to pass continuous runtime but exceed duty cycle
        movements.extend([
            {
                "id": "fail_duty_cycle_1",
                "description": f"FAIL: Should exceed duty cycle limit (small movement but no capacity)",
                "target_height": min(pos + 10.0, 54.0),  # Small 10-inch movement = 2.1s
                "current_height": pos,
                "enabled": True
            },
            {
                "id": "fail_duty_cycle_2", 
                "description": f"FAIL: Should definitely exceed duty cycle limit",
                "target_height": max(pos - 10.0, 24.0),  # Small 10-inch movement = 2.1s
                "current_height": pos,
                "enabled": True
            }
        ])
    
    config = {"movements": movements}
    
    # Save to file
    with open(output_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✅ Generated {len(movements)} movements in {output_file}")
    print(f"Expected: {full_movements_possible} successes, {len(movements) - full_movements_possible} duty cycle failures")
    print(f"All movements respect 30s continuous runtime limit")
    
    return config

if __name__ == "__main__":
    generate_duty_cycle_test_config()