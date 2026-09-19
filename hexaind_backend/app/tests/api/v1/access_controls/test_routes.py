from typing import Mapping

from bson import ObjectId
from fastapi import Request, status
import pytest
import pytest_mock
import pytest_asyncio
from app.services.access_controls.roles.schemas import RoleFeaturesMapRequestName, RolesFeaturesMapCreateRequest, RolesFeaturesMapCreateResponse, RolesFeaturesMapGetRequest, RolesFeaturesMapGetResponse, RolesFeaturesMap
from app.core.services.jwt_token_utils.jwt_token_utils import JWTBearer
from app.api.endpoints.v1.access_controls.routes import UsersAccessControlDetailsRouter
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

from app.services.access_controls.user_projects.schemas import CreateMappingRequest, CreateMappingRequestMultiple, DeleteUserProjMappingRequest, GetRolesBasedOnIdRequest, GetRolesBasedOnIdResponse, UserProjectsMappingWithDetails, UsersAccessControlDetailsBaseResponse
from app.services.admin.authentication.schemas import User
from app.tests.api.v1.access_controls.conftest import sample_role_feature


async def do_nothing(user_id: str,
                     roles_features_map_data: RolesFeaturesMapCreateRequest):
    return "mocked_role_id"

@pytest.mark.asyncio
async def test_create_roles_features_map_success(mocker, async_mongo_client):
    # Mock Request
    mock_request = mocker.Mock(spec=Request)

    # Mock RolesFeaturesMapCreateRequest
    roles_features_map_data = RolesFeaturesMapCreateRequest(
        # Populate with the required fields and values
        version='1.0',
        name='abcd',
        description="",
        role_type='PROJECT_ROLE',
        source_type='SYSTEM_GENERATED_ROLE'
    )

    # Mock RolesFeaturesMapService.insert_roles_features_map
    mocker.patch(
        'app.services.access_controls.roles.service.RolesFeaturesMapService.insert_roles_features_map',
        side_effect=do_nothing)
    # mock_service_method.return_value = "mocked_role_id"

    # Mock JWT Verification
    mock_jwt_token = mocker.patch(
        'app.api.endpoints.v1.access_controls.routes.decodeJWT')
    mock_jwt_token.return_value = {
        "email": "admin@office.com", "user_id": "new_user_id"}
    
    response = await UsersAccessControlDetailsRouter.create_roles_features_map(
        site_id='site_id',
        roles_features_map_data=roles_features_map_data,
        db_async_client=AsyncIOMotorClient(),
        token=JWTBearer()
    )

    # Assertions
    assert isinstance(response, RolesFeaturesMapCreateResponse)
    assert response.succeeded is True
    assert response.message == "Creation Successful"
    assert response.role_id == "mocked_role_id"


@pytest.mark.asyncio
async def test_get_roles_features_map_id_success(mocker, async_mongo_client):
    # Mock dependencies
    mocker.patch('app.api.endpoints.v1.access_controls.routes.decodeJWT', return_value={
                 "email": "admin@office.com", "user_id": "new_user_id"})
    mock_service_method = mocker.patch('app.services.access_controls.roles.service.RolesFeaturesMapService.get_roles_features_map_by_id')
    obj = sample_role_feature()
    res = await async_mongo_client.Hexaind.roles_features_mapping.insert_one(obj.model_dump())
    obj.id = str(res.inserted_id)
    # Adjust with expected data structure
    mock_service_method.return_value = RolesFeaturesMap(
        name='abdhs',
        description='sjhfg',
        role_type='PROJECT_ROLE',
        source_type="SYSTEM_GENERATED_ROLE",
        last_modified_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        last_modified_by='djkf',
        created_by='kbdfk',
        is_active=True
    )

    # Mock request data
    config = RolesFeaturesMapGetRequest(roles_id=obj.id)

    # Execute the route function
    response = await UsersAccessControlDetailsRouter.get_roles_features_map_id(
        site_id="site_id",
        config=config,
        db_async_client=mocker.MagicMock(),
        token="mocked_token"
    )

    # Assertions
    assert response.succeeded is True
    assert response.message == "Fetch successfull"


