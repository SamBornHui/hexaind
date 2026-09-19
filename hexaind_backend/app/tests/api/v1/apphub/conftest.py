import pytest
from unittest.mock import MagicMock, patch
from typing import List

from app.services.apphub.services.apphub_service import AppInfo


@pytest.fixture
def mock_app_info_list() -> List[AppInfo]:
    """Fixture providing a list of mock AppInfo objects."""
    return [
        AppInfo(name="app1", url="http://example.com/app1", health_status="Healthy"),
        AppInfo(name="app2", url="http://example.com/app2", health_status="Degraded"),
        AppInfo(name="app3", url="http://example.com/app3", health_status="Progressing")
    ]


@pytest.fixture
def mock_app_details() -> dict:
    """Fixture providing mock application details."""
    return {
        "name": "test-app",
        "namespace": "default",
        "project": "default",
        "sync_status": "Synced",
        "health_status": "Healthy",
        "repo": "https://github.com/example/repo",
        "path": "path/to/app",
        "target_revision": "main",
        "destination": {
            "server": "https://kubernetes.default.svc",
            "namespace": "default"
        },
        "created_at": "2023-01-01T00:00:00Z",
        "resources": [
            {
                "kind": "Deployment",
                "name": "test-deployment",
                "namespace": "default",
                "status": "Synced",
                "health_status": "Healthy"
            }
        ]
    }


@pytest.fixture
def mock_apphub_service(mock_app_info_list, mock_app_details):
    """Fixture providing a mock AppHubService."""
    mock_service = MagicMock()
    mock_service.get_apps_list.return_value = mock_app_info_list
    mock_service.get_application_details.return_value = mock_app_details
    
    return mock_service 