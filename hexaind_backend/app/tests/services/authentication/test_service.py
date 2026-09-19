from datetime import datetime, timezone
import pytest
from unittest.mock import patch

from app.services.admin.authentication.service import AuthenticationService
from app.services.admin.authentication.schemas import (LoginResponse, SSOLoginSchema, AzureTokensSchema, GcpTokensSchema)
from unittest.mock import AsyncMock

from mongomock_motor import AsyncMongoMockClient

def get_sample_user():
    return {
        "name": "",
        "email": "hamza@databrick.tech",
        "created_at": datetime(2024, 3, 1, 13, 30, 59, 350000),
        "updated_at": datetime(2024, 3, 1, 13, 30, 59, 350000),
        "created_by": "databrickadmin@databrick.tech",
        "is_active": 1,
        "is_super_admin": False,
        "is_sso_user": True,
        "login_status": True,
        "last_login_date": datetime(2024, 3, 1, 13, 30, 59, 350000)
        }

@pytest.fixture
def mocked_async_client():
    return AsyncMongoMockClient()

@pytest.mark.asyncio

async def validate_sso_token_and_return_jwt_token(mocked_async_client):

    user_json = get_sample_user()
    
    usr_ins = await mocked_async_client.Hexaind.users.insert_one(user_json)

    auth_serv = AuthenticationService(db_async_client=mocked_async_client)

    # Mock the method using patch
    #with patch.object(auth_serv, 'decode_azure', AsyncMock(return_value='hamza@databrick.tech')):
    with patch.object(auth_serv, '_AuthenticationService__validate_azure_token_and_return_email', AsyncMock(return_value='hamza@databrick.tech')):
        azure_schema = AzureTokensSchema(access_token="DummyAccessToken", raw_token="DummyRawToken")
        sso_schema = SSOLoginSchema(tokens_schema=azure_schema)

        result = await auth_serv.validate_sso_token_and_return_jwt_token(sso_schema)

        check_for_asserts(result)
    
    with patch.object(auth_serv, '_AuthenticationService__validate_gcp_token_and_return_email', AsyncMock(return_value='hamza@databrick.tech')):
        gcp_schema = GcpTokensSchema(gcp_id_token="DummyGCPToken")
        sso_schema = SSOLoginSchema(tokens_schema=gcp_schema)

        result = await auth_serv.validate_sso_token_and_return_jwt_token(sso_schema)
        check_for_asserts(result)
    
def check_for_asserts(result):
    assert isinstance(result, LoginResponse)
    assert result != None
    assert result.access_token != None
    assert result.refresh_token != None
