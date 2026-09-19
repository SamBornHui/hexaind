import csv
import json
import logging
import pandas as pd
from typing import List, Union
from pathlib import Path

from app.core.celery.celery_worker import create_celery_app
from app.core.services.action_handler.handler import (
    DatasetActionResult,
    WidgetResultResponse,
)
from app.core.services.save_datasets.service import SaveService
from app.services.admin.authentication.dao import AuthenticationDao
from app.services.data.assets.datasets.dao import DatasetsDao
from app.services.data.assets.datasets.schemas import (
    DatasetMetadata,
    DatasetSourceFormats,
    AccessMode,
)
from app.services.workflows.designer.schemas import (
    ActionResult,
    ActionResultType,
    DatasetConfiguration,
    SaveWidgetConfig,
    WidgetType,
    Workflow,
    FileFormatOptions,
)
from app.services.workflows.designer.service import WorkflowDesignerService
from app.services.workflows.sessions.service import WorkflowSessionService
from app.workers.utils import common_widget_manager
from app.config.env_vars import environment

app = create_celery_app("save_action_worker")

logger = logging.getLogger(__package__)


def load_dataframe(value: Union[dict, list]) -> pd.DataFrame:
    """
    Convert a given value into a pandas DataFrame.

    Args:
    value (Union[dict, list]): The input data to be converted into a DataFrame.
                               It can be a list of dictionaries, an empty list, or any other type.

    Returns:
    pd.DataFrame: A DataFrame representation of the input value.
                  - If the input is a list of dictionaries, it converts it to a DataFrame.
                  - If the input is an empty list, it returns an empty DataFrame.
                  - For other types, it creates a DataFrame with a single column named 'Value'.
    """
    if isinstance(value, list) and value and isinstance(value[0], dict):
        # Convert list of dicts to DataFrame and write to Excel
        df = pd.DataFrame(value)
    elif isinstance(value, list) and not value:
        # Handle empty DataFrame
        df = pd.DataFrame()
    else:
        # Handle other types by creating a simple DataFrame
        df = pd.DataFrame({"Value": [value]})

    return df


def from_json_to_excel(json_file_path: Path, excel_file_path: Path):
    """
    Load data from a JSON file and save it as an Excel file with each key as a sheet name.

    Args:
        json_file_path (Path): Path to the JSON file.
        excel_file_path (Path): Path to save the Excel file.

    """
    with open(json_file_path, "r") as file:
        data = json.load(file)

    with pd.ExcelWriter(excel_file_path) as writer:
        for key, value in data.items():
            load_dataframe(value).to_excel(writer, sheet_name=key, index=False)

    logger.info(f"Data successfully saved to Excel file: {excel_file_path}")


def from_json_to_dataframe(json_file_path: Path) -> pd.DataFrame:
    """
    Convert a JSON file to a pandas DataFrame.

    Args:
        json_file_path (Path): The path to the JSON file.

    Returns:
        pd.DataFrame: The resulting DataFrame.

    Notes:
        The function attempts to load the DataFrame from the JSON content.
        If an error occurs during loading, it will silently pass and try the next item.
    """

    with open(json_file_path, "r") as file:
        data = json.load(file)

    for _, value in data.items():
        try:
            return load_dataframe(value)
        except:
            pass

    logger.info(f"Data successfully loaded to dataframe: ")


@app.task(name="task_save")
def task_save(action_id: str):
    logger.info("Inside task_save")

    with common_widget_manager(app, action_id) as (
        action_handler,
        run_record,
        widget,
        new_dataset_dir,
    ):
        if widget.type != WidgetType.SAVE:
            logger.exception("Invalid action submitted to SAVE worker")
            raise Exception("Invalid action submitted to SAVE worker")

        inputs: List[WidgetResultResponse] = list(
            action_handler.get_widget_inputs_from_prev_actions(widget.inputs).values()
        )
        save_configs: SaveWidgetConfig = widget.config
        dataset_config_mapping = {
            dataset_config.dataset_name: dataset_config
            for dataset_config in reversed(save_configs.datasetConfig)
        }
        for output in inputs:
            output_name = output.output_name
            if output.result_type == ActionResultType.DICTIONARY:
                if (
                    dataset_config_mapping[output_name].destination_config.file_Format
                    == FileFormatOptions.EXCEL
                ):
                    file_path = Path(new_dataset_dir) / f"{output_name}.xlsx"
                    from_json_to_excel(
                        Path(output.result_value.dict_file_path), file_path
                    )
                elif (
                    dataset_config_mapping[output_name].destination_config.file_Format
                    == FileFormatOptions.CSV
                ):
                    file_path = Path(new_dataset_dir) / f"{output_name}.csv"
                    from_json_to_dataframe(
                        Path(output.result_value.dict_file_path)
                    ).to_csv(file_path, index=False)

                elif (
                    dataset_config_mapping[output_name].destination_config.file_Format
                    == FileFormatOptions.PARQUET
                ):
                    file_path = Path(new_dataset_dir) / f"{output_name}.parquet"
                    from_json_to_dataframe(
                        Path(output.result_value.dict_file_path)
                    ).to_parquet(file_path, index=False)

                logger.info("file_path------", file_path)
                output_id = (
                    action_handler.datasets_handler.save_tabular_dataset_helper_sync(
                        input_data=str(file_path),
                        project_id=run_record.project_id,
                        site_id=run_record.site_id,
                        user_id=run_record.owner_id,
                        action_id=action_id,
                        run_id=run_record.id,
                        workflow_id=run_record.workflow_id,
                        name=widget.name,
                        description=widget.description,
                        access_mode=AccessMode.INTERNAL,
                        metadata=None,
                    )
                )
            else:
                output_id = output.result_value.id

            if (
                output.result_type != ActionResultType.DATASET
                and output.result_type != ActionResultType.DICTIONARY
            ):
                continue
            dataset_config: DatasetConfiguration = dataset_config_mapping[output_name]
            if dataset_config.doNotSaveFlag:
                continue
            save_service = SaveService(
                user_id=run_record.owner_id,
                project_id=run_record.project_id,
                old_dataset_id=output_id,
                site_id=run_record.site_id,
                action_id=action_handler.action_id,
                workflow_id=run_record.workflow_id,
                run_id=run_record.id,
                new_dataset_dir=new_dataset_dir,
                dataset_dao=DatasetsDao(db_sync_client=action_handler.db_client),
            )
            try:
                metadata = DatasetMetadata(
                    data_source=DatasetSourceFormats.GENERATED_IN_WORKFLOW_EXECUTION_FORMAT.format(
                        widget.type.value.lower()
                    )
                )
                new_dataset_id = save_service.save_dataset(dataset_config, metadata)
                action_result_id = action_handler.create_action_result_record(
                    ActionResult(
                        type=ActionResultType.DATASET,
                        result=DatasetActionResult(dataset_id=new_dataset_id),
                    )
                )
                action_handler.action_success_handler(action_result_id=action_result_id)
                logger.info("Updated action status")
            except Exception as e:
                logger.exception("unable to save dataset")
                raise Exception("unable to save dataset") from e

        # TODO Extend for other types of result type saves (Ex: model building pickle file, etc.)

        # elif prev_action_results[0].result_type == ActionResultType.MODEL:
        #     pass
