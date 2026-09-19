from datetime import datetime, timezone

import pytest
import pytest_asyncio
from app.services.data.assets.datasets.dao import DatasetsDao
from app.services.data.assets.datasets.schemas import Dataset
from mongomock import MongoClient
from mongomock_motor import AsyncMongoMockClient


@pytest.fixture
def sync_mongo_client():
    return MongoClient()


@pytest.fixture
def async_mongo_client():
    return AsyncMongoMockClient()


@pytest.fixture
def dataset_dao(sync_mongo_client, async_mongo_client):
    return DatasetsDao(db_sync_client=sync_mongo_client, db_async_client=async_mongo_client)


@pytest.fixture
def sample_dataset():
    return Dataset.model_validate({
        "_id": "65e839b8ab81f3032d51e4e7",
        "id": "65e839b8ab81f3032d51e4e7",
        "version": "1.0",
        "user_id": "",
        "project_id": "65e81deb75865234ef3f047a",
        "site_id": "1",
        "action_id": "",
        "name": "bt",
        "description": "bt",
        "dataset_type": "TABULAR",
        "dataset_information": [
            {
                "preview": None,
                "statistics": None,
                "visualize": None,
                "dataset_schema": None
            }
        ],
        "upload_status": "COMPLETED",
        "upload_stats": {
            "percentage": "100%"
        },
        "metadata": {},
        "created_at": "2024-03-06T15:09:04.348Z",
        "dataset_location": [
            {
                "isfolder": False,
                "size": "39169",
                "extension": ".csv",
                "path": "/tmp/hexaind-data/datasets/6fddd49d-b987-4abc-90a3-da12fdbde190.csv",
                "last_modified_by": "",
                "last_modified_at": "2024-03-06T15:09:04.321Z"
            }
        ],
        "access_mode": "EXTERNAL",
        "tags": []
    })


@pytest.fixture
def sync_insert_dataset(dataset_dao, sample_dataset):
    dataset = dataset_dao.db_sync.datasets.insert_one(sample_dataset.model_dump())
    yield dataset.inserted_id
    dataset_dao.db_sync.datasets.delete_one({
        "_id": dataset.inserted_id
    })


@pytest_asyncio.fixture
async def async_insert_dataset(dataset_dao, sample_dataset):
    dataset = await dataset_dao.db_async.datasets.insert_one(sample_dataset.model_dump())
    yield dataset.inserted_id
    await dataset_dao.db_async.datasets.delete_one({
        "_id": dataset.inserted_id
    })
