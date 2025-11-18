"""
Simplified Prefect flows for automated desk control.

Provides scheduled automation and workflow orchestration using Prefect.
Uses the comprehensive desk_controller.execute_custom_movements() function.
"""

import time
import os
import sys
from prefect import flow, task
from prefect.logging import get_run_logger

# Add the scripts directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our modular components  
from desk_controller import (
    move_to_height, 
    test_sequence, 
    LOWEST_HEIGHT,
    execute_custom_movements,
    check_duty_cycle_status_before_execution
)
from duty_cycle import show_duty_cycle_status, get_duty_cycle_status, load_state


@task
def log_info(message: str):
    """Log information message"""
    print(message)


@task
def duty_cycle_status_task():
    """
    Check duty cycle status as a Prefect task.
    Reuses existing check_duty_cycle_status_before_execution() from desk_controller.
    """
    logger = get_run_logger()
    
    try:
        # Use the existing function - no need to reimplement
        status = check_duty_cycle_status_before_execution()
        
        # Log for Prefect monitoring
        logger.info(f"Duty cycle check completed:")
        logger.info(f"  Usage: {status['current_usage']:.1f}s / 120s ({status['percentage_used']:.1f}%)")
        logger.info(f"  Remaining: {status['remaining_capacity']:.1f}s")
        logger.info(f"  Position: {status['current_position']}\"")
        
        return status
        
    except Exception as e:
        logger.error(f"Failed to check duty cycle status: {e}")
        raise


@task  
def execute_movement(target_height: float, current_height: float = None):
    """Execute a single movement as a Prefect task"""
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
def execute_custom_movements_task(config_file: str = "movement_configs.json"):
    """
    Execute custom movements from configuration file as a Prefect task.
    
    This is a thin wrapper around desk_controller.execute_custom_movements()
    which already handles all the complexity:
    - Loading movement configs
    - Pre-execution duty cycle checking  
    - Movement validation
    - Movement execution
    - Post-execution status reporting
    """
    logger = get_run_logger()
    logger.info(f"Executing custom movements from {config_file}")
    
    try:
        # This function does EVERYTHING - no need for separate loading/validation tasks
        result = execute_custom_movements(config_file)
        
        if result["success"]:
            logger.info(f"✅ All movements completed successfully ({result['successful']}/{result['total_movements']})")
        else:
            logger.info(f"⚠️ Movements completed with some failures ({result['failed']}/{result['total_movements']} failed)")
            
        return result
    except Exception as e:
        logger.error(f"❌ Custom movements execution failed: {e}")
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


# =============================================================================
# FLOWS
# =============================================================================

@flow
def simple_movement_flow(target_height: float, current_height: float = None):
    """Simple Prefect flow for moving to a specific height with duty cycle checking"""
    logger = get_run_logger()
    logger.info(f"=== SIMPLE MOVEMENT FLOW ===")
    logger.info(f"Target: {target_height}\", Current: {current_height}\"")
    
    # Check duty cycle status using existing function
    initial_status = duty_cycle_status_task()
    
    # Abort if insufficient capacity
    if initial_status["remaining_capacity"] < 1.0:
        logger.error("❌ MOVEMENT ABORTED: Insufficient duty cycle capacity")
        raise ValueError("Insufficient duty cycle capacity - must wait for reset")
    
    # Execute the movement
    result = execute_movement(target_height, current_height)
    
    # Check final duty cycle status
    final_status = duty_cycle_status_task()
    
    # Log usage
    capacity_used = initial_status["remaining_capacity"] - final_status["remaining_capacity"]
    logger.info(f"Movement completed - Duty cycle used: {capacity_used:.1f}s")
    
    return {
        **result,
        "initial_duty_status": initial_status,
        "final_duty_status": final_status,
        "capacity_used": capacity_used
    }


@flow
def custom_movements_flow(config_file: str = "movement_configs.json"):
    """
    Simplified Prefect flow to execute custom movements.
    
    Uses the comprehensive desk_controller.execute_custom_movements() function
    which already includes all necessary features internally.
    """
    logger = get_run_logger()
    logger.info("=== CUSTOM MOVEMENTS FLOW ===")
    
    # Execute custom movements - this function already does all the duty cycle checking
    result = execute_custom_movements_task(config_file)
    
    logger.info("Custom movements flow completed")
    return result


@flow
def duty_cycle_monitoring_flow():
    """
    Simplified duty cycle monitoring flow.
    Uses existing duty cycle checking functions.
    """
    logger = get_run_logger()
    logger.info("=== DUTY CYCLE MONITORING FLOW ===")
    
    # Use existing duty cycle status function
    status = duty_cycle_status_task()
    
    # Simple recommendation logic
    remaining = status["remaining_capacity"]
    
    if remaining < 5:
        recommendation = "wait"
        logger.warning("⚠️ VERY LOW CAPACITY - Recommend waiting for duty cycle reset")
    elif remaining < 15:
        recommendation = "small_movements_only"
        logger.warning("⚠️ LOW CAPACITY - Use small movements only")
    elif remaining < 60:
        recommendation = "moderate_planning"
        logger.info("✅ MODERATE CAPACITY - Plan movements carefully")
    else:
        recommendation = "normal_operations"
        logger.info("✅ GOOD CAPACITY - Normal operations possible")
    
    return {
        "status": status,
        "recommendation": recommendation,
        "operational_mode": recommendation
    }


@flow
def scheduled_duty_cycle_check():
    """
    Scheduled duty cycle monitoring using existing functions.
    Just wraps duty_cycle_monitoring_flow for scheduled execution.
    """
    logger = get_run_logger()
    logger.info("=== SCHEDULED DUTY CYCLE CHECK ===")
    
    # Use the monitoring flow
    result = duty_cycle_monitoring_flow()
    
    # Log summary for scheduled monitoring
    status = result["status"]
    logger.info(f"Scheduled duty cycle check:")
    logger.info(f"  Usage: {status['current_usage']:.1f}s / 120s ({status['percentage_used']:.1f}%)")
    logger.info(f"  Mode: {result['recommendation']}")
    
    # Alert on very low capacity
    if status["remaining_capacity"] < 10:
        logger.warning("🚨 ALERT: Very low duty cycle capacity remaining!")
    
    return result


@flow  
def test_sequence_flow(movement_distance: float = 0.5, rest_time: float = 10.0):
    """Prefect flow for automated test sequence"""
    logger = get_run_logger()
    logger.info(f"=== TEST SEQUENCE FLOW ===")
    logger.info(f"Distance: {movement_distance}\", Rest: {rest_time}s")
    
    # Check duty cycle before starting using existing function
    initial_status = duty_cycle_status_task()
    
    # Execute test sequence
    result = execute_test_sequence(movement_distance, rest_time)
    
    # Check final status
    final_status = duty_cycle_status_task()
    
    logger.info("Test sequence flow completed")
    return {
        **result,
        "initial_duty_status": initial_status,
        "final_duty_status": final_status
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