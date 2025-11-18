"""
Duty cycle management for motor protection.

Implements a 10% duty cycle (2 minutes on, 18 minutes off) using a sliding window approach.
Tracks individual usage periods and enforces both continuous runtime and total usage limits.
"""

import time
import json
import os
from constants import LOWEST_HEIGHT
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional

# Duty cycle constants
DUTY_CYCLE_PERIOD = 1200  # 20 minutes in seconds
DUTY_CYCLE_MAX_ON_TIME = 120  # 2 minutes in seconds (10% of 20 minutes)
DUTY_CYCLE_PERCENTAGE = 0.10  # 10% duty cycle
MAX_CONTINUOUS_RUNTIME = 30  # Maximum continuous movement time in seconds

STATE_FILE = "lifter_state.json"


def load_state():
    """Load the current state from file"""
    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
        
        # Ensure all required keys exist with proper defaults
        if "usage_periods" not in state:
            state["usage_periods"] = []
        if "last_position" not in state:
            state["last_position"] = LOWEST_HEIGHT  # Default to minimum height
        if "total_up_time" not in state:
            state["total_up_time"] = 0.0
        
        return state
    except FileNotFoundError:
        # Return default state if file doesn't exist
        return {
            "usage_periods": [],
            "last_position": LOWEST_HEIGHT,
            "total_up_time": 0.0
        }


def save_state(state: Dict[str, Any]) -> None:
    """Save state to JSON file"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def clean_old_usage_periods(state: Dict[str, Any]) -> Dict[str, Any]:
    """Remove usage periods older than the duty cycle period"""
    current_time = time.time()
    cutoff_time = current_time - DUTY_CYCLE_PERIOD
    
    # Keep only periods that end after the cutoff time
    state["usage_periods"] = [
        period for period in state["usage_periods"] 
        if period[1] > cutoff_time  # period[1] is end_timestamp
    ]
    return state


def get_current_duty_cycle_usage(state: Dict[str, Any]) -> float:
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


def record_usage_period(state: Dict[str, Any], start_time: float, end_time: float, duration: float) -> Dict[str, Any]:
    """Record a usage period in the duty cycle tracking"""
    state["usage_periods"].append([start_time, end_time, duration])
    return state


def check_movement_against_duty_cycle(target_height: float, current_height: Optional[float] = None, up_rate: float = 4.8, down_rate: float = 4.8) -> dict:
    """
    Check if a movement to a target height would exceed duty cycle limits.
    
    Args:
        target_height: Target height in mm/inches
        current_height: Current height (if None, loads from state)
        up_rate: Movement rate upward (mm/s or inches/s)
        down_rate: Movement rate downward (mm/s or inches/s)
        
    Returns:
        dict: {
            "allowed": bool,
            "error": str or None,
            "estimated_duration": float,
            "current_usage": float,
            "remaining_capacity": float,
            "movement_type": "UP" or "DOWN",
            "distance": float
        }
    """
    # Load current state
    state = load_state()
    
    if current_height is None:
        current_height = state.get("last_position", LOWEST_HEIGHT)
    
    # Calculate movement requirements
    distance = abs(target_height - current_height)
    movement_type = "UP" if target_height > current_height else "DOWN"
    rate = up_rate if movement_type == "UP" else down_rate
    
    if distance == 0:
        return {
            "allowed": True,
            "error": None,
            "estimated_duration": 0.0,
            "current_usage": get_current_duty_cycle_usage(state),
            "remaining_capacity": DUTY_CYCLE_MAX_ON_TIME - get_current_duty_cycle_usage(state),
            "movement_type": movement_type,
            "distance": distance
        }
    
    estimated_duration = distance / rate
    
    # Check continuous runtime limit
    if estimated_duration > MAX_CONTINUOUS_RUNTIME:
        return {
            "allowed": False,
            "error": f"Movement would take {estimated_duration:.1f}s, exceeding {MAX_CONTINUOUS_RUNTIME}s continuous runtime limit",
            "estimated_duration": estimated_duration,
            "current_usage": get_current_duty_cycle_usage(state),
            "remaining_capacity": DUTY_CYCLE_MAX_ON_TIME - get_current_duty_cycle_usage(state),
            "movement_type": movement_type,
            "distance": distance
        }
    
    # Check duty cycle limits
    current_usage = get_current_duty_cycle_usage(state)
    remaining_capacity = DUTY_CYCLE_MAX_ON_TIME - current_usage
    
    if estimated_duration > remaining_capacity:
        return {
            "allowed": False,
            "error": f"Movement would exceed 10% duty cycle limit. Current usage: {current_usage:.1f}s, Remaining: {remaining_capacity:.1f}s in {DUTY_CYCLE_PERIOD:.0f}s window",
            "estimated_duration": estimated_duration,
            "current_usage": current_usage,
            "remaining_capacity": remaining_capacity,
            "movement_type": movement_type,
            "distance": distance
        }
    
    return {
        "allowed": True,
        "error": None,
        "estimated_duration": estimated_duration,
        "current_usage": current_usage,
        "remaining_capacity": remaining_capacity,
        "movement_type": movement_type,
        "distance": distance
    }


def get_duty_cycle_status(state: Dict[str, Any]) -> Dict[str, float]:
    """Get current duty cycle status information"""
    current_usage = get_current_duty_cycle_usage(state)
    remaining_time = max(0, DUTY_CYCLE_MAX_ON_TIME - current_usage)
    percentage_used = current_usage / DUTY_CYCLE_MAX_ON_TIME * 100
    
    return {
        "current_usage": current_usage,
        "max_usage": DUTY_CYCLE_MAX_ON_TIME,
        "remaining_time": remaining_time,
        "percentage_used": percentage_used,
        "window_period": DUTY_CYCLE_PERIOD
    }


def show_duty_cycle_status():
    """Display current duty cycle status in a user-friendly format"""
    state = load_state()
    status = get_duty_cycle_status(state)
    current_usage = get_current_duty_cycle_usage(state)
    
    print("Current Duty Cycle Status:")
    print(f"  Current usage: {current_usage:.2f}s / {status['max_usage']}s")
    print(f"  Percentage used: {status['percentage_used']:.2f}%")
    print(f"  Remaining time: {status['remaining_time']:.2f}s")
    print(f"  Window period: {status['window_period']}s ({status['window_period']/60:.0f} minutes)")
    
    if len(state.get("usage_periods", [])) > 0:
        print(f"  Recent usage periods: {len(state['usage_periods'])}")
        print(f"  Total up time (all time): {state.get('total_up_time', 0):.1f}s")