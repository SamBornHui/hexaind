import logging
import traceback
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient

from app.api.rbac.end_points_v1_access_control import CheckNameRoute
from app.core.db.db_utils import get_db_async
from app.core.services.jwt_token_utils.jwt_token_utils import JWTBearer, decodeJWT
from app.services.access_controls.user_projects.service import (
    UsersProjectsMappingsService,
)
from app.services.admin.authentication.dao import AuthenticationDao
from app.services.admin.authentication.schemas import User
from app.services.admin.authentication.service import AuthenticationService
from app.services.notification.schema import (
    NotificationCategory,
    NotificationImportance,
    NotificationMessages,
    NotificationModel,
    NotificationType,
)
from app.services.notification.service import Notification
from app.services.workflows.designer.service import WorkflowDesignerService
from app.services.workflows.designer.widget_rules import *
from app.services.workflows.scheduling.service import ScheduleService
from app.services.workflows.sessions.schemas import (
    CreateWorkflowSessionRequest,
    CreateWorkflowSessionResponse,
    FavouriteWorkflow,
    FavouriteWorkflowResponse,
    GetAllSessionsResponse,
    WorkflowSessionDB,
)
from app.services.workflows.sessions.service import WorkflowSessionService
from app.actions import Actions

logger = logging.getLogger(__package__)
workflow_session_router = APIRouter(
    tags=["Workflows", "WF Session Manager"], route_class=CheckNameRoute
)


