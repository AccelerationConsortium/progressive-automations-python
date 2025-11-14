#!/bin/bash
# Setup script for Raspberry Pi LG-07 Lift Control
# Run this script on your Raspberry Pi to set up the environment

set -e  # Exit on any error

echo "🛠️  Setting up LG-07 Lift Control on Raspberry Pi"
echo "================================================="

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "❌ This script must be run on a Raspberry Pi"
    exit 1
fi

echo "✅ Running on Raspberry Pi"

# Update package list
echo "📦 Updating package list..."
sudo apt update

# Install Python and pip if not present
echo "🐍 Installing Python and pip..."
sudo apt install -y python3 python3-pip python3-dev

# Install RPi.GPIO
echo "🔌 Installing RPi.GPIO..."
sudo apt install -y python3-rpi.gpio

# Install the package in development mode
echo "📚 Installing progressive-automations-python..."
cd "$(dirname "$0")"
pip3 install -e .

# Install additional dependencies if any
if [ -f "requirements-pi.txt" ]; then
    echo "📋 Installing Raspberry Pi specific requirements..."
    pip3 install -r requirements-pi.txt
fi

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x src/progressive_automations_python/pi/lg07_lift/test_hardware.py
chmod +x src/progressive_automations_python/pi/lg07_lift/app.py

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Connect your relays to GPIO pins 17 (UP) and 27 (DOWN)"
echo "2. Connect relays to FLTCON UP/DOWN buttons"
echo "3. Test with: python3 src/progressive_automations_python/pi/lg07_lift/test_hardware.py"
echo "4. Or run: python3 src/progressive_automations_python/pi/lg07_lift/app.py up"
echo ""
echo "⚠️  Safety note: Test with short movements first and ensure emergency stop works!"