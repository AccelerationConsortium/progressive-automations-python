"""
Prefect flows and deployments for automated desk control.

Provides scheduled automation and workflow orchestration using Prefect.
Integrates with the desk controller for safe, automated movements.
"""

import time
from prefect import flow, task
from prefect.logging import get_run_logger

# Import our modular components
from desk_controller import move_to_height, test_sequence, LOWEST_HEIGHT


@task
def log_info(message: str):
    """Log information message"""
    logger = get_run_logger()
    logger.info(message)
    print(message)


@task  
def execute_movement(target_height: float, current_height: float = None):
    """Execute a movement as a Prefect task"""
    logger = get_run_logger()
    
    try:
        result = move_to_height(target_height, current_height)
        
        if result["success"]:
            logger.info(f"Movement successful: {result}")
            return result
        else:
            logger.error(f"Movement failed: {result['error']}")
            raise ValueError(result["error"])
            
    except Exception as e:
        logger.error(f"Movement execution failed: {e}")
        raise


@task
def execute_test_sequence(movement_distance: float = 0.5, rest_time: float = 10.0):
    """Execute test sequence as a Prefect task"""
    logger = get_run_logger()
    
    try:
        result = test_sequence(movement_distance, rest_time)
        
        if result["success"]:
            logger.info(f"Test sequence successful: {result}")
            return result
        else:
            logger.error(f"Test sequence failed: {result.get('error', 'Unknown error')}")
            raise ValueError(result.get("error", "Test sequence failed"))
            
    except Exception as e:
        logger.error(f"Test sequence execution failed: {e}")
        raise


@flow
def move_to_height_flow(target_height: float, current_height: float = None):
    """Prefect flow for moving to a specific height"""
    log_info(f"Starting movement flow: target={target_height}, current={current_height}")
    
    result = execute_movement(target_height, current_height)
    
    log_info(f"Movement flow completed: {result}")
    return result


@flow  
def custom_test_sequence_flow(movement_distance: float = 0.5, rest_time: float = 10.0):
    """Prefect flow for custom test sequence"""
    log_info(f"Starting test sequence: distance={movement_distance}, rest={rest_time}")
    
    start_height = LOWEST_HEIGHT
    up_target = start_height + movement_distance
    
    log_info(f"Test sequence plan:")
    log_info(f"  Starting at: {start_height}\"")
    log_info(f"  Will move to: {up_target}\"")
    log_info(f"  Then rest for {rest_time} seconds")
    log_info(f"  Then return to: {start_height}\"")
    
    # Phase 1: Move up
    log_info(f"--- Phase 1: Moving UP {movement_distance} inches ---")
    result1 = execute_movement(up_target, start_height)
    
    # Phase 2: Rest
    log_info(f"--- Phase 2: Resting for {rest_time} seconds ---")
    time.sleep(rest_time)
    log_info("Rest complete.")
    
    # Phase 3: Move down  
    log_info(f"--- Phase 3: Moving DOWN {movement_distance} inches ---")
    result2 = execute_movement(start_height, up_target)
    
    log_info("Custom test sequence complete!")
    
    return {
        "success": True,
        "phase1_result": result1,
        "phase2_result": result2,
        "total_duration": result1.get("duration", 0) + result2.get("duration", 0)
    }


@flow
def desk_control_cli_flow():
    """Prefect flow for CLI-based desk control"""
    log_info("Starting CLI flow")
    
    try:
        from desk_controller import LOWEST_HEIGHT, HIGHEST_HEIGHT
        
        current = float(input(f"Enter current height in inches ({LOWEST_HEIGHT}-{HIGHEST_HEIGHT}): "))
        target = float(input(f"Enter target height in inches ({LOWEST_HEIGHT}-{HIGHEST_HEIGHT}): "))
        
        result = execute_movement(target, current)
        log_info("CLI flow completed successfully!")
        return result
        
    except ValueError as e:
        log_info(f"Error: {e}")
        raise
    except KeyboardInterrupt:
        log_info("Operation cancelled.")
        raise


def deploy_test_sequence(schedule_cron: str = "39 4 * * *", deployment_name: str = "desk-lifter-test-sequence-1139pm-toronto"):
    """Deploy the test sequence with scheduling"""
    
    custom_test_sequence_flow.from_source(
        source=".",
        entrypoint="scripts/prefect_flows.py:custom_test_sequence_flow",
    ).deploy(
        name=deployment_name,
        work_pool_name="default-agent-pool", 
        cron=schedule_cron,  # Default: Run daily at 11:39 PM Toronto time (4:39 AM UTC)
    )
    
    print(f"Deployment '{deployment_name}' created with schedule '{schedule_cron}'!")
    print("Run 'prefect worker start --pool default-agent-pool' to execute scheduled flows.")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "deploy":
        deploy_test_sequence()
    elif len(sys.argv) > 1 and sys.argv[1] == "test":
        custom_test_sequence_flow()
    else:
        desk_control_cli_flow()