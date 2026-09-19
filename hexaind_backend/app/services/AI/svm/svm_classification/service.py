import os
import sys
import json
from app.services.data.curation.data.source.model import DataSourceModel
import mlflow
import logging
import matplotlib
matplotlib.use("Agg")
import pandas as pd
from sklearn import svm
from datetime import datetime
from pymongo import MongoClient
import matplotlib.pyplot as plt
from motor.motor_asyncio import AsyncIOMotorClient
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    ConfusionMatrixDisplay,
    f1_score,
    confusion_matrix,
    classification_report,
)

from .svmc_helpers import resample
from ..dao import SVMDao
from ..schemas import *

from app.config.env_vars import environment as env
from app.services.notification.service import Notification
from app.services.notification.schema import (
    NotificationModel,
    NotificationType,
    NotificationCategory,
    NotificationImportance,
)
from app.services.AI.models.utils.model_utils import ModelUtils
from app.services.data.assets.datasets.schemas import Dataset, MachineLearningModel, AccessMode

logger = logging.getLogger(__package__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))


class SVMC:
    def __init__(
        self,
        db_sync_client: MongoClient = None,
        db_async_client: AsyncIOMotorClient = None,
    ) -> None:
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
            model = svm.SVC(
                kernel=svmr_config.kernel,
                C=svmr_config.C,
                gamma=svmr_config.gamma,
                class_weight="balanced",
            )
        elif svmr_config.kernel == "poly":
            model = svm.SVC(
                kernel=svmr_config.kernel,
                C=svmr_config.C,
                gamma=svmr_config.gamma,
                coef0=svmr_config.coef0,
                degree=svmr_config.degree,
                class_weight="balanced",
            )
        elif svmr_config.kernel == "sigmoid":
            model = svm.SVC(
                kernel=svmr_config.kernel,
                C=svmr_config.C,
                gamma=svmr_config.gamma,
                coef0=svmr_config.coef0,
                class_weight="balanced",
            )
        elif svmr_config.kernel == "linear":
            model = svm.SVC(
                kernel=svmr_config.kernel, C=svmr_config.C, class_weight="balanced"
            )

        return model

    def confusion_metrics_plot(self, confustion_matrix, conf_mat_file, model):
        logger.info("Inside cunfusion metrics plot")
        disp = ConfusionMatrixDisplay(
            confusion_matrix=confustion_matrix, display_labels=model.classes_
        )
        disp.plot()
        plt.savefig(conf_mat_file + ".png")
        plt.close()

    def pre_processing(self, data, svmr_config):

        # extracting the feature columns
        feature_columns = data.drop(columns=svmr_config.output_cols)
        # extracting the target columns
        target_columns = data[svmr_config.output_cols]

        cat_var_names = feature_columns.select_dtypes(
            ["object", "category"]
        ).columns.to_list()
        # Categorical variable encoding if categorical variables exist
        if len(cat_var_names) > 0:
            feature_columns = pd.get_dummies(
                feature_columns, columns=cat_var_names
            )  # One hot categorical encoding
            # feature_train_resampled = pd.get_dummies(feature_resampled, columns = cat_var_names)  #One hot categorical encoding

        sampler_type = (
            svmr_config.sampling
        )  # type of sampling used in case of target imbalance
        feature_resampled, target_resampled = resample(
            feature_columns, target_columns, sampler_type
        )

        # Standardize features by removing the mean and scaling to unit variance
        scaler = StandardScaler()
        feature_resampled_standardize = scaler.fit_transform(feature_resampled)

        return (
            feature_columns,
            target_columns,
            feature_resampled,
            target_resampled,
            feature_resampled_standardize,
        )

    def train_svmc(
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
        dataset_record:Dataset= None,
        widget_urn: str = None,
    ):
        try:
            logger.info("Inside SVM classification training method")
            # loading the data
            data = ModelUtils.read_data_for_training(dataset_record=dataset_record,data_path=data_path)

            # checking for empty data
            if data.empty:
                raise ValueError("Loaded data is empty")

            data = ModelUtils.check_and_drop_nan(data, svmr_config.input_cols + svmr_config.output_cols) 
            # pre processing
            (
                feature_columns,
                target_columns,
                feature_resampled,
                target_resampled,
                feature_resampled_standardize,
            ) = self.pre_processing(data, svmr_config)

            svm_model = self.set_model_configuration(svmr_config)

            # Set up MLflow
            mlflow.set_tracking_uri(
                env.mlflow_tracking_uri
            )  # Set this to your MLflow server's URI
            experiment_name = f"SVMC_{project_id}_{wf_id}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            mlflow.set_experiment(experiment_name)
            mlflow.set_tag("SVM version", "v1.0")
            mlflow.set_tag("Model type", "SVM")
            mlflow.set_tag("custom_run_id", run_id)
            with mlflow.start_run(nested=True) as run:
                model_name = f"svmc_model_{run.info.run_id}"
                model_path = os.path.join(result_folders, model_name)
                conf_mat_file = os.path.join(model_path, "SVM_confusion_matrix")
                os.makedirs(model_path, exist_ok=True)
                summary_file = os.path.join(model_path, "summary.csv")
                ml_model = dict(
                    user_id=user_id,
                    project_id=project_id,
                    site_id=site_id,
                    wf_run_id=run_id,
                    description="svmc model description",
                    created_at=datetime.now(),
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
                # creating notification
                notification_obj = {
                    "message": "SVM Classification Model training has started",
                    "category_id": wf_id,
                    "project_id": project_id,
                    "notification_type": NotificationType.INFO,
                    "importance": NotificationImportance.MEDIUM,
                    "notification_category": NotificationCategory.MODEL,
                }
                self.send_notification(notification_obj=notification_obj)
                logger.info("Model Training started")

                svm_model.fit(feature_resampled_standardize, target_resampled)

                target_pred = svm_model.predict(feature_columns)

                # Compute error metrics, should be saved as Tabular Data
                accuracy = accuracy_score(target_columns, target_pred)
                precision = precision_score(
                    target_columns, target_pred, average="weighted"
                )
                recall = recall_score(target_columns, target_pred, average="weighted")
                f1 = f1_score(target_columns, target_pred, average="weighted")
                conf_matrix = confusion_matrix(target_columns, target_pred)
                report = classification_report(
                    target_columns, target_pred, output_dict=True
                )

                mlflow.log_metrics(
                    {
                        "accuracy": accuracy,
                        "precision": precision,
                        "recall": recall,
                        "f1_score": f1,
                    }
                )

                model_det = dict(
                    testing_samples=0,
                    training_samples=data.shape[0],
                    configs=svmr_config.model_dump(),
                    dataset_name=dataset_name,
                )
                model_det["type"] = "SVM Classifier"

                summary = {
                    "accuracy": accuracy,
                    "precision": precision,
                    "recall": recall,
                    "f1_score": f1,
                    "confusion_matrix": conf_matrix.tolist(),
                    "report": report,
                }

                cat_var_names = feature_columns.select_dtypes(
                    ["object", "category"]
                ).columns.to_list()
                if len(cat_var_names) > 0:
                    summary["cat_var_names"] = cat_var_names

                model_obj = ml_model.copy()
                logger.info(ml_model)

                self.confusion_metrics_plot(conf_matrix, conf_mat_file, svm_model)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                model_det["name"] = f"{model_det['type']}_{timestamp}"
                model_det["feature_imp_plot"] = None
                model_det["metrics"] = report
                model_det["visualizations"] = [conf_mat_file + ".png"]
                model_obj["model"] = model_det
                model_obj["dataset_path"] = str(data_path)

                ml_model = MachineLearningModel(**model_obj)
                self.svmr_dao.insert_svm_record_sync(ml_model.model_dump())

                prediction = {"col_name": target_pred.tolist()}
                prediction_df = pd.DataFrame(prediction)
                all_ind = [i for i in range(data.shape[0])]
                summary["all_indices"] = json.dumps(all_ind)
                for col_name in prediction_df.columns:
                    # Convert the column data to a JSON string
                    json_string = json.dumps(prediction_df[col_name].tolist())
                    summary[col_name] = json_string

                model_summary_df = pd.DataFrame([summary])
                model_summary_df.to_csv(summary_file, index=False)
                mlflow.log_artifact(summary_file)
                mlflow.sklearn.log_model(svm_model, "model")
                artifact_final_path = os.path.join(result_folders, model_name)
                mlflow.artifacts.download_artifacts(run_id=run.info.run_id,dst_path=artifact_final_path)
                logger.info(f"Artifacts downloaded to: {artifact_final_path}")
            
                mlflow.end_run()
                notification_obj["message"] = (
                    "SVM Classification Model has been trained"
                )
                logger.info("Model Training ended")
                self.send_notification(notification_obj=notification_obj)

                return SVMRResponse(tabular_path=summary_file,models_path=os.path.join(artifact_final_path,"model"))

        except Exception as e:
            logger.error("Failed to train SVM model", exc_info=True)
            notification_obj = {
                "message": "SVM Classification Model training has failed",
                "category_id": wf_id,
                "project_id": project_id,
                "notification_type": NotificationType.ERROR,
                "importance": NotificationImportance.HIGH,
                "notification_category": NotificationCategory.MODEL,
            }

            self.send_notification(notification_obj=notification_obj)
            # print(e)
            #
            return SVMRResponse(exception_detail=str(e))
