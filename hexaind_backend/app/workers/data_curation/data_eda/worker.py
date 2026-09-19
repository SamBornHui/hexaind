import logging
import pickle
import traceback
import zlib
from pathlib import Path
from typing import List

from app.config.env_vars import environment
from app.config.redis_config import get_sync_redis_client
from app.core.celery.celery_worker import create_celery_app
from app.core.celery.global_config import API_JOBS_QUEUE
from app.core.services.action.schemas import ActionRunStatus
from app.core.services.action_handler.handler import ActionHandler
from app.services.data.assets.datasets.schemas import (
    ColumnStatistics,
    Dataset,
    DatasetMetadata,
)
from app.services.data.assets.datasets.service import DatasetsService
from app.services.data.correlation.service import CorrelationService
from app.services.data.curation.data.source.model import DataSourceModel
from app.services.data.curation.eda.visualizations.model import DataVisualization
from app.services.workflows.designer.base_schemas import WidgetType
from app.services.workflows.designer.schemas import (
    ApiCorrelationConfig,
    ApiVisualizationConfig,
    UniqueValuesConfig,
)

logger = logging.getLogger(__package__)

app = create_celery_app("eda_generator", default_queue=API_JOBS_QUEUE)


def compute_preview_stats_helper(dataset: Dataset, dataset_service: DatasetsService):
    logger.info(f"(Step 1/13) Fetched Dataset record with name: {dataset.name}")

    input_data = dataset.dataset_location[0].path  # Assuming dataset has single path
    logger.info(f"(Step 2/13) Input data: {input_data}")

    result = DatasetsService.get_column_statistics_from_tabular_data(
        file_path=input_data,
        preview=True,
        calculate_categorical_stats=True,
        calculate_numerical_stats=True,
        column_data_types=True,
    )

    statistics = result["column_statistics"]
    preview_data = result["preview"]
    total_rows = result["total_rows"]
    total_columns = result["col_count"]
    numerical_col_count = result["numerical_col_count"]
    categorical_col_count = result["categorical_col_count"]

    logger.info(
        f"(Step 3/13) Fetched Total rows: {total_rows}, Total columns: {total_columns}, Numerical columns: {numerical_col_count}, Categorical columns: {categorical_col_count}"
    )
    logger.info(f"(Step 4/13) Fetched Statistics")
    logger.info(f"(Step 5/13) Fetched Preview Data")

    db_format_statistics: List[ColumnStatistics] = (
        DatasetsService.convert_statistics_from_client_supported_format_to_db_record_format(
            statistics=statistics
        )
    )
    logger.info(f"(Step 6/13) Converted Statistics to DB format")

    # write stats to the file
    numeric_stats_file, categorical_stats_file = (
        DatasetsService.write_statistics_to_file(
            statistics=db_format_statistics,
            result_file_location=str(Path(dataset.dataset_location[0].path).parent),
            result_file_prefix=str(dataset.id),
            num_stats=True,
            cat_stats=True,
        )
    )

    logger.info(
        f"(Step 7/13) Wrote Statistics to file: {numeric_stats_file}, {categorical_stats_file}"
    )

    # write Preview to the file
    preview_file_path = DatasetsService.write_preview_to_file(
        preview_data=preview_data,
        result_file_location=str(Path(dataset.dataset_location[0].path).parent),
        result_file_prefix=str(dataset.id),
    )
    logger.info(f"(Step 8/13) Wrote Preview to file: {preview_file_path}")

    # update dataset record
    _ = dataset_service.update_datset_statistics_preview_total_count_sync(
        dataset_id=str(dataset.id),
        numerical_stats_file=numeric_stats_file,
        categorical_stats_file=categorical_stats_file,
        preview_file_path=preview_file_path,
        total_row_count=total_rows,
        total_col_count=total_columns,
        total_numeric_col_count=numerical_col_count,
        total_categorical_count=categorical_col_count,
    )
    logger.info(
        f"(Step 9/13) Updated Statistics, Preview, and Total Row/Column Count in dataset record with name: {dataset.name}"
    )

    col_type_data = result["column_data_types"]

    metadata = dataset.metadata

    # write column metadata to the file
    columns_metadata_file = DatasetsService.write_column_metadata_to_file(column_metadata=col_type_data, result_file_location=str(Path(input_data).parent), metadata=metadata)
    if metadata is None:
        metadata = DatasetMetadata(data_source=None, columns_metadata=None, columns_metadata_file=columns_metadata_file)
    else:
        metadata.columns_metadata = None
        metadata.columns_metadata_file = columns_metadata_file
        
    dataset_service.update_dataset_record_data_sync(
        dataset_id=str(dataset.id),
        key_to_update="metadata",
        data=metadata.model_dump(mode="json"),
    )
    logger.info(
        f"(Step 10/13) Updated Metadata in dataset record with name: {dataset.name}"
    )


