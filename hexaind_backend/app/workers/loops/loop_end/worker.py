from app.core.services.action_handler.handler import *
from app.services.workflows.designer.schemas import *
from app.workers.celery_config import *
from app.workers.utils import common_widget_manager
from app.core.celery.celery_worker import create_celery_app
import logging

app = create_celery_app('loop_end_action_worker')

logger = logging.getLogger(__package__)

@app.task(name="task_loop_end")
def task_loop_end(action_id: str, invoked_by_action_id: str = None):

    logger.info("Inside task_loop_end") 
    with common_widget_manager(app, action_id) as (
        action_handler,
        run_record,
        widget,
        new_dataset_dir
    ):

        custom_run_state = action_handler.get_custom_run_state()
        logger.info("got the custom run state")

        if widget.type != WidgetType.LOOP_END:
            logger.exception("Invalid action submited to LOOP_END worker")
            raise Exception("Invalid action submited to LOOP_END worker")
        
        invoked_action_handler = ActionHandler(invoked_by_action_id)
        logger.info("Invoked action handler")
 
        result_ids = invoked_action_handler.action_record.result_ids
        logger.info(f"invoked result ids {result_ids}")

        termination_criteria_config: LoopEndConfig = widget.config

        # updating the custom_run_state of the rescale action
        custom_run_state.total_invoke_count += 1
        is_terminate = False
        if termination_criteria_config.termination_criteria == TerminationCriteria.ON_LOOP_COUNT:

            if custom_run_state.total_invoke_count >= termination_criteria_config.loop_end_config.loop_count: 
                is_terminate = True
                logger.info("loop terminated")
           
        elif termination_criteria_config.termination_criteria == TerminationCriteria.CUSTOM_CODE:
            is_terminate = True #TODO

        custom_run_state.custom_state = dict(terminate=is_terminate)
        logger.info(f"custom run state, {custom_run_state.custom_state}")

        action_handler.update_action_custom_run_state(custom_run_state=custom_run_state) # update the action run state
        logger.info("Updated the custom run state")
        
        # save the results (attaching result record id to the action record)
        action_handler.action_success_handler(action_result_id=result_ids, append_results=False)
        logger.info("Save the results.")
