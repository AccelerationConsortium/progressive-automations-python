"""
Prefect flow deployment for desk lifter control.

Imports the Prefect-decorated move_to_height flow from desk_controller and provides deployment utilities.
"""

from progressive_automations_python.desk_controller import move_to_height


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
    
    deployment = move_to_height.from_source(
        source=".",
        entrypoint="desk_controller.py:move_to_height",
    ).deploy(
        name=deployment_name,
        work_pool_name="default-process-pool",
    )
    
    print(f"✅ Deployment '{deployment_name}' created!")
    print(f"To run from Prefect Cloud: Use flow 'move-to-height/{deployment_name}'")
    print(f"Parameter: target_height (float, in inches)")
    
    return deployment_name


if __name__ == "__main__":
    # Deploy when run directly
    deploy_move_desk_flow()