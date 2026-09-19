import uuid
import dask.dataframe as dd
from app.workers.celery_worker import *
from app.core.services.action_handler.handler import *
from app.services.workflows.designer.schemas import *
from app.services.data.assets.datasets.schemas import (
    Dataset,
    AccessMode,
    DatasetLocation,
    DatasetMetadata,
    DatasetSourceFormats,
)
from app.services.data.curation.service import filter_data_by_column_handler
from app.core.celery.celery_worker import create_celery_app
from app.workers.utils import common_widget_manager
from app.config.env_vars import environment
from app.services.data.curation.data.source.model import DataSourceModel

app = create_celery_app("filter_action_worker")


@app.task(name="task_filter")
def task_filter(action_id: str):
    with common_widget_manager(app, action_id) as (
        action_handler,
        run_record,
        widget,
        new_dataset_dir,
    ):
        if widget.type != WidgetType.FILTER:
            raise Exception("Invalid action submited to FILTER worker")
        dataset_metadata = DatasetMetadata(
            data_source=DatasetSourceFormats.GENERATED_IN_WORKFLOW_EXECUTION_FORMAT.format(
                widget.type.value.lower()
            )
        )

        # Initialize an list to store all WidgetResultResponse objects
        prev_action_results: List[WidgetResultResponse] = list(
            action_handler.get_widget_inputs_from_prev_actions(widget.inputs).values()
        )

        # Check the prev action results are compatible with the filter widget
        if (
            not prev_action_results
            or prev_action_results[0].result_type != ActionResultType.DATASET
        ):
            raise Exception(
                "Filter action got non-compatible result from it's prev action"
            )

        # take the prev result
        dataset_record: Dataset = prev_action_results[0].result_value
        dataframe = DataSourceModel.from_dataset(dataset_record).dataframe
        # assuming getting only one file for now:
        if not isinstance(dataframe, dd.DataFrame) or dataframe.shape[0].compute() == 0:
            raise Exception("Filter action did not get valid dataset")

        file_ext = dataset_record.dataset_location[0].extension

        unique_file = f"FILTER_{widget.outputs[0].name}_{uuid.uuid4()}{file_ext}"  # file name to store the filter result
        file_path = str(Path(new_dataset_dir, unique_file))

        path = filter_data_by_column_handler(
            dataframe, widget.config, dest_path=file_path
        )

        # save the dataset details in mongo record
        dataset_id = action_handler.datasets_handler.save_tabular_dataset_helper_sync(
            input_data=path,
            project_id=run_record.project_id,
            site_id=run_record.site_id,
            user_id=run_record.owner_id,
            action_id=action_id,
            run_id=run_record.id,
            workflow_id=run_record.workflow_id,
            name=widget.outputs[0].name,
            description=f"Dataset by {WidgetType.FILTER} Worker action_id {action_handler.action_id}",
            access_mode=AccessMode.INTERNAL,
            metadata=dataset_metadata,
        )

        # saving the action results to the collection
        action_result_id = action_handler.create_action_result_record(
            ActionResult(
                output_name=widget.outputs[0].name,
                type=ActionResultType.DATASET,
                result=DatasetActionResult(dataset_id=dataset_id),
            )
        )

        # save the results (attaching result record id to the action record)
        action_handler.action_success_handler(action_result_id=action_result_id)