@pytest.mark.asyncio
async def test_get_roles_features_map_name_success(mocker, async_mongo_client):
    mocker.patch('app.api.endpoints.v1.access_controls.routes.decodeJWT', return_value={
                 "email": "admin@office.com", "user_id": "new_user_id"})
    mock_service_method = mocker.patch(
        'app.services.access_controls.roles.service.RolesFeaturesMapService.get_roles_features_map_by_name')
    # Adjust with expected data structure
    obj = sample_role_feature()
    res = await async_mongo_client.Hexaind.roles_features_mapping.insert_one(obj.model_dump())
    obj.id = str(res.inserted_id)

    mock_service_method.return_value = RolesFeaturesMap(
        name='abdhs',
        description='sjhfg',
        role_type='PROJECT_ROLE',
        source_type="SYSTEM_GENERATED_ROLE",
        last_modified_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        last_modified_by='djkf',
        created_by='kbdfk',
        is_active=True
    )

    # Mock request data
    config = RoleFeaturesMapRequestName(role_name='abdhs')

    # Execute the route function
    response = await UsersAccessControlDetailsRouter.get_roles_features_map_name(
        site_id="site_id",
        config=config,
        db_async_client=async_mongo_client,
        token="mocked_token"
    )
    # Assertions
    assert response.succeeded is True
    assert response.message == "Fetch successfull"


@pytest.mark.asyncio
async def test_get_all_roles_success(mocker, async_mongo_client):
    mocker.patch('app.api.endpoints.v1.access_controls.routes.decodeJWT', return_value={
                 "email": "admin@office.com", "user_id": "new_user_id"})
    mock_service_method = mocker.patch(
        'app.services.access_controls.roles.service.RolesFeaturesMapService.fetch_all_roles_features_maps')
    # Adjust based on expected return
    mock_service_method.return_value = ([RolesFeaturesMap(
        _id= 'wjkdbv ndsm,',
        name='abdhs',
        description='sjhfg',
        role_type='PROJECT_ROLE',
        source_type="SYSTEM_GENERATED_ROLE",
        last_modified_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        last_modified_by='djkf',
        created_by='kbdfk',
        is_active=True
    ),
    RolesFeaturesMap(
        _id='jkeehfnamaslnv',
        name='abdhs',
        description='sjhfg',
        role_type='PROJECT_ROLE',
        source_type="SYSTEM_GENERATED_ROLE",
        last_modified_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        last_modified_by='djkf',
        created_by='kbdfk',
        is_active=True
    )],2)

    # Execute the route function
    response = await UsersAccessControlDetailsRouter.get_all_roles(
        site_id="site_id",
        db_async_client=async_mongo_client,
        token="mocked_token"
    )

    # Assertions
    assert response.succeeded is True
    assert response.message == "Fetch all successfull"
    # or adjust based on expected roles count
    assert len(response.results) == 2




@pytest.mark.asyncio
async def test_update_user_mappings_for_project_success(mocker, async_mongo_client):
    # Mock JWT token verification
    mocker.patch(
        'app.api.endpoints.v1.access_controls.routes.decodeJWT',
        return_value={"email": "admin@office.com", "user_id": "requesting_user_id"})

    # Mock the service method for updating mappings
    mock_service_method = mocker.patch(
        'app.services.access_controls.user_projects.service.UsersProjectsMappingsService.update_existing_mappings_for_project')
    # Assuming this method does not return a value
    mock_service_method.return_value = None

    # Prepare the request payload with multiple mappings
    create_mapping_request_multiple = CreateMappingRequestMultiple(
        mappings=[
            CreateMappingRequest(user_id="user1", project_id="project1", role_id="role1"),
            CreateMappingRequest(user_id="user2", project_id="project1", role_id="role2")
        ]
    )

    # Execute the route function
    response_model = await UsersAccessControlDetailsRouter.update_user_mappings_for_project(
        site_id="test_site_id",
        create_mapping_request=create_mapping_request_multiple,
        db_async_client=async_mongo_client,
        token="mocked_token"
    )

    # Assertions
    assert response_model.succeeded is True
    assert response_model.message == "Create mappings successfully"

    # Verify that the service method was called with expected parameters
    args, kwargs = mock_service_method.call_args
    assert kwargs["user_mappings"] == create_mapping_request_multiple.mappings
    assert kwargs["user_id"] == "requesting_user_id"


