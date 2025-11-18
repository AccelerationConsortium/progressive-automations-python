# Desk Control Scripts

This directory contains scripts for controlling a Progressive Automations desk lifter.

## 🚀 Quick Start

**For the modern modular system:**
```bash
# Navigate to the modular package
cd desk_control/

# Run interactive CLI
python main.py

# Run test sequence  
python main.py test

# Check duty cycle status
python main.py status

# Deploy Prefect automation
python main.py deploy
```

## 📁 Directory Structure

```
scripts/
├── desk_control/              # 🆕 Modern modular system
│   ├── main.py               # Main CLI interface
│   ├── desk_controller.py    # High-level control logic
│   ├── movement_control.py   # GPIO operations
│   ├── duty_cycle.py         # Motor protection
│   ├── prefect_flows.py      # Automation & scheduling
│   └── README.md             # Detailed documentation
├── constants.py              # Shared constants (pins, calibration)
├── lifter_state.json         # Persistent state file
├── lifter_calibration.txt    # Calibration data
└── desk_control_prefect_LEGACY.py  # 📦 Original monolithic file (backup)
```

## ✨ What's New

### **Modular Architecture**
The code has been refactored into focused, maintainable modules:

- **`movement_control.py`** - GPIO pin control and movement execution
- **`duty_cycle.py`** - 10% duty cycle protection with sliding window
- **`desk_controller.py`** - Height management and safety checks
- **`prefect_flows.py`** - Workflow automation and scheduling
- **`main.py`** - Unified command-line interface

### **Improved Duty Cycle**
- ✅ True sliding window (not hard resets every 20 minutes)
- ✅ Precise timestamp tracking of usage periods
- ✅ Automatic cleanup of old periods
- ✅ Real-time duty cycle status monitoring

### **Better Safety**
- ✅ Comprehensive error handling
- ✅ GPIO cleanup in all scenarios
- ✅ Continuous runtime limits (30s max per movement)
- ✅ Height range validation

## 📖 Usage Examples

```bash
# Basic movement
python desk_control/main.py move 25.0 30.0    # Move from 25" to 30"

# Test sequence with custom parameters  
python desk_control/main.py test 1.0 5.0      # 1" movement, 5s rest

# Duty cycle monitoring
python desk_control/main.py status

# Prefect automation
python desk_control/main.py deploy "0 12 * * *"  # Deploy for noon daily
```

## 🔧 Configuration

Edit `constants.py` to adjust:
- GPIO pin assignments
- Calibration values (height range, movement rates)

## 📚 Documentation

See `desk_control/README.md` for detailed documentation of the modular system.

## 🏛️ Legacy Code

The original monolithic file is preserved as `desk_control_prefect_LEGACY.py` for reference, but the modular system in `desk_control/` should be used for all new development.