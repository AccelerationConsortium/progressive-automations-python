# LG-07 Lift Control - Raspberry Pi Setup

This directory contains the Raspberry Pi implementation for controlling an LG-07 lifting column via FLTCON remote.

## Hardware Requirements

- Raspberry Pi (any model with GPIO pins)
- Relay board/module (2 relays minimum)
- FLTCON remote control unit
- LG-07 lifting column
- Jumper wires for connections

## Hardware Connections

### GPIO Pin Assignments (BCM numbering)
- **GPIO 17 (Pin 11)**: UP relay control
- **GPIO 27 (Pin 13)**: DOWN relay control
- **GND (Pin 6)**: Common ground for relays

### Relay Connections
1. Connect relay board to Raspberry Pi GPIO pins
2. Connect relay outputs to FLTCON remote buttons:
   - Relay 1 (GPIO 17) → FLTCON UP button
   - Relay 2 (GPIO 27) → FLTCON DOWN button
3. Ensure relays are configured as **ACTIVE-LOW** (closed when GPIO is LOW)

## Software Setup

### Option 1: Automated Setup (Recommended)
```bash
# Copy project to Raspberry Pi
scp -r progressive-automations-python pi@raspberrypi.local:~/

# SSH to Raspberry Pi
ssh pi@raspberrypi.local

# Run setup script
cd progressive-automations-python
chmod +x setup-pi.sh
./setup-pi.sh
```

### Option 2: Manual Setup
```bash
# Update system
sudo apt update
sudo apt install -y python3 python3-pip python3-rpi.gpio

# Install package
pip3 install -e .

# Install Pi-specific requirements
pip3 install -r requirements-pi.txt
```

## Testing

### Hardware Test (Recommended First Step)
```bash
cd progressive-automations-python
python3 src/progressive_automations_python/pi/lg07_lift/test_hardware.py
```

This will run an automated test sequence:
1. Small UP movement (0.5s)
2. Small DOWN movement (0.5s)
3. Quick UP nudge (0.2s)
4. Quick DOWN nudge (0.2s)
5. Emergency stop test

### Manual Testing
```bash
# Move up for 1 second
python3 src/progressive_automations_python/pi/lg07_lift/app.py up

# Move down for 2 seconds
python3 src/progressive_automations_python/pi/lg07_lift/app.py down --time 2.0

# Quick nudge up
python3 src/progressive_automations_python/pi/lg07_lift/app.py nudge up --time 0.3
```

### Interactive Manual Test
```bash
python3 src/progressive_automations_python/pi/lg07_lift/test_hardware.py
# Choose option 2 for manual testing
```

## Safety Precautions

⚠️ **Important Safety Notes:**

1. **Test with short movements first** - Start with 0.2-0.5 second movements
2. **Have emergency stop ready** - Ctrl+C will trigger emergency stop
3. **Monitor the lift** - Ensure it moves in expected direction
4. **Check relay polarity** - Verify relays activate when GPIO goes LOW
5. **Secure connections** - Loose wires can cause intermittent operation

## Troubleshooting

### Lift doesn't move
- Check relay connections to FLTCON buttons
- Verify FLTCON has power and is paired with LG-07
- Test relays independently (they should click when activated)

### Wrong direction
- Swap relay connections between UP/DOWN buttons
- Check GPIO pin assignments in `lift_driver.py`

### GPIO errors
- Ensure you're running as a user with GPIO access (usually `pi`)
- Check that RPi.GPIO is installed: `python3 -c "import RPi.GPIO"`

### Import errors
- Run `pip3 install -e .` from project root
- Check Python path includes the src directory

## Configuration

Edit `config.yaml` to customize:
- GPIO pin assignments
- Default timing values
- Safety settings

## Next Steps

Once basic control works, consider adding:
- Position feedback sensors
- Web interface for remote control
- Automated movement sequences
- Safety limit switches
- Logging and monitoring