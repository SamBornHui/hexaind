import json
import logging
import argparse
from pathlib import Path
import os
import datetime
import pickle #p1
from datetime import datetime, timezone
import matplotlib
matplotlib.use('cairo')
from pyDOE import lhs              #p1
from sklearn.metrics import mean_absolute_percentage_error,mean_absolute_error #p1
from .mogp import MultitaskGPModel, normScaling, unitScaling, unitScalingMod, kldiv, rechypers  #jdev

from numpy import pi
from copy import deepcopy
import requests
import sys

from typing import List
import numpy as np
import pandas as pd
import torch
import gpytorch  #p1

from ax import (
    Data,
    Experiment,
    Metric,
    Objective,
    OptimizationConfig,
    ParameterType,
    RangeParameter,
    Runner,
    SearchSpace,
)
from ax.service.managed_loop import optimize
from ax.service.ax_client import AxClient
from ax.core.observation import ObservationFeatures
from ax.modelbridge.generation_strategy import GenerationStrategy, GenerationStep
from ax.modelbridge.factory import get_MOO_EHVI, get_MOO_PAREGO, get_GPEI
from ax.modelbridge.registry import Models
from ax.modelbridge.modelbridge_utils import get_pending_observation_features
from ax.modelbridge.modelbridge_utils import (
    extract_search_space_digest,
    extract_objective_weights,
)

from ax.service.utils.instantiation import ObjectiveProperties
from ax.models.torch.botorch_modular.surrogate import Surrogate


from ax.metrics.noisy_function import NoisyFunctionMetric
from ax.service.utils.report_utils import exp_to_df
from ax.runners.synthetic import SyntheticRunner

from botorch.models.gp_regression import FixedNoiseGP, SingleTaskGP
from botorch.acquisition.monte_carlo import qExpectedImprovement, qNoisyExpectedImprovement
from botorch.utils.multi_objective import pareto


from ax.modelbridge.factory import get_MOO_EHVI, get_MOO_NEHVI, get_MOO_PAREGO
from ax.modelbridge.modelbridge_utils import observed_hypervolume

# from databrick.ax_mobo import logging_details
from ax.storage.json_store.load import load_experiment
from ax.storage.json_store.save import save_experiment

# for testing
# recommendation_output_path = Path(os.environ["MOBO_RECOMMENDATION_PATH"])

logger = logging.getLogger(__package__)
logger.setLevel(logging.DEBUG)

