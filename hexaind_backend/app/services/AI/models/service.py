import os
from re import S
import sys
import json
import mlflow
import torch
import joblib
import logging
import numpy as np
import pandas as pd
import dask.array as da
from pathlib import Path
from bson import ObjectId
from pymongo import MongoClient
from typing import Dict, List, Union
from motor.motor_asyncio import AsyncIOMotorClient
from sklearn.model_selection import train_test_split
from app.services.data.assets.datasets.schemas import (
    MachineLearningModel,
)
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    median_absolute_error,
    mean_absolute_percentage_error,
)

from .schemas import HighlightPointResponse
from .dao import ModelDao

from app.services.notification.service import Notification
from app.services.notification.schema import (
    NotificationModel,
    NotificationMessages,
    NotificationType,
    NotificationCategory,
    NotificationImportance,
)


logger = logging.getLogger(__package__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))


class GPCPrediction:
    def __init__(self, run_id):
        self.run_id = run_id
        self.load_gpc_prediction_data()

    def load_pytorch_model(self):
        # Load the PyTorch model
        model_uri = (
            f"runs:/{self.run_id}/model"  # Replace <run_id> with the actual run ID
        )
        self.model = mlflow.pytorch.load_model(model_uri)

    def download_artifacts(self, artifacts_path):
        # Download artifacts
        artifacts_uri = f"runs:/{self.run_id}/{artifacts_path}"
        artifacts_local_path = mlflow.artifacts.download_artifacts(
            artifact_uri=artifacts_uri
        )
        return artifacts_local_path

    def load_scaler(self, scaler_path):
        # Load the scaler
        self.scaler = joblib.load(scaler_path)

    def load_class_names(self, class_names_path):
        # Load the class names
        with open(class_names_path, "r") as f:
            self.class_names = json.load(f)

    def load_gpc_prediction_data(self):
        # Load the GPC model data
        self.load_pytorch_model()
        scaler_path = self.download_artifacts("scaler/scaler.pkl")
        class_names_path = self.download_artifacts("class_names/class_names.json")
        self.load_scaler(scaler_path)
        self.load_class_names(class_names_path)

    def predict(self, X):
        # Standardize the input data
        X_new_scaled = self.scaler.transform(X)

        # Convert to PyTorch tensor
        X_new_tensor = torch.from_numpy(X_new_scaled).float()

        # Ensure the model is in evaluation mode
        self.model.eval()

        # Ensure no gradients are computed during inference
        with torch.no_grad():
            # Get the predictive distribution
            predictive_distribution = self.model(X_new_tensor)

            # Extract mean predictions (logits)
            mean_predictions = predictive_distribution.mean

            # Get the predicted class indices (argmax of the mean predictions along the class dimension)
            predicted_class_indices = mean_predictions.argmax(dim=0)

        # Convert class indices to class names
        predicted_class_names = [
            self.class_names[idx] for idx in predicted_class_indices.numpy()
        ]

        return predicted_class_names


class AutoGluonPrediction(mlflow.pyfunc.PythonModel):

    def load_context(self, context):
        from autogluon.tabular import TabularPredictor

        self.predictor = TabularPredictor.load(context.artifacts.get("predictor_path"))

    def predict(self, context, model_input, params=None):
        if params is None:
            params = {}
        model_name = params.get("model_name", None)

        # Model input is expected to be in DataFrame format
        if isinstance(model_input, dict) and "dataframe_split" in model_input:
            model_input = pd.DataFrame(
                model_input["dataframe_split"]["data"],
                columns=model_input["dataframe_split"]["columns"],
            )

        return self._predict(model_input, model_name=model_name)

    def _predict(self, model_input, model_name=None):
        return self.predictor.predict(model_input, model=model_name)


