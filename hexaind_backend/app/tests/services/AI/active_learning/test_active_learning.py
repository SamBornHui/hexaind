import warnings
import pytest
warnings.filterwarnings('ignore')
from app.services.AI.mobo.service import MOBOService
from app.services.AI.mobo.schemas import MOBOConfig
from app.core.dao.dao_base import get_db_sync




def generates_mobo_inputs(params,kwarg):
    client=get_db_sync()
    db = client['Hexaind']["workflows"]
    workflow_obj = db.find_one()
    workflow_id  = str(workflow_obj['_id'])
    kwarg['workflow_id'] = workflow_id
    mobo_config = MOBOConfig(**params)
    mobo_inputs = MOBOService(db_sync_client=client)
    result = mobo_inputs.run_mobo(mobo_config,**kwarg)
    print(result)
    assert result.tabular_path != None

@pytest.mark.fixme
def test_mobo_inputs():
    mobo_input_payload = {
     'input_variables': ['dcp_spacer', 'pp_spacer', 'ips_pressure', 'up_pressure', 'friction_coeff', 'upper_radius', 'lower_radius', 't_value', 'lr_opening', 'catcher_depth', 'ips_radius', 'dcr_radius', 'dcp_radius_1', 'dcp_radius_2'],
     'input_variables_constraints': [[0.18, 0.18001799999999998], [0.144, 58], [61.75703273, 116.5307904], [60, 60.006], [0.05, 5], [0.005153495, 25], [0.005101214, 20.030728065], [0.010755824, 35.036], [1.679, 51.729843213], [0.085417634, 40.1], [0.029229092, 50.1], [0.060678336, 30.123677806], [0.027145029, 38.1], [0.02, 25.1]],
     'output_variables': ['buckle_pressure', 'max_thinning'],
     'output_variables_objectives': ['MAXIMUM', 'MINIMUM'],
     'output_variables_thresholds': [111, 11],
     'num_iterations': 2,
     'run_iterations': True,
     # 'experiment_type': 'OPTIMIZATION',
     'experiment_type': 'ACTIVE_LEARNING',
     'widget_type': 'ACTIVE_LEARNING',
     'batch_size': 1,
    #  'constraints_module_id': '65eb2ecab9f582c7c2d6a2b5', #'65a164decbe8ff10ec0dcd55'
    #  'constraints_module_id': None

     }
    kwargs = {'workflow_id': 'Xy3O7cE1x6iVFj6ukFzIVxjpmficWZh123real',
     'workflow_name': 'AICED_CUST_AL_short',
     'project_id': '657849cebb20a16a3466db93',
     'training_data_path': 'app/services/AI/mobo/tests/filtered_inputs_outputs_30.csv',
    #  'training_data_path': '/home/muhammad/Downloads/all_inputs_some_outputs_30 (1).csv',

      'initialize_experiment': True,
    }
    
    generates_mobo_inputs(mobo_input_payload,kwargs)


