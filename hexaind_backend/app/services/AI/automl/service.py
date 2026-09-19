import matplotlib
matplotlib.use("Agg")
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
import logging
import mlflow
import traceback
import numpy as np
import torch
from autogluon.tabular import TabularPredictor
from matplotlib import pyplot as plt
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from sklearn.metrics import ConfusionMatrixDisplay, classification_report
import traceback

from .dao import AutoMLDao
from .schemas import AutoMLConfig, AutoMLResponse
from .automl_reg.service import AutoMLRegService
from .automl_cls.service import AutoMLClsService

from app.services.AI.models.utils.model_utils import ModelUtils
from app.services.AI.models.service import autogluon_log_model, error_metrics_report
from app.config.env_vars import environment as env
from app.services.data.assets.datasets.schemas import AccessMode, Dataset, MachineLearningModel
from app.services.notification.schema import (
    NotificationCategory,
    NotificationImportance,
    NotificationModel,
    NotificationType,
)
from app.services.notification.service import Notification

logger = logging.getLogger(__package__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))

class AutoMLService:
    def __init__(self, db_sync_client: MongoClient = None, db_async_client: AsyncIOMotorClient = None) -> None:  # type: ignore
        logger.info("Initializing AutoMLService")
        self.automl_dao = AutoMLDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )

    def send_notification(self, notification_obj):
        logger.info(f"Sending notification: {notification_obj['message']}")
        verified_notfication_obj = NotificationModel(**notification_obj)
        notification_service_obj = Notification(
            db_sync_client=self.automl_dao.db_sync_client
        )
        notification_service_obj.create_notification_sync(verified_notfication_obj)

    

    def train_automl(
        self,
        ml_config: AutoMLConfig,
        data_path: Path,
        result_folders: Path,
        project_id: str,
        wf_id: str,
        run_id: str,
        dataset_name: str,
        user_id: str,
        site_id: str,
        user_name: str,
        dataset_record: Dataset=None,
        widget_urn: str=None,
    ):

        try:
            logger.info("Starting Auto_ML training")
            logger.info(f"Auto_ML configuration {str(ml_config)}")

            if not data_path.exists():
                raise FileNotFoundError(f"Data file not found at path: {data_path}")

            if ml_config.problem_type == "classification":
                logger.info("Preprocessing for classification")
                data, train_data, test_data = AutoMLClsService.preprocess_automl_cls(
                    data_path,
                    ml_config.input_cols,
                    ml_config.output_col,
                    ml_config.split_ratio,
                    dataset_record,

                )
                hyperparameters = (
                    ml_config.automl_config.automl_hyperparameters_cls.model_dump()
                )
                eval_metrics = ml_config.automl_config.evaluation_metric_cls

            else:
                logger.info("Preprocessing for regression")
                data, train_data, test_data = AutoMLRegService.preprocess_automl_reg(
                    data_path,
                    ml_config.input_cols,
                    ml_config.output_col,
                    ml_config.split_ratio,
                    dataset_record,
                )
                hyperparameters = (
                    ml_config.automl_config.automl_hyperparameters.model_dump()
                )
                eval_metrics = ml_config.automl_config.evaluation_metric

            

            self.problem_type = ml_config.problem_type
            hyperparameter_tune_kwargs = (
                ml_config.additional_hyperparameter_tune_kwargs.model_dump()
            )

            self.result_folders = result_folders
            self.extra_metrics = [eval_metrics]

            mlflow.set_tracking_uri(
                env.mlflow_tracking_uri
            )
            logger.info("Creating MLFLOW experiment")
            experiment_name = f"AutoML_{ml_config.problem_type}_{project_id}_{wf_id}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            mlflow.set_experiment(experiment_name)
            mlflow.set_tag(f"AutoML {ml_config.problem_type} version", "v1.0")
            mlflow.set_tag("Model type", f"AutoML {ml_config.problem_type}")
            mlflow.set_tag("custom_run_id", run_id)
            flat_params_dict = ModelUtils.flatten_dict(ml_config.model_dump())
            notification_obj = {
                "message": f"AutoML {ml_config.problem_type} Model training has started",
                "category_id": wf_id,
                "project_id": project_id,
                "notification_type": NotificationType.INFO,
                "importance": NotificationImportance.MEDIUM,
                "notification_category": NotificationCategory.MODEL,
            }

            self.ml_model = dict(
                user_id=user_id,
                project_id=project_id,
                site_id=site_id,
                wf_run_id=run_id,
                description=f"AutoML {ml_config.problem_type} model description",
                created_at=datetime.now(timezone.utc),
                ml_model_file_path=None,
                access_mode=AccessMode.INTERNAL,
                tags=[],
                user_name=user_name,
                dataset_path=str(data_path),
                widget_urn=widget_urn,
            )
            self.model_detail = dict(
                testing_samples=test_data.shape[0],
                training_samples=train_data.shape[0],
                configs=ml_config.model_dump(),
                dataset_name=dataset_name,
            )
            logger.info("Starting MLFLOW experiment")
            with mlflow.start_run(nested=True) as run:
                model_name = f"AutoML_{ml_config.problem_type}_model_{run.info.run_id}"
                model_path = os.path.join(result_folders, model_name)
                os.makedirs(model_path, exist_ok=True)
                self.ml_model["ml_model_file_path"] = model_path
                self.summary_file = os.path.join(model_path, "summary.csv")
                self.ml_model["ml_flow_detail"] = dict(
                    experiment_id=run.info.experiment_id,
                    experiment_name=experiment_name,
                    run_id=run.info.run_id,
                )
                self.send_notification(notification_obj=notification_obj)
                mlflow.log_params(flat_params_dict)
                predictor = ModelUtils.train_and_log_models(data=data, train_data=train_data, test_data=test_data, hyperparameters=hyperparameters, eval_metric=eval_metrics, label=ml_config.output_col, model_path=model_path, hyperparameter_tune_kwargs=hyperparameter_tune_kwargs, problem_type=ml_config.problem_type, model_detail=self.model_detail, extra_metrics=self.extra_metrics, db_sync_client=self.automl_dao.db_sync_client, ml_model_obj=self.ml_model)
                predictor.save()
                autogluon_log_model(model_path, model_name=predictor.model_names()[0])
                mlflow.log_artifact(self.summary_file)
                artifact_final_path = os.path.join(result_folders, model_name) 
                mlflow.artifacts.download_artifacts(run_id=run.info.run_id, dst_path=artifact_final_path)
            
            logger.info(f"MLFLOW Experiment Completed")

            mlflow.end_run()

            notification_obj["message"] = (
                f"Model AutoML {ml_config.problem_type} has been trained"
            )
            self.send_notification(notification_obj=notification_obj)

            return AutoMLResponse(
                exception_detail=None, tabular_path=Path(self.summary_file),models_path=os.path.join(artifact_final_path,"model")
            )

        except Exception as e:
            # traceback.print_exc()
            logger.error("AutoML training failed", exc_info=True)
            notification_obj = {
                "message": "AutoML Cls Model training has failed",
                "category_id": wf_id,
                "project_id": project_id,
                "notification_type": NotificationType.ERROR,
                "importance": NotificationImportance.HIGH,
                "notification_category": NotificationCategory.MODEL,
            }

            self.send_notification(notification_obj=notification_obj)
            return AutoMLResponse(exception_detail=str(e))
