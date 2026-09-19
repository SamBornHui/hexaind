import asyncio
import json
import logging
import uuid
from pathlib import Path
from app.services.apps.image_analysis.schema import SpatialStatisticsConfig
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
from app.services.workflows.designer.schemas import *
logger = logging.getLogger(__package__)

app = create_celery_app("spatial_statistics_action_worker")


@app.task(name="task_spatial_statistics")
def task_spatial_statistics(action_id: str):

    with common_widget_manager(app, action_id) as (
        action_handler,
        run_record,
        widget,
        new_dataset_dir,
    ):
        if widget.type != WidgetType.SPATIAL_STATISTICS:
            logger.exception("Invalid action submited to SPATIAL_STATISTICS worker")
            raise KeyError("Invalid action submited to SPATIAL_STATISTICS worker")

        prev_action_results_response = action_handler.get_all_inputs_from_prev_action() # Dataset
        logger.info("collected data from the previous action results")
             
        spatial_statistics_config: SpatialStatisticsConfig = widget.config
        # calling image analysis service class
        image_analysis_widget_service = ImageAnalysisWidgetsService(db_sync_client=action_handler.db_client)
        spatial_statistics_results = image_analysis_widget_service.batchProcessing( spatial_statistics_config, run_record.project_id)
        if spatial_statistics_results.exception_detail:
            logger.exception(f"spatial_statistics widget raised exception: {spatial_statistics_results.exception_detail}")
            raise Exception(f"spatial_statistics widget raised exception: {spatial_statistics_results.exception_detail}")
        dataset_id = action_handler.datasets_handler.save_tabular_dataset_helper_sync(input_data=str(spatial_statistics_results.tabular_path), project_id=run_record.project_id, site_id=run_record.site_id, user_id=run_record.owner_id, 
                                                                                                        action_id=action_id, run_id=run_record.id, workflow_id=run_record.workflow_id, 
                                                                                                        name=widget.name, description=widget.description, access_mode=AccessMode.INTERNAL
                                                                                                        )
        action_result_id = action_handler.create_action_result_record(ActionResult(type=ActionResultType.DATASET, result=DatasetActionResult(dataset_id=dataset_id), output_name=widget.outputs[0].name))
        logger.info(f"created the action result record with action result id {action_result_id}")
        
        # # save the results (attaching result record id to the action record)
        action_handler.action_success_handler(action_result_id=[action_result_id], append_results=False)
        