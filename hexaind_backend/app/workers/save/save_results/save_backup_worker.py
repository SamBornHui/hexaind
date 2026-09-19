from app.core.services.action_handler.handler import *
from app.services.workflows.designer.schemas import *
from app.workers.celery_config import *
from app.workers.utils import common_widget_manager
from app.core.celery.celery_worker import create_celery_app
def task_save(action_id: str):

    with common_widget_manager(app, action_id) as (
        action_handler,
        run_record,
        widget
    ):
        if widget.type != WidgetType.SAVE:
            raise Exception("Invalid action submited to SAVE worker")
        
        prev_action_results_response = action_handler.get_all_inputs_from_prev_action()

        # Initialize an empty list to store all WidgetResultResponse objects
        prev_action_results: List[WidgetResultResponse] = []

        # terate over all values (which are lists) in the dictionary and extend the prev_action_results list
        for result_list in prev_action_results_response.values():
            prev_action_results.extend(result_list)
        
        # Check the prev action results are compatible with the filter widget
        if not prev_action_results or len(prev_action_results) > 1: # TODO If widget have multiple outputs
            raise Exception("Filter action got non-compatible result from it's prev action")
        
        if prev_action_results[0].result_type == ActionResultType.DATASET:
            """save tabular dataset"""
            dataset_record: Dataset = prev_action_results[0].result_value
            save_config: SaveConfig = widget.config.config
            result = action_handler.update_dataset_record_access_mode(dataset_id=dataset_record.id, name=save_config.name, description=save_config.description, access_mode=AccessMode.EXTERNAL)

            if result:
                # saving the action results to the collection
                action_result_id = action_handler.create_action_result_record(ActionResult(type=ActionResultType.DATASET, result=DatasetActionResult(dataset_id=dataset_record.id))) 

                # save the results (attaching result record id to the action record)
                action_handler.action_success_handler(action_result_id=action_result_id)
            else:
                raise Exception("Unable to save the dataset")
        
        # TODO Extend for other types of result type saves (Ex: model building pickle file, etc.)
            
        # elif prev_action_results[0].result_type == ActionResultType.MODEL:
        #     pass