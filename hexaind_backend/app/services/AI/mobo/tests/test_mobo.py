import subprocess
from pathlib import Path
from pymongo import MongoClient
import pytest
import requests
import json
import warnings
warnings.filterwarnings('ignore')
import sys
sys.path.append('../')
sys.path.append('../../../../../')

from ..service import MOBOService


def generates_mobo_inputs(params):
    db_config = dict(db_address = params['internal_ip'] + ':27017', db_name = "Databrick", db_username = "Databrick", db_password = "test")
    client = MongoClient(db_config['db_address'],
                        username=db_config['db_username'],
                        password=db_config['db_password'],
                        authSource=db_config['db_name'])

    mobo_inputs = MOBOService(db_sync_client=client)
    result = mobo_inputs.run_mobo(params)
    assert type(result) == dict

@pytest.mark.fixme
def test_mobo_inputs():
    mobo_input_payload = {'mobo_id': 'Xy3O7cE1x6iVFj6ukFzIVxjpmficWZh12',
        'mobo_name': 'AICED_QUICK',
        'experiment_id': 'Xy3O7cE1x6iVFj6ukFzIVxjpmficWZh12',
        'experiment_name': 'AICED_QUICK',
        'project_id': '657849cebb20a16a3466db93',
        'training_data_path': 'all_inputs_some_outputs_30 (1).csv',
        'input_variables': ['dcpSpacerThickness',
        'ppSpacerThickness',
        'ipsPressure',
        'upPressure',
        'frictionCf'],
        'input_variables_constraints': [[0.172, 0.192],
        [0.1475, 0.1675],
        [90, 193.3498952],
        [60, 140],
        [0.02, 0.1]],
        'output_variables': ['bucklingPressure', 'maxThinning'],
        'output_variables_objectives': ['max', 'min'],
        'output_variables_thresholds': [111, 11],
        'num_iterations': 1,
        'initialize_experiment': True,
        'run_iterations': True,
        'black_box_method': 'existing_connection',
        'workflow_type': 'optimization',
        'batch_size': 1,
        'socket_url': 'https://scholars1api.corp.databrick.tech',
        'internal_ip': '192.168.0.66',
        'user_id': '657849a6bb20a16a3466db92',}
    
    generates_mobo_inputs(mobo_input_payload)


