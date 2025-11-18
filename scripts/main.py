#!/usr/bin/env python3
"""
Main entry point for the desk control system.

This script provides a unified interface to all desk control functionality:
- Direct movement control
- Test sequences  
- Prefect deployment and automation
- Duty cycle monitoring

Usage Examples:
    python main.py                          # Interactive CLI
    python main.py test                     # Run test sequence
    python main.py deploy                   # Deploy Prefect automation
    python main.py move 25.0 30.0          # Move from 25" to 30"
    python main.py status                   # Show duty cycle status
"""

import sys
import os

# Add the scripts directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import from the modular files
from desk_controller import move_to_height, test_sequence, cli_interface
from duty_cycle import get_duty_cycle_status, load_state


def show_help():
    """Display help information"""
    print(__doc__)


def show_duty_cycle_status():
    """Show current duty cycle status"""
    state = load_state()
    status = get_duty_cycle_status(state)
    
    print("=== Duty Cycle Status ===")
    print(f"Current usage: {status['current_usage']:.1f}s / {status['max_usage']}s")
    print(f"Percentage used: {status['percentage_used']:.1f}%")
    print(f"Remaining time: {status['remaining_time']:.1f}s")
    print(f"Window period: {status['window_period']}s (20 minutes)")
    print(f"Total periods tracked: {len(state['usage_periods'])}")
    
    if state.get("last_position"):
        print(f"Last known position: {state['last_position']}\"")
    if state.get("total_up_time"):
        print(f"Total up time (all time): {state['total_up_time']:.1f}s")


def main():
    """Main entry point"""
    if len(sys.argv) == 1:
        # No arguments - run interactive CLI
        cli_interface()
        
    elif sys.argv[1] == "help" or sys.argv[1] == "--help" or sys.argv[1] == "-h":
        show_help()
        
    elif sys.argv[1] == "test":
        # Run test sequence
        distance = 0.5  # default
        rest_time = 10.0  # default
        
        if len(sys.argv) > 2:
            distance = float(sys.argv[2])
        if len(sys.argv) > 3:
            rest_time = float(sys.argv[3])
            
        result = test_sequence(distance, rest_time)
        if not result["success"]:
            print(f"Test failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
            
    elif sys.argv[1] == "move":
        # Direct movement command
        if len(sys.argv) < 4:
            print("Usage: python main.py move <current_height> <target_height>")
            sys.exit(1)
            
        current_height = float(sys.argv[2])
        target_height = float(sys.argv[3])
        
        result = move_to_height(target_height, current_height)
        if not result["success"]:
            print(f"Movement failed: {result['error']}")
            sys.exit(1)
            
    elif sys.argv[1] == "status":
        # Show duty cycle status
        show_duty_cycle_status()
        
    elif sys.argv[1] == "deploy":
        if "--immediate" in sys.argv:
            from prefect_flows import deploy_test_sequence_immediate
            deploy_test_sequence_immediate()
        else:
            from prefect_flows import deploy_test_sequence
            deploy_test_sequence()
            
    elif sys.argv[1] == "prefect-test":
        # Run test sequence via Prefect
        try:
            from prefect_flows import custom_test_sequence_flow
            
            distance = 0.5  # default
            rest_time = 10.0  # default
            
            if len(sys.argv) > 2:
                distance = float(sys.argv[2])
            if len(sys.argv) > 3:
                rest_time = float(sys.argv[3])
                
            custom_test_sequence_flow(distance, rest_time)
            
        except ImportError as e:
            print(f"Prefect not available: {e}")
            print("Install with: pip install prefect")
            sys.exit(1)
            
    else:
        print(f"Unknown command: {sys.argv[1]}")
        print("Run 'python main.py help' for usage information")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)