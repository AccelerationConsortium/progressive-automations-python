#!/usr/bin/env python3
"""
Hardware test script for LG-07 lift control on Raspberry Pi.
Run this script directly on your Raspberry Pi to test the FLTCON connection.

Usage:
    python test_hardware.py

Make sure:
1. Relays are connected to GPIO pins 17 (UP) and 27 (DOWN)
2. Relays are connected to FLTCON UP/DOWN buttons
3. FLTCON is powered and connected to LG-07 lift
4. Run with: python test_hardware.py
"""

import sys
import os
import time

# Add the package to path
sys.path.insert(0, os.path.dirname(__file__))

from progressive_automations_python.pi.lg07_lift.lift_driver import (
    press_up, press_down, nudge, emergency_stop, cleanup
)

def test_sequence():
    """Run a test sequence of movements."""
    print("🧪 Starting LG-07 Lift Hardware Test")
    print("=" * 40)

    try:
        # Test 1: Small up movement
        print("Test 1: Small UP movement (0.5 seconds)")
        print("Watch the lift - it should move UP slightly")
        input("Press Enter to start test 1...")
        press_up(0.5)
        print("✅ UP movement completed")
        time.sleep(2)

        # Test 2: Small down movement
        print("\nTest 2: Small DOWN movement (0.5 seconds)")
        print("Watch the lift - it should move DOWN slightly")
        input("Press Enter to start test 2...")
        press_down(0.5)
        print("✅ DOWN movement completed")
        time.sleep(2)

        # Test 3: Nudge up
        print("\nTest 3: Quick UP nudge (0.2 seconds)")
        input("Press Enter to start test 3...")
        nudge('up', 0.2)
        print("✅ UP nudge completed")
        time.sleep(1)

        # Test 4: Nudge down
        print("\nTest 4: Quick DOWN nudge (0.2 seconds)")
        input("Press Enter to start test 4...")
        nudge('down', 0.2)
        print("✅ DOWN nudge completed")
        time.sleep(1)

        # Test 5: Emergency stop
        print("\nTest 5: Emergency stop test")
        print("This should immediately stop any movement")
        emergency_stop()
        print("✅ Emergency stop activated")

        print("\n🎉 All hardware tests completed successfully!")
        print("If the lift moved as expected, your FLTCON connection is working!")

    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        emergency_stop()

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        emergency_stop()

    finally:
        print("\n🧹 Cleaning up GPIO...")
        cleanup()
        print("✅ GPIO cleanup completed")

def manual_test():
    """Allow manual testing of individual functions."""
    print("🔧 Manual Test Mode")
    print("Commands:")
    print("  u <seconds>  - Move UP for specified seconds")
    print("  d <seconds>  - Move DOWN for specified seconds")
    print("  nu <seconds> - Nudge UP for specified seconds")
    print("  nd <seconds> - Nudge DOWN for specified seconds")
    print("  stop         - Emergency stop")
    print("  quit         - Exit manual mode")
    print()

    try:
        while True:
            cmd = input("Command: ").strip().lower()

            if cmd == 'quit':
                break
            elif cmd == 'stop':
                emergency_stop()
                print("⏹️  Emergency stop")
            elif cmd.startswith('u '):
                try:
                    seconds = float(cmd.split()[1])
                    print(f"⬆️  Moving UP for {seconds} seconds...")
                    press_up(seconds)
                    print("✅ UP movement completed")
                except (ValueError, IndexError):
                    print("❌ Invalid command. Use: u <seconds>")
            elif cmd.startswith('d '):
                try:
                    seconds = float(cmd.split()[1])
                    print(f"⬇️  Moving DOWN for {seconds} seconds...")
                    press_down(seconds)
                    print("✅ DOWN movement completed")
                except (ValueError, IndexError):
                    print("❌ Invalid command. Use: d <seconds>")
            elif cmd.startswith('nu '):
                try:
                    seconds = float(cmd.split()[1])
                    print(f"⬆️  Nudging UP for {seconds} seconds...")
                    nudge('up', seconds)
                    print("✅ UP nudge completed")
                except (ValueError, IndexError):
                    print("❌ Invalid command. Use: nu <seconds>")
            elif cmd.startswith('nd '):
                try:
                    seconds = float(cmd.split()[1])
                    print(f"⬇️  Nudging DOWN for {seconds} seconds...")
                    nudge('down', seconds)
                    print("✅ DOWN nudge completed")
                except (ValueError, IndexError):
                    print("❌ Invalid command. Use: nd <seconds>")
            else:
                print("❌ Unknown command")

    except KeyboardInterrupt:
        print("\n⏹️  Manual test interrupted")
        emergency_stop()

    finally:
        cleanup()

if __name__ == "__main__":
    print("LG-07 Lift Hardware Test Script")
    print("Choose test mode:")
    print("1. Automated test sequence")
    print("2. Manual testing")
    print()

    choice = input("Enter choice (1 or 2): ").strip()

    if choice == '1':
        test_sequence()
    elif choice == '2':
        manual_test()
    else:
        print("❌ Invalid choice")