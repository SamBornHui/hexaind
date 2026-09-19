import json

from app.config.env_vars import thermocalc_environment
from app.core.services.action_handler.handler import *
from app.services.apps.thermocalc_web_service.schemas import ThermoCalcJobStatus
from app.services.workflows.designer.schemas import *
from app.utils.file_utils import FileUtils
from app.core.celery.celery_worker import create_celery_app
from app.core.celery.global_config import THERMOCALC_ACTION_WORKER_DEFAULT_QUEUE

from app.services.AI.thermocalc.service import ThermocalcService
from app.services.apps.thermocalc_web_service.service import ThermoCalcAPIService
from app.core.db.db_utils import get_thermocalc_db_sync

import pandas as pd
import logging
from uuid import uuid4

# Initialize the Celery app
app = create_celery_app('thermocalc_tasks_worker', default_queue=THERMOCALC_ACTION_WORKER_DEFAULT_QUEUE)
logger = logging.getLogger(__package__)


@app.task(name="task_thermocalc_sub_action")
def task_thermocalc_sub_action(parent_job_id: str, data_path: str, start_index: int, TC23A_HOME: str, 
                            TC23B_HOME: str, 
                            LSHOST: str,
                            connection_type:str):
    try:
        output_file_name = Path(data_path).name.split('.')[0]
        logger.info(f"received thermocalc_action with {parent_job_id} and {output_file_name}")
        db_client = get_db_sync()
        thermocalc_service = ThermocalcService(db_sync_client=db_client)
        
        db_thermocalc_client  =  get_thermocalc_db_sync()
        thermocalc_api_service = ThermoCalcAPIService(db_sync_client=db_thermocalc_client)
        job_config = thermocalc_api_service.get_job_sync(parent_job_id)

        source_file_path = str(Path(data_path).parent/f"extracted_{uuid4()}.csv")
        with open(data_path, 'r') as file:
            json_data = json.load(file)
        df = pd.DataFrame(json_data)
        df.to_csv(source_file_path, index=False)
        logger.info(f"starting compute_thermodynamic_features with {parent_job_id} and {output_file_name}")

        connection_config ={
                            "TC23A_HOME": TC23A_HOME, 
                            "TC23B_HOME": TC23B_HOME, 
                            "LSHOST": LSHOST,
        }

        thermodynamic_features_data = thermocalc_service.compute_thermodynamic_features(
            connection_id=job_config.connector_id,
            python_file_path=job_config.module_path,
            input_features=job_config.input_features,
            output_features=job_config.output_features,
            input_file_path=source_file_path,
            start=start_index,
            end=0,
            connection_config =connection_config,
            connection_type = connection_type,
            read_entire_file=True
            )
        logger.info(f"completed compute_thermodynamic_features with {parent_job_id} and {output_file_name}")
        results_file_path = thermocalc_environment.thermocalc_home / f"task_outputs/{parent_job_id}/{uuid4()}_output_{output_file_name}.csv"
        results_file_path.parent.mkdir(parents=True, exist_ok=True)
        # saving the results to disk
        FileUtils.SaveTabularFileToDisk(data=thermodynamic_features_data, destination_path=str(results_file_path))
        logger.info(f"saved results with {parent_job_id} and {output_file_name} to {results_file_path.name}")
        logger.info(f"triggered complete_action with {parent_job_id} and {output_file_name}")
        # api call for now, we can directly hit db too
        thermocalc_api_service.complete_task_sync(parent_job_id)

        job_config = thermocalc_api_service.get_job_sync(parent_job_id)
        logger.info(f"completed task with {parent_job_id} and {output_file_name}, {job_config.status}")
        if job_config.status == ThermoCalcJobStatus.COMPLETED and job_config.results_file_path is None:
            # aggregate results
            try:
                aggregated_results_path=thermocalc_environment.thermocalc_home / f"job_results/{parent_job_id}/{uuid4()}.csv"
                aggregated_results_path.parent.mkdir(parents=True, exist_ok=True)
                batch_job_result_paths = list(results_file_path.parent.glob('*.csv'))
                ThermocalcService.thermocalc_sub_action_results_aggregator(
                    file_paths=batch_job_result_paths, result_file_path=str(aggregated_results_path)
                )
                thermocalc_api_service.update_results_path(parent_job_id,str(aggregated_results_path))
            except Exception as e:
                logger.error(f"unable to update aggregated results {e}")

    except Exception as e:
        logger.exception(
            f"Error occurred while completing task_thermocalc_sub_action {parent_job_id},{parent_job_id},{start_index}:{e}")