@app.task(name="task_eda_generate_update")
def task_eda_generate_update(action_id: str, api_job_id: str):
    action_handler = ActionHandler(action_id)
    action = action_handler.get_action_record()

    if not action.action_config.type == WidgetType.API_JOBS:
        raise Exception(
            f"Invalid action submitted, {action.action_config.type} not supported by {WidgetType.API_JOBS} worker"
        )

    action_handler.update_run_status(status=ActionRunStatus.RUNNING)
    try:

        logger.info(f"{'*'*30} Preview Stats Generation Started {'*'*30}")
        dataset_service = DatasetsService(db_sync_client=action_handler.db_client)
        dataset: Dataset = dataset_service.get_dataset_by_id_sync(
            dataset_id=action.action_config.config.config.dataset_id
        )

        # Compute preview stats (step 1-11)
        compute_preview_stats_helper(dataset=dataset, dataset_service=dataset_service)

        dataset_service.update_dataset_record_data_sync(
            dataset_id=str(dataset.id),
            key_to_update="api_job_id",
            data=api_job_id,
        )
        logger.info(
            f"(Step 12/13) Updated Preview Stats ID in dataset record with eda_id: {api_job_id} and dataset id: {dataset.id}"
        )

        action_handler.action_success_handler(action_result_id="")
        logger.info(
            f"(Step 13/13) Updated Action Result in action record with id: {action_id}"
        )
    except Exception as e:
        action_handler.action_failure_handler(
            action_id=action_id,
            exception_msg=str(e),
            traceback_msg=traceback.format_exc(),
        )
        logger.exception(
            f"(Step ERROR) Updated Action Result in action record with id: {action_id}"
        )

    logger.info(f"{'*'*30} Preview Stats Generation Finished {'*'*30}")


@app.task(name="task_eda_generate_visualization")
def task_eda_generate_visualization(action_id: str):
    """
    Celery task to generate and save data visualizations based on the given action.

    Args:
        action_id (str): The unique identifier for the action to be processed.
    """
    action_handler = ActionHandler(action_id)
    action = action_handler.get_action_record()

    if not action.action_config.type == WidgetType.API_JOBS:
        raise Exception(
            f"Invalid action submitted, {action.action_config.type} not supported by {WidgetType.API_JOBS} worker"
        )

    action_handler.update_run_status(status=ActionRunStatus.RUNNING)
    try:
        logger.info(f"{'*'*30} Visualization Generation Started {'*'*30}")

        # Extract visualization configuration from the action
        visualization_config: ApiVisualizationConfig = (
            action.action_config.config.config
        )
        dataset_id = visualization_config.dataset_id
        visualization = visualization_config.visualization
        interactive = visualization.root.interactive
        visualization_hash = visualization_config.visualization_hash

        # Initialize dataset service and retrieve dataset
        dataset_service = DatasetsService(db_sync_client=action_handler.db_client)
        dataset: Dataset = dataset_service.get_dataset_by_id_sync(dataset_id=dataset_id)
        logger.info(f"Retrieved dataset with ID: {dataset_id}")

        # Determine output path for the visualization
        output_dir: Path = (
            environment.datasets_cache_folder
            / dataset.id
            / "plots"
            / visualization_hash
        )
        output_dir.parent.mkdir(exist_ok=True, parents=True)
        if interactive:
            output_path = output_dir.with_suffix(".html")
            logger.info("Visualization will be saved as an interactive HTML plot.")
        else:
            output_path = output_dir.with_suffix(".jpeg")
            logger.info("Visualization will be saved as a static JPEG image.")

        # Generate the visualization
        dataframe = DataSourceModel.from_dataset(dataset).dataframe
        figure = visualization.figure(dataframe=dataframe)
        figure.update_coloraxes(colorbar_title_side="right")
        DataVisualization.write(
            figure=figure, interactive=interactive, plot_path=output_path
        )
        logger.info(f"Visualization created and saved to {output_path}")

        # Update dataset with the visualization path
        dataset.visualization_paths.update({visualization_hash: str(output_path)})
        dataset_service.update_dataset_record_data_sync(
            dataset_id=dataset_id,
            key_to_update="visualization_paths",
            data=dataset.visualization_paths,
        )
        logger.info(
            f"Dataset with ID {dataset_id} updated with new visualization path."
        )

        # Mark the action as successful
        action_handler.action_success_handler(action_result_id="")
        logger.info(f"{'*'*30} Visualization Generation Finished {'*'*30}")

    except Exception as e:
        error_msg = (
            f"Error generating visualization for action ID {action_id}: {str(e)}"
        )
        logger.exception(error_msg)
        action_handler.action_failure_handler(
            action_id=action_id,
            exception_msg=error_msg,
            traceback_msg=traceback.format_exc(),
        )


