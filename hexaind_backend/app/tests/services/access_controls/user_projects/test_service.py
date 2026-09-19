import pytest
import pytest_mock
import pytest_asyncio

from datetime import datetime, timezone

from bson import ObjectId
from mongomock.mongo_client import MongoClient
from mongomock_motor import AsyncMongoMockClient

from app.services.access_controls.roles.schemas import RolesFeaturesMap
from app.services.access_controls.user_projects.service import UsersProjectsMappingsService
from app.services.access_controls.user_projects.schemas import UsersProjectsMapping, CreateMappingRequest
from app.services.admin.authentication.schemas import User
from app.services.admin.projects.schemas import Project


@pytest.fixture
def mocked_async_client():
    return AsyncMongoMockClient()


@pytest.fixture
def mocked_sync_client():
    return MongoClient()


@pytest.mark.asyncio
async def test_common_dao_methods(mocker, mocked_async_client):
    service = UsersProjectsMappingsService(db_async_client=mocked_async_client)

    user_id = str(ObjectId())
    mapped_user_id = str(ObjectId())
    project_id = str(ObjectId())
    role_id = "role1"

    await service.create_new_mapping(user_id, mapped_user_id, project_id, role_id)

    find_result = await service.get_mapping(mapped_user_id, project_id)
    assert find_result.role_id == role_id

    find_results = await service.get_mappings_by_user_id(mapped_user_id)
    assert len(find_results) == 1
    assert find_results[0].user_id == mapped_user_id
    assert find_results[0].project_id == project_id
    assert find_results[0].role_id == role_id

    find_results[0].id = None
    role_id = "role2"
    await service.update_existing_mapping(user_id=user_id, mapped_user_id=mapped_user_id, project_id=project_id,
                                          role_id=role_id)
    find_results = await service.get_mappings_by_project_id(project_id, False)
    assert len(find_results) == 1
    assert find_results[0].user_id == mapped_user_id
    assert find_results[0].project_id == project_id
    assert find_results[0].role_id == role_id

    await service.delete_user_proj_mappings(mapped_user_id=mapped_user_id, project_id=project_id)


@pytest.mark.asyncio
async def test_update_existing_mappings_for_project(mocker, mocked_async_client):
    service = UsersProjectsMappingsService(db_async_client=mocked_async_client)
    project_id_1 = str(ObjectId())
    user_id_1 = str(ObjectId())
    user_id_0 = str(ObjectId())
    user_id_2 = str(ObjectId())
    user_id_3 = str(ObjectId())
    
    for (p, u, r) in [(project_id_1, user_id_1, 'r1'), (project_id_1, user_id_0, 'r2'), (project_id_1, user_id_2, 'r3'), (project_id_1, user_id_3, 'r6')]:
        await service.create_new_mapping('admin', u, p, r)

    modify_to = [(project_id_1, user_id_1, 'r1'), (project_id_1, user_id_0, 'r8')]
    mappings = []
    for (p, u, r) in modify_to:
        mappings.append(CreateMappingRequest(user_id=u, project_id=p, role_id=r))
    await service.update_existing_mappings_for_project(mappings, "admin2")

    find_results = await service.get_mappings_by_project_id(project_id_1,False)
    assert len(find_results) == 2
    res_dict = {
        (res.project_id, res.user_id, res.role_id): res
        for res in find_results
    }
    result = res_dict[(project_id_1, user_id_1, 'r1')]
    assert result.last_modified_by == 'admin'
    result = res_dict[(project_id_1, user_id_0, 'r8')]
    assert result.last_modified_by == 'admin2'


async def get_test_project_by_id_async(p_id: str):
    return Project(
        id=p_id,
        name=p_id,
        created_at=datetime.now(timezone.utc)
    )


async def get_test_all_roles_features_async(search_term='', page_number=1, page_limit=1000):

    res = [
        RolesFeaturesMap(
            _id="role1",
            name="role1",
            description="",
            created_at=datetime.now(timezone.utc),
            created_by='admin',
            last_modified_at=datetime.now(timezone.utc),
            is_active=True,
            last_modified_by='admin'
        ),
        RolesFeaturesMap(
            _id="role2",
            name="role2",
            description="",
            created_at=datetime.now(timezone.utc),
            created_by='admin',
            last_modified_at=datetime.now(timezone.utc),
            is_active=True,
            last_modified_by='admin'
        )
    ]
    return res, 2


async def get_test_user_by_id(user_id: str):
    return {
        'id': user_id,
        'name': user_id
    }


@pytest.mark.asyncio
async def test_get_mapping_details(mocker, mocked_async_client):
    project_id_1 = str(ObjectId())
    project_id_2 = str(ObjectId())
    user_id_1 = str(ObjectId())
    user_id_2 = str(ObjectId())
    admin = str(ObjectId())
    service = UsersProjectsMappingsService(db_async_client=mocked_async_client)
    for (p, u, r) in [(project_id_1, user_id_1, 'role1'), (project_id_1, user_id_2, 'role2'),
                      (project_id_2, user_id_1, 'role2')]:
        await service.create_new_mapping(admin, u, p, r)

    mocker.patch('app.services.access_controls.user_projects.service.ProjectDao.get_project_by_id_async',
                 side_effect=get_test_project_by_id_async)

    async def temp_side_effect(p_id):
        return []

    async def temp_get_users_dict(some_list):
        sample_user = {
            "email":"email@gmail.com",
            "invited_by_id":str(ObjectId()),
            "updated_at":datetime.now(timezone.utc),
            "status":"Active",
            "server_role_value":4
        }
        return { id: User(name=id, **sample_user) for id in some_list}

    mocker.patch(
        'app.services.access_controls.user_projects.service.UsersProjectsMappingsDao.get_server_role_admins_as_project_admins_for_project',
        side_effect=temp_side_effect)
    mocker.patch(
        'app.services.access_controls.user_projects.service.UsersProjectsMappingsService.get_users_dict',
        side_effect=temp_get_users_dict)

    mocker.patch('app.services.access_controls.user_projects.service.RolesFeaturesMapDao.get_all_roles_features_async',
                 side_effect=get_test_all_roles_features_async)
    mocker.patch('app.services.access_controls.user_projects.service.AuthenticationDao.get_user_by_id',
                 side_effect=get_test_user_by_id)

    results = await service.get_mapping_details_by_project_id(project_id_1)
    assert len(results) == 2
    for result in results:
        assert result.user_name in [user_id_1, user_id_2]
        assert result.role_name in ['role1', 'role2']

    # TODO: LET cant be used in mongomock aggregate so need to reimplement below test assertions.
    # results = await service.get_mapping_details_by_user_id(user_id_1)
    # assert len(results) == 2
    # for result in results:
    #     assert result.project_name in [project_id_1, project_id_2]
    #     assert result.role_name in ['role1', 'role2']
    #
    # results = await service.get_mapping_details_by_user_id(user_id_2)
    # assert len(results) == 1
    # for result in results:
    #     assert result.project_name in [project_id_1]
    #     assert result.role_name in ['role2']


def test_generate_user_project_mapping():
    user_id = "user1"
    project_id = "project1"
    role_id = "role1"
    result = UsersProjectsMappingsService.generate_user_project_mapping(user_id, project_id, role_id)

    assert isinstance(result, UsersProjectsMapping)
    assert result.user_id == user_id
    assert result.project_id == project_id
    assert result.role_id == role_id
    assert result.is_active is True
    # Since `datetime.now(timezone.utc)` will be different every time, we check if it's recent instead of matching exact values
    assert abs((datetime.now(timezone.utc) - result.created_at).total_seconds()) < 5
    assert result.created_by == ''
