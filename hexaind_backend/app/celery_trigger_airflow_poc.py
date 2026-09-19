import asyncio
import sys
import time

from dotenv import load_dotenv
from app.core.db.db_utils import get_db_async
from app.custom_logging import load_logging
from logging import getLogger
from app.services.notification.service import Notification
from app.services.notification.schema import (
    NotificationModel,
    NotificationType,
    NotificationCategory,
    NotificationImportance,
)
from app.services.workflows.scheduling.service import ScheduleService
from app.api.endpoints.v1.workflows.runner.routes import WorkflowRunnerRouter
from app.services.workflows.runner.service import RunService
from app.core.services.jwt_token_utils.jwt_token_utils import get_fresh_access_token

# Load environment variables from a .env file
load_dotenv()
load_logging()
logger = getLogger(__package__)


async def create_dag_based_on_workflow(
    schedule_id, workflow_id, project_id, token, site_id
):
    db_client_async = get_db_async()
    wf_runner = WorkflowRunnerRouter()
    config = {
        "run_source": "SCHEDULE",
        "run_source_details": {"schedule_id": schedule_id},
    }
    run_obj = await wf_runner.run_an_existing_workflow(
        site_id, project_id, workflow_id, config, token, db_client_async
    )
    return run_obj


async def create_job_notification(
    schedule_id, project_id, success: bool, running: bool
):
    try:
        db_client_async = get_db_async()
        scheduled_service = ScheduleService(db_async_client=db_client_async)

        existing_schedule = await scheduled_service.fetch_schedule_by_id_async(
            schedule_id=schedule_id
        )
        if success:
            if running:
                message = f"Job {existing_schedule.name} has been completed"
            else:
                message = f"Job {existing_schedule.name} has been triggered"
            notification_type = NotificationType.SUCCESS
            importance = NotificationImportance.MEDIUM
        else:
            if running:
                message = f"Job {existing_schedule.name} has failed"
            else:
                message = f"Job {existing_schedule.name} has failed to trigger"
            notification_type = NotificationType.ERROR
            importance = NotificationImportance.HIGH

        notification_obj = {
            "message": message,
            "category_id": schedule_id,
            "project_id": project_id,
            "notification_type": notification_type,
            "importance": importance,
            "notification_category": NotificationCategory.SCHEDULED_JOBS,
        }
        verified_notfication_obj = NotificationModel(**notification_obj)
        notification_service_obj = Notification(db_async_client=db_client_async)
        await notification_service_obj.create_notification(verified_notfication_obj)
    except Exception as e:
        logger.error(f"unable to create Job notification due to exception:{str(e)}")


async def check_status(schedule_id, project_id, run_id):
    db_client_async = get_db_async()

    run_service_obj = RunService(db_async_client=db_client_async)
    while True:

        run_obj = await run_service_obj.get_run_by_id_async(run_id=run_id)

        if run_obj.run_status == "SUCCEEDED":
            logger.info("job completed successfully")
            is_success = True
            await create_job_notification(
                schedule_id=schedule_id,
                project_id=project_id,
                success=is_success,
                running=True,
            )
            break

        elif run_obj.run_status == "FAILED":
            logger.info("JOB has failed ")
            is_success = False
            await create_job_notification(
                schedule_id=schedule_id,
                project_id=project_id,
                success=is_success,
                running=True,
            )
            break
        elif run_obj.run_status == "IDLE":
            break

        time.sleep(1)


if __name__ == "__main__":
    if len(sys.argv) != 6:
        logger.error(
            "Usage: python airflow_poc.py <schedule_id> <workflow_id> <project_id> <token> <site_id>"
        )
        sys.exit(1)

    schedule_id = str(sys.argv[1])
    workflow_id = str(sys.argv[2])
    project_id = str(sys.argv[3])
    token = str(sys.argv[4])
    site_id = str(sys.argv[5])
    token = get_fresh_access_token(token)
    logger.info(f"token = {token}")
    logger.info(f"schedule_id = {schedule_id}")
    logger.info(f"workflow_id = {workflow_id}")
    logger.info(f"site_id = {site_id}")
    logger.info(f"workflow_id = {workflow_id}")
    logger.info("starting method to trigger run")

    try:
        run_obj = asyncio.run(
            create_dag_based_on_workflow(
                schedule_id, workflow_id, project_id, token, site_id
            )
        )
        is_success = True
    except Exception as e:
        is_success = False
        logger.exception(f"Unable to schedule a wf with wf_id {e}")
        raise
    
    finally:
        asyncio.run(
            create_job_notification(
                schedule_id=schedule_id,
                project_id=project_id,
                success=is_success,
                running=False,
            )
        )
        logger.info(f"Completed scheduling with wf_id")
        asyncio.run(
            check_status(
                schedule_id=schedule_id, project_id=project_id, run_id=run_obj.run_id
            )
        )
