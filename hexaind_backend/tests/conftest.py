import pathlib
import json
from bson import json_util, ObjectId
import pytest
import pytest_asyncio
import pytest_mock
from mongomock_motor import AsyncMongoMockClient
from mongomock import MongoClient
from fastapi.testclient import TestClient
import asyncio
import os

from app.core.services.jwt_token_utils.jwt_token_utils import getAccessToken
from app.main import app
from app.core.db.db_utils import get_db_async
from app.init_db import (
    generate_system_generated_roles,
    generate_user_and_roles,
    generate_endpoints_features_table,
)


mock_client = MongoClient()
async_mock_client = AsyncMongoMockClient(
    mock_mongo_client=mock_client
)  # Asynchronous client to use same db


@pytest.fixture(scope="session")
def mongo_client():
    return mock_client


@pytest.fixture(scope="session")
async def async_mongo_client():
    try:
        yield async_mock_client
    finally:
        pass


async def override_get_db_async():
    try:
        yield async_mock_client
    finally:
        pass


@pytest.fixture(scope="function")
def mock_db_clients(mocker):
    async def test_mock():
        return async_mock_client

    mocker.patch(
        "app.api.rbac.end_points_v1_access_control.get_db_sync",
        return_value=mock_client,
    )
    mocker.patch(
        "app.api.rbac.end_points_v1_access_control.get_db_async", side_effect=test_mock
    )
    mocker.patch("app.main.get_db_sync", return_value=mock_client)
    # mocker.patch("app.main.get_db_async", side_effect=test_mock)


@pytest.fixture(scope="function")
def app_client(mock_db_clients):
    app.dependency_overrides[get_db_async] = override_get_db_async
    asyncio.run(generate_user_and_roles(async_mock_client))
    asyncio.run(generate_system_generated_roles(async_mock_client))
    asyncio.run(generate_endpoints_features_table(async_mock_client))
    client = TestClient(app)
    try:
        yield client
    finally:
        app.dependency_overrides.clear()


# import json
# from bson.json_util import dumps # Find documents in the collectioncursor = collection.find() # Convert the cursor to a JSON
# users_list = db.users.find({})

# json_data = dumps(users_list)
# print(json_data)


@pytest.fixture(scope="session")
def load_data_to_db(mongo_client):
    db = mongo_client["Hexaind"]
    data_details = {
        "modules": "resources/insert_modules.json",
        "queries": "resources/insert_queries.json",
        "connectors": "resources/insert_connectors.json",
        # "users": "resources/insert_users.json",
    }
    cwd = pathlib.Path(str(__file__))
    for db_collection in data_details:
        file_path = str(cwd.parent.absolute() / data_details[db_collection])
        data = json.loads(open(file_path).read(), object_hook=json_util.object_hook)
        db[db_collection].delete_many({})  # TODO: CHECK IF THIS IS REQUIRED
        db[db_collection].insert_many(data)


@pytest.fixture(scope="function")
def get_valid_server_admin_token():
    email = "databrickadmin@databrick.tech"
    user_id = "65967ecac48951a0928b7dac"
    server_role_value = 1
    return getAccessToken(email, server_role_value, user_id)


@pytest.fixture(scope="session")
def env_setup():
    """Setup environment variables for testing"""
    os.environ['HEXAIND_DATA'] = os.getenv('HEXAIND_DATA', 'hexaind-data')
    os.environ['HEXAIND_HOME'] = os.getenv('HEXAIND_HOME', 'hexaind-home')
    os.environ['HEXAIND_DRIVE'] = os.getenv('HEXAIND_DRIVE', 'hexaind-drive')
