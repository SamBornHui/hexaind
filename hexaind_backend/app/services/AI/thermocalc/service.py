from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Tuple, List
from app.utils.file_utils import FileUtils
from app.core.services.action.service import ActionService
from app.services.data.assets.modules.service import ModuleService
from app.services.data.assets.modules.schemas import *
from app.core.services.action.schemas import *
from app.services.admin.connectors.service import ConnectorService
from app.services.admin.connectors.schemas import Connector, ConnectorType, ThermocalcConnectorConfiguration
from app.services.AI.thermocalc.schemas import Features, ThermocalcConfig, ThermocalcSubJobConfig
from app.config.env_vars import environment, thermocalc_environment

import pandas as pd
import os, sys, contextlib, builtins
import unittest.mock as mock
from uuid import uuid4
from pathlib import Path
import importlib.util
import logging
import sys

logger = logging.getLogger(__package__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))

THERMO_CALC_CUSTOM_FUNCTION_NAME = os.environ.get("THERMO_CALC_CUSTOM_FUNCTION_NAME", "perform_predictions")
THERMO_CALC_GET_INPUT_OUTPUT_FEATURES_FUNCTION_NAME = os.environ.get("THERMO_CALC_GET_INPUT_OUTPUT_FEATURES_FUNCTION_NAME", "get_input_output_features")

IS_STANDALONE_DEPLOYMENT = environment.is_standalone_deployment
CONTAINER_HEXAIND_DATA = os.environ.get("CONTAINER_HEXAIND_DATA")
HEXAIND_DESTINATION = os.environ.get("HEXAIND_DESTINATION")

def container_to_host_path_resolver(path: str) -> str:
    """
    Resolves a file path from a container path to a host path.

    Args:
    path (str): The file path within the container.

    Returns:
    str: The corresponding file path on the host.
    """
    # Check if the path actually starts with the CONTAINER_HEXAIND_DATA prefix
    if IS_STANDALONE_DEPLOYMENT and path.startswith(CONTAINER_HEXAIND_DATA):
        # Replace the container base path with the host base path
        return path.replace(CONTAINER_HEXAIND_DATA, HEXAIND_DESTINATION, 1)
    else:
        return path


def host_to_container_path_resolver(path: str) -> str:
    """
    Resolves a file path from a host path to a container path.

    Args:
    path (str): The file path on the host.

    Returns:
    str: The corresponding file path in the container.
    """
    # Check if the path actually starts with the HEXAIND_DESTINATION prefix
    if IS_STANDALONE_DEPLOYMENT and path.startswith(HEXAIND_DESTINATION):
        # Replace the host base path with the container base path
        return path.replace(HEXAIND_DESTINATION, CONTAINER_HEXAIND_DATA, 1)
    else:
        # Optionally handle or report paths that do not start with HEXAIND_DESTINATION
        return path

