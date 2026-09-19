import os
import sys
import json
from app.services.data.curation.data.source.model import DataSourceModel
import mlflow
import joblib
import logging
import datetime
import pandas as pd
from pathlib import Path
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient

from .dao import SVMDao
from .schemas import SVMRConfig, SVMRResponse
from .svmr_helpers import standardize_inputs_outputs, MSVR

from app.services.notification.service import Notification
from app.services.AI.models.service import error_metrics_report
from app.services.notification.schema import (
    NotificationModel,
    NotificationType,
    NotificationCategory,
    NotificationImportance,
)
from app.config.env_vars import environment as env
from app.services.AI.svm.svm_classification.service import SVMC
from app.services.AI.models.utils.model_utils import ModelUtils
from app.services.data.assets.datasets.schemas import Dataset, MachineLearningModel, AccessMode

logger = logging.getLogger(__package__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))


class SVMModelWrapper(mlflow.pyfunc.PythonModel):
    def __init__(self, model, x_scaler, y_scaler):

        self.model = model
        self.x_scaler = x_scaler
        self.y_scaler = y_scaler

    def predict(self, context, model_input):

        # Standardize the input data
        if self.x_scaler:
            model_input = self.x_scaler.transform(model_input)

        # Make predictions
        pred = self.model.predict(model_input)

        # Inverse transform the predictions
        if self.y_scaler:
            pred = self.y_scaler.inverse_transform(pred)

        return pred


