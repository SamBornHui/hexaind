import logging
import traceback
from typing import Optional, Dict

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
    UploadFile,
    Form,
    File,
)
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient

from app.api.rbac.end_points_v1_access_control import CheckNameRoute
from app.config.env_vars import environment
from app.core.db.db_utils import get_db_async
from app.core.services.jwt_token_utils.jwt_token_utils import decodeJWT
from app.services.admin.authentication.service import AuthenticationService
from app.services.admin.projects.service import ProjectService
from app.services.data.folder_management.service import FolderManagement
from app.services.notification.schema import (
    NotificationCategory,
    NotificationImportance,
    NotificationMessages,
    NotificationModel,
    NotificationType,
)
from app.services.notification.service import Notification
from app.services.workflows.designer.service import WorkflowDesignerService
from app.services.workflows.runner.service import RunService
from app.services.workflows.sessions.service import WorkflowSessionService
from app.services.workflows.workflow_designer.schemas import *
from app.services.AI.rescale.schemas import StopRescale
from app.services.AI.models.service import ModelService
from app.services.workflows.workflow_designer.service import (
    InteractiveWorkflowDesginerService,
)
from app.actions import Actions
logger = logging.getLogger(__package__)
interactive_workflow_designer_router = APIRouter(
    tags=["Interactive Workflow Designer", "IWD Designer"], route_class=CheckNameRoute
)