global DEV_MODE
DEV_MODE = True
# EDIT THIS
class AXRecommendation:

    """
    Build and run an experiment instance for multiobjective Bayesian optimization using AX-BoTorch
    """
    def __init__(self, 
        workflow_name: str = None,
        workflow_id: str = None,
        experiment_type: str = 'OPTIMIZATION',           #p1
        initialized_experiment: bool = False,
        training_data_path: str = None,
        candidate_data_path: str = None,
        variables: List[str] = [],
        input_variables: List[str] = [],
        input_variables_constraints: List[List[float]] = None, ### new
        output_variables: List[str] = [],
        output_variables_objectives: List[str] = [],       
        output_variables_thresholds: List[float] = [],  ### new
        outcome_constraints_variables:List[str] = [],
        outcome_constraints: List[str] = [],
        outcome_constraints_active: bool = False,
        outcome_constraints_variables_list: List = [],
        candidate_data_path_updated: str = None,  ### update from xpred_path_updated - this variable might not be needed in future
        candidate_data_generator: str = None,
        surrogate_model: str = None,
        acquisition_function: str = None,
        recommendation_output: str = None,
        output_path: str = None,            ### what will this be used for? - may need to remove in future
        num_iterations: int = None,         ### maybe remove from class in future
        tolerance: float = None,            ### maybe remove from class in future
        termination_criteria: str = None,   ### maybe remove from class in future
        experiment_connection_type: str = None,
        experiment_connection: str = None,
        existing_experiment: bool = False,
        existing_experiment_path: str = None,
        output_path_trial_log: str = None,
        black_box_method: str = None,
        objectives_api_url: List[str] = [],
        rabbitmq_url: str = None,
        routing_key: str = None,
        queue_name: str = None,
        exchange_name: str = None,
        socket_url: str = None,
        user_id: str = None,
        is_single_optimization: bool = False,
        dev_mode: bool = True,
        *args,
        **kwargs
        ) -> None:

        self.workflow_id = workflow_id
        self.workflow_name = workflow_name
        self.experiment_type = experiment_type             #p1
        self.training_data_path = training_data_path
        self.candidate_data_path = candidate_data_path       
        self.output_path = output_path        
        self.variables = variables
        self.input_variables = input_variables
        self.input_variables_constraints = input_variables_constraints  ### new
        self.output_variables = output_variables
        self.output_variables_objectives = output_variables_objectives
        self.output_variables_thresholds = output_variables_thresholds  ### new
        self.outcome_constraints_variables = outcome_constraints_variables  ### new
        self.outcome_constraints_active = outcome_constraints_active
        self.outcome_constraints = outcome_constraints  ### new
        self.outcome_constraints_variables_list = outcome_constraints_variables_list
        self.surrogate_model = surrogate_model
        self.candidate_data_path_updated = candidate_data_path_updated ### updated
        self.acquisition_function = acquisition_function
        self.recommendation_output = recommendation_output
        self.num_iterations = num_iterations
        self.tolerance = tolerance
        self.termination_criteria = termination_criteria
        self.experiment_connection_type = experiment_connection_type
        self.experiment_connection = experiment_connection
        self.existing_experiment = existing_experiment
        self.existing_experiment_path = existing_experiment_path
        self.output_path_trial_log = output_path_trial_log
        self.components = input_variables
        self.input_variables = input_variables  ### UPDATED 
        self.black_box_method = black_box_method
        self.objectives_api_url = objectives_api_url
        self.rabbitmq_url = rabbitmq_url
        self.routing_key = routing_key
        self.queue_name = queue_name
        self.exchange_name = exchange_name
        self.initialized_experiment = initialized_experiment
        self.socket_url = socket_url
        self.user_id = user_id
        # store last next observation
        self.next_observation = None  ### this variable might not be needed in class
        self.trial_data = None
        self.trial_data_full = None
        self.old_df = None
        self.is_single_optimization = is_single_optimization
        self.dev_mode = dev_mode,
        self.ct = 0
        

        #group min/max into lists
        self.mins=[]
        self.maxs=[]
        for cons in self.input_variables_constraints:
            self.mins.append(cons[0])
            self.maxs.append(cons[1])
        
        #define folder paths
        self.file_path = os.path.join(self.output_path_trial_log, self.workflow_name)
        self.initial_folder_path = self.file_path +'/trials/initial_data'
        self.trials_folder_path = self.file_path +'/trials'
        self.al_error_metric_list = ['MAE', 'NMAE']
        
        #initialize error metrics
        if experiment_type == 'ACTIVE_LEARNING':
            self.al_error_metrics = []
            for metric in self.al_error_metric_list:
                for objective in self.output_variables:
                    self.al_error_metrics.append(f'{objective}_{metric}')
            self.al_error_metrics.append('Entropy')
            self.al_error_metrics.append('KL_divergence')
        
        if self.initialized_experiment == False:
            self.ct = 0
        else:
            self.ct = self.ct

        if self.outcome_constraints_active:
            exception = False
            cons_list = self.outcome_constraints[0].split(' ')
            if self.outcome_constraints_variables_list and cons_list[0] in outcome_constraints_variables_list:
                pass
            else:
                msg = 'Please choose appropriate feature name'
                dev_msg = "Invalid value in 'outcome_constraints_variables' field"
                exception = True
            
            if cons_list[1] == '>=' or cons_list[1] == '<=':
                pass
            else:
                msg = "Please choose appropriate outcome_constraints_operator '>=' or '<=' "
                dev_msg = "Invalid value in 'outcome_constraints_operator' field"
                exception = True
            
            try:
                eval(cons_list[2])
            except:
                msg = 'Please enter numerical value for outcome constraint'
                dev_msg = 'Invalid value in outcome constraint field'
                exception = True
                

            if exception:
                throwException(msg, self.user_id, self.socket_url, dev_msg, workflow_id=self.workflow_id)
                logger.error(dev_msg)
                sys.exit()
        else:
            self.outcome_constraints = []

        global DEV_MODE
        DEV_MODE = self.dev_mode
        self.trial_early_stopped = False
        
    def configure_experiment(self):

        """Configures the optimization experiment based on user input"""

        # Configure input variable/parameter information
        parameters = []
        for i in range(len(self.input_variables)):
            parameters.append({
            "name": self.input_variables[i],
            "type": "range", 
            "bounds": [self.input_variables_constraints[i][0], self.input_variables_constraints[i][1]],
            "value_type": "float",
            })
        if self.is_single_optimization:
            try:
                assert len(self.output_variables) == 1
                assert len(self.output_variables_objectives) == 1
                assert len(self.output_variables_thresholds) == 1
            except AssertionError as e:
                logger.error(f'Parameter (output_variables,output_variables_thresholds, output_variables_objectives) should be of len 1, {e}', 
                    )
                
        # Convert min/max to Boolean(min)
        objective_min_bool = []
        for i in self.output_variables_objectives:
            if i == 'MINIMUM':
                objective_min_bool.append(True)
            elif i == 'MAXIMUM':
                objective_min_bool.append(False)

        # Configure output/objective information
        objectives = {}
        for i in range(len(self.output_variables)):
            objectives.update({self.output_variables[i]:ObjectiveProperties(minimize=objective_min_bool[i], threshold=self.output_variables_thresholds[i])})

        max_batch_size = 100 # make adjustable in future

        ### check if this section is needed ### - if so, then need to update the lower/upper limits
        x_params = []
        for i in range(len(self.input_variables)):
            x_params.append(RangeParameter(name=self.input_variables[i], lower=0, upper=1, parameter_type=ParameterType.FLOAT))

        search_space = SearchSpace(
            parameters=x_params,)    

        # Configure generation of new data for experiment
        gs = GenerationStrategy(
            steps=[
                # 2. Bayesian optimization step (requires data obtained from previous phase and learns
                # from all data available at the time of each new candidate generation call)
                GenerationStep(
                    model=Models.BOTORCH_MODULAR,
                    num_trials=-1,  # No limitation on how many trials should be produced from this step
                    max_parallelism=max_batch_size,  # Parallelism limit for this step, often lower than for Sobol
                    model_kwargs={
                        "fit_out_of_design": True,
                         "surrogate": Surrogate(SingleTaskGP),
                         #"botorch_acqf_class": qNoisyExpectedImprovement,
                                },
                            ),
                        ]
                    )

        if self.existing_experiment == True:
            ax_client = AxClient.load_from_json_file(self.existing_experiment_path)
        else:
            ax_client = AxClient(generation_strategy=gs, verbose_logging = False)
            ax_client.create_experiment(
                name=self.workflow_name,
                parameters=parameters,
                objectives=objectives,
                outcome_constraints = self.outcome_constraints,
                immutable_search_space_and_opt_config=True,        
            )
        self.ax_client = ax_client
        return None

    
    def mobo_initialize(self, data_to_append=None):
        """
        Initializes the initial data to the experiment.
        """
        if os.path.splitext(self.training_data_path)[1] == '.csv':
            Train = pd.read_csv(self.training_data_path)
        else:
            Train = pd.read_parquet(self.training_data_path)
        Train = Train.drop_duplicates()
        x_train = Train[self.input_variables]
        y_train = Train[self.output_variables]
        outcome_constraints_train = Train[self.outcome_constraints_variables]
        self.n_train = len(x_train)

        #NEED ASSERTION/TRY that outcome variable exists

        ct = 0
        for i in range(self.n_train):
            self.ax_client.attach_trial(x_train.iloc[i, :].to_dict())
            y_trial = {}
            for j in range(len(self.output_variables)):
                #y_trial.update({self.output_variables[j]:(y_train.iloc[i, j], 0.0)}) #SEM=0
                y_trial.update({self.output_variables[j]:(y_train.iloc[i, j], np.nan)}) #SEM=nan
            if self.outcome_constraints_active:
                for k in range(len(self.outcome_constraints_variables)):
                    y_trial.update({self.outcome_constraints_variables[k]:(outcome_constraints_train.iloc[i, k], np.nan)}) #SEM=nan
            self.ax_client.complete_trial(trial_index=i, raw_data=(y_trial)) # SEM=0
            
            ct = i

        if self.experiment_type == 'OPTIMIZATION':
            #model_bridge = ax_client.generation_strategy.model # move to mobo recommend
            if self.is_single_optimization:
                self.gpei_model = None
                self.gpei_data = self.ax_client.experiment.fetch_data()
            else:
                # MOBO case
                self.ehvi_model = None
                self.ehvi_data = self.ax_client.experiment.fetch_data()

                trial_data_temp = self.pareto_optimal_points()
                trial_data_temp['Data type'] = 'Initial'
                trial_data_temp['Hypervolume'] = 0
                trial_data_temp['Hypervolume % change'] = 0
                trial_data_temp['trial_index_visual'] = trial_data_temp['trial_index'] + 1.
                timestamp_now = datetime.now(timezone.utc)
                trial_data_temp['trial_timestamp'] = timestamp_now
                # print('in mobo intialize:   \n',trial_data_temp)
                # print('in mobo intialize trial_index_visual:   \n', trial_data_temp['trial_index_visual'])
                trial_data_temp.to_csv(self.file_path + ".csv", index=False)
            #trial_data_temp.to_csv(str(Path(self.output_path_trial_log) / ("output_path_trial_log_"+self.workflow_name+".csv")), index=False)
            #save_experiment(self.ax_client.experiment, self.workflow_id + "_initialized.json") #for testing
            
        if self.experiment_type == 'ACTIVE_LEARNING':              #p1
            
            #Create master csv
            trial_data_temp = exp_to_df(self.ax_client.experiment)
            trial_data_temp['Data type'] = 'Initial'
            trial_data_temp['trial_index_visual'] = trial_data_temp['trial_index'] + 1.

            for metric in self.al_error_metrics:
                trial_data_temp[metric] = np.nan
            
            trial_data_temp['job_id'] = None
            timestamp_now = datetime.now(timezone.utc)
            trial_data_temp['trial_timestamp'] = timestamp_now
            trial_data_temp.to_csv(self.file_path + ".csv", index=False)
            
            #make folder for initial data
            # initial_folder = self.file_path+'/trials/initial_data'
            os.makedirs(self.initial_folder_path, exist_ok=True)
            trial_data_temp.to_csv(self.initial_folder_path + "/initial_data.csv", index=False)
            
            #create LHD based on paratemer ranges (linear input constraints)
            n_cand = 500
            cand_path = self.create_lhd_candidates(n_candidates = n_cand)
            
            #create all_inputs csv
            df_cand = pd.read_csv(cand_path)
            df_inputs = self.get_input_datapoints()
            df = pd.concat([df_inputs, df_cand], axis=0)
            df.to_csv(self.initial_folder_path+'/all_inputs.csv', index=False)
            logger.info('Initialized AL experiment')

        self.ct = ct
        return ct
    
    def combine_trials_metrics(self, trial_index, use_master_csv=True):
        df_exp = exp_to_df(self.ax_client.experiment)
        df_exp.sort_index(axis=0, inplace=False)
        df_exp.reset_index(inplace=True, drop=True)
        
        columns = []
        columns.append('Data type')
        columns.append('trial_index_visual')
        if self.experiment_type == 'ACTIVE_LEARNING':
            for metric in self.al_error_metrics:
                columns.append(metric)
        

        if self.black_box_method == 'existing_connection':
            columns.append('job_id')
        columns.append('trial_timestamp')
        
        if use_master_csv==True:
            trials_metrics = pd.read_csv(self.file_path + ".csv")
            # columns = [item for sublist in columns for item in sublist]
            df_temp_full = pd.concat([df_exp, trials_metrics[columns]], axis=1, sort=False)
            df_temp_full['trial_index_visual'] = df_temp_full['trial_index']+1.
            column_timestamp = df_temp_full.pop("trial_timestamp")
            df_temp_full.insert(df_temp_full.shape[1]-1, 'trial_timestamp', column_timestamp)
        else:
            try:
                trials_metrics = pd.read_csv(self.trials_folder_path + '/trials/trial_' +str(trial_index-1) + "/trials_metrics.csv")
                # columns = [item for sublist in columns for item in sublist]
                df_temp_full = pd.concat([df_exp, trials_metrics[columns]], axis=1, sort=False)
                column_timestamp = df_temp_full.pop("trial_timestamp")
                df_temp_full.insert(df_temp_full.shape[1]-1, 'trial_timestamp', column_timestamp)
            except:
                print('Could not find previous trial data.')
                df_exp['trial_index_visual'] = df_exp['trial_index'] + 1.
                for metric in self.al_error_metrics:
                    df_exp[metric] = np.nan
                timestamp_now = datetime.now(timezone.utc)
                df_exp['trial_timestamp'] = timestamp_now
                df_temp_full = df_exp
            
        # df_temp_full.to_csv(self.file_path + ".csv", index=False)
        df_temp_full.to_csv(self.trials_folder_path + '/trial_' + str(trial_index) + "/trials_metrics.csv", index=False)
        self.trial_data_full = df_temp_full   
        return None
    
    def read_trials_metrics(self, trial_index, master_csv=True):
        if master_csv==True:
            df_temp_full = pd.read_csv(self.file_path + ".csv")
        else:
            df_temp_full = pd.read_csv(self.trials_folder_path + '/trial_' + str(trial_index) + "/trials_metrics.csv")

        return df_temp_full
    
    def update_trials_metrics(self, df, trial_index, job_id = None, save_to_trial_dir=True, append_exp_data=True, last_index=None):
        df_exp = exp_to_df(self.ax_client.experiment)
        df_exp.sort_index(axis=0, inplace=False)
        df_exp.reset_index(inplace=True, drop=True)
        
        columns=[]
        columns.append('Data type')
        columns.append('trial_index_visual')
        if self.experiment_type == 'ACTIVE_LEARNING':
            for metric in self.al_error_metrics:
                columns.append(metric)
            
        # if job_id:
        #     columns.append('job_id')

        if self.black_box_method == 'existing_connection':
            columns.append('job_id') 
        columns.append('trial_timestamp')
        # columns_save = [item for sublist in columns for item in sublist]
        columns_save = columns
        df_temp = df[columns_save]
        # df_temp.to_csv(self.file_path + "/trials_metrics.csv", index=False)

        if save_to_trial_dir==True:
            # df_temp.to_csv(self.trials_folder_path + '/trial_' +str(trial_index) + "/trials_metrics.csv", index=False)
            pass
            
        if append_exp_data==True:
            df_temp_full = pd.concat([df_exp, df[columns_save]], axis=1, sort=False)
            # df_temp_full.to_csv(self.file_path + "/trials_metrics_full.csv", index=False)
            df_temp_full[~(df_temp_full.trial_status == 'RUNNING')].to_csv(self.file_path + ".csv", index=False)
           

            self.trial_data_full = df_temp_full
        
        if append_exp_data==True & save_to_trial_dir==True:
            df_temp_full.to_csv(self.trials_folder_path + '/trial_' +str(trial_index) + "/trials_metrics_full.csv", index=False)
        
        return None
    
    def read_candidate_points(self, csv_path):
        x_cand = pd.read_csv(csv_path)
        # x_cand['Status'] = 'Candidate'    
        
        return x_cand

    #Dead functions not used in run.py 
    def read_updated_candidate_points(self):
        
        X_pred = pd.read_csv(self.candidate_data_path_updated)
        X_pred = X_pred[self.input_variables]
        X_pred = X_pred.drop_duplicates()
        X_pred = X_pred.loc[X_pred['Status'] == 'Candidate']            
        observation_features = [
            ObservationFeatures(dict(zip(unique_components, x_pred)))
            for x_pred in X_pred[self.input_variables].values
            ]
        
        return observation_features
 
    
    def generator_recommend(self):
        """Recommend point(s) for next experiment."""
        if self.is_single_optimization:
            self.gpei_data = self.ax_client.experiment.fetch_data()
        else:
            # MOBO case
            self.ehvi_data = self.ax_client.experiment.fetch_data()

        next_trial_params, trial_index = self.ax_client.get_next_trial()        
        model_bridge = self.ax_client.generation_strategy.model