@pytest.mark.fixme
@pytest.mark.asyncio
async def test_modify_existing_user_project_mapping_success(mocker, async_mongo_client):
    # Mock JWT token verification
    mocker.patch(
        'app.api.endpoints.v1.access_controls.routes.decodeJWT',
        return_value={"email": "admin@office.com", "user_id": "requesting_user_id"})

    # Mock the service method called within the route
    mock_service_method = mocker.patch(
        'app.services.access_controls.user_projects.service.UsersProjectsMappingsService.update_existing_mapping')
    mock_service_method.return_value = "mocked_mapping_id"
    sample_user = {
        "email": "email@gmail.com",
        "invited_by_id": str(ObjectId()),
        "updated_at": datetime.now(timezone.utc),
        "status": "Active",
        "server_role_value": 4
    }
    mocker.patch(
        'app.api.endpoints.v1.service.access_controls.routes.AuthenticationService',
        return_value=User(name=id, **sample_user))

    # Prepare the request payload
    create_mapping_request = CreateMappingRequest(
        user_id="target_user_id",
        project_id="target_project_id",
        role_id="target_role_id"
    )

    # Execute the route function
    response_model = await UsersAccessControlDetailsRouter.modify_existing_user_project_mapping(
        site_id="test_site_id",
        create_mapping_request=create_mapping_request,
        db_async_client=async_mongo_client,
        token="mocked_token"
    )

    # Assertions
    assert response_model.mapping_id == "mocked_mapping_id"
    assert response_model.succeeded is True
    assert response_model.message == "Updated mapping successfully"


@pytest.mark.asyncio
async def test_get_mapping_details_by_project_id_success(mocker, async_mongo_client):
    # Mock JWT token verification
    mocker.patch(
        'app.api.endpoints.v1.access_controls.routes.decodeJWT',
        return_value={"email": "admin@office.com", "user_id": "requesting_user_id"})

    # Mock the service method for fetching mapping details
    mock_service_method_with_details = mocker.patch(
        'app.services.access_controls.user_projects.service.UsersProjectsMappingsService.get_mapping_details_by_project_id')
    mock_service_method_with_details.return_value = [
        UserProjectsMappingWithDetails(
            user_id="12345",
            project_id="54321",
            role_id="67890",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            created_by="admin",
            last_modified_at=datetime.now(timezone.utc),
            last_modified_by="admin_update",
            user_name="John Doe",
            project_name="Project X",
            role_name="Developer"
        )
    ]

    # Mock the service method for fetching mappings without details
    mock_service_method_without_details = mocker.patch(
        'app.services.access_controls.user_projects.service.UsersProjectsMappingsService.get_mappings_by_project_id')
    mock_service_method_without_details.return_value = [
        UserProjectsMappingWithDetails(
            user_id="12345",
            project_id="54321",
            role_id="67890",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            created_by="admin",
            last_modified_at=datetime.now(timezone.utc),
            last_modified_by="admin_update",
            user_name="John Doe",
            project_name="Project X",
            role_name="Developer"
        )
    ]

    # Prepare the request payloads
    request_with_details = GetRolesBasedOnIdRequest(
        id="project1", get_details=True)
    request_without_details = GetRolesBasedOnIdRequest(
        id="project1", get_details=False)

    # Execute the route function for the scenario with get_details=True
    response_with_details = await UsersAccessControlDetailsRouter.get_mapping_details_by_project_id(
        site_id="test_site_id",
        request=request_with_details,
        db_async_client=async_mongo_client,
        token="mocked_token"
    )

    # Assertions for get_details=True scenario
    assert response_with_details.succeeded is True
    assert response_with_details.message == "Mappings fetched successfully based on project id."
    assert len(response_with_details.mappings) > 0

    # Execute the route function for the scenario without get_details
    response_without_details = await UsersAccessControlDetailsRouter.get_mapping_details_by_project_id(
        site_id="test_site_id",
        request=request_without_details,
        db_async_client=async_mongo_client,
        token="mocked_token"
    )

    # Assertions for get_details=False scenario
    assert response_without_details.succeeded is True
    assert response_without_details.message == "Mappings fetched successfully based on project id."
    assert len(response_without_details.mappings) > 0

    # Verifying the correct service methods were called
    mock_service_method_with_details.assert_called_once_with("project1")
    mock_service_method_without_details.assert_called_once_with("project1")


