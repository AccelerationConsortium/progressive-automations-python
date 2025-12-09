"""
Prefect flow deployment for desk lifter control.

Imports the Prefect-decorated move_to_height flow from desk_controller and provides deployment utilities.
"""

from progressive_automations_python.desk_controller import move_to_height
from prefect.runner.storage import GitRepository


# =============================================================================
# DEPLOYMENT FUNCTION
# =============================================================================

def deploy_move_desk_flow(deployment_name: str = "move-desk"):
    """Deploy the move desk flow for Prefect Cloud execution.
    
    Args:
        deployment_name: Name for the deployment in Prefect Cloud
    
    Returns:
        str: The deployment name for reference
    """
    
    # Create deployment with Git source
    deployment = move_to_height.to_deployment(
        name=deployment_name,
        work_pool_name="desk-lifter-pool",
        storage=GitRepository(
            url="https://github.com/AccelerationConsortium/progressive-automations-python.git",
            reference="main"
        ),
        entrypoint="src/progressive_automations_python/desk_controller.py:move_to_height"
    )
    
    # Deploy it
    deployment_id = deployment.apply()
    
    print(f"✅ Deployment '{deployment_name}' created with ID: {deployment_id}")
    print(f"Work pool: desk-lifter-pool")
    print(f"Source: GitHub repository")
    print(f"To run: prefect deployment run 'move-to-height/{deployment_name}' --param target_height=30")
    print(f"Parameter: target_height (float, in inches)")
    
    return deployment_name


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--deploy", action="store_true", help="Create deployment")
    args = parser.parse_args()
    
    if args.deploy:
        deploy_move_desk_flow()
    else:
        # Default: just test the flow directly
        print("Testing flow directly with target height 30...")
        result = move_to_height(30.0)
        print(f"Result: {result}")