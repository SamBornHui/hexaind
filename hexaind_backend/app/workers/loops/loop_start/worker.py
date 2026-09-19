from app.core.services.action_handler.handler import *
from app.services.workflows.designer.schemas import *
from app.workers.celery_config import *
from app.core.celery.celery_worker import create_celery_app
from app.workers.utils import common_widget_manager
import logging

app = create_celery_app('loop_start_action_worker')
logger = logging.getLogger(__package__)
 
@app.task(name="task_loop_start")
def task_loop_start(action_id: str, invoked_by_action_id: str = None):
    logger.info("Inside task loop start")
 
    with common_widget_manager(app, action_id) as (
        action_handler,
        run_record,
        widget,
        new_dataset_dir
    ):

        custom_run_state = action_handler.get_custom_run_state()
        logger.info(f"current custom run state is {custom_run_state}")

        if widget.type != WidgetType.LOOP_START:
            logger.error("Invalid action submited to LOOP_START worker")
            raise Exception("Invalid action submited to LOOP_START worker")
        
        invoked_action_handler = ActionHandler(invoked_by_action_id)
        logger.info("invoked action handler.")
 
        result_ids = invoked_action_handler.action_record.result_ids
        logger.info(f"Result id's from loop start worker: {result_ids}")


        # updating the custom run state
        custom_run_state.total_invoke_count += 1
        action_handler.update_action_custom_run_state(custom_run_state=custom_run_state) # update the action run state
        logger.info("Updated the action run state.")

        # save the results (attaching result record id to the action record)
        action_handler.action_success_handler(action_result_id=result_ids, append_results=False)
        logger.info("Saved the results")
