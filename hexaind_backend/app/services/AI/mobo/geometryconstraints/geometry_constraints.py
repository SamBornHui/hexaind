
from pathlib import Path
import os
import sys
import logging
import zipfile
import traceback
import pandas as pd
import logging as logger
from app.services.data.assets.modules.service import *
from app.services.data.assets.modules.utils import import_module_from_path

logger = logging.getLogger(__package__)
logger.setLevel(logging.DEBUG)
class GCService:

    def get_custom_driver_data(self, module_id, db_syc_client=None):
        logger.info('in get custom driver data')
        
        try:
            ms = ModuleService(db_sync_client=db_syc_client)
            modules_info = ms.get_module_record_by_id(module_id=module_id)
            module_path = modules_info.module_location.path
            if modules_info.module_location.extension == 'ZIP':
                logging.info('zip block')
                modules_dir = os.path.dirname(modules_info.module_location.path)
                modules_dir = Path(modules_dir)
                if not (modules_dir/'custom_driver.py').is_file():
                    logger.info('going to extract zip file')
                    with zipfile.ZipFile(modules_info.module_location.path, 'r') as zip_ref:
                        # Extract all contents to the specified directory
                        zip_ref.extractall(modules_dir)
                else:
                    logger.info('zip already extracted')

                sys.path.append(str(modules_dir))
                module_path = str(modules_dir/'custom_driver.py')

            self.custom_module = import_module_from_path(module_path=module_path)
        except:
            traceback.print_exc()
            dev_msg = f'Error in module block: {module_id}'
            logger.error(dev_msg,)
    

    def execute_cust_preprocess(self, parameters_file):
        try:
            fail_flag, rescale_files = self.custom_module.PreProcess(Path(parameters_file))
            return fail_flag, rescale_files
        except:
            traceback.print_exc()
            dev_msg = f'Error in executing validation block '
            logger.error(dev_msg)
            
    def output_path_dir(self, parent, exp_id):
        exp_id_path = os.path.join(parent, exp_id)
        os.makedirs(exp_id_path, exist_ok=True)
        return exp_id_path
    
    def apply_gc(self, parameters) -> any:
        try:

            observations = parameters['next_observations']
            constraints_module_id = parameters['constraints_module_id']
            db_syc_client = parameters['db_syc_client']
            self.get_custom_driver_data(constraints_module_id, db_syc_client=db_syc_client)

            for idx in  observations:
                observations[idx]['fail_flag'], observations[idx]['rescale_files'] = self.execute_cust_preprocess(observations[idx]['iter_csv_path'])

            return observations
        except Exception as e:
            traceback.print_exc()
            return e






    
    
