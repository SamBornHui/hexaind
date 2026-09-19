from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from app.core.db.db_utils import get_db_async, get_db_sync
from app.services.admin.authentication.schemas import (GenericResponse)
from app.api.rbac.end_points_v1_access_control import CheckNameRoute
from pydantic import EmailStr
from app.core.services.email_utils.email_utils import send_simple_mail
from app.services.admin.healthcheck.service import HealthCheckService
from app.services.access_controls.roles.service import RolesFeaturesMapService
from app.services.access_controls.user_projects.service import UsersProjectsMappingsService

logger = logging.getLogger(__package__)
healthcheck_router = APIRouter(prefix='/v1/healthcheck', tags=["Healthcheck"], route_class=CheckNameRoute)


class HealthCheckRouter:

    def __init__(self):
        pass

    @staticmethod
    @healthcheck_router.get("/test_mail_delivery")
    async def test_mail_delivery(email: EmailStr) -> GenericResponse:
        resp = send_simple_mail(to_mail_ids=[email])
        if resp:
            return GenericResponse(status=True, message=f"Successfully Sent the test mail to {email}")
        else:
            return GenericResponse(status=False, message=f"Failed to send test mail to {email}. Please check Network issues if any")
        
    @staticmethod
    @healthcheck_router.get("/get_database_status")
    async def test_database(async_client: AsyncIOMotorClient = Depends(get_db_async), sync_client = Depends(get_db_sync)):
        healthcheck_service = HealthCheckService(db_async_client=async_client, db_sync_client=sync_client)
        resp = await healthcheck_service.check_database_status()
        if resp:
            return resp
        else:
            return GenericResponse(status=False, message="Failed to get Database Health Check")
        
    @staticmethod
    @healthcheck_router.get("/get_users_details")
    async def get_users_details(async_client: AsyncIOMotorClient = Depends(get_db_async), sync_client = Depends(get_db_sync)):
        healthcheck_service = HealthCheckService(db_async_client=async_client, db_sync_client=sync_client)
        resp = await healthcheck_service.get_user_details()
        if resp:
            return resp
        else:
            return GenericResponse(status=False, message="Failed to get User Details")
        
    @staticmethod
    @healthcheck_router.get("/test_keyvault_access")
    async def test_keyvault_access(async_client: AsyncIOMotorClient = Depends(get_db_async), sync_client = Depends(get_db_sync)):
        healthcheck_service = HealthCheckService(db_async_client=async_client, db_sync_client=sync_client)
        return await healthcheck_service.test_secret_manager_access()
    
    @staticmethod
    @healthcheck_router.get("/create_app_permissions")
    async def test_keyvault_access(async_client: AsyncIOMotorClient = Depends(get_db_async), sync_client = Depends(get_db_sync)):
        try:
            service = RolesFeaturesMapService(db_async_client=async_client)
            cnt = await service.generate_app_permisssions_table()
            return {"status": True, "description": f"App Permissions created succussesfully. Count {cnt}"}
        except Exception as e:
            error = "Error While trying to insert app permissions"
            logger.exception(error)
            return

