import pytest
from mongomock.mongo_client import MongoClient
from mongomock_motor import AsyncMongoMockClient


@pytest.fixture
def mocked_db_sync_client():
    return MongoClient()

@pytest.fixture
def mocked_db_async_client(mocked_db_sync_client):
    return AsyncMongoMockClient(mock_mongo_client=mocked_db_sync_client)

