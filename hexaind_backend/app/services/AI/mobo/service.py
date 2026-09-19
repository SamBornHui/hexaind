import os
import sys
import json
import shutil
import logging
import traceback
import pandas as pd
from pathlib import Path
from pymongo import MongoClient
from typing import Mapping, Dict, List, Callable
from motor.motor_asyncio import AsyncIOMotorClient

from app.config.env_vars import environment
from .schemas import MOBOConfig, MOBOResponse
from .models import *
from .demo_optimization_api import demos
from .geometryconstraints.geometry_constraints import GCService
from .dao import MOBODao
from app.services.data.folder_management.service import FolderManagement
from app.services.data.folder_management.schema import CreateFolder
from app.services.workflows.workflow_designer.service import WorkflowDesignerService

import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__package__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))

class MOBOService:

    def __init__(self, db_sync_client: MongoClient = None, db_async_client: AsyncIOMotorClient = None) -> None: # type: ignore
        self.mobodao = MOBODao(db_sync_client=db_sync_client, db_async_client=db_async_client)
    
    def initialize_mobo(self):
        #initialize MOBO here
        ax_params = self.ax_parameters.model_dump()
        ax_params['output_path_trial_log'] = self.folder_dir
        ax_params['workflow_name'] = self.workflow_name
        ax_params['workflow_id'] = self.workflow_id
        ax_params['training_data_path'] = self.training_data_path
        ax_params['initialized_experiment'] = self.initialize_experiment

        ax_obj = AXRecommendation(**ax_params)
        if not ax_obj.existing_experiment:
            logger.info('Initializing ax mobo')
            ax_obj.configure_experiment()
            ax_obj.mobo_initialize()
            ax_obj.mobo_save_experiment(self.file_path)
            self.update_DB_with_trials_data(ax_obj, clear_trial_data=True,)    
    
    def load_experiment(self):
        try:
            logger.info("Loading saved experiment")
            ax_params = self.ax_parameters.model_dump()
            ax_params['workflow_name'] = self.workflow_name
            ax_params['workflow_id'] = self.workflow_id
            ax_params['training_data_path'] = self.training_data_path
            ax_params['initialized_experiment'] = self.initialize_experiment
            ax_params['output_path_trial_log'] = self.folder_dir
            ax_obj = AXRecommendation(**ax_params)
            ax_obj.ax_client = mobo_load_experiment(self.file_path + ".json")
            return ax_obj
        except Exception as e:
            traceback.print_exc()
            dev_msg = f'When loading existing experiment for [run_additional_iterations], {e}'
            msg = f'Error encountered when processing trial data (Error 021).'
            # throwException(msg,self.ax_parameters['user_id'], self.ax_parameters['socket_url'], dev_msg=dev_msg, workflow_id=self.ax_parameters['experiment_id'])
            logger.error(dev_msg)

    def update_DB_with_trials_data(self, ax_obj: Mapping, clear_trial_data: bool=False, num_iterations: int=0):
        workflow_update = dict()
        if not clear_trial_data:
            ax_obj.trial_data_full = ax_obj.trial_data_full.replace(np.nan, '', regex=True)
            ax_obj.trial_data_full.loc[ax_obj.trial_data_full.trial_status == 'RUNNING', 'batch'] = ax_obj.batch
            running_data = ax_obj.trial_data_full.loc[ax_obj.trial_data_full.trial_status == 'RUNNING'].to_dict('records')
            workflow_update = {'$set': {'trials_data':json.dumps(running_data, indent=4, sort_keys=True, default=str), 'num_iterations': num_iterations}}
        else:
            workflow_update = {'$set': {'trials_data':[], 'num_iterations': num_iterations}}
        self.mobodao.update_record_sync(self.workflow_name, self.project_id, workflow_update)

    def generate_recommendations(self, ax_obj: Mapping, batch_size: int):
        if ax_obj.experiment_type == 'OPTIMIZATION':
            self.next_observations = ax_obj.generator_recommend_batch(batch_size=batch_size)
            self.update_experiment = ax_obj.mobo_update_experiment
        else:
            self.next_observations = ax_obj.al_generator_recommend()
            self.update_experiment = ax_obj.al_update_experiment
    
    def generate_mobo_inputs(self, ax_obj: Mapping):
        workflow_trials_data = self.mobodao.find_record_sync(self.workflow_name, self.project_id)
        if not workflow_trials_data['stop_pending']:
            self.update_DB_with_trials_data(ax_obj, clear_trial_data=True)
            logger.info("running iteration" + str(self.ax_parameters.num_iterations))
            self.generate_recommendations(ax_obj, self.ax_parameters.batch_size)
            # self.update_DB_with_trials_data(ax_obj)
            self.ax_parameters.num_iterations -= 1
            self.update_DB_with_trials_data(ax_obj, num_iterations=self.ax_parameters.num_iterations)
            ax_obj.mobo_save_experiment(self.file_path)
                
    def output_path_dir(self,parent: str, exp_id: str) -> str:
        exp_id_path = os.path.join(parent, exp_id)
        os.makedirs(exp_id_path, exist_ok=True)
        return exp_id_path

    def get_exp_file_path(self, workflow_id: str, workflow_name: str, folder_name: str=None, results_folder: str=None):
        if not results_folder:
            ### where should env variable be define
            # hexaind_data = os.environ.get('HEXAIND_DATA', '/tmp')
            path_list = ['hexaind-datasets', 'mobo_experiments', workflow_id]
            if folder_name == 'connection':
                path_list.remove('mobo_experiments')
                path_list.insert(1, folder_name)
            elif folder_name:
                path_list.append(folder_name)
            self.folder_dir = str(environment.hexaind_data)
            for p in path_list:
                self.folder_dir = self.output_path_dir(self.folder_dir, p)
        else:
            self.folder_dir = results_folder
        
        # self.ax_parameters['output_path_trial_log'] = self.folder_dir
        self.file_path = os.path.join(self.folder_dir, workflow_name)

    async def get_exp_file_path_async(self, workflow_id: str, workflow_name: str, folder_name: str=None, results_folder: str=None):
        if not results_folder:
            ### where should env variable be define
            # hexaind_data = os.environ.get('HEXAIND_DATA', '/tmp')
            path_list = ['hexaind-datasets', 'mobo_experiments', workflow_id]
            if folder_name == 'connection':
                path_list.remove('mobo_experiments')
                path_list.insert(1, folder_name)
            elif folder_name:
                path_list.append(folder_name)
            self.folder_dir = str(environment.hexaind_data)
            for p in path_list:
                self.folder_dir = self.output_path_dir(self.folder_dir, p)
        else:
            self.folder_dir = results_folder
        # self.ax_parameters['output_path_trial_log'] = self.folder_dir
        self.file_path = os.path.join(self.folder_dir, workflow_name)

    def save_data_as_csv(self, path: Path):
        dict_list = [{**inner_dict, 'idx': key} for key, inner_dict in self.next_observations.items()]
        df = pd.DataFrame.from_dict(dict_list)
        # Save the DataFrame to a CSV file
        df.to_csv(path, index=False)

    def create_recommendations_csv(self, next_observation, trial_dir):
        df = pd.DataFrame.from_dict(data = [next_observation])
        rescale_iter_csv_path = trial_dir + '/param_values.csv'
        df.to_csv(rescale_iter_csv_path, index=False)
        return rescale_iter_csv_path

    def use_previous_run_data(self):
        shutil.copy(self.ax_parameters.dataset, self.file_path + '.csv')
        shutil.copy(self.ax_parameters.dataset.replace('.csv', '.json'), self.file_path + '.json')

    def create_folder(self,folder_path:str, folder_name:str, workflow_id:str):
        logger.debug(f"project - - - - - -- - -id {workflow_id}")
        project_service_obj = WorkflowDesignerService(db_sync_client=self.mobodao.db_sync_client)
        workflow_obj = project_service_obj.get_workflow_by_id(workflow_id)
        folder_managment_obj =FolderManagement(
                                    db_sync_client=self.mobodao.db_sync_client
                                    )
        create_folder = CreateFolder(destination_folder=str(folder_path),
                                folder_name=folder_name,
                                user_id=workflow_obj.owner_id)
        folder_managment_obj.create_folder_sync(siteId=workflow_obj.site_id,
                                                projectId=workflow_obj.project_id,
                                                create_folder=create_folder
                                                )

    def perform_geometry_constraints(self, copy_obs: Dict, batch_folder: str):
        failed_trials = None
        for idx in self.next_observations:
            trial_folder = self.output_path_dir(batch_folder, f'trial_{str(idx)}')
            self.next_observations[idx]['iter_csv_path'] = self.create_recommendations_csv(self.next_observations[idx], trial_folder)

        if self.ax_parameters.constraints_module_id:
            gc_params = dict(next_observations=self.next_observations, constraints_module_id=self.ax_parameters.constraints_module_id, db_syc_client=self.mobodao.db_sync_client )
            self.next_observations = GCService().apply_gc(gc_params)

            logger.info(f"after gc {self.next_observations}")
            if type(self.next_observations) != dict:
                self.next_observations = copy_obs
            else:
                failed_trials = {key: self.next_observations.pop(key) for key, value in list(self.next_observations.items()) if value["fail_flag"]}
                logger.info(f"failed trials {failed_trials}")
                for key in failed_trials:   self.update_experiment(evaluated_data={}, job_id=None, trial_idx=key, abandon_trial=True)
        
        return failed_trials
    
    def run_mobo(self, ax_parameters: MOBOConfig, workflow_id: str=None, workflow_name: str=None, project_id: str=None, training_data_path: Path=None, initialize_experiment: bool=False, results_folder: str=None) -> MOBOResponse:
        try:
            logger.info(f"Running MOBO {ax_parameters}")
            self.ax_parameters = ax_parameters
            self.workflow_id = workflow_id
            self.workflow_name = workflow_name
            self.project_id = project_id
            self.training_data_path = training_data_path
            self.initialize_experiment = initialize_experiment

            self.get_exp_file_path(workflow_id=self.workflow_id, workflow_name=self.workflow_name, results_folder=results_folder)
            # file_path_directory = os.path.join(self.folder_dir)  ### added this path for saving param_values.csv
            ## is this needed???
            # iter_url = ax_parameters.socket_url + '/featureEngineering/RunningBatchSocket' 
            if self.initialize_experiment:
                try:
                    self.initialize_mobo()
                except Exception as e:
                    dev_msg = f'When initializing optimization, {e}'
                    # msg = f'Error encountered when initializing optimization.'
                    # throwException(msg,self.ax_parameters['user_id'], self.ax_parameters['socket_url'], dev_msg=dev_msg, workflow_id=self.ax_parameters['experiment_id'])
                    logger.error(dev_msg)
                    return MOBOResponse(exception_detail=str(e))
                
            elif self.ax_parameters.dataset and os.path.exists(self.ax_parameters.dataset):
                try:
                    self.use_previous_run_data()
                except:
                    self.initialize_mobo()
                    
            ax_obj = self.load_experiment()
            self.mobodao.clear_record_sync(self.workflow_name, self.project_id, self.ax_parameters.num_iterations)
            self.generate_mobo_inputs(ax_obj)
            copy_obs = self.next_observations.copy()

            self.batch_id = next(iter(self.next_observations))
            batch_folder = self.output_path_dir(self.folder_dir,  'batch_{}'.format(str(self.batch_id)))
            failed_trials = self.perform_geometry_constraints(copy_obs, batch_folder)
            self.all_observation_data = self.next_observations.copy()
            while failed_trials:
                self.generate_recommendations(ax_obj, len(failed_trials))
                copy_obs = self.next_observations.copy()
                failed_trials = self.perform_geometry_constraints(copy_obs, batch_folder)
                logger.debug(f"length of failed trial:   {len(failed_trials)}")
                self.all_observation_data.update(self.next_observations.copy())
                ax_obj.mobo_save_experiment(self.file_path)
            self.next_observations = self.all_observation_data.copy()
            mobo_output = None
            if self.next_observations:
                batch_folder = self.output_path_dir(self.folder_dir,  'batch_{}'.format(str(self.batch_id)))
                mobo_output = batch_folder + f'/{(self.ax_parameters.experiment_type).lower()}_output.csv'
                self.save_data_as_csv(mobo_output)
            elif self.ax_parameters.num_iterations:
                self.run_mobo(ax_parameters, self.workflow_id, self.workflow_name, self.project_id)
            
            terminate = True if not self.ax_parameters.num_iterations and not mobo_output else False
            
            self.create_folder(folder_path=self.folder_dir,
                                   folder_name='batch_{}'.format(str(ax_obj.batch)),
                                   workflow_id=self.workflow_id)
            
            return MOBOResponse(tabular_path=mobo_output, terminate=terminate)
        
        except Exception as e:
            traceback.print_exc()
            logger.error("An error occurred in MOBO run. ", exc_info=True)
            return MOBOResponse(exception_detail=str(e))
        
    def load_json(self, json_file: Path) -> Dict:
        with open(json_file, 'r') as file:
            return json.load(file)
    

    def load_data_from_csv(self, path: Path) -> Dict:
        # Read the CSV file back into a DataFrame
        df_loaded = pd.read_csv(path)
        df_loaded.drop(columns=['iter_csv_path'], inplace=True, errors='ignore')


        # Convert and return  the DataFrame back to a dictionary, using keys as indices
        return df_loaded.to_dict('records')
    
    def get_test_method(self, cols):
        if 'dcpSpacerThickness' in cols or 'dcp_spacer' in cols:
            test_func = demos.can_fem
        elif 'r' and 'h' in cols:
            test_func = demos.cone_areas
        elif 'Si' and 'Fe' in cols:
            test_func = demos.ai_physics_v2
        else:
            test_func = demos.bced_v2
        return test_func

    def get_extra_rescale_variables_output(self, path: Path, varibales_aliases: Dict=None, output_variables: List[str]=None):
        df_out = pd.read_csv(path)
        for i in output_variables:
            temp_cols = [i]
            if varibales_aliases: temp_cols = [varibales_aliases[i]]
            df_out.drop(columns=temp_cols, errors='ignore', inplace=True)
        return df_out.to_dict('records')[0]

    def get_extra_thermocalc_variables_output(self, temp):
        in_out_cols = self.ax_parameters.input_variables + self.ax_parameters.output_variables
        for col in in_out_cols:
            if col in temp:
                del temp[col]

        return temp

    
    def get_next_observation_evaluation(self, rescale_output: Path=None, thermocalc_output: Path=None, prediction_output: str=None, sort_rescale_trial_data: Callable=None):
        
        self.next_observation_evaluation = list()
        self.additional_output_data = list()
        self.observation_data = self.load_data_from_csv(rescale_output or thermocalc_output or prediction_output)
        logger.info(f"\n all observation: \n  {self.observation_data}")
        test_evaluation_method = None
        for i in self.observation_data:
            evaluation_data = dict()
            i['trial_status'] = i.get('trial_status', 'COMPLETED')
            if i['trial_status'] == 'Failed':
                self.next_observation_evaluation.append(evaluation_data)
                self.additional_output_data.append(evaluation_data)
            else:
                if prediction_output:
                    evaluation_data = {key: (i.get(key), None) for key in self.ax_parameters.output_variables}
                    self.additional_output_data.append([])
                    
                elif thermocalc_output or i['test_mode']:    
                    next_observation = pd.read_csv(i['parameters_file']).to_dict('records')[0] if rescale_output else i.copy()
                    test_evaluation_method = test_evaluation_method or self.get_test_method(list(next_observation.keys()))
                    logger.info(f"\n next observation: \n {next_observation}")
                    evaluation_data = test_evaluation_method(recommendation=next_observation)
                    logger.info(f"\n evaluation_data: \n evaluation_data")
                    self.additional_output_data.append(self.get_extra_thermocalc_variables_output(next_observation.copy()))

                else:
                    evaluation_data = i.get('next_observation_evaluation', None)
                    if evaluation_data:
                        evaluation_data = eval(evaluation_data) if type(evaluation_data) == str else evaluation_data
                        output_variables_aliases = i.get('output_variables_aliases', '{}')
                        output_variables_aliases = eval(output_variables_aliases)
                    else:
                        output_variables_aliases = {'buckle_pressure':'Buckling Pressure', 'max_thinning':'Max Thinning Percent'} #if headers in output csv are different than output_variables
                        evaluation_data = sort_rescale_trial_data(csv_path = i['output_file_path'], output_variables_aliases = output_variables_aliases)
                        
                        ### will be uncommented in near future
                        # try:
                        #     #multiple maxThinning from rescale output by -1
                        #     rev_thinning = evaluation_data['maxThinning'][0]*-1
                        #     evaluation_data['maxThinning'] = (rev_thinning, None)
                        # except:
                        #     logger.error('Variable maxThinning not found in output.')
                        
                    self.additional_output_data.append(self.get_extra_rescale_variables_output(i['output_file_path'], varibales_aliases=output_variables_aliases, output_variables=self.ax_parameters.output_variables))

                self.next_observation_evaluation.append({ ev : tuple(evaluation_data[ev]) for ev in evaluation_data })

    def update_mobo_experiment(self, ax_parameters: MOBOConfig, rescale_output: Path=None, prediction_output: Path=None, thermocalc_output: Path=None, workflow_id: str=None, workflow_name: str=None, project_id: str=None, results_folder: str=None) -> MOBOResponse:
        try:
            self.ax_parameters = ax_parameters
            self.ax_parameters.dataset = None
            self.workflow_id = workflow_id
            self.workflow_name = workflow_name
            self.project_id = project_id
            self.training_data_path = None
            self.initialize_experiment = False
            self.get_exp_file_path(workflow_id=self.workflow_id, workflow_name=self.workflow_name, results_folder=results_folder)
            
            ax_obj = self.load_experiment()
            ax_obj.file_path = self.file_path
            self.get_next_observation_evaluation(rescale_output=rescale_output, prediction_output=prediction_output, thermocalc_output=thermocalc_output, sort_rescale_trial_data=ax_obj.sort_rescale_trial_data)
            ax_obj.batch = int(self.observation_data[0]['idx'])
            update_exp = ax_obj.mobo_update_experiment if self.ax_parameters.experiment_type == 'OPTIMIZATION' else ax_obj.al_update_experiment
            for idx, i in enumerate(self.observation_data):
                job_id = i.get('job_id', None)
                visual_dir = i.get('visual_dir', None)
                trial_idx = i.get('idx', None)
                update_exp(evaluated_data=self.next_observation_evaluation[idx], trial_idx=trial_idx, job_id=job_id, additional_output_data=self.additional_output_data[idx], visual_dir=visual_dir, trial_status=i['trial_status'])

            document = self.mobodao.find_record_sync(self.workflow_name, self.project_id)
            logger.info(f"document: {document}")
            self.ax_parameters.num_iterations = document.get('num_iterations')
            if not self.ax_parameters.num_iterations:
                return MOBOResponse(tabular_path=None, terminate=True)
            else:
                return self.run_mobo(self.ax_parameters, self.workflow_id, self.workflow_name, self.project_id, results_folder=results_folder)
            
        except Exception as e:
            traceback.print_exc()
            logger.error("An error occurred in MOBO Update exp. ", exc_info=True)
            return MOBOResponse(exception_detail=str(e))

    
    
