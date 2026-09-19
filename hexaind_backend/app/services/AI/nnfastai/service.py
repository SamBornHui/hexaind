# Original code with MLflow integration
from app.services.data.curation.data.source.model import DataSourceModel
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
import pandas as pd
import mlflow
import os
import datetime
import logging
import sys

from .dao import NNFastAIDao
from .schemas import NNFastAIConfig, NNFastAIResponse

from app.services.AI.models.utils.model_utils import ModelUtils
from app.services.AI.models.service import autogluon_log_model
from app.services.data.assets.datasets.schemas import AccessMode, Dataset
from app.services.notification.service import Notification
from app.services.notification.schema import (
    NotificationModel,
    NotificationType,
    NotificationCategory,
    NotificationImportance)

from app.config.env_vars import environment as env

logger = logging.getLogger(__package__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))


class NNFastAIService:
    def __init__(self, db_sync_client: MongoClient = None, db_async_client: AsyncIOMotorClient = None) -> None: # type: ignore
        logger.info("Initializing NN_Fast_AI Service")

        self.fastai = NNFastAIDao(db_sync_client=db_sync_client, db_async_client=db_async_client)


    def send_notification(self, notification_obj):
        logger.info(f"Sending notification: {notification_obj['message']}")
        verified_notfication_obj = NotificationModel(**notification_obj)
        notification_service_obj = Notification(db_sync_client=self.fastai.db_sync_client)
        notification_service_obj.create_notification_sync(verified_notfication_obj)

    
    
    def train_fastai(self, ml_config: NNFastAIConfig, data_path: Path, result_folders: Path, project_id: str, wf_id: str, run_id: str, dataset_name: str, user_id: str, site_id: str, user_name: str, dataset_record: Dataset=None, widget_urn: str=None) -> NNFastAIResponse:
        try:
            logger.info("Starting NN_Fast training")
            logger.info(f"NN_Fast configuration {str(ml_config)}")
            # Verify data path and load data using pandas
            if not data_path.exists():
                raise FileNotFoundError(f"Data file not found at path: {data_path}")

            data = ModelUtils.read_data_for_training(dataset_record=dataset_record,data_path=data_path)

            if data.empty:
                raise ValueError("Loaded data is empty")
            
            logger.info("Preprocessing for NN_Fast AI")

            total_cols = list(ml_config.input_cols)
            total_cols.append(ml_config.output_col)
            data = ModelUtils.check_and_drop_nan(data, total_cols)
            probmlem_type = ml_config.problem_type
            data = data[total_cols]
            data = data.sample(frac=1).reset_index(drop=True)
            train_data = data.sample(frac=ml_config.split_ratio/100, random_state=42)
            test_data = data.drop(train_data.index)

            hyperparameters = ml_config.fastai_hyperparameters.model_dump()
            hyperparameter_tune_kwargs = ml_config.additional_hyperparameter_tune_kwargs.model_dump()
            
            self.result_folders =  result_folders
            self.extra_metrics = ['mean_absolute_error', 'mean_squared_error', 'root_mean_squared_error']
            # Set up MLflow
            mlflow.set_tracking_uri(env.mlflow_tracking_uri)  # Set this to your MLflow server's URI
            experiment_name = f"NNFastAI_{project_id}_{wf_id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            mlflow.set_experiment(experiment_name)
            mlflow.set_tag("NNFastAI version", "v1.0")
            mlflow.set_tag("Model type", "NNFastAI")
            mlflow.set_tag('custom_run_id', run_id)
            flat_params_dict = ModelUtils.flatten_dict(ml_config.model_dump())
            notification_obj = {"message":"NN_FastAi Model training has started",
                                'category_id':wf_id,
                                'project_id':project_id,
                                'notification_type':NotificationType.INFO,
                                'importance':NotificationImportance.MEDIUM,
                                'notification_category':NotificationCategory.MODEL}
            
            self.ml_model = dict(user_id=user_id, project_id=project_id, site_id=site_id, wf_run_id=run_id, description='NNFastAI model description', created_at=datetime.datetime.now(),
                                            ml_model_file_path=None, access_mode=AccessMode.INTERNAL, tags=[], user_name=user_name, dataset_path=str(data_path), widget_urn=widget_urn)
            self.model_detail = dict(testing_samples=test_data.shape[0], training_samples=train_data.shape[0], configs=ml_config.model_dump(), dataset_name=dataset_name)

            with mlflow.start_run(nested=True) as run:
                model_name = f"NNFastAI_model_{run.info.run_id}"
                model_path = os.path.join(result_folders, model_name)
                os.makedirs(model_path, exist_ok=True)
                self.ml_model['ml_model_file_path'] = model_path
                self.summary_file = os.path.join(model_path, 'summary.csv')
                self.ml_model['ml_flow_detail'] = dict(experiment_id=run.info.experiment_id, 
                                                       experiment_name=experiment_name, 
                                                       run_id=run.info.run_id)
                self.send_notification(notification_obj=notification_obj)
                mlflow.log_params(flat_params_dict)
                predictor = ModelUtils.train_and_log_models(data, train_data, test_data, hyperparameters, ml_config.evaluation_metric, ml_config.output_col, model_path, hyperparameter_tune_kwargs, probmlem_type, self.model_detail, self.extra_metrics, self.fastai.db_sync_client, self.ml_model)
                predictor.save()
                autogluon_log_model(model_path, model_name=predictor.model_names()[0])
                mlflow.log_artifact(self.summary_file)
                artifact_final_path = os.path.join(result_folders, model_name)
                mlflow.artifacts.download_artifacts(run_id=run.info.run_id,dst_path=artifact_final_path)
                logger.info(f"Artifacts downloaded to: {artifact_final_path}")
            
            

            mlflow.end_run()

            notification_obj['message'] = "Model NN_FastAi has been trained"
            self.send_notification(notification_obj=notification_obj)

            return NNFastAIResponse(tabular_path=self.summary_file,models_path=os.path.join(artifact_final_path,"model"))

        
        except Exception as e:
            notification_obj = {"message":"NN_FastAi Model training has failed",
                                'category_id':wf_id,
                                'project_id':project_id,
                                'notification_type':NotificationType.ERROR,
                                'importance':NotificationImportance.HIGH,
                                'notification_category':NotificationCategory.MODEL}
            
            self.send_notification(notification_obj=notification_obj)
            return NNFastAIResponse(exception_detail=str(e))
