import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from typing import Dict, List, Any

from app.main import app
from app.services.apphub.services.apphub_service import AppInfo


@pytest.fixture
def test_client():
    """Fixture providing a FastAPI TestClient."""
    return TestClient(app)


def test_get_applications_integration(test_client, mock_apphub_service, mock_app_info_list):
    """Integration test for GET /v1/apphub/applications endpoint."""
    # Patch the AppHubService to return mock data
    with patch('app.api.endpoints.v1.apphub.apis.routes.AppHubService', return_value=mock_apphub_service):
        # Make the request to the endpoint
        response = test_client.get("/v1/apphub/applications")
        
        # Assertions
        assert response.status_code == 200
        
        # Parse response data
        response_data = response.json()
        assert len(response_data) == len(mock_app_info_list)
        
        # Verify each application's data
        for i, app_data in enumerate(response_data):
            assert app_data["name"] == mock_app_info_list[i].name
            assert app_data["url"] == mock_app_info_list[i].url
            assert app_data["health_status"] == mock_app_info_list[i].health_status


def test_get_application_details_integration(test_client, mock_apphub_service, mock_app_details):
    """Integration test for GET /v1/apphub/applications/{application_name} endpoint."""
    # Patch the AppHubService to return mock data
    with patch('app.api.endpoints.v1.apphub.apis.routes.AppHubService', return_value=mock_apphub_service):
        # Make the request to the endpoint
        response = test_client.get("/v1/apphub/applications/test-app")
        
        # Assertions
        assert response.status_code == 200
        
        # Parse response data
        response_data = response.json()
        
        # Verify application details
        assert response_data["name"] == mock_app_details["name"]
        assert response_data["health_status"] == mock_app_details["health_status"]
        assert len(response_data["resources"]) == len(mock_app_details["resources"])
        
        # Verify resource details
        assert response_data["resources"][0]["kind"] == mock_app_details["resources"][0]["kind"]
        assert response_data["resources"][0]["name"] == mock_app_details["resources"][0]["name"]
        assert response_data["resources"][0]["health_status"] == mock_app_details["resources"][0]["health_status"]


def test_get_applications_error_handling(test_client):
    """Integration test for error handling in GET /v1/apphub/applications endpoint."""
    # Mock AppHubService to raise an exception
    mock_service = patch('app.api.endpoints.v1.apphub.apis.routes.AppHubService')
    mock_instance = mock_service.start().return_value
    mock_instance.get_apps_list.side_effect = Exception("Connection error")
    
    try:
        # Make the request to the endpoint
        response = test_client.get("/v1/apphub/applications")
        
        # Assertions
        assert response.status_code == 500
        
        # Parse response data
        response_data = response.json()
        assert response_data["detail"]["code"] == "get_applications_error"
        assert "Connection error" in response_data["detail"]["message"]
    finally:
        mock_service.stop()


def test_get_application_details_error_handling(test_client):
    """Integration test for error handling in GET /v1/apphub/applications/{application_name} endpoint."""
    # Mock AppHubService to raise an exception
    mock_service = patch('app.api.endpoints.v1.apphub.apis.routes.AppHubService')
    mock_instance = mock_service.start().return_value
    mock_instance.get_application_details.side_effect = Exception("Application not found")
    
    try:
        # Make the request to the endpoint
        response = test_client.get("/v1/apphub/applications/non-existent-app")
        
        # Assertions
        assert response.status_code == 500
        
        # Parse response data
        response_data = response.json()
        assert response_data["detail"]["code"] == "get_application_details_error"
        assert "Application not found" in response_data["detail"]["message"]
    finally:
        mock_service.stop()


def test_get_applications_invalid_auth(test_client):
    """Integration test for authentication failure in GET /v1/apphub/applications endpoint."""
    # Mock AppHubService login to raise an exception
    mock_service = patch('app.api.endpoints.v1.apphub.apis.routes.AppHubService')
    mock_instance = mock_service.start().return_value
    mock_instance.get_apps_list.side_effect = Exception("Authentication failed")
    
    try:
        # Make the request to the endpoint
        response = test_client.get("/v1/apphub/applications")
        
        # Assertions
        assert response.status_code == 500
        
        # Parse response data
        response_data = response.json()
        assert response_data["detail"]["code"] == "get_applications_error"
        assert "Authentication failed" in response_data["detail"]["message"]
    finally:
        mock_service.stop() 