import pytest
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
from app.services.AI.xgboost.schemas import XGBoostConfig
from app.services.AI.xgboost.service import XGBoostService

@pytest.fixture
def xgb_service():
    db_sync_client = MongoClient()
    db_async_client = AsyncIOMotorClient()
    return XGBoostService(db_sync_client=db_sync_client, db_async_client=db_async_client)

def test_xgb_service_init(xgb_service):
    assert xgb_service is not None


@pytest.mark.fixme
def test_train_xgb(xgb_service):
    config = {
    "version": "1.0",
    "input_cols": [
        "PC1",
        "PC2",
        "PC3",
        "PC4",
        "PC5",
        "PC6",
        "PC7",
        "PC8",
        "PC9",
        "PC10",
        "PC11",
        "PC12",
        "PC13",
        "PC14",
        "PC15",
        "PC16"
    ],
    "problem_type": "regression",
    "hyper_params": {
        "k_fold": 10,
        "split_ratio": 20,
        "learning_rate": 0.3,
        "n_estimators": 10,
        "max_depth": 10,
        "input_scaling": None,
        "split_type": "Random",
        "subsample": 0.5,
        "colsample_bytree": 0.8,
        "colsample_bylevel": 0.8,
        "colsample_bynode": 0.8,
        "num_parallel_tree": 5,
        "encoding_type": None
    },
    "widget_type": "XGBOOST",
    "output_col": "k33"
}

    ml_config = XGBoostConfig(**config)
    data_path = Path('app/tests/services/AI/automl/k_data.csv')
    result_folders = '/tmp'
    project_id = 'project_id'
    wf_id = 'wf_id'
    run_id = 'run_id'
    dataset_name = 'dataset_name'
    user_id = 'user_id'
    site_id = 'site_id'
    user_name = 'user_name'
    widget_urn = 'widget_urn'
    response = xgb_service.train_xgb(ml_config, data_path, result_folders, project_id, wf_id, run_id, dataset_name, user_id, site_id, user_name, widget_urn=widget_urn)
    # Check results
    assert response.tabular_path


def test_train_xgb_failure(xgb_service):
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
    response = xgb_service.train_xgb(None, data_path, result_folders, project_id, wf_id, run_id, dataset_name, user_id, site_id, user_name)
    assert response.exception_detail