def autogluon_log_model(
    predictor_path: str, mlflow_path: str = "model", model_name: str = None
):
    from mlflow.models import infer_signature

    artifacts = {"predictor_path": predictor_path}
    conda_env = {
        "channels": ["conda-forge"],
        "dependencies": ["python=3.10", "pip"],
        "pip": ["mlflow", "autogluon.tabular==0.4.0", "cloudpickle"],
        "name": "mlflow-env",
    }

    params = {"model_name": model_name}
    # params' default values are saved with ModelSignature
    signature = infer_signature(params=params)

    mlflow.pyfunc.log_model(
        artifact_path=mlflow_path,
        python_model=AutoGluonPrediction(),
        artifacts=artifacts,
        conda_env=conda_env,
        signature=signature,
    )


def categorical_encoding(
    df: pd.DataFrame,
    categ_labels: List = None,
    output_label: str = None,
    cat_encoding: str = "Onehot",
):
    categ_labels = df.select_dtypes(["object", "category", "string"]).columns.to_list()

    # One-hot encoding
    if cat_encoding == "Onehot" or cat_encoding == "One_hot":
        if len(categ_labels) > 0:
            # Getting the one hot encoding of categorical variables
            df = pd.get_dummies(df, categ_labels)

        return df

    # Mean encoding
    elif cat_encoding == "Mean":

        unique_categ_labels = (
            {}
        )  # Dictionary to store unique entries in categorical variables
        for categ in categ_labels:

            # Mean encoding the variable
            mean_encoded_subject = df.groupby(categ)[output_label].mean().to_dict()

            # Unique entries in categorical variables
            unique_categ_labels[categ] = mean_encoded_subject

            # Mapping values to categorical variables
            df[categ] = df[categ].map(mean_encoded_subject)

        return df, unique_categ_labels

    # Raising error if an invalid option for cat_encoding is entered
    else:
        logger.info("No encoding found")
        return df


# custom_train_test_split for dask base function
def custom_dask_train_test_split(
    x, y, test_size=0.2, split_type="Random", random_state=None
):
    """
    This function is useful for splitting the data either randomly or sequentially for dask objets
    and it will aslo return the indices of the train and test data poitns
    """

    # decide random or sequential
    shuffle = True if split_type == "Random" else False

    if shuffle:  # random split
        X_train, X_test, y_train, y_test, train_indices, test_indices = (
            train_test_split(
                x,
                y,
                da.arange(x.shape[0]),
                test_size=test_size,
                shuffle=True,
                random_state=random_state,
            )
        )
    else:  # sequential split
        X_train, X_test, y_train, y_test, train_indices, test_indices = (
            train_test_split(
                x,
                y,
                da.arange(x.shape[0]),
                test_size=test_size,
                shuffle=False,
                random_state=None,
            )
        )
    return X_train, X_test, y_train, y_test, train_indices, test_indices


# custom_train_test_split for sklearn base function
def custom_scikit_train_test_split(
    x, y, test_size=0.2, split_type="Random", random_state=None
):
    """
    This function is useful for splitting the data either randomly or sequentially for pandas or sklearn objects
    and it will aslo return the indices of the train and test data poitns
    """
    logger.debug(f"split type {str(split_type)}")
    # decide random or sequential
    shuffle = True if split_type == "Random" else False

    if shuffle:  # random split
        X_train, X_test, y_train, y_test, train_indices, test_indices = (
            train_test_split(
                x,
                y,
                np.arange(x.shape[0]),
                test_size=test_size,
                shuffle=True,
                random_state=random_state,
            )
        )
    else:  # sequential split
        X_train, X_test, y_train, y_test, train_indices, test_indices = (
            train_test_split(
                x,
                y,
                np.arange(x.shape[0]),
                test_size=test_size,
                shuffle=False,
                random_state=None,
            )
        )
    return X_train, X_test, y_train, y_test, train_indices, test_indices


