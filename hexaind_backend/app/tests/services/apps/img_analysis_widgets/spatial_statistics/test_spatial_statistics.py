import pytest
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient

from app.services.apps.image_analysis.service import ImageAnalysisService
from app.services.apps.image_analysis.schema import SpatialStatisticsConfig
from app.core.dao.dao_base import get_db_async,get_db_sync
from unittest.mock import AsyncMock, patch
from app.services.apps.image_analysis.workflow_widgets.service import ImageAnalysisWidgetsService

from bson import ObjectId
from datetime import datetime

@pytest.fixture
def image_analysis_widget_service():
    db_sync_client = MongoClient()
    db_async_client = AsyncIOMotorClient()
    
    return ImageAnalysisWidgetsService(db_sync_client=db_sync_client, db_async_client=db_async_client)

def test_image_analysis_widget_service_init(image_analysis_widget_service):
    assert image_analysis_widget_service is not None

def insert_dataset_doc(collection, data):
    client  = get_db_sync()
    db = client['Hexaind'][collection]
    dataset_doc = db.insert_one(data)
    inserted_id = dataset_doc.inserted_id
    # inserted_doc = db.find_one({"_id": inserted_id})
    return inserted_id

def delete_dataset_doc(collection, data):
    client  = get_db_sync()
    db = client['Hexaind'][collection]
    db.delete_one(data)
    return 

@pytest.mark.asyncio
@pytest.mark.fixme
async def test_spatial_statistics(image_analysis_widget_service):
    

    insert_dataset = {
        # "_id": ObjectId("6758201ad7b99f4bc6584861"),
        "id": None,
        "version": "1.0",
        "user_id": "66fa7d1ff53c6f575e66c9a3",
        "project_id": "67233288fc036817c3f16aa0",
        "site_id": "1",
        "action_id": "",
        "name": "hr_defects_week_0_sm",
        "description": "hr_defects_week_0_sm",
        "dataset_type": "IMAGE_DATASET",
        "dataset_sub_type": None,
        "dataset_information": [],
        "upload_status": "COMPLETED",
        "upload_stats": {"percentage": "100%"},
        "metadata": {
            "data_source": "",
            "columns_metadata": None,
            "columns_metadata_file": None
        },
        "created_at": datetime.fromisoformat("2024-12-10T11:03:54.598"),
        "created_by": "Databrick Admin",
        "dataset_location": [
            {
                "isfolder": True,
                "size": "2951842",
                "extension": "N/A",
                "path": "app/tests/services/apps/img_analysis_widgets/processed_image_datasets/hr_defects_week_0_sm1733828636200",
                "last_modified_by": "Databrick Admin",
                "last_modified_at": datetime.fromisoformat("2024-12-10T11:03:54.598")
            }
        ],
        "access_mode": "EXTERNAL",
        "tags": [],
        "excel_sheets_name": None,
        "custom_information": None,
        "api_job_id": "",
        "visualization_paths": {},
        "visualization_job_ids": {},
        "correlation_paths": {},
        "correlation_job_ids": {}
    }
    dataset_id = insert_dataset_doc('datasets', insert_dataset)
    
    insert_dm_dataset={
                        # "_id": ObjectId("6758201ad7b99f4bc6584861"),
                        "_id": dataset_id,
                        "connections_id": "",
                        "data_type": "IMAGE_DATASET",
                        "created_by": "Databrick Admin",
                        "dataset_name": "hr_defects_week_0_sm",
                        "demo": False,
                        "favorited_by": [],
                        "file_type": "image",
                        "foldersdata": [
                            {
                            "subfoldername": "HR_BoatScale",
                            "selectedimages": [
                                {
                                "orignalpath": "app/tests/services/apps/img_analysis_widgets/processed_image_datasets/hr_defects_week_0_sm1733828636200/HR_BoatScale/HR_Boat_Scale (1).JPG",
                                "convertedpath": "app/tests/services/apps/img_analysis_widgets/processed_image_datasets/hr_defects_week_0_sm1733828636200/HR_BoatScale/processedimg/HR_Boat_Scale (1).JPG",
                                "thumbnailpath": "app/tests/services/apps/img_analysis_widgets/processed_image_datasets/hr_defects_week_0_sm1733828636200/HR_BoatScale/processedimg/thumbnail_HR_Boat_Scale (1).png"
                                },
                            ],
                            "processing_attributes": {},
                            "foldersize": "2.805 MB",
                            "kbsize": 2941571,
                            "foldertype": [
                                "JPG"
                            ],
                            "path": "app/tests/services/apps/img_analysis_widgets/processed_image_datasets/hr_defects_week_0_sm1733828636200/HR_BoatScale/",
                            "datapoints": 2
                            }
                        ],
                        "meta_data": {
                            "contributors": [
                            "Databrick"
                            ],
                            "description": "hr_defects_week_0_sm",
                            "keywords": [],
                            "schema": []
                        },
                        "prefix": "PR036-D018_",
                        "project_id": "67233288fc036817c3f16aa0",
                        "remote_server": False,
                        "source": "Local Drive",
                        "user_id": "66fa7d1ff53c6f575e66c9a3",
                        "datapoints": 2,
                        "path": "app/tests/services/apps/img_analysis_widgets/processed_image_datasets/hr_defects_week_0_sm1733828636200/",
                        "size": "2.805 MB",
                        "kbsize": 2941571,
                        "curated": False,
                        "last_access": {
                            "$date": "2024-12-10T16:03:56.207Z"
                        },
                        "enable_FE": True
                        }
    
    insert_dataset_doc('DMCreatedDatasets', insert_dm_dataset)
    spatial_statistics_config = SpatialStatisticsConfig(
        version = "1.0",
        widget_type= "SPATIAL_STATISTICS",
        cutoff= 1,
        quantTech= "AngularyResolvedChordLengthDistributions",
        datasetId= str(dataset_id),
        metadata= "app/tests/services/apps/img_analysis_widgets/spatial_statistics/hr_defects_week0_sm.csv",
        local_states= [[0],[1]],
        coarsening= 1,
        ang_int= 15
    )
    
    project_id = 'project_id'
    results = image_analysis_widget_service.batchProcessing(spatial_statistics_config, project_id)
    
    filter = {'_id': dataset_id}
    delete_dataset_doc('datasets',filter)
    delete_dataset_doc('DMCreatedDatasets',filter)
    filter_FEbatchinfo = {'datasetId':dataset_id}
    delete_dataset_doc('FEbatchinfo',filter_FEbatchinfo)
    
    assert results
