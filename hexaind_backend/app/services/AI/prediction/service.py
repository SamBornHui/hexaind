import os
import sys
from app.services.data.curation.data.source.model import DataSourceModel
import mlflow
import psutil
import asyncio
import socket
import signal
import logging
import subprocess
import socket
import requests
import json
import time
import pandas as pd
from bson import ObjectId
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient

from .dao import PredictionDao
from .schemas import DeployModel, PredictionConfig, PredictionResponse

from app.services.AI.models.service import categorical_encoding
from app.services.data.assets.datasets.schemas import Dataset, DeployedStatus
from app.services.data.assets.datasets.schemas import MachineLearningModel
from app.services.notification.service import Notification
from app.services.notification.schema import (
    NotificationCategory,
    NotificationImportance,
    NotificationType,
    NotificationModel,
)
from app.services.AI.models.utils.model_utils import ModelUtils

logger = logging.getLogger(__package__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))


class PredictionService:
    def __init__(self, db_sync_client: MongoClient = None, db_async_client: AsyncIOMotorClient = None) -> None:  # type: ignore
        logger.info("Initializing Prediction Service")
        self.prediction_dao = PredictionDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )

    def send_notification(self, notification_obj):
        logger.info(f"Sending notification: {notification_obj['message']}")
        verified_notfication_obj = NotificationModel(**notification_obj)
        notification_service_obj = Notification(
            db_sync_client=self.prediction_dao.db_sync_client
        )
        notification_service_obj.create_notification_sync(verified_notfication_obj)

    async def redeploy_models(self):
        logger.info("Redeploying Models")
        query = {"ml_deployed_status.status": "deployed"}
        dep_models = await self.prediction_dao.get_all_document(query=query)
        for model in dep_models:
            try:
                logger.info(f"checking if xgboost model is found")
                if "XGBoost/" in model["model"]["type"]:
                    query = {"_id": ObjectId(model["_id"])}
                    logger.info(f"deleting model {model['_id']} of xgboost")
                    await self.prediction_dao.delete_document(query, "models")
                    logger.info(f"model {model['_id']} of xgboost deleted")
                else:
                    model_uri = f"runs:/{model['ml_flow_detail']['run_id']}/model"
                    if not await self.find_process_using_port(
                        port=model["ml_deployed_status"]["port"]
                    ):
                        port = model["ml_deployed_status"]["port"]
                        command = [
                            "mlflow",
                            "models",
                            "serve",
                            "-m",
                            model_uri,
                            "-p",
                            str(port),
                            "-h",
                            "0.0.0.0",
                            "--no-conda",
                        ]
                        if not self.serve_model(command, port=port):
                            logger.debug(f"Error redeploying model {model['_id']}")
                            query = {"_id": ObjectId(model["_id"])}
                            await self.prediction_dao.delete_document(query, "models")
                    else:
                        logger.info("Model is already deployed")
            except:
                logger.debug(f"Error redeploying model {model['_id']}")
                model["ml_deployed_status"]["status"] = "trained"
                model["ml_deployed_status"]["port"] = None
                await self.prediction_dao.update_document(
                    {"_id": ObjectId(model["_id"])}, model, "models"
                )

    def find_empty_ports(self):
        start_port = 5001  # Replace with your desired start port
        end_port = 5400  # Replace with your desired end port
        for port in range(start_port, end_port + 1):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                result = s.connect_ex(("0.0.0.0", port))
                if result != 0:  # Non-zero result indicates the port is not in use
                    return port

    def serve_model(self, command, port, timeout=30):

        # Launch the serving process
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        start_time = time.time()
        while True:
            # Check if the process has completed
            retcode = process.poll()
            if retcode is not None:
                if retcode == 0:
                    # Process completed successfully
                    logger.info(
                        "Process completed successfully but did not start serving."
                    )
                    return 0
                else:
                    # Process failed, handle the error
                    stdout, stderr = process.communicate()
                    logger.info("Failed to deploy model: %s", stderr.decode().strip())
                    return 0

            # Check if the port is active
            if self.find_process_using_port_sync(port):
                logger.info("Model is successfully served.")
                return 1

            # If the timeout has been reached, terminate the process and raise an error
            if (time.time() - start_time) > timeout:
                process.terminate()
                stdout, stderr = process.communicate()
                logger.info(
                    "Failed to deploy model timeout: %s", stderr.decode().strip()
                )
                return 0

            logger.debug("Waiting for model to be served...")
            time.sleep(1)

    async def deploy_model(self, deploy_model: DeployModel):
        model = await self.prediction_dao.get_document(
            {"_id": ObjectId(deploy_model.ml_id)}, "models"
        )
        logger.info(f"model:  {model}")
        if model:
            model_name = model["ml_flow_detail"]["experiment_name"]
            run_id = model["ml_flow_detail"]["run_id"]
            model_uri = f"runs:/{run_id}/model"

            ## comment out this for now may be used in future
            # mlflow.register_model(model_uri, model_name)
            # client = mlflow.tracking.MlflowClient()
            # client.transition_model_version_stage(name=model_name,
            #                                     version=1, stage="Production")

            port = self.find_empty_ports()
            command = [
                "mlflow",
                "models",
                "serve",
                "-m",
                model_uri,
                "-p",
                str(port),
                "-h",
                "0.0.0.0",
                "--no-conda",
            ]
            if self.serve_model(command, port):
                st = {"port": port, "status": DeployedStatus.deployed}
            else:
                st = {"port": 0, "status": DeployedStatus.trained}

            model["ml_deployed_status"] = st
            logger.info(f"model:  {model}")
            await self.prediction_dao.update_document(
                {"_id": ObjectId(deploy_model.ml_id)}, model, "models"
            )
            model["_id"] = str(model["_id"])
            return model

    def find_pids_by_port(self, port):
        try:
            ### may be uncommented for windows in future if needed
            # if os.name == 'nt':  # For Windows
            #     result = subprocess.check_output(["netstat", "-ano"], universal_newlines=True)
            #     pids = []
            #     for line in result.splitlines():
            #         if f":{port} " in line:
            #             pids.append(int(line.split()[-1]))
            #     return pids
            # else:  # For Unix-based systems
            result = subprocess.check_output(
                ["lsof", "-t", f"-i:{port}"], universal_newlines=True
            )
            return [int(pid) for pid in result.strip().split("\n")]
        except subprocess.CalledProcessError as e:
            logger.debug(f"Error finding PID for port {port}: {e}")
            return []

    async def is_port_open_async(self, host, port):
        """Checks if a specific port is open on a given host asynchronously.

        Args:
            host: The hostname or IP address to check.
            port: The port number to check.

        Returns:
            True if the port is open, False otherwise.
        """
        try:
            _, writer = await asyncio.open_connection(host, port)
            await writer.drain()  # Ensure data is sent before closing
            writer.close()
            return True
        except (asyncio.TimeoutError, ConnectionError):
            return False
        finally:
            await asyncio.sleep(0)  # Yield to other tasks (optional)

    def is_port_open(self, host, port):
        """Checks if a specific port is open on a given host.

        Args:
            host: The hostname or IP address to check.
            port: The port number to check.

        Returns:
            True if the port is open, False otherwise.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)  # Set a timeout to avoid blocking indefinitely
                result = s.connect_ex((host, port))
                return result == 0  # Connection successful
        except socket.error:
            return False  # Connection error, likely port not open

    def find_process_using_port_sync(self, port):
        for proc in psutil.process_iter(["pid", "name", "connections"]):
            if proc.info["connections"] is not None:
                for conn in proc.info["connections"]:
                    if conn.laddr.port == port:
                        return proc
        return None

    async def find_process_using_port(self, port):
        loop = asyncio.get_event_loop()
        for proc in await loop.run_in_executor(
            None, lambda: list(psutil.process_iter(["pid", "name", "connections"]))
        ):
            if proc.info["connections"] is not None:
                for conn in proc.info["connections"]:
                    if conn.laddr.port == port:
                        return proc
        return None

    async def kill_process_using_port(self, port):
        process = await self.find_process_using_port(port)
        if process:
            logger.info(
                f"Killing process {process.info['name']} (PID: {process.info['pid']}) using port {port}"
            )
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, process.terminate)
            await loop.run_in_executor(None, process.wait, 5)
        else:
            logger.info(f"No process found using port {port}")

    async def kill_process(self, pid):
        try:
            ### may be uncommented for windows in future if needed
            # if os.name == 'nt':  # For Windows
            #     subprocess.check_output(["taskkill", "/PID", str(pid), "/F"])
            # else:  # For Unix-based systems

            os.kill(pid, signal.SIGTERM)
            logger.info(f"Process {pid} killed successfully")
        except Exception as e:
            logger.debug(f"Error killing process {pid}: {e}")

    async def undeploy_model(self, deploy_model: DeployModel):
        model = await self.prediction_dao.get_document(
            {"_id": ObjectId(deploy_model.ml_id)}, "models"
        )
        if "port" in model["ml_deployed_status"].keys():
            port = model["ml_deployed_status"]["port"]
        try:
            # pids = await self.find_pids_by_port(port)
            # for pid in pids:
            #     await self.kill_process(pid)
            # await self.async_kill_process_by_port(port)
            await self.kill_process_using_port(port)
        except:
            logger.debug(f"Error killing process for port {port}")

        st = {"port": port, "status": DeployedStatus.trained}
        model["ml_deployed_status"] = st
        await self.prediction_dao.update_document(
            {"_id": ObjectId(deploy_model.ml_id)}, model, "models"
        )
        model["_id"] = str(model["_id"])
        return model

    def convert_predictions_to_df(self, predictions, output_cols, output_std_cols):
        # Check if predictions contain dictionaries or lists
        if isinstance(predictions[0], dict):
            df = pd.DataFrame(predictions)
            df.columns = output_cols  # Rename columns
        elif isinstance(predictions[0], list):
            # df = pd.DataFrame(predictions, columns=output_cols)
            # Handle the case where predictions are provided as lists
            preds_data = predictions[0]
            stds_data = predictions[1] if len(predictions) > 1 else None

            # Create DataFrame for predictions
            df_preds = pd.DataFrame(preds_data, columns=output_cols)

            if stds_data is not None:
                # Create DataFrame for standard deviations if available
                df_stds = pd.DataFrame(stds_data, columns=output_std_cols)
                # Combine DataFrames
                df = pd.concat([df_preds, df_stds], axis=1)
            else:
                df = df_preds

        elif isinstance(predictions, list) and isinstance(predictions[0], (int, float)):
            # Handling pre_data (list of numeric values)
            df = pd.DataFrame(predictions, columns=output_cols)
            logger.info("Data is pre_data (list of numbers)")

        else:
            raise ValueError("Unsupported data structure in 'predictions'.")
        return df

    ### Commenting out for now may be removed in future
    # def convert_predictions_to_df(self, predictions, output_cols):
    #     # Check if predictions contain dictionaries or lists
    #     if isinstance(predictions[0], dict):
    #         df = pd.DataFrame(predictions)
    #         df.columns = output_cols  # Rename columns
    #     elif isinstance(predictions[0], list):
    #         df = pd.DataFrame(predictions, columns=output_cols)
    #     else:
    #         raise ValueError("Unsupported data structure in 'predictions'.")
    #     return df

    def get_prediction(
        self,
        prediction_config: PredictionConfig,
        wf_id: str,
        project_id: str,
        data_path: str,
        result_folders: str,
        dataset_record: Dataset = None,
    ):

        try:
            logger.info("Getting prediction")
            model = self.prediction_dao.get_document_by_id_sync(
                {"_id": ObjectId(prediction_config.ml_id)}, "models"
            )
            model["_id"] = str(model["_id"])
            ml_model = MachineLearningModel(**model)
            input_cols = ml_model.model.configs.input_cols
            if "output_cols" in ml_model.model.configs.model_fields:
                output_cols = ml_model.model.configs.output_cols
            else:
                output_cols = [ml_model.model.configs.output_col]

            total_cols = input_cols + output_cols

            all_data = ModelUtils.read_data_for_training(
                dataset_record=dataset_record, data_path=data_path
            )

            if not ml_model.model.type == "XGBoost":
                total_cols = [
                    element for element in total_cols if element in all_data.columns
                ]
                all_data = all_data[total_cols].dropna()

            data = all_data[input_cols]
            rem_data = all_data.drop(columns=input_cols, errors="ignore")
            if all_data.columns.intersection(output_cols).any():
                output_cols = [i + "_prediction" for i in output_cols]

            output_std_cols = [f"{col}_std" for col in output_cols]
            payload = None
            model_name = ml_model.model.type
            ml_sub_type = ml_model.model.ml_sub_type
            if ml_sub_type == "autogluon":
                payload = {
                    "dataframe_split": data.to_dict(orient="split"),
                    "params": {
                        "model_name": model_name,
                    },
                }

            elif ml_model.model.type == "XGBoost" or ml_model.model.type == "MPR":
                if ml_model.model.type == "XGBoost":
                    o_l = ml_model.model.configs.hyper_params.encoding_type
                else:
                    o_l = ml_model.model.configs.categorical_encoding

                data = categorical_encoding(
                    df=data,
                    output_label=ml_model.model.configs.output_col,
                    cat_encoding=o_l,
                )
                if isinstance(data, tuple):
                    data = data[0]
                payload = {"instances": data.to_numpy().tolist()}
            else:
                data = categorical_encoding(data)
                payload = {"instances": data.to_numpy().tolist()}

            port = ml_model.ml_deployed_status.port
            # Set the prediction endpoint URL
            url = f"http://mlflow_apis:{port}/invocations"
            # Set headers
            headers = {"Content-Type": "application/json"}

            model_name = model_name.replace("/", "_")
            prediction_csv = os.path.join(
                result_folders, f"{wf_id}_{model_name}_predictions.csv"
            )
            try:
                # Make the prediction request
                response = requests.post(url, headers=headers, data=json.dumps(payload))
                predictions = response.json()
                logger.info(f"Predictions: {predictions}")
                pred_data = self.convert_predictions_to_df(
                    predictions["predictions"], output_cols, output_std_cols
                )
                full_data = pd.concat([data, rem_data, pred_data], axis=1)
                full_data.to_csv(prediction_csv, index=False)
                return PredictionResponse(tabular_path=prediction_csv)
            except Exception as e:
                logger.debug(f"Error making prediction request: {e}")
                raise

        except Exception as e:
            logger.error("Prediction failed", exc_info=True)
            notification_obj = {
                "message": "Prediction has failed",
                "category_id": wf_id,
                "project_id": project_id,
                "notification_type": NotificationType.ERROR,
                "importance": NotificationImportance.HIGH,
                "notification_category": NotificationCategory.PREDICTION,
            }

            self.send_notification(notification_obj=notification_obj)
            return PredictionResponse(exception_detail=str(e))
