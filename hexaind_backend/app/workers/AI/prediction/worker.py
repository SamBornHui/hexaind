import os
import logging
from pathlib import Path

from app.core.services.action_handler.handler import *
from app.services.workflows.designer.schemas import *
from app.config.env_vars import environment
from app.services.data.assets.datasets.schemas import (
    Dataset,
    AccessMode,
    DatasetLocation,
    DatasetSubType,
)
from app.services.AI.prediction.service import PredictionService
from app.workers.utils import common_widget_manager
from app.core.celery.global_config import PREDICTION_ACTION_WORKER_DEFAULT_QUEUE
from app.core.celery.celery_worker import (
    create_celery_app,
)  # create_celery_non_global_app #create_celery_app


app = create_celery_app(
    "prediction_action_worker", default_queue=PREDICTION_ACTION_WORKER_DEFAULT_QUEUE
)
logger = logging.getLogger(__package__)


@app.task(name="task_prediction")
def task_prediction(action_id: str):
    logger.info("inside task_prediction")

    with common_widget_manager(app, action_id) as (
        action_handler,
        run_record,
        widget,
        new_dataset_dir
    ):

        action_record: Action = action_handler.action_record

        if widget.type != WidgetType.PREDICTION:
            logger.exception("Invalid action submitted to prediction worker")
            raise Exception("Invalid action submitted to prediction worker")

        dataset_id = None

        # setting result directory
        results_folder = Path(
                    new_dataset_dir
                )
        results_folder.mkdir(parents=True, exist_ok=True)
        results_folder = str(results_folder)

        prev_action_results_response = (
            action_handler.get_all_inputs_from_prev_action()
        )  # Dataset
        logger.info("collected data from the previous action results")

        # Initialize an empty list to store all WidgetResultResponse objects
        prev_action_results: List[WidgetResultResponse] = []

        # iterate over all values (which are lists) in the dictionary and extend the prev_action_results list
        for result_list in prev_action_results_response.values():
            prev_action_results.extend(result_list)

        # Check the prev action results are compatible with the filter widget
        if (
            not prev_action_results
            or len(prev_action_results) > 1
            or prev_action_results[0].result_type != ActionResultType.DATASET
        ):
            logger.exception(
                "prediction action got non-compatible result(s) from it's prev action"
            )
            raise Exception(
                "prediction action got non-compatible result(s) from it's prev action"
            )

        # take the prev result
        dataset_record: Dataset = prev_action_results[0].result_value
        dataset_path_info: DatasetLocation = dataset_record.dataset_location[0]

        # assuming getting only one file for now:
        if not dataset_path_info.isfolder:
            dataset_path = dataset_path_info.path
        else:
            # Need to add logic for reading multiple files/fodler. TODO
            logger.exception(
                "prediction action got folder as a result from it's prev action."
            )
            raise Exception(
                "prediction action got folder as a result from it's prev action."
            )

        # initializing the prediction service
        pred_config: PredictionConfig = widget.config

        # Building kwargs for prediction-service
        kwargs = dict(
            wf_id=run_record.workflow_id,
            project_id=run_record.project_id,
            data_path=Path(dataset_path),
            result_folders=results_folder,
            dataset_record=dataset_record,
        )

        logger.info("prediction kwargs:   ", kwargs)
        # calling prediction service class
        pred_service = PredictionService(db_sync_client=action_handler.db_client)
        pred_output = pred_service.get_prediction(pred_config, **kwargs)

        if pred_output.exception_detail:
            logger.exception(
                f"prediction widget raised exception: {pred_output.exception_detail}"
            )
            raise Exception(
                f"prediction widget raised exception: {pred_output.exception_detail}"
            )

        dataset_id = action_handler.datasets_handler.save_tabular_dataset_helper_sync(
            input_data=str(pred_output.tabular_path),
            project_id=run_record.project_id,
            site_id=run_record.site_id,
            user_id=run_record.owner_id,
            action_id=action_id,
            run_id=run_record.id,
            workflow_id=run_record.workflow_id,
            name=widget.name,
            description=widget.description,
            access_mode=AccessMode.INTERNAL,
            input_data_sub_type=DatasetSubType.PREDICTION_RESULTS
        )

        logger.info(f"Saved the tabular dataset with id {dataset_id}")

        # saving the action results to the collection
        action_result_id = action_handler.create_action_result_record(
            ActionResult(
                type=ActionResultType.DATASET,
                result=DatasetActionResult(dataset_id=dataset_id),
                output_name=widget.outputs[0].name,
            )
        )
        logger.info(
            f"created the action result record with action result id {action_result_id}"
        )

        # updating the custom_run_state of the prediction action only if it is in cycle
        if action_record.is_cycle:
            # fetch custom run state for widget:
            custom_run_state = action_handler.get_custom_run_state()
            logger.info(f"custom run state of prediction {custom_run_state}")

            # update the custom run-state with intermediate results
            custom_run_state.total_invoke_count += 1
            custom_run_state.cycle_intermediate_results.append(
                CycleIntermediateResults(
                    invocation_num=custom_run_state.total_invoke_count,
                    result_record_ids=[action_result_id],
                )
            )
            action_handler.update_action_custom_run_state(
                custom_run_state=custom_run_state
            )  # update the action run state
            logger.info("Updated action custom state of prediction widget.")

        # # save the results (attaching result record id to the action record)
        action_handler.action_success_handler(
            action_result_id=[action_result_id], append_results=False
        )