@app.task(name="task_eda_generate_correlation")
def task_eda_generate_correlation(action_id: str):
    """
    Celery task to generate and save correlation data for a dataset based on the given action.

    Args:
        action_id (str): The unique identifier for the action to be processed.
    """
    action_handler = ActionHandler(action_id)
    action = action_handler.get_action_record()

    if not action.action_config.type == WidgetType.API_JOBS:
        raise Exception(
            f"Invalid action submitted, {action.action_config.type} not supported by {WidgetType.API_JOBS} worker"
        )

    action_handler.update_run_status(status=ActionRunStatus.RUNNING)
    try:
        logger.info(f"{'*'*30} Correlation Generation Started {'*'*30}")

        # Extract correlation configuration from the action
        correlation_config: ApiCorrelationConfig = action.action_config.config.config
        dataset_id = correlation_config.dataset_id
        correlation_schema = correlation_config.correlation_schema
        correlation_hash = correlation_config.correlation_hash

        # Initialize dataset service and retrieve dataset
        dataset_service = DatasetsService(db_sync_client=action_handler.db_client)
        dataset: Dataset = dataset_service.get_dataset_by_id_sync(dataset_id=dataset_id)
        logger.info(f"Retrieved dataset with ID: {dataset_id}")

        # Determine output path for the correlation data
        output_dir: Path = (
            environment.datasets_cache_folder
            / dataset.id
            / "correlation"
            / correlation_hash
        )
        output_dir.parent.mkdir(exist_ok=True, parents=True)
        output_path = output_dir.with_suffix(".html")

        # Generate correlation data
        correlation = CorrelationService.correlation(
            corr_schema=correlation_schema, dataset=dataset
        )
        logger.info("Correlation data generated successfully.")

        # Generate the heatmap plot
        CorrelationService.generate_heatmap_plot(
            correlation.corr_heatmap, str(output_path)
        )

        # Update dataset with the correlation path
        dataset.correlation_paths.update({correlation_hash: str(output_path)})
        dataset_service.update_dataset_record_data_sync(
            dataset_id=dataset_id,
            key_to_update="correlation_paths",
            data=dataset.correlation_paths,
        )
        logger.info(f"Dataset with ID {dataset_id} updated with new correlation path.")

        # Mark the action as successful
        action_handler.action_success_handler(action_result_id="")
        logger.info(f"{'*'*30} Correlation Generation Finished {'*'*30}")

    except Exception as e:
        error_msg = f"Error generating correlation for action ID {action_id}: {str(e)}"
        logger.exception(error_msg)
        action_handler.action_failure_handler(
            action_id=action_id,
            exception_msg=error_msg,
            traceback_msg=traceback.format_exc(),
        )


@app.task(name="task_eda_generate_unique_values")
def task_eda_generate_unique_values(action_id: str):
    """
    Celery task to generate unique values for a specified column in a dataset.

    Parameters:
    action_id (str): The ID of the action triggering this task.
    dataset_location (str): The location of the dataset file.
    column_name (str): The name of the column to extract unique values from.

    Returns:
    dict: A dictionary containing the action_id and the unique values.

    Raises:
    ValueError: If the file format is unsupported or the column is not categorical.
    Exception: If there is an error reading the file or processing the data.
    """
    action_handler = ActionHandler(action_id)
    action = action_handler.get_action_record()

    if not action.action_config.type == WidgetType.API_JOBS:
        raise Exception(
            f"Invalid action submitted, {action.action_config.type} not supported by {WidgetType.API_JOBS} worker"
        )

    action_handler.update_run_status(status=ActionRunStatus.RUNNING)
    try:
        logger.info(f"{'*'*30} Unique Values Generation Started {'*'*30}")
    
        # Extract unique values configuration from the action
        unique_values_config: UniqueValuesConfig = action.action_config.config.config
        dataset_id = unique_values_config.dataset_id
        column_name = unique_values_config.column_name

        # Initialize dataset service and retrieve dataset
        dataset_service = DatasetsService(db_sync_client=action_handler.db_client)
        dataset: Dataset = dataset_service.get_dataset_by_id_sync(dataset_id=dataset_id)
        logger.info(f"Retrieved dataset with ID: {dataset_id}")

        # Generate unique values for the column
        unique_values = DatasetsService.get_unique_values_in_column(
            dataset=dataset, column_name=column_name
        )
        logger.info(f"Unique values for column {column_name} generated successfully.")

        ### START: Store the unique values in Redis
        redis_sync_client = get_sync_redis_client()
        redis_key = f"{dataset_id}:{column_name}"
        redis_sync_client.delete(redis_key) # Delete the key if it already exists
        
        # 1. Serialize the NumPy array using Pickle (pickling the data to preserve the sorting order)
        pickled_data = pickle.dumps(unique_values)
        
        # 2. Compress the serialized data using zlib (zlib compression ratio is 1:2, reduces the size by half)
        compressed_data = zlib.compress(pickled_data)
        
        # 3. Store the compressed data in Redis
        redis_sync_client.set(redis_key, compressed_data)
        ### END: Store the unique values in Redis

        logger.info(f"Unique values for column {column_name} stored in Redis.")

        # Mark the action as successful
        action_handler.action_success_handler(action_result_id="")
        logger.info(f"{'*'*30} Unique Values Generation Finished {'*'*30}")

    except Exception as e:
        error_msg = (
            f"Error generating unique values for action ID {action_id}: {str(e)}"
        )
        logger.exception(error_msg)
        action_handler.action_failure_handler(
            action_id=action_id,
            exception_msg=error_msg,
            traceback_msg=traceback.format_exc(),
        )