import logging
import traceback
from contextlib import contextmanager

from app.core.services.action_handler.handler import *
from app.custom_logging import ctx_action, ctx_widget, ctx_action_record, ctx_user
from app.services.admin.authentication.dao import AuthenticationDao
from app.services.workflows.designer.service import WorkflowDesignerService
from app.services.workflows.sessions.service import WorkflowSessionService
from app.config.env_vars import environment

logger = logging.getLogger(__package__)


def notify_end_action_to_action_manager(app, action_id: str):
    logger.info("Current widget execution is done.")
    app.send_task(
        "end_action",
        kwargs={"action_id": action_id},
        queue="start_end",
        routing_key="end",
    )


def initialize_worker(app, action_id):
    try:
        logger.info("Preparing the environment for the widget execution")
        ######################################################
        # common code for all the workers #
        ######################################################
        action_handler = ActionHandler(action_id)
        _, run_record = action_handler.initialize()

        if action_handler.action_record.status in [
            ActionRunStatus.FAILED,
            ActionRunStatus.SUCCEEDED,
        ]:  # we should not execute task twice
            return None

        action_handler.update_run_status(ActionRunStatus.RUNNING)
        widget: Widget = action_handler.get_widget_config()
        #######################################################
        logger.info("Successfully fetched the widget config")

        session_service = WorkflowSessionService(
            db_sync_client=action_handler.db_client,
        )
        session_record = session_service.get_sessions_from_workflow_sync(
            published_wf_id=run_record.workflow_id
        )

        workflow_service = WorkflowDesignerService(
            db_sync_client=action_handler.db_client
        )
        workflow: Workflow = workflow_service.get_workflow_by_id(
            workflow_id=run_record.workflow_id
        )

        if workflow.workflow_version == "v0":
            new_dataset_dir = environment.data_folder_format_string.format(
                run_record.project_id, run_record.workflow_id, run_record.id
            )
        else:
            new_dataset_dir = (
                environment.data_folder_format_string_for_published_wf.format(
                    run_record.project_id,
                    session_record.workflow_id,
                    run_record.workflow_id,
                    run_record.id,
                )
            )

        logger.info(f"Widget Config: {widget.config}")

        return action_handler, run_record, widget, new_dataset_dir

    except Exception as e:
        logger.error(f"Fail to initialize the Action Handler..! Exception: {str(e)}")
        return None


def workflow_exception_handler(action_handler, action_id, e: Exception):
    logger.error("Exception occured in task: " + repr(e) + traceback.format_exc())
    try:
        action_handler.action_failure_handler(
            action_id, exception_msg=str(e), traceback_msg=str(traceback.format_exc())
        )
    except Exception as e:
        logger.error(
            "Failure to update the action status: " + repr(e) + traceback.format_exc()
        )


@contextmanager
def common_widget_manager(app, action_id):

    widget_token, action_token = None, None
    app.log.redirect_stdouts(name="app.workers") # redirecting the stdout to the logger
    try:
        widget_token = ctx_widget.set(None)
        action_token = ctx_action.set(None)
        action_record_token = ctx_action_record.set(None)
        user_token = ctx_user.set(None)
        result = initialize_worker(app, action_id)
        if result is None:
            return
        action_handler, run_record, widget, new_dataset_dir = result
        widget_token = ctx_widget.set(widget)
        action_token = ctx_action.set(run_record)
        user_id = run_record.owner_id
        user = AuthenticationDao().get_user_by_id_sync(
            user_id=user_id
        )
        if user is not None:
            ctx_user.set({"email": user.email, "user_id": user_id})
        action_record_token = ctx_action_record.set(action_handler.action_record)
        yield result

    except Exception as e:
        workflow_exception_handler(
            action_handler=action_handler, action_id=action_id, e=e
        )

    finally:
        notify_end_action_to_action_manager(app=app, action_id=action_id)
        if widget_token and ctx_widget.get(widget_token) is not None:
            ctx_widget.reset(widget_token)
        if action_token and ctx_widget.get(action_token) is not None:
            ctx_action.reset(action_token)
        if user_token and ctx_user.get(user_token) is not None:
            ctx_user.reset(user_token)
        if (
            action_record_token
            and ctx_action_record.get(action_record_token) is not None
        ):
            ctx_action_record.reset(action_record_token)
