import json
import os
import time
import sys
import traceback
import logging
import pandas as pd
from pathlib import Path, PosixPath
from typing import Dict, Mapping
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient

from .schemas import RescaleConfig, RescaleResponse
from .dao import RescaleDao
from .rescale_methods import (
    create_trigger_rescale_job, 
    get_completed_job_rescale, 
    complete_rescale_job_flow,
    parse_job_content
)
from app.services.admin.connectors.service import ConnectorService, FileDetails
from app.services.data.assets.modules.utils import import_module_from_path
from app.config.env_vars import rescale_environment

logger = logging.getLogger(__package__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))

class RescaleService:

    def __init__(self, db_sync_client: MongoClient = None, db_async_client: AsyncIOMotorClient = None) -> None: # type: ignore
        self.rescaledao = RescaleDao(db_sync_client=db_sync_client, 
                                     db_async_client=db_async_client)

    def create_job(self, next_observation: Mapping, trial_index: int) -> Dict:
        rescale_files = eval(next_observation.get("rescale_files", '[]'))
        iter_csv_path = next_observation.get("iter_csv_path")

        kwargs = {"rescale_files": rescale_files, "rescale_config": self.parameters.rescale_configs}
        return create_trigger_rescale_job(
            self.workflow_name, trial_index, iter_csv_path, self.doc, **kwargs
        )

    def serialize_and_dump_to_json(self, file_path: Path):
        def convert_paths(obj):
            if isinstance(obj, Path):
                return str(obj)
            elif isinstance(obj, dict):
                return {key: convert_paths(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_paths(element) for element in obj]
            return obj

        serialized_data = convert_paths(self.job_data)

        with open(file_path, 'w') as file:
            json.dump(serialized_data, file, indent=4)

    def load_data_from_csv(self, path: Path) -> Dict:
        # Read the CSV file back into a DataFrame
        df_loaded = pd.read_csv(path)
        df_loaded.set_index('idx', inplace=True)
        # Convert and return  the DataFrame back to a dictionary, using keys as indices
        return df_loaded.to_dict(orient='index')

    def save_data_as_csv(self, path: Path):
        df = pd.DataFrame.from_dict(self.job_data)
        # Save the DataFrame to a CSV file
        df.to_csv(path)
    
    
    def process_job(self, jd, jd_copy):
        if not jd['test_mode']:
            token, job_id = jd['token'], jd['job_id']
            response = get_completed_job_rescale(token=token, job_id=job_id)
            if not self.parameters.rescale_configs.run_job or response:
                response_result = parse_job_content(response=response, job_id=job_id)
                if response_result['status'] == 'Failed' or response_result['statusReason'] == 'A run failed':
                    logger.info(f'Job {job_id} failed with reason: {response_result["statusReason"]}')  
                    raise 
                
                jd_copy.remove(jd)
                jd['visual_dir'] = complete_rescale_job_flow(**jd)
                if self.parameters.rescale_configs.software.post_python:
                    module_path = next(item.file_path for item in self.parameters.rescale_configs.files_detail if item.file_name == 'custom_driver.py')
                    module_path = Path(module_path)
                    custom_module = import_module_from_path(module_path=str(module_path))
                    kwargs = {
                        'rescale_output_file': Path(jd['output_file_path']),
                        'trial_folder': Path(jd['trial_folder']),
                        'parameters_file': Path(jd['parameters_file']),
                        'additional_files_dir': module_path.parent
                    }
                    jd['next_observation_evaluation'] = custom_module.PostProcess(**kwargs)
                    jd['output_variables_aliases'] = custom_module.output_variables_aliases
        else:
            jd_copy.remove(jd)
            jd['visual_dir'] = None
    
    def process_all_jobs(self, rescale_status_interval: int):
        jd_copy = self.job_data[:]  # Create a shallow copy
        while jd_copy:
            for jd in list(jd_copy):  # Create a list copy for safe iteration
                try:
                    self.process_job(jd, jd_copy)
                except Exception as e:
                    jd_copy.remove(jd)
                    logger.info(f'Job {jd["job_id"]} failed with exception: {e}')
                    jd['trial_status'], jd['visual_dir'] = 'Failed', None

            time.sleep(rescale_status_interval)

    def run_rescale(self, parameters: RescaleConfig, mobo_output: Path = None, 
                    workflow_name: str = None) -> RescaleResponse:
        try:
            self.parameters = parameters
            self.mobo_output = mobo_output
            self.workflow_name = workflow_name

            observations = self.load_data_from_csv(self.mobo_output)
            batch_folder = os.path.dirname(os.path.dirname(observations[next(iter(observations))]['iter_csv_path']))
            self.doc = self.rescaledao.get_connector(connector_id=self.parameters.rescale_connector_id).configuration
            
            ### to run 5 mins job uncomment the following line
            # self.parameters.rescale_configs.run_job = True
            self.job_data = []
            
            if self.parameters.rescale_configs.software.pre_python:
                ### will add function in future release
                pass

            
            connector_obj = ConnectorService(db_sync_client=self.rescaledao.db_sync_client)
            rescale_status_interval = 5
            ####  uploading file into rescale
            if not self.parameters.rescale_configs.test_mode:
                rescale_status_interval = rescale_environment.status_interval
                for i in self.parameters.rescale_configs.files_detail:
                    if i.upload_rescale and not i.rescale_id:
                        result = connector_obj.upload_files_to_rescale(rescale_data=[FileDetails(**i.model_dump())], connector_id=self.parameters.rescale_connector_id)[0]
                        i.rescale_id = result.id
                    
            for idx, observation in observations.items():
                self.job_data.append(self.create_job(observation, int(idx)))
            
            self.process_all_jobs(rescale_status_interval=rescale_status_interval)

            rescale_output = os.path.join(batch_folder, 'rescale_output.csv')
            logger.info(f'job_data:  {self.job_data}')
            self.save_data_as_csv(rescale_output)
            return RescaleResponse(tabular_path=rescale_output)
        
        except Exception as e:
            traceback.print_exc()
            logger.debug("An error occurred in rescale run. ", e)
            return RescaleResponse(exception_detail=str(e))

