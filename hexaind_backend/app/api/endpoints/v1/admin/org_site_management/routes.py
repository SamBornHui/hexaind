import traceback
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List
from app.core.db.db_utils import get_db_async
from app.services.admin.org_site_management.schemas import Site, Role
from app.services.admin.org_site_management.service import OrgSiteManagementService
from app.core.services.jwt_token_utils.jwt_token_utils import JWTBearer
from app.api.rbac.end_points_v1_access_control import CheckNameRoute

logger = logging.getLogger(__package__)
role_mngt_router = APIRouter(prefix='/v1/site-management',  tags=['SiteManagement'], route_class=CheckNameRoute)

class AuthenticationRouter:
    
    def __init__(self):
        pass

    @role_mngt_router.get("/getRolesList")
    async def get_roles_list(token: str = '', client: AsyncIOMotorClient = Depends(get_db_async)) -> List[Role]:
        """
        Returns Users Roles List like Org Admin, Site Admin, Project Admin, User, Read only User
        """
        logger.info("inside get roles list.")
        try:
            org_mngt_service = OrgSiteManagementService(db_async_client=client)
            logger.info("Returning the user roles list")
            return await org_mngt_service.get_roles_list()
        
        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed with exception {e}")
        
    @role_mngt_router.get("/getSitesList")
    async def get_sites_list(token: str = '', client: AsyncIOMotorClient = Depends(get_db_async)) -> List[Site]:
        """
        Returns Available Sites List
        """
        logger.info("inside get sites list.")
        try:
            org_mngt_service = OrgSiteManagementService(db_async_client=client)
            logger.info("Returning the sites list")
            return await org_mngt_service.get_sites_list(token)
        
        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed with exception {e}")