class SVMRService:
    def __init__(
        self,
        db_sync_client: MongoClient = None,
        db_async_client: AsyncIOMotorClient = None,
    ) -> None:
        logger.info("Initializing SVMRService")
        self.svmr_dao = SVMDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )
        
        


    def send_notification(self, notification_obj):
        verified_notfication_obj = NotificationModel(**notification_obj)
        notification_service_obj = Notification(
            db_sync_client=self.svmr_dao.db_sync_client
        )
        notification_service_obj.create_notification_sync(verified_notfication_obj)

    def set_model_configuration(self, svmr_config):
        logger.info("Inside set model configutation")
        if svmr_config.kernel == "rbf":
            model = MSVR(
                kernel=svmr_config.kernel, C=svmr_config.C, gamma=svmr_config.gamma
            )
        elif svmr_config.kernel == "poly":
            model = MSVR(
                kernel=svmr_config.kernel,
                C=svmr_config.C,
                gamma=svmr_config.gamma,
                coef0=svmr_config.coef0,
                degree=svmr_config.degree,
            )
        elif svmr_config.kernel == "sigmoid":
            model = MSVR(
                kernel=svmr_config.kernel,
                C=svmr_config.C,
                gamma=svmr_config.gamma,
                coef0=svmr_config.coef0,
            )
        elif svmr_config.kernel == "linear":
            model = MSVR(kernel=svmr_config.kernel, C=svmr_config.C)
        return model

    def pre_processing(self, data, svmr_config):

        X = data[svmr_config.input_cols]
        y = data[svmr_config.output_cols]

        cat_var_names = X.select_dtypes(["object", "category", "string"]).columns.to_list()

        if len(cat_var_names) > 0:
            X = pd.get_dummies(X, columns=cat_var_names)  # One hot categorical encoding

        x_scaler, y_scaler, train_x, train_y = standardize_inputs_outputs(X, y)

        return X, y, x_scaler, y_scaler, train_x, train_y

    def train_svm(
        self,
        svmr_config: SVMRConfig,
        data_path: Path,
        result_folders: str,
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

            if svmr_config.problem_type == "classification":
                logger.info(f"Inside SVM classification training method")
                svmc_obj = SVMC(db_sync_client=self.svmr_dao.db_sync_client)
                response = svmc_obj.train_svmc(
                    svmr_config=svmr_config,
                    data_path=data_path,
                    result_folders=result_folders,
                    project_id=project_id,
                    wf_id=wf_id,
                    run_id=run_id,
                    dataset_name=dataset_name,
                    user_id=user_id,
                    site_id=site_id,
                    user_name=user_name,
                    dataset_record=dataset_record,
                    widget_urn=widget_urn,
                )
                return response

            logger.info(f"Inside SVM regression training method {svmr_config}")
            output_cols = svmr_config.output_cols
            y_cols = output_cols
            data = ModelUtils.read_data_for_training(dataset_record=dataset_record,data_path=data_path)

            data = ModelUtils.check_and_drop_nan(data, svmr_config.input_cols + y_cols)
            # preprocessing
            X, y, x_scaler, y_scaler, train_x, train_y = self.pre_processing(
                data, svmr_config
            )

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

            # Set up MLflow
            mlflow.set_tracking_uri(
                env.mlflow_tracking_uri
            )  # Set this to your MLflow server's URI

            experiment_name = f"SVM_{project_id}_{wf_id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            mlflow.set_experiment(experiment_name)
            mlflow.set_tag("SVMR version", "v1.0")
            mlflow.set_tag("Model type", "SVMR")
            mlflow.set_tag("custom_run_id", run_id)

            notification_obj = {
                "message": "SVM Regression Model training has started",
                "category_id": wf_id,
                "project_id": project_id,
                "notification_type": NotificationType.INFO,
                "importance": NotificationImportance.MEDIUM,
                "notification_category": NotificationCategory.MODEL,
            }

            model = self.set_model_configuration(svmr_config)
            logger.info("Creating MLFLOW experiment")

            with mlflow.start_run(nested=True) as run:
                model_name = f"svmr_model_{run.info.run_id}"
                model_path = os.path.join(result_folders, model_name)
                os.makedirs(model_path, exist_ok=True)
                scaler_x_path = os.path.join(model_path, "scaler_x.pkl")
                scaler_y_path = os.path.join(model_path, "scaler_y.pkl")
                summary_file = os.path.join(model_path, "summary.csv")
                ml_model = dict(
                    user_id=user_id,
                    project_id=project_id,
                    site_id=site_id,
                    wf_run_id=run_id,
                    description="svmr model description",
                    created_at=datetime.datetime.now(),
                    ml_model_file_path=model_path,
                    access_mode=AccessMode.INTERNAL,
                    tags=[],
                    user_name=user_name,
                    dataset_path=data_path,
                    widget_urn=widget_urn,
                )

                ml_model["ml_flow_detail"] = dict(
                    experiment_id=run.info.experiment_id,
                    experiment_name=experiment_name,
                    run_id=run.info.run_id,
                )

                params_dict = svmr_config.model_dump()
                mlflow.log_params(params_dict)
                model.fit(train_x, train_y)
                self.send_notification(notification_obj=notification_obj)
                logger.info("Model Training started")
                preds = model.predict(X)

                preds_orig = y_scaler.inverse_transform(preds)
                train_y = y_scaler.inverse_transform(train_y)

                if len(svmr_config.output_cols) > 1:
                    summary = error_metrics_report(y_test=train_y, y_pred=preds_orig, multioutput='raw_values', cols_name=svmr_config.output_cols)
                else:
                    summary = error_metrics_report(y_test=train_y, y_pred=preds_orig)
             
                model_det = dict(
                    testing_samples=0,
                    training_samples=data.shape[0],
                    configs=svmr_config.model_dump(),
                    dataset_name=dataset_name,
                )
                model_det["type"] = "SVM Regressor"

                
                cat_var_names = X.select_dtypes(
                    ["object", "category"]
                ).columns.to_list()
                if len(cat_var_names) > 0:
                    summary["cat_var_names"] = cat_var_names

                model_obj = ml_model.copy()
                model_det["name"] = f"{model_det['type']}_{timestamp}"

                model_det["name"] = f"{model_det['type']}_{timestamp}"
                model_det["feature_imp_plot"] = None
                model_det["metrics"] = summary
                model_obj["model"] = model_det
                logger.info(model_obj)
                ml_model = MachineLearningModel(**model_obj)
                self.svmr_dao.insert_svm_record_sync(ml_model.model_dump())

                prediction = {
                    col_name: [row[i] for row in preds_orig]
                    for i, col_name in enumerate(output_cols)
                }
                prediction_df = pd.DataFrame(
                    {
                        f"predict_{col_name}": values
                        for col_name, values in prediction.items()
                    }
                )
                all_ind = [i for i in range(data.shape[0])]
                summary["all_indices"] = json.dumps(all_ind)
                for col_name in prediction_df.columns:
                    # Convert the column data to a JSON string
                    json_string = json.dumps(prediction_df[col_name].tolist())
                    summary[col_name] = json_string
                model_summary_df = pd.DataFrame([summary])

                joblib.dump(x_scaler, scaler_x_path)
                joblib.dump(y_scaler, scaler_y_path)
                model_summary_df.to_csv(summary_file, index=False)
                mlflow.log_artifact(summary_file)
                mlflow.log_artifact(scaler_x_path, artifact_path="scaler_x")
                mlflow.log_artifact(scaler_y_path, artifact_path="scaler_y")
                svm_wrapper = SVMModelWrapper(model, x_scaler, y_scaler)
                mlflow.pyfunc.log_model(
                    artifact_path="model",
                    python_model=svm_wrapper,
                    artifacts={"scaler_x": scaler_x_path, "scaler_y": scaler_y_path},
                )
                artifact_final_path = os.path.join(result_folders, model_name)
                mlflow.artifacts.download_artifacts(run_id=run.info.run_id,dst_path=artifact_final_path)
                logger.info(f"Artifacts downloaded to: {artifact_final_path}")
            
                mlflow.end_run()
                logger.info(f"MLFLOW Experiment Completed")

                logger.info("Model Training ended")
                notification_obj["message"] = "SVM Regression Model has been trained"
                self.send_notification(notification_obj=notification_obj)

                return SVMRResponse(tabular_path=summary_file,models_path=os.path.join(artifact_final_path,"model"))

        except Exception as e:
            logger.error("SVM training failed", exc_info=True)

            notification_obj = {
                "message": "SVM Regression Model training has failed",
                "category_id": wf_id,
                "project_id": project_id,
                "notification_type": NotificationType.ERROR,
                "importance": NotificationImportance.HIGH,
                "notification_category": NotificationCategory.MODEL,
            }

            self.send_notification(notification_obj=notification_obj)
            return SVMRResponse(exception_detail=str(e))
