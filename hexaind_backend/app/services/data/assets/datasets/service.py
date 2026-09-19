import json
import logging
import os
import shutil
import time
import traceback
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
# from dask.dataframe.core import DataFrame
import dask.dataframe as dd
# from dask.dataframe.io.io import from_pandas
# from dask.dataframe.multi import concat
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import DirectoryPath
from pymongo import MongoClient

from app.config.env_vars import environment
from app.core.services.action.dao import ActionsDao
from app.core.services.action.schemas import Action
from app.services.admin.authentication.service import (
    AuthenticationService,
    User,
)
from app.services.data.assets.datasets.dao import DatasetsDao
from app.services.data.assets.datasets.schemas import (
    AccessMode,
    ApiJob,
    ApiJobType,
    ColumnStatistics,
    Dataset,
    DatasetDeleteType,
    DatasetLocation,
    DatasetMetadata,
    DatasetSource,
    DatasetSourceFormats,
    DatasetSubType,
    DatasetType,
    DeleteDatasetResponse,
    DeleteDatasetResponseStatus,
    DeleteDatasetsResponse,
    MachineLearningModel,
    TabularColumnType,
    TabularDatasetInformation,
    UploadStats,
    UploadStatus,
    WorkflowDatasetCustomInformation,
)
from app.services.data.curation.data.sink.model import DataSinkModel
from app.services.data.curation.data.source.model import DataSourceModel
from app.services.data.curation.eda.statistics.v1_0.model import (
    CategoricalStatistics,
    ColumnType,
    DataStatistics,
    NumericalStatistics,
)
from app.utils.file_utils import FileUtils

logger = logging.getLogger(__package__)


