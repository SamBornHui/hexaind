# Original code with MLflow integration
import os
import sys
import json
import joblib
import mlflow
import logging
import textwrap
import datetime
import numpy as np
import pandas as pd
from typing import List
from pathlib import Path
from pymongo import MongoClient
from matplotlib import pyplot as plt
from motor.motor_asyncio import AsyncIOMotorClient

from .dao import XGBoosttDao
from .xgboost_helper import RegressionXGBoost
from .schemas import XGBoostConfig, XGBoostResponse

from app.services.AI.models.utils.model_utils import ModelUtils
from app.services.data.assets.datasets.schemas import (
    Dataset,
    MachineLearningModel,
    AccessMode,
)
from app.services.notification.service import Notification
from app.services.notification.schema import (
    NotificationModel,
    NotificationType,
    NotificationCategory,
    NotificationImportance,
)

from app.config.env_vars import environment as env

logger = logging.getLogger(__package__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))


class XGBModelWrapper(mlflow.pyfunc.PythonModel):
    def __init__(self, model, x_scaler):
        self.model = model
        self.x_scaler = x_scaler

    def predict(self, context, model_input):
        logger.debug("Predicting with XGBModelWrapper")
        # Standardize the input data
        X_scaled = model_input
        if self.x_scaler is not None:
            X_scaled = self.x_scaler.transform(model_input)

        preds = self.model.predict(X_scaled)

        return preds