@pytest.mark.asyncio
async def test_get_projects_based_on_user_id_success(mocker, async_mongo_client):
    # Mock JWT token verification
    mock_decode_jwt = mocker.patch(
        'app.api.endpoints.v1.access_controls.routes.decodeJWT',
        return_value={"email": "admin@office.com", "user_id": "requesting_user_id"})

    # Mock the service methods
    mock_get_mapping_details_by_user_id = mocker.patch(
        'app.services.access_controls.user_projects.service.UsersProjectsMappingsService.get_mapping_details_by_user_id')
    mock_get_mapping_details_by_user_id.return_value = [
        UserProjectsMappingWithDetails(
            user_id="12345",
            project_id="54321",
            role_id="67890",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            created_by="admin",
            last_modified_at=datetime.now(timezone.utc),
            last_modified_by="admin_update",
            user_name="John Doe",
            project_name="Project X",
            role_name="Developer"
        )
    ]
    mock_get_mappings_by_user_id = mocker.patch(
        'app.services.access_controls.user_projects.service.UsersProjectsMappingsService.get_mappings_by_user_id')
    mock_get_mappings_by_user_id.return_value = [
        UserProjectsMappingWithDetails(
            user_id="12345",
            project_id="54321",
            role_id="67890",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            created_by="admin",
            last_modified_at=datetime.now(timezone.utc),
            last_modified_by="admin_update",
            user_name="John Doe",
            project_name="Project X",
            role_name="Developer"
        )
    ]

    # Prepare the request payload
    request_with_details = GetRolesBasedOnIdRequest(
        id="user1", get_details=True)
    request_without_details = GetRolesBasedOnIdRequest(
        id="user2", get_details=False)

    # Execute the route function for both scenarios
    response_with_details = await UsersAccessControlDetailsRouter.get_projects_based_on_user_id(
        site_id="test_site_id",
        request=request_with_details,
        db_async_client=mocker.MagicMock(spec=AsyncIOMotorClient),
        token="mocked_token"
    )

    response_without_details = await UsersAccessControlDetailsRouter.get_projects_based_on_user_id(
        site_id="test_site_id",
        request=request_without_details,
        db_async_client=mocker.MagicMock(spec=AsyncIOMotorClient),
        token="mocked_token"
    )

    # Assertions for get_details=True scenario
    assert response_with_details.succeeded is True
    assert response_with_details.message == "Mappings fetched successfully based on user id."
    assert len(response_with_details.mappings) > 0

    # Assertions for get_details=False scenario
    assert response_without_details.succeeded is True
    assert response_without_details.message == "Mappings fetched successfully based on user id."
    assert len(response_without_details.mappings) > 0


@pytest.mark.asyncio
async def test_delete_user_proj_map_success(mocker, async_mongo_client):
    # Mock JWT token verification
    mocker.patch(
        'app.api.endpoints.v1.access_controls.routes.decodeJWT',
        return_value={"email": "admin@office.com", "user_id": "requesting_user_id"})

    # Mock the service method for deleting mappings
    mock_service_method = mocker.patch(
        'app.services.access_controls.user_projects.service.UsersProjectsMappingsService.delete_user_proj_mappings')
    mock_service_method.return_value = 2  # Assume 2 mappings were deleted

    # Prepare the request payload
    delete_request = DeleteUserProjMappingRequest(
        user_id="target_user_id",
        project_id="target_project_id"
    )

    # Execute the route function
    response_model = await UsersAccessControlDetailsRouter.delete_user_proj_map(
        site_id="test_site_id",
        config=delete_request,
        db_async_client=async_mongo_client,
        token="mocked_token"
    )

    # Assertions
    assert response_model.succeeded is True
    assert response_model.message == "Deleted all the matching mappings. delete count: 2"
