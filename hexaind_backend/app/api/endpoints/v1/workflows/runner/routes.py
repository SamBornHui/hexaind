import logging
import traceback
from datetime import timedelta
from pathlib import Path
from typing import Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorClient

from app.api.rbac.end_points_v1_access_control import CheckNameRoute
from app.config.env_vars import environment
from app.core.celery.celery_worker import create_celery_app
from app.core.db.db_utils import get_db_async
from app.core.services.action.schemas import *
from app.core.services.action.service import ActionService
from app.core.services.jwt_token_utils.jwt_token_utils import JWTBearer, decodeJWT
from app.services.admin.authentication.service import AuthenticationService
from app.services.admin.projects.service import ProjectService
from app.services.data.folder_management.service import FolderManagement
from app.services.workflows.designer.service import Workflow, WorkflowDesignerService
from app.services.workflows.runner.schemas import (
    GetAllRunsResponse,
    RunActionsConfig,
    RunResponse,
    RunSource,
    RunStatusResponse,
    RunSummaryResponse,
    RunWidgetStatus,
)
from app.services.workflows.runner.service import (
    Run,
    RunService,
    RunSource,
    RunState,
    RunStatus,
    WorkflowCopy,
    WorkflowCopyService,
)
from app.services.workflows.sessions.service import WorkflowSessionService
from app.actions import Actions
workflow_runner_router = APIRouter(
    tags=["Workflows", "WF Runner"], route_class=CheckNameRoute
)
logger = logging.getLogger(__package__)


def trigger_workflow_run(start_urn: str, run_actions_list: List[RunActionsConfig]):
    logging.info("trigger workflow")

    start_action_id = None
    for run_actions in run_actions_list:
        if run_actions.urn == start_urn:
            start_action_id = run_actions.action_id
            break

    # inserting the start task in queue
    logger.info("creating celery app...")
    celeryApp = create_celery_app("run_workflow")
    celeryApp.send_task(
        "start_action",
        kwargs={"action_id": start_action_id},
        queue="start_end",
        routing_key="start",
    )


