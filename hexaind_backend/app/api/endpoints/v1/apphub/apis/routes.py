import logging
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient

from app.api.rbac.end_points_v1_access_control import CheckNameRoute
from app.core.db.db_utils import get_db_async
from app.services.apphub.services.apphub_service import AppHubService, AppInfo
from app.config.env_vars import apphub_environment

logger = logging.getLogger(__name__)

apphub_router = APIRouter(
    tags=["AppHub"], route_class=CheckNameRoute
)


class AppHubRouter:
    """Router for AppHub API endpoints."""

    def __init__(self) -> None:
        """Initialize the AppHub router."""
        pass

    @apphub_router.get(
        "/v1/apphub/applications",
        response_model=List[AppInfo],
        status_code=status.HTTP_200_OK,
    )
    async def get_applications(
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> List[AppInfo]:
        """
        Get a list of all applications from AppHub.
        
        Args:
            client: Database client
            
        Returns:
            List of AppInfo objects containing application information
            
        Raises:
            HTTPException: If there's an error retrieving applications
        """
        try:
            # Initialize AppHub service with environment variables
            apphub_service = AppHubService(
                host=apphub_environment.host,
                username=apphub_environment.username,
                password=apphub_environment.password
            )
            
            # Get applications list
            applications: List[AppInfo] = apphub_service.get_apps_list()
            
            return applications
            
        except Exception as e:
            logger.error(f"Error getting applications from AppHub: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "get_applications_error", "message": str(e)},
            )

    @apphub_router.get(
        "/v1/apphub/applications/{application_name}",
        status_code=status.HTTP_200_OK,
    )
    async def get_application_details(
        application_name: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific application.
        
        Args:
            application_name: Name of the application to retrieve details for
            client: Database client
            
        Returns:
            Dictionary containing application details
            
        Raises:
            HTTPException: If there's an error retrieving application details
        """
        try:
            # Initialize AppHub service with environment variables
            apphub_service = AppHubService(
                host=apphub_environment.host,
                username=apphub_environment.username,
                password=apphub_environment.password
            )
            
            # Get application details
            application_details = apphub_service.get_application_details(name=application_name)
            
            return application_details
            
        except Exception as e:
            logger.error(f"Error getting application details from AppHub: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"code": "get_application_details_error", "message": str(e)},
            ) 