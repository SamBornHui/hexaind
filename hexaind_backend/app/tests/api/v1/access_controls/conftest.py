from app.services.access_controls.roles.dao import RolesFeaturesMapDao, RolesFeaturesMap
from datetime import datetime, timezone
import pytest
from mongomock_motor import AsyncMongoMockClient


@pytest.fixture
def async_mongo_client():
    return AsyncMongoMockClient()

def sample_role_feature():
    return RolesFeaturesMap.model_validate({
        "version": "1.0",
        "name": "Full Member",
        "description": "User with read, write, update, delete project permissions",
        "role_type": "PROJECT_ROLE",
        "features": {
            "assets": {
                "datasets": {
                    "create": True,
                    "read": True,
                    "update": True,
                    "delete": True
                },
                "ml_models": {
                    "create": True,
                    "read": True,
                    "update": True,
                    "delete": True
                },
                "workflows": {
                    "create": True,
                    "read": True,
                    "update": True,
                    "delete": True,
                    "execute": True
                },
                "recipes": {
                    "create": True,
                    "read": True,
                    "update": True,
                    "delete": True,
                    "execute": True
                },
                "connectors": {
                    "create": True,
                    "read": True,
                    "update": True,
                    "delete": True
                }
            },
            "tools": {
                "jupyter": {
                    "execute": True
                },
                "dsg_tool": {
                    "execute": True
                }
            },
            "resources": {
                "jobs": {
                    "read": True
                },
                "help_support": {
                    "read": True
                }
            },
            "manage_project_users": {
                "add": False,
                "read": False,
                "modify": False,
                "delete": False
            }
        },
        "created_at": datetime.now(timezone.utc),
        "created_by": "65967ecac48951a0928b7dac",
        "is_active": True,
        "last_modified_at": datetime.now(timezone.utc),
        "last_modified_by": "65967ecac48951a0928b7dac",
        "source_type": "SYSTEM_GENERATED_ROLE"
    })