class WorkflowRunnerRouter:

    def __init__(self):
        pass

    @workflow_runner_router.get(
        "/v1/sites/{siteId}/projects/{projectId}/workflows/{workflowId}/run_summary/{runId}",
        response_model=RunSummaryResponse,
        status_code=status.HTTP_200_OK,
    )
    async def get_wf_run_summary(
        siteId: str,
        projectId: str,
        workflowId: str,
        runId: str,
        token: str = "",
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> RunSummaryResponse:

        try:
            decoded_token = decodeJWT(token=token)
            logger.info(
                f"Fetch wf run summary with runId {runId} by user {decoded_token.get('user_id','NotFound')}."
            )
            run_service = RunService(db_async_client=client)

            run = await run_service.get_run_by_id_async(runId)
            logger.info(f"retrieved info related to the workflow run {runId}")

            action_service = ActionService(db_async_client=client)
            actions: List[Action] = await action_service.get_actions_by_run_id_async(
                run_id=runId
            )

            widgets_status = [
                RunWidgetStatus(urn=action.action_config.urn, status=action.status)
                for action in actions
            ]

            failed_widget_urn = None
            if run.run_status == RunStatus.FAILED:
                # identify failed widget
                for widget_details in widgets_status:
                    if widget_details.status == ActionRunStatus.FAILED:
                        failed_widget_urn = widget_details.urn
                        break
            total_time_difference = run.last_modified_at - run.created_at
            days = total_time_difference.days
            hours, remainder = divmod(total_time_difference.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            formatted_difference = f"{days:02}:{hours:02}:{minutes:02}:{seconds:02}"

            return RunSummaryResponse(
                run=run,
                widgets_status=widgets_status,
                failed_widget_urn=failed_widget_urn,
                total_time=formatted_difference,
            )

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "failed to get run summary", "message": str(e)},
            )

    @workflow_runner_router.get(
        "/v1/sites/{siteId}/projects/{projectId}/workflows/{workflowId}/run",
        response_model=GetAllRunsResponse,
        status_code=status.HTTP_200_OK,
    )
    async def get_all_runs_for_workflow(
        siteId: str,
        projectId: str,
        workflowId: str,
        page_limit: int = Query(default=10),
        page_number: int = Query(default=1),
        search_term: Optional[str] = None,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> GetAllRunsResponse:

        try:
            logger.info("inside get all run for the workflow.")
            run_service = RunService(db_async_client=client)

            runs, count = await run_service.get_all_runs_in_project_async(
                projectId=projectId,
                search_term=search_term,
                page_number=page_number,
                page_limit=page_limit,
                workflowId=workflowId,
            )
            logger.info(f"retrieved all the workflow run. Count: {count}")

            return GetAllRunsResponse(runs=runs, total_count=count)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "failed to get runs for a workflow", "message": str(e)},
            )
    @staticmethod
    @workflow_runner_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/workflow/{workflowId}/run",
        response_model=RunResponse,
        openapi_extra={"actions":Actions.Run_workflow.value},
    )
    async def run_an_existing_workflow(
        siteId: str,
        projectId: str,
        workflowId: str,
        config: Dict = Body(...),
        token: str = "",
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> RunResponse:
        try:
            """
            This entire operation is written using db transactions
            Since this job should be fully atomic,
                * Either create run and place activities in collection
                * or Revoke entire transaction.
                * This can be achieved only with replica setup (# TODO)
            """
            logger.info("inside run existing workflow method.")

            session_service = WorkflowSessionService(db_async_client=client)
            session_record = await session_service.get_sessions_from_workflow(
                published_wf_id=workflowId
            )

            workflow_service = WorkflowDesignerService(db_async_client=client)
            workflow: Workflow = await workflow_service.get_workflow_by_id_async(
                workflow_id=workflowId
            )
            master_workflow = await workflow_service.get_workflow_by_id_async(
                workflow_id=session_record.workflow_id
            )

            actions = workflow.widgets
            if not actions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No widgets found in the workflow",
                )

            auth_service = AuthenticationService(db_async_client=client)
            user = await auth_service.get_user_by_token_or_id(token=token)

            proj_service = ProjectService(db_async_client=client)
            project = await proj_service.get_project_by_id_async(project_id=projectId)

            run_source = (
                RunSource.SCHEDULE
                if config.get("run_source") == "SCHEDULE"
                else RunSource.WORKFLOW
            )
            run_source_details = config.get("run_source_details", None)
            run_service = RunService(db_async_client=client)
            run_obj = Run(
                site_id=siteId,
                project_id=projectId,
                workflow_id=workflowId,
                created_at=datetime.now(timezone.utc),
                actions=[],
                owner_id=user.id,
                owner_name=user.name,
                run_source=run_source,
                run_source_details=run_source_details,
                run_status=RunStatus.RUNNING,
                run_state=RunState.START,
                interactive_mode=False,
                is_single_widget_run=False,
                schedule_to_delete_widgets=[],
                name=workflow.name,
                description="",
                last_modified_at=datetime.now(timezone.utc),
                last_modified_by_id=user.id,
            )

            run_id = await run_service.create_run_async(run_obj=run_obj)
            destination_folder = Path(
                environment.data_folder_format_string_for_published_wf.format(
                    projectId,
                    session_record.workflow_id,
                    workflowId,
                    run_id,
                )
            )
            folder_names = {
                f"p_{projectId}": project.name,
                "Workflow_Results": "WorkflowResults",
                f"wf_{session_record.workflow_id}": master_workflow.name,
                f"wf_{workflowId}": workflow.name,
                f"r_{run_id}": f"Run at {str(datetime.now())}",
            }

            folder_mngmnt_service = FolderManagement(db_async_client=client)
            await folder_mngmnt_service.create_subfolders(
                siteId=siteId,
                projectId=projectId,
                user_id=user.id,
                folder_names=folder_names,
                full_path=str(destination_folder),
            )

            logger.info(f"created run for the workflow with run id {run_id}")

            workflow_copy_service = WorkflowCopyService(db_async_client=client)
            await workflow_copy_service.create_workflow_copy_async(
                workflow=workflow, run_id=run_id
            )

            action_service = ActionService(db_async_client=client)
            actions_list: List[Action] = action_service.get_actions_from_widgets(
                run_id=run_id, actions=actions
            )

            run_actions_list: List[RunActionsConfig] = []
            for action in actions_list:
                action.run_id = run_id
                action_id = await action_service.create_action_async(action=action)
                run_actions_list.append(
                    RunActionsConfig(urn=action.action_config.urn, action_id=action_id)
                )

            logger.info("Updating the run actions and about to the run the workflow.")
            await run_service.update_run_action_config_async(
                run_id=run_id, run_action_config_list=run_actions_list
            )

            logger.info("trigerring the workflow...")
            trigger_workflow_run(workflow.start[0], run_actions_list)

            return RunResponse(run_id=run_id)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            logger.critical(f"Scheduled run with workflow id {workflowId} failed")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "failed to trigger a run for a pipeline",
                    "message": str(e),
                },
            )

    @workflow_runner_router.get(
        "/v1/sites/{siteId}/projects/{projectId}/workflow/{workflowId}/run/{runId}/status",
        response_model=RunStatusResponse,
    )
    async def get_workflow_run_status(
        siteId: str,
        projectId: str,
        workflowId: str,
        runId: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> RunStatusResponse:

        try:
            logger.info("Inside get workflow run status...")

            workflow_copy_service = WorkflowCopyService(db_async_client=client)
            workflow_copy: WorkflowCopy = (
                await workflow_copy_service.get_workflow_copy_by_run_id_async(
                    run_id=runId
                )
            )

            action_service = ActionService(db_async_client=client)
            actions: List[Action] = await action_service.get_actions_by_run_id_async(
                run_id=runId
            )

            widgets_status = [
                RunWidgetStatus(urn=action.action_config.urn, status=action.status)
                for action in actions
            ]
            logger.info(f"current workflow widgets status: {widgets_status}")

            return RunStatusResponse(
                workflow=workflow_copy.workflow, widgets_status=widgets_status
            )

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "Unable to fetch the run status record at this moment",
                    "message": str(e),
                },
            )

    @workflow_runner_router.get(
        "/v1/sites/{siteId}/projects/{projectId}/workflow/{workflowId}/run/{runId}/widget/{urn}/result",
        response_model=List[WidgetResultResponse],
    )
    async def get_workflow_widget_result(
        siteId: str,
        projectId: str,
        workflowId: str,
        runId: str,
        urn: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> List[WidgetResultResponse]:

        try:
            logger.info("inside get workflow widget result.")

            action_service = ActionService(db_async_client=client)
            logger.info("getting the result with run id and urn.")
            return await action_service.get_action_result_by_run_id_and_urn_async(
                run_id=runId, urn=urn
            )

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "Unable to fetch the results for the given widget at this moment",
                    "message": str(e),
                },
            )


workflow_runner_router_obj = WorkflowRunnerRouter()
