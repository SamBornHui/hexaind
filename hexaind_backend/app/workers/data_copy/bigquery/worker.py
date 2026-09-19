import logging
import uuid
from pathlib import Path

from app.config.env_vars import environment
from app.core.celery.celery_worker import create_celery_app
from app.services.data.assets.datasets.schemas import (
    DatasetMetadata,
    DatasetSourceFormats,
)
from app.workers.utils import common_widget_manager
from app.core.schemas.action_result import (
    ActionResult,
    ActionResultType,
    DatasetActionResult,
)
from app.core.services.action.schemas import ActionRunStatus
from app.services.workflows.designer.service import WorkflowDesignerService
from app.services.admin.projects.service import ProjectService
from app.core.services.action_handler.handler import AccessMode, ActionHandler, ListOfStringsActionResult
from app.services.admin.connectors.schemas import ConnectorType
from app.services.data.assets.datasets.service import DatasetsService
from app.services.data.bigquery.service import BigQueryService
from app.services.data.snowflake.service import SnowflakeService
from app.services.workflows.designer.schemas import (
    BigQueryDatasetType,
    SourceType,
    WidgetType,
)
from app.services.data.bigquery.schemas import BigQueryDatasetQueryConfig
from app.services.data.snowflake.schemas import SnowFlakeDatasetTypes
from app.workers.data_curation.data_eda.worker import compute_preview_stats_helper


# from app.services.workflows.runner.schemas import *

logger = logging.getLogger(__package__)

app = create_celery_app("bigquery_action_worker")


def get_sql_query_from_prev_widget(action_handler: ActionHandler):

    if (
        isinstance(action_handler.action_record.depends_on, list)
        and len(action_handler.action_record.depends_on) > 0
    ):

        if len(action_handler.action_record.depends_on) > 1:
            raise Exception("Error: DATA_COPY - bigquery depends on multiple widgets.")

        # get the query from previous widget
        prev_action_results_response = (
            action_handler.get_all_inputs_from_prev_action_as_list()
        )
        for action_results in prev_action_results_response:
            for action_result in action_results:
                if action_result.result_type == ActionResultType.STRING:
                    return action_result.result_value.string_value

        raise Exception("Invalid Widget before DATA_COPY widget.")

    return None