class ThermocalcService:

    def __init__(self, db_sync_client: MongoClient = None, db_async_client: AsyncIOMotorClient = None) -> None:
        logger.info("Initializing Thermocalc Service")
        #self.connector_dao = ConnectorDao(db_sync_client=db_sync_client, db_async_client=db_async_client)
        self.action_service = ActionService(db_sync_client=db_sync_client, db_async_client=db_async_client) 
        self.connector_service = ConnectorService(db_sync_client=db_sync_client, db_async_client=db_async_client)
        self.module_service = ModuleService(db_sync_client=db_sync_client, db_async_client=db_async_client)

    def sub_actions_creator(self, parent_action_record: Action, dataset_path: str) -> List[str]:
        logger.info("Creating Sub-Actions")

        #action_id = await action_service.create_action_async(action=action)
        
        dataframe = pd.read_csv(dataset_path)
        total_rows = len(dataframe)

        if total_rows < 1:
            logger.error("Thermocalc expects atleast one row to process. But got zero.")
            raise Exception("Thermocalc expects atleast one row to process. But got zero.")

        thermo_calc_batch_size = thermocalc_environment.thermocalc_batch_limit


        action_batches: List[Action] = []
        for i in range(0, total_rows, thermo_calc_batch_size):
            action_batches.append(Action(run_id=parent_action_record.run_id,
                                         action_config=parent_action_record.action_config,
                                         sub_action_config=ThermocalcSubJobConfig(start=i, end=min(i + thermo_calc_batch_size, total_rows)-1, source_file_path=dataset_path),
                                         status=ActionRunStatus.IDLE
                                         ))
        
        action_ids = self.action_service.create_actions_sync(actions=action_batches)

        # append this action_id's to the parent action
        self.action_service.update_sub_actions_sync(action_id=parent_action_record.id, sub_action_ids=action_ids)

        return action_ids
    
    @contextlib.contextmanager
    def load_module_temporarily(self, spec):
        """
        Temporarily add the module to sys.modules
        """
        logger.info("Loading Module Temporarily")

        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        try:
            spec.loader.exec_module(module)
            yield module
        finally:
            # Remove the module from sys.modules after usage to clean up
            del sys.modules[spec.name]

    def verify_and_get_features_from_user_code(self, file_path: str) -> Features:
        """
        This function will verify whether the user uploaded python file will consists the THERMO_CALC_CUSTOM_FUNCTION_NAME and 
        Logic to retrieve the input and output features
        """
        logger.info("verifying and getting features from user code")

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            try:
                return original_import(name, *args, **kwargs)
            except ImportError:
                return mock.Mock()

        builtins.__import__ = mock_import

        try:
            spec = importlib.util.spec_from_file_location(file_path[:-3], file_path)
            with self.load_module_temporarily(spec) as module:

                if not hasattr(module, THERMO_CALC_GET_INPUT_OUTPUT_FEATURES_FUNCTION_NAME):
                    logger.error(f"Thermocalc module is missing the required function(s): {THERMO_CALC_GET_INPUT_OUTPUT_FEATURES_FUNCTION_NAME}")
                    raise Exception(f"Thermocalc module is missing the required function(s): {THERMO_CALC_GET_INPUT_OUTPUT_FEATURES_FUNCTION_NAME}")
                
                if not hasattr(module, THERMO_CALC_CUSTOM_FUNCTION_NAME):
                    logger.error(f"Thermocalc module is missing the required function(s): {THERMO_CALC_CUSTOM_FUNCTION_NAME}")
                    raise Exception(f"Thermocalc module is missing the required function(s): {THERMO_CALC_CUSTOM_FUNCTION_NAME}")
                
                # getting input and output features from user code
                func = getattr(module, THERMO_CALC_GET_INPUT_OUTPUT_FEATURES_FUNCTION_NAME)
                result = func()

                if not (isinstance(result, list) and len(result) == 2 and isinstance(result[0], list) and isinstance(result[1], list)):
                    logger.error(f"Expected function to return input output features as List(List(['input_col1', ..]), List(['output_col1', ...])). But got {result}")
                    raise Exception(f"Expected function to return input output features as List(List(['input_col1', ..]), List(['output_col1', ...])). But got {result}")
                
                return Features(input_features=result[0], output_features=result[1])

        except Exception as e:

            logger.error(f"rror processing the user-uploaded Python file in thermocalc service while fetching input output features: {str(e)}")
            raise Exception(f"Error processing the user-uploaded Python file in thermocalc service while fetching input output features: {str(e)}")
        finally:
            # Restore the original import function to prevent affecting other parts of the system
            builtins.__import__ = original_import

    def compute_thermodynamic_features_helper(self, action_record: Action, result_file_path: str) -> str: #TODO return should be path class instead of string path
        logger.info("Computing thermodynamic features helper")

        widget_config: ThermocalcConfig = action_record.action_config.config

        job_specific_config: ThermocalcSubJobConfig = action_record.sub_action_config 

        module:Module = self.module_service.get_module_record_by_id(module_id=widget_config.module_id)

        thermodynamic_features_data = self.compute_thermodynamic_features(connection_id=widget_config.thermocalc_connector_id, 
                                                                          python_file_path=container_to_host_path_resolver(module.module_location.path), 
                                                                          input_features=widget_config.input_features,
                                                                          output_features=widget_config.output_features,
                                                                          input_file_path=job_specific_config.source_file_path, 
                                                                          start=job_specific_config.start, 
                                                                          end=job_specific_config.end)
        
        #file_path = environment.CONTAINER_HEXAIND_DATA / f"hexaind-datasets/thermocalc_temp_results/{uuid4().hex}.csv"
        file_path = Path(result_file_path)
            
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # saving the results to disk
        FileUtils.SaveTabularFileToDisk(data=thermodynamic_features_data, destination_path=str(file_path))

        return str(file_path)

    def compute_thermodynamic_features(self, 
                                       connection_id: str, python_file_path: str,
                                       input_features: list, output_features: list, 
                                       input_file_path: str, start: int, end: int, 
                                       connection_config:dict,
                                       connection_type:str,
                                       read_entire_file: bool =False,
                                       ) -> pd.DataFrame:
        
        try:
            logger.info("Computing thermodynamic features")
            if not input_file_path.endswith(".csv"):
                logger.error(f"Thermocalc service is expecting .csv files only as input. But got {input_file_path}")
                raise Exception(f"Thermocalc service is expecting .csv files only as input. But got {input_file_path}")
            
            # reading the whole of data
            data_chunk = pd.read_csv(input_file_path) if read_entire_file else pd.read_csv(input_file_path,
                                                                                           skiprows=range(1, start + 1),
                                                                                           nrows=end - start + 1)

            # Extract only the necessary input features for processing
            input_data_dict = data_chunk[input_features].to_dict(orient='records')

            if connection_type!= ConnectorType.THERMOCALC:
                logger.error(f"Thermocalc job got connection which is not compatible. expected {ConnectorType.THERMOCALC}, but got {connection_type}")
                raise Exception(f"Thermocalc job got connection which is not compatible. expected {ConnectorType.THERMOCALC}, but got {connection_type}")
            
            connection_env = connection_config

            results = self.run_client_code_for_thermodynamic_features(python_file_path=python_file_path, 
                                                                      input_data=input_data_dict,
                                                                      function_to_invoke=THERMO_CALC_CUSTOM_FUNCTION_NAME,
                                                                      connection_details_env=connection_env
                                                                      )
            results_df = pd.DataFrame(results)
            combined_results = pd.concat([data_chunk, results_df[output_features]], axis=1)

            return ThermocalcService.results_post_process(result=combined_results, expected_features=output_features, start_index=start)
        
        except Exception as e:
            logger.error(f"Error processing the user-uploaded Python file in thermocalc service: {str(e)}")
            raise Exception(f"Error processing the user-uploaded Python file in thermocalc service: {str(e)}")

    def run_client_code_for_thermodynamic_features(self, python_file_path: str, input_data: pd.DataFrame, connection_details_env: dict, function_to_invoke="perform_predictions"):

        try:
            logger.info("Running client code for thermodynamic features")
            with self.run_client_code_for_thermodynamic_features_helper(file_path=python_file_path, 
                                                                        function_name=function_to_invoke,
                                                                        env_vars=connection_details_env) as func:

                results = func(input_data)
                if not isinstance(results, list) or not all(isinstance(item, dict) for item in results):
                    logger.error(f"User given custom python file is returning other than list of dict. Getting {type(results)}")
                    raise Exception(f"User given custom python file is returning other than list of dict. Getting {type(results)}")
                
                return results
            
        except Exception as e:
            logger.error(f"Error processing the user-uploaded Python file in thermocalc service: {str(e)}")
            raise Exception(f"Error processing the user-uploaded Python file in thermocalc service: {str(e)}") 
    
    @contextlib.contextmanager
    def run_client_code_for_thermodynamic_features_helper(self, file_path: str, function_name: str, env_vars: dict):
        """
        A context manager to set environment variables, run a function from a Python file,
        and then clean up the environment variables afterwards.

        :param file_path: The path to the Python file.
        :param function_name: The name of the function to run from the Python file.
        :param env_vars: A dictionary of environment variables to set.
        """
        logger.info("Runing client code for thermodynamic features")
        # Backup the original environment variables
        original_env = {key: os.environ.get(key) for key in env_vars}
        # Set the new environment variables
        os.environ.update(env_vars)

        # Load the module
        module = None
        try:
            spec = importlib.util.spec_from_file_location(function_name, file_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            func = getattr(module, function_name)
            yield func

        except Exception as e:
            logger.error(f"Error processing the user-uploaded Python file in thermocalc service: {str(e)}")
            raise Exception(f"Error processing the user-uploaded Python file in thermocalc service: {str(e)}")
        
        finally:
            # Restore the original environment variables
            for key, value in original_env.items():
                if value is None: del os.environ[key]
                else: os.environ[key] = value

            # Remove the module
            if module:
                del sys.modules[module.__name__]
    @staticmethod
    def thermocalc_sub_action_results_aggregator(file_paths: list, result_file_path: str) -> str: # return should be replaced by Path class of python TODO
        logger.info("Aggregatiing thermocalc sub action results")
        dfs = []

        # Loop through the file paths, read each CSV, and append to the list
        for file_path in file_paths:
            df = pd.read_csv(file_path)
            dfs.append(df)

        # Concatenate all dataframes vertically
        combined_df = pd.concat(dfs, ignore_index=True)

        # Sort the combined dataframe based on 'HEXAIND_BATCH_INDEX'
        sorted_df = combined_df.sort_values(by='HEXAIND_BATCH_INDEX')

        # Drop the 'HEXAIND_BATCH_INDEX' column
        final_df = sorted_df.drop(columns=['HEXAIND_BATCH_INDEX'])

        file_path = Path(result_file_path)
        
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # saving the results to disk
        FileUtils.SaveTabularFileToDisk(data=final_df, destination_path=str(file_path))

        return str(file_path)

    @staticmethod
    def results_post_process(result: pd.DataFrame, expected_features: list, start_index: int) -> pd.DataFrame:
        """
        1. logic to handle missing columns, if user specified columns in output_features but 
        they didn't came after processesing the .py file then we are appending those columns with None values in result df

        2. Adding HEXAIND_BATCH_INDEX so that while aggregating we can sort the results
        """
        logger.info("Doing post processing")
        # Check for any expected features not present in result DataFrame
        missing_features = [col for col in expected_features if col not in result.columns]
        
        # Create a DataFrame with None values for missing features
        if missing_features:
            for col in missing_features:
                result[col] = None

        result.index = range(start_index, start_index + len(result))
        result.reset_index(inplace=True)
        result = result.rename(columns={'index': 'HEXAIND_BATCH_INDEX'})  # to order the results at the time of aggregation

        return result




    