class InteractiveWorkflowDesignerRouter:

    def __init__(self):
        pass

    @interactive_workflow_designer_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/sessions/{sessionId}/workflow/save",
        status_code=status.HTTP_200_OK,
        openapi_extra={"actions":Actions.Save_workflow.value},

    )
    async def save_workflow_in_session(
        siteId: str,
        projectId: str,
        sessionId: str,
        saveObj: Dict,
        token: str = "",
        user_id: str = "",
        client: AsyncIOMotorClient = Depends(get_db_async),
    ):

        try:
            if user_id:
                last_updated_by = user_id
            elif token:
                decoded_token = decodeJWT(token=token)
                last_updated_by = decoded_token.get("user_id", "")
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "save_workflow_in_session_error",
                        "message": "User id not found",
                    },
                )

            interactive_designer_service = InteractiveWorkflowDesginerService(
                db_async_client=client
            )

            # Dict to SaveWorkflowRequest
            save_workflow_request = SaveWorkflowRequest(**saveObj)
            await interactive_designer_service.save_workflow_in_session(
                session_id=sessionId,
                save_workflow_obj=save_workflow_request,
                last_updated_by=last_updated_by,
            )

            # prepare response
            return SaveWorkflowResponse(invalid_widgets=save_workflow_request.validation_errors) #TODO

        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "save_workflow_in_session_error", "message": str(e)},
            )

    @interactive_workflow_designer_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/sessions/{sessionId}/workflow/saveas",
        response_model=SaveAsWorkflowResponse,
        status_code=status.HTTP_201_CREATED,
        openapi_extra={"actions":Actions.Save_workflow.value},
    )
    async def saveas_workflow_in_session(
        siteId: str,
        projectId: str,
        sessionId: str,
        saveasObj: SaveAsWorkflowRequest,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> SaveAsWorkflowResponse:

        try:
            interactive_designer_service = InteractiveWorkflowDesginerService(
                db_async_client=client
            )
            workflow_id = await interactive_designer_service.saveas_workflow_in_session(
                session_id=sessionId, save_workflow_obj=saveasObj
            )

            # creating notification
            workflow_designer_obj = WorkflowDesignerService(db_async_client=client)
            workflow_obj = await workflow_designer_obj.get_workflow_by_id_async(
                workflow_id
            )
            message = f"Workflow {workflow_obj.name} has been published"
            notification_obj = {
                "message": message,
                "category_id": workflow_id,
                "project_id": projectId,
                "notification_type": NotificationType.SUCCESS,
                "importance": NotificationImportance.MEDIUM,
                "notification_category": NotificationCategory.WORKFLOWS,
            }
            verified_notfication_obj = NotificationModel(**notification_obj)
            notification_service_obj = Notification(db_async_client=client)
            await notification_service_obj.create_notification(verified_notfication_obj)

            return SaveAsWorkflowResponse(workflow_id=workflow_id)

        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "save_workflow_in_session_error", "message": str(e)},
            )

    @interactive_workflow_designer_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/sessions/{sessionId}/workflow/duplication/{type}",
        response_model=SaveAsWorkflowResponse,
        status_code=status.HTTP_201_CREATED,
    )
    async def duplicate_workflow_in_session(
        siteId: str,
        projectId: str,
        sessionId: str,
        duplicateObj: DuplicateWorkflowRequest,
        type: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> SaveAsWorkflowResponse:

        try:
            interactive_designer_service = InteractiveWorkflowDesginerService(
                db_async_client=client
            )

            if type == "master":
                data = await interactive_designer_service.duplicate_master_workflow(
                    duplicate_workflow_request_obj=duplicateObj,
                    site_id=siteId,
                    project_id=projectId,
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                    detail={
                        "code": "duplicate_workflow_in_session",
                        "message": "Only master workflow duplication is allowed at this moment.",
                    },
                )

            _ = await InteractiveWorkflowDesignerRouter.save_workflow_in_session(
                siteId=siteId,
                projectId=projectId,
                sessionId=data["new_session_id"],
                saveObj=data["save_object"],
                user_id=duplicateObj.user_id,
                client=client,
            )

            message = f"New Workflow Session {duplicateObj.name} has been created."
            notification_obj = {
                "message": message,
                "category_id": "",
                "project_id": projectId,
                "notification_type": NotificationType.SUCCESS,
                "importance": NotificationImportance.MEDIUM,
                "notification_category": NotificationCategory.WORKFLOWS,
            }
            verified_notfication_obj = NotificationModel(**notification_obj)
            notification_service_obj = Notification(db_async_client=client)
            await notification_service_obj.create_notification(verified_notfication_obj)

            return SaveAsWorkflowResponse(workflow_id="")
        except HTTPException as e:
            logger.error(f"Error in duplicate_workflow_in_session:\nstatus_code: {e.status_code}\ndetail: {e.detail}", exc_info=True)
            raise HTTPException(status_code=e.status_code, detail=e.detail)
        except Exception as e:
            logger.error(f"Error in duplicate_workflow_in_session: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "duplicate_workflow_in_session", "message": str(e)},
            )

    @interactive_workflow_designer_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/sessions/{sessionId}/workflow/template",
        response_model=SaveAsWorkflowResponse,
        status_code=status.HTTP_201_CREATED,
    )
    async def save_workflow_as_template(
        siteId: str,
        projectId: str,
        sessionId: str,
        # templateObj: DuplicateWorkflowRequest,
        name: str = Form(...),
        description: str = Form(...),
        user_name: str = Form(...),
        user_id: str = Form(...),
        workflow_id: str = Form(...),
        version_tag: str = Form(...),
        file: UploadFile = File(...),
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> SaveAsWorkflowResponse:

        try:
            templateObj = {
                "name": name,
                "description": description,
                "user_name": user_name,
                "user_id": user_id,
                "workflow_id": workflow_id,
                "version_tag": version_tag,
            }

            interactive_designer_service = InteractiveWorkflowDesginerService(
                db_async_client=client
            )

            data = await interactive_designer_service.save_workflow_as_template(
                session_id=sessionId,
                project_id=projectId,
                templateObj=DuplicateWorkflowRequest(**templateObj),
                file=file,
            )

            workflow_id = data["new_workflow_id"]

            # creating notification
            workflow_designer_obj = WorkflowDesignerService(db_async_client=client)
            workflow_obj = await workflow_designer_obj.get_workflow_by_id_async(
                workflow_id
            )
            message = f"Workflow {workflow_obj.name} has been saved as a template "
            notification_obj = {
                "message": message,
                "category_id": workflow_id,
                "project_id": projectId,
                "notification_type": NotificationType.SUCCESS,
                "importance": NotificationImportance.MEDIUM,
                "notification_category": NotificationCategory.WORKFLOWS,
            }
            verified_notfication_obj = NotificationModel(**notification_obj)
            notification_service_obj = Notification(db_async_client=client)
            await notification_service_obj.create_notification(verified_notfication_obj)

            return SaveAsWorkflowResponse(workflow_id=workflow_id)

        except Exception as e:
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "save_workflow_as_template_error", "message": str(e)},
            )

    @interactive_workflow_designer_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/sessions/{sessionId}/workflow/run",
        status_code=status.HTTP_200_OK,
        openapi_extra={"actions":Actions.Run_workflow.value},

    )
    async def run_workflow_in_session(
        siteId: str,
        projectId: str,
        sessionId: str,
        runObj: RunWorkflowInSession,
        token: str = "",
        client: AsyncIOMotorClient = Depends(get_db_async),
    ):

        try:
            auth_service = AuthenticationService(db_async_client=client)
            user = await auth_service.get_user_by_token_or_id(token=token)

            session_service = WorkflowSessionService(db_async_client=client)
            session_record = await session_service.get_workflow_session_async(
                session_id=sessionId
            )

            ## unlink workflow run id from models for master case
            if session_record.run_id:
                model_obj = ModelService(db_async_client=client)
                await model_obj.unlink_wf_run_id_from_models(
                    project_id=projectId, run_id=session_record.run_id
                )

            destination_folder = Path(
                environment.data_folder_format_string.format(
                    projectId,
                    session_record.workflow_id,
                    session_record.run_id,
                )
            )

            proj_service = ProjectService(db_async_client=client)
            project = await proj_service.get_project_by_id_async(project_id=projectId)

            workflow_service = WorkflowDesignerService(db_async_client=client)
            workflow: Workflow = await workflow_service.get_workflow_by_id_async(
                workflow_id=session_record.workflow_id
            )
            folder_names = {
                f"p_{projectId}": project.name,
                "Workflow_Results": "WorkflowResults",
                f"wf_{session_record.workflow_id}": workflow.name,
                f"r_{session_record.run_id}": f"Run at {str(datetime.now())}",
            }

            folder_mngmnt_service = FolderManagement(db_async_client=client)
            await folder_mngmnt_service.create_subfolders(
                siteId=siteId,
                projectId=projectId,
                user_id=user.id,
                folder_names=folder_names,
                full_path=str(destination_folder),
            )
            interactive_designer_service = InteractiveWorkflowDesginerService(
                db_async_client=client
            )
            await interactive_designer_service.run_workflow_in_session(
                session_id=sessionId, clear_outputs=runObj.rerun_completed_widgets
            )

        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "run_workflow_in_session_error", "message": str(e)},
            )

    @interactive_workflow_designer_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/sessions/{sessionId}/workflow/stop",
        status_code=status.HTTP_200_OK,
    )
    async def stop_workflow_in_session(
        siteId: str,
        projectId: str,
        sessionId: str,
        stop_rescale_info: Optional[StopRescale] = None,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ):

        try:
            interactive_designer_service = InteractiveWorkflowDesginerService(
                db_async_client=client
            )
            await interactive_designer_service.stop_workflow_in_session(
                session_id=sessionId, stop_rescale_info=stop_rescale_info
            )

        except Exception as e:
            logger.error("stop_workflow_in_session_error", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "stop_workflow_in_session_error", "message": str(e)},
            )

    @interactive_workflow_designer_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/sessions/{sessionId}/workflow/widget/{widgetURN}/run",
        status_code=status.HTTP_200_OK,
        openapi_extra={"actions":Actions.Run_workflow.value},

    )
    async def run_widget_workflow_in_session(
        siteId: str,
        projectId: str,
        sessionId: str,
        widgetURN: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ):

        try:
            interactive_designer_service = InteractiveWorkflowDesginerService(
                db_async_client=client
            )
            await interactive_designer_service.run_widget_workflow_in_session(
                session_id=sessionId, widget_urn=widgetURN
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "stop_workflow_in_session_error", "message": str(e)},
            )

    @interactive_workflow_designer_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/sessions/{sessionId}/workflow/widget/{widgetURN}/stop",
        status_code=status.HTTP_200_OK,
    )
    async def stop_widget_workflow_in_session(
        siteId: str,
        projectId: str,
        sessionId: str,
        widgetURN: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ):

        try:
            interactive_designer_service = InteractiveWorkflowDesginerService(
                db_async_client=client
            )
            await interactive_designer_service.stop_workflow_in_session(
                session_id=sessionId
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "stop_workflow_in_session_error", "message": str(e)},
            )

    @interactive_workflow_designer_router.get(
        "/v1/sites/{siteId}/projects/{projectId}/sessions/{sessionId}/workflow/run/status",
        response_model=WorkflowSessionRunStatus,
        status_code=status.HTTP_200_OK,
    )
    async def workflow_run_status_in_session(
        siteId: str,
        projectId: str,
        sessionId: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> WorkflowSessionRunStatus:

        try:

            interactive_designer_service = InteractiveWorkflowDesginerService(
                db_async_client=client
            )
            session_workflow_run_status: WorkflowSessionRunStatus = (
                await interactive_designer_service.get_workflow_run_status_in_session(
                    session_id=sessionId
                )
            )

            return session_workflow_run_status

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "workflow_run_status_in_session_error",
                    "message": str(e),
                },
            )

    @interactive_workflow_designer_router.get(
        "/v1/sites/{siteId}/projects/{projectId}/sessions/{sessionId}/workflow/run/widget/{widgetURN}/results",
        response_model=List[WidgetResultResponse],
        status_code=status.HTTP_200_OK,
    )
    async def widget_run_results_workflow_in_session(
        siteId: str,
        projectId: str,
        sessionId: str,
        widgetURN: str,
        output_name: Optional[str] = None,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> List[WidgetResultResponse]:

        try:

            interactive_designer_service = InteractiveWorkflowDesginerService(
                db_async_client=client
            )
            session_workflow_widget_results = await interactive_designer_service.get_widget_run_results_workflow_in_session(
                session_id=sessionId, widget_urn=widgetURN, output_name=output_name
            )

            return session_workflow_widget_results

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "widget_run_results_workflow_in_session_error",
                    "message": "Please ensure the previous widget executes successfully before proceeding with the next one.",
                },
            )
