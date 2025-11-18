"""
Constants module - imports from user-editable config.py

For backward compatibility and to provide a single import point.
Edit config.py to customize values for your setup.
"""

from progressive_automations_python.config import (
    UP_PIN,
    DOWN_PIN,
    LOWEST_HEIGHT,
    HIGHEST_HEIGHT,
    UP_RATE,
    DOWN_RATE
)

__all__ = [
    'UP_PIN',
    'DOWN_PIN',
    'LOWEST_HEIGHT',
    'HIGHEST_HEIGHT',
    'UP_RATE',
    'DOWN_RATE'
]