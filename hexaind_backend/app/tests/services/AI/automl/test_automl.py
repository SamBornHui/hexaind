import pytest
from unittest.mock import patch, MagicMock
from pymongo import MongoClient
# from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
from app.services.AI.automl.dao import AutoMLDao 
from app.services.AI.automl.schemas import AutoMLConfig, AutoMLResponse
from app.services.AI.automl.service import AutoMLService

@pytest.fixture
def automl_service():
    db_sync_client = MongoClient()
    # db_async_client = AsyncIOMotorClient()
    return AutoMLService(db_sync_client=db_sync_client)

def test_automl_service_init(automl_service):
    assert automl_service is not None


@pytest.mark.fixme
def test_update_hyperparameters_for_gpu(automl_service):
    hyperparameters = {'XGB': {}, 'GBM': {}, 'CAT': {}, 'FASTAI': {}}
    result = automl_service.update_hyperparameters_for_gpu(hyperparameters, use_gpu=True)
    assert result == {'XGB': {'tree_method': 'gpu_hist'}, 'GBM': {'device_type': 'gpu'}, 'CAT': {'task_type': 'GPU'}, 'FASTAI': {'num_gpus': 1}}

@pytest.mark.fixme
def test_train_automl_regression(automl_service):
    config = {
            'version': '1.0',
            'problem_type': 'regression',
            'widget_type':'AUTOML',
            'input_cols': ['PC1',
            'PC2',
            'PC3',
            'PC4',
            'PC5',
            'PC6',
            'PC7',
            'PC8',
            'PC9',
            'PC10',
            'PC11',
            'PC12',
            'PC13',
            'PC14',
            'PC15',
            'PC16'],
            'output_col': 'k33',
            'split_ratio': 50,
            'additional_hyperparameter_tune_kwargs': {'scheduler': 'local',
            'searcher': 'auto',
            'num_trials': 1,
            'time_out': 600},
            'automl_config': {'input_scaling':'Standard',
            'evaluation_metric':'mean_absolute_error',
            'automl_hyperparameters': {'GBM': {}
            }}
                }
    ml_config = AutoMLConfig(**config)
    data_path = Path('app/tests/services/AI/automl/k_data.csv')
    result_folders = '/tmp'
    project_id = 'project_id'
    wf_id = 'wf_id'
    run_id = 'run_id'
    dataset_name = 'dataset_name'
    user_id = 'user_id'
    site_id = 'site_id'
    user_name = 'user_name'
    response = automl_service.train_automl(ml_config, data_path, result_folders, project_id, wf_id, run_id, dataset_name, user_id, site_id, user_name)
    # Check results
    assert response.tabular_path

# def test_train_automl_classification(automl_service):
#     config = {
#         'version': '1.0',
#         'problem_type': 'classification',
#         'widget_type':'AUTOML',
#         'input_cols': ['Feature0', 'Feature1'],
#         'output_col': 'Class',
#         'split_ratio': 50,
#         'additional_hyperparameter_tune_kwargs': {'scheduler': 'local',
#         'searcher': 'auto',
#         'num_trials': 1,
#         'time_out': 600},
#         'automl_config': {'evaluation_metric_cls':'accuracy',
#         'automl_hyperparameters_cls': {'GBM': [{'extra_trees': True,
#             'ag_args': {'name_suffix': 'XT'}},
#             {},
#             'GBMLarge'],
#         'CAT': {},
#         'XGB': {}}}
#         }
#     ml_config = AutoMLConfig(**config)
#     data_path = Path('app/tests/services/AI/gaussian_process_cls/pcdata_mag_train.csv')
#     result_folders = '/tmp'
#     project_id = 'project_id'
#     wf_id = 'wf_id'
#     run_id = 'run_id'
#     dataset_name = 'dataset_name'
#     user_id = 'user_id'
#     site_id = 'site_id'
#     user_name = 'user_name'
#     response = automl_service.train_automl(ml_config, data_path, result_folders, project_id, wf_id, run_id, dataset_name, user_id, site_id, user_name)
#     # Check results
#     assert response.tabular_path

@pytest.mark.fixme
def test_train_automl_failure(automl_service):
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
    response = automl_service.train_automl(None, data_path, result_folders, project_id, wf_id, run_id, dataset_name, user_id, site_id, user_name)
    assert response.exception_detail

