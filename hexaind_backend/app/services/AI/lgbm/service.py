# Original code with MLflow integration
import pandas as pd
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
import mlflow
import os
import datetime
import logging
import sys

from .dao import LGBMDao
from .schemas import LGBMConfig, LGBMResponse

from app.services.AI.models.utils.model_utils import ModelUtils
from app.services.AI.models.service import autogluon_log_model
from app.services.data.assets.datasets.schemas import AccessMode
from app.services.notification.service import Notification
from app.services.notification.schema import (
    NotificationModel,
    NotificationType,
    NotificationCategory,
    NotificationImportance)

from app.services.data.assets.datasets.schemas import Dataset, DatasetMetadata, DatasetSourceFormats, DatasetType
from app.services.data.curation.data.source.model import DataSourceModel
from app.config.env_vars import environment as env

logger = logging.getLogger(__package__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))

class LGBMService:
    def __init__(self, db_sync_client: MongoClient = None, db_async_client: AsyncIOMotorClient = None) -> None: # type: ignore
        logger.info("Initializing LGBM Service")
        self.lgbm_dao = LGBMDao(db_sync_client=db_sync_client, db_async_client=db_async_client)


    def send_notification(self, notification_obj):
        verified_notfication_obj = NotificationModel(**notification_obj)
        notification_service_obj = Notification(db_sync_client=self.lgbm_dao.db_sync_client)
        notification_service_obj.create_notification_sync(verified_notfication_obj)

    
    def train_lgbm(self, lgbm_config: LGBMConfig, data_path: Path, result_folders: Path,
                     project_id: str, wf_id: str, run_id: str, dataset_name: str, user_id: str, site_id: str, user_name: str,
                     dataset_record: Dataset=None, widget_urn: str=None) -> LGBMResponse:
        try:
            logger.info("Starting LGBM training")
            logger.info(f"LGBM configuration {str(lgbm_config)}")
            # Verify data path and load data using pandas
            if not data_path.exists():
                raise FileNotFoundError(f"Data file not found at path: {data_path}")
            data = ModelUtils.read_data_for_training(dataset_record=dataset_record,data_path=data_path)

            if data.empty:
                raise ValueError("Loaded data is empty")
            logger.info("Preprocessing for regression")

            total_cols = list(lgbm_config.input_cols)
            total_cols.append(lgbm_config.output_col)
            data = ModelUtils.check_and_drop_nan(data, total_cols)
            
            problem_type = lgbm_config.problem_type
            data = data[total_cols]
            data = data.sample(frac=1).reset_index(drop=True)
            train_data = data.sample(frac=lgbm_config.split_ratio/100, random_state=42)
            test_data = data.drop(train_data.index) 
            hyperparameters = lgbm_config.lgbm_hyperparameters.model_dump()
            hyperparameter_tune_kwargs = lgbm_config.additional_hyperparameter_tune_kwargs.model_dump()
            
            self.result_folders =  result_folders
            self.extra_metrics = ['mean_absolute_error', 'mean_squared_error', 'root_mean_squared_error']
            # Set up MLflow
            logger.info("Creating MLFLOW experiment")

            mlflow.set_tracking_uri(env.mlflow_tracking_uri)  # Set this to your MLflow server's URI
            experiment_name = f"LGBM_{project_id}_{wf_id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            mlflow.set_experiment(experiment_name)
            mlflow.set_tag("LGBM version", "v1.0")
            mlflow.set_tag("Model type", "LGBM")
            mlflow.set_tag('custom_run_id', run_id)
            flat_params_dict = ModelUtils.flatten_dict(lgbm_config.model_dump())
            notification_obj = {"message":"LGBM Model training has started",
                                'category_id':wf_id,
                                'project_id':project_id,
                                'notification_type':NotificationType.INFO,
                                'importance':NotificationImportance.MEDIUM,
                                'notification_category':NotificationCategory.MODEL}
            
            self.ml_model = dict(user_id=user_id, project_id=project_id, site_id=site_id, wf_run_id=run_id, description='lgbm model description', created_at=datetime.datetime.now(),
                                            ml_model_file_path=None, access_mode=AccessMode.INTERNAL, tags=[], user_name=user_name, dataset_path=str(data_path), widget_urn=widget_urn)
            self.model_detail = dict(testing_samples=test_data.shape[0], training_samples=train_data.shape[0], configs=lgbm_config.model_dump(), dataset_name=dataset_name)

            top_features = []
            logger.info("Starting MLFLOW experiment")

            with mlflow.start_run(nested=True) as run:
                model_name = f"LGBM_model_{run.info.run_id}"
                model_path = os.path.join(result_folders, model_name) #result_folders/model_name
                os.makedirs(model_path, exist_ok=True)
                self.ml_model['ml_model_file_path'] = model_path
                self.summary_file = os.path.join(model_path, 'summary.csv')
                self.ml_model['ml_flow_detail'] = dict(experiment_id=run.info.experiment_id, experiment_name=experiment_name, run_id=run.info.run_id)
                self.send_notification(notification_obj=notification_obj)
                mlflow.log_params(flat_params_dict)
                predictor, shap_importance = ModelUtils.train_and_log_models(data, train_data, test_data, hyperparameters, lgbm_config.evaluation_metric, lgbm_config.output_col, model_path, hyperparameter_tune_kwargs, problem_type, self.model_detail, self.extra_metrics, self.lgbm_dao.db_sync_client, self.ml_model, return_best_model_shap_importance=True)
                if shap_importance is not None:
                    top_features = shap_importance['column_name'].values.tolist()[:10] # grab top 10 features

                predictor.save()
                autogluon_log_model(model_path, model_name=predictor.model_names()[0])
                mlflow.log_artifact(self.summary_file)

                artifact_final_path = os.path.join(result_folders, model_name) #result_folders/artifact_name
                mlflow.artifacts.download_artifacts(run_id=run.info.run_id, dst_path=artifact_final_path)
                logger.info(f"Artifacts downloaded to: {artifact_final_path}")
            
            mlflow.end_run()
            logger.info("MLFLOW Experiment Completed")

            notification_obj['message'] = "Model LGBM has been trained"
            self.send_notification(notification_obj=notification_obj)

            return LGBMResponse(tabular_path=self.summary_file, best_model_top_features=top_features, models_path=os.path.join(artifact_final_path,"model"))

        
        except Exception as e:
            logger.error("LGBM training failed", exc_info=True)

            notification_obj = {"message":"LGBM Model training has failed",
                                'category_id':wf_id,
                                'project_id':project_id,
                                'notification_type':NotificationType.ERROR,
                                'importance':NotificationImportance.HIGH,
                                'notification_category':NotificationCategory.MODEL}
            
            self.send_notification(notification_obj=notification_obj)
            return LGBMResponse(exception_detail=str(e))
