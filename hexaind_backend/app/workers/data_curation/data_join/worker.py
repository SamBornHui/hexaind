from app.workers.celery_worker import *
from app.core.services.action_handler.handler import *
from app.services.workflows.designer.schemas import *
from app.workers.celery_config import *
from app.workers.utils import common_widget_manager
import asyncio
import logging

from app.core.db.db_utils import get_db_sync
from app.core.services.data_transformation.tabular.schemas import JoinModel
from app.core.services.data_transformation.tabular.service import (
    DataTransformJoinService,
)
from app.services.workflows.designer.schemas import JoinConfig
from app.core.celery.celery_worker import create_celery_app
from app.services.data.assets.datasets.schemas import (
    Dataset,
    DatasetType,
    DatasetMetadata,
    DatasetSourceFormats,
)

# Initialize the Celery app
app = create_celery_app("join_worker")
logger = logging.getLogger(__package__)


@app.task(name="task_join")
def task_task_join(action_id: str):
    logger.info("Inside task_join.")
    with common_widget_manager(app, action_id) as (
        action_handler,
        run_record,
        widget,
        new_dataset_dir,
    ):
        if widget.type != WidgetType.JOIN:
            raise Exception("Invalid action submited to DataTransform worker")

        handle_data_join(widget, action_handler, WidgetType.JOIN, new_dataset_dir)


def handle_data_join(
    widget: Widget,
    action_handler: ActionHandler,
    widget_type: WidgetType,
    dest_file_path,
):
    db_client = get_db_sync()
    data_trn_service = DataTransformJoinService()
    dataset_service = DatasetsService(db_sync_client=db_client)
    logger.info("received the join service and dataset service")

    inputs: List[WidgetResultResponse] = list(
        action_handler.get_widget_inputs_from_prev_actions(widget.inputs).values()
    )
    if not inputs or len(inputs) < 2:
        error_str = f"DataTransform {widget_type} didn't get enough input results from previous widget. There should be 2 input results required"
        logger.exception(error_str)
        raise Exception(error_str)

    if (
        inputs[0] is None
        or inputs[1] is None
        or inputs[0].result_type != ActionResultType.DATASET
        or inputs[1].result_type != ActionResultType.DATASET
    ):
        error_str = f"DataTransform {widget_type} previous widgets results must be {ActionResultType.DATASET}. Can't perfrom the operation"
        logger.exception(error_str)
        raise Exception(error_str)

    left_dataset_record: Dataset = inputs[0].result_value
    right_dataset_record: Dataset = inputs[1].result_value

    if (
        left_dataset_record is None
        or right_dataset_record is None
        or left_dataset_record.dataset_type != DatasetType.TABULAR
        or right_dataset_record.dataset_type != DatasetType.TABULAR
    ):
        error_str = f"DataTransform {widget_type} Didn't get enough {ActionResultType.DATASET}. input results"
        logger.exception(error_str)
        raise Exception(error_str)

    file_path = None
    run_record = action_handler.get_run_record()

    if widget_type == WidgetType.JOIN:
        dataset_metadata = DatasetMetadata(
            data_source=DatasetSourceFormats.GENERATED_IN_WORKFLOW_EXECUTION_FORMAT.format(
                widget.type.value.lower()
            )
        )
        join_config: JoinConfig = widget.config

        # Make it compatible with old widgets which have single column
        if (
            len(join_config.left_columns) == 0
            and len(join_config.right_columns) == 0
            and len(join_config.left_column) > 0
            and len(join_config.right_column) > 0
        ):
            join_config.left_columns.append(join_config.left_column)
            join_config.right_columns.append(join_config.right_column)

        join_model = JoinModel(
            left_dataset=left_dataset_record,
            right_dataset=right_dataset_record,
            left_columns=join_config.left_columns,
            right_columns=join_config.right_columns,
            join_type=join_config.join_type,
        )

        file_path = asyncio.run(
            data_trn_service.transform_join(
                widget.outputs[0].name, join_model, run_record.owner_id, dest_file_path, widget.use_gpu, output_format="parquet"
            )
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
        error_str = f"Widget Type {widget_type} Cannot be handled by join worker"
        logger.exception(error_str)
        raise Exception(error_str)
