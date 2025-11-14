#!/usr/bin/env python3
"""
Basic application for controlling LG-07 lift via FLTCON on Raspberry Pi.

This provides a simple command-line interface for lift control.
For production use, consider adding:
- Web API (Flask/FastAPI)
- Configuration file support
- Position feedback
- Safety limits
- Logging
"""

import sys
import signal
import argparse
from progressive_automations_python.pi.lg07_lift.lift_driver import (
    press_up, press_down, nudge, emergency_stop, cleanup
)

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully."""
    print("\n⏹️  Received signal, stopping lift and cleaning up...")
    emergency_stop()
    cleanup()
    sys.exit(0)

def main():
    """Main application entry point."""
    # Set up signal handlers for clean shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    parser = argparse.ArgumentParser(description='LG-07 Lift Control')
    parser.add_argument('command', choices=['up', 'down', 'nudge'],
                       help='Movement command')
    parser.add_argument('direction', nargs='?', choices=['up', 'down'],
                       help='Direction for nudge command')
    parser.add_argument('-t', '--time', type=float, default=1.0,
                       help='Movement time in seconds (default: 1.0)')
    parser.add_argument('--test', action='store_true',
                       help='Run hardware test instead of single command')

    args = parser.parse_args()

    try:
        if args.test:
            # Run the hardware test
            print("🧪 Running hardware test...")
            from test_hardware import test_sequence
            test_sequence()
        elif args.command == 'up':
            print(f"⬆️  Moving UP for {args.time} seconds...")
            press_up(args.time)
            print("✅ UP movement completed")
        elif args.command == 'down':
            print(f"⬇️  Moving DOWN for {args.time} seconds...")
            press_down(args.time)
            print("✅ DOWN movement completed")
        elif args.command == 'nudge':
            if not args.direction:
                print("❌ Direction required for nudge command")
                sys.exit(1)
            print(f"⬆️  Nudging {args.direction.upper()} for {args.time} seconds...")
            nudge(args.direction, args.time)
            print("✅ Nudge completed")

    except Exception as e:
        print(f"❌ Error: {e}")
        emergency_stop()
        sys.exit(1)

    finally:
        cleanup()

if __name__ == "__main__":
    main()
