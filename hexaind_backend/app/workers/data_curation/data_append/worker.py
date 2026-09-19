from app.workers.celery_worker import *
from app.core.services.action_handler.handler import *
from app.services.workflows.designer.schemas import *
from app.workers.celery_config import *
from app.workers.utils import common_widget_manager
import asyncio
import logging

from app.core.db.db_utils import get_db_sync
from app.core.services.data_transformation.tabular.schemas import AppendModel
from app.core.services.data_transformation.tabular.service import DataTransformAppendService
from app.services.workflows.designer.schemas import  AppendConfig
from app.core.celery.celery_worker import create_celery_app
from app.services.data.assets.datasets.schemas import Dataset, DatasetType, DatasetMetadata, DatasetSourceFormats

# Initialize the Celery app
app = create_celery_app('append_worker')
logger = logging.getLogger(__package__)

@app.task(name="task_append")
def task_task_append(action_id: str):
    logger.info("Inside task_append.")
    with common_widget_manager(app, action_id) as (
        action_handler,
        run_record,
        widget,
        new_dataset_dir
    ):
        if widget.type != WidgetType.APPEND:
            raise Exception("Invalid action submited to DataTransform worker")
        
        handle_data_append(widget, action_handler, WidgetType.APPEND, new_dataset_dir)


def handle_data_append(widget: Widget, action_handler: ActionHandler, widget_type: WidgetType, dest_file_path ):
    db_client = get_db_sync()
    data_trn_service =  DataTransformAppendService ()
    dataset_service  =  DatasetsService(db_sync_client=db_client)
    logger.info("received the append service and dataset service")


    inputs: List[WidgetResultResponse] = list(action_handler.get_widget_inputs_from_prev_actions(widget.inputs).values())
    if not inputs or len(inputs) < 2:
        error_str = f"DataTransform {widget_type} didn't get enough input results from previous widget. There should be atleast 2 input results required"
        logger.exception(error_str)
        raise Exception(error_str)
    

    datasets_list = []
    for input in inputs:
        if input is None or input.result_type != ActionResultType.DATASET or input.result_value is None or input.result_value.dataset_type != DatasetType.TABULAR:
            error_str = f"DataTransform {widget_type} previous widgets results must be {ActionResultType.DATASET}. Can't perfrom the operation"
            logger.exception(error_str)
            raise Exception(error_str)
        datasets_list.append(input.result_value)

    file_path = None
    run_record = action_handler.get_run_record()

    if widget_type == WidgetType.APPEND:
        append_config: AppendConfig = widget.config
        append_model = AppendModel(datasets_list=datasets_list,
                        max_rows = append_config.max_rows,
                        ignore_index = append_config.ignore_index,
                        column_type_pref_list=append_config.column_type_pref_list,
                        convert_words_to_number=append_config.convert_words_to_number)
        
        file_path =  asyncio.run(data_trn_service.transform_append(append_model, run_record.owner_id,  widget.outputs[0].name, dest_file_path, widget.use_gpu))
        
    if file_path != None:
        metadata = DatasetMetadata(
            data_source=DatasetSourceFormats.GENERATED_IN_WORKFLOW_EXECUTION_FORMAT.format(
                WidgetType.APPEND.value.lower()))
        dataset_id = dataset_service.save_tabular_dataset_helper_sync(str(file_path), project_id=run_record.project_id,
                                                                      user_id=run_record.owner_id,
                                                                      site_id=run_record.site_id,
                                                                      name=widget.outputs[0].name,
                                                                      description=f'Dataset by {widget_type} Worker action_id {action_handler.action_id}',
                                                                      metadata=metadata)
        action_results = [ActionResult(type=ActionResultType.DATASET, result=DatasetActionResult(dataset_id=dataset_id))]
        logger.info("Created dataset and action results")
        if len(widget.outputs) == 1:
           action_result_ids = action_handler.create_action_result_records(action_results=action_results, outputs=widget.outputs)
           logger.info("Created action results.")
        #action_result_id = action_handler.action_results_dao.create_result(action_result)
           for result_id in action_result_ids:
            action_handler.action_success_handler(action_result_id=result_id)
        else:
            logger.exception(f"Widget Type {widget_type} Expecting only one output.")
            raise Exception(f"Widget Type {widget_type} Expecting only one output.")
    else:
        logger.exception(f"Widget Type {widget_type} Cannot be handled by append worker")
        raise Exception(f"Widget Type {widget_type} Cannot be handled by append worker")
