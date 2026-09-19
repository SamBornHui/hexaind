from pathlib import Path

import pytest
import pytest_mock
import pytest_asyncio
from mongomock.mongo_client import MongoClient
from mongomock_motor import AsyncMongoMockClient

from app.services.data.datasets_conversion.schemas import DatasetsConversionType, DatasetsConversionFromConfig
from app.utils.dataset_utils import generate_dataset_object

from app.services.data.datasets_conversion.service import DatasetsConversionsService, DatasetsConversionRequest


@pytest.fixture
def mocked_async_client():
    return AsyncMongoMockClient()


@pytest.fixture
def mocked_sync_client():
    return MongoClient()


@pytest.fixture
def datasets_conversion_request():
    request = DatasetsConversionRequest(conversion_type=DatasetsConversionType.TABULAR_PARQUET_TO_CSV,
                                        from_config=DatasetsConversionFromConfig(dataset_id='test_dataset_id'))
    return request


async def mock_get_by_id(x):
    penguin_csv_file_path = Path(__file__).parent.parent.parent.parent / "resources" / "penguins.parquet"
    return generate_dataset_object(str(penguin_csv_file_path))


async def mock_insert_to_db(x):
    return "inserted_id"


@pytest.mark.asyncio
@pytest.mark.fixme
async def test_convert_dataset(mocker, mocked_async_client, mocked_sync_client, datasets_conversion_request):
    service = DatasetsConversionsService(db_sync_client=mocked_sync_client, db_async_client=mocked_async_client)
    penguin_csv_file_path = Path(__file__).parent.parent.parent.parent / "resources" / "penguins.parquet"
    dataset = generate_dataset_object(str(penguin_csv_file_path))

    mocker.patch("app.services.data.datasets_conversion.service.DatasetsDao.get_dataset_by_id_async",
                 side_effect=mock_get_by_id)
    mocker.patch("app.services.data.datasets_conversion.service.DatasetsDao.insert_dataset_record_async",
                 side_effect=mock_insert_to_db)
    mocker.patch("app.services.data.datasets_conversion.helper.TabularParquetToTabularCSV.convert",
                 return_value=dataset)
    await service.convert_dataset(datasets_conversion_request, user_id='test_user_id')


