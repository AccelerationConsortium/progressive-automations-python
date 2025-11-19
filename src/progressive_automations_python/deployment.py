"""
Prefect deployment configuration for desk lifter control.

This module provides utilities for creating and managing Prefect deployments
that can be triggered externally and run asynchronously.
"""

from pathlib import Path


def create_deployments(work_pool_name: str = "desk-lifter-pool"):
    """
    Create Prefect deployment for desk control.
    
    This should be run once during setup to register the flow with Prefect Cloud.
    
    Args:
        work_pool_name: Name of the work pool to use (default: "desk-lifter-pool")
        
    Usage:
        from progressive_automations_python.deployment import create_deployments
        create_deployments("my-work-pool")
    """
    from progressive_automations_python.prefect_flows import simple_movement_flow
    
    # Get the source directory (where the package is installed)
    source_dir = Path(__file__).parent
    
    print(f"Creating deployment with work pool: {work_pool_name}")
    print("=== DEPLOYING DESK CONTROL FLOW ===")
    
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
    
    print(f"\n🎉 Deployment created successfully!")
    print(f"\nNext steps:")
    print(f"1. Start a worker: prefect worker start --pool {work_pool_name}")
    print(f"2. Trigger a flow from Python:")
    print(f"   from prefect.deployments import run_deployment")
    print(f"   run_deployment('simple-movement-flow/move-to-position', parameters={{'target_height': 30.0}}, timeout=0)")
    print(f"3. Or from CLI:")
    print(f"   prefect deployment run 'simple-movement-flow/move-to-position' --param target_height=30.0")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        work_pool = sys.argv[1]
    else:
        work_pool = "desk-lifter-pool"
    
    create_deployments(work_pool)
