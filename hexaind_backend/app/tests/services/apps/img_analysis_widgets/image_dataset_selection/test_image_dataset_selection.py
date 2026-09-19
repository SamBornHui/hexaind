from app.services.data.assets.image_datasets.schemas import ImagesDatasetResponse
import pytest
from pymongo import MongoClient
from app.services.apps.image_analysis.schema import *
from app.core.dao.dao_base import get_db_async,get_db_sync
from unittest.mock import AsyncMock, patch
from app.services.data.assets.image_datasets.service import ImageDatasetsService
def get_project_id():
    client  = get_db_sync()
    db = client['Hexaind']["datasets"]
    dataset_doc = db.find_one({"dataset_type": "IMAGE_DATASET"})
    project_id  = dataset_doc['project_id']
    return project_id
@pytest.fixture
def image_datasets_service():
    client = get_db_async()
    
    return ImageDatasetsService( db_async_client= client)
def test_image_datasets_service_init(image_datasets_service):
    assert image_datasets_service is not None
@pytest.mark.asyncio
@pytest.mark.fixme
async def test_dataset_selection(image_datasets_service):
    project_id = get_project_id()
    image_datasets = await image_datasets_service.get_image_datasets(project_id)
    results = ImagesDatasetResponse(image_datasets=image_datasets)
    assert results is not None