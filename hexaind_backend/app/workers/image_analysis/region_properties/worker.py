import asyncio
import json
import logging
import uuid
from pathlib import Path
from app.utils.file_utils import FileUtils
from app.config.env_vars import environment
from app.core.celery.celery_worker import create_celery_app
from app.workers.utils import common_widget_manager
from app.services.data.assets.datasets.schemas import Dataset, DatasetType, AccessMode, DatasetLocation
from app.services.apps.image_analysis.workflow_widgets.service import ImageAnalysisWidgetsService
from app.core.schemas.action_result import (
    ActionResult,
    ActionResultType,
    DictionaryActionResult,
)

from app.core.services.action_handler.handler import *
from app.services.data.assets.image_datasets.schemas import RegionPropertiesConfig
from app.services.workflows.designer.schemas import *
logger = logging.getLogger(__package__)

app = create_celery_app("region_property_action_worker")


@app.task(name="task_region_property")
def task_region_property(action_id: str):

    with common_widget_manager(app, action_id) as (
        action_handler,
        run_record,
        widget,
        new_dataset_dir,
    ):
        if widget.type != WidgetType.REGION_PROPERTY:
            logger.exception("Invalid action submited to REGION_PROPERTY worker")
            raise KeyError("Invalid action submited to REGION_PROPERTY worker")

        prev_action_results_response = action_handler.get_all_inputs_from_prev_action() # Dataset
        logger.info("collected data from the previous action results")
        # Initialize an empty list to store all WidgetResultResponse objects
        prev_action_results: List[WidgetResultResponse] = []
        # iterate over all values (which are lists) in the dictionary and extend the prev_action_results list
        for result_list in prev_action_results_response.values():
            prev_action_results.extend(result_list)
        
        # Check the prev action results are compatible with the filter widget
        if not prev_action_results or len(prev_action_results) > 1 or prev_action_results[0].result_type != ActionResultType.DICTIONARY:
            logger.exception("REGION_PROPERTIES action got non-compatible result(s) from it's prev action")
            raise Exception("REGION_PROPERTIES action got non-compatible result(s) from it's prev action")
        
        # take the prev result
        selected_datasets = []
        if prev_action_results[0].result_type == ActionResultType.DICTIONARY:
            json_string = prev_action_results[0].result_value.dict_value
            prev_widget = json.loads(json_string)
            selected_datasets = prev_widget["image_datasets"]
             
        region_props_config: RegionPropertiesConfig = widget.config
        # calling image analysis service class
        image_analysis_widget_service = ImageAnalysisWidgetsService(db_sync_client=action_handler.db_client)
        reg_props_results = asyncio.run( image_analysis_widget_service.process_region_props(selected_datasets, region_props_config,run_record.project_id))
        
        dataset_id = action_handler.datasets_handler.save_tabular_dataset_helper_sync(input_data=str(reg_props_results['reg_props_results_file']), project_id=run_record.project_id, site_id=run_record.site_id, user_id=run_record.owner_id, 
                                                                                                        action_id=action_id, run_id=run_record.id, workflow_id=run_record.workflow_id, 
                                                                                                        name=widget.name, description=widget.description, access_mode=AccessMode.INTERNAL
                                                                                                        )
        action_result_id = action_handler.create_action_result_record(ActionResult(type=ActionResultType.DATASET, result=DatasetActionResult(dataset_id=dataset_id), output_name=widget.outputs[0].name))
        logger.info(f"created the action result record with action result id {action_result_id}")
        
        # # save the results (attaching result record id to the action record)
        action_handler.action_success_handler(action_result_id=[action_result_id], append_results=False)
        