class DatasetsService:
    def __init__(
        self,
        db_sync_client: Optional[MongoClient] = None,
        db_async_client: Optional[AsyncIOMotorClient] = None,
    ) -> None:
        self.datasets_dao = DatasetsDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )
        self.action_dao = ActionsDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )
        self.authentication_service = AuthenticationService(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )

    async def get_datasets_async(
        self,
        site_id: str,
        project_id: str,
        dataset_type: str,
        search_term: Optional[str] = None,
        page_limit: Optional[int] = None,
        page_number: int = 1,
        access_mode: AccessMode = AccessMode.EXTERNAL,
        file_ext: Optional[str] = None,
    ) -> Tuple[List[Dataset], int]:
        datasets, total_count = await self.datasets_dao.get_datasets_async(
            site_id=site_id,
            project_id=project_id,
            dataset_type=dataset_type,
            search_term=search_term,
            page_limit=page_limit,
            page_number=page_number,
            access_mode=access_mode,
            file_ext=file_ext,
        )
        return (datasets, total_count)

    async def get_dataset_by_id(self, dataset_id: str) -> Dataset:
        dataset = await self.datasets_dao.get_dataset_by_id_async(dataset_id=dataset_id)
        return dataset

    def get_dataset_by_id_sync(self, dataset_id: str) -> Dataset:
        dataset = self.datasets_dao.get_dataset_by_id(dataset_id=dataset_id)
        return dataset

    def duplicate_dataset_record_sync(
        self, dataset_id: str, metadata: Optional[DatasetMetadata] = None
    ) -> str:
        dataset_record: Dataset = self.get_dataset_by_id_sync(dataset_id=dataset_id)
        dataset_locations: list[DatasetLocation] = dataset_record.dataset_location

        new_dataset_locations: list[DatasetLocation] = []
        for dataset_location in dataset_locations:
            if dataset_location.isfolder:
                pass  # TODO: add deep copy of folder
            else:
                current_file_path = dataset_location.path
                new_file_path = FileUtils.add_timestamp_to_filename(current_file_path)
                FileUtils.createDeepCopyOfFile(current_file_path, new_file_path)

                new_dataset_locations.append(
                    DatasetLocation(
                        isfolder=dataset_location.isfolder,
                        size=dataset_location.size,
                        extension=dataset_location.extension,
                        path=new_file_path,
                        last_modified_at=dataset_location.last_modified_at,
                        last_modified_by=dataset_location.last_modified_by,
                    )
                )

        dataset_record.access_mode = AccessMode.INTERNAL
        dataset_record.created_at = datetime.now(timezone.utc)
        dataset_record.dataset_location = new_dataset_locations

        return self.datasets_dao.insert_dataset_record(dataset_record)

    async def delete_datasets_async(
        self,
        dataset_ids: List[str],
        dataset_type: str,
        dataset_delete_type: DatasetDeleteType,
    ) -> DeleteDatasetsResponse:
        results = []
        for dataset_id in dataset_ids:
            try:
                if dataset_type == "TABULAR":
                    await self.datasets_dao.delete_dataset_record_async(
                        dataset_id, dataset_delete_type
                    )

                else:
                    await self.datasets_dao.delete_module_record_async(
                        dataset_id, dataset_delete_type
                    )
                results.append(
                    DeleteDatasetResponse(
                        dataset_id=dataset_id,
                        status=DeleteDatasetResponseStatus.SUCCESS,
                        message=None,
                    )
                )
            except Exception as e:
                results.append(
                    DeleteDatasetResponse(
                        dataset_id=dataset_id,
                        status=DeleteDatasetResponseStatus.FAIL,
                        message=str(e),
                    )
                )

        return DeleteDatasetsResponse(response=results)

    async def delete_dataset_by_id_async(
        self, dataset_id: str, force_delete: bool = False
    ) -> bool:
        try:
            dataset_record: Dataset = await self.datasets_dao.get_dataset_by_id_async(
                dataset_id=dataset_id
            )
        except KeyError:
            print("Dataset already got deleted")
            return True

        if not force_delete or dataset_record.access_mode == AccessMode.EXTERNAL:
            return True

        try:
            file_locations = [
                (record.path, record.isfolder)
                for record in dataset_record.dataset_location
            ]
            print(
                f"deleting dataset({dataset_id}) files {file_locations} from platform"
            )
            self.delete_files_helper(
                file_paths=file_locations
            )  # delete all file locations on disk

        except KeyError:
            return True  # TODO make logging

        except FileNotFoundError:
            pass  # TODO make logging

        # finally removing the dataset records in db
        return await self.datasets_dao.delete_dataset_by_id_async(dataset_id=dataset_id)

    def save_machine_learning_model_helper_sync(
        self,
        model_file_path: str,
        dataset: Dataset,
        user_id: str,
        project_id: str,
        site_id: str,
        access_mode: AccessMode,
        action_id: str = "",
        run_id: str = "",
        workflow_id: str = "",
        name: str = "",
        description: str = "",
        tags: List[str] = [],
    ) -> str:
        if not model_file_path and not model_file_path.lower().endswith(".pkl"):
            raise Exception(
                f"Expecting valid file path ends with .pkl. But got {model_file_path}"
            )

        machine_learning_model_file_record = MachineLearningModel(
            user_id=user_id,
            project_id=project_id,
            site_id=site_id,
            action_id=action_id,
            name=name,
            description=description,
            created_at=datetime.now(timezone.utc),
            ml_model_file_path=model_file_path,
            dataset=dataset,
            access_mode=access_mode,
            tags=tags,
        )

        return self.datasets_dao.insert_machine_learning_model_record(
            machine_learning_model_file_record
        )

    async def get_machine_learning_model_by_id_async(
        self, machine_learning_model_id: str
    ) -> MachineLearningModel:
        machine_learning_model_record: MachineLearningModel = (
            await self.datasets_dao.get_machine_learning_model_by_id_async(
                machine_learning_model_id=machine_learning_model_id
            )
        )

        return machine_learning_model_record

    async def delete_machine_learning_model_by_id_async(
        self, machine_learning_model_record_id: str
    ) -> bool:
        try:
            machine_learning_model_record: MachineLearningModel = (
                await self.get_machine_learning_model_by_id_async(
                    machine_learning_model_id=machine_learning_model_record_id
                )
            )

            ml_model_file_path = machine_learning_model_record.ml_model_file_path

            self.delete_files_helper(file_paths=[(ml_model_file_path, False)])

        except KeyError:
            return True  # TODO make logging

        except FileNotFoundError:
            pass  # TODO make logging

        # finally removing the ml-model records in db
        return await self.datasets_dao.delete_machine_learning_model_by_id_async(
            machine_learning_model_record_id=machine_learning_model_record_id
        )

    def save_mobo_recommendation_dataset_helper_sync(
        self,
        input_data,
        project_id: str,
        user_id: str,
        site_id: str,
        action_id: str = "",
        run_id: str = "",
        workflow_id: str = "",
        name: str = "",
        description: str = "",
        tags: List[str] = [],
        access_mode: AccessMode = AccessMode.INTERNAL,
        custom_information: Optional[WorkflowDatasetCustomInformation] = None,
    ):
        # Check if input_data is a JSON string (file path)
        if isinstance(input_data, str):
            if not (
                input_data.lower().endswith(".json")
                or input_data.lower().endswith(".csv")
            ):  # TODO remove .csv condition
                raise ValueError("File path must point to a JSON file.")

            if not FileUtils.is_file_exist(input_data):
                raise Exception(f"Not found the json file: {input_data}")

            file_location_info = self.get_file_info(input_data)

        elif FileUtils.is_json_serializable(
            input_data
        ):  # Check if input_data is a JSON object
            data_path = self.save_json_to_location(input_data, project_id)
            file_location_info = self.get_file_info(data_path)

        else:
            raise ValueError(
                "Input data must be either a JSON storage compatible or a JSON file path."
            )

        dataset = Dataset(
            user_id=user_id,
            project_id=project_id,
            site_id=site_id,
            action_id=action_id,
            name=name,
            description=description,
            dataset_type=DatasetType.MOBO_RECOMMENDATIONS,
            dataset_information=[],
            upload_status=UploadStatus.COMPLETED,
            upload_stats=UploadStats(percentage="100%"),
            metadata={},  # Placeholder for metadata # type: ignore
            created_at=datetime.now(timezone.utc),
            dataset_location=[file_location_info],  # Placeholder for dataset location
            access_mode=access_mode,
            tags=tags,
            custom_information=custom_information,
        )

        return self.datasets_dao.insert_dataset_record(dataset)

    async def save_json_data_helper_async(
        self,
        input_data,
        project_id: str,
        user_id: str,
        created_by: str,
        site_id: str,
        action_id: str = "",
        run_id: str = "",
        workflow_id: str = "",
        name: str = "",
        description: str = "",
        tags: List[str] = [],
        access_mode: AccessMode = AccessMode.INTERNAL,
        metadata: Optional[DatasetMetadata] = None,
    ):
        try:
            # Check if input_data is a JSON string (file path)
            if isinstance(input_data, str):
                if not input_data.lower().endswith(".json"):
                    raise ValueError("File path must point to a JSON file.")

                if not FileUtils.is_file_exist(input_data):
                    raise Exception(f"Not found the json file: {input_data}")

                file_location_info = self.get_file_info(input_data)

            elif FileUtils.is_json_serializable(
                input_data
            ):  # Check if input_data is a JSON object
                data_path = self.save_json_to_location(input_data, project_id)
                file_location_info = self.get_file_info(data_path)

            else:
                raise ValueError(
                    "Input data must be either a JSON storage compatible or a JSON file path."
                )

            dataset = Dataset(
                user_id=user_id,
                project_id=project_id,
                site_id=site_id,
                action_id=action_id,
                name=name,
                description=description,
                dataset_type=DatasetType.JSON,
                dataset_information=[],
                upload_status=UploadStatus.COMPLETED,
                upload_stats=UploadStats(percentage="100%"),
                metadata=metadata,  # Placeholder for metadata
                created_at=datetime.now(timezone.utc),
                dataset_location=[
                    file_location_info
                ],  # Placeholder for dataset location
                access_mode=access_mode,
                tags=tags,
                custom_information=None,
                created_by=created_by,
            )

            return await self.datasets_dao.insert_dataset_record_async(dataset)

        except Exception as e:
            print(str(e))
            return str(e)

    def save_json_data_helper_sync(
        self,
        input_data,
        project_id: str,
        user_id: str,
        created_by: str,
        site_id: str,
        action_id: str = "",
        run_id: str = "",
        workflow_id: str = "",
        name: str = "",
        description: str = "",
        tags: List[str] = [],
        access_mode: AccessMode = AccessMode.INTERNAL,
        metadata: Optional[DatasetMetadata] = None,
    ):
        try:
            # Check if input_data is a JSON string (file path)
            if isinstance(input_data, str):
                if not input_data.lower().endswith(".json"):
                    raise ValueError("File path must point to a JSON file.")

                if not FileUtils.is_file_exist(input_data):
                    raise Exception(f"Not found the json file: {input_data}")

                file_location_info = self.get_file_info(input_data)

            elif FileUtils.is_json_serializable(
                input_data
            ):  # Check if input_data is a JSON object
                data_path = self.save_json_to_location(input_data, project_id)
                file_location_info = self.get_file_info(data_path)

            else:
                raise ValueError(
                    "Input data must be either a JSON storage compatible or a JSON file path."
                )

            dataset = Dataset(
                user_id=user_id,
                project_id=project_id,
                site_id=site_id,
                action_id=action_id,
                name=name,
                description=description,
                dataset_type=DatasetType.JSON,
                dataset_information=[],
                upload_status=UploadStatus.COMPLETED,
                upload_stats=UploadStats(percentage="100%"),
                metadata=metadata,  # Placeholder for metadata
                created_at=datetime.now(timezone.utc),
                dataset_location=[
                    file_location_info
                ],  # Placeholder for dataset location
                access_mode=access_mode,
                tags=tags,
                custom_information=None,
                created_by=created_by,
            )

            return self.datasets_dao.insert_dataset_record(dataset)

        except Exception as e:
            print(str(e))
            return str(e)

    def upload_dataset(
        self,
        siteId: str,
        projectId: str,
        name: str,
        description: str,
        dataset_type: DatasetType,
        user: User,
        file_path: str,
        file_extension: str,
        data_source: Optional[DatasetSource] = DatasetSource.LOCAL,
        access_mode: AccessMode = AccessMode.EXTERNAL,
        tags: List[str] = [],
    ):
        if dataset_type == DatasetType.TEXT:
            metadata = DatasetMetadata(
                data_source=DatasetSourceFormats.LOCAL_FILE_UPLOAD_FORMAT.format(
                    dataset_type.TEXT.value.lower()
                )
            )
            dataset_id = self.save_path_as_text_dataset_sync(
                text_file_path=Path(file_path),
                project_id=projectId,
                site_id=siteId,
                user_id=user.id,  # type: ignore
                created_by=user.name,
                name=name,
                description=description,
                access_mode=AccessMode.EXTERNAL,
                metadata=metadata,
            )
        elif dataset_type == DatasetType.JSON:
            metadata = DatasetMetadata(
                data_source=DatasetSourceFormats.LOCAL_FILE_UPLOAD_FORMAT.format(
                    file_extension
                )
            )
            dataset_id = self.save_json_data_helper_sync(
                input_data=str(file_path),
                project_id=projectId,
                site_id=siteId,
                user_id=user.id,  # type: ignore
                created_by=user.name,
                name=name,
                description=description,
                access_mode=AccessMode.EXTERNAL,
                metadata=metadata,
            )
        else:
            if data_source == DatasetSource.LOCAL:
                metadata = DatasetMetadata(
                    data_source=DatasetSourceFormats.LOCAL_FILE_UPLOAD_FORMAT.format(
                        file_extension
                    )
                )
            elif data_source == DatasetSource.MOUNTED_DRIVE:
                metadata = DatasetMetadata(
                    data_source=DatasetSourceFormats.MOUNTED_DRIVE_FILE_UPLOAD_FORMAT.format(
                        file_extension
                    )
                )
            else:
                metadata = None
            dataset_id = self.save_tabular_dataset_helper_sync(
                input_data=file_path,
                project_id=projectId,
                site_id=siteId,
                user_id=user.id,  # type: ignore
                # created_by=user.name,
                action_id="",
                run_id="",
                workflow_id="",
                name=name,
                description=description,
                access_mode=access_mode,
                metadata=metadata,
                tags=tags,
            )

        return dataset_id

    async def save_path_as_text_dataset_async(
        self,
        text_file_path: Path,
        project_id: str,
        user_id: str,
        created_by: str,
        site_id: str,
        action_id: str = "",
        run_id: str = "",
        workflow_id: str = "",
        name: str = "",
        description: str = "",
        tags: List[str] = [],
        access_mode: AccessMode = AccessMode.INTERNAL,
        metadata: Optional[DatasetMetadata] = None,
    ):
        if not text_file_path.exists():
            raise FileNotFoundError(f"Not found the file: {text_file_path}")

        if not FileUtils.is_text_file(str(text_file_path)):
            raise ValueError(f"{text_file_path.name} is not a text file")

        file_location_info = self.get_file_info(str(text_file_path))

        dataset = Dataset(
            user_id=user_id,
            project_id=project_id,
            site_id=site_id,
            action_id=action_id,
            name=name,
            description=description,
            dataset_type=DatasetType.TEXT,
            dataset_information=[],
            upload_status=UploadStatus.COMPLETED,
            upload_stats=UploadStats(percentage="100%"),
            metadata=metadata,  # Placeholder for metadata
            created_at=datetime.now(timezone.utc),
            dataset_location=[file_location_info],  # Placeholder for dataset location
            access_mode=access_mode,
            tags=tags,
            custom_information=None,
            created_by=created_by,
        )

        return await self.datasets_dao.insert_dataset_record_async(dataset)

    def save_path_as_text_dataset_sync(
        self,
        text_file_path: Path,
        project_id: str,
        user_id: str,
        created_by: str,
        site_id: str,
        action_id: str = "",
        run_id: str = "",
        workflow_id: str = "",
        name: str = "",
        description: str = "",
        tags: List[str] = [],
        access_mode: AccessMode = AccessMode.INTERNAL,
        metadata: Optional[DatasetMetadata] = None,
    ):
        if not text_file_path.exists():
            raise FileNotFoundError(f"Not found the file: {text_file_path}")

        if not FileUtils.is_text_file(str(text_file_path)):
            raise ValueError(f"{text_file_path.name} is not a text file")

        file_location_info = self.get_file_info(str(text_file_path))

        dataset = Dataset(
            user_id=user_id,
            project_id=project_id,
            site_id=site_id,
            action_id=action_id,
            name=name,
            description=description,
            dataset_type=DatasetType.TEXT,
            dataset_information=[],
            upload_status=UploadStatus.COMPLETED,
            upload_stats=UploadStats(percentage="100%"),
            metadata=metadata,  # Placeholder for metadata
            created_at=datetime.now(timezone.utc),
            dataset_location=[file_location_info],  # Placeholder for dataset location
            access_mode=access_mode,
            tags=tags,
            custom_information=None,
            created_by=created_by,
        )

        return self.datasets_dao.insert_dataset_record(dataset)

    @staticmethod
    def generate_file_info(input_data: str | pd.DataFrame, project_id: str):
        # writes dataframe to file
        if isinstance(input_data, pd.DataFrame):
            data_path = DatasetsService.save_dataframe_to_location(
                input_data, project_id
            )
        else:
            data_path = input_data
        file_location_info = DatasetsService.get_file_info(data_path)
        return file_location_info

    @staticmethod
    def generate_tabular_dataset_info_and_update_metadata(
        input_data_path, metadata=None
    ):
        result = DatasetsService.get_column_statistics_from_tabular_data(
            file_path=input_data_path, preview=True, column_data_types=True
        )
        column_statistics, total_rows = (
            DatasetsService.convert_statistics_from_client_supported_format_to_db_record_format(
                result["column_statistics"]
            ),
            result["total_rows"],
        )

        total_columns, numerical_col_count, categorical_col_count = (
            result["col_count"],
            result["numerical_col_count"],
            result["categorical_col_count"],
        )

        # write stats to the file
        numeric_stats_file, categorical_stats_file = (
            DatasetsService.write_statistics_to_file(
                statistics=column_statistics,
                result_file_location=str(Path(input_data_path).parent),
            )
        )

        preview, col_type_data = result["preview"], result["column_data_types"]

        # write preview to the file
        preview_file_path = DatasetsService.write_preview_to_file(
            preview_data=preview, result_file_location=str(Path(input_data_path).parent)
        )

        # write column metadata to the file
        columns_metadata_file = DatasetsService.write_column_metadata_to_file(
            column_metadata=col_type_data,
            result_file_location=str(Path(input_data_path).parent),
            metadata=metadata,
        )
        if metadata is None:
            metadata = DatasetMetadata(
                data_source=None,
                columns_metadata=None,
                columns_metadata_file=columns_metadata_file,
            )
        else:
            metadata.columns_metadata = None
            metadata.columns_metadata_file = columns_metadata_file

        tabular_dataset_info = TabularDatasetInformation(
            preview=None,
            statistics=None,
            numerical_statistics_file=numeric_stats_file,
            categorical_statistics_file=categorical_stats_file,
            preview_file=preview_file_path,
            row_count=total_rows,
            col_count=total_columns,
            numerical_col_count=numerical_col_count,
            categorical_col_count=categorical_col_count,
            dataset_schema=None,
        )

        # TODO: rename below var and segregate accordingly
        side_effect = {"excel_sheets_name": result.get("excel_sheets_name")}

        return tabular_dataset_info, metadata, side_effect

    def save_tabular_dataset_helper_sync(
        self,
        input_data,
        project_id: str,
        user_id: str,
        site_id: str,
        action_id: str = "",
        run_id: str = "",
        workflow_id: str = "",
        name: str = "",
        description: str = "",
        tags: List[str] = [],
        input_data_sub_type: Optional[DatasetSubType] = None,
        access_mode: AccessMode = AccessMode.INTERNAL,
        custom_information: Optional[WorkflowDatasetCustomInformation] = None,
        metadata: Optional[DatasetMetadata] = None,
        dataset_information: Optional[List[TabularDatasetInformation]] = None,
    ):
        file_location_info = self.generate_file_info(
            input_data=input_data, project_id=project_id
        )
        if dataset_information is None:
            tabular_dataset_info, metadata, se_results = (
                self.generate_tabular_dataset_info_and_update_metadata(
                    input_data_path=file_location_info.path, metadata=metadata
                )
            )
        else:
            # note: if dataset_info is present => in case of datacatalog a json file contains this info
            tabular_dataset_info = dataset_information[0]
            se_results = {}
            # metadata is already updated in this case

        user = self.authentication_service.get_user_sync(user_id=user_id)
        if user is None:
            raise KeyError(f"User with {user_id=} not found")

        if "scrap_analysis" and "upload" in tags:
            logger.info("SAM upload file case")
            from app.services.apps.scrap_analysis.service import SAMService

            custom_information = SAMService().save_baseline_custom_info_sync(
                user, file_location_info.path, name, tags
            )

        dataset = Dataset(
            user_id=user_id,
            project_id=project_id,
            site_id=site_id,
            action_id=action_id,
            name=name,
            description=description,
            dataset_type=DatasetType.TABULAR,
            dataset_sub_type=input_data_sub_type,
            dataset_information=[tabular_dataset_info],
            upload_status=UploadStatus.COMPLETED,
            upload_stats=UploadStats(percentage="100%"),
            metadata=metadata,  # Placeholder for metadata
            created_at=datetime.now(timezone.utc),
            created_by=user.name,
            dataset_location=[file_location_info],  # Placeholder for dataset location
            access_mode=access_mode,
            tags=tags,
            custom_information=custom_information,
            excel_sheets_name=se_results.get("excel_sheets_name", None),
        )
        return self.datasets_dao.insert_dataset_record(dataset)

    async def validate_new_dataset_properties(self, name: str, project_id: str):
        await self.datasets_dao.get_dataset_by_name(name, project_id)

    async def save_tabular_dataset_helper_async(
        self,
        input_data,
        project_id: str,
        user_id: str,
        site_id: str,
        created_by: str = "",
        action_id: str = "",
        run_id: str = "",
        workflow_id: str = "",
        name: str = "",
        description: str = "",
        tags: List[str] = [],
        access_mode: AccessMode = AccessMode.INTERNAL,
        custom_information: Optional[WorkflowDatasetCustomInformation] = None,
        metadata: Optional[DatasetMetadata] = None,
        dataset_information: Optional[List[TabularDatasetInformation]] = None,
    ):
        # Check if input_data is a DataFrame or a file path
        file_location_info = self.generate_file_info(
            input_data=input_data, project_id=project_id
        )
        if dataset_information is None:
            tabular_dataset_info, metadata, se_results = (
                self.generate_tabular_dataset_info_and_update_metadata(
                    input_data_path=file_location_info.path, metadata=metadata
                )
            )
        else:
            tabular_dataset_info = dataset_information[0]

        dataset = Dataset(
            user_id=user_id,
            project_id=project_id,
            action_id=action_id,
            site_id=site_id,
            name=name,
            description=description,
            dataset_type=DatasetType.TABULAR,
            dataset_information=[tabular_dataset_info],
            upload_status=UploadStatus.COMPLETED,
            upload_stats=UploadStats(percentage="100%"),
            metadata=metadata,  # Placeholder for metadata
            created_at=datetime.now(timezone.utc),
            created_by=created_by,
            dataset_location=[file_location_info],  # Placeholder for dataset location
            access_mode=access_mode,
            tags=tags,
            custom_information=custom_information,
        )

        return await self.datasets_dao.insert_dataset_record_async(dataset)

    # @staticmethod
    # def get_file_info(
    #     file_path: str, last_modified_by: Optional[str] = None
    # ) -> DatasetLocation:
    #     """Returns the file information needed for DatasetLocation."""

    #     isfolder = os.path.isdir(file_path)
    #     size = str(os.path.getsize(file_path)) if not isfolder else "N/A"
    #     extension = os.path.splitext(file_path)[1] if not isfolder else "N/A"
    #     last_modified_at = datetime.now(timezone.utc)

    #     return DatasetLocation(
    #         isfolder=isfolder,
    #         size=size,
    #         extension=extension,
    #         path=file_path,
    #         last_modified_by=last_modified_by,
    #         last_modified_at=last_modified_at,
    #     )

    @staticmethod
    def get_file_info(
    file_path: str, last_modified_by: Optional[str] = None
    ) -> DatasetLocation:
        """Returns the file information needed for DatasetLocation, including folder size calculation."""

        path = Path(file_path)
        isfolder = path.is_dir()

        if isfolder:
            size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
            first_file = next((f for f in path.rglob('*') if f.is_file()), None)
            extension = first_file.suffix if first_file else "N/A"
        else:
            size = path.stat().st_size
            extension = path.suffix

        last_modified_at = datetime.now(timezone.utc)

        return DatasetLocation(
            isfolder=isfolder,
            size=str(size),
            extension=extension,
            path=file_path,
            last_modified_by=last_modified_by,
            last_modified_at=last_modified_at,
        )

    def save_json_to_location(self, json_data, project_id: str) -> str:
        """
        Saves a json to a specified path with a unique UUID file name.
        :param json_data: dict/json to be saved.
        :param project_id: Project identifier used in the path.
        """
        try:
            # Construct the directory path
            dir_path = environment.datasets_folder

            # Ensure the directory exists
            os.makedirs(dir_path, exist_ok=True)

            # Generate a unique file name using UUID
            file_name = f"data_{uuid.uuid4()}.json"

            # Complete file path
            file_path = os.path.join(dir_path, file_name)

            # Save the json to the file
            with open(file_path, "w") as f:
                json.dump(json_data, f)

            return file_path

        except Exception as e:
            print(traceback.format_exc())
            raise Exception(
                "Exception occured while writing json data to disk: ", str(e)
            )

    @staticmethod
    def save_dataframe_to_location(df: pd.DataFrame, project_id: str) -> str:
        """
        Saves a DataFrame to a specified path with a unique UUID file name.
        :param df: DataFrame to be saved.
        :param project_id: Project identifier used in the path.
        """
        try:
            file_path = environment.datasets_folder / f"data_{uuid.uuid4()}.csv"
            file_path.parent.mkdir(parents=True, exist_ok=True)

            DataSinkModel.from_path(file_path).to_sink(dd.from_pandas(df, npartitions=1))

            return str(file_path)

        except Exception as e:
            print(traceback.format_exc())
            raise Exception(
                "Exception occured while writing pandas dataframe to disk: ", str(e)
            )

    @staticmethod
    def read_preview_from_file(
        preview_file: str,
        page_size: Optional[int] = None,
        page_number: Optional[int] = None,
    ) -> dict:
        # Read the JSON file
        with open(preview_file, "r") as f:
            data = json.load(f)

        # Extract the "data" key, and preserve the "index" and "columns"
        columns = data.get("columns", [])
        preview_data = data.get("data", [])

        if page_size is not None and page_number is not None:
            # Calculate start and end indices for pagination
            start_index = (page_number - 1) * page_size
            end_index = start_index + page_size
            preview_data = preview_data[start_index:end_index]

        return {"columns": columns, "data": preview_data}

    @staticmethod
    def write_preview_to_file(
        preview_data: Dict,
        result_file_location: str,
        result_file_prefix: Optional[str] = None,
    ):
        if result_file_prefix is None:
            result_file_prefix = str(uuid.uuid4())

        try:
            # Define file paths
            result_file_location_path = Path(result_file_location)
            preview_file_path = (
                result_file_location_path / f"{result_file_prefix}_preview.json"
            )

            with open(preview_file_path, "w") as preview_file:
                json.dump(preview_data, preview_file, default=str)

            return str(preview_file_path)

        except Exception as e:
            logger.exception(msg=f"Writing statistics failed with exception: {str(e)}")
            raise e

    @staticmethod
    def read_statistics_from_file(
        numerical_stats_file: Optional[str] = None,
        categorical_stats_file: Optional[str] = None,
        page_size: Optional[int] = None,
        page_number: Optional[int] = None,
    ) -> List[ColumnStatistics]:
        statistics = []

        try:
            # Helper function to load and deserialize data from a given file path
            def load_statistics(file_path: str):
                try:
                    with open(file_path, "rb") as file:
                        data = json.loads(file.read())
                        if isinstance(data, list):  # Ensuring the JSON is an array
                            statistics.extend(
                                [ColumnStatistics(**item) for item in data]
                            )
                except Exception as e:
                    print(f"An error occurred while reading {file_path}: {e}")

            # Load numerical statistics if the file path is provided
            if numerical_stats_file:
                load_statistics(numerical_stats_file)

            # Load categorical statistics if the file path is provided
            if categorical_stats_file:
                load_statistics(categorical_stats_file)

            if page_size and page_number:
                # Calculate start and end indices for pagination
                start_index = (page_number - 1) * page_size
                end_index = start_index + page_size

                statistics = statistics[start_index:end_index]

            return statistics

        except Exception as e:
            logger.exception(
                msg=f"Unable read statistics. failed with exception: {str(e)}"
            )
            raise e

    @staticmethod
    def write_statistics_to_file(
        statistics: List[ColumnStatistics],
        result_file_location: str,
        result_file_prefix: Optional[str] = None,
        num_stats=True,
        cat_stats=True,
    ) -> Tuple[str, str]:
        if result_file_prefix is None:
            result_file_prefix = str(uuid.uuid4())

        try:
            # Define file paths
            result_file_location_path = Path(result_file_location)
            numerical_stats_file, categorical_stats_file = None, None

            if num_stats:
                # separating the numerical and categorical stats
                numerical_data = [
                    item.dict()
                    for item in statistics
                    if item.type == TabularColumnType.NUMERICAL
                ]
                numerical_stats_file = (
                    result_file_location_path
                    / f"{result_file_prefix}_numerical_stats.json"
                )
                # Write numerical stats to a json file
                with open(numerical_stats_file, "w") as num_file:
                    json.dump(numerical_data, num_file, default=str)

            if cat_stats:
                categorical_data = [
                    item.dict()
                    for item in statistics
                    if item.type == TabularColumnType.CATEGORICAL
                ]
                categorical_stats_file = (
                    result_file_location_path
                    / f"{result_file_prefix}_categorical_stats.json"
                )
                # Write categorical stats to file
                with open(categorical_stats_file, "w") as cat_file:
                    json.dump(categorical_data, cat_file, default=str)

            return str(numerical_stats_file), str(categorical_stats_file)

        except Exception as e:
            logger.exception(msg=f"Writing statistics failed with exception: {str(e)}")
            raise e

    @staticmethod
    def convert_statistics_from_client_supported_format_to_db_record_format(
        statistics: List[DataStatistics],
    ) -> List[ColumnStatistics]:
        def create_column_statistics(stats, type) -> List[ColumnStatistics]:
            result = []

            # Iterate through column names and data to create ColumnStatistics objects
            for column_name, data in zip(stats.column_names, stats.data):
                parameters = dict(zip(stats.row_names, data))
                column_statistics = ColumnStatistics(
                    name=column_name, type=type, parameters=parameters
                )
                result.append(column_statistics)

            return result

        result = []

        for item in statistics:
            match item:
                case NumericalStatistics():
                    result.extend(
                        create_column_statistics(item, TabularColumnType.NUMERICAL)
                    )
                case CategoricalStatistics():
                    result.extend(
                        create_column_statistics(item, TabularColumnType.CATEGORICAL)
                    )
        return result

    @staticmethod
    def convert_stastics_from_db_record_format_to_client_supported_format(
        column_statistics: List[ColumnStatistics],
    ) -> List[DataStatistics]:
        if not column_statistics:
            raise ValueError("The input column_statistics list is empty")

        # Group columns by type
        grouped_columns = defaultdict(list)

        for column_stat in column_statistics:
            grouped_columns[column_stat.type].append(column_stat)

        # Create DataStatistics objects for each group
        result: List[DataStatistics] = []

        for column_type, columns in grouped_columns.items():
            row_names = list(
                columns[0].parameters.keys()
            )  # Assuming all columns of the same type have the same row names
            column_names = [column.name for column in columns]
            data = [list(column.parameters.values()) for column in columns]

            # Create a DataStatistics object for each column type
            data_statistics = DataStatistics.model_validate(
                dict(
                    column_type=column_type,
                    column_names=column_names,
                    row_names=row_names,
                    data=data,
                )
            )
            result.append(data_statistics)

        return result

    @staticmethod
    def compute_numeric_statistics(dataframe):
        # Function to compute statistics for each partition
        def partition_stats(df):
            stats = df.describe(percentiles=[0.25, 0.5, 0.75])
            missing_values = df.isnull().sum()
            stats.loc["missing"] = missing_values
            return stats

        # Apply the function to each partition
        partitioned_stats = dataframe.map_partitions(partition_stats)
        # Compute the final aggregated statistics
        final_stats = partitioned_stats.compute()
        return final_stats

    @staticmethod
    def get_column_statistics_from_tabular_data(
        file_path: str,
        preview: bool = False,
        column_data_types: bool = False,
        calculate_numerical_stats: bool = True,  # New flag for numerical stats
        calculate_categorical_stats: bool = True,  # New flag for categorical stats
    ) -> dict:
        """
        This method is implemented using Polars to get Preview and Statistics from tabular dataset
        Input:
            file_path: str. Path of the csv/parquet
            preview: bool and optional flag. If it is true then it will return the preview.
            column_data_types: bool
            calculate_numerical_stats: bool. If True, calculate numerical statistics.
            calculate_categorical_stats: bool. If True, calculate categorical statistics.
        Output:
            dict:
                column_statistics: List[ColumnStatistics]
                total_rows: int
                preview: dict
                column_data_types: dict
        """

        try:
            data_source = DataSourceModel.from_path(file_path)
            input_data = data_source.dataframe
            original_data = data_source.original_dataframe

            statistics = []
            numerical_col_count, categorical_col_count = None, None

            # Compute numeric stats if the flag is True and there are numerical columns
            if calculate_numerical_stats:
                numeric_df = input_data.select_dtypes(include="number")
                if not numeric_df.columns.empty:
                    numeric_stats = (
                        DatasetsService.compute_numeric_statistics(numeric_df)
                        .fillna(np.nan)
                        .replace([np.nan], [None])
                        .T.to_dict(orient="split")
                    )
                    statistics.append(
                        NumericalStatistics(
                            column_type=ColumnType.NUMERICAL,
                            column_names=numeric_stats["index"],
                            row_names=numeric_stats["columns"],
                            data=numeric_stats["data"],
                        )
                    )
                    numerical_col_count = len(numeric_df.columns)

            # Compute categorical stats if the flag is True and there are categorical columns
            if calculate_categorical_stats:
                categoric_df = input_data.select_dtypes(exclude="number")
                if not categoric_df.columns.empty:
                    categoric_stats = (
                        dd.concat(
                            [
                                categoric_df.describe(exclude="number"),
                                categoric_df.isnull()
                                .sum()
                                .to_frame(name="missing")
                                .compute()
                                .T,
                            ],
                        )
                        .fillna(np.nan)
                        .replace([np.nan], [None])
                        .compute()
                        .T.to_dict(orient="split")
                    )
                    statistics.append(
                        CategoricalStatistics(
                            column_type=ColumnType.CATEGORICAL,
                            column_names=categoric_stats["index"],
                            row_names=categoric_stats["columns"],
                            data=categoric_stats["data"],
                        )
                    )
                    categorical_col_count = len(categoric_df.columns)

            total_rows = input_data.shape[0].compute()
            col_count = len(input_data.columns)
            result = {
                "column_statistics": statistics,
                "total_rows": total_rows,
                "col_count": col_count,
                "numerical_col_count": numerical_col_count,
                "categorical_col_count": categorical_col_count,
                "excel_sheets_name": None,
            }

            if preview:
                preview_data = (
                    input_data.head(1000)
                    .iloc[:, :500]
                    .fillna(np.nan)
                    .replace([np.nan], [None])
                    .to_dict(orient="split")
                )
                result["preview"] = preview_data

            if column_data_types:
                column_data_types = original_data.dtypes.apply(
                    lambda x: {
                        "datatype": str(x),
                        "data_category": DatasetsService.get_data_category(x),
                    }
                ).to_dict()
                result["column_data_types"] = column_data_types

            return result

        except Exception as e:
            logger.exception(msg=f"Failed with exception: {str(e)}")
            raise Exception(f"{str(e)}")

    def get_column_statistics_from_data_frame(
        self, input_data: Union[pd.DataFrame, dd.DataFrame]
    ) -> dict:
        result = dict()

        if not isinstance(input_data, (pd.DataFrame, dd.DataFrame)):
            raise Exception("Expecting the input_data as pandas/dask dataframe")

        if isinstance(input_data, dd.DataFrame):
            input_data = input_data.compute()

        column_statistics = []

        description = input_data.describe(
            include=[
                "int16",
                "int32",
                "int64",
                "float16",
                "float32",
                "float64",
                "object",
                "category",
            ]
        )  # Extend the types if needed (don't use all, since some data types may generate exceptions)
        missing_count = input_data.isnull().sum()
        description.loc["missing"] = missing_count

        numerical_col_count, categorical_col_count = 0, 0

        for column in description.columns:
            if input_data[column].dtype in [
                "int16",
                "int32",
                "int64",
                "float16",
                "float32",
                "float64",
            ]:
                column_type = TabularColumnType.NUMERICAL
                numerical_col_count += 1

            else:
                column_type = TabularColumnType.CATEGORICAL
                categorical_col_count += 1

            stats = description[column].fillna("").to_dict()

            column_stat = ColumnStatistics(
                name=column, type=column_type, parameters=stats
            )
            column_statistics.append(column_stat)

        result["column_statistics"] = column_statistics
        result["total_rows"] = input_data.shape[0]
        result["col_count"] = input_data.shape[1]
        result["numerical_col_count"] = numerical_col_count
        result["categorical_col_count"] = categorical_col_count

        return result

    def update_dataset_record_access_mode(
        self, dataset_id: str, name: str, description: str, access_mode: AccessMode
    ) -> bool:
        return self.datasets_dao.update_dataset_record_access_mode(
            dataset_id=dataset_id,
            name=name,
            description=description,
            access_mode=access_mode,
        )

    def get_selected_columns(self, columns_data: List[dict]):
        """
        To get selected features list

        Args:
            columns_data (List[dict]): list of dictionaries

        Returns:
            _type_: list of feature names
        """
        columns = [data["column_name"] for data in columns_data if data["selected"]]
        return columns

    def get_selected_dataframe(
        self, filepath: str, selected_columns: List[str]
    ) -> pd.DataFrame:
        """
        To get dataframe with selected columns.

        Args:
            filepath (str): path of the file
            selected_columns (List[str]): list of feature names

        Raises:
            Exception: _description_

        Returns:
            _type_: dataframe
        """

        try:
            return (
                DataSourceModel.from_path(filepath)
                .dataframe[selected_columns]
                .compute()
            )
        except Exception as e:
            raise Exception(f"Failed with exception, {str(e)}")

    
    def list_directory(path: Path, file_ext: Optional[str] = None) -> List[Dict[str, str]]:
        """Returns only the first-level children (files and folders) of the given directory.

        Args:
            path (Path): The root directory to scan.
            file_ext (Optional[str], optional): File extension filter (e.g., '.txt'). Defaults to None.

        Returns:
            List[Dict[str, str]]: A list of dictionaries representing files and folders.
        """

        children = []
        file_ext = file_ext.lower().strip() if file_ext else None  # Normalize extension

        with os.scandir(path) as entries:
            for entry in entries:
                full_path = entry.path

                if entry.is_dir(follow_symlinks=False):
                    children.append({
                        "name": entry.name,
                        "full_path": full_path,
                        "type": "folder",
                    })
                elif file_ext is None or entry.name.lower().endswith(file_ext):
                    children.append({
                        "name": entry.name,
                        "full_path": full_path,
                        "type": "file",
                    })

        return children

    @staticmethod
    def delete_files_helper(file_paths: List[Tuple[str, bool]]):
        """
        This is the helper function to delete file/folder on disk.
        args:
            file_paths: List[Tuple[bool, str]] --> A list of tuples, each containing a boolean indicating if the path is a folder (True) or a file (False), and the path itself.
        """
        for path, is_folder in file_paths:
            try:
                if is_folder:
                    shutil.rmtree(
                        path
                    )  # If the path is a folder, use shutil.rmtree to delete the folder and all its contents
                else:
                    os.remove(
                        path
                    )  # If the path is a file, use os.remove to delete the file

            except FileNotFoundError:
                raise FileNotFoundError(f"The path does not exist: {path}")

            except PermissionError:
                raise Exception(f"Permission denied: {path}")

            except Exception as e:
                raise Exception(f"Error deleting {path}: {e}")

    async def rename_dataset(
        self, dataset_id: str, name: str, last_modified_by: str
    ) -> bool:
        """Renaming of the existing dataset

        Args:
            dataset_id (str): _description_
            name (str): _description_

        Returns:
            bool: _description_
        """

        return await self.datasets_dao.update_dataset_name_async(
            dataset_id=dataset_id, name=name, last_modified_by=last_modified_by
        )

    def update_dataset_path_sync(self, dataset_id: str, updated_path: str) -> bool:
        """
        This is a utility function written for to update the datset path in mongodb
        """
        return self.datasets_dao.update_dataset_path_sync(
            dataset_id=dataset_id, updated_path=updated_path
        )

    def update_datset_statistics_preview_total_count_sync(
        self,
        dataset_id: str,
        numerical_stats_file: Optional[str] = None,
        categorical_stats_file: Optional[str] = None,
        preview_file_path: Optional[str] = None,
        total_row_count: Optional[int] = None,
        total_col_count: Optional[int] = None,
        total_numeric_col_count: Optional[int] = None,
        total_categorical_count: Optional[int] = None,
    ) -> bool:
        """
        This is a utility function to update column_statistics, total_row_count, preview of the dataset record
        """
        return self.datasets_dao.update_datset_statistics_preview_total_count(
            dataset_id=dataset_id,
            numerical_stats_file=numerical_stats_file,
            categorical_stats_file=categorical_stats_file,
            preview_file_path=preview_file_path,
            total_row_count=total_row_count,
            total_col_count=total_col_count,
            total_numeric_col_count=total_numeric_col_count,
            total_categorical_count=total_categorical_count,
        )

    def update_dataset_record_data_sync(
        self, dataset_id: str, key_to_update: str, data: Any
    ):
        return self.datasets_dao.update_dataset_record_data(
            dataset_id=dataset_id, key_to_update=key_to_update, data=data
        )

    def save_api_jobs_record_sync(
        self,
        dataset_id: str,
        user_id: str,
        action_id: str,
        job_type: ApiJobType,
        visualization_hash: Optional[str] = None,
        correlation_hash: Optional[str] = None,
        column_name: Optional[str] = None,
    ):
        api_job = ApiJob(
            dataset_id=dataset_id,
            user_id=user_id,
            action_id=action_id,
            created_at=datetime.now(timezone.utc),
            api_job_type=job_type,
            visualization_hash=visualization_hash,
            correlation_hash=correlation_hash,
            column_name=column_name,
        )

        return self.datasets_dao.insert_api_jobs_record(api_job=api_job)

    def get_api_job_record(
        self, api_job_id: Optional[str] = None, search_query: Optional[dict] = None
    ) -> Optional[ApiJob]:
        try:
            return self.datasets_dao.get_api_job_record_by_id(
                api_job_id=api_job_id, search_query=search_query
            )
        except KeyError as e:
            logger.error(f"Error while fetching action record: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error while fetching action record: {str(e)}")
            raise e

    def get_api_job_action_record_sync(
        self, api_job_id: Optional[str] = None, search_query: Optional[dict] = None
    ) -> Optional[Action]:
        try:
            record = self.get_api_job_record(api_job_id, search_query)
            if record is None:
                return None
            if record.action_id is None:
                return None
            action = self.action_dao.get_action_by_id(record.action_id)
            return action
        except KeyError as e:
            logger.error(f"Error while fetching action record: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error while fetching action record: {str(e)}")
            raise e

    def update_api_job_record_sync(
        self, api_job_id: str, key_to_update: str, data: Any
    ):
        return self.datasets_dao.update_preview_stats_record(
            api_job_id=api_job_id, key_to_update=key_to_update, data=data
        )

    def delete_api_jobs_record_sync(self, api_job_id: str):
        return self.datasets_dao.delete_api_jobs_record(api_job_id=api_job_id)

    @staticmethod
    def get_unique_values_in_column(dataset: Dataset, column_name: str) -> np.ndarray:
        """
        Get unique values in a column of a dataset efficiently for large data.

        Parameters:
        dataset (Dataset): The dataset object containing the location of the dataset file.
        column_name (str): The name of the column to extract unique values from.

        Returns:
        np.ndarray: An array of unique values in the specified column.

        Raises:
        ValueError: If the file format is unsupported or the column is not categorical.
        Exception: If there is an error reading the file or processing the data.
        """
        input_data = DataSourceModel.from_dataset(dataset).dataframe

        # Check if the column datatype is categorical
        column_dtype = input_data[column_name].dtype
        logger.info(f"Column datatype: {column_dtype}")
        if pd.api.types.is_numeric_dtype(column_dtype):
            logger.error(
                f"Column {column_name} is not categorical. Found datatype: {column_dtype}"
            )
            raise ValueError(
                f"Column {column_name} is not categorical. Found datatype: {column_dtype}"
            )

        def get_unique_values(series):
            series = series.astype("string").astype("object")
            return series.unique()

        # Compute unique values per partition and aggregate
        logger.debug(f"Computing unique values for column '{column_name}'")
        start_time = time.time()
        unique_values_per_partition = input_data[column_name].map_partitions(
            get_unique_values
        )
        unique_values = np.unique(unique_values_per_partition.compute())

        # Sort the unique values in-place
        unique_values.sort()
        end_time = time.time()
        logger.info(f"Unique values computed in {end_time - start_time:.2f} seconds")

        return unique_values

    @staticmethod
    def write_column_metadata_to_file(
        column_metadata: dict,
        result_file_location: str,
        metadata: Optional[DatasetMetadata] = None,
    ) -> str:
        try:
            if not metadata or not metadata.columns_metadata_file:
                result_file_location_path = Path(result_file_location)
                result_file_name = f"{str(uuid.uuid4())}_column_metadata.json"
                column_metadata_file = result_file_location_path / result_file_name
            else:
                # if file already exists, update the file contents.
                column_metadata_file = metadata.columns_metadata_file

            with open(column_metadata_file, "w") as fp:
                json.dump(column_metadata, fp)

            return str(column_metadata_file)

        except Exception as e:
            logger.exception(msg=f"Writing statistics failed with exception: {str(e)}")
            raise e

    @staticmethod
    def read_column_metadata_from_file(column_metadata_file: Path) -> dict:
        try:
            with column_metadata_file.open() as fp:
                column_metadata = json.load(fp)

            return column_metadata

        except Exception as e:
            logger.exception(
                msg=f"Reading column metadata failed with exception: {str(e)}"
            )
            raise e

    @staticmethod
    def get_data_category(dtype: str) -> str:
        """helper function to get the data category of the column data type

                Args:
            dtype (str): python data type of the column

        Returns:
            str: data category of the column data type
        """

        if pd.api.types.is_numeric_dtype(dtype):
            return TabularColumnType.NUMERICAL
        else:
            return TabularColumnType.CATEGORICAL
