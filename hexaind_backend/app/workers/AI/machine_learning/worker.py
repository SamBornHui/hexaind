import uuid
from app.workers.celery_worker import *
from app.core.services.action_handler.handler import *
from app.services.workflows.designer.schemas import *
from app.services.data.assets.datasets.schemas import Dataset, AccessMode, DatasetLocation
from app.services.AI.machine_learning.lightgbm_regressor.service import LightGbmModelBuilder
from app.config.env_vars import environment
from app.core.celery.celery_worker import create_celery_app
from app.workers.utils import common_widget_manager
import logging

app = create_celery_app('model_builder_action_worker')

logger = logging.getLogger(__package__)

@app.task(name="task_model_builder")
def task_model_builder(action_id: str):
    logger.info("inside task_model_builder")

    with common_widget_manager(app, action_id) as (
        action_handler,
        run_record,
        widget,
        new_dataset_dir
    ):
        if widget.type != WidgetType.MODEL_BUILDER:
            logger.exception("Invalid action submited to MODEL BUILDER worker")
            raise Exception("Invalid action submited to MODEL BUILDER worker")
        
        prev_action_results_response = action_handler.get_all_inputs_from_prev_action()
        logger.info("taken results from previous actions.")

        # Initialize an empty list to store all WidgetResultResponse objects
        prev_action_results: List[WidgetResultResponse] = []

        # terate over all values (which are lists) in the dictionary and extend the prev_action_results list
        for result_list in prev_action_results_response.values():
            prev_action_results.extend(result_list)
        
        # Check the prev action results are compatible with the filter widget
        if not prev_action_results or len(prev_action_results) > 1 or prev_action_results[0].result_type != ActionResultType.DATASET:
            logger.exception("Model builder action got non-compatible result(s) from it's prev action")
            raise Exception("Model builder action got non-compatible result(s) from it's prev action")
        
        # take the prev result
        dataset_record: Dataset = prev_action_results[0].result_value
        dataset_path_info: DatasetLocation = dataset_record.dataset_location[0]

        # assuming getting only one file for now:
        if not dataset_path_info.isfolder:
            dataset_path = dataset_path_info.path
            
        else:
            # Need to add logic for reading multiple files/fodler. TODO
            logger.exception("Filter action got folder as a result from it's prev action.")
            raise Exception("Filter action got folder as a result from it's prev action.")
        
        # initializing the model service and training the model
        unique_file = f"ML_MODEL_{uuid.uuid4()}.pkl"
        model_config: ModelBuilderConfig = widget.config

        # Load appropriate model class
        if model_config.model == ModelType.LIGHT_GBM:
            lightgbm_model_builder = LightGbmModelBuilder(db_async_client=action_handler.db_client)
            model_file_path = lightgbm_model_builder.light_gbm_model_builder_handler(datapath=dataset_path, model_config=model_config, results_path=f"{environment.hexaind_data}/{unique_file}")
        
        # TODO elif  model_config.model == ModelType.DTREE: pass

        # save the dataset details in mongo record 
        model_record_id = action_handler.datasets_handler.save_machine_learning_model_helper_sync(model_file_path=model_file_path, dataset=dataset_record,
                                                                                                  project_id=run_record.project_id, user_id=run_record.owner_id, site_id=run_record.site_id, 
                                                                                                  action_id=action_id, run_id=run_record.id, workflow_id=run_record.workflow_id, 
                                                                                                  name="", description="", tags=[], access_mode=AccessMode.EXTERNAL
                                                                                                  )
        logger.info(f"saved the machine learning model with model record id {model_record_id}")
            
        # saving the action results to the collection
        action_result_id = action_handler.create_action_result_record(ActionResult(type=ActionResultType.MODEL, result=DatasetActionResult(dataset_id=model_record_id)))
        logger.info("created action result record.")

        # save the results (attaching result record id to the action record)
        action_handler.action_success_handler(action_result_id=action_result_id)
        logger.info("saved the results")
