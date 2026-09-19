import uuid
from app.workers.celery_worker import *
from app.core.services.action_handler.handler import *
from app.services.workflows.designer.schemas import *
from app.workers.celery_config import *
from app.workers.utils import common_widget_manager
import asyncio
import logging

from app.core.db.db_utils import get_db_sync
from app.services.data.curation.data_transformation.rename_columns.service import (
    RenameService,
)
from app.services.workflows.designer.schemas import (
    RenameActivityConfig,
    RenameConfig,
)
from app.core.celery.celery_worker import create_celery_app
from app.services.data.assets.datasets.schemas import (
    Dataset,
    DatasetMetadata,
    DatasetSourceFormats,
    DatasetType,
)


# Initialize the Celery app
app = create_celery_app("rename_worker")
logger = logging.getLogger(__package__)


# Testing
@app.task(name="task_rename_columns")
def task_rename_columns(action_id: str):
    logger.info("Inside rename_columns.")
    with common_widget_manager(app, action_id) as (
        action_handler,
        run_record,
        widget,
        new_dataset_dir,
    ):
        if widget.type != WidgetType.RENAME_COLUMNS:
            raise Exception("Invalid action submited to DataTransform worker")

        handle_rename_columns(
            widget,
            action_handler,
            WidgetType.RENAME_COLUMNS,
            new_dataset_dir,
        )


def handle_rename_columns(
    widget: Widget,
    action_handler: ActionHandler,
    widget_type: WidgetType,
    dest_file_path,
):
    db_client = get_db_sync()  # Mongo client
    data_trn_service = RenameService()  # logic
    dataset_service = DatasetsService(db_sync_client=db_client)  #
    logger.info("received the drop columns service and dataset service")

    inputs: List[WidgetResultResponse] = list(
        action_handler.get_widget_inputs_from_prev_actions(widget.inputs).values()
    )

    if inputs[0] is None or inputs[0].result_type != ActionResultType.DATASET:
        error_str = f"DataTransform {widget_type} previous widgets results must be {ActionResultType.DATASET}. Can't perfrom the operation"
        logger.exception(error_str)
        raise Exception(error_str)

    dataset_record: Dataset = inputs[0].result_value

    if dataset_record is None or dataset_record.dataset_type != DatasetType.TABULAR:
        error_str = f"DataTransform {widget_type} Didn't get enough {ActionResultType.DATASET}. input results"
        logger.exception(error_str)
        raise Exception(error_str)

    file_path = None
    run_record = action_handler.get_run_record()

    if widget_type == WidgetType.RENAME_COLUMNS:
        dataset_metadata = DatasetMetadata(
            data_source=DatasetSourceFormats.GENERATED_IN_WORKFLOW_EXECUTION_FORMAT.format(
                widget.type.value.lower()
            )
        )
        rename_columns_config: RenameConfig = widget.config.config

        file_ext = dataset_record.dataset_location[0].extension
        unique_file = f"RENAME_{widget.outputs[0].name}_{uuid.uuid4()}{file_ext}"  # file name to store the result
        output_file_path = str(Path(dest_file_path, unique_file))

        file_path = data_trn_service.rename_columns_handler(
            rename_columns_config=rename_columns_config,
            dataset=dataset_record,
            dest_path=str(output_file_path),
        )

    if file_path != None:
        dataset_id = dataset_service.save_tabular_dataset_helper_sync(
            str(file_path),
            project_id=run_record.project_id,
            user_id=run_record.owner_id,
            site_id=run_record.site_id,
            name=widget.outputs[0].name,
            description=f"Dataset by {widget_type} Worker action_id {action_handler.action_id}",
            metadata=dataset_metadata,
        )
        action_results = [
            ActionResult(
                type=ActionResultType.DATASET,
                result=DatasetActionResult(dataset_id=dataset_id),
            )
        ]
        logger.info("Created dataset and action results")
        if len(widget.outputs) == 1:
            action_result_ids = action_handler.create_action_result_records(
                action_results=action_results, outputs=widget.outputs
            )
            logger.info("Created action results.")
            for result_id in action_result_ids:
                action_handler.action_success_handler(action_result_id=result_id)
        else:
            error_str = f"Widget Type {widget_type} Expecting only one output."
            logger.exception(error_str)
            raise Exception(error_str)
    else:
        error_str = (
            f"Widget Type {widget_type} Cannot be handled by drop_columns worker"
        )
        logger.exception(error_str)
        raise Exception(error_str)
