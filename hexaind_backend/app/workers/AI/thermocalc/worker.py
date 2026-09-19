import time

from app.config.env_vars import thermocalc_environment
from app.core.services.action_handler.handler import *
from app.services.apps.thermocalc_web_service.schemas import ThermoCalcJobStatus, ThermoCalcJobRegisterationRequest
from app.services.data.assets.modules.service import ModuleService
from app.services.workflows.designer.schemas import *
from app.workers.AI.thermocalc.worker_utils import (
    create_job,
    register_job,
    receive_task,
    get_status,
    get_batches_count,
    batches_data_generator,
    get_results_file,
)
from app.core.db.db_utils import get_db_async, get_db_sync
from app.services.admin.connectors.schemas import Connector
from app.workers.utils import common_widget_manager
from app.core.celery.celery_worker import create_celery_app
from app.core.celery.global_config import THERMOCALC_ACTION_WORKER_DEFAULT_QUEUE
from app.services.data.assets.datasets.schemas import (
    Dataset,
    DatasetType,
    DatasetSubType,
    DatasetLocation,
)

import logging
from uuid import uuid4

# Initialize the Celery app
app = create_celery_app(
    "thermocalc_action_worker", default_queue=THERMOCALC_ACTION_WORKER_DEFAULT_QUEUE
)
logger = logging.getLogger(__package__)


@app.task(name="task_thermocalc")
def task_thermocalc_dispatcher(action_id: str):
    with common_widget_manager(app, action_id) as (
        action_handler,
        run_record,
        widget,
        new_dataset_dir,
    ):

        # validations
        if widget.type != WidgetType.THERMOCALC:
            raise Exception("Invalid action submited to Thermocalc worker")
        action_record: Action = action_handler.action_record

        inputs: List[WidgetResultResponse] = list(
            action_handler.get_widget_inputs_from_prev_actions(widget.inputs).values()
        )
        if not inputs or len(inputs) < 1 or len(inputs) > 2:
            raise Exception(
                f"Therocalc {widget.type} expecting one input, But got {len(inputs)}"
            )
        if inputs[0] is None or inputs[0].result_type != ActionResultType.DATASET:
            raise Exception(
                f"Therocalc previous widgets results must be {ActionResultType.DATASET}. Can't perfrom the operation"
            )
        dataset_record: Dataset = inputs[0].result_value
        if dataset_record is None or dataset_record.dataset_type != DatasetType.TABULAR:
            raise Exception(
                f"Therocalc Didn't get dataset of type {DatasetType.TABULAR}. But got {dataset_record.dataset_type}"
            )
        dataset_path_info: DatasetLocation = dataset_record.dataset_location[0]
        # assuming getting only one file for now:
        if dataset_path_info.isfolder:
            # Need to add logic for reading multiple files/fodler. TODO
            raise Exception(
                "Thermocalc widget got folder as a result from it's prev action. Expected only one tabular file"
            )

        # request thermo calc apis
        results_file_path = (
            new_dataset_dir + f"/thermocalc_results_{uuid4().hex}.csv"
        )
        module_service = ModuleService(db_sync_client=action_handler.db_client)
        module = module_service.get_module_record_by_id(widget.config.module_id)


        trigger_and_poll_thermocalc_service(
            widget, run_record, action_id, dataset_path_info.path, results_file_path, module.module_location.path
        )

        # store results
        dataset_id = action_handler.datasets_handler.save_tabular_dataset_helper_sync(
            input_data=results_file_path,
            input_data_sub_type=DatasetSubType.THERMOCALC_RESULTS,
            project_id=run_record.project_id,
            site_id=run_record.site_id,
            user_id=run_record.owner_id,
            action_id=action_id,
            run_id=run_record.id,
            workflow_id=run_record.workflow_id,
            name=widget.outputs[0].name,
            description=f"Dataset by thermocalc Worker action_id {action_handler.action_id}",
            access_mode=AccessMode.INTERNAL,
        )
        # saving the action results to the collection
        action_result_ids = action_handler.create_action_result_records(
            action_results=[
                ActionResult(
                    type=ActionResultType.DATASET,
                    result=DatasetActionResult(dataset_id=dataset_id),
                )
            ],
            outputs=widget.outputs,
        )

        # updating the custom_run_state of the thermocalc action only if it is in cycle
        if action_record.is_cycle:
            # fetch custom run state for widget:
            custom_run_state = action_handler.get_custom_run_state()
            logger.info(f"custom run state of thermocalc {custom_run_state}")

            # update the custom run-state with intermediate results
            custom_run_state.total_invoke_count += 1
            custom_run_state.cycle_intermediate_results.append(
                CycleIntermediateResults(
                    invocation_num=custom_run_state.total_invoke_count,
                    result_record_ids=action_result_ids,
                )
            )
            action_handler.update_action_custom_run_state(
                custom_run_state=custom_run_state
            )  # update the action run state
            logger.info("Updated action custom state of thermocalc widget.")

        # save the results (attaching result record id to the action record)
        action_handler.action_success_handler(
            action_result_id=action_result_ids, append_results=False
        )
        logger.info("completed thermocalc widget execution, saved action_results")

def trigger_and_poll_thermocalc_service(
    widget, run_record, action_id, dataset_path, results_file_path, module_file_path
):
    if not module_file_path.endswith(".py"):
        raise ValueError(f"Currently only .py suffix modules are only acceptable")
    parent_job_id = create_job(run_record.id, action_id,module_file_path)
    batches_count = get_batches_count(
        dataset_path, thermocalc_environment.thermocalc_batch_limit
    )
    register_payload = ThermoCalcJobRegisterationRequest(expected_tasks=batches_count,
                                                         input_features=widget.config.input_features,
                                                         output_features=widget.config.output_features,
                                                         connector_id=widget.config.thermocalc_connector_id)
    register_job(parent_job_id, register_payload)
    logger.info(
        f"total batches for action_id {action_id} and parent_id {parent_job_id} is {batches_count}"
    )


    connector_service = ConnectorService(db_sync_client=get_db_sync(), db_async_client=get_db_async())
    connection: Connector = connector_service.get_connector_by_id(connector_id=widget.config.thermocalc_connector_id)
    # trigger each subactions
    for start_index, end_index, batch in batches_data_generator(
        dataset_path, thermocalc_environment.thermocalc_batch_limit
    ):
        
        receive_task(parent_job_id, batch, start_index, connection)
        logger.info(
            f"triggered task for parent_job_id {parent_job_id} with {start_index} to {end_index}"
        )
    # polling
    tc_job = get_status(parent_job_id)
    for i in range(thermocalc_environment.max_polling_count_for_tc_status):
        if tc_job.status == ThermoCalcJobStatus.COMPLETED:
            if tc_job.results_file_path:
                break
            logger.info(f"Thermocalc job completed but results not yet aggregated {tc_job.id}")
        elif tc_job.status != ThermoCalcJobStatus.IN_PROGRESS:
            raise ValueError(
                f"Thermocalc JobStatus while poling should not be {tc_job.status}, {tc_job.id}"
            )
        time.sleep(thermocalc_environment.seconds_to_sleep_for_tc_status)
        tc_job = get_status(parent_job_id)
    if tc_job.status != ThermoCalcJobStatus.COMPLETED:
        raise ValueError(
            f"waited max time, still tasks completed ack not received for {parent_job_id}"
        )
    get_results_file(parent_job_id, results_file_path)
