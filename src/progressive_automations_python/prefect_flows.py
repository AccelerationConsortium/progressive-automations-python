"""
Prefect flow for desk lifter control.

Provides workflow orchestration using Prefect for remote desk control.
"""

from prefect import flow, task
from prefect.logging import get_run_logger

from progressive_automations_python.desk_controller import (
    move_to_height, 
    check_duty_cycle_status_before_execution
)
from progressive_automations_python.duty_cycle import check_movement_against_duty_cycle, load_state
from progressive_automations_python.config import UP_RATE, DOWN_RATE

# Decorate core functions as tasks
move_to_height_task = task(move_to_height)
check_duty_cycle_status_task = task(check_duty_cycle_status_before_execution)


@flow
def simple_movement_flow(target_height: float):
    """Prefect flow for moving desk to a specific height with duty cycle management
    
    Movement will execute even if duty cycle capacity is full - it will wait as needed.
    """
    logger = get_run_logger()
    logger.info(f"=== SIMPLE MOVEMENT FLOW ===")
    logger.info(f"Target: {target_height}\"")
    
    # Check duty cycle status
    initial_status = check_duty_cycle_status_task()
    logger.info(f"Initial duty cycle: {initial_status['current_usage']:.1f}s / {initial_status['window_period']}s used")
    
    # Get current position
    state = load_state()
    current_height = state.get("last_position")
    
    if current_height is None:
        logger.error("❌ MOVEMENT ABORTED: No last known position")
        raise ValueError("No last known position in state file")
    
    # Check movement requirements
    check_result = check_movement_against_duty_cycle(target_height, current_height, UP_RATE, DOWN_RATE)
    
    if not check_result["allowed"]:
        # Movement not immediately possible - will wait
        wait_time = check_result.get("wait_time_needed", 0)
        logger.warning(f"⏳ Duty cycle capacity insufficient - will wait {wait_time:.1f}s before movement")
        
        # Wait for duty cycle to free up
        import time
        time.sleep(wait_time)
        logger.info(f"✅ Wait complete - proceeding with movement")
    
    # Execute the movement
    result = move_to_height_task(target_height)
    
    # Check final duty cycle status
    final_status = check_duty_cycle_status_task()
    
    # Log usage
    capacity_used = initial_status["remaining_capacity"] - final_status["remaining_capacity"]
    logger.info(f"Movement completed - Duty cycle used: {capacity_used:.1f}s")
    
    return {
        **result,
        "initial_duty_status": initial_status,
        "final_duty_status": final_status,
        "capacity_used": capacity_used,
        "wait_time": check_result.get("wait_time_needed", 0) if not check_result["allowed"] else 0
    }


# =============================================================================
# DEPLOYMENT FUNCTIONS
# =============================================================================

def deploy_custom_movements_flow(deployment_name: str = "custom-movements"):
    """Deploy the main custom movements flow"""
    
    deployment = custom_movements_flow.from_source(
        source=".",
        entrypoint="prefect_flows.py:custom_movements_flow",
    ).deploy(
        name=deployment_name,
        work_pool_name="default-process-pool",
    )
    
    print(f"✅ Deployment '{deployment_name}' created!")
    print(f"To run: prefect deployment run 'custom-movements-flow/{deployment_name}'")
    return deployment_name


def deploy_duty_cycle_monitoring(deployment_name: str = "duty-cycle-monitor", schedule_cron: str = None):
    """Deploy duty cycle monitoring flow with optional scheduling"""
    
    deploy_kwargs = {
        "name": deployment_name,
        "work_pool_name": "default-process-pool",
    }
    
    if schedule_cron:
        from prefect.client.schemas.schedules import CronSchedule
        deploy_kwargs["schedule"] = CronSchedule(cron=schedule_cron)
        print(f"Deploying with cron schedule: {schedule_cron}")
    
    deployment = scheduled_duty_cycle_check.from_source(
        source=".",
        entrypoint="prefect_flows.py:scheduled_duty_cycle_check",
    ).deploy(**deploy_kwargs)
    
    print(f"✅ Deployment '{deployment_name}' created!")
    if schedule_cron:
        print(f"Scheduled to run: {schedule_cron}")
    else:
        print(f"To run: prefect deployment run 'scheduled-duty-cycle-check/{deployment_name}'")
    return deployment_name


def deploy_test_sequence(deployment_name: str = "test-sequence"):
    """Deploy test sequence flow"""
    
    deployment = test_sequence_flow.from_source(
        source=".",
        entrypoint="prefect_flows.py:test_sequence_flow",
    ).deploy(
        name=deployment_name,
        work_pool_name="default-process-pool",
    )
    
    print(f"✅ Deployment '{deployment_name}' created!")
    print(f"To run: prefect deployment run 'test-sequence-flow/{deployment_name}'")
    return deployment_name


def deploy_all_flows():
    """Deploy all desk control flows"""
    print("=== DEPLOYING ALL SIMPLIFIED DESK CONTROL FLOWS ===")
    
    # Deploy main flows
    deploy_custom_movements_flow()
    deploy_test_sequence()
    
    # Deploy monitoring flows
    deploy_duty_cycle_monitoring("duty-cycle-monitor-scheduled", "*/10 * * * *")
    deploy_duty_cycle_monitoring("duty-cycle-monitor-immediate")
    
    print("\n🎉 All deployments created!")
    print("\nAvailable flows:")
    print("  1. custom-movements - Main movement execution")
    print("  2. test-sequence - Automated test sequence")
    print("  3. duty-cycle-monitor-scheduled - Auto monitoring (every 10min)")
    print("  4. duty-cycle-monitor-immediate - On-demand monitoring")
    
    return True


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            test_sequence_flow()
        elif sys.argv[1] == "movements":
            custom_movements_flow()
        elif sys.argv[1] == "monitor":
            duty_cycle_monitoring_flow()
        elif sys.argv[1] == "deploy":
            deploy_all_flows()
        else:
            print("Usage: python prefect_flows.py [test|movements|monitor|deploy]")
    else:
        custom_movements_flow()