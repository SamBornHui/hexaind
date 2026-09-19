import pytest
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
from app.services.AI.k_nearest_neighbors.schemas import KNNConfig
from app.services.AI.k_nearest_neighbors.service import KNNService

@pytest.fixture
def knn_service():
    db_sync_client = MongoClient()
    db_async_client = AsyncIOMotorClient()
    return KNNService(db_sync_client=db_sync_client, db_async_client=db_async_client)

def test_knn_service_init(knn_service):
    assert knn_service is not None


@pytest.mark.fixme
def test_train_knn(knn_service):
    config = dict(
            input_cols= ['PC1', 'PC2', 'PC3', 'PC4', 'PC5', 'PC6', 'PC7', 'PC8', 'PC9', 'PC10', 'PC11', 'PC12', 'PC13', 'PC14', 'PC15', 'PC16',],
            output_col= 'k33',
            widget_type= 'KNEIGHBORS',
            evaluation_metric='mean_absolute_error',
            knn_hyperparameters = {
            'KNN': {},   # KNN hyperparameters
            },
            additional_hyperparameter_tune_kwargs = {"num_trials": 1},
            split_ratio= 50
        )
    ml_config = KNNConfig(**config)
    data_path = Path('app/tests/services/AI/automl/k_data.csv')
    result_folders = '/tmp'
    project_id = 'project_id'
    wf_id = 'wf_id'
    run_id = 'run_id'
    dataset_name = 'dataset_name'
    user_id = 'user_id'
    site_id = 'site_id'
    user_name = 'user_name'
    response = knn_service.train_knn(ml_config, data_path, result_folders, project_id, wf_id, run_id, dataset_name, user_id, site_id, user_name)
    # Check results
    assert response.tabular_path


@pytest.mark.fixme
def test_train_knn_failure(knn_service):
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
    response = knn_service.train_knn(None, data_path, result_folders, project_id, wf_id, run_id, dataset_name, user_id, site_id, user_name)
    assert response.exception_detail