def error_metrics_report(
    y_test: Union[pd.Series, np.ndarray, List[List]],
    y_pred: Union[pd.Series, np.ndarray, List[List]],
    multioutput: str = "uniform_average",
    cols_name: List[str] = [],
) -> Dict:

    # Convert inputs to numpy arrays if they aren't already
    y_test = np.array(y_test)
    y_pred = np.array(y_pred)

    # Calculate metrics
    mae = mean_absolute_error(y_test, y_pred, multioutput=multioutput)
    mse = mean_squared_error(y_test, y_pred, multioutput=multioutput)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred, multioutput=multioutput)
    mape = mean_absolute_percentage_error(y_test, y_pred, multioutput=multioutput) * 100
    medae = median_absolute_error(y_test, y_pred, multioutput=multioutput)

    # Initialize metrics report
    metrics_report = {}

    if multioutput == "raw_values" and cols_name:
        metrics_report = {
            "Mean Absolute Error (MAE)": dict(zip(cols_name, mae.tolist())),
            "Mean Squared Error (MSE)": dict(zip(cols_name, mse.tolist())),
            "Root Mean Squared Error (RMSE)": dict(zip(cols_name, rmse.tolist())),
            "R2 Score": dict(zip(cols_name, r2.tolist())),
            "Mean Absolute Percentage Error (MAPE)": dict(
                zip(cols_name, mape.tolist())
            ),
            "Median Absolute Error (MedAE)": dict(zip(cols_name, medae.tolist())),
        }
    else:
        metrics_report = {
            "Mean Absolute Error (MAE)": mae,
            "Mean Squared Error (MSE)": mse,
            "Root Mean Squared Error (RMSE)": rmse,
            "R2 Score": r2,
            "Mean Absolute Percentage Error (MAPE)": mape,
            "Median Absolute Error (MedAE)": medae,
        }

    return metrics_report


