"""
Prefect flow for desk lifter control.

Simple flow execution - just call the decorated function directly.
"""

from progressive_automations_python.desk_controller import move_to_height

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-height", type=float, required=True, help="Target height in inches")
    args = parser.parse_args()
    
    print(f"Running Prefect flow: move_to_height({args.target_height})")
    result = move_to_height(args.target_height)
    print(f"Flow result: {result}")