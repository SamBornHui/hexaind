import pytest
from bson.objectid import ObjectId
from app.services.data.assets.datasets.dao import DatasetsDao, AccessMode, DatasetDeleteType


@pytest.mark.fixme
@pytest.mark.asyncio
async def test_update_dataset_name_success(dataset_dao, async_insert_dataset):
    # Execute
    result = await dataset_dao.update_dataset_name_async(async_insert_dataset, 'New Name', 'user2')

    # Verify
    updated_dataset = await dataset_dao.db_async.datasets.find_one(
        {'_id': async_insert_dataset})
    assert result is True
    assert updated_dataset['name'] == 'New Name'
    assert updated_dataset['dataset_location'][0]['last_modified_by'] == 'user2'


@pytest.mark.asyncio
async def test_update_dataset_name_failure(dataset_dao):
    # Attempt to update a non-existing dataset
    result = await dataset_dao.update_dataset_name_async('65eaa3a86325614a545df48e', 'New Name', 'user2')

    # Verify
    assert result is False



@pytest.mark.fixme
@pytest.mark.asyncio
async def test_delete_dataset_record_async_soft(dataset_dao, async_insert_dataset):
    try:
        await dataset_dao.delete_dataset_record_async(str(async_insert_dataset), DatasetDeleteType.SOFT)
        dataset = await dataset_dao.get_dataset_by_id_async(str(async_insert_dataset))
        assert dataset.access_mode == 'INTERNAL'
    except Exception as e:
        pytest.fail(f"Unexpected exception raised: {e}")
