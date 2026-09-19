from app.core.services.action_handler.handler import *
from app.services.workflows.designer.schemas import *
from app.services.data.assets.datasets.schemas import Dataset, AccessMode, DatasetLocation, DatasetType, \
    DatasetMetadata, DatasetSourceFormats
from app.services.AI.rescale.service import RescaleService
from app.services.AI.rescale.schemas import RescaleConfig
from app.core.celery.celery_worker import create_celery_app #create_celery_non_global_app 
from app.core.celery.global_config import RESCALE_ACTION_WORKER_DEFAULT_QUEUE
from app.workers.utils import common_widget_manager
from app.services.data.assets.datasets.schemas import WorkflowDatasetCustomInformation, WidgetType
from app.services.AI.rescale.rescale_methods import form_rescale_custom_information
import logging

# Initialize the Celery app
app = create_celery_app('rescale_action_worker', default_queue=RESCALE_ACTION_WORKER_DEFAULT_QUEUE)
logger = logging.getLogger(__package__)

@app.task(name="task_rescale", acks_late=False)
def task_rescale(action_id: str):
    logger.info("inside task rescale")

    with common_widget_manager(app, action_id) as (
        action_handler,
        run_record,
        widget,
        new_dataset_dir
    ):

        custom_run_state = action_handler.get_custom_run_state()
        logger.info(f"custom run state {custom_run_state}")

        if widget.type != WidgetType.RESCALE:
            logger.exception("Invalid action submitted to RESCALE worker")
            raise Exception("Invalid action submitted to RESCALE worker")
        metadata = DatasetMetadata(
            data_source=DatasetSourceFormats.GENERATED_IN_WORKFLOW_EXECUTION_FORMAT.format(widget.type.value.lower()))

        prev_action_results_response = action_handler.get_all_inputs_from_prev_action() # Dataset
        logger.info("taken all inputs from previous action")

        # Initialize an empty list to store all WidgetResultResponse objects
        prev_action_results: List[WidgetResultResponse] = []

            # iterate over all values (which are lists) in the dictionary and extend the prev_action_results list
        for result_list in prev_action_results_response.values():
            prev_action_results.extend(result_list)
            
        # Check the prev action results are compatible with the filter widget
        if not prev_action_results or len(prev_action_results) > 1 or prev_action_results[0].result_type != ActionResultType.DATASET:
            logger.exception("Rescale action got non-compatible result(s) from it's prev action")
            raise Exception("Rescale action got non-compatible result(s) from it's prev action")
        
        # take the prev result
        dataset_record: Dataset = prev_action_results[0].result_value
        dataset_path_info: DatasetLocation = dataset_record.dataset_location[0]

        if dataset_record.dataset_type != DatasetType.TABULAR:
            logger.exception("Rescale action got non-compatible result type from it's prev action")
            raise Exception("Rescale action got non-compatible result type from it's prev action")
        
        rescale_config: RescaleConfig = widget.config
        kw_args = {
            'workflow_name': run_record.name,
            'mobo_output': dataset_path_info.path,
            "user_id": run_record.owner_id, 
            }
        
        # setting result directory
        results_folder = Path(
                    new_dataset_dir
                )
        results_folder.mkdir(parents=True, exist_ok=True)
        results_folder = str(results_folder)
        kw_args['results_folder'] = results_folder

        rescale_service = RescaleService(db_sync_client=action_handler.db_client)
        
        rescale_results = rescale_service.run_rescale(rescale_config, **kw_args)

        if rescale_results.exception_detail:
            logger.exception(f"rescale widget raised exception: {rescale_results.exception_detail}")
            raise Exception(f"rescale widget raised exception: {rescale_results.exception_detail}")
        
        custom_information: WorkflowDatasetCustomInformation = WorkflowDatasetCustomInformation(
            widget_type=WidgetType.RESCALE,
            custom_information=form_rescale_custom_information(rescale_results.tabular_path)
        )

        dataset_id = action_handler.datasets_handler.save_tabular_dataset_helper_sync(
            input_data=str(rescale_results.tabular_path), project_id=run_record.project_id, site_id=run_record.site_id,
            user_id=run_record.owner_id,
            action_id=action_id, run_id=run_record.id, workflow_id=run_record.workflow_id,
            name=widget.name, description=widget.description, access_mode=AccessMode.INTERNAL,
            custom_information=custom_information, metadata=metadata)
        
        # saving the action results to the collection
        action_result_id = action_handler.create_action_result_record(ActionResult(type=ActionResultType.DATASET, result=DatasetActionResult(dataset_id=dataset_id), output_name=widget.outputs[0].name))
        logger.info("created action result record.")

        # updating the custom_run_state of the rescale action
        custom_run_state.total_invoke_count += 1
        custom_run_state.cycle_intermediate_results.append(CycleIntermediateResults(invocation_num=custom_run_state.total_invoke_count, result_record_ids=[action_result_id]))
        action_handler.update_action_custom_run_state(custom_run_state=custom_run_state) # update the action run state
        logger.info("Updated action custom state")

        # save the results (attaching result record id to the action record)
        action_handler.action_success_handler(action_result_id=action_result_id, append_results=False)
        logger.info("Saving the results")
