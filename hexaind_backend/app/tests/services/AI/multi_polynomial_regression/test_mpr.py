import pytest
# from unittest.mock import patch, MagicMock
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path

from app.services.AI.multi_polynomial_regression.service import MPRService
from app.services.AI.multi_polynomial_regression.schemas import MPRConfig
from pydantic import BaseModel, Field, conint, validator, ValidationError

@pytest.fixture
def mpr_service():
    db_sync_client = MongoClient()
    db_async_client = AsyncIOMotorClient()
    return MPRService(db_sync_client=db_sync_client, db_async_client=db_async_client)

def test_mpr_service_init(mpr_service):
    assert mpr_service is not None


@pytest.mark.fixme
def test_train_gpr(mpr_service):

    # Create a dict object
    config_dict = {
        "version": "1.0",
        "problem_type": "regression",
        "widget_type": "MPR",
        "input_cols": ["x", "y"],
        "output_col": "z",
        "split_ratio": 42,
        "split_type": "Random",
        "input_scaling": "Standard",
        "polynomial_degree": 3,
        "polynomial_degree_feature": None,
        "cross_validation_folds": 10,
        "random_state": 42,
        "categorical_encoding": None
    }

    try:
        config = MPRConfig(**config_dict)
        print(config)
    except ValidationError as e:
        print(e.json())
    results_folder = '/tmp'
    data_path2 =  'app/tests/services/AI/multi_polynomial_regression/XYZ_PD3.csv'
    kwargs = {
        'data_path': Path(data_path2),  # The path is converted to a Path object
        'result_folders': Path(results_folder),  # The results_folder is converted to a Path object
        'project_id': '657849cebb20a16a3466db93',
        'wf_id': 'Xy3O7cE1x6iVFj6ukFzIVxjpmficWZh123567',
        'run_id': '789',  # Extracted from results_folder, assuming 'r_789' is the run ID
        'dataset_name': 'theromocalc_test',  # Assuming dataset name is based on the file name
        'user_id': 'user123',  # Replace with actual user ID if needed
        'site_id': 'site456',  # Replace with actual site ID if needed
        'user_name': 'JohnDoe',  # Replace with actual user name if needed
        'dataset_record': None,  # You can replace this with an actual Dataset object if available
        "widget_urn" : 'widget_urn'
    }

    response = mpr_service.train_mpr(config, **kwargs)    # Check results
    assert response.tabular_path


@pytest.mark.fixme
def test_train_gpr_failure(mpr_service):
    # Test to handle and assert on exceptions
    results_folder = '/tmp'
    data_path2 =  Path('app/tests/services/AI/multi_polynomial_regression/XYZ_PD3.csv')
    kwargs = {
        'data_path': Path(data_path2),  # The path is converted to a Path object
        'result_folders': Path(results_folder),  # The results_folder is converted to a Path object
        'project_id': '657849cebb20a16a3466db93',
        'wf_id': 'Xy3O7cE1x6iVFj6ukFzIVxjpmficWZh123567',
        'run_id': '789',  # Extracted from results_folder, assuming 'r_789' is the run ID
        'dataset_name': 'theromocalc_test',  # Assuming dataset name is based on the file name
        'user_id': 'user123',  # Replace with actual user ID if needed
        'site_id': 'site456',  # Replace with actual site ID if needed
        'user_name': 'JohnDoe',  # Replace with actual user name if needed
        'dataset_record': None,  # You can replace this with an actual Dataset object if available
        "widget_urn" : 'widget_urn'
    }
    response = mpr_service.train_mpr(None, **kwargs)
    assert response.exception_detail

