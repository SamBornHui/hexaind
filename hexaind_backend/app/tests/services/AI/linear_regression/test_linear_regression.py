import pytest
from unittest.mock import patch, MagicMock
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
from app.services.AI.linear_regression.schemas import LinearRegressionConfig
from app.services.AI.linear_regression.service import LinearRegressionService

@pytest.fixture
def linear_regression_service():
    db_sync_client = MongoClient()
    db_async_client = AsyncIOMotorClient()
    return LinearRegressionService(db_sync_client=db_sync_client, db_async_client=db_async_client)

def test_linear_regression_service_init(linear_regression_service):
    assert linear_regression_service is not None


@pytest.mark.fixme
def test_train_linear_regression(linear_regression_service):
    config = dict(
            input_cols= ['PC1', 'PC2', 'PC3', 'PC4', 'PC5', 'PC6', 'PC7', 'PC8', 'PC9', 'PC10', 'PC11', 'PC12', 'PC13', 'PC14', 'PC15', 'PC16',],
            output_col= 'k33',
            widget_type= 'LINEAR_REGRESSION',
            evaluation_metric='mean_absolute_error',
            lr_hyperparameters = {
            'LR': {}, 
            },
            additional_hyperparameter_tune_kwargs = {"num_trials": 1},
            split_ratio= 50
        )
    ml_config = LinearRegressionConfig(**config)
    data_path = Path('app/tests/services/AI/automl/k_data.csv')
    result_folders = '/tmp'
    project_id = 'project_id'
    wf_id = 'wf_id'
    run_id = 'run_id'
    dataset_name = 'dataset_name'
    user_id = 'user_id'
    site_id = 'site_id'
    user_name = 'user_name'
    response = linear_regression_service.train_linear_regression(ml_config, data_path, result_folders, project_id, wf_id, run_id, dataset_name, user_id, site_id, user_name)
    # Check results
    assert response.tabular_path


@pytest.mark.fixme
def test_train_linear_regression_failure(linear_regression_service):
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
    response = linear_regression_service.train_linear_regression(None, data_path, result_folders, project_id, wf_id, run_id, dataset_name, user_id, site_id, user_name)
    assert response.exception_detail

