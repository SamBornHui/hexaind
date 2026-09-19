import pytest
from unittest.mock import patch, MagicMock
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
from app.services.AI.automl.dao import AutoMLDao 
from app.services.AI.gpr.dao import GPRDao 
from app.services.AI.gpr.schemas import GPRConfig, GPRResponse
from app.services.AI.gpr.service import GPRService

@pytest.fixture
def gpr_service():
    db_sync_client = MongoClient()
    db_async_client = AsyncIOMotorClient()
    return GPRService(db_sync_client=db_sync_client, db_async_client=db_async_client)

def test_gpr_service_init(gpr_service):
    assert gpr_service is not None


@pytest.mark.fixme
def test_train_gpr(gpr_service):
    config = dict(
            input_cols= ["GF","R","LA","Machining","LR","Temperature","fot1","fot2","fot3"],
            output_cols= ["k","b"],
            widget_type= "GPR",
            mean='constant',
            variational= {
                'num_latents': 4,
                'num_inducin': 4
            },
            spectral_kernel= {
            'spectral_selected': True,
            'num_mixtures': 9
            },
            kernel_selected= [
            False,
            False,
            False,
            False,
            False
            ]
        )
    ml_config = GPRConfig(**config)
    data_path = Path('app/tests/services/AI/gpr/B_cat_data.csv')
    result_folders = '/tmp'
    project_id = 'project_id'
    wf_id = 'wf_id'
    run_id = 'run_id'
    dataset_name = 'dataset_name'
    user_id = 'user_id'
    site_id = 'site_id'
    user_name = 'user_name'
    response = gpr_service.train_gpr(ml_config, data_path, result_folders, project_id, wf_id, run_id, dataset_name, user_id, site_id, user_name)
    # Check results
    assert response


@pytest.mark.fixme
def test_train_gpr_failure(gpr_service):
    # Test to handle and assert on exceptions
    data_path = Path('app/tests/services/AI/gpr/B_cat_datass.csv')
    result_folders = '/tmp'
    project_id = 'project_id'
    wf_id = 'wf_id'
    run_id = 'run_id'
    dataset_name = 'dataset_name'
    user_id = 'user_id'
    site_id = 'site_id'
    user_name = 'user_name'
    response = gpr_service.train_gpr(None, data_path, result_folders, project_id, wf_id, run_id, dataset_name, user_id, site_id, user_name)
    assert response.exception_detail