class XGBoostService:
    def __init__(self, db_sync_client: MongoClient = None, db_async_client: AsyncIOMotorClient = None) -> None:  # type: ignore
        logger.debug("Initializing XGBoostService")
        self.xgb_dao = XGBoosttDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )

    def send_notification(self, notification_obj):
        logger.debug(f"Sending notification: {notification_obj}")
        verified_notfication_obj = NotificationModel(**notification_obj)
        notification_service_obj = Notification(
            db_sync_client=self.xgb_dao.db_sync_client
        )
        notification_service_obj.create_notification_sync(verified_notfication_obj)

    def plot_feature_importance(
        self, importances: np.ndarray, feature_names: List[str], save_path: str
    ):
        logger.debug("Plotting feature importance")
        logger.debug(f"feature importance {str(importances)}")
        order = np.argsort(
            importances.mean(axis=1)
        )  # order from lowest to highest mean importance
        importance = importances.mean(axis=1)
        wrapped_feature_names = np.array(
            [textwrap.fill(name, width=15) for name in feature_names]
        )
        # reorder: lowest to highest importance
        order = np.argsort(importance)
        # Determine figure height based on the number of features
        figure_height = 8  # Default height
        figure_width = 10  # Default width
        dynamic_adjust = 0.5 * len(feature_names)
        if dynamic_adjust > figure_height:
            figure_height = dynamic_adjust
            figure_width = dynamic_adjust

        # Set figure size
        plt.figure(figsize=(figure_width, figure_height))
        bars = plt.barh(wrapped_feature_names[order], importance[order], color="teal")
        plt.xlabel("Feature Importance")
        plt.ylabel("Features")
        plt.title("Feature importance - Permutation")
        # plt.gca().invert_yaxis()  # Highest importance at the top

        # Optional: Set alignment for better appearance
        for bar in bars:
            bar.set_edgecolor("none")  # Optional: Remove edge color to reduce clutter
            width = bar.get_width()
            label_x_pos = (
                width + 0.01 if width < 0.1 else width - 0.05
            )  # Adjust threshold (0.1) and position (-0.05) as needed
            alignment = "left" if width < 0.1 else "right"
            plt.text(
                label_x_pos,
                bar.get_y() + bar.get_height() / 2,
                f"{width:.3f}",
                va="center",
                ha=alignment,
                color="white" if width >= 0.1 else "black",
                weight="bold" if width >= 0.1 else "normal",
            )

        # Save the plot
        plt.savefig(save_path, bbox_inches="tight")
        plt.close()
        logger.debug(f"Feature importance plot saved to {save_path}")

    def train_xgb(
        self,
        ml_config: XGBoostConfig,
        data_path: Path,
        result_folders: Path,
        project_id: str,
        wf_id: str,
        run_id: str,
        dataset_name: str,
        user_id: str,
        site_id: str,
        user_name: str,
        dataset_record: Dataset = None,
        widget_urn: str = None,
    ) -> XGBoostResponse:
        try:
            logger.info("Starting XGBoost training process")

            # Verify data path and load data using pandas
            if not data_path.exists():
                raise FileNotFoundError(f"Data file not found at path: {data_path}")

            # if dataset_record:
            #     data = DataSourceModel.from_dataset(dataset_record).dataframe
            #     data = data.compute()
            # else:
            #     data = pd.read_csv(data_path)
            data = ModelUtils.read_data_for_training(
                dataset_record=dataset_record, data_path=data_path
            )

            if data.empty:
                raise ValueError("Loaded data is empty")

            total_cols = list(ml_config.input_cols)
            total_cols.append(ml_config.output_col)
            problem_type = ml_config.problem_type
            data = data[total_cols]
            X = data[ml_config.input_cols]
            y = data[ml_config.output_col]

            self.result_folders = result_folders
            # Set up MLflow
            mlflow.set_tracking_uri(
                env.mlflow_tracking_uri
            )  # Set this to your MLflow server's URI
            experiment_name = f"XGBoost_{project_id}_{wf_id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            mlflow.set_experiment(experiment_name)
            mlflow.set_tag("XGBoost version", "v1.0")
            mlflow.set_tag("Model type", "XGBoost")
            mlflow.set_tag("custom_run_id", run_id)
            flat_params_dict = ModelUtils.flatten_dict(ml_config.model_dump())
            notification_obj = {
                "message": "XG_Boost Model training has started",
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
                description="XGBoost model description",
                created_at=datetime.datetime.now(),
                ml_model_file_path=None,
                access_mode=AccessMode.INTERNAL,
                tags=[],
                user_name=user_name,
                dataset_path=str(data_path),
                widget_urn=widget_urn,
            )

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            with mlflow.start_run(nested=True) as run:
                model_name = f"XGBoost_model_{run.info.run_id}"
                model_path = os.path.join(result_folders, model_name)
                os.makedirs(model_path, exist_ok=True)
                scaler_x_path = os.path.join(model_path, "scaler_x.pkl")
                summary_file = os.path.join(model_path, "summary.csv")
                feature_importance_path = os.path.join(
                    model_path,
                    f"XGB_{ml_config.output_col}_feature_imp_{timestamp}.png",
                )
                self.ml_model["ml_model_file_path"] = model_path
                self.ml_model["ml_flow_detail"] = dict(
                    experiment_id=run.info.experiment_id,
                    experiment_name=experiment_name,
                    run_id=run.info.run_id,
                )
                # self.send_notification(notification_obj=notification_obj)
                mlflow.log_params(flat_params_dict)
                logger.info("Training XGBoost model")
                model = RegressionXGBoost(X, y, **ml_config.hyper_params.model_dump())
                model.preprocess_xgboost()
                model.train_xgb()
                importances = model.feature_importance()
                feature_name = ml_config.input_cols
                # if model.cat_var_names:
                #     feature_name = model.encoded_feature_names
                self.plot_feature_importance(
                    importances,
                    feature_name,
                    feature_importance_path,
                )

                summary = ModelUtils.error_metrics_report(model.y_test, model.yh_test)
                for key, value in summary.items():
                    if isinstance(value, np.float32):
                        summary[key] = round(float(value), 3)
                self.model_detail = dict(
                    testing_samples=model.X_test.shape[0],
                    training_samples=model.X_train.shape[0],
                    configs=ml_config.model_dump(),
                    dataset_name=dataset_name,
                    name=f"XGBoost_{timestamp}",
                    type="XGBoost",
                    metrics=summary,
                    cv_metrics=model.cv_metrics,
                    feature_imp_plot=feature_importance_path,
                )

                self.ml_model["model"] = self.model_detail

                ml_model = MachineLearningModel(**self.ml_model)
                self.xgb_dao.insert_record_sync(ml_model.model_dump())

                all_ind = model.all_ind
                input_all = pd.concat([model.X_train, model.X_test])
                if (
                    ml_config.hyper_params.split_ratio == 100
                    or ml_config.hyper_params.split_ratio == 0
                ):
                    # all_ind = model.all_ind
                    input_all = model.X_train

                pred_all = model.XGB.predict(input_all)
                summary["all_indices"] = json.dumps(all_ind)
                summary["train_indices"] = json.dumps(model.train_ind)
                summary["test_indices"] = json.dumps(model.test_ind)
                summary["model"] = self.model_detail["type"]
                column_name = f"predict_{ml_config.output_col}"
                summary[column_name] = json.dumps(pred_all.tolist())
                model_summary_df = pd.DataFrame([summary])
                joblib.dump(model.scaling_func, scaler_x_path)
                # Save model and necessary information
                dict_out = dict()
                dict_out["model"] = model.XGB
                dict_out["x_scaler"] = model.scaling_func
                dict_out["cat_var_names"] = model.cat_var_names
                dict_out["x_vars"] = ml_config.input_cols
                dict_out["y_vars"] = ml_config.output_col
                joblib.dump(
                    dict_out, filename=os.path.join(model_path, "xgb_model.joblib")
                )
                model_summary_df.to_csv(summary_file, index=False)

                mlflow.log_artifact(scaler_x_path, artifact_path="scaler_x")
                wrapped_model = XGBModelWrapper(
                    model=model.XGB, x_scaler=model.scaling_func
                )
                mlflow.pyfunc.log_model(
                    artifact_path="model",
                    python_model=wrapped_model,
                    artifacts={"scaler_x": scaler_x_path},
                )
                mlflow.log_artifact(summary_file)

                artifact_name = f"XGBoost_model_{run.info.run_id}"
                artifact_final_path = os.path.join(result_folders, artifact_name)
                artifact_path = ""
                client = mlflow.tracking.MlflowClient()

                # Get the artifact URI
                client.download_artifacts(
                    run_id=run.info.run_id,
                    path=artifact_path,
                    dst_path=artifact_final_path,
                )
                artifact_final_path = os.path.join(result_folders, model_name)
                mlflow.artifacts.download_artifacts(
                    run_id=run.info.run_id, dst_path=artifact_final_path
                )
                logger.info(f"Artifacts downloaded to: {artifact_final_path}")

            mlflow.end_run()
            logger.info("XGBoost model training completed successfully")

            notification_obj["message"] = "Model XG_Boost has been trained"
            # self.send_notification(notification_obj=notification_obj)

            return XGBoostResponse(
                tabular_path=summary_file, models_path=artifact_final_path
            )

        except Exception as e:
            logger.exception(
                f"Error in training XGBoost model: {str(e)}", exc_info=True
            )
            notification_obj = {
                "message": "XG_Boost Model training has failed",
                "category_id": wf_id,
                "project_id": project_id,
                "notification_type": NotificationType.ERROR,
                "importance": NotificationImportance.HIGH,
                "notification_category": NotificationCategory.MODEL,
            }

            # self.send_notification(notification_obj=notification_obj)
            return XGBoostResponse(exception_detail=str(e))
