import pytest
from app.services.access_controls.roles.dao import RolesFeaturesMap
from app.services.access_controls.roles.schemas import RoleType
import datetime

from app.tests.services.access_controls.roles.conftest import sample_role_feature


@pytest.mark.asyncio
async def test_insert_roles_features(roles_features_dao):

    role_features_map = RolesFeaturesMap(
        name="Admin",
        description="Administrator role",
        role_type=RoleType.PROJECT_ROLE,
        created_at=datetime.datetime.now(datetime.timezone.utc),
        created_by="tester",
        is_active=True,
        last_modified_at=datetime.datetime.now(datetime.timezone.utc),
        last_modified_by="tester",
        source_type="SYSTEM_GENERATED_ROLE"
    )

    result_id = await roles_features_dao.insert_roles_features(role_features_map)
    assert isinstance(result_id, str)


@pytest.mark.asyncio
async def test_update_roles_features(roles_features_dao, async_mongo_client):

    obj = sample_role_feature()
    res = await async_mongo_client.Hexaind.roles_features_mapping.insert_one(obj.model_dump())
    obj.id = str(res.inserted_id)
    obj.name = "adfasdf"
    await roles_features_dao.update_roles_features(obj)


@pytest.mark.asyncio
async def test_get_roles_features(roles_features_dao, async_mongo_client):

    obj = sample_role_feature()
    res = await async_mongo_client.Hexaind.roles_features_mapping.insert_one(obj.model_dump())
    obj.id = str(res.inserted_id)
    # obj.name = "adfasdf"
    res = await roles_features_dao.get_role_feature_map_id_async(obj.id)
    assert res is not None
    assert res.name == obj.name

    res = await roles_features_dao.get_role_by_name_async(obj.name)
    assert res is not None
    assert res.name == obj.name

    res,_ = await roles_features_dao.get_all_roles_features_async(obj.name,page_number=1,page_limit=100)
    assert len(res) == 1
    assert res[0].name == obj.name