class WorkflowSessionRouter:

    def __init__(self):
        pass

    @workflow_session_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/workflow/session",
        response_model=CreateWorkflowSessionResponse,
        status_code=status.HTTP_201_CREATED,
        openapi_extra={"actions":Actions.Create_workflow.value}
    )
    async def create_workflow_session(
        siteId: str,
        projectId: str,
        session: CreateWorkflowSessionRequest,
        token: str = "",
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> CreateWorkflowSessionResponse:

        try:
            logger.info("creating workflow session")

            auth_serv = AuthenticationService(db_async_client=client)
            user_data = await auth_serv.get_user_by_token_or_id(token=token)

            workflow_session_service = WorkflowSessionService(db_async_client=client)
            session_id = await workflow_session_service.create_workflow_session_async(
                user_id=user_data.id,
                user_name=user_data.name,
                site_id=siteId,
                project_id=projectId,
                create_session_req_obj=session,
            )

            logger.info(f"created workflow session: {session_id}")

            # creating notification
            workflow_session_obj = (
                await workflow_session_service.get_workflow_session_async(session_id)
            )
            message = f"Workflow {workflow_session_obj.name} has been created"
            notification_obj = {
                "message": message,
                "category_id": workflow_session_obj.workflow_id,
                "project_id": projectId,
                "notification_type": NotificationType.INFO,
                "importance": NotificationImportance.MEDIUM,
                "notification_category": NotificationCategory.WORKFLOWS,
            }
            verified_notfication_obj = NotificationModel(**notification_obj)
            notification_service_obj = Notification(db_async_client=client)
            await notification_service_obj.create_notification(verified_notfication_obj)

            return CreateWorkflowSessionResponse(session_id=session_id)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "workflow_session_creation_error", "message": str(e)},
            )

    @workflow_session_router.delete(
        "/v1/sites/{siteId}/projects/{projectId}/workflow/session/{sessionId}"
    )
    async def delete_workflow_session(
        siteId: str,
        projectId: str,
        sessionId: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> JSONResponse:
        try:
            logger.info("Deleting workflow session")

            workflow_session_service = WorkflowSessionService(db_async_client=client)
            scheduling_service = ScheduleService(db_async_client=client)

            session = await workflow_session_service.get_workflow_session_async(
                session_id=sessionId
            )

            saved_workflows_to_delete = []
            for wf in session.saved_workflows:
                schedule_records = (
                await scheduling_service.fetch_schedules_by_workflow_id_async(
                    workflow_id=wf.workflow_id
                    )
                )
                # logger.info(f"schedule records {schedule_records}")
                logger.info(f"schedule records length {len(schedule_records)}")
                if len(schedule_records) > 0:
                    for schedule_record in schedule_records:
                        await scheduling_service.delete_schedule(
                            schedule_id=schedule_record.dag_id
                        )
                saved_workflows_to_delete.append(wf.workflow_id)
            
            await workflow_session_service.delete_workflow_session_async(
                session_id=sessionId, saved_workflow_ids=saved_workflows_to_delete
            )

            logger.info(f"deleted session with session_id: {sessionId}")
            return UpdateWorkflowResponse(success=True)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "session_delete_error", "message": str(e)},
            )
    @workflow_session_router.get(
        "/v1/sites/{siteId}/projects/{projectId}/session/{sessionId}",
        response_model=WorkflowSessionDB,
        status_code=status.HTTP_200_OK,
#        openapi_extra= {"actions":Actions.Create_workflow.value}
    )
    async def get_session_by_id(
        siteId: str,
        projectId: str,
        sessionId: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> WorkflowSessionDB:
        try:
            logger.info("getting session with session id's")

            workflow_session_service = WorkflowSessionService(db_async_client=client)

            logger.info("returning the session from session service.")

            return await workflow_session_service.get_workflow_session_async(
                session_id=sessionId
            )

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "while fetching workflow session", "message": str(e)},
            )

    @workflow_session_router.get(
        "/v1/sites/{siteId}/projects/{projectId}/session",
        response_model=GetAllSessionsResponse,
        status_code=status.HTTP_200_OK,
    )
    async def get_all_workflow_sessions(
        siteId: str,
        projectId: str,
        page_limit: int = Query(default=10),
        page_number: int = Query(default=1),
        search_term: Optional[str] = None,
        get_updated_details: bool = False,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> GetAllSessionsResponse:

        try:

            logger.info("getting all the sessions based on site and project id.")

            workflow_session_service = WorkflowSessionService(db_async_client=client)
            workflow_sessions, count = (
                await workflow_session_service.get_all_workflow_sessions_async(
                    projectId=projectId,
                    search_term=search_term,
                    page_number=page_number,
                    page_limit=page_limit,
                )
            )

            logger.info(
                f"retrieved all the workflow-sessions from database. Sessions count: {count}"
            )
            user_access_controls_service = UsersProjectsMappingsService(
                db_async_client=client
            )

            session_ids_to_remove = []
            if get_updated_details:
                workflow_service = WorkflowDesignerService(db_async_client=client)
                for session in workflow_sessions:
                    deactivated_wf = []
                    try:
                        # overriding session last modified by with recently updated master wf time
                        master_wf_details = (
                            await workflow_service.get_workflow_by_id_async(
                                workflow_id=session.workflow_id
                            )
                        )
                        await workflow_service.add_last_run_details_to(session)
                        session.last_modified_at = master_wf_details.last_modified_at

                        # adding updated details for saved wf's
                        for saved_wf in session.saved_workflows:
                            try:
                                wf_details = (
                                    await workflow_service.get_workflow_by_id_async(
                                        saved_wf.workflow_id
                                    )
                                )
                                await workflow_service.add_last_run_details_to(saved_wf)
                                saved_wf.name = wf_details.name
                                saved_wf.description = wf_details.description
                                users = (
                                    await user_access_controls_service.get_users_dict(
                                        [
                                            wf_details.last_modified_by_id,
                                            wf_details.owner_id,
                                        ]
                                    )
                                )
                                saved_wf.last_modified_by = (
                                    users.get(wf_details.last_modified_by_id).name
                                    if wf_details.last_modified_by_id in users
                                    else "user deactivated"
                                )
                                saved_wf.created_by = (
                                    users.get(wf_details.owner_id).name
                                    if wf_details.owner_id in users
                                    else "user deactivated"
                                )
                                saved_wf.created_at = wf_details.created_at
                                saved_wf.last_modified_at = wf_details.last_modified_at
                            except ValueError as e:
                                deactivated_wf.append(saved_wf)
                            except Exception as e:
                                logger.error(f"{str(e)}", exc_info=True)
                        session.saved_workflows = [
                            wf
                            for wf in session.saved_workflows
                            if wf not in deactivated_wf
                        ]
                    except Exception as e:
                        logger.error(
                            f"Got error while fetching latest data related to wf {session.workflow_id}, {str(e)}"
                        )
                        session_ids_to_remove.append(session.id)

            return GetAllSessionsResponse(
                sessions=workflow_sessions,
                invalid_session_ids=session_ids_to_remove,
                sessions_count=count,
                page_number=page_number,
                page_limit=page_limit,
            )
        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "while fetching workflow-sessions", "message": str(e)},
            )

    @workflow_session_router.get(
        "/v1/sites/{siteId}/projects/{projectId}/templates",
        response_model=GetAllSessionsResponse,
        status_code=status.HTTP_200_OK,
    )
    async def get_all_workflow_templates(
        siteId: str,
        projectId: str,
        page_limit: int = Query(default=10),
        page_number: int = Query(default=1),
        search_term: Optional[str] = None,
        get_updated_details: bool = False,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> GetAllSessionsResponse:

        try:

            logger.info("getting all the templates based on site and project id.")

            workflow_session_service = WorkflowSessionService(db_async_client=client)
            workflow_sessions, count = (
                await workflow_session_service.get_all_workflow_templates_async(
                    projectId=projectId,
                    search_term=search_term,
                    page_number=page_number,
                    page_limit=page_limit,
                )
            )

            logger.info(
                f"retrieved all the workflow-templates from database. templates count: {count}"
            )
            user_access_controls_service = UsersProjectsMappingsService(
                db_async_client=client
            )

            session_ids_to_remove = []
            if get_updated_details:
                workflow_service = WorkflowDesignerService(db_async_client=client)
                for session in workflow_sessions:
                    deactivated_wf = []
                    try:
                        # overriding session last modified by with recently updated master wf time
                        master_wf_details = (
                            await workflow_service.get_workflow_by_id_async(
                                workflow_id=session.workflow_id
                            )
                        )
                        await workflow_service.add_last_run_details_to(session)
                        session.last_modified_at = master_wf_details.last_modified_at

                        # adding updated details for saved wf's
                        for saved_wf in session.saved_workflows:
                            try:
                                wf_details = (
                                    await workflow_service.get_workflow_by_id_async(
                                        saved_wf.workflow_id
                                    )
                                )
                                await workflow_service.add_last_run_details_to(saved_wf)
                                saved_wf.name = wf_details.name
                                saved_wf.description = wf_details.description
                                users = (
                                    await user_access_controls_service.get_users_dict(
                                        [
                                            wf_details.last_modified_by_id,
                                            wf_details.owner_id,
                                        ]
                                    )
                                )
                                saved_wf.last_modified_by = (
                                    users.get(wf_details.last_modified_by_id).name
                                    if wf_details.last_modified_by_id in users
                                    else "user deactivated"
                                )
                                saved_wf.created_by = (
                                    users.get(wf_details.owner_id).name
                                    if wf_details.owner_id in users
                                    else "user deactivated"
                                )
                                saved_wf.created_at = wf_details.created_at
                                saved_wf.last_modified_at = wf_details.last_modified_at
                            except ValueError as e:
                                deactivated_wf.append(saved_wf)
                            except Exception as e:
                                logger.error(f"{str(e)}", exc_info=True)
                        session.saved_workflows = [
                            wf
                            for wf in session.saved_workflows
                            if wf not in deactivated_wf
                        ]
                    except Exception as e:
                        logger.error(
                            f"Got error while fetching latest data related to wf {session.workflow_id}, {str(e)}"
                        )
                        session_ids_to_remove.append(session.id)

            return GetAllSessionsResponse(
                sessions=workflow_sessions,
                invalid_session_ids=session_ids_to_remove,
                sessions_count=count,
                page_number=page_number,
                page_limit=page_limit,
            )
        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "while fetching workflow-templates", "message": str(e)},
            )

    @workflow_session_router.put(
        "/v1/sites/{siteId}/projects/{projectId}/session/{sessionId}",
        status_code=status.HTTP_200_OK,
        openapi_extra={"actions":Actions.Update_workflow.value}
    )
    async def update_workflow_session(
        siteId: str,
        projectId: str,
        sessionId: str,
        session: CreateWorkflowSessionRequest,
        token: str = "",
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> JSONResponse:
        try:
            logger.info("Updating the session...")
            decoded_token = decodeJWT(token=token)

            workflow_session_service = WorkflowSessionService(db_async_client=client)

            await workflow_session_service.update_workflow_session_async(
                user_id=decoded_token.get("user_id", ""),
                user_name="",
                site_id=siteId,
                project_id=projectId,
                sesssion_id=sessionId,
                new_session=session,
            )

            # as we uploaded the session name and description,these changes need to moved to master wf too , as edit option provided on master copy
            workflow_service = WorkflowDesignerService(db_async_client=client)
            workflow_session = (
                await workflow_session_service.get_workflow_session_async(
                    session_id=sessionId
                )
            )
            master_workflow = await workflow_service.get_workflow_by_id_async(
                workflow_session.workflow_id
            )
            master_workflow.name = workflow_session.name
            master_workflow.description = workflow_session.description
            await workflow_service.update_workflow_async(
                user_id=decoded_token.get("user_id", ""),
                workflow_id=workflow_session.workflow_id,
                new_workflow=master_workflow,
            )

            logger.info(f"updated the workflow. {UpdateWorkflowResponse(success=True)}")

            return UpdateWorkflowResponse(success=True)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "workflow_session_update_error", "message": str(e)},
            )

    @workflow_session_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/workflow/update_favourite",
        status_code=status.HTTP_200_OK,
    )
    async def favourite_workflow(
        siteId: str,
        projectId: str,
        favourite_workflow: FavouriteWorkflow,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> JSONResponse:
        try:
            workflow_session_service = WorkflowSessionService(db_async_client=client)
            await workflow_session_service.favourite_workflow(favourite_workflow)
            return FavouriteWorkflowResponse(
                message="Favouritee updated", workflow_id=favourite_workflow.workflow_id
            )

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "favourite_workflow_update_error", "message": str(e)},
            )
