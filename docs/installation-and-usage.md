# Installation and Usage Guide

This guide covers the complete installation and usage workflow for the Progressive Automations desk lifter control system.

## Prerequisites

1. **Hardware Setup**: Follow the [Raspberry Pi Setup Guide](raspberry-pi-setup.md) for hardware configuration
2. **Bill of Materials**: See [Bill of Materials](bill_of_materials.md) for required components
3. **Raspberry Pi**: Raspberry Pi 5 with Debian Trixie and Python 3.11+

## Configuration

After installation, you can customize duty cycle limits and calibration values by editing the configuration file:

```python
# Location: site-packages/progressive_automations_python/config.py
# Or find it with: python -c "import progressive_automations_python.config as c; print(c.__file__)"

# Key settings to adjust during initial setup:
# - DUTY_CYCLE_PERCENTAGE: Motor duty cycle (default: 0.10 = 10%)
# - MAX_CONTINUOUS_RUNTIME: Maximum single movement time (default: 30s)
# - LOWEST_HEIGHT / HIGHEST_HEIGHT: Your desk's physical range
# - UP_RATE / DOWN_RATE: Measured movement rates (inches/second)
```

The configuration includes validation to prevent invalid values.

## Installation

### Step 1: Install the Package

```bash
pip install progressive-automations-python
```

This installs the package with all dependencies, including Prefect for workflow orchestration.

### Step 2: Configure Prefect Cloud

You need a Prefect Cloud account for remote workflow orchestration.

