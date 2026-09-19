import os
import sys
import json
import joblib
import mlflow
import logging
import textwrap
import numpy as np
import pandas as pd
import mlflow.pyfunc
from typing import List
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient

from .dao import MPRDao
from .mpr_model import RegressionMPR
from .schemas import MPRConfig, MPRResponse

from app.config.env_vars import environment as env
from app.services.data.assets.datasets.schemas import (
    AccessMode,
    Dataset,
    MachineLearningModel,
)
from app.services.AI.models.utils.model_utils import ModelUtils
from app.services.notification.service import Notification
from app.services.notification.schema import (
    NotificationModel,
    NotificationType,
    NotificationCategory,
    NotificationImportance,
)


logger = logging.getLogger(__package__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))


class MPRPrediction(mlflow.pyfunc.PythonModel):
    def __init__(self, model):
        self.model = model

    def predict(self, context, model_input):
        logger.debug("Predicting with MPRPrediction")
        # Standardize the input data
        preds = self.model.predict(model_input)

        return preds


class MPRService:
    def __init__(self, db_sync_client: MongoClient = None, db_async_client: AsyncIOMotorClient = None) -> None:  # type: ignore
        self.mpr_dao = MPRDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )

    def plot_feature_importance(
        self,
        importances: np.ndarray,
        feature_names: List[str],
        save_path: str,
    ):
        logger.debug("Plotting feature importance")
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
        plt.title(f"Feature importance - Permutation")
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

    def send_notification(self, notification_obj):
        verified_notfication_obj = NotificationModel(**notification_obj)
        notification_service_obj = Notification(
            db_sync_client=self.mpr_dao.db_sync_client
        )
        notification_service_obj.create_notification_sync(verified_notfication_obj)

    def flatten_dict(self, d, parent_key="", sep="."):
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def train_mpr(
        self,
        mpr_config: MPRConfig,
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
    ):
        try:
            # data collection
            logger.info("Inside NPR training")
            logger.info(f"mpr_configuration:{str(mpr_config)}")
            if not data_path.exists():
                raise FileNotFoundError(f"Data file not found at path: {data_path}")

            collected_data = ModelUtils.read_data_for_training(
                dataset_record=dataset_record, data_path=data_path
            )

            if collected_data.empty:
                raise ValueError("collected_data data is empty")

            # removing null values
            all_columns: List = mpr_config.input_cols.copy()
            all_columns.append(mpr_config.output_col)

            required_data = ModelUtils.check_and_drop_nan(collected_data, all_columns)

            # seperating feature ==>  columns X and target ==> columns Y
            X = required_data[mpr_config.input_cols]
            y = required_data[mpr_config.output_col]

            logger.info("Setting ML_flow Experiment")
            mlflow.set_tracking_uri(
                env.mlflow_tracking_uri
            )  # Set this to your MLflow server's URI
            experiment_name = (
                f"MPR_{project_id}_{wf_id}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            )
            mlflow.set_experiment(experiment_name)
            mlflow.set_tag("MPR version", "v1.0")
            mlflow.set_tag("Model type", "MPR")
            mlflow.set_tag("custom_run_id", run_id)
            flat_params_dict = self.flatten_dict(mpr_config.model_dump())
            notification_obj = {
                "message": "MPR Model training has started",
                "category_id": wf_id,
                "project_id": project_id,
                "notification_type": NotificationType.INFO,
                "importance": NotificationImportance.MEDIUM,
                "notification_category": NotificationCategory.MODEL,
            }

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.ml_model = dict(
                user_id=user_id,
                project_id=project_id,
                site_id=site_id,
                wf_run_id=run_id,
                description="MPR model description",
                created_at=datetime.now(),
                ml_model_file_path=None,
                access_mode=AccessMode.INTERNAL,
                tags=[],
                user_name=user_name,
                dataset_path=str(data_path),
                widget_urn=widget_urn,
            )
            self.model_detail = dict(
                type="MPR",
                name=f"{mpr_config.output_col}_MPR_{timestamp}",
                configs=mpr_config.model_dump(),
                dataset_name=dataset_name,
            )

            logger.info("Starting ML_flow Experiment")
            with mlflow.start_run(nested=True) as run:
                model_name = f"MPR_model_{run.info.run_id}"
                model_path = os.path.join(result_folders, model_name)
                os.makedirs(model_path, exist_ok=True)
                self.summary_file = os.path.join(model_path, "summary.csv")
                self.ml_model["ml_model_file_path"] = model_path
                self.feature_imp_plot = os.path.join(
                    self.ml_model["ml_model_file_path"], "MPR_feature_imp.png"
                )

                self.ml_model["ml_flow_detail"] = dict(
                    experiment_id=run.info.experiment_id,
                    experiment_name=experiment_name,
                    run_id=run.info.run_id,
                )

                mlflow.log_params(flat_params_dict)

                self.send_notification(notification_obj=notification_obj)

                logger.info("Starting model training ")
                ###############################################################################
                # Set up model
                if mpr_config.polynomial_degree_feature:

                    pd_value = [
                        x.feature_value for x in mpr_config.polynomial_degree_feature
                    ]
                else:
                    pd_value = mpr_config.polynomial_degree
                logger.info(f"shape of X {str(X.shape)}")
                logger.info(f"shape of y {str(y.shape)}")

                self.mpr_regression_obj = RegressionMPR(
                    X=X,
                    y=y,
                    split_type=mpr_config.split_type,
                    PD=pd_value,
                    CV_folds=mpr_config.cross_validation_folds,
                    split_ratio=mpr_config.split_ratio / 100,
                    split_random_state=mpr_config.random_state,
                    use_dask=False,
                    dr_basis=None,
                    n_models=20,
                    cat_encoding=mpr_config.categorical_encoding,
                    input_scaling=mpr_config.input_scaling,
                )
                ###############################################################################

                if self.mpr_regression_obj.premature_exit:  ###underfit case
                    return MPRResponse(
                        exception_detail=self.mpr_regression_obj.premature_exit_msg
                    )

                self.model_detail["feature_imp_plot"] = self.feature_imp_plot
                self.model_detail["testing_samples"] = (
                    self.mpr_regression_obj.X_test.shape[0]
                )
                self.model_detail["training_samples"] = (
                    self.mpr_regression_obj.X_train.shape[0]
                )

                # ploting feature importance
                importances = self.mpr_regression_obj.feature_importance()
                feature_name = mpr_config.input_cols
                # if mpr_config.categorical_encoding:
                #     feature_name = self.mpr_regression_obj.X_train.columns
                self.plot_feature_importance(
                    importances,
                    feature_name,
                    self.feature_imp_plot,
                )

                if mpr_config.split_ratio == 0:
                    prediction = self.mpr_regression_obj.yh_train
                else:
                    prediction = np.concatenate(
                        (
                            self.mpr_regression_obj.yh_train,
                            self.mpr_regression_obj.yh_test,
                        ),
                        axis=0,
                    )

                metrics_report = self.mpr_regression_obj.metrics_report
                cv_metrics = self.mpr_regression_obj.cv_metrics
                summary = metrics_report.copy()

                self.model_detail["metrics"] = summary.copy()
                self.model_detail["cv_metrics"] = cv_metrics
                # all_ind = self.mpr_regression_obj.train_ind.tolist() + self.mpr_regression_obj.test_ind.tolist()
                summary["all_indices"] = json.dumps(self.mpr_regression_obj.all_ind)
                summary["train_indices"] = json.dumps(self.mpr_regression_obj.train_ind)
                summary["test_indices"] = json.dumps(self.mpr_regression_obj.test_ind)
                summary["model"] = self.model_detail["type"]

                logger.info(f"prediction:{str(prediction)}")

                predict_col = "predict_" + mpr_config.output_col
                summary[predict_col] = json.dumps(prediction.tolist())

                model_summary_df = pd.DataFrame([summary])

                model_summary_df.to_csv(self.summary_file, index=False)

                self.ml_model["model"] = self.model_detail

                ml_model = MachineLearningModel(**self.ml_model)
                self.mpr_dao.insert_record_sync(ml_model.model_dump())
                # Convert the dictionary to a DataFrame

                # loggin the tranformer class
                x_scaler = None
                if hasattr(self.mpr_regression_obj, "scaling_func"):
                    # # Log and the scaler and class names as artifacts
                    x_scaler = self.mpr_regression_obj.scaling_func
                    scaler_path = os.path.join(model_path, "scaler.pkl")
                    joblib.dump(x_scaler, scaler_path)
                    mlflow.log_artifact(scaler_path, artifact_path="scaler_x")

                # Save model and necessary information
                dict_out = dict()
                dict_out["model"] = self.mpr_regression_obj
                dict_out["x_scaler"] = x_scaler
                x_cols = X.columns.to_list()
                set1 = set(x_cols)
                set2 = set(mpr_config.input_cols)
                difference = list(set1.symmetric_difference(set2))
                if difference:
                    dict_out["cat_var_names"] = difference
                dict_out["x_vars"] = mpr_config.input_cols
                dict_out["y_vars"] = mpr_config.output_col
                joblib.dump(
                    dict_out, filename=os.path.join(model_path, "mpr_model.joblib")
                )

                mlflow.log_artifact(self.feature_imp_plot)

                mpr_prediction_model = MPRPrediction(model=self.mpr_regression_obj)
                mlflow.pyfunc.log_model(
                    artifact_path="model",
                    python_model=mpr_prediction_model,
                    artifacts={"scaler_x": scaler_path},
                )

                mlflow.log_artifact(self.summary_file)
                artifact_final_path = os.path.join(result_folders, model_name)
                mlflow.artifacts.download_artifacts(run_id=run.info.run_id,dst_path=artifact_final_path)
                logger.info(f"Artifacts downloaded to: {artifact_final_path}")
                mlflow.end_run()
                notification_obj["message"] = "Model MPR has been trained"
                self.send_notification(notification_obj=notification_obj)

            return MPRResponse(
                tabular_path=self.summary_file, models_path=os.path.join(artifact_final_path,"model")
            )

        except Exception as e:
            logger.error(f"Failed to trained model {str(e)}", exc_info=True)
            notification_obj = {
                "message": "MPR Model training has failed",
                "category_id": wf_id,
                "project_id": project_id,
                "notification_type": NotificationType.ERROR,
                "importance": NotificationImportance.HIGH,
                "notification_category": NotificationCategory.MODEL,
            }

            self.send_notification(notification_obj=notification_obj)
            return MPRResponse(exception_detail=str(e))
