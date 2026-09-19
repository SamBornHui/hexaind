import pandas as pd
import traceback
from app.workers.celery_worker import *
from app.core.services.action_handler.handler import *
from app.services.workflows.designer.schemas import *
from app.services.data.assets.datasets.schemas import Dataset, AccessMode, DatasetLocation
from app.services.AI.post_rescale.service import PostRescaleService
from app.services.AI.post_rescale.schemas import PostRescaleConfig
from app.workers.celery_config import *
from app.workers.utils import common_widget_manager
import celery
import logging

# Initialize the Celery app
app = celery.Celery('post_rescale_worker', 
                    broker=celery_broker_url,
                    broker_connection_retry=broker_connection_retry,
                    broker_connection_max_retries=broker_connection_max_retries,  # Retry indefinitely
                    broker_connection_retry_delay=broker_connection_retry_delay)

logger = logging.getLogger(__package__)


def notify_end_action_to_action_manager(app, action_id: str):
    app.send_task("end_action", 
                  kwargs={"action_id": action_id},
                  queue="start_end",
                  routing_key="end"
                )

@app.task(name="task_post_rescale")
def task_post_rescale(action_id: str):
    logger.info("inside task post rescale")

    with common_widget_manager(app, action_id) as (
        action_handler,
        run_record,
        widget,
        new_dataset_dir
    ):
        if widget.type != WidgetType.POST_RESCALE:
            logger.exception("Invalid action submitted to MOBO worker")
            raise Exception("Invalid action submited to MOBO worker")
        
        prev_action_results_response = action_handler.get_all_inputs_from_prev_action()
        logger.info("taken all inputs from previous action")

        # Initialize an empty list to store all WidgetResultResponse objects
        prev_action_results: List[WidgetResultResponse] = []

        # terate over all values (which are lists) in the dictionary and extend the prev_action_results list
        for result_list in prev_action_results_response.values():
            prev_action_results.extend(result_list)
        
        # Check the prev action results are compatible with the filter widget
        if not prev_action_results or len(prev_action_results) > 1 or prev_action_results[0].result_type != ActionResultType.PATH:
            logger.exception("Rescale action got non-compatible result(s) from it's prev action")
            raise Exception("Rescale action got non-compatible result(s) from it's prev action")
        
        # take the prev result
        rescale_result: RescaleActionResult = prev_action_results[0].result_value

        # validating previous action result
        if not os.path.exists(rescale_result.rescale_output):
            logger.exception("Rescale action got string path which does not exists as a result from it's prev action.")
            raise Exception("Rescale action got string path which does not exists as a result from it's prev action.")
        
        # initializing the post rescale service 
        post_rescale_config: PostRescaleConfig = widget.config

        post_rescale_config.rescale_output = rescale_result.rescale_output 
        # calling post rescale service class
        post_rescale_service = PostRescaleService(db_sync_client=action_handler.db_client)
        post_rescale_output = post_rescale_service.run_post_rescale(post_rescale_config)
        
        # saving the action results to the collection
        action_result_id = action_handler.create_action_result_record(ActionResult(type=ActionResultType.PATH, result=PostRescaleActionResult(post_rescale_output=post_rescale_output.json_path)))
        logger.info("created action result record.")

        # save the results (attaching result record id to the action record)
        action_handler.action_success_handler(action_result_id=action_result_id)
        logger.info("Saving the results")
