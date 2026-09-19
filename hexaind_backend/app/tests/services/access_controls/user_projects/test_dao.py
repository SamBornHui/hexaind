import datetime

import pytest
import pytest_mock
import pytest_asyncio
from bson import ObjectId
from mongomock.mongo_client import MongoClient
from mongomock_motor import AsyncMongoMockClient

from app.services.access_controls.user_projects.schemas import UsersProjectsMapping
from app.services.access_controls.user_projects.dao import UsersProjectsMappingsDao


@pytest.fixture
def mocked_async_client():
    return AsyncMongoMockClient()


@pytest.fixture
def mocked_sync_client():
    return MongoClient()


def get_users_projects_mapping(u_id, p_id, r_id):
    return UsersProjectsMapping(
        user_id=u_id,
        project_id=p_id,
        role_id=r_id,
        is_active=True,
        created_at=datetime.datetime.now(datetime.timezone.utc),
        created_by='user',
        last_modified_at=datetime.datetime.now(datetime.timezone.utc),
        last_modified_by='user'
    )


@pytest.mark.asyncio
async def test_insert_users_projects_mapping(mocker, mocked_async_client, mocked_sync_client):
    dao = UsersProjectsMappingsDao(db_async_client=mocked_async_client)
    user_project_mapping = get_users_projects_mapping('1', '2', '3')
    inserted_id = await dao.insert_users_projects_mapping(user_project_mapping)
    assert inserted_id is not None
    assert inserted_id == "1_2"
    user_project_mapping = await dao.get_users_projects_mapping_by_user_id_and_project_id('1', "2")
    assert user_project_mapping.user_id == "1"
    assert user_project_mapping.project_id == "2"
    assert user_project_mapping.role_id == "3"


@pytest.mark.asyncio
async def test_get_mappings_by_user_id(mocker, mocked_async_client, mocked_sync_client):
    dao = UsersProjectsMappingsDao(db_async_client=mocked_async_client)
    user_project_mapping = get_users_projects_mapping('11', '2', '3')
    await dao.insert_users_projects_mapping(user_project_mapping)
    results = await dao.get_users_projects_mapping_by_user_id(user_project_mapping.user_id)
    assert len(results) > 0
    assert results[0].user_id == user_project_mapping.user_id


@pytest.mark.asyncio
async def test_get_mappings_by_project_id(mocker, mocked_async_client, mocked_sync_client):
    dao = UsersProjectsMappingsDao(db_async_client=mocked_async_client)
    project_id=str(ObjectId())
    user_id_1=str(ObjectId())
    user_id_2 = str(ObjectId())
    user_project_mapping = get_users_projects_mapping(user_id_1, project_id, '3')
    await dao.insert_users_projects_mapping(user_project_mapping)
    user_project_mapping = get_users_projects_mapping(user_id_2, project_id, '3')
    await dao.insert_users_projects_mapping(user_project_mapping)
    results = await dao.get_users_projects_mapping_by_project_id(user_project_mapping.project_id, False)
    assert len(results) == 2
    assert results[0].project_id == user_project_mapping.project_id
    assert results[1].project_id == user_project_mapping.project_id


@pytest.mark.asyncio
async def test_get_mappings_by_user_id_project_id(mocker, mocked_async_client, mocked_sync_client):
    dao = UsersProjectsMappingsDao(db_async_client=mocked_async_client)
    user_project_mapping = get_users_projects_mapping('11', '212', '3')
    await dao.insert_users_projects_mapping(user_project_mapping)
    results = await dao.get_users_projects_mapping_by_user_id_and_project_id(user_project_mapping.user_id,
                                                                             user_project_mapping.project_id)
    assert results is not None
    assert results.user_id == user_project_mapping.user_id
    assert results.project_id == user_project_mapping.project_id


@pytest.mark.asyncio
async def test_delete_users_projects_mappings(mocker, mocked_async_client, mocked_sync_client):
    dao = UsersProjectsMappingsDao(db_async_client=mocked_async_client)
    user_project_mapping = get_users_projects_mapping('11', '2', '3')
    await dao.insert_users_projects_mapping(user_project_mapping)
    await dao.delete_users_projects_mappings(user_project_mapping.user_id,
                                                             user_project_mapping.project_id)

