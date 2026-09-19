from pymongo import MongoClient
import warnings
warnings.filterwarnings('ignore')
import sys
sys.path.append('../../../../../')
from app.services.AI.rescale.service import RescaleService
from app.services.AI.rescale.schemas import RescaleResponse


def perform_rescale(configs, kw_args):
    db_config = dict(db_address = '0.0.0.0' + ':27017', db_name = "Databrick", db_username = "Databrick", db_password = "test")
    client = MongoClient(db_config['db_address'],
                            username=db_config['db_username'],
                            password=db_config['db_password'],
                            authSource=db_config['db_name'])

    obj = RescaleService(db_sync_client=client)
    result = obj.run_rescale(parameters=configs, **kw_args)
    assert result.model_fields == RescaleResponse.model_fields

def test_rescale():
    
    configs = {'rescale_connector_id': '65a517707518c363e4c0d3fb',
    'rescale_configs': {'name': 'Sample ABAQUS Simulation',
    'test_mode': True,
    'run_job': False,
    'files_detail': [{'file_name': 'abaqus_job.py',
        'file_path': '/hexaind-data/hexaind-datasets/connection/65a517707518c363e4c0d3fb/abaqus_job.py',
        'upload_rescale': True,
        'rescale_id': ''},
    {'file_name': 'PostProcessing.py',
        'file_path': 'PostProcessing.py',
        'upload_rescale': True,
        'rescale_id': 'GZNYxh'}],
    'software': {'analysis': {'code': 'abaqus-dsls',
        'version': '2021-golden-DSLS'},
    'hardware': {'walltime': 3,
        'coreType': 'starlite_max',
        'slots': 1,
        'coresPerSlot': 4},
    'command': 'abaqus cae noGUI=MG_Forming.py; abaqus job=FormingJob.inp cpus=$RESCALE_CORES_PER_SLOT mp_mode=mpi interactive parallel=domain double=both output_precision=full; abaqus cae noGUI=MG_Springback.py; abaqus job=SpringbackJob.inp cpus=$RESCALE_CORES_PER_SLOT mp_mode=mpi interactive double=both output_precision=full; abaqus cae noGUI=MG_Buckling.py; abaqus job=BucklingJob.inp cpus=$RESCALE_CORES_PER_SLOT mp_mode=mpi interactive double=both output_precision=full; abaqus python PostProcessing.py;abaqus cae noGUI=Visualizer.py',
    'reusable_job_file': 'custom_driver.py,MG_Forming.py,MG_Springback.py,MG_Buckling.py,PostProcessing.py,Visualizer.py,scaler.pkl,gp_scaling.pkl,sedata.csv',
    'dynamic_job_file': 'param_values.csv',
    'pre_python': None,
    'post_python': None,
    'output_file': 'PerfMetricsFile.csv',
    'visualize_files': ['ShellGeometry.png',
        'ShellGeometry_Closeup.png',
        'FormingAnimation_Script.avi'],
    'envVars': {'DSLS_LICENSE_FILE': '4085@novelis'}}}}
    kw_args = {'workflow_name': 'AICED_CUST',
               'mobo_output':'AICED_TEST/mobo_output.csv'    }
    perform_rescale(configs, kw_args)
