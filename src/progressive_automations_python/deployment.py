"""
Prefect deployment configuration for desk lifter control.

This module provides utilities for creating and managing Prefect deployments
that can be triggered externally and run asynchronously.
"""

from pathlib import Path


def create_deployments(work_pool_name: str = "default-process-pool"):
    """
    Create Prefect deployments for all desk control flows.
    
    This should be run once during setup to register the flows with Prefect Cloud.
    
    Args:
        work_pool_name: Name of the work pool to use (default: "default-process-pool")
        
    Usage:
        from progressive_automations_python.deployment import create_deployments
        create_deployments("my-work-pool")
    """
    from progressive_automations_python.prefect_flows import (
        simple_movement_flow,
        custom_movements_flow,
        test_sequence_flow,
        duty_cycle_monitoring_flow,
        scheduled_duty_cycle_check
    )
    
    # Get the source directory (where the package is installed)
    source_dir = Path(__file__).parent
    
    print(f"Creating deployments with work pool: {work_pool_name}")
    print("=== DEPLOYING ALL DESK CONTROL FLOWS ===")
    
    # Deploy simple movement flow
    simple_movement_flow.from_source(
        source=str(source_dir.parent.parent),
        entrypoint="progressive_automations_python/prefect_flows.py:simple_movement_flow",
    ).deploy(
        name="move-to-position",
        work_pool_name=work_pool_name,
        description="Move desk to a specific height position with duty cycle management"
    )
    print(f"✓ Deployed 'simple-movement-flow/move-to-position'")
    
    # Deploy custom movements flow
    custom_movements_flow.from_source(
        source=str(source_dir.parent.parent),
        entrypoint="progressive_automations_python/prefect_flows.py:custom_movements_flow",
    ).deploy(
        name="custom-movements",
        work_pool_name=work_pool_name,
        description="Execute custom movements from configuration file"
    )
    print(f"✓ Deployed 'custom-movements-flow/custom-movements'")
    
    # Deploy test sequence flow
    test_sequence_flow.from_source(
        source=str(source_dir.parent.parent),
        entrypoint="progressive_automations_python/prefect_flows.py:test_sequence_flow",
    ).deploy(
        name="test-sequence",
        work_pool_name=work_pool_name,
        description="Execute a test movement sequence"
    )
    print(f"✓ Deployed 'test-sequence-flow/test-sequence'")
    
    # Deploy duty cycle monitoring (immediate)
    duty_cycle_monitoring_flow.from_source(
        source=str(source_dir.parent.parent),
        entrypoint="progressive_automations_python/prefect_flows.py:duty_cycle_monitoring_flow",
    ).deploy(
        name="duty-cycle-monitor",
        work_pool_name=work_pool_name,
        description="Check duty cycle status on demand"
    )
    print(f"✓ Deployed 'duty-cycle-monitoring-flow/duty-cycle-monitor'")
    
    # Deploy scheduled duty cycle monitoring (every 10 minutes)
    from prefect.client.schemas.schedules import CronSchedule
    scheduled_duty_cycle_check.from_source(
        source=str(source_dir.parent.parent),
        entrypoint="progressive_automations_python/prefect_flows.py:scheduled_duty_cycle_check",
    ).deploy(
        name="duty-cycle-monitor-scheduled",
        work_pool_name=work_pool_name,
        schedule=CronSchedule(cron="*/10 * * * *"),
        description="Scheduled duty cycle monitoring (every 10 minutes)"
    )
    print(f"✓ Deployed 'scheduled-duty-cycle-check/duty-cycle-monitor-scheduled' (every 10 min)")
    
    print(f"\n🎉 All deployments created successfully!")
    print(f"\nNext steps:")
    print(f"1. Start a worker: prefect worker start --pool {work_pool_name}")
    print(f"2. Trigger a flow from Python:")
    print(f"   from prefect.deployments import run_deployment")
    print(f"   run_deployment('simple-movement-flow/move-to-position', parameters={{'target_height': 30.0}}, timeout=0)")
    print(f"3. Or from CLI:")
    print(f"   prefect deployment run 'simple-movement-flow/move-to-position' --param target_height=30.0")


def get_deployment_examples():
    """
    Return example code for using the deployments.
    
    Returns:
        String with example code
    """
    return '''
# Example 1: Trigger movement asynchronously and poll status
from prefect.deployments import run_deployment
from prefect import get_client
import asyncio

# Trigger the movement (returns immediately with timeout=0)
flow_run = run_deployment(
    name="move-desk-to-position/move-to-position",
    parameters={"position_inches": 35.5},
    timeout=0  # Return immediately without waiting
)

print(f"Flow run started with ID: {flow_run.id}")

# Later, check the status
async def check_status(flow_run_id):
    async with get_client() as client:
        flow_run = await client.read_flow_run(flow_run_id)
        print(f"Status: {flow_run.state.type}")
        
        if flow_run.state.type == "COMPLETED":
            # Get the result from the completed flow
            result = await flow_run.state.result()
            print(f"Final position: {result['final_position']}")
            print(f"At target: {result['at_target']}")
            print(f"Duty cycle: {result['duty_cycle_status']}")
        
        return flow_run

# Check status
flow_run_status = asyncio.run(check_status(flow_run.id))

# Example 2: Check current position
position_check = run_deployment(
    name="check-desk-position/check-position",
    timeout=30  # Wait up to 30 seconds for result
)

print(f"Current position: {position_check}")

# Example 3: Polling loop to wait for completion
async def wait_for_completion(flow_run_id, check_interval=5, max_wait=300):
    """Poll until flow completes or timeout"""
    import time
    start_time = time.time()
    
    async with get_client() as client:
        while time.time() - start_time < max_wait:
            flow_run = await client.read_flow_run(flow_run_id)
            
            if flow_run.state.is_final():
                result = await flow_run.state.result() if flow_run.state.type == "COMPLETED" else None
                return {
                    "completed": True,
                    "status": flow_run.state.type,
                    "result": result
                }
            
            await asyncio.sleep(check_interval)
        
        return {"completed": False, "status": "TIMEOUT"}

# Use the polling function
result = asyncio.run(wait_for_completion(flow_run.id))
print(f"Final result: {result}")
'''


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        work_pool = sys.argv[1]
    else:
        work_pool = "desk-lifter-pool"
    
    create_deployments(work_pool)
