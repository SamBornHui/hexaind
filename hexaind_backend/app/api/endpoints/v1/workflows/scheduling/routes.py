import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi.params import Query

from app.api.rbac.end_points_v1_access_control import CheckNameRoute
from app.core.db.db_utils import get_db_async
from app.services.access_controls.user_projects.service import (
    UsersProjectsMappingsService,
)
from app.services.admin.authentication.service import AuthenticationService

from app.services.workflows.scheduling.schemas import (
    DeleteResponse,
    PauseRequest,
    PauseResponse,
    ScheduleRequest,
    ScheduleResponse,
    GetAllSchedulesResponse,
    UpdateScheduleRequest,
    WFSchedule,
    GetAllSchedulesRequest,
)
from app.services.workflows.scheduling.service import ScheduleService
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from app.services.notification.service import Notification
from app.services.notification.schema import (
    NotificationModel,
    NotificationMessages,
    NotificationType,
    NotificationCategory,
    NotificationImportance,
)
from app.services.workflows.designer.service import WorkflowDesignerService


logger = logging.getLogger(__package__)

scheduling_router = APIRouter(tags=["Scheduling"], route_class=CheckNameRoute)


class SchedulingRouter:

    def __init__(self):
        pass

    @staticmethod
    @scheduling_router.post(
        "/v1/sites/{site_id}/projects/{project_id}/scheduling/create_schedule",
        response_model=ScheduleResponse,
    )
    async def create_schedule(
        site_id: str,
        project_id: str,
        sc_req: ScheduleRequest,
        token: str = "",
        client: AsyncIOMotorClient = Depends(get_db_async),
    ):

        try:
            logger.info("inside create schedule,")
            auth_serv = AuthenticationService(db_async_client=client)
            scheduled_service = ScheduleService(db_async_client=client)
            user = await auth_serv.get_user_by_token_or_id(token=token)
            logger.info(f"Current user: {user.name}")
            schedule_data = WFSchedule(
                name=sc_req.name,
                project_id=project_id,
                site_id=site_id,
                workflow_id=sc_req.workflow_id,
                start_date=sc_req.start_date,
                end_date=sc_req.end_date,
                scheduled_interval=sc_req.schedule_interval,
                schedule_interval_metadata=sc_req.schedule_interval_metadata,
                schedule_type=sc_req.schedule_type,
                event_based_config=sc_req.event_based_config,
                is_active=True,
                dag_file_path="",
                created_by_id=user.id,
                created_at=datetime.now(timezone.utc),
                last_modified_by_id=user.id,
                last_modified_at=datetime.now(timezone.utc),
                repeat_type=sc_req.repeat_type,
                repeat_value=sc_req.repeat_value,
                cron_week_days=sc_req.cron_week_days,
            )

            scheduled_id = await scheduled_service.create_schedule(
                token=token, wf_schedule=schedule_data, tags=sc_req.tags
            )
            logger.info(f"Created schedule with schedule id: {scheduled_id}")

            try:
                # creating notification
                message = f"Job {sc_req.name} has been scheduled"
                notification_obj = {
                    "message": message,
                    "category_id": scheduled_id,
                    "project_id": project_id,
                    "notification_type": NotificationType.INFO,
                    "importance": NotificationImportance.MEDIUM,
                    "notification_category": NotificationCategory.SCHEDULED_JOBS,
                }
                verified_notfication_obj = NotificationModel(**notification_obj)
                notification_service_obj = Notification(db_async_client=client)
                await notification_service_obj.create_notification(
                    verified_notfication_obj
                )
            except Exception as e:
                logger.info(f"Notification is not created due to {str(e)}")

            return ScheduleResponse(schedule_id=scheduled_id, succeeded=True)
        except KeyError as e:
            logger.exception(f"failed to create schedule: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create schedule: {e}",
            )
        except Exception as e:
            logger.exception(f"failed to create schedule {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create schedule: {e}",
            )

    @staticmethod
    @scheduling_router.post(
        "/v1/sites/{site_id}/projects/{project_id}/scheduling/update_schedule",
        response_model=ScheduleResponse,
    )
    async def modify_schedule(
        site_id: str,
        project_id: str,
        sc_req: UpdateScheduleRequest,
        token: str = "",
        client: AsyncIOMotorClient = Depends(get_db_async),
    ):

        try:
            logger.info("inside modify schedule.")
            auth_serv = AuthenticationService(db_async_client=client)
            scheduled_service = ScheduleService(db_async_client=client)

            user = await auth_serv.get_user_by_token_or_id(token=token)
            logger.info(f"Current user: {user.name}")

            existing_schedule = await scheduled_service.fetch_schedule_by_id_async(
                schedule_id=sc_req.schedule_id
            )

            schedule_data = WFSchedule(
                name=sc_req.name,
                project_id=project_id,
                site_id=site_id,
                workflow_id=sc_req.workflow_id,
                start_date=sc_req.start_date,
                end_date=sc_req.end_date,
                scheduled_interval=sc_req.schedule_interval,
                schedule_interval_metadata=sc_req.schedule_interval_metadata,
                schedule_type=sc_req.schedule_type,
                is_active=True,
                dag_file_path="",
                created_by_id=existing_schedule.created_by_id,
                created_at=existing_schedule.created_at,
                last_modified_by_id=user.id,
                last_modified_at=datetime.now(timezone.utc),
                repeat_type=sc_req.repeat_type,
                repeat_value=sc_req.repeat_value,
                cron_week_days=sc_req.cron_week_days,
            )
            # deleting existing schedule
            await scheduled_service.delete_schedule(schedule_id=sc_req.schedule_id)
            logger.info(f"Deleted schedule {sc_req.schedule_id}")
            created_id = await scheduled_service.create_schedule(
                token=token, wf_schedule=schedule_data, tags=sc_req.tags
            )
            logger.info(f"Updated Schedule {created_id}")
            try:
                # creating notification
                message = f"Job {existing_schedule.name} has been modified"
                notification_obj = {
                    "message": message,
                    "category_id": created_id,
                    "project_id": project_id,
                    "notification_type": NotificationType.INFO,
                    "importance": NotificationImportance.MEDIUM,
                    "notification_category": NotificationCategory.SCHEDULED_JOBS,
                }
                verified_notfication_obj = NotificationModel(**notification_obj)
                notification_service_obj = Notification(db_async_client=client)
                await notification_service_obj.create_notification(
                    verified_notfication_obj
                )
            except Exception as e:
                logger.info(f"Notification is not created due to {str(e)}")

            return ScheduleResponse(schedule_id=created_id, succeeded=True)

        except Exception as e:
            logger.exception(f"failed to modify schedule {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create schedule: {e}",
            )

    @staticmethod
    @scheduling_router.post(
        "/v1/sites/{site_id}/projects/{project_id}/scheduling/pause_schedule",
        response_model=PauseResponse,
    )
    async def pause_schedule(
        site_id: str,
        project_id: str,
        config: PauseRequest,
        token: str = "",
        client: AsyncIOMotorClient = Depends(get_db_async),
    ):

        try:
            logger.info("inside pause schedule")
            auth_serv = AuthenticationService(db_async_client=client)
            scheduled_service = ScheduleService(db_async_client=client)

            user = await auth_serv.get_user_by_token_or_id(token=token)
            logger.info(f"Current user: {user.name}")
            result = await scheduled_service.pause_dag(
                last_modified_id=user.id,
                schedule_id=config.schedule_id,
                is_paused=config.is_paused,
            )
            logger.info(f"Paused the dag {config.schedule_id}.py")

            return PauseResponse(
                succeeded=True, message="Updated DAG status succesfully."
            )

        except Exception as e:
            logger.exception(f"failed to pause schedule {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update is_active: {e}",
            )

    @staticmethod
    @scheduling_router.delete(
        "/v1/sites/{site_id}/projects/{project_id}/scheduling/delete_schedule/{schedule_id}",
        response_model=DeleteResponse,
    )
    async def delete_schedule(
        site_id: str,
        project_id: str,
        schedule_id: str,
        token: str = "",
        client: AsyncIOMotorClient = Depends(get_db_async),
    ):

        try:
            logger.info("inside the delete schedule")
            scheduled_service = ScheduleService(db_async_client=client)

            result = await scheduled_service.delete_schedule(schedule_id=schedule_id)
            logger.info(f"deleted the requested schedule of the dag . {result}")
            return DeleteResponse(
                succeeded=True, message="Delete DAG Schedule successfully."
            )

        except Exception as e:
            logger.exception(f"failed to delete schedule {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update is_active: {e}",
            )

    @staticmethod
    @scheduling_router.post(
        "/v1/sites/{site_id}/projects/{project_id}/scheduling/get_all_schedules",
        response_model=GetAllSchedulesResponse,
        status_code=status.HTTP_200_OK,
    )
    async def get_all_schedules(
        site_id: str,
        project_id: str,
        config: GetAllSchedulesRequest,  # add token
        page_limit: int = Query(default=100),
        page_number: int = Query(default=1),
        search_term: Optional[str] = None,
        max_runs_fetch_limit: int = Query(default=5),
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> GetAllSchedulesResponse:

        try:
            logger.info("inside get all schedules.")
            schedule_service = ScheduleService(db_async_client=client)
            if config.get_details:
                schedules, count = (
                    await schedule_service.fetch_all_schedules_with_details_async(
                        project_id=project_id,
                        search_term=search_term,
                        page_number=page_number,
                        page_limit=page_limit,
                        max_runs_fetch_limit=max_runs_fetch_limit,
                    )
                )
                fetch_user_details_for = [
                    schedule.created_by_id for schedule in schedules
                ]
                users_projects_mappings_service = UsersProjectsMappingsService(
                    db_async_client=client
                )
                users_list = await users_projects_mappings_service.get_users_dict(
                    users_list=fetch_user_details_for
                )
                for schedule in schedules:
                    if schedule.created_by_id in users_list:
                        schedule.created_by_name = users_list.get(
                            schedule.created_by_id
                        ).name
                    else:
                        schedule.created_by_name = "Unknown"
            else:
                schedules, count = await schedule_service.fetch_all_schedules_async(
                    project_id=project_id,
                    search_term=search_term,
                    page_number=page_number,
                    page_limit=page_limit,
                )

            logger.info(f"retrieved all the schedules. Count: {count}")

            return GetAllSchedulesResponse(schedules=schedules, total_count=count)

        except Exception as e:
            logger.exception(f"failed to get all schedules: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={f"failed to get schedules {str(e)}"},
            )

    @scheduling_router.get(
        "/v1/sites/{site_id}/projects/{project_id}/scheduling/get_schedule_by_id/{schedule_id}",
        response_model=WFSchedule,
        status_code=status.HTTP_200_OK,
    )
    async def get_schedule_by_id(
        site_id: str,
        project_id: str,
        schedule_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> WFSchedule:

        try:
            logger.info("inside get schedule by id.")
            schedule_service = ScheduleService(db_async_client=client)

            logger.info(
                f"will return the schedule fetched schedule_id: {schedule_id}. "
            )
            return await schedule_service.fetch_schedule_by_id_async(
                schedule_id=schedule_id
            )

        except Exception as e:
            logger.exception(
                f"failed to get schedule based on schedule_id {schedule_id}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={f"failed to get schedule, {str(e)}"},
            )


scheduling_router_obj = SchedulingRouter()
