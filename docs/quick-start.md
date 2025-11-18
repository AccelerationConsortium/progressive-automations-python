# Quick Start Guide

This guide shows the complete end-to-end workflow for using the desk lifter control system.

## Complete Setup (One Time)

```bash
# 1. Install the package
pip install progressive-automations-python

# 2. Login to Prefect Cloud
prefect cloud login -k <your-api-key>

# 3. Create the work pool
prefect work-pool create desk-lifter-pool --type process

# 4. Deploy the flows
python -c "from progressive_automations_python.deployment import create_deployments; create_deployments()"

# 5. Start the worker (keep this running)
prefect worker start --pool desk-lifter-pool
```

## Testing Hardware (Optional)

```bash
# Test GPIO connections
progressive_automations_python --test UP
progressive_automations_python --test DOWN

# Check duty cycle status
progressive_automations_python --status
```

## Production Usage

### From External Python Code

```python
from prefect.deployments import run_deployment
from prefect import get_client
import asyncio

# Trigger movement asynchronously (returns immediately)
flow_run = run_deployment(
    name="simple-movement-flow/move-to-position",
    parameters={"target_height": 35.5},
    timeout=0  # Don't wait, return immediately
)

print(f"Movement triggered: {flow_run.id}")

# Poll status later
async def check_status(flow_run_id):
    async with get_client() as client:
        flow_run = await client.read_flow_run(flow_run_id)
        
        if flow_run.state.type == "COMPLETED":
            result = await flow_run.state.result()
            print(f"✅ At position: {result['movement_result']['end_height']}\"")
            return True
        elif flow_run.state.type == "FAILED":
            print(f"❌ Failed: {flow_run.state.message}")
            return False
        else:
            print(f"⏳ Still moving...")
            return None

# Check if complete
complete = asyncio.run(check_status(flow_run.id))
```

### From Prefect CLI

```bash
# Trigger a movement
prefect deployment run 'simple-movement-flow/move-to-position' --param target_height=30.0

# Run test sequence
prefect deployment run 'test-sequence-flow/test-sequence'

# Check duty cycle
prefect deployment run 'duty-cycle-monitoring-flow/duty-cycle-monitor'
```

## Equipment Orchestration Pattern

```python
async def run_experiment():
    """Example: coordinate desk with other equipment"""
    from prefect.deployments import run_deployment
    from prefect import get_client
    import asyncio
    
    # Step 1: Move desk to position
    desk_run = run_deployment(
        name="simple-movement-flow/move-to-position",
        parameters={"target_height": 30.0},
        timeout=0
    )
    
    # Step 2: Wait for desk to reach position
    async with get_client() as client:
        while True:
            flow_run = await client.read_flow_run(desk_run.id)
            if flow_run.state.is_final():
                if flow_run.state.type == "COMPLETED":
                    print("✅ Desk in position")
                    break
                else:
                    raise RuntimeError("Desk movement failed")
            await asyncio.sleep(2)
    
    # Step 3: Now trigger dependent equipment
    print("Triggering other equipment...")
    # ... your other equipment code here ...

# Run it
asyncio.run(run_experiment())
```

## Key Concepts

1. **Async Execution**: Use `timeout=0` in `run_deployment()` to return immediately
2. **Position Polling**: Use Prefect's `get_client()` to check `flow_run.state`
3. **Duty Cycle**: System enforces 10% duty cycle (2min on / 18min off) automatically
4. **Work Pool**: `desk-lifter-pool` must be running on the Raspberry Pi
5. **Testing CLI**: Only use `progressive_automations_python` for initial hardware testing

## Next Steps

- Read [Installation and Usage Guide](installation-and-usage.md) for complete details
- View [Raspberry Pi Setup](raspberry-pi-setup.md) for hardware configuration
- Check [Bill of Materials](bill_of_materials.md) for required components
