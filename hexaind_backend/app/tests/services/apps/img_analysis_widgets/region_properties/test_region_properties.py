from app.services.data.assets.image_datasets.schemas import RegionPropertiesConfig
import pytest
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient

from app.services.apps.image_analysis.service import ImageAnalysisService
from app.services.apps.image_analysis.schema import *
from app.core.dao.dao_base import get_db_async,get_db_sync
from unittest.mock import AsyncMock, patch
from app.services.apps.image_analysis.workflow_widgets.service import ImageAnalysisWidgetsService
from app.services.data.assets.image_datasets.schemas import RegionPropertiesConfig, ImgDatasets
from app.services.data.assets.datasets.service import DatasetsService

@pytest.fixture
def image_analysis_widget_service():
    db_sync_client = MongoClient()
    db_async_client = AsyncIOMotorClient()
    
    return ImageAnalysisWidgetsService(db_sync_client=db_sync_client, db_async_client=db_async_client)

def test_image_analysis_widget_service_init(image_analysis_widget_service):
    assert image_analysis_widget_service is not None

@pytest.mark.fixme
@pytest.mark.asyncio
async def test_region_properties(image_analysis_widget_service):
    selected_datasets = [
        # ImgDatasets(
        {"dataset_id" :"1",
        "dataset_name" : "hr_defect_week_0",
        "defect_metadata_path": "app/tests/services/apps/img_analysis_widgets/region_properties/hr_defects_week0_sm_metadata.csv"
        }# )
    ]
    processed_data = [
        {
            "folder_id": "674dc85641d1ef0a28044993",
            "original_img_path": "app/tests/services/apps/img_analysis_widgets/processed_image_datasets/hr_defect_week_01733150804329/HR_BoatScale/HR_Boat_Scale (1).JPG",
            "masked_img_path": "app/tests/services/apps/img_analysis_widgets/processed_image_datasets/hr_defect_week_01733150804329/HR_BoatScale/modifiedimages//HR_Boat_Scale (1).JPG",
            "segmented_img_path": "app/tests/services/apps/img_analysis_widgets/processed_image_datasets/hr_defect_week_01733150804329/HR_BoatScale/HR_Boat_Scale (1)/Remove small objects_postprocessed_binary1733150915397.png",
            "segmented_data_id": "674dc8e741d1ef0a280449ee",
            "scale": None,
            "popup_unit": None
        }
        ]
    region_props_config = RegionPropertiesConfig(
        version = "1.0",
        widget_type= "REGION_PROPERTY",
        region_properties= [
            "image_convex",
            "eccentricity",
            "area_filled",
            "perimeter",
            "euler_number",
            "bbox",
            "area_bbox",
            "image_intensity",
            "image",
            "intensity_max",
            "axis_major_length",
            "intensity_mean",
            "label",
            "area_convex",
            "axis_minor_length",
            "image_filled",
            "orientation",
            "coords",
            "feret_diameter_max",
            "area",
            "intensity_min",
            "solidity",
            "extent",
            "perimeter_crofton",
            "equivalent_diameter_area",
        ])
    project_id = 'project_id'
    dataset_service = DatasetsService()
    Objects_df = await image_analysis_widget_service.calc_regionprops(processed_data, region_props_config)
    df_reg_props = await image_analysis_widget_service.get_defect_characteristics(selected_datasets, Objects_df)
    reg_props_results_file = dataset_service.generate_file_info(input_data=df_reg_props,project_id=project_id)
       
    assert reg_props_results_file