#         print('\n\n\n next_trial_params :', next_trial_params)
        predicted_trial_values = model_bridge.predict([ObservationFeatures(next_trial_params)])
        
        if self.trial_data_full is None:
            try:
                self.trial_data_full = pd.read_csv(self.file_path + ".csv")
                assert len(self.trial_data_full) == trial_index
            except Exception as e:
                logger.error(f'Creating trial data, error loading exising trial_data (generator), {e}', 
                    )
                # temp_df = exp_to_df(self.ax_client.experiment)
                temp_df = self.pareto_optimal_points()
                temp_df['Hypervolume'] = 0 # need to recover hypervolume from previous trial data
                temp_df['Hypervolume % change'] = 0
                temp_df['trial_index_visual'] = temp_df['trial_index'] + 1.
                timestamp_now = datetime.now(timezone.utc)
                temp_df['trial_timestamp'] = timestamp_now
                temp_df['Data type'] = 'Trial data'
                self.trial_data_full = temp_df
                temp_df.to_csv(self.file_path + ".csv", index=False) #uncomment in dev
        
        #print('in generator_recommend trial_index:   \n',trial_index)
        self.trial_data_full.loc[trial_index,'trial_index'] = trial_index
        self.trial_data_full['trial_index_visual'] = self.trial_data_full['trial_index'] + 1
        self.trial_data_full.loc[trial_index,'trial_status'] = 'RUNNING'
        self.trial_data_full.loc[trial_index,'trial_timestamp'] = datetime.now(timezone.utc)
        #print('in generator_recommend trial_data_full:   \n',self.trial_data_full)

        self.updateCSVWithInputsVal(next_trial_params)
        self.trial_data_full.to_csv(self.file_path + ".csv", index=False)

        return next_trial_params

    
    def generator_recommend_batch(self, batch_size: int):
        """Recommend batch of points for next experiment.
            batch_size: value should come from user input in UI, it is the number
            of parallel recommendations generated for each trial iteration.
        """
        logger.info('------------- in generator_recommend_batch -------------')
        # print('batch_size:    ', batch_size)
        self.batch = batch_size
        if self.is_single_optimization:
            self.gpei_data = self.ax_client.experiment.fetch_data()
        else:
            # MOBO case
            self.ehvi_data = self.ax_client.experiment.fetch_data()

        #suggest new points
        next_trial_params, _ = self.ax_client.get_next_trials(max_trials=batch_size)
        
        trial_idx = list(next_trial_params.keys())
        # print('\n\n\n next_trial_params :', next_trial_params)
        
        # get data to update master csv
        if self.trial_data_full is None:
            try:
                self.trial_data_full = pd.read_csv(self.file_path + ".csv")
                # assert len(self.trial_data_full) == trial_idx[0]
            except Exception as e:
                logger.error(f'Creating trial data, error loading exising trial_data (generator), {e}') 
                    #)
                # temp_df = exp_to_df(self.ax_client.experiment)
                temp_df = self.pareto_optimal_points()
                temp_df['Hypervolume'] = 0 # need to recover hypervolume from previous trial data
                temp_df['Hypervolume % change'] = 0
                temp_df['trial_index_visual'] = temp_df['trial_index'] + 1.
                timestamp_now = datetime.now(timezone.utc)
                temp_df['trial_timestamp'] = timestamp_now
                temp_df['Data type'] = 'Trial data'
                self.trial_data_full = temp_df
                temp_df.to_csv(self.file_path + ".csv", index=False) #uncomment in dev
        
        # update loop for master csv
        for trial_index in trial_idx:
            #print('in generator_recommend trial_index:   \n',trial_index)
            self.trial_data_full.loc[trial_index,'trial_index'] = trial_index
            self.trial_data_full['trial_index_visual'] = self.trial_data_full['trial_index'] + 1
            self.trial_data_full.loc[trial_index,'trial_status'] = 'RUNNING'
            self.trial_data_full.loc[trial_index,'batch'] = trial_idx[0]
            self.trial_data_full.loc[trial_index,'trial_timestamp'] = datetime.now(timezone.utc)
            #print('in generator_recommend trial_data_full:   \n',self.trial_data_full)

        self.batch = next(iter(next_trial_params))
        self.updateCSVWithInputsVal(next_trial_params, batch=True) #update to receive multiple recommendations


        return next_trial_params
    
    
    def generator_recommend_batch_series(self, batch_size: int):
        """Recommend batch of points for next experiment.
            batch_size: value should come from user input in UI, it is the number
            of parallel recommendations generated for each trial iteration.
        """
        print('------------- in generator_recommend_batch_series -------------')
        # print('batch_size:    ', batch_size)
        self.batch = batch_size
        if self.is_single_optimization:
            self.gpei_data = self.ax_client.experiment.fetch_data()
        else:
            # MOBO case
            self.ehvi_data = self.ax_client.experiment.fetch_data()

        #suggest new points
        trial_params = []
        trial_idx = []
        next_trial_params={}
        for b in range(batch_size):
            tp, ti = self.ax_client.get_next_trial()
            trial_params.append(tp)
            trial_idx.append(ti)
            next_trial_params[str(ti)]=tp
            
        # get data to update master csv
        if self.trial_data_full is None:
            try:
                self.trial_data_full = pd.read_csv(self.file_path + ".csv")
                assert len(self.trial_data_full) == trial_idx[0]
            except Exception as e:
                logger.error(f'Creating trial data, error loading exising trial_data (generator), {e}', 
                    )
                # temp_df = exp_to_df(self.ax_client.experiment)
                temp_df = self.pareto_optimal_points()
                temp_df['Hypervolume'] = 0 # need to recover hypervolume from previous trial data
                temp_df['Hypervolume % change'] = 0
                temp_df['trial_index_visual'] = temp_df['trial_index'] + 1.
                timestamp_now = datetime.now(timezone.utc)
                temp_df['trial_timestamp'] = timestamp_now
                temp_df['Data type'] = 'Trial data'
                self.trial_data_full = temp_df
                temp_df.to_csv(self.file_path + ".csv", index=False) #uncomment in dev
        
        # update loop for master csv
        for trial_index in trial_idx:
            #print('in generator_recommend trial_index:   \n',trial_index)
            self.trial_data_full.loc[trial_index,'trial_index'] = trial_index
            self.trial_data_full['trial_index_visual'] = self.trial_data_full['trial_index'] + 1
            self.trial_data_full.loc[trial_index,'trial_status'] = 'RUNNING'
            self.trial_data_full.loc[trial_index,'batch'] = trial_idx[0]
            self.trial_data_full.loc[trial_index,'trial_timestamp'] = datetime.now(timezone.utc)
            #print('in generator_recommend trial_data_full:   \n',self.trial_data_full)

        self.batch = next(iter(next_observations))
        self.updateCSVWithInputsVal(next_trial_params, batch=True) #update to receive multiple recommendations
        # print('next_trial_params:   ', next_trial_params)

        return next_trial_params
    
    
    def updateLocalStorageCol(self):
        intialize_wf_data = {'user_id': self.user_id, 'workflowstatus': 'running', 'exectionProgress': False, 'batch_size': 1, 'enableStopBatchRun': False, 'runningIterationData': None, 'iterationData': None, 'dagdetails': None}                    
        workflow_update = {'$set': intialize_wf_data}
        self.db.localstorages.update_one({'workflow_id': self.workflow_id}, workflow_update)

    def updateCSVWithInputsVal(self, next_observation, batch=False):
        if batch==False:
            for i in next_observation:
                self.trial_data_full.loc[len(self.trial_data_full)-1, i] = next_observation[i]
        else:
            for trial in list(next_observation.keys()):
                for i in next_observation[trial]:
                    self.trial_data_full.loc[trial, i] = next_observation[trial][i]
                    
    
    def al_generator_recommend(self):                                              
        """Recommend point(s) for next active learning experiment."""
              
        parser = argparse.ArgumentParser(description="Databrick Technologies active learning suite")
        parser.add_argument("--train", action='store_false', help="train (True) cuda")
        parser.add_argument("--n_epoch", default=500, type=int, help="number of epochs for training MOGP")
        parser.add_argument("--lr", default=0.1, type=float, help="learning rate")
        parser.add_argument("--latent_gp", default=2, type=int, help="number of latent GPs for LMC model")
        parser.add_argument("--init_hyp", action='store_false', help="initialize hyperparameters with prior iteration values")
        args1, unknown = parser.parse_known_args()
        
        # Load inputs/outputs
        inputs = self.get_input_datapoints(sort_completed=True).to_numpy()
        outputs = self.get_output_datapoints(sort_completed=True).to_numpy()
        
        # Load candidate points
        cand_path = self.file_path + '_lhd_candidates.csv'
        x_cand = self.read_candidate_points(cand_path)
        
        # Normal scaling
        device = torch.device("cuda" if (torch.cuda.is_available()) else "cpu")
        # train_x, train_x_min, train_x_max = unitScaling(inputs,device)
        train_x, train_x_min, train_x_max = unitScalingMod(inputs, cmin=self.mins, cmax=self.maxs, device=device)
        train_y, mo, so = normScaling(outputs,device)
        train_x = train_x.contiguous()
        train_y = train_y.contiguous()        

        # Initialize Model
        likelihood = gpytorch.likelihoods.MultitaskGaussianLikelihood(num_tasks=args1.latent_gp).double().to(device)
        model = MultitaskGPModel(train_x, train_y, likelihood, args1.latent_gp, 2).double().to(device)
        
        # create trial and state directory
        trial_index = self.ax_client.experiment.num_trials
        trial_folder = self.trials_folder_path+'/trial_'+str(trial_index)
        trial_state_curr = trial_folder+'/state'
        os.makedirs(trial_folder, exist_ok=True)
        os.makedirs(trial_state_curr, exist_ok=True)
        print(f'Created trial state folder {trial_state_curr}')

        # load hypers if available
        hypers_file_path_prev = self.trials_folder_path+'/trial_'+str(trial_index-1) + "/hypers.json"
        hypers_file_path_curr = self.trials_folder_path+'/trial_'+str(trial_index) + "/hypers.json"
        
        try:
            with open(hypers_file_path_prev, 'rb') as f:
                hypers = pickle.load(f)
            print('hypers loaded')
            model.initialize(**hypers)
            print(f'Model initialized with loaded hypers from {hypers_file_path_prev}')
        except FileNotFoundError as e:
            print(e)
            logger.error(f'{hypers_file_path_prev} not found when loading hyperparameters. Continuing without initialized hyperparameters')
            pass
        
        # train model
        model.train()
        likelihood.train()
        optimizer = torch.optim.Adam(model.parameters(), lr=args1.lr)
        mll = gpytorch.mlls.ExactMarginalLogLikelihood(likelihood, model)

        for j in range(args1.n_epoch):
            optimizer.zero_grad()
            output = model(train_x)
            loss = -mll(output, train_y)
            loss.backward()
            if j % 100 == 0:
                print('epoch %d/%d - Loss: %.3f' % (j, args1.n_epoch, loss.item()))
            optimizer.step()
                
        # record & save hyperparameters for initialization
        hypers = rechypers(model,likelihood,args1.latent_gp) 
        with open(hypers_file_path_curr, 'wb') as f:
            pickle.dump(hypers, f, pickle.HIGHEST_PROTOCOL)        
              
        # predict & find max. variance point 
        model.eval()
        likelihood.eval()
        # x_cand_torch = torch.from_numpy(x_cand.values).double().to(device)
        # x_cand_scaled, x_cand_scaled_min, x_cand_scaled_max = unitScaling(x_cand.values,device)
        x_cand_scaled, x_cand_scaled_min, x_cand_scaled_max = unitScalingMod(x_cand.values, cmin=self.mins, cmax=self.maxs, device=device)
        predictions = likelihood(model(x_cand_scaled))
        var = torch.sum(predictions.variance,dim=-1)
        indx = var.argsort(descending=True)[0].detach().cpu().numpy()
        # max_var_list.append(var[indx].detach().cpu().numpy())
        print('Max variance: %.3f' % var[indx])
        
        # find next recommendation point & remove from lhd
        # x_lhd_rev = (x_lhd+1)/2*(train_x_max-train_x_min)+train_x_min  #these should be min/max constraints
        xnew = x_cand.iloc[int(indx),:]
        x_cand.drop([int(indx)], inplace=True)
        x_cand.reset_index(drop=True)
        # x_cand = np.delete(x_lhd.detach().cpu().numpy(),indx,axis=0)
        # np.save(self.file_path + '_candidates.npy', x_lhd)
        x_cand.to_csv(cand_path, index=False)

        print('indx: ', indx)
        print('recommendation: ', xnew)
        print('new x_lhd len: ', len(x_cand))
        
        #format new datapoint for experiment
        next_trial_params = {}
        for i, var  in enumerate(self.input_variables):
            # print('next_trial_value_type: ', type(xnew[0,i].detach().cpu().numpy().item()))
            # next_trial_params[str(var)] = xnew[0,i].detach().cpu().numpy().item()
            next_trial_params[str(var)] = xnew[i]
        
        #attach new inputs to new trial
        self.ax_client.attach_trial(next_trial_params)
        
        # calc entropy
        # allinputs = torch.cat((train_x, x_cand_scaled), 0)
        # all_inputs=np.vstack((inputs, x_cand.values))
        all_inputs = pd.read_csv(self.initial_folder_path+'/all_inputs.csv').to_numpy()
        all_inputs_scaled, all_inputs_scaled_min, all_inputs_scaled_max = unitScalingMod(all_inputs, cmin=self.mins, cmax=self.maxs, device=device)
        # p = likelihood(model(allinputs))
        p = likelihood(model(all_inputs_scaled))
        entrop = 0.5*(p._covar.log_det() + p.covariance_matrix.shape[0]*(1 + np.log(2*np.pi)))
        #print(f'Entropy in al_generator_recommend {entrop}')

        #save model state to trial folder
        torch.save(model.state_dict(), trial_state_curr + '/mogp_model_state.pth')
        torch.save(likelihood.state_dict(), trial_state_curr + '/mogp_likelihood_state.pth')
        
        #try calculate KL div at this stage - dev
        try:
            trial_state_prev = self.trials_folder_path+'/trial_'+str(trial_index-1)+'/state'
            p1_cov = torch.load(f'{trial_state_prev}/covariance.pt')
            p1_pre = torch.load(f'{trial_state_prev}/precision.pt')
            p1_mean = torch.load(f'{trial_state_prev}/mean.pt')
            p1_cov_log_det = torch.load(f'{trial_state_prev}/cov_log_det.pt')
            print(f'***al_recommend: Loaded previous covariance from {trial_state_prev}')
            
            p_cov = p.covariance_matrix
            p_pre = p.precision_matrix
            p_mean = p.mean
            p_cov_log_det = p._covar.log_det()
            
            term1 = (p_cov_log_det - p1_cov_log_det)
            term2 = torch.trace(torch.matmul(p_pre,p1_cov))
            term3 = torch.matmul(torch.matmul((p_mean-p1_mean).flatten(),p_pre),(p_mean-p1_mean).flatten())
            kldiv = 0.5*(term1 + term2 + term3 - p1_cov.shape[0])

            kld1 = kldiv.detach().cpu().numpy()
            print(f'***al_recommend: KL_DIV for trial {trial_index}: {kld1}')
        except Exception as e:
            print(f'***al_recommend: could not calculate previous covariance from {trial_state_prev}')
            print(e)
            pass
        
        # save model covariance matrices
        torch.save(p.covariance_matrix, f'{trial_state_curr}/covariance.pt')
        torch.save(p.precision_matrix, f'{trial_state_curr}/precision.pt')
        torch.save(p.mean, f'{trial_state_curr}/mean.pt')
        torch.save(p._covar.log_det(), f'{trial_state_curr}/cov_log_det.pt')
        logger.info(f'Saved current covariance to {trial_state_curr}')
        
        self.combine_trials_metrics(trial_index=trial_index, use_master_csv=True)
        self.batch = trial_index
        return {trial_index: next_trial_params}
    
    
    def get_input_datapoints(self, sort_completed=False):                                
        '''Get data corresponding to input variables in the experiment'''
        

        trial_data_temp = exp_to_df(self.ax_client.experiment)
        if sort_completed:
            trial_data_temp = trial_data_temp.loc[trial_data_temp['trial_status']=='COMPLETED']
        input_data = trial_data_temp[self.input_variables]
        input_data.sort_index(axis=0, inplace=False)
        input_data.reset_index(inplace=True, drop=True)
        

        return input_data

    def get_output_datapoints(self, sort_completed=False):                                
        '''Get data corresponding to output variables in the experiment'''
        
        trial_data_temp = exp_to_df(self.ax_client.experiment)
        if sort_completed:
            trial_data_temp = trial_data_temp.loc[trial_data_temp['trial_status']=='COMPLETED']
        output_data = trial_data_temp[self.output_variables]
        output_data.sort_index(axis=0, inplace=False)
        output_data.reset_index(inplace=True, drop=True)
        
        return output_data

    def generator_recommend_manual(self, n_recommendations):
        """Recommend n_recommendations for next experiment."""
        
        if self.trial_data is None:
            try:
                self.trial_data = pd.read_csv(self.file_path + ".csv")
                assert len(self.trial_data) == trial_index
            except Exception as e:
                logger.error(f'Creating trial data (recommend_manual), error loading exising trial_data (generator), {e}', 
                )
                temp_df = self.pareto_optimal_points()
                temp_df['Hypervolume'] = 0 # need to recover hypervolume from previous trial data
                temp_df['Hypervolume % change'] = 0
                temp_df['trial_index_visual'] = temp_df['trial_index'] + 1.
                timestamp_now = datetime.now(timezone.utc)
                temp_df['trial_timestamp'] = timestamp_now
                temp_df['Data type'] = 'Trial data'
                self.trial_data = temp_df


        ehvi_model=None
        ehvi_model = get_MOO_EHVI(experiment=self.ax_client.experiment, data=self.ax_client.experiment.fetch_data())
        recc = ehvi_model.gen(n_recommendations) # - how many trials to generate

        input_recommendations = recc.param_df
        input_recommendations.reset_index(inplace=True)
        input_recommendations['Trial rank'] = input_recommendations.index+1
        model_preds = pd.DataFrame(recc._model_predictions[0])

        recommendations = pd.concat([input_recommendations, model_preds], axis=1)
        trial_rank = recommendations.pop("Trial rank")
        recommendations.insert(1, "Trial rank", trial_rank)
        timestamp_now = datetime.now(timezone.utc)
        recommendations['recommendation_timestamp'] = timestamp_now
        recommendations['Data type'] = 'Recommendation'
        trial_data = pd.concat([self.trial_data, recommendations], axis=0, ignore_index=True)
        trial_data.to_csv(self.file_path + ".csv", index=False) 
        # recommendations.to_csv(str(Path(self.output_path_trial_log) / ("output_path_trial_log_"+self.optimization_id+"_recc.csv")), index=False) #uncomment to test in dev

        return recommendations

    
    def sort_api_trail_data(self, params):
        trial_data = dict()
        for i in range(len(self.objectives_api_url)):
            if self.black_box_method=='model':
                pred_mobo_payload = {'inputs': params, 'model_ids': self.output_models, 'outputs': self.output_variables}
                url = f'http://{self.internal_ip}:7003/hexaindanalytics/PredictMOBO'
                response = requests.post(url, json=pred_mobo_payload)
                evaluated_data = json.loads(response.content.decode('utf-8'))
                evaluated_data = { ev : tuple(evaluated_data[ev]) for ev in evaluated_data }
            else:
                evaluated_data = get_api_eval(params = params, url = self.objectives_api_url[i], user_id = self.user_id, socket_url = self.socket_url, workflow_id=self.workflow_id, file_path=self.file_path, update_db_trial_data=self.updateDBWithTrialsData)
            trial_data.update({self.output_variables[i]: evaluated_data[self.output_variables[i]]})
        if self.outcome_constraints_variables:
            for k in range(len(self.outcome_constraints_variables)):
                trial_data.update({self.outcome_constraints_variables[k]: evaluated_data[self.outcome_constraints_variables[k]]})
        return trial_data


    def sort_rescale_trial_data(self, csv_path, output_variables_aliases = None):
        trial_data = dict()
        #get data and format output from rescale output csv
        try:
            evaluated_data = pd.read_csv(csv_path) #path to ../workflow_id/job_id/...csv file
            for i in range(len(self.output_variables)):
                if output_variables_aliases:
                    trial_data.update({self.output_variables[i]: tuple((evaluated_data[output_variables_aliases[self.output_variables[i]]][0], None))})
                else:
                    trial_data.update({self.output_variables[i]: tuple((evaluated_data[self.output_variables[i]][0], None))})
        except Exception as ex:
            logger.exception(msg=ex)
            self.trial_early_stopped = True
        
        return trial_data


    def mobo_update_experiment_manual(self, evaluated_data, SEM = np.nan):
        """
        Allows user to input experiment trial evaluations manually
        """
        
        """ For multiple trials submitted at once
        try:
            logger.info('Asserting trial data for adding to experiment')
            assert evaluated_data['Trials'] != None
            new_trial_data = pd.DataFrame(evaluated_data['Trials']).T
            input_trial_data = new_trial_data[self.input_variables]
            output_trial_data = new_trial_data[self.output_variables]
            for var in self.variables:
                assert var in new_trial_data.columns
        except Exception as e: 
            logger.error(f'When reading trial data, {e}', 
                    )
        """

        # for one trial submitted at oonce
        try:
            logger.info('Asserting trial data for adding to experiment')
            assert evaluated_data != None
            new_trial_data = pd.DataFrame(evaluated_data, index=[0])
            assert len(new_trial_data) == 1
            new_trial_data.set_index('trial_index_visual', drop=False, inplace=True)
            input_trial_data = new_trial_data[self.input_variables].astype(float)       #assumes all incoming data is float
            output_trial_data = new_trial_data[self.output_variables].astype(float)     #assumes all incoming data is float
            for var in self.variables:
                assert var in new_trial_data.columns
        except Exception as e:
            self.updateDBWithTrialsData(clear_trial_data=True)
            df = pd.read_csv(self.file_path + ".csv")
            df = df.drop(df[df['trial_status'] == 'RUNNING'].index)
            df.to_csv(self.file_path + ".csv", index=False)
            dev_msg = f'When reading trial data, {e}'
            msg = 'Error encountered when processing trial data (Error 011).'
            throwException(msg, self.user_id, self.socket_url, dev_msg, workflow_id=self.workflow_id)
            logger.error(dev_msg)
            sys.exit()
            
        # Requires for AXRecommendatioo class to be instantiated with an experiment with data
        ax_client_copy = deepcopy(self.ax_client)
        if self.is_single_optimization:
            gpei_data_copy = ax_client_copy.experiment.fetch_data()
        else:
            # MOBO case
            ehvi_data_copy = ax_client_copy.experiment.fetch_data()
        # ehvi_data_copy = ax_client_copy.experiment.fetch_data()

        if self.trial_data is None:
            try:
                self.trial_data = pd.read_csv(self.file_path + ".csv")
                # self.trial_data = pd.read_csv(str(Path(self.output_path_trial_log) / ("output_path_trial_log_"+self.workflow_name+".csv")))
                # assert len(self.trial_data) == trial_index
            except Exception as e:
                self.updateDBWithTrialsData(clear_trial_data=True)
                df = pd.read_csv(self.file_path + ".csv")
                df = df.drop(df[df['trial_status'] == 'RUNNING'].index)
                df.to_csv(self.file_path + ".csv", index=False)
                dev_msg = f'When reading trial data for upadting experiment, {e}'
                msg = "Error encountered when processing trial data (Error 012)."
                throwException(msg, self.user_id, self.socket_url, dev_msg, workflow_id=self.workflow_id)
                logger.error(dev_msg)
                sys.exit()
        
        drop_idx = (self.trial_data[self.trial_data['Data type'] == 'Recommendation'].index)
        self.trial_data.drop(drop_idx , inplace=True)

        """ For multiple trials submitted at once
        # Get trial index for new trials
        try:
            # ct = len(self.ax_client.experiment.trials) - 1
            ct = int(exp_to_df(self.ax_client.experiment)['trial_index'][-1:])
            assert ct == int(new_trial_data['trial_index'][0]) - 1
            ct = ct+1 # set trial count as # of trials + 1
        except Exception as e: 
            logger.error(f'When asserting experiment trial index and new trial index, {e}', 
                    )
        # ct = list(self.ax_client.experiment._trial_indices_by_status[4])[0] #loaded trial
        #self.ax_client.complete_trial(trial_index = trial_index, raw_data = evaluated_data) 
        """
            
        # Get trial index for new trials
        try:
            # ct = len(self.ax_client.experiment.trials) - 1
            ct = int(exp_to_df(self.ax_client.experiment)['trial_index'][-1:])
            assert ct == int(new_trial_data['trial_index']) - 1
            ct = ct+1 # set trial count as # of trials + 1
        except Exception as e:
            self.updateDBWithTrialsData(clear_trial_data=True)
            df = pd.read_csv(self.file_path + ".csv")
            df = df.drop(df[df['trial_status'] == 'RUNNING'].index)
            df.to_csv(self.file_path + ".csv", index=False)
            dev_msg = f'When asserting experiment trial index and new trial index, {e}'
            msg = "Error encountered when processing trial data (Error 013)."
            throwException(msg, self.user_id, self.socket_url, dev_msg, workflow_id=self.workflow_id)
            logger.error(dev_msg)
            sys.exit()
        
        ehvi_model=None
        hv = []
        hv_change = []
        trials_to_update = []
        logger.info('Beginning adding new trials to experiment')
        for i, trial in enumerate(new_trial_data['trial_index']):
            trial_int = int(trial)
            logger.info('Current trial index being added to experiment ' + str(trial_int))
            self.ax_client.attach_trial(input_trial_data.iloc[i, :].to_dict())
            y_trial = {}
            for j in range(len(self.output_variables)):
                #y_trial.update({self.output_variables[j]:(y_train.iloc[i, j], 0.0)}) #SEM=0
                y_trial.update({self.output_variables[j]:(output_trial_data.iloc[i, j], np.nan)}) #SEM=nan
            
            self.ax_client.complete_trial(trial_index=trial_int, raw_data=(y_trial)) # SEM=0
            if self.is_single_optimization:
                gpei_model = get_GPEI(experiment=self.ax_client.experiment, data=self.ax_client.experiment.fetch_data())
            
            else:
                # MOBO case
                ehvi_model = get_MOO_EHVI(experiment=self.ax_client.experiment, data=self.ax_client.experiment.fetch_data())
            
            try:
                hv.append(observed_hypervolume(modelbridge=ehvi_model))
            except:
                hv.append(0.0)
            trials_to_update.append(ct)
            ct = ct+1
        logger.info('Finished adding new trials to experiment')

        trial_data_temp = self.pareto_optimal_points()
        self.trial_data = pd.concat([trial_data_temp, self.trial_data[['trial_timestamp', 'Data type', 'Hypervolume', 'Hypervolume % change']]], axis=1)

        if len(new_trial_data) == 1:
            self.trial_data.loc[trials_to_update[0]:trials_to_update[-1],'Data type'] = 'Trial data'
            self.trial_data.loc[trials_to_update[0]:trials_to_update[-1],'Hypervolume'] = hv
            hv_diff = abs(self.trial_data['Hypervolume'].pct_change()*100)
            self.trial_data['Hypervolume % change'] = hv_diff
            if self.trial_data.loc[trials_to_update[0]-1,'Hypervolume'] == 0: #account for HV = 0 in previous trials
                self.trial_data.loc[trials_to_update[0],'Hypervolume % change'] = 0
            self.trial_data['Hypervolume % change'].replace([np.inf, -np.inf], np.nan, inplace=True)


            self.trial_data['trial_index_visual'] = self.trial_data['trial_index'] + 1.
            self.trial_data.loc[trials_to_update[0]:trials_to_update[-1],'trial_timestamp'] = datetime.now(timezone.utc)
            self.trial_data.to_csv(self.file_path + ".csv", index=False)
            self.trial_data_full = self.trial_data
        elif len(new_trial_data) > 1:
            self.trial_data.loc[trials_to_update,'Data type'] = 'Trial data'
            self.trial_data.loc[trials_to_update,'Hypervolume'] = hv
            hv_diff = abs(self.trial_data['Hypervolume'].pct_change()*100)
            self.trial_data['Hypervolume % change'] = hv_diff
            if self.trial_data.loc[trials_to_update-1,'Hypervolume'] == 0: #account for HV = 0 in previous trials
                self.trial_data.loc[trials_to_update,'Hypervolume % change'] = 0
            self.trial_data['Hypervolume % change'].replace([np.inf, -np.inf], np.nan, inplace=True)


            self.trial_data['trial_index_visual'] = self.trial_data['trial_index'] + 1.
            self.trial_data.loc[trials_to_update,'trial_timestamp'] = datetime.now(timezone.utc)
            self.trial_data.to_csv(self.file_path + ".csv", index=False)
            self.trial_data_full = self.trial_data

        return None


    def mobo_update_experiment(self, evaluated_data, trial_idx=None, abandon_trial=False, job_id=None, visual_dir=None, additional_output_data=None, trial_status='Complete'):
        """
        Update MOBO experiment with new data that is either provided from black box method
        """
        # Instantiate the HV model prior to trial update
        # ax_client_copy = deepcopy(self.ax_client)
        # if self.is_single_optimization:
        #     gpei_data_copy = ax_client_copy.experiment.fetch_data()
        #     gpei_model=None
        #     # get_MOO_EHVI for gpei / SOO?
        #     gpei_model = get_GPEI(experiment=ax_client_copy.experiment, data=gpei_data_copy)
        # else:
        #     # MOBO case
        #     ehvi_data_copy = ax_client_copy.experiment.fetch_data()
            # ehvi_model=None
        #     ehvi_model = get_MOO_EHVI(experiment=ax_client_copy.experiment, data=ehvi_data_copy)
                

        logger.debug(f'evaluated_data: {evaluated_data}')
        
        # trial_idx use for batch trials
        if trial_idx==None:
            trial_index = list(self.ax_client.experiment._trial_indices_by_status[4])[0] #loaded trial
        else:
            trial_index = trial_idx
        
        hv = np.nan
        if abandon_trial or self.trial_early_stopped or trial_status == 'Failed':
            if self.trial_early_stopped:
                self.ax_client.stop_trial_early(trial_index = trial_index)
            else:
                self.ax_client.abandon_trial(trial_index = trial_index)
        else:
            # Complete trial with evaluated data    
            self.ax_client.complete_trial(trial_index = trial_index, raw_data = evaluated_data)    
            # Calculate hypervolume
            # hv = observed_hypervolume(modelbridge=ehvi_model)
        
        if self.trial_data is None:
            try:
                self.trial_data = pd.read_csv(self.file_path + ".csv")
                # self.trial_data = pd.read_csv(str(Path(self.output_path_trial_log) / ("output_path_trial_log_"+self.workflow_name+".csv")))
                # assert len(self.trial_data) == trial_index
            except Exception as e:
                logger.error(f'When reading trial data for updating experiment, {e}', 
                    )
        
        trial_data_temp = self.pareto_optimal_points()
        trial_data_temp.reset_index(drop=True, inplace=True)
        # self.trial_data = self.trial_data_full
        self.trial_data['Pareto-optimal'] = self.trial_data['Pareto-optimal'].apply(bool)
        # data_equal = self.trial_data['Pareto-optimal'].iloc[:-1].equals(trial_data_temp['Pareto-optimal'].iloc[:-1])
        data_equal = False

        
        cols = list(trial_data_temp.columns)
        for i in cols:
            self.trial_data.drop(i, axis=1, inplace=True, errors='ignore')
        
        self.trial_data = pd.concat([trial_data_temp, self.trial_data], axis=1, sort=True)
        
        last_index = len(self.trial_data)-1
        if trial_idx:
            last_index = trial_idx
        self.trial_data.loc[last_index,'Data type'] = 'Trial data'
        self.trial_data.loc[last_index,'Hypervolume'] = hv
        ####### commenting out this for now
        # if hv!= np.nan and self.trial_data['Hypervolume'].loc[last_index] != 0:
        #     self.trial_data.loc[last_index,'Hypervolume % change'] = 100*(hv-self.trial_data['Hypervolume'].loc[last_index-1])/(self.trial_data['Hypervolume'].loc[last_index-1])
        # else:
        #     self.trial_data.loc[last_index,'Hypervolume % change'] = 0

        self.trial_data.loc[last_index,'Hypervolume % change'] = np.nan
        self.trial_data.loc[last_index,'trial_timestamp'] = datetime.now(timezone.utc)
        if job_id or abandon_trial:
            self.trial_data.loc[last_index,'job_id'] = job_id
        else:
            logger.info(f'job_id {job_id} not found at index  {last_index}  ')
        
        if visual_dir:
            self.trial_data.loc[last_index, 'visual_dir'] = visual_dir
        
        if additional_output_data:
            for d in additional_output_data:
                self.trial_data.loc[last_index, d] = additional_output_data[d]
        
        self.trial_data.loc[last_index, 'trial_index_visual'] = last_index+1
        self.trial_data.loc[last_index, 'batch'] = self.batch
        # self.trial_data = pd.concat([trial_data_temp, self.trial_data], axis=1, sort=True)
        self.trial_data = self.trial_data.sort_values(by='trial_index')
        self.trial_data.loc[~(self.trial_data.trial_status == 'RUNNING')].to_csv(self.file_path + ".csv", index=False)
        self.trial_data_full = self.trial_data
        self.trial_data_full.loc[self.trial_data_full.trial_status == 'RUNNING', 'batch'] = self.batch
        self.mobo_save_experiment(self.file_path)
        return data_equal


    
    def al_update_experiment(self, evaluated_data, job_id=None, trial_idx=None, abandon_trial=False, visual_dir=None, additional_output_data=None, trial_status='Complete'):
        """
        Update AL experiment with new data that is either provided from black box method
        """

        # trial_idx use for batch trials
        if trial_idx == None:
            trial_index = list(self.ax_client.experiment._trial_indices_by_status[4])[0] #loaded trial
        else:
            trial_index = trial_idx
        
        # Complete trial with evaluated data    
        if abandon_trial or self.trial_early_stopped or trial_status == 'Failed':
            if abandon_trial or trial_status:
                self.ax_client.abandon_trial(trial_index = trial_index)
            else:
                self.ax_client.stop_trial_early(trial_index = trial_index)
            mae_list = [np.nan, np.nan]
            nmae_list = [np.nan, np.nan]
            entrop = np.nan
            kld = np.nan
        else:
            logger.info('trial_index:  {trial_index}')
            self.ax_client.complete_trial(trial_index = trial_index, raw_data = evaluated_data)    

            logger.info(f'updated trial index {trial_index}')
            # Get allinputs
            inputs = self.get_input_datapoints(sort_completed=True).to_numpy()
            outputs = self.get_output_datapoints(sort_completed=True).to_numpy()
            
            assert len(inputs==len(outputs))
            # Load candidate points
            cand_path = self.file_path + '_lhd_candidates.csv'
            x_cand = self.read_candidate_points(cand_path)
            
            # Normal scaling
            device = torch.device("cuda" if (torch.cuda.is_available()) else "cpu")
            #train_x, train_x_min, train_x_max = unitScaling(inputs,device)
            train_x, train_x_min, train_x_max = unitScalingMod(inputs, cmin=self.mins, cmax=self.maxs, device=device)
            train_y, mo, so = normScaling(outputs,device)
            train_x = train_x.contiguous()
            train_y = train_y.contiguous()   
            logger.info(f'len train_x: {len(train_x)}')
            
            #define current trial model and state location
            trial_state_curr = self.trials_folder_path+'/trial_'+str(trial_index)+'/state'
            
            #Load current model state & covar
            dict_model = torch.load(trial_state_curr + '/mogp_model_state.pth', map_location=device)
            dict_likelihood = torch.load(trial_state_curr + '/mogp_likelihood_state.pth', map_location=device)
            p_cov = torch.load(f'{trial_state_curr}/covariance.pt')
            p_pre = torch.load(f'{trial_state_curr}/precision.pt')
            p_mean = torch.load(f'{trial_state_curr}/mean.pt')
            p_cov_log_det = torch.load(f'{trial_state_curr}/cov_log_det.pt')
            
            # Initialize current trial model
            parser = argparse.ArgumentParser(description="Databrick Technologies Active Learning suite")
            parser.add_argument("--latent_gp", default=2, type=int, help="number of latent GPs for LMC model")
            args1, unknown = parser.parse_known_args()
            likelihood = gpytorch.likelihoods.MultitaskGaussianLikelihood(num_tasks=args1.latent_gp).double().to(device)
            model = MultitaskGPModel(train_x,train_y, likelihood, args1.latent_gp, 2).double().to(device)
            model.load_state_dict(dict_model)
            likelihood.load_state_dict(dict_likelihood)
            model.eval()
            likelihood.eval()
                    
            #MAE NMAE
            y_pred = likelihood(model(train_x)).mean*so + mo
            y_real = train_y*so + mo
            mae_1 = mean_absolute_error(y_real[:,0].detach().cpu().numpy(),y_pred[:,0].detach().cpu().numpy())
            mae_2 = mean_absolute_error(y_real[:,1].detach().cpu().numpy(),y_pred[:,1].detach().cpu().numpy()) 
            nmae_1 = mean_absolute_percentage_error(y_real[:,0].detach().cpu().numpy(),y_pred[:,0].detach().cpu().numpy())*100
            nmae_2 = mean_absolute_percentage_error(y_real[:,1].detach().cpu().numpy(),y_pred[:,1].detach().cpu().numpy())*100
            mae_list = [mae_1, mae_2]
            nmae_list = [nmae_1, nmae_2]
            
            #Entropy
            entrop = 0.5*(p_cov_log_det + p_cov.shape[0]*(1 + np.log(2*np.pi)))
            entrop = entrop.detach().cpu().numpy().item()
            logger.info(f'entrop {entrop}')
            
            # load previous trial model covar and calculate KL divergence
            try:
                trial_index_prev = self.get_last_trial_state()
                trial_state_prev = self.trials_folder_path+'/trial_'+str(trial_index_prev)+'/state'
                p1_cov = torch.load(f'{trial_state_prev}/covariance.pt')
                p1_pre = torch.load(f'{trial_state_prev}/precision.pt')
                p1_mean = torch.load(f'{trial_state_prev}/mean.pt')
                p1_cov_log_det = torch.load(f'{trial_state_prev}/cov_log_det.pt')
                
                #calc KL
                term1 = (p_cov_log_det - p1_cov_log_det)
                term2 = torch.trace(torch.matmul(p_pre,p1_cov))
                term3 = torch.matmul(torch.matmul((p_mean-p1_mean).flatten(),p_pre),(p_mean-p1_mean).flatten())
                kld = 0.5*(term1 + term2 + term3 - p1_cov.shape[0])
                kld = kld.detach().cpu().numpy()
                # print('kl-divergence: %.3f  -  initial: %.3f' % (kld.detach().cpu().numpy()))
                logger.info(f'KL divergence for trial index {trial_index}: {kld}')
            except:
                logger.info(f' Previous trial {trial_index_prev} model information was not found. Setting KL_div to nan.')  
                kld = np.nan
        
        
        #Update master csv
        df_trials = self.read_trials_metrics(trial_index=trial_index, master_csv=False)
        idx_last = trial_idx #df_trials.index[-1]
        df_trials.loc[idx_last,'Data type'] = 'Trial data'
        for metric in self.al_error_metric_list:
            if metric == 'MAE':
                for i, objective in enumerate(self.ax_client.objective_names):
                    df_trials.loc[idx_last, f'{objective}_{metric}'] = mae_list[i]
            if metric == 'NMAE':
                for i, objective in enumerate(self.ax_client.objective_names):
                    df_trials.loc[idx_last, f'{objective}_{metric}'] = nmae_list[i]
            # for objective in self.ax_client.objective_names:
            #     var_error_metrics.append(f'{objective}_{metric}')

        df_trials.loc[idx_last,'Entropy'] = entrop
        df_trials.loc[idx_last,'KL_divergence'] = kld
        if job_id:
            df_trials.loc[idx_last,'job_id'] = job_id

        if visual_dir:
            df_trials.loc[idx_last, 'visual_dir'] = visual_dir

        if additional_output_data:
            for d in additional_output_data:
                df_trials.loc[idx_last, d] = additional_output_data[d]

        timestamp_now = datetime.now(timezone.utc)
        df_trials.loc[idx_last,'trial_timestamp'] = timestamp_now
        
        self.update_trials_metrics(df=df_trials, trial_index=trial_index, job_id=job_id, last_index=idx_last)
        self.trial_data = self.trial_data_full
        self.trial_data_full.loc[self.trial_data_full.trial_status == 'RUNNING', 'batch'] = self.batch
        self.mobo_save_experiment(self.file_path)
        return True
    
    
    def pareto_optimal_points(self):
        #Determine Pareto-optimal points - using BoTorch

        # Get data from trial
        trial_data_temp = exp_to_df(self.ax_client.experiment)

        # Decode constraints and label  - currently support only single constraint
        #salman change
        if self.outcome_constraints_active:
            idx = self.outcome_constraints[0].rfind("=")
            outcome_constraint_num = float(self.outcome_constraints[0][idx+1:])

            # Check if data is within outcome constraint
            if '>' in self.outcome_constraints[0]:
                trial_data_temp['constraint_check'] = trial_data_temp[self.outcome_constraints_variables[0]]>=outcome_constraint_num
            elif '<' in self.outcome_constraints[0]:
                trial_data_temp['constraint_check'] = trial_data_temp[self.outcome_constraints_variables[0]]<=outcome_constraint_num
            trial_data_temp['constraint_check_num'] = trial_data_temp['constraint_check']*1
            trial_data_temp['constraint_check_nan'] = trial_data_temp['constraint_check_num']
            trial_data_temp['constraint_check_nan'].replace(0, np.nan, inplace=True)

            # Filter only to have outputs within constraint
            constrained_outputs = []
            for i, obj in enumerate(self.output_variables):
                objective_name = obj
                objective_name_constrained = objective_name + '_constraint'
                trial_data_temp[objective_name_constrained] = trial_data_temp[objective_name]*trial_data_temp['constraint_check_nan']
                constrained_outputs.append(objective_name_constrained)

        # Translate objectives
        min_multiplier = []
        for obj in self.ax_client.experiment._optimization_config.objective.objectives:
            if obj.minimize==False:
                min_multiplier.append(1.)
            else:
                min_multiplier.append(-1.)

        # Find Pareto-optimal points
        if self.outcome_constraints_active:
            outcomes = torch.tensor(trial_data_temp[constrained_outputs].to_numpy()*min_multiplier)
            par = pareto.is_non_dominated(outcomes, deduplicate=True)
            invalid_idx = trial_data_temp.index[trial_data_temp['constraint_check_num']==0].tolist()
            trial_data_temp['Pareto-optimal'] = par
            trial_data_temp['Pareto-optimal_num'] = par*1.
            trial_data_temp.loc[invalid_idx,'Pareto-optimal_num'] = -1
        else:
            outcomes = torch.tensor(trial_data_temp[self.output_variables].to_numpy()*min_multiplier)
            par = pareto.is_non_dominated(outcomes, deduplicate=True)
            trial_data_temp['Pareto-optimal'] = par
            trial_data_temp['Pareto-optimal_num'] = par*1.

        return trial_data_temp
    
    def mobo_save_experiment(self, workflow_id):
        #save_experiment(self.ax_client.experiment, self.workflow_id + ".json")
        self.ax_client.save_to_json_file(workflow_id + ".json")
        return None
    
    def collect_inputs_minmax(self):
        inputs_min = []
        inputs_max = []
        for par in self.ax_client.experiment.parameters:
            inputs_min.append(self.ax_client.experiment.parameters[par]._lower)
            inputs_max.append(self.ax_client.experiment.parameters[par]._upper)
        return inputs_min, inputs_max
    
    def create_lhd_candidates(self, n_candidates):
        device = torch.device("cuda" if (torch.cuda.is_available()) else "cpu") 
        x_lhd = lhs(len(self.input_variables), samples=int(n_candidates))
        x_lhd = 2*x_lhd - 1 
        #convert lhd space to parameter range
        inputs_min, inputs_max = self.collect_inputs_minmax()
        x_lhd = (x_lhd+1)*(np.array(inputs_max)-np.array(inputs_min))/2+np.array(inputs_min)
        df = pd.DataFrame(x_lhd)
        df.columns = self.input_variables
        lhd_save_path = self.file_path + '_lhd_candidates.csv'
        df.to_csv(lhd_save_path, index=False)
        return lhd_save_path
    
    def get_last_trial_state(self):                                
        '''
        Get last trial id with status=completed and data_type=trial data
        '''
        trial_data = pd.read_csv(self.file_path + ".csv")
        try:
            last_trial_state_id = int(trial_data[(trial_data["trial_status"]=='COMPLETED') & (trial_data["Data dtype"]=='Trial data')].iloc[-1].trial_index)
        except:
            print('No prior trial found with completed trial data.')
            last_trial_state_id = None
        
        return last_trial_state_id

