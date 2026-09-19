from app.utils.file_utils import FileUtils
from app.core.services.action_handler.handler import *
from app.services.workflows.designer.schemas import *
from app.config.env_vars import environment
from app.services.data.assets.datasets.schemas import Dataset, AccessMode, DatasetLocation
from app.services.AI.gaussian_process_cls.service import GPCService
from app.workers.utils import common_widget_manager
from app.core.celery.global_config import GPC_ACTION_WORKER_DEFAULT_QUEUE
from app.core.celery.celery_worker import create_celery_app #create_celery_non_global_app #create_celery_app
from pathlib import Path
import logging

app = create_celery_app('gpc_action_worker', default_queue=GPC_ACTION_WORKER_DEFAULT_QUEUE)
logger = logging.getLogger(__package__)

@app.task(name="task_gpc")
def task_gpc(action_id: str):
    logger.info("inside task_gpc")
    with common_widget_manager(app, action_id) as (
        action_handler,
        run_record,
        widget,
        new_dataset_dir
    ):
        if widget.type != WidgetType.GPC:
            logger.exception("Invalid action submited to GPC worker")
            raise Exception("Invalid action submited to GPC worker")
        
        dataset_id = None
        # setting result directory
        results_folder = Path(
                    new_dataset_dir
                )
        results_folder.mkdir(parents=True, exist_ok=True)
        results_folder = str(results_folder)
 
        prev_action_results_response = action_handler.get_all_inputs_from_prev_action() # Dataset
        logger.info("collected data from the previous action results")
        # Initialize an empty list to store all WidgetResultResponse objects
        prev_action_results: List[WidgetResultResponse] = []
        # iterate over all values (which are lists) in the dictionary and extend the prev_action_results list
        for result_list in prev_action_results_response.values():
            prev_action_results.extend(result_list)
        
        # Check the prev action results are compatible with the filter widget
        if not prev_action_results or len(prev_action_results) > 1 or prev_action_results[0].result_type != ActionResultType.DATASET:
            logger.exception("GPC action got non-compatible result(s) from it's prev action")
            raise Exception("GPC action got non-compatible result(s) from it's prev action")
        
        # take the prev result
        dataset_record: Dataset = prev_action_results[0].result_value
        dataset_path_info: DatasetLocation = dataset_record.dataset_location[0]
        # assuming getting only one file for now:
        if not dataset_path_info.isfolder:
            dataset_path = dataset_path_info.path
        else:
            # Need to add logic for reading multiple files/fodler. TODO
            logger.exception("GPC action got folder as a result from it's prev action.")
            raise Exception("GPC action got folder as a result from it's prev action.")
        
        # initializing the GPC service 
        GPC_config: GPCConfig = widget.config
        # Building kwargs for GPC-service
        kwargs = dict(run_id=run_record.id, 
                        wf_id=run_record.workflow_id,
                        project_id=run_record.project_id,
                        data_path=Path(dataset_path),
                        result_folders=results_folder,
                        dataset_name=dataset_record.name,
                        user_id=run_record.owner_id,
                        user_name=run_record.owner_name,
                        site_id=run_record.site_id,
                        dataset_record=dataset_record,
                        widget_urn = widget.urn,
                        )
        

        # calling GPC service class
        gpc_service = GPCService(db_sync_client=action_handler.db_client)
        gpc_output = gpc_service.train_gpc(GPC_config, **kwargs)
        if gpc_output.exception_detail:
            logger.exception(f"GPC widget raised exception: {gpc_output.exception_detail}")
            raise Exception(f"GPC widget raised exception: {gpc_output.exception_detail}")
        
        
        dataset_id = action_handler.datasets_handler.save_tabular_dataset_helper_sync(input_data=str(gpc_output.tabular_path), project_id=run_record.project_id, site_id=run_record.site_id, user_id=run_record.owner_id, 
                                                                                                        action_id=action_id, run_id=run_record.id, workflow_id=run_record.workflow_id, 
                                                                                                        name=widget.name, description=widget.description, access_mode=AccessMode.INTERNAL
                                                                                                        )
        logger.info(f"Saved the tabular dataset with id {dataset_id}")   
       #To facilitate the smooth running of old workflows , we use if-else check  
        if len(widget.outputs) == 1:
            action_result_id = action_handler.create_action_result_record(ActionResult(type=ActionResultType.DATASET, result=DatasetActionResult(dataset_id=dataset_id), output_name=widget.outputs[0].name))
            logger.info(f"created the action result record with action result id {action_result_id}")
            action_handler.action_success_handler(action_result_id=[action_result_id], append_results=False)

        else:
            action_result_id = action_handler.create_action_result_record(ActionResult(type=ActionResultType.DATASET, result=DatasetActionResult(dataset_id=dataset_id), output_name=widget.outputs[0].name))
            action_result_id_2 = action_handler.create_action_result_record(ActionResult(type=ActionResultType.FILE_OR_FOLDER_PATH, result=FileActionResult(file_path_value=gpc_output.models_path), output_name=widget.outputs[1].name))
            logger.info(f"created the action result record with action result id {action_result_id}")


            # # save the results (attaching result record id to the action record)
            action_handler.action_success_handler(action_result_id=[action_result_id,action_result_id_2], append_results=False)
