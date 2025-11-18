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
from typing import List, Tuple, Dict, Any

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


def get_remaining_duty_time(state: Dict[str, Any]) -> float:
    """Get remaining duty cycle time in seconds"""
    current_usage = get_current_duty_cycle_usage(state)
    return max(0, DUTY_CYCLE_MAX_ON_TIME - current_usage)


def record_usage_period(state: Dict[str, Any], start_time: float, end_time: float, duration: float) -> Dict[str, Any]:
    """Record a usage period in the duty cycle tracking"""
    state["usage_periods"].append([start_time, end_time, duration])
    return state


def check_duty_cycle_limits(state: Dict[str, Any], required_time: float) -> Tuple[bool, Dict[str, Any], str]:
    """
    Check if the movement is within duty cycle limits using sliding window
    
    Returns:
        (is_valid, updated_state, info_message)
    """
    # Clean old periods and get current usage
    state = clean_old_usage_periods(state)
    current_usage = get_current_duty_cycle_usage(state)
    
    # Check continuous runtime limit
    if required_time > MAX_CONTINUOUS_RUNTIME:
        error_msg = f"Movement duration {required_time:.1f}s exceeds maximum continuous runtime of {MAX_CONTINUOUS_RUNTIME}s"
        return False, state, error_msg
    
    # Check if adding this movement would exceed the duty cycle limit
    if current_usage + required_time > DUTY_CYCLE_MAX_ON_TIME:
        remaining_time = DUTY_CYCLE_MAX_ON_TIME - current_usage
        error_msg = f"Movement would exceed {DUTY_CYCLE_PERCENTAGE*100:.0f}% duty cycle limit. Current usage: {current_usage:.1f}s, Remaining: {remaining_time:.1f}s in {DUTY_CYCLE_PERIOD}s window"
        return False, state, error_msg
    
    info_msg = f"Duty cycle OK: {current_usage:.1f}s + {required_time:.1f}s <= {DUTY_CYCLE_MAX_ON_TIME}s ({DUTY_CYCLE_PERCENTAGE*100:.0f}% of {DUTY_CYCLE_PERIOD}s)"
    return True, state, info_msg


def get_duty_cycle_status(state: Dict[str, Any]) -> Dict[str, float]:
    """Get current duty cycle status information"""
    current_usage = get_current_duty_cycle_usage(state)
    remaining_time = get_remaining_duty_time(state)
    percentage_used = current_usage / DUTY_CYCLE_MAX_ON_TIME * 100
    
    return {
        "current_usage": current_usage,
        "max_usage": DUTY_CYCLE_MAX_ON_TIME,
        "remaining_time": remaining_time,
        "percentage_used": percentage_used,
        "window_period": DUTY_CYCLE_PERIOD
    }