def test_api_eval(params, url, user_id=None, socket_url=None, workflow_id=None):
    # for testing - evaluate data from demo API
    data = dict()
    if 'recommendations' in url:    
        data['demo_name'] = 'demo_1'
    elif 'can-end-fem' in url:
        data['demo_name'] = 'can_fem'
    elif 'ai_physics' in url: 
        data['demo_name'] = 'ai_physics'
    elif 'bced_v1' in url: 
        data['demo_name'] = 'bced_v1'
    elif 'bced_v2' in url: 
        data['demo_name'] = 'bced_v2'
    
    data['recommendation'] = params
    try:
        response = requests.post(url, json=data, timeout=2.50)
    except Exception as e:
        dev_msg =  f'Error in recommendation url, {e}'
        msg = "Error encountered evaluating new trial data (Error 014)."
        # throwException(msg, user_id, socket_url, dev_msg, workflow_id=workflow_id)
        logger.error(dev_msg)
    evaluation = json.loads(response.content.decode('utf-8'))
    observation_evaluation = { i : tuple(evaluation[i]) for i in evaluation }
    return observation_evaluation
    
def mobo_load_experiment(experiment_path):
    # loaded_experiment = load_experiment(experiment_path)
    loaded_experiment = AxClient.load_from_json_file(experiment_path)
    return loaded_experiment

