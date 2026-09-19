import pytest
from app.services.access_controls.roles.schemas import RoleType, RolesFeaturesMapCreateRequest, RoleCreationType

from app.tests.services.access_controls.roles.conftest import sample_role_feature


@pytest.mark.asyncio
async def test_insert_roles_features(roles_features_service):

    role_features_map = RolesFeaturesMapCreateRequest(
        name="Admin",
        description="Administrator role",
        role_type=RoleType.PROJECT_ROLE,
        source_type=RoleCreationType.SYSTEM_GENERATED_ROLE
    )

    result_id = await roles_features_service.insert_roles_features_map(user_id="", roles_features_map_data=role_features_map)
    assert isinstance(result_id, str)


@pytest.mark.asyncio
async def test_get_roles_features(roles_features_service, async_mongo_client):

    obj = sample_role_feature()
    res = await async_mongo_client.Hexaind.roles_features_mapping.insert_one(obj.model_dump())
    obj.id = str(res.inserted_id)
    res = await roles_features_service.get_roles_features_map_by_id(obj.id)
    assert res is not None
    assert res.name == obj.name

    res = await roles_features_service.get_roles_features_map_by_name(obj.name)
    assert res is not None
    assert res.name == obj.name

    res, _ = await roles_features_service.fetch_all_roles_features_maps(obj.name, page_number=1, page_limit=100)
    assert len(res) == 1
    assert res[0].name == obj.name
