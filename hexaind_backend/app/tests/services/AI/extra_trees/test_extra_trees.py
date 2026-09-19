import pytest
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
from app.services.AI.extratrees.schemas import ExtraTreesConfig
from app.services.AI.extratrees.service import ExtraTreesService

@pytest.fixture
def xt_service():
    db_sync_client = MongoClient()
    db_async_client = AsyncIOMotorClient()
    return ExtraTreesService(db_sync_client=db_sync_client, db_async_client=db_async_client)

def test_xt_service_init(xt_service):
    assert xt_service is not None


@pytest.mark.fixme
def test_train_xt(xt_service):
    config = dict(
            input_cols= ['PC1', 'PC2', 'PC3', 'PC4', 'PC5', 'PC6', 'PC7', 'PC8', 'PC9', 'PC10', 'PC11', 'PC12', 'PC13', 'PC14', 'PC15', 'PC16',],
            output_col= 'k33',
            evaluation_metric='mean_absolute_error',
            widget_type= 'EXTRA_TREES',
            extratrees_hyperparameters = {
            'XT': {},   # ExtraTees
            },
            additional_hyperparameter_tune_kwargs = {
                "scheduler": "local",
                 "searcher": "auto",
                "num_trials": 10,
                "time_out": 600
            },
            split_ratio= 50
        )
    ml_config = ExtraTreesConfig(**config)
    data_path = Path('app/tests/services/AI/automl/k_data.csv')
    result_folders = '/tmp'
    project_id = 'project_id'
    wf_id = 'wf_id'
    run_id = 'run_id'
    dataset_name = 'dataset_name'
    user_id = 'user_id'
    site_id = 'site_id'
    user_name = 'user_name'
    response = xt_service.train_extra_trees(ml_config, data_path, result_folders, project_id, wf_id, run_id, dataset_name, user_id, site_id, user_name)
    # Check results
    assert response.tabular_path


@pytest.mark.fixme
def test_train_rf_failure(xt_service):
    # Test to handle and assert on exceptions
    data_path = Path('app/tests/services/AI/automl/k_datass.csv')
    result_folders = '/tmp'
    project_id = 'project_id'
    wf_id = 'wf_id'
    run_id = 'run_id'
    dataset_name = 'dataset_name'
    user_id = 'user_id'
    site_id = 'site_id'
    user_name = 'user_name'
    response = xt_service.train_extra_trees(None, data_path, result_folders, project_id, wf_id, run_id, dataset_name, user_id, site_id, user_name)
    assert response.exception_detail

