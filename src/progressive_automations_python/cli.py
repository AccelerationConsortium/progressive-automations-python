"""
Command-line interface for progressive automations desk lifter control.
"""

import argparse
import sys


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











def main():
    """Main CLI entry point"""
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
    
    args = parser.parse_args()
    
    # Handle commands
    if args.test:
        return test_movement(args.test)
    elif args.status:
        return show_status()
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
