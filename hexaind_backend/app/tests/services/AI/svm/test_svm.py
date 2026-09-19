import pytest
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
from app.services.AI.svm.schemas import SVMRConfig
from app.services.AI.svm.service import SVMRService

@pytest.fixture
def svm_service():
    db_sync_client = MongoClient()
    db_async_client = AsyncIOMotorClient()
    return SVMRService(db_sync_client=db_sync_client, db_async_client=db_async_client)

def test_svm_service_init(svm_service):
    assert svm_service is not None


@pytest.mark.fixme
def test_train_regression_svm(svm_service):
    config = {
    "version": "1.0",
    "widget_type": "SVM",  # Assuming WidgetType.SVM resolves to the string 'SVM'
    "kernel": "sigmoid",
    "C": 1e-1,
    "gamma": 1e-5,
    "coef0": 1.2,
    "degree": None,
    "epsilon": 0.1,
    "tol": 0.001,
    "input_cols" :['PC1', 'PC2', 'PC3', 'PC4', 'PC5', 'PC6', 'PC7', 'PC8', 'PC9', 'PC10',
            'PC11', 'PC12', 'PC13', 'PC14', 'PC15'],
    "output_cols" :['PC16','k33'],
    "problem_type": "regression",  # Assuming an example value for ProblemType
    "sampling": "randomus"  # Assuming None or a specific sampling value
    }
    ml_config = SVMRConfig(**config)
    data_path = 'app/tests/services/AI/automl/k_data.csv'
    result_folders = '/tmp'
    project_id = 'project_id'
    wf_id = 'wf_id'
    run_id = 'run_id'
    dataset_name = 'dataset_name'
    user_id = 'user_id'
    site_id = 'site_id'
    user_name = 'user_name'
    response = svm_service.train_svm(ml_config, data_path, result_folders, project_id, wf_id, run_id, dataset_name, user_id, site_id, user_name)
    # Check results
    assert response.tabular_path

@pytest.mark.fixme
def test_train_classification_svm(svm_service):
    config = dict(
            kernel="sigmoid",
            C=1e-1,
            gamma=1e-5,
            coef0=1.2,
            input_cols =['Feature0','Feature1'],
            output_cols =['Class'],
            sampling = "smote",
            problem_type = "classification",
            widget_type = "SVM"

        )


    ml_config = SVMRConfig(**config)
    data_path = 'app/tests/services/AI/gaussian_process_cls/pcdata_mag_train.csv'
    result_folders = '/tmp'
    project_id = 'project_id'
    wf_id = 'wf_id'
    run_id = 'run_id'
    dataset_name = 'dataset_name'
    user_id = 'user_id'
    site_id = 'site_id'
    user_name = 'user_name'
    response = svm_service.train_svm(ml_config, data_path, result_folders, project_id, wf_id,
                                      run_id, dataset_name, user_id, site_id, user_name)
    # Check results
    assert response.tabular_path


@pytest.mark.fixme
def test_train_fastai_failure(svm_service):
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
    response = svm_service.train_svm(None, data_path, result_folders, project_id, wf_id, run_id, dataset_name, user_id, site_id, user_name)
    assert response.exception_detail