1. Sign up at [https://www.prefect.io/](https://www.prefect.io/)
2. Get your API key from the Prefect Cloud dashboard
3. Login from your Raspberry Pi using Prefect's CLI:

```bash
prefect cloud login -k <your-api-key>
```

### Step 3: Create Work Pool

Create a work pool for the desk lifter using Prefect's CLI:

```bash
prefect work-pool create desk-lifter-pool --type process
```

### Step 4: Deploy Flows to Prefect Cloud

Deploy all desk control flows using Python:

```python
from progressive_automations_python.deployment import create_deployments

create_deployments("desk-lifter-pool")
```

This creates the following deployments:
- `simple-movement-flow/move-to-position` - Move to a specific height
- `custom-movements-flow/custom-movements` - Execute multiple configured movements
- `test-sequence-flow/test-sequence` - Test sequence (up, wait, down)
- `duty-cycle-monitoring-flow/duty-cycle-monitor` - On-demand duty cycle check

### Step 5: Start a Prefect Worker

On your Raspberry Pi, start a worker to execute flows using Prefect's CLI:

```bash
prefect worker start --pool desk-lifter-pool
```

Keep this running in a terminal or set up as a systemd service for automatic startup.

## Testing During Initial Setup

> **Note**: The `progressive_automations_python` CLI is provided for initial hardware testing and troubleshooting only. For production use, trigger flows via `run_deployment()` or Prefect's CLI.

### Test Hardware Connections

Test UP or DOWN movement for 2 seconds to verify GPIO connections:

```bash
progressive_automations_python --test UP
progressive_automations_python --test DOWN
```

### Check Duty Cycle Status

View current duty cycle usage during debugging:

```bash
progressive_automations_python --status
```

## Production Usage: Async Deployment and Position Polling

**This is the primary way to use the desk lifter system.** Trigger movements asynchronously from external systems and poll their status later.

### Triggering Movements Asynchronously

From any Python environment with network access to Prefect Cloud:

```python
from prefect.deployments import run_deployment

# Trigger a movement (returns immediately with timeout=0)
flow_run = run_deployment(
    name="simple-movement-flow/move-to-position",
    parameters={"target_height": 35.5, "current_height": 24.0},
    timeout=0  # Return immediately without waiting
)

print(f"Movement started with flow run ID: {flow_run.id}")
# Continue with other work while the desk moves...
```

### Polling Position Status

Check if the movement has completed:

```python
from prefect import get_client
import asyncio

async def check_movement_status(flow_run_id):
    """Check if the movement has completed"""
    async with get_client() as client:
        flow_run = await client.read_flow_run(flow_run_id)
        
        print(f"Status: {flow_run.state.type}")
        
        if flow_run.state.type == "COMPLETED":
            # Movement completed successfully
            result = await flow_run.state.result()
            print(f"✅ Movement completed!")
            print(f"  Final position: {result['movement_result']['end_height']}\"")
            print(f"  At target: {abs(result['movement_result']['end_height'] - result['movement_result']['start_height']) < 0.1}")
            print(f"  Duty cycle remaining: {result['final_duty_status']['remaining_capacity']:.1f}s")
            return result
        elif flow_run.state.type == "FAILED":
            print(f"❌ Movement failed: {flow_run.state.message}")
            return None
        else:
            print(f"⏳ Still running... (state: {flow_run.state.type})")
            return None

# Check status
result = asyncio.run(check_movement_status(flow_run.id))
```

### Complete Polling Example

Wait for a movement to complete with periodic polling:

```python
import asyncio
import time

async def wait_for_movement_completion(flow_run_id, check_interval=5, max_wait=300):
    """
    Poll until movement completes or timeout.
    
    This is similar to preheating an oven - you set the temperature and check later,
    not sit in front of it the whole time.
    
    Args:
        flow_run_id: The flow run ID from run_deployment
        check_interval: Seconds between status checks (default: 5)
        max_wait: Maximum time to wait in seconds (default: 300)
        
    Returns:
        dict with completion status and result
    """
    from prefect import get_client
    
    start_time = time.time()
    
    async with get_client() as client:
        while time.time() - start_time < max_wait:
            flow_run = await client.read_flow_run(flow_run_id)
            
            if flow_run.state.is_final():
                if flow_run.state.type == "COMPLETED":
                    result = await flow_run.state.result()
                    return {
                        "completed": True,
                        "success": True,
                        "result": result
                    }
                else:
                    return {
                        "completed": True,
                        "success": False,
                        "error": flow_run.state.message
                    }
            
            print(f"⏳ Still moving... ({time.time() - start_time:.1f}s elapsed)")
            await asyncio.sleep(check_interval)
        
        return {
            "completed": False,
            "success": False,
            "error": "Timeout waiting for movement"
        }

# Use it
result = asyncio.run(wait_for_movement_completion(flow_run.id))

if result["completed"] and result["success"]:
    print(f"✅ Desk reached target position!")
    print(f"Details: {result['result']}")
else:
    print(f"❌ Movement did not complete: {result.get('error', 'Unknown error')}")
```

### Checking Duty Cycle Before Triggering

Check if there's enough duty cycle capacity before triggering a movement:

```python
from prefect.deployments import run_deployment

# Check current duty cycle status
status_run = run_deployment(
    name="duty-cycle-monitoring-flow/duty-cycle-monitor",
    timeout=30  # Wait for result
)

remaining = status_run["status"]["remaining_capacity"]

if remaining > 10:  # Need at least 10 seconds
    # Safe to trigger movement
    flow_run = run_deployment(
        name="simple-movement-flow/move-to-position",
        parameters={"target_height": 35.5},
        timeout=0
    )
    print(f"Movement triggered: {flow_run.id}")
else:
    print(f"⚠️ Insufficient duty cycle capacity ({remaining:.1f}s remaining)")
    print("Wait for duty cycle window to reset")
```

### Using Prefect CLI for Manual Triggers

You can also trigger flows directly using Prefect's CLI:

```bash
# Trigger a movement to 30 inches
prefect deployment run 'simple-movement-flow/move-to-position' --param target_height=30.0

# Run a test sequence
prefect deployment run 'test-sequence-flow/test-sequence' --param movement_distance=0.5 --param rest_time=10.0

# Check duty cycle
prefect deployment run 'duty-cycle-monitoring-flow/duty-cycle-monitor'
```

## Integration with Other Equipment

When integrating with other equipment that depends on the desk position:

```python
async def orchestrate_equipment_workflow():
    """
    Example: Move desk, wait for completion, then trigger dependent equipment
    """
    from prefect.deployments import run_deployment
    from prefect import get_client
    import asyncio
    
    # Step 1: Trigger desk movement
    print("Step 1: Moving desk to position...")
    desk_run = run_deployment(
        name="simple-movement-flow/move-to-position",
        parameters={"target_height": 30.0},
        timeout=0
    )
    
    # Step 2: Poll until desk reaches position
    print("Step 2: Waiting for desk to reach position...")
    result = await wait_for_movement_completion(desk_run.id)
    
    if not (result["completed"] and result["success"]):
        raise RuntimeError("Desk movement failed")
    
    print(f"✅ Desk at position: {result['result']['movement_result']['end_height']}\"")
    
    # Step 3: Now safe to trigger dependent equipment
    print("Step 3: Triggering dependent equipment...")
    # ... trigger your other equipment here ...
    
    return {"desk_movement": result, "equipment_triggered": True}

# Run the orchestration
result = asyncio.run(orchestrate_equipment_workflow())
```

## Duty Cycle Management

The system enforces a 10% duty cycle (2 minutes on, 18 minutes off) to protect the motor:

- **Maximum continuous runtime**: 30 seconds
- **Maximum usage in 20-minute window**: 120 seconds (2 minutes)
- **Automatic tracking**: All movements are tracked automatically
- **Safety enforcement**: Movements exceeding limits are rejected

View current usage:

```bash
progressive_automations_python --status
```

Output example:
```
=== DUTY CYCLE STATUS ===
Current usage: 15.2s / 120.0s (12.7%)
Remaining capacity: 104.8s
Percentage used: 12.7%
Window period: 1200s (20 minutes)
Current position: 24.0"
Last movement: 2.1s ago

✅ GOOD CAPACITY - Normal operations possible
```

## Generating Movement Configurations

Generate optimized movement sequences based on current duty cycle:

```bash
progressive_automations_python --generate-movements
```

This creates `movement_configs.json` with movements that:
1. Respect the 30-second continuous runtime limit
2. Use available capacity efficiently
3. Demonstrate successful movements within limits
4. Show duty cycle protection when limits would be exceeded

## Troubleshooting

### Movement Rejected: Insufficient Duty Cycle

**Error**: `Movement would exceed 10% duty cycle limit`

**Solution**: Wait for the duty cycle window to reset. Check status with:
```bash
progressive_automations_python --status
```

### GPIO Permission Denied

**Error**: `Permission denied` when accessing GPIO

**Solution**: Ensure your user is in the `gpio` group:
```bash
sudo usermod -a -G gpio $USER
# Then reboot
```

### Prefect Worker Not Running

**Error**: Flow triggered but never executes

**Solution**: Ensure a Prefect worker is running:
```bash
prefect worker start --pool default-process-pool
```

Consider setting up a systemd service to keep the worker running.

### Position Unknown

**Error**: `No current height provided and no last known position`

**Solution**: Provide the current height explicitly:
```bash
progressive_automations_python --move 30.0 --current 24.0
```

The system will remember the position for future movements.

## Command Reference

### Prefect CLI (Primary Interface)

```bash
# Login to Prefect Cloud
prefect cloud login -k <api-key>

# Create work pool
prefect work-pool create desk-lifter-pool --type process

# Start worker (keep running)
prefect worker start --pool desk-lifter-pool

# Trigger deployments manually
prefect deployment run 'simple-movement-flow/move-to-position' --param target_height=30.0
prefect deployment run 'test-sequence-flow/test-sequence'
prefect deployment run 'duty-cycle-monitoring-flow/duty-cycle-monitor'
```

### Package CLI (Testing/Debugging Only)

```bash
# Hardware testing (initial setup)
progressive_automations_python --test UP|DOWN

# Status check (debugging)
progressive_automations_python --status
```

## Python API Examples

For viewing complete Python examples for async deployment and polling:

```bash
progressive_automations_python --examples
```

This displays comprehensive code examples for:
- Async movement triggering
- Status polling
- Polling loops with timeout
- Duty cycle checking
- Equipment workflow orchestration

## Next Steps

1. ✅ Complete hardware setup per [Raspberry Pi Setup](raspberry-pi-setup.md)
2. ✅ Install package: `pip install progressive-automations-python`
3. ✅ Configure Prefect Cloud: `prefect cloud login -k <api-key>`
4. ✅ Create work pool: `prefect work-pool create desk-lifter-pool --type process`
5. ✅ Deploy flows via Python: `create_deployments("desk-lifter-pool")`
6. ✅ Start worker: `prefect worker start --pool desk-lifter-pool`
7. ✅ Test hardware (optional): `progressive_automations_python --test UP`
8. ✅ **Trigger flows via `run_deployment()` from your automation code!**

For more information, see:
- [Raspberry Pi Setup](raspberry-pi-setup.md)
- [Bill of Materials](bill_of_materials.md)
- [Prefect Documentation](https://docs.prefect.io/)
