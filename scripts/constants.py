# GPIO pin constants for desk lifter control
# BCM numbering
UP_PIN = 18   # BCM numbering, physical pin 12  
DOWN_PIN = 17 # BCM numbering, physical pin 11

# Calibration data
LOWEST_HEIGHT = 23.7  # inches
HIGHEST_HEIGHT = 54.5  # inches
UP_RATE = 0.54  # inches per second
DOWN_RATE = 0.55  # inches per second

# Duty cycle constants
DUTY_CYCLE_PERIOD = 20 * 60  # 20 minutes in seconds
DUTY_CYCLE_MAX_ON_TIME = 2 * 60  # 2 minutes in seconds (10% of 20 minutes)
DUTY_CYCLE_PERCENTAGE = 0.10  # 10% duty cycle
MAX_CONTINUOUS_RUNTIME = 30  # Maximum continuous movement time in seconds

STATE_FILE = "lifter_state.json"