def create_recommendations_csv(next_observation, trial_dir):
    df = pd.DataFrame.from_dict(data = [next_observation])
    rescale_iter_csv_path = trial_dir + '/param_values.csv'
    df.to_csv(rescale_iter_csv_path, index=False)
    return rescale_iter_csv_path
def get_api_eval(params, url, user_id=None, socket_url=None, workflow_id=None, file_path=None, update_db_trial_data=None):
    # evaluate data from demo API
    data = dict()
    if 'recommendations' in url:    
        data['demo_name'] = 'demo_1'
    if 'can-end-fem' in url:
        data['demo_name'] = 'can_fem'
    if 'ai_physics' in url:
        data['demo_name'] = 'ai_physics'
    if 'bced_v1' in url: 
        data['demo_name'] = 'bced_v1'
    if 'bced_v2' in url: 
        data['demo_name'] = 'bced_v2'
    
    data['recommendation'] = params
    try:
        response = requests.post(url, json=data, timeout=2.50)
    except Exception as e:
        if file_path:
            df = pd.read_csv(file_path + '.csv')
            df = df.drop(df[df['trial_status'] == 'RUNNING'].index)
            df.to_csv(file_path + ".csv", index=False)
        update_db_trial_data(clear_trial_data=True)
        dev_msg =  f'Error in recommendation url, {e}'
        msg = "Error encountered evaluating new trial data (Error 014)."
        throwException(msg, user_id, socket_url, dev_msg, workflow_id=workflow_id)
        logger.error(dev_msg)
        sys.exit()    
    evaluation = json.loads(response.content.decode('utf-8'))
    observation_evaluation = { i : tuple(evaluation[i]) for i in evaluation }
    return observation_evaluation

