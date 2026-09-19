import datetime

import pytest
import pytest_mock
from app.services.data.assets.modules.dao import ModulesDao



def get_sample_module_dump():
     return {
        "user_id": "",
        "project_id": "1",
        "site_id": "1",
        "action_id": "",
        "name": "66d40c80-f057-485a-bcc3-8b9431f3dbcb",
        "description": "Imported as part of CustomPythonWidgetRecipe browse",
        "module_type": "PYTHON",
        "upload_status": "COMPLETED",
        "upload_stats": {
            "percentage": "100%"
        },
        "metadata": None,
        "created_at": datetime.datetime.now(datetime.timezone.utc),
        "module_location": {
            "extension": "PY",
            "path": "/tmp/modules/66d40c80-f057-485a-bcc3-8b9431f3dbcb/join.py"
        },
        "access_mode": "INTERNAL",
        "tags": []
    }

@pytest.mark.asyncio
async def test_get_module_record_by_id_async(mocked_db_async_client , mocked_db_sync_client):
    module_dict = get_sample_module_dump()
    modules_dao = ModulesDao(db_sync_client=mocked_db_sync_client, db_async_client=mocked_db_async_client)
    # Insert the sample module into the mock database
    inserted = await mocked_db_async_client.Hexaind.modules.insert_one(module_dict)
    module_id = str(inserted.inserted_id)

    fetched_module = await modules_dao.get_module_record_by_id_async(module_id)

    # Assertions
    assert fetched_module is not None
    assert fetched_module.name == "66d40c80-f057-485a-bcc3-8b9431f3dbcb"

@pytest.mark.asyncio
async def test_get_module_record_by_id_async_not_found(mocked_db_async_client , mocked_db_sync_client):
    with pytest.raises(KeyError) as exc_info:
        modules_dao = ModulesDao(db_sync_client=mocked_db_sync_client, db_async_client=mocked_db_async_client)
        await modules_dao.get_module_record_by_id_async("65d1b7fe27aafedb3b7cb1e4")
