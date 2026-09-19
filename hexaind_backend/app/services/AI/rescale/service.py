import re
import json
import os
import time
import sys
import shutil
import traceback
import logging
import pandas as pd
import numpy as np
from pathlib import Path, PosixPath
import threading
from typing import Dict, Mapping, List
from pymongo import MongoClient
from queue import Queue
from motor.motor_asyncio import AsyncIOMotorClient

from .schemas import RescaleConfig, RescaleResponse, RescaleRunningINFO
from .dao import RescaleDao
from .rescale_methods import (
    create_trigger_rescale_job, 
    get_completed_job_rescale, 
    complete_rescale_job_flow,
    parse_job_content,
    stop_job
)
from app.services.admin.connectors.service import ConnectorService, FileDetails
from app.services.data.assets.modules.utils import import_module_from_path
from app.services.data.assets.datasets.service import DatasetsService
from app.services.apps.image_analysis.segmentation1 import send_data_sync
from app.config.env_vars import environment, rescale_environment

logger = logging.getLogger(__package__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))

class RescaleService:

    def __init__(self, db_sync_client: MongoClient = None, db_async_client: AsyncIOMotorClient = None) -> None: # type: ignore
        self.rescaledao = RescaleDao(db_sync_client=db_sync_client, 
                                     db_async_client=db_async_client)
        
        self.max_parallel_jobs = None  # Control max parallel jobs
        self.job_queue = Queue()  # Queue to manage jobs
        self.in_progress_jobs = 0  # Track the number of jobs currently in progress
        self.lock = threading.Lock()  # Lock for ensuring thread-safe updates to shared variables
        self.stop_event = threading.Event()  # Event to signal when to stop processing jobs
        self.batch_mode = False
        self.observation_df = None
        self.rescale_output = None
        self.job_data = []
        self.input_variables = []
        self.output_variables = []
        self.dataset_id = None
        self.wf_id = ""
        self.run_id = ""
        

    def create_job(self, next_observation: Mapping, trial_index: int) -> Dict:
        rescale_files = eval(next_observation.get("rescale_files", '[]'))
        iter_csv_path = next_observation.get("iter_csv_path")
        next_observation['trial_status'] = 'job_created'
        logger.info(f'Creating job for trial index: {trial_index}')
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
        # Check if 'idx' or 'trial_index' columns exist and set the index accordingly
        if 'idx' in df_loaded.columns:
            df_loaded.set_index('idx', inplace=True)
        elif 'trial_index' in df_loaded.columns:
            df_loaded.set_index('trial_index', inplace=True)
        else:
            logger.info("No 'idx' or 'trial_index' column found in the DataFrame. Setting index from 1. to number of rows.")
            # If both columns are missing, set the index starting from 1 to the number of rows
            df_loaded.index = range(1, len(df_loaded) + 1)
            
        # Convert and return  the DataFrame back to a dictionary, using keys as indices
        return df_loaded.to_dict(orient='index')

    def save_data_as_csv(self, path: Path):
        self.observation_df.drop(columns=['iter_csv_path'], inplace=True, errors='ignore')
        if not self.batch_mode:
            self.observation_df = pd.DataFrame.from_dict(self.job_data)
        # Save the DataFrame to a CSV file
        self.observation_df.to_csv(path, index=False)
    
    def ingest_data_internally(self, user_id: str) -> str:
        logger.info("Ingesting data internally")
        dataset_id = DatasetsService(db_sync_client=self.rescaledao.db_sync_client).save_tabular_dataset_helper_sync(
            input_data=self.rescale_output, project_id='', site_id='', user_id=user_id)
        
        logger.info(f"Dataset saved with ID: {dataset_id}")
        return dataset_id
        
    def simplify_dict(self, input_dict: Dict) -> Dict:
        """
        Simplifies the input dictionary by removing tuple values
        and keeping only the first element in the tuple if necessary.
        
        Args:
            input_dict (dict): The input dictionary with either plain values 
                            or tuples as values.

        Returns:
            dict: A simplified dictionary with only plain values.
        """
        simplified_dict = {}
        
        for key, value in input_dict.items():
            if isinstance(value, tuple):
                # Take the first element of the tuple if it's a tuple
                simplified_dict[key] = value[0]
            else:
                # If it's not a tuple, keep the original value
                simplified_dict[key] = value
        
        return simplified_dict    
    
    def update_df_with_outdict(self, new_data: dict, idx: int):
        # Convert dictionary to a DataFrame
        new_df = pd.DataFrame(new_data, index=[idx])
        
        # Identify the position of 'trial_status' column
        trial_status_pos = self.observation_df.columns.get_loc('trial_status')
        
        # Add or update columns from new_data before 'trial_status' column
        for col in new_df.columns:
            if col not in self.observation_df.columns:
                # Insert new columns before 'trial_status' and update specific row
                self.observation_df.insert(trial_status_pos, col, pd.NA)
                # Adjust position of trial_status because of the newly inserted column
                trial_status_pos += 1
                
            # Update the specific row with idx for existing columns
            self.observation_df.loc[self.observation_df['trial_index'] == idx, col] = new_df[col].iloc[0]

    
    def sleep_stop_event(self, total_sleep_time, obs) -> int:
        sleep_interval = 1  # Check every 1 second for stop signal
        elapsed_time = 0
        
        while elapsed_time < total_sleep_time:
            # Sleep in intervals and check for stop signals
            time.sleep(sleep_interval)
            elapsed_time += sleep_interval
            
            if self.stop_event.is_set():  # Check if stop signal is received
                logger.info(f"trial index {obs['trial_index']} has been stopped.")
                obs['trial_status'] = 'Stopped'
                stop_job(obs['token'], obs['job_id'])
                self.update_dataframe(self.observation_df, obs, self.rescale_output)
                return 1 # Exit the job early if stop signal is received
        
        return 0  # Return 0 if job is not stopped
    
    def process_job(self, jd: Dict, obs: Dict, jd_copy: Dict=None):
        try:
            if not jd['test_mode']:
                token, job_id = jd['token'], jd['job_id']
                obs['token'] = token
                logger.info(f"Job {jd['idx']} going to sleep time of {jd['sleep_time']} seconds.")
                if self.sleep_stop_event(jd['sleep_time'], obs=obs):
                    return  # Exit the function if the job was stopped
                
                logger.info(f"Job {jd['idx']} woke up after sleep time of {jd['sleep_time']} seconds.")
                response = get_completed_job_rescale(token=token, job_id=job_id)
                response_result = parse_job_content(response=response[1], job_id=job_id)
                logger.info(f"Job {job_id} response: {response_result} in process_job")
                obs['trial_status'] = response_result[1]['status'] if not response_result[0] and response_result[1] else 'NA'
                if not self.parameters.rescale_configs.run_job or response[0]:
                    jd['visual_dir'] = complete_rescale_job_flow(**jd)
                    if not jd['output_file_path'].exists() and (response_result[1]['status'] == 'Failed' or response_result[1]['statusReason'] == 'A run failed'):
                        logger.info(f'Job {job_id} failed with reason: {response_result[1]["statusReason"]}')
                        obs['trial_status'] = 'Failed'
                        self.update_dataframe(self.observation_df, obs, self.rescale_output)
                        self.update_in_progress_jobs(-1)
                        return  # Exit the function if the job failed
                    
                    # jd_copy.remove(jd)
                    out_dict = pd.read_csv(jd['output_file_path']).to_dict('records')[0]
                    try:
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
                            out_dict.update(self.simplify_dict(jd['next_observation_evaluation']))
                    except:
                        logger.debug('Failed to perform post processing now rescale data will be added into master csv as it ')                    
                    
                    # obs.update(out_dict)
                    self.update_df_with_outdict(out_dict, obs['trial_index'])                    
                    obs['trial_status'] = response_result[1]['status']
                    obs['visual_dir'] = jd['visual_dir']
                    obs['visualize_files'] = jd['visualize_files']
                    self.update_dataframe(self.observation_df, obs, self.rescale_output)
                    logger.info(f"observation for {obs['trial_index']} is {obs}")
                    
                else:
                    self.update_dataframe(self.observation_df, obs, self.rescale_output)
                    self.process_job(jd, obs)
            else:
                # jd_copy.remove(jd)
                jd['visual_dir'] = None
                
        except Exception as e:
            logger.error(f"An error occurred while processing job {jd['job_id']}: {e}", exc_info=True)
            obs['trial_status'] = 'Failed'
            self.update_dataframe(self.observation_df, obs, self.rescale_output)
            
    def extract_value_after_specific_str(self, path, specific_str: str='wf'):
        # Use regular expression to find the value after 'wf_'
        match = re.search(r'{}_([^/]+)'.format(specific_str), path)
        if match:
            return match.group(1)
        return ''
    

    def update_dataframe(self, df: pd.DataFrame, update_data: Dict, csv_path: str):
        """
        Updates a specific row in the DataFrame based on the 'trial_index' column and saves the result to a CSV file.

        Args:
            df (pd.DataFrame): The DataFrame containing the original data.
            update_data (dict): The dictionary containing the updated data, including 'trial_index' for row identification.
            csv_path (str): The file path where the CSV should be saved.

        """
        if update_data:
            idx = update_data.get('trial_index')
            
            # Check if 'trial_index' exists in the DataFrame
            if idx in df.index:
                # Iterate over each key-value pair in update_data and update row by column
                for key, value in update_data.items():
                    # if key != 'trial_index':  # Skip 'trial_index' as we don't need to update that
                    if isinstance(value, (list, dict, np.ndarray)):
                        logger.warning(f"Skipping non-scalar value for column {key}")
                    else:
                        df.at[idx, key] = value  # Update scalar values only
            else:
                logger.info(f"Index {idx} not found in the DataFrame.")

        df.drop(columns=['iter_csv_path'], inplace=True, errors='ignore')
        # Save the updated DataFrame to a CSV file
        df.to_csv(csv_path, index=False)
        logger.info(f"DataFrame updated and saved to {csv_path}")

        try:
            logger.info(f"Sending data to rescale socket")
            dataset_cache_folder = environment.datasets_cache_folder / self.dataset_id
            if dataset_cache_folder.exists():
                shutil.rmtree(dataset_cache_folder)
            url = rescale_environment.socket_url
            send_data_sync(data={'dataset_id': self.dataset_id, 'workflow_id': self.wf_id}, url=url)
            logger.info(f"Data sent to rescale socket")
        except Exception as e:
            logger.error(f"Error in sending data to rescale socket: {e}")
    
    # Helper function to safely update the in-progress job counter
    def update_in_progress_jobs(self, delta):
        with self.lock:  # Ensures only one thread can modify self.in_progress_jobs at a time
            self.in_progress_jobs += delta
            
    def process_all_jobs(self, rescale_status_interval: int):
        count = 15  # Used to increment sleep time for each job
        threads = []  # List to keep track of all thread objects        
        
        # Main loop: keeps running until all jobs are processed
        while True:
            
            rescale_running_info: RescaleRunningINFO = self.rescaledao.get_rescale_running_info(wf_run_id=self.run_id)
            if (rescale_running_info.stop_all or rescale_running_info.stop_pending) and not self.job_queue.empty():
                logger.info("Stopping all pending jobs")
                while not self.job_queue.empty():
                    # Fetch a job from the queue
                    obs = self.job_queue.get()
                    obs['trial_status'] = 'Stopped'  # Update the observation status
                    obs['job_id'] = ""  # Store the job ID in the observation
                    self.update_dataframe(self.observation_df, obs, self.rescale_output)
                    logger.info(f"Stopped job for trial index: {obs['trial_index']}")
                    
                logger.info("All pending jobs were stopped")
                if rescale_running_info.stop_all:
                    logger.info("Stopping all running jobs")
                    self.stop_event.set()  # Set the stop event to signal all threads to stop
                    for thread in threads:
                        thread.join()  # Wait for all threads to finish
                    logger.info("All running jobs were stopped")
                    
                logger.info("All jobs have been stopped.")
            
            # Only create and start new jobs if we haven't reached the max parallel job limit
            elif self.in_progress_jobs < self.max_parallel_jobs and not self.job_queue.empty():
                # Fetch a job from the queue
                obs = self.job_queue.get()
                jd = self.create_job(obs, obs['trial_index'])  # Create the job dictionary
                self.job_data.append(jd)  # Append job details to job_data for logging or future reference
                obs['trial_status'] = 'Running'  # Update the observation status
                obs['job_id'] = jd['job_id']  # Store the job ID in the observation
                idx = obs['trial_index']  # The index of the job being processed
                logger.info(f'Creating job for trial index: {idx}')
                
                # Set custom sleep time for job, increases based on job count
                jd['sleep_time'] = rescale_status_interval #* count
                
                # Safely increment the in-progress job counter
                self.update_in_progress_jobs(1)
                # Wrapper function to execute job processing in a thread
                def job_wrapper(jd, obs):
                    try:
                        self.process_job(jd, obs)  # Process the job (runs the core job logic)
                    except Exception as e:
                        
                        # Log any exception that occurs during job processing
                        logger.error(f'Error processing job {jd["idx"]}: {str(e)}', exc_info=True)
                    finally:
                        # Safely decrement the in-progress job counter after the job is done
                        self.update_in_progress_jobs(-1)

                # Create a new thread to process the job and start it
                thread = threading.Thread(target=job_wrapper, args=(jd, obs, ))
                threads.append(thread)  # Add the thread to the list of active threads
                thread.start()  # Start the thread
                
                count += 2  # Increment count to stagger sleep times between jobs
                self.update_dataframe(self.observation_df, obs, self.rescale_output)

            
            # If we've reached the max parallel jobs, wait for some jobs to complete
            elif self.in_progress_jobs == self.max_parallel_jobs:
                logger.info('Max parallel jobs reached. Waiting for jobs to complete.')
                time.sleep(rescale_status_interval//2)  # Sleep for a bit before checking again
            
            # If all jobs are completed but the queue is empty, ensure remaining jobs finish
            else:
                logger.info('Waiting for remaining jobs to finish.')
                time.sleep(rescale_status_interval//2)  # Polling with sleep to allow jobs to finish
                if not threads:
                    break
            
            # Check the status of running threads
            for thread in threads:
                if not thread.is_alive():
                    threads.remove(thread)
            
            # # Check if all threads are finished and queue is empty
            # if all(not thread.is_alive() for thread in threads):
            #     break  # Exit loop if all threads are done
            
        
        logger.info('All jobs have been processed.')  # Final log when all jobs are complete
  
        
    # Define a function to check if all columns in output_cols have values for a given row
    def check_completion(self, row, output_cols: List[str]) -> str:
        # If all output columns are not null for the row, mark as 'completed', else 'pending'
        return 'completed' if row[output_cols].notna().all() else 'pending'

    def run_rescale(self, parameters: RescaleConfig, mobo_output: Path = None, 
                    workflow_name: str = None, results_folder: str=None, user_id: str=None) -> RescaleResponse:
        try:
            self.parameters = parameters
            self.mobo_output = mobo_output
            self.workflow_name = workflow_name
            self.batch_mode = self.parameters.rescale_configs.batch_mode
            observations = self.load_data_from_csv(self.mobo_output)
            self.observation_df = pd.DataFrame.from_dict(observations, orient='index')
            if self.batch_mode:
                batch_folder = results_folder
            else:
                batch_folder = os.path.dirname(os.path.dirname(observations[next(iter(observations))]['iter_csv_path']))
            self.rescale_output = os.path.join(batch_folder, 'rescale_output.csv')
            logger.info(f"rescale_output:--- {self.rescale_output}")
            self.doc = self.rescaledao.get_connector(connector_id=self.parameters.rescale_connector_id).configuration
            self.input_variables = self.parameters.rescale_configs.input_variables
            self.output_variables = self.parameters.rescale_configs.output_variables
            if self.output_variables:
                # Apply the function to each row and update the 'trial_status' column
                self.observation_df['trial_status'] = self.observation_df.apply(self.check_completion, output_cols=self.output_variables, axis=1)
            else:
                self.observation_df['trial_status'] = 'In Queue'    
            
            observations = self.observation_df[self.observation_df['trial_status'] == 'In Queue'].to_dict(orient='index')
            self.max_parallel_jobs = len(observations)
            if self.parameters.rescale_configs.batch_mode:
                self.max_parallel_jobs = self.parameters.rescale_configs.max_parallel_jobs
                self.save_data_as_csv(self.rescale_output)
                logger.info(f'user_id:----  {user_id}')
                if user_id: self.dataset_id = self.ingest_data_internally(user_id=user_id)
                self.update_dataframe(self.observation_df, {}, self.rescale_output)
            
            ### to run 5 mins job uncomment the following line
            # self.parameters.rescale_configs.run_job = True
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
                observation['trial_index'] = int(idx)
                if self.batch_mode:
                    trial_folder = os.path.join(batch_folder, f'trial_{idx}')
                    os.makedirs(trial_folder, exist_ok=True)  # Create the trial folder if it doesn't exist
                    csv_file = os.path.join(trial_folder, 'param_values.csv')
                    pd.DataFrame([observation]).to_csv(csv_file, index=False)
                    observation['iter_csv_path'] = csv_file
                
                self.job_queue.put(observation)  # Add job to the queue
            
            self.wf_id = self.extract_value_after_specific_str(self.rescale_output)
            self.run_id = self.extract_value_after_specific_str(self.rescale_output, specific_str='r')
            running_info = RescaleRunningINFO(
                run_id=self.run_id,
                workflow_id=self.wf_id,
                user_id=user_id,
                project_id='',
                running_data=[]
            )
            result = self.rescaledao.get_rescale_running_info(wf_run_id=self.run_id)
            if result:
                running_info.stop_all = result.stop_all
                running_info.stop_pending = result.stop_pending
            self.rescaledao.save_rescale_running_info(running_info.model_dump())
            self.process_all_jobs(rescale_status_interval=rescale_status_interval)
            logger.info(f'job_data:  {self.job_data}')
            self.save_data_as_csv(self.rescale_output)
            running_info.stop_all = running_info.stop_pending = False
            self.rescaledao.update_rescale_running_info(wf_run_id=self.run_id, rescale_running_info=running_info.model_dump())
            return RescaleResponse(tabular_path=self.rescale_output)
        
        except Exception as e:
            traceback.print_exc()
            logger.debug("An error occurred in rescale run. ", e)
            return RescaleResponse(exception_detail=str(e))
        
        
    async def update_rescale_running_info(self, run_id: str, stop_all: bool, stop_pending: bool):
        
        update_data = {
            "stop_all": stop_all,
            "stop_pending": stop_pending
        }
        
        await self.rescaledao.update_rescale_running_info(run_id=run_id, rescale_running_info=update_data)
