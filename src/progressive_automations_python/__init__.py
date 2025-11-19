import sys

if sys.version_info[:2] >= (3, 8):
    # TODO: Import directly (no need for conditional) when `python_requires = >= 3.8`
    from importlib.metadata import PackageNotFoundError, version  # pragma: no cover
else:
    from importlib_metadata import PackageNotFoundError, version  # pragma: no cover

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = "progressive-automations-python"
    __version__ = version(dist_name)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError

# Export main API
from progressive_automations_python.config import (
    LOWEST_HEIGHT,
    HIGHEST_HEIGHT,
    UP_RATE,
    DOWN_RATE,
    UP_PIN,
    DOWN_PIN
)

from progressive_automations_python.desk_controller import (
    move_to_height,
    check_duty_cycle_status_before_execution
)

from progressive_automations_python.duty_cycle import (
    load_state,
    save_state,
    get_duty_cycle_status,
    show_duty_cycle_status
)

from progressive_automations_python.prefect_flows import (
    simple_movement_flow,
)

from progressive_automations_python.deployment import (
    create_deployments
)

__all__ = [
    "__version__",
    "LOWEST_HEIGHT",
    "HIGHEST_HEIGHT",
    "UP_RATE",
    "DOWN_RATE",
    "UP_PIN",
    "DOWN_PIN",
    "move_to_height",
    "check_duty_cycle_status_before_execution",
    "load_state",
    "save_state",
    "get_duty_cycle_status",
    "show_duty_cycle_status",
    "simple_movement_flow",
    "create_deployments"
]
