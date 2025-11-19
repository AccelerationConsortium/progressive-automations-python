# Raspberry Pi 5 GPIO Setup for Desk Lifter Control

This document describes the setup required to run the desk lifter control scripts on a Raspberry Pi 5 running Debian Trixie.

## Hardware Requirements

- Raspberry Pi 5 (with BCM2712 SoC)
- GPIO pins connected to the desk lifter motor controller:
  - UP_PIN: GPIO 18 (physical pin 12)
  - DOWN_PIN: GPIO 17 (physical pin 11)
- Power supply: 5V USB-C (at least 3A, preferably 5A for high-power peripherals)

## Software Requirements

- Debian Trixie (13.x)
- Python 3.11 or later
- Virtual environment (`venv`)

## GPIO Library Compatibility

The standard `RPi.GPIO` library does not support Raspberry Pi 5 due to changes in the BCM2712 SoC. Instead, use `rpi-lgpio`, a drop-in replacement that provides the same API but uses the `lgpio` library for GPIO access.

## Installation Steps

1. **Clone the repository** (if not already done):
   ```bash
   git clone https://github.com/AccelerationConsortium/progressive-automations-python.git
   cd progressive-automations-python
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Remove incompatible RPi.GPIO package** (if installed):
   ```bash
   sudo apt remove -y python3-rpi.gpio
   ```

5. **Ensure user is in the gpio group** (for GPIO access without sudo):
   ```bash
   sudo usermod -a -G gpio $USER
   ```
   Reboot after adding the user to the group.

## Running the Scripts

Activate the virtual environment and run the scripts from the `scripts/` directory:

```bash
source venv/bin/activate
cd scripts
python move_to_height_no_reset.py
```

Available scripts:
- `move_to_height_no_reset.py`: Move the desk to a target height
- `move_to_height.py`: Alternative height control script
- `desk_control_prefect.py`: Prefect-based workflow orchestration
- `test_up.py`: Test upward movement
- `test_down.py`: Test downward movement
- `reset_to_lowest.py`: Reset to lowest position

## Calibration

The scripts use calibration data:
- Lowest height: 23.7 inches
- Highest height: 54.5 inches
- Up rate: 0.54 inches/second
- Down rate: 0.55 inches/second

Adjust these values in the script if your setup differs.

State is saved in `lifter_state.json` in the scripts directory.

## Troubleshooting

### RuntimeError: Cannot determine SOC peripheral base address

This error occurs when using the old `RPi.GPIO` library on Raspberry Pi 5. Ensure you have installed `rpi-lgpio` and removed `python3-rpi.gpio`.

### Permission denied on GPIO access

- Ensure your user is in the `gpio` group: `groups $USER` should include `gpio`.
- If not, run `sudo usermod -a -G gpio $USER` and reboot.

### Script runs but motor doesn't move

- Check GPIO pin connections.
- Verify the motor controller is powered and connected correctly.
- Test with `test_up.py` and `test_down.py` to isolate issues.

### Virtual environment issues

- Always activate the venv before running scripts: `source venv/bin/activate`
- If pip installs fail with "externally-managed-environment", you're trying to install system-wide. Use the venv.

## Notes

- The scripts use BCM pin numbering.
- GPIO access requires root permissions or membership in the `gpio` group.
- On Raspberry Pi 5, USB peripherals may be limited to 600mA if using a 3A power supply. Use a 5A supply for high-power devices.
- This setup is tested on Debian Trixie with Raspberry Pi 5.