@app.task(name="task_data_copy")
def task_data_copy(action_id: str):

    with common_widget_manager(app, action_id) as (
        action_handler,
        run_record,
        widget,
        new_dataset_dir,
    ):
        if widget.type != WidgetType.DATA_COPY:
            logger.exception("Invalid action submited to DATA_COPY worker")
            raise KeyError("Invalid action submited to DATA_COPY worker")

        bigquery_service = BigQueryService(db_sync_client=action_handler.db_client)
        snowflake_service = SnowflakeService(db_sync_client=action_handler.db_client)
        results_prefix = Path(new_dataset_dir)
        results_prefix.mkdir(parents=True, exist_ok=True)
        if widget.config.source.type == SourceType.BIGQUERY:
            logger.info("executing source type bigquery")

            bigquery_connector_obj = action_handler.get_connector(
                widget.config.source.configuration.bigquery_connector_id
            )
            if bigquery_connector_obj.type != ConnectorType.BIGQUERY:
                logger.exception("Not a BigQuery Connector")
                raise ValueError("not a BigQuery connector")

            if (
                widget.config.source.configuration.dataset_configuration.dataset_type
                == BigQueryDatasetType.QUERY
            ):
                sql_query = get_sql_query_from_prev_widget(
                    action_handler=action_handler
                )
                if sql_query:
                    widget.config.source.configuration.dataset_configuration.dataset.query = (
                        sql_query
                    )

            unique_file = f"BQ_data_{uuid.uuid4()}.csv"

            config = widget.config.source.configuration.dataset_configuration.dataset
            match config:
                case BigQueryDatasetQueryConfig():
                    # updating dynamic query params
                    dyanamic_query_params = bigquery_service.get_dyanmic_query_params(
                        run_record
                    )
                    config.query_params.update(dyanamic_query_params)
                case _:
                    pass

            path = bigquery_service.bigquery_data_copy_handler(
                bigquery_connector_obj,
                widget.config,
                dest_path=f"{str(results_prefix)}/{unique_file}",
            )
            metadata = DatasetMetadata(
                data_source=DatasetSourceFormats.GENERATED_IN_WORKFLOW_EXECUTION_FORMAT.format(
                    SourceType.BIGQUERY.value.lower()
                )
            )
            # save the dataset details in mongo record
            dataset_id = (
                action_handler.datasets_handler.save_tabular_dataset_helper_sync(
                    input_data=path,
                    project_id=run_record.project_id,
                    site_id=run_record.site_id,
                    user_id=run_record.owner_id,
                    action_id=action_id,
                    run_id=run_record.id,
                    workflow_id=run_record.workflow_id,
                    name=widget.config.sink.dataset_name,
                    description=widget.config.sink.dataset_description,
                    access_mode=AccessMode.INTERNAL,
                    metadata=metadata,
                )
            )
            logger.info("Generated dataset from BigQuery datacopy.")

            # saving the action results to the collection
            action_results = [
                ActionResult(
                    type=ActionResultType.DATASET,
                    result=DatasetActionResult(dataset_id=dataset_id),
                )
            ]
        
        ##############################################################################################################################

        elif widget.config.source.type == SourceType.SNOWFLAKE:
            logger.info("executing source type snowflake")

            snowflake_connector_obj = action_handler.get_connector(
                widget.config.source.configuration.snowflake_connector_id
            )
            if snowflake_connector_obj.type != ConnectorType.SNOWFLAKE:
                logger.exception("Not a Snowflake Connector")
                raise ValueError("not a Snowflake connector")

            if (
                widget.config.source.configuration.dataset_configuration.dataset_type
                == SnowFlakeDatasetTypes.QUERY
            ):
                sql_query = get_sql_query_from_prev_widget(
                    action_handler=action_handler
                )
                if sql_query:
                    widget.config.source.configuration.dataset_configuration.dataset.query = (
                        sql_query
                    )

            unique_file = f"SnowFlake_data_{uuid.uuid4()}.parquet"

            path = snowflake_service.snowflake_data_copy_handler(
                snowflake_connector_obj=snowflake_connector_obj,
                snowflake_config=widget.config,
                dest_path=f"{str(results_prefix)}/{unique_file}",
            )
            metadata = DatasetMetadata(
                data_source=DatasetSourceFormats.GENERATED_IN_WORKFLOW_EXECUTION_FORMAT.format(
                    SourceType.SNOWFLAKE.value.lower()
                )
            )
            # save the dataset details in mongo record
            dataset_id = (
                action_handler.datasets_handler.save_tabular_dataset_helper_sync(
                    input_data=path,
                    project_id=run_record.project_id,
                    site_id=run_record.site_id,
                    user_id=run_record.owner_id,
                    action_id=action_id,
                    run_id=run_record.id,
                    workflow_id=run_record.workflow_id,
                    name=widget.config.sink.dataset_name,
                    description=widget.config.sink.dataset_description,
                    access_mode=AccessMode.INTERNAL,
                    metadata=metadata,
                )
            )
            logger.info("Generated dataset from SnowFlake datacopy.")

            # saving the action results to the collection
            action_results = [
                ActionResult(
                    type=ActionResultType.DATASET,
                    result=DatasetActionResult(dataset_id=dataset_id),
                )
            ]

        elif widget.config.source.type == SourceType.LOCAL:

            widget_name = "CSV_File"  # TODO: Currently only csv widget is using below logic , in future change accordingly
            metadata = DatasetMetadata(
                data_source=DatasetSourceFormats.GENERATED_IN_WORKFLOW_EXECUTION_FORMAT.format(
                    widget_name
                )
            )
            # get dataset record from db
            dataset_service = DatasetsService(db_sync_client=action_handler.db_client)
            new_dataset_id = dataset_service.duplicate_dataset_record_sync(
                widget.config.source.configuration.dataset_id, metadata
            )
            
            # compute preview and statistics for the new the dataset if not already computed
            new_dataset = dataset_service.get_dataset_by_id_sync(dataset_id=new_dataset_id)
            statistics_exist = new_dataset.dataset_information[0].statistics or (
                new_dataset.dataset_information[0].numerical_statistics_file
                and new_dataset.dataset_information[0].categorical_statistics_file
                and Path(new_dataset.dataset_information[0].numerical_statistics_file).exists()
                and Path(new_dataset.dataset_information[0].categorical_statistics_file).exists()
            )
            if not statistics_exist:
                compute_preview_stats_helper(dataset=new_dataset, dataset_service=dataset_service)


            action_results = [
                ActionResult(
                    type=ActionResultType.DATASET,
                    result=DatasetActionResult(dataset_id=new_dataset_id),
                )
            ]

        elif widget.config.source.type == SourceType.MOUNTED_DRIVE:
            action_results = [
                ActionResult(
                    type=ActionResultType.DATASET,
                    result=DatasetActionResult(
                        dataset_id=widget.config.source.configuration.dataset_id
                    ),
                )
            ]

        action_result_ids = action_handler.create_action_result_records(
            action_results=action_results, outputs=widget.outputs
        )
        logger.info("widget results stored successfully")

        # save the results
        for action_result_id in action_result_ids:
            action_handler.action_success_handler(action_result_id=action_result_id)




@app.task(name="task_text_data")
def task_text_data(action_id: str):
    #this worker specifically to cater the use case of VPSC simulation
    with common_widget_manager(app, action_id) as values:

        action_handler, run_record, widget = values[:3]

        if widget.type != WidgetType.TEXT_DATA:
            logger.exception("Invalid action submitted to task_vpsc_data worker")
            raise KeyError("Invalid action submitted to task_vpsc_data worker")

        source_list = widget.config.source

        dataset_service = DatasetsService(db_sync_client=action_handler.db_client)
        all_dataset_paths = []
        for source1 in source_list:
            dataset_obj = dataset_service.get_dataset_by_id_sync(dataset_id=source1.configuration.dataset_id)
            all_dataset_paths.append(dataset_obj.dataset_location[0].path)
        
        action_result_id = action_handler.create_action_result_record(
            ActionResult(
                type=ActionResultType.STRINGS_LIST,
                result=ListOfStringsActionResult(strings_list_value = all_dataset_paths),
                output_name=widget.outputs[0].name,
            )
        )

        logger.info(f"Created the action result record with action result id {action_result_id}")

        # Save the results (attaching result record id to the action record)
        action_handler.action_success_handler(
            action_result_id=[action_result_id, action_result_id],
            append_results=False,
        )


