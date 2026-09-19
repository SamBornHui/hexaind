import pytest
from unittest.mock import patch
from typing import List, Dict, Any

from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient

from app.api.endpoints.v1.apphub.apis.routes import AppHubRouter
from app.services.apphub.services.apphub_service import AppInfo


@pytest.mark.asyncio
async def test_get_applications_success(mocker, mock_apphub_service, mock_app_info_list):
    """Test successful retrieval of applications."""
    # Mock the AsyncIOMotorClient
    mock_client = mocker.Mock(spec=AsyncIOMotorClient)
    
    # Patch the AppHubService constructor
    with patch('app.api.endpoints.v1.apphub.apis.routes.AppHubService', return_value=mock_apphub_service):
        # Call the endpoint
        result = await AppHubRouter.get_applications(client=mock_client)
        
        # Assertions
        assert len(result) == len(mock_app_info_list)
        for i, app_info in enumerate(result):
            assert app_info.name == mock_app_info_list[i].name
            assert app_info.url == mock_app_info_list[i].url
            assert app_info.health_status == mock_app_info_list[i].health_status
        
        # Verify AppHubService was initialized correctly
        mock_apphub_service.get_apps_list.assert_called_once()


@pytest.mark.asyncio
async def test_get_applications_exception(mocker):
    """Test error handling when retrieving applications fails."""
    # Mock the AsyncIOMotorClient
    mock_client = mocker.Mock(spec=AsyncIOMotorClient)
    
    # Mock the AppHubService
    mock_apphub_service = mocker.Mock()
    mock_apphub_service.get_apps_list.side_effect = Exception("Connection error")
    
    # Patch the AppHubService constructor
    with patch('app.api.endpoints.v1.apphub.apis.routes.AppHubService', return_value=mock_apphub_service):
        # Call the endpoint and expect an exception
        with pytest.raises(HTTPException) as exc_info:
            await AppHubRouter.get_applications(client=mock_client)
        
        # Assertions
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail["code"] == "get_applications_error"
        assert "Connection error" in exc_info.value.detail["message"]


@pytest.mark.asyncio
async def test_get_application_details_success(mocker, mock_apphub_service, mock_app_details):
    """Test successful retrieval of application details."""
    # Mock the AsyncIOMotorClient
    mock_client = mocker.Mock(spec=AsyncIOMotorClient)
    
    # Patch the AppHubService constructor
    with patch('app.api.endpoints.v1.apphub.apis.routes.AppHubService', return_value=mock_apphub_service):
        # Call the endpoint
        result = await AppHubRouter.get_application_details(
            application_name="test-app",
            client=mock_client
        )
        
        # Assertions
        assert result == mock_app_details
        assert result["name"] == mock_app_details["name"]
        assert result["health_status"] == mock_app_details["health_status"]
        assert len(result["resources"]) == len(mock_app_details["resources"])
        
        # Verify AppHubService was initialized correctly
        mock_apphub_service.get_application_details.assert_called_once_with(name="test-app")


@pytest.mark.asyncio
async def test_get_application_details_exception(mocker):
    """Test error handling when retrieving application details fails."""
    # Mock the AsyncIOMotorClient
    mock_client = mocker.Mock(spec=AsyncIOMotorClient)
    
    # Mock the AppHubService
    mock_apphub_service = mocker.Mock()
    mock_apphub_service.get_application_details.side_effect = Exception("Application not found")
    
    # Patch the AppHubService constructor
    with patch('app.api.endpoints.v1.apphub.apis.routes.AppHubService', return_value=mock_apphub_service):
        # Call the endpoint and expect an exception
        with pytest.raises(HTTPException) as exc_info:
            await AppHubRouter.get_application_details(
                application_name="non-existent-app",
                client=mock_client
            )
        
        # Assertions
        assert exc_info.value.status_code == 500
        assert exc_info.value.detail["code"] == "get_application_details_error"
        assert "Application not found" in exc_info.value.detail["message"] 