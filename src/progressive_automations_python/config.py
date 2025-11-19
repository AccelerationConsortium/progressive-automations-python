"""
User-editable configuration for desk lifter control.

Edit these values during initial setup to match your hardware and requirements.
"""

# =============================================================================
# GPIO PIN CONFIGURATION
# =============================================================================
# BCM pin numbering
UP_PIN = 18   # BCM numbering, physical pin 12  
DOWN_PIN = 17 # BCM numbering, physical pin 11


# =============================================================================
# CALIBRATION DATA
# =============================================================================
# Measure these values for your specific desk lifter setup
LOWEST_HEIGHT = 23.7   # inches - minimum height position
HIGHEST_HEIGHT = 54.5  # inches - maximum height position
UP_RATE = 0.54         # inches per second - measured movement rate going up
DOWN_RATE = 0.55       # inches per second - measured movement rate going down


# =============================================================================
# DUTY CYCLE LIMITS (MOTOR PROTECTION)
# =============================================================================
# These values protect the motor from overheating
# Adjust only if your motor specs differ from standard PA desk lifters

# Duty cycle percentage (e.g., 0.10 = 10% = 2 min on, 18 min off)
DUTY_CYCLE_PERCENTAGE = 0.10

# Sliding window period in seconds (default: 1200s = 20 minutes)
DUTY_CYCLE_PERIOD = 1200  

# Maximum total on-time within the window (default: 120s = 2 minutes)
# Calculated as: DUTY_CYCLE_PERIOD * DUTY_CYCLE_PERCENTAGE
DUTY_CYCLE_MAX_ON_TIME = 120  

# Maximum continuous runtime in seconds (default: 45s)
# This prevents single long movements from damaging the motor
MAX_CONTINUOUS_RUNTIME = 45


# =============================================================================
# STATE MANAGEMENT
# =============================================================================
# File to store persistent state (position, duty cycle usage, etc.)
STATE_FILE = "lifter_state.json"


# =============================================================================
# VALIDATION
# =============================================================================
def validate_config():
    """Validate configuration values"""
    errors = []
    
    # Validate height range
    if LOWEST_HEIGHT >= HIGHEST_HEIGHT:
        errors.append(f"LOWEST_HEIGHT ({LOWEST_HEIGHT}) must be less than HIGHEST_HEIGHT ({HIGHEST_HEIGHT})")
    
    # Validate movement rates
    if UP_RATE <= 0:
        errors.append(f"UP_RATE ({UP_RATE}) must be positive")
    if DOWN_RATE <= 0:
        errors.append(f"DOWN_RATE ({DOWN_RATE}) must be positive")
    
    # Validate duty cycle
    if not (0 < DUTY_CYCLE_PERCENTAGE <= 1.0):
        errors.append(f"DUTY_CYCLE_PERCENTAGE ({DUTY_CYCLE_PERCENTAGE}) must be between 0 and 1")
    
    if DUTY_CYCLE_MAX_ON_TIME > DUTY_CYCLE_PERIOD:
        errors.append(f"DUTY_CYCLE_MAX_ON_TIME ({DUTY_CYCLE_MAX_ON_TIME}) cannot exceed DUTY_CYCLE_PERIOD ({DUTY_CYCLE_PERIOD})")
    
    expected_max_on = DUTY_CYCLE_PERIOD * DUTY_CYCLE_PERCENTAGE
    if abs(DUTY_CYCLE_MAX_ON_TIME - expected_max_on) > 1:
        errors.append(
            f"DUTY_CYCLE_MAX_ON_TIME ({DUTY_CYCLE_MAX_ON_TIME}) should equal "
            f"DUTY_CYCLE_PERIOD * DUTY_CYCLE_PERCENTAGE ({expected_max_on:.1f})"
        )
    
    if MAX_CONTINUOUS_RUNTIME > DUTY_CYCLE_MAX_ON_TIME:
        errors.append(
            f"MAX_CONTINUOUS_RUNTIME ({MAX_CONTINUOUS_RUNTIME}) cannot exceed "
            f"DUTY_CYCLE_MAX_ON_TIME ({DUTY_CYCLE_MAX_ON_TIME})"
        )
    
    if errors:
        raise ValueError("Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors))
    
    return True


# Validate on import
validate_config()


# =============================================================================
# SMOKE TEST PARAMETERS
# =============================================================================
# Quick test parameters for initial validation and debugging
# These are NOT used in production - only for manual testing

SMOKE_TEST = {
    # Small movement for quick testing (inches)
    "movement_distance": 0.5,
    
    # Short wait time for test sequences (seconds)
    "rest_time": 5.0,
    
    # Test target heights within safe range
    "test_heights": [24.0, 25.0, 24.5],
    
    # Quick duty cycle test (uses minimal capacity)
    "quick_cycle_test": True
}