def throwException(msg, user_id, url, dev_msg=None, workflow_id=None):
    # preparing exception detail for ui
    print('in throw exectopn:  ',msg, dev_msg, url)
    if url:
        except_url = url + '/featureEngineering/moboNotificationSocket'
        sock_data = dict()
        sock_data['status'] = False
        sock_data['msg'] = msg
        sock_data['workflow_id'] = workflow_id
        sock_data['user_id'] = user_id
        logger.info(f"Developer info:   {dev_msg}  ")
        logger.info(f"in throw exceptiopn:   {sock_data}  {except_url}")
        updatingUI(sock_data, except_url)
    elif DEV_MODE:
        logger.info("Developer mode is enable")
    else:
        logger.error(f"'socket_url' is {url}")
        sys.exit()

def updatingUI(data, url):
    # sending data to ui
    # print('in updating ui:   ',data, url) 
    if url:
        requests.post(url, data=data, timeout=2.50)
    else:
        logger.error('Notification URL not found')
        sys.exit()

def getLastIteration(path):
    # getting last row of dataframe and saving into dict
    last_iter = dict()
    if path:
        df = pd.read_csv(path)
        last_iter = df.tail(1).to_dict('records')[0]
        last_iter = dict(map(lambda x: (x[0].replace(' ', ''), x[1]), last_iter.items()))

    return last_iter

def getPandasSpecificIdxDict(df, idx):
    df = df.replace(np.nan, '', regex=True)
    idx_itr = df.iloc[idx,:].to_dict()
    idx_itr['trial_timestamp'] = str(idx_itr['trial_timestamp'])
    return idx_itr     

def fetchKeysValue(keyname, obj, defaultname=''):
    # extracting key value from object
    if keyname in obj:
        keyvalue = obj[keyname]
        del obj[keyname]
    else:
        keyvalue = defaultname
    
    return keyvalue
