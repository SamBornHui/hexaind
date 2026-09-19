import pytest
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
from app.services.AI.gaussian_process_cls.service import GPCConfig, GPCService

@pytest.fixture
def gpc_service():
    db_sync_client = MongoClient()
    db_async_client = AsyncIOMotorClient()
    return GPCService(db_sync_client=db_sync_client, db_async_client=db_async_client)

def test_gpc_service_init(gpc_service):
    assert gpc_service is not None


@pytest.mark.fixme
def test_train_gpc(gpc_service):
    config = {
            "version": "1.0",
            "input_cols": [
                "Feature0",
                "Feature1"
            ],
            "widget_type": "GPC",
            "mean": "linear",
            "variational": False,
            "spectral_kernel_setting": {
                "spectral_kernel": False,
                "num_mixtures": 0
            },
            "sampler_type": "randomus",
            "max_trains": 1500,
            "covariance_function": {
                "kernel_selected": True,
                "covariance_function_selection": [False, True, True, False, False]
            },
            "output_col": "Class",
            "num_epochs": 10,
            "batch_size":10
        }
    ml_config = GPCConfig(**config)
    data_path = Path('app/tests/services/AI/gaussian_process_cls/pcdata_mag_train.csv')
    result_folders = '/tmp'
    project_id = 'project_id'
    wf_id = 'wf_id'
    run_id = 'run_id'
    dataset_name = 'dataset_name'
    user_id = 'user_id'
    site_id = 'site_id'
    user_name = 'user_name'
    response = gpc_service.train_gpc(ml_config, data_path, result_folders, project_id, wf_id, run_id, dataset_name, user_id, site_id, user_name)
    # Check results
    assert response.tabular_path


@pytest.mark.fixme
def test_train_gpc_failure(gpc_service):
    # Test to handle and assert on exceptions
    data_path = Path('app/tests/services/AI/gaussain_process_cls/pcdatas_mag_train.csv')
    result_folders = '/tmp'
    project_id = 'project_id'
    wf_id = 'wf_id'
    run_id = 'run_id'
    dataset_name = 'dataset_name'
    user_id = 'user_id'
    site_id = 'site_id'
    user_name = 'user_name'
    response = gpc_service.train_gpc(None, data_path, result_folders, project_id, wf_id, run_id, dataset_name, user_id, site_id, user_name)
    assert response.exception_detail

