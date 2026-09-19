import asyncio
import os
import logging

from app.api.endpoints.v1.workflows.runner.routes import WorkflowRunnerRouter
from app.core.db.db_utils import get_db_async
from app.core.services.action_handler.handler import *
from app.core.services.jwt_token_utils.jwt_token_utils import getAccessToken
from app.services.admin.authentication.schemas import User
from app.services.admin.authentication.service import AuthenticationService
from app.services.workflows.designer.schemas import *
from app.config.env_vars import environment
from app.workers.utils import common_widget_manager
from app.core.celery.global_config import EVENTS_QUEUE
from app.core.celery.celery_worker import (
    create_celery_app,
)  # create_celery_non_global_app
from app.services.workflows.scheduling.service import ScheduleService

# create_celery_app


app = create_celery_app("events_manager_worker", default_queue=EVENTS_QUEUE)
logger = logging.getLogger(__package__)

global db_client
db_client = get_db_sync()

# async def run_wf():


async def asynchronous_functions(schedules):
    db_async_client = get_db_async()
    auth_service = AuthenticationService(db_async_client=db_async_client)
    wf_runner = WorkflowRunnerRouter()

    for schedule in schedules:
        print(schedule)
        # send_task_helper(task_name: "some_task" , config: {"scheudle_trigger"}, queue_name: "events",routing:key///}

        config = {
            "run_source": "SCHEDULE",
            "run_source_details": {"schedule_id": schedule.dag_id},
        }
        user_id = schedule.created_by_id
        user: User = await auth_service.get_user_with_id(user_id)
        token = getAccessToken(user.email, user.server_role_value, user.id)
        x = await wf_runner.run_an_existing_workflow(
            schedule.site_id,
            schedule.project_id,
            schedule.workflow_id,
            config,
            token,
            db_client_async,
        )
        logger.info(f"Run Status: {x}")


@app.task(name="task_schedule_workflows")
def task_schedule_workflows(**kwargs):
    logger.info("inside task_schedule_workflows")
    logger.info(f"KWARGS: {kwargs}")
    scheduling_service = ScheduleService(db_sync_client=db_client)

    schedules = scheduling_service.get_schedules_with_workflow(
        workflow_id=kwargs.get("workflow_id"), current_run_status=RunStatus.SUCCEEDED
    )

    asyncio.run(asynchronous_functions(schedules=schedules))
    logger.info("Completed all triggers.")
