"""
Command-line interface for progressive automations desk lifter control.
"""

import argparse
import logging
import sys

from progressive_automations_python import __version__

__author__ = "Sterling G. Baird"
__copyright__ = "Sterling G. Baird"
__license__ = "MIT"

_logger = logging.getLogger(__name__)


# ---- Python API ----
# The functions defined in this section can be imported by users in their
# Python scripts/interactive interpreter, e.g. via
# `from progressive_automations_python.skeleton import fib`,
# when using this Python module as a library.


def test_movement(direction: str):
    """Test UP or DOWN movement for 2 seconds"""
    try:
        # Import GPIO control functions
        from progressive_automations_python.movement_control import (
            setup_gpio, cleanup_gpio, press_up, release_up, press_down, release_down
        )
        import time
        
        setup_gpio()
        
        print(f"Testing {direction} movement for 2 seconds...")
        
        if direction.upper() == "UP":
            press_up()
            time.sleep(2.0)
            release_up()
        elif direction.upper() == "DOWN":
            press_down()
            time.sleep(2.0)
            release_down()
        else:
            print(f"Invalid direction: {direction}. Use UP or DOWN.")
            return 1
        
        cleanup_gpio()
        print(f"{direction} test complete!")
        return 0
        
    except ImportError as e:
        print(f"Error: GPIO library not available. This command must be run on a Raspberry Pi.")
        print(f"Details: {e}")
        return 1
    except Exception as e:
        print(f"Error during test: {e}")
        return 1


def show_status():
    """Show current duty cycle status"""
    try:
        from progressive_automations_python.duty_cycle import show_duty_cycle_status
        show_duty_cycle_status()
        return 0
    except Exception as e:
        print(f"Error showing status: {e}")
        return 1


# ---- CLI ----
# The functions defined in this section are wrappers around the main Python
# API allowing them to be called directly from the terminal as a CLI
# executable/script.


def parse_args(args):
    """Parse command line parameters

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--help"]``).

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    parser = argparse.ArgumentParser(
        description="Progressive Automations Desk Lifter Control",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples (for testing/debugging only):
  progressive_automations_python --test UP
  progressive_automations_python --test DOWN
  progressive_automations_python --status
        """
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"progressive-automations-python {__version__}",
    )
    parser.add_argument(
        "--test",
        type=str,
        choices=["UP", "DOWN", "up", "down"],
        help="Test UP or DOWN movement for 2 seconds"
    )
    
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current duty cycle status"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        help="set loglevel to INFO",
        action="store_const",
        const=logging.INFO,
    )
    parser.add_argument(
        "-vv",
        "--very-verbose",
        dest="loglevel",
        help="set loglevel to DEBUG",
        action="store_const",
        const=logging.DEBUG,
    )
    return parser.parse_args(args)


def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(
        level=loglevel, stream=sys.stdout, format=logformat, datefmt="%Y-%m-%d %H:%M:%S"
    )


def main(args):
    """Wrapper allowing CLI functions to be called with string arguments in a CLI fashion

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--verbose", "--test", "UP"]``).
    """
    args = parse_args(args)
    setup_logging(args.loglevel)
    _logger.debug("Starting desk lifter control...")
    
    # Handle commands
    if args.test:
        result = test_movement(args.test)
        sys.exit(result)
    elif args.status:
        result = show_status()
        sys.exit(result)
    else:
        # No command specified, print help
        print("No command specified. Use --help for usage information.")
        sys.exit(0)


def run():
    """Calls :func:`main` passing the CLI arguments extracted from :obj:`sys.argv`

    This function can be used as entry point to create console scripts with setuptools.
    """
    main(sys.argv[1:])


if __name__ == "__main__":
    # ^  This is a guard statement that will prevent the following code from
    #    being executed in the case someone imports this file instead of
    #    executing it as a script.
    #    https://docs.python.org/3/library/__main__.html

    # After installing your project with pip, users can also run your Python
    # modules as scripts via the ``-m`` flag, as defined in PEP 338::
    #
    #     python -m progressive_automations_python.skeleton 42
    #
    run()
