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


def deploy_flows(work_pool: str = "default-process-pool"):
    """Deploy all Prefect flows"""
    try:
        from progressive_automations_python.deployment import create_deployments
        create_deployments(work_pool)
        return 0
    except Exception as e:
        print(f"Error deploying flows: {e}")
        return 1


def move_to_position(target: float, current: float = None):
    """Move desk to a specific position"""
    try:
        from progressive_automations_python.desk_controller import move_to_height
        result = move_to_height(target, current)
        
        if result["success"]:
            print(f"✅ Movement successful: {result}")
            return 0
        else:
            print(f"❌ Movement failed: {result.get('error', 'Unknown error')}")
            return 1
            
    except Exception as e:
        print(f"Error during movement: {e}")
        return 1


def run_test_sequence(distance: float = 0.5, rest: float = 10.0):
    """Run a test sequence"""
    try:
        from progressive_automations_python.desk_controller import test_sequence
        result = test_sequence(distance, rest)
        
        if result["success"]:
            print(f"✅ Test sequence successful")
            return 0
        else:
            print(f"❌ Test sequence failed: {result.get('error', 'Unknown error')}")
            return 1
            
    except Exception as e:
        print(f"Error during test sequence: {e}")
        return 1


def generate_movements():
    """Generate movement configurations"""
    try:
        from progressive_automations_python.generate_movements import generate_duty_cycle_test_config
        generate_duty_cycle_test_config()
        return 0
    except Exception as e:
        print(f"Error generating movements: {e}")
        return 1


def show_examples():
    """Show usage examples for async deployment"""
    try:
        from progressive_automations_python.deployment import get_deployment_examples
        print(get_deployment_examples())
        return 0
    except Exception as e:
        print(f"Error showing examples: {e}")
        return 1


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Progressive Automations Desk Lifter Control",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  progressive_automations_python --test UP
  progressive_automations_python --test DOWN
  progressive_automations_python --status
  progressive_automations_python --deploy
  progressive_automations_python --move 30.0 --current 24.0
  progressive_automations_python --test-sequence --distance 0.5 --rest 10.0
  progressive_automations_python --generate-movements
  progressive_automations_python --examples
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
    
    parser.add_argument(
        "--deploy",
        action="store_true",
        help="Deploy all Prefect flows to Prefect Cloud"
    )
    
    parser.add_argument(
        "--work-pool",
        type=str,
        default="default-process-pool",
        help="Work pool name for deployments (default: default-process-pool)"
    )
    
    parser.add_argument(
        "--move",
        type=float,
        metavar="TARGET",
        help="Move desk to target height in inches"
    )
    
    parser.add_argument(
        "--current",
        type=float,
        metavar="CURRENT",
        help="Current height in inches (optional, uses last known if not provided)"
    )
    
    parser.add_argument(
        "--test-sequence",
        action="store_true",
        help="Run a test sequence (move up, wait, move down)"
    )
    
    parser.add_argument(
        "--distance",
        type=float,
        default=0.5,
        help="Distance for test sequence in inches (default: 0.5)"
    )
    
    parser.add_argument(
        "--rest",
        type=float,
        default=10.0,
        help="Rest time for test sequence in seconds (default: 10.0)"
    )
    
    parser.add_argument(
        "--generate-movements",
        action="store_true",
        help="Generate movement configurations based on current duty cycle"
    )
    
    parser.add_argument(
        "--examples",
        action="store_true",
        help="Show examples for async deployment and position polling"
    )
    
    args = parser.parse_args()
    
    # Handle commands
    if args.test:
        return test_movement(args.test)
    elif args.status:
        return show_status()
    elif args.deploy:
        return deploy_flows(args.work_pool)
    elif args.move is not None:
        return move_to_position(args.move, args.current)
    elif args.test_sequence:
        return run_test_sequence(args.distance, args.rest)
    elif args.generate_movements:
        return generate_movements()
    elif args.examples:
        return show_examples()
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