class ModelService:
    def __init__(
        self,
        db_sync_client: MongoClient = None,
        db_async_client: AsyncIOMotorClient = None,  # type: ignore
    ) -> None:
        self.modeldao = ModelDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )

    async def delete_previous_runs_models(self, project_id: str, run_id: str):
        query = {"project_id": project_id, "wf_run_id": run_id}
        logger.info(
            f"Deleting models for project_id: {project_id} and run_id: {run_id}"
        )
        await self.modeldao.delete_all_models(project_id=project_id, query=query)
        logger.info(f"Deleted models for project_id: {project_id} and run_id: {run_id}")

    async def unlink_wf_run_id_from_models(self, project_id: str, run_id: str):
        query = {"project_id": project_id, "wf_run_id": run_id}
        logger.info(
            f"Unlinking models for project_id: {project_id} and run_id: {run_id}"
        )
        await self.modeldao.unlink_wf_run_id_from_models(query=query)
        logger.info(
            f"Unlinked models for project_id: {project_id} and run_id: {run_id}"
        )

    async def save_and_update_models(
        self, models: List[MachineLearningModel], project_id: str
    ) -> Union[List[MachineLearningModel], List]:
        failed_models = []
        for model in models:
            model_json = model.model_dump()
            model_json["_id"] = ObjectId(model_json["id"])
            try:
                existing_doc = await self.modeldao.get_model_by_id_async(
                    model_id=model_json["_id"], project_id=project_id
                )
                data = {
                    "model.name": model_json["model"]["name"],
                    "access_mode": "EXTERNAL",
                }
                if existing_doc:
                    # If document exists, check if model.name matches
                    if (
                        existing_doc["model"]["name"] == model_json["model"]["name"]
                        and existing_doc["access_mode"] == "EXTERNAL"
                    ):
                        failed_models.append(model)
                        logger.debug(
                            f"A model with the name '{model_json['model']['name']}' already exists."
                        )
                    else:
                        # If _id exists but model.name is different, update model.name
                        await self.modeldao.update_model_async(
                            query={"_id": model_json["_id"]},
                            data=data,
                            col_name="models",
                        )
                        logger.info(
                            f"Updated model name: {model_json['model']['name']}"
                        )

            except:
                logger.debug(
                    f"A model with the name '{model_json['model']['name']}' failed to save."
                )
                failed_models.append(model)

        return failed_models

    async def load_viz_data(
        self,
        data,
        chosen_column,
        indices,
        predict_col,
        all_indices,
        output_col,
        pred_std,
    ):

        data = data.iloc[all_indices, :]
        chosen_feature_values_list = data[chosen_column].loc[indices].tolist()
        predicted_series = pd.Series(predict_col, index=all_indices)
        pred_std_series = None
        if pred_std.any():
            pred_std_series = pred_std.loc[indices].tolist()

        predicted_series = predicted_series.loc[indices]
        output_col_series = data[output_col].loc[indices]
        residual = predicted_series - output_col_series

        return {
            "prediction_parity": {
                "target_value": output_col_series.tolist(),
                "prediction_value": predicted_series.tolist(),
            },
            "chosen_residual": {
                "chosen_feature_values": chosen_feature_values_list,
                "residual_values": residual.tolist(),
            },
            "prediction_std": pred_std_series,
        }

    async def create_visualization(
        self,
        model: str,
        summary_path: str,
        data_path: str,
        chosen_column: str,
        output_col: str,
        split_ratio: int,
        data_type: str,
    ):

        if str(data_path).endswith("csv"):
            data = pd.read_csv(data_path)
        else:
            data = pd.read_parquet(data_path)

        drop_nan_cols = [chosen_column, output_col]
        if model != "XGBoost":
            data = self.drop_nan_zero_rows(
                data, drop_nan=True, output_label=None, drop_nan_cols=drop_nan_cols
            )
        summary_file = os.path.join(summary_path, "summary.csv")
        summary_df = pd.read_csv(summary_file)

        matching_index = summary_df[
            summary_df["model"].apply(lambda x: x in model)
        ].index
        f_matching_index = matching_index[0]
        predict_col = json.loads(
            summary_df.at[f_matching_index, f"predict_{output_col}"]
        )
        all_indices = json.loads(summary_df.at[f_matching_index, "all_indices"])
        std_col = f"std_{output_col}"
        pred_std_series = pd.Series()
        if std_col in summary_df.columns:
            pred_std_col = json.loads(summary_df.at[f_matching_index, std_col])
            pred_std_series = pd.Series(pred_std_col, index=all_indices)
        if data_type == "test":
            indices = json.loads(summary_df.at[f_matching_index, "test_indices"])

        if data_type == "train":
            indices = json.loads(summary_df.at[f_matching_index, "train_indices"])

        if data_type == "all":
            indices = json.loads(summary_df.at[f_matching_index, "test_indices"])
            test_data = await self.load_viz_data(
                data,
                chosen_column,
                indices,
                predict_col,
                all_indices,
                output_col,
                pred_std_series,
            )
            indices = json.loads(summary_df.at[f_matching_index, "train_indices"])
            train_data = await self.load_viz_data(
                data,
                chosen_column,
                indices,
                predict_col,
                all_indices,
                output_col,
                pred_std_series,
            )
            return {"test_data": test_data, "train_data": train_data}

        return await self.load_viz_data(
            data,
            chosen_column,
            indices,
            predict_col,
            all_indices,
            output_col,
            pred_std_series,
        )

    def drop_nan_zero_rows(
        self, df, drop_nan=True, output_label=None, drop_nan_cols=None
    ):

        # Dropping rows with nans
        if isinstance(drop_nan, bool) and drop_nan:
            if drop_nan_cols:
                df = df.dropna(subset=drop_nan_cols).reset_index(drop=True)
            else:
                df = df.dropna().reset_index(drop=True)
        else:
            raise ValueError("drop_nan parameter must be either True or False.")

        # Dropping rows with zero in the output value
        if output_label is None:  # No zero output row is dropped
            return df.reset_index(drop=True)
        elif output_label is not None and output_label in df.columns:
            return df[df[output_label] != 0].reset_index(drop=True)
        else:
            raise ValueError(
                "output_label must be either None or a label from the df.columns"
            )

    async def compare_models_visualization(self, project_id, models_config):
        compare_models_graph = []
        for config in models_config.models_config:
            models_graph = {
                "project_id": project_id,
                "summary_path": config.summary_path,
                "graph_data": {},
            }
            models_graph["graph_data"] = await self.create_visualization(
                config.model,
                config.summary_path,
                config.data_path,
                config.chosen_column,
                config.output_col,
                config.split_ratio,
                config.data_type,
            )
            compare_models_graph.append(models_graph)
        return compare_models_graph

    def calculate_residual_errors(self, obj):
        target = obj["Output (Target)"]
        prediction = obj["Output (Prediction)"]
        if isinstance(prediction, tuple):
            prediction = prediction[0]
        residual = prediction - target
        error_percentage = abs(residual / target)
        return round(residual, 4), round(error_percentage * 100, 4)

    def add_item_in_first_position_in_dict(
        self, d, new_pair, old_key
    ):  # insert a newPair (key, value) after old_key
        return {
            key: d.get(key, new_pair[1])
            for key in list(d.keys())[:0] + [new_pair[0]] + list(d.keys())[0:]
        }

    def highlighted_point_summary(
        self,
        model,
        summary_path,
        data_path,
        chosen_column,
        output_col,
        split_ratio,
        data_type,
        graph_name,
        coordinates,
    ):

        summary_file = os.path.join(summary_path, "summary.csv")
        summary_df = pd.read_csv(summary_file)
        drop_nan_cols = [chosen_column, output_col]
        data = pd.read_csv(data_path)
        data = self.drop_nan_zero_rows(
            data, drop_nan=True, output_label=None, drop_nan_cols=drop_nan_cols
        )

        matching_index = summary_df[
            summary_df["model"].apply(lambda x: x in model)
        ].index
        f_matching_index = matching_index[0]
        all_indices = json.loads(summary_df.at[f_matching_index, "all_indices"])
        if data_type == "test":
            indices = json.loads(summary_df.at[f_matching_index, "test_indices"])
        if data_type == "train":
            indices = json.loads(summary_df.at[f_matching_index, "train_indices"])
        if data_type == "all":
            indices = all_indices

        predict_col = json.loads(
            summary_df.at[f_matching_index, f"predict_{output_col}"]
        )
        predict_std_col = pd.Series()
        if f"std_{output_col}" in summary_df.columns:
            predict_std_col = json.loads(
                summary_df.at[f_matching_index, f"std_{output_col}"]
            )
            predict_std_col = pd.Series(predict_std_col, index=all_indices)
            predict_std_col = predict_std_col.loc[indices]
        data = data.iloc[all_indices, :]
        chosen_feature_values = data[chosen_column].loc[indices]
        predicted_series = pd.Series(predict_col, index=all_indices)
        predicted_series = predicted_series.loc[indices]
        output_col_series = data[output_col].loc[indices]
        residual = predicted_series - output_col_series

        # Create the dictionary using dictionary comprehension
        target_pred_dict = {
            (output_col_series[idx], predicted_series[idx]): idx
            for idx in output_col_series.index
        }
        residual_target_pred_dict = {
            (chosen_feature_values[idx], residual[idx]): idx for idx in residual.index
        }
        output_prediction = None
        row_num = None

        if graph_name == "parity":
            tar_tup_parity = (
                coordinates["target_x"],
                coordinates["prediction_y"],
            )  # in the form of (target,prediction).

            if tar_tup_parity in target_pred_dict:
                row_num = target_pred_dict[tar_tup_parity]
                # dataframe_row = data.iloc[row_num]
                # df = dataframe_row.to_frame().to_dict()
                data_to_be_sent = data.loc[row_num, :].to_dict()
                output_prediction = coordinates["prediction_y"]
            else:
                raise ValueError("Target point is not found")

        elif graph_name == "residual":
            tar_tup_residual = (
                coordinates["target_x"],
                coordinates["prediction_y"],
            )  # in the form of (feature,residual).

            if tar_tup_residual in residual_target_pred_dict:
                row_num = residual_target_pred_dict[tar_tup_residual]

                # dataframe_row = data.iloc[row_num]
                # df = dataframe_row.to_frame().to_dict()
                # data_to_be_sent = df[row_num]
                data_to_be_sent = data.loc[row_num, :].to_dict()
                for i in residual_target_pred_dict.items():
                    if i[0] == tar_tup_residual:
                        for j in target_pred_dict.items():
                            if j[1] == i[1]:
                                output_prediction = j[0][1]
                                break
            else:
                raise ValueError("Target point is not found")

        old_key = list(data_to_be_sent.keys())[0]
        output_target = data_to_be_sent[output_col]
        data_to_be_sent.pop(output_col)
        if predict_std_col.any():
            data_to_be_sent["Prediction Std"] = predict_std_col.loc[row_num]
        prediction_pair = ("Output (Prediction)", output_prediction)
        target_pair = ("Output (Target)", output_target)
        data_to_be_sent = self.add_item_in_first_position_in_dict(
            data_to_be_sent, prediction_pair, old_key
        )
        data_to_be_sent = self.add_item_in_first_position_in_dict(
            data_to_be_sent, target_pair, old_key
        )

        residual, error_percentage = self.calculate_residual_errors(
            {
                "Output (Target)": output_target,
                "Output (Prediction)": output_prediction,
            }
        )
        data_to_be_sent["Error Percentage"] = error_percentage
        data_to_be_sent["Residual"] = residual

        updated_dict = {
            "Output (Target)": data_to_be_sent.pop("Output (Target)"),
            "Output (Prediction)": data_to_be_sent.pop("Output (Prediction)"),
        }
        if "Prediction Std" in data_to_be_sent.keys():
            updated_dict.update(
                {"Output (Prediction) std": data_to_be_sent.pop("Prediction Std")}
            )

        updated_dict.update(data_to_be_sent)

        return updated_dict

    async def find_pickle_files(self, wf_run_id: str, project_id: str):

        models: List[MachineLearningModel] = await self.modeldao.get_models_by_run_id(
            run_id=wf_run_id, project_id=project_id
        )
        logger.info(f"{len(models)} found with run id {wf_run_id}")
        pkl_files = []
        base_dir = models[0]["ml_model_file_path"]
        base_path = Path(base_dir)
        logger.info(f"Base model directory - {base_path}")

        has_automl_model = (
            True if models[0]["model"]["configs"]["widget_type"] == "AUTOML" else False
        )
        if has_automl_model:
            base_path = base_path / "models"
            logger.info(f"AutoML directory - {base_path}")

        model_name = None
        for file_path in base_path.rglob("*.pkl"):
            relative_path = file_path.relative_to(base_path)

            if has_automl_model:
                logger.info("AUTOML")
                model_folder = relative_path.parts[0]
                model_name = model_folder
                logger.info(f"Model Name: {model_name}")
            else:
                model_folder = base_path.name
                model_name = f"{model_folder}_{file_path.stem}"  # Use folder name + file name (without extension)
                logger.info(f"Model Name: {model_name}")

            pkl_files.append(
                {
                    "model_name": model_name,  # Model name as defined
                    "file_path": str(file_path),  # Convert to string for compatibility
                }
            )

        joblib_files = list(base_path.rglob("*.joblib"))
        if joblib_files:
            for file_path in joblib_files:
                relative_path = file_path.relative_to(base_path)
                model_folder = base_path.name
                model_name = f"{model_folder}_{file_path.stem}"  # Use folder name + file name (without extension)
                logger.info(f"Model Name: {model_name}")

                pkl_files.append(
                    {
                        "model_name": model_name,  # Model name as defined
                        "file_path": str(
                            file_path
                        ),  # Convert to string for compatibility
                    }
                )

        return pkl_files, base_path
