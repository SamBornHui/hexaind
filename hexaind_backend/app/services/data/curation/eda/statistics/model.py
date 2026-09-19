from __future__ import annotations

import asyncio
import logging
import pickle
import traceback
import zlib
from pathlib import Path
from typing import Annotated, List, Optional

from numpy import ndarray
from pydantic import Field, PositiveInt, RootModel

from app.config.redis_config import AsyncRedis
from app.core.celery.celery_worker import create_celery_app
from app.core.celery.global_config import API_JOBS_QUEUE, API_JOBS_RK
from app.core.services.action.schemas import Action, ActionRunStatus
from app.core.services.action.service import ActionService
from app.services.data.assets.datasets.service import DatasetsService
from app.services.workflows.designer.base_schemas import WidgetType
from app.services.workflows.designer.schemas import (
    ApiJobsConfig,
    PreviewStatsConfig,
    UniqueValuesConfig,
    Widget,
)

from ......config.env_vars import environment
from ....assets.datasets.schemas import ApiJobType, Dataset, TabularColumnType
from ...data.source.model import DataSourceModel
from ..utils import hash_obj
from .v1_0.model import DataStatisticsModel as DataStatisticsModelV1_0

logger = logging.getLogger(__package__)


class DataStatistics(RootModel):
    root: Annotated[DataStatisticsModelV1_0, Field(discriminator="version")]

    @classmethod
    def from_data_source(
        cls,
        data_source: DataSourceModel,
        page: Optional[PositiveInt] = 1,
        page_size: Optional[PositiveInt] = 100,
    ) -> DataStatistics:
        return DataStatistics(
            root=DataStatisticsModelV1_0.from_data_source(data_source=data_source)
        )

    @staticmethod
    def from_db(
        dataset: Dataset,
        num_stat,
        cat_stat,
        page: Optional[PositiveInt] = None,
        page_size: Optional[PositiveInt] = None,
        dataset_service: DatasetsService = None,
        action_service: ActionService = None,
    ):

        try:

            if not dataset:
                return None

            action_record = dataset_service.get_api_job_action_record_sync(
                api_job_id=dataset.api_job_id
            )
            if action_record and action_record.status == ActionRunStatus.RUNNING:
                return {"api_job_id": dataset.api_job_id}

            if action_record and action_record.status == ActionRunStatus.FAILED:
                raise Exception(
                    f"Failed to compute statistics for dataset {dataset.name}, api_job_id: {dataset.api_job_id}"
                )

            if dataset.dataset_information:
                statistics_exist = dataset.dataset_information[0].statistics or (
                    dataset.dataset_information[0].numerical_statistics_file
                    and dataset.dataset_information[0].categorical_statistics_file
                    and Path(
                        dataset.dataset_information[0].numerical_statistics_file
                    ).exists()
                    and Path(
                        dataset.dataset_information[0].categorical_statistics_file
                    ).exists()
                )

                if not statistics_exist:
                    # create a new action for generating statistics
                    action_config = Widget(
                        urn="",
                        name=f"Statistics_{dataset.name}",
                        description=f"Statistics data generation for dataset id {dataset.id}",
                        type=WidgetType.API_JOBS,
                        config=ApiJobsConfig(
                            job_type=ApiJobType.PREVIEW_STATS,
                            config=PreviewStatsConfig(dataset_id=str(dataset.id)),
                            widget_type=WidgetType.API_JOBS,
                        ),
                    )
                    action = Action(
                        run_id="",
                        action_config=action_config,
                        status=ActionRunStatus.IDLE,
                    )

                    action_ids = action_service.create_actions_sync(actions=[action])
                    api_job_id = dataset_service.save_api_jobs_record_sync(
                        dataset_id=dataset.id,
                        user_id=dataset.user_id,
                        action_id=action_ids[0],
                        job_type=ApiJobType.PREVIEW_STATS,
                    )
                    celeryApp = create_celery_app("eda_generator")
                    celeryApp.send_task(
                        "task_eda_generate_update",
                        kwargs={"action_id": action_ids[0], "api_job_id": api_job_id},
                        queue=API_JOBS_QUEUE,
                        routing_key=API_JOBS_RK,
                    )

                    dataset_service.update_dataset_record_data_sync(
                        dataset_id=str(dataset.id),
                        key_to_update="api_job_id",
                        data=api_job_id,
                    )

                    return {"api_job_id": api_job_id}

                else:
                    info = dataset.dataset_information[0]

                    total_rows = info.row_count if info.row_count else 0
                    total_columns = info.col_count if info.col_count else 0
                    numerical_col_count = (
                        info.numerical_col_count if info.numerical_col_count else 0
                    )
                    categorical_col_count = (
                        info.categorical_col_count if info.categorical_col_count else 0
                    )

                    if info.statistics:
                        # case for the old datasets where we stored the stats in db instead of files

                        client_format_statistics = info.statistics
                        if page_size and page:
                            start_index = (page - 1) * page_size
                            end_index = start_index + page_size

                            client_format_statistics = client_format_statistics[
                                start_index:end_index
                            ]

                        total_columns = (
                            info.col_count if info.col_count else len(info.statistics)
                        )

                        numerical_col_count, categorical_col_count = 0, 0
                        for column_stat in info.statistics:
                            if column_stat.type == TabularColumnType.NUMERICAL:
                                numerical_col_count += 1
                            else:
                                categorical_col_count += 1

                    else:
                        # case for the new datasets where we stored the stats in files

                        numerical_stats_file, categorical_stats_file = (
                            info.numerical_statistics_file,
                            info.categorical_statistics_file,
                        )

                        if num_stat and not cat_stat:
                            categorical_stats_file = None

                        if cat_stat and not num_stat:
                            numerical_stats_file = None

                        client_format_statistics = (
                            DatasetsService.read_statistics_from_file(
                                numerical_stats_file=numerical_stats_file,
                                categorical_stats_file=categorical_stats_file,
                                page_size=page_size,
                                page_number=page,
                            )
                        )

                    statistics: List[DataStatistics] = (
                        DatasetsService.convert_stastics_from_db_record_format_to_client_supported_format(
                            column_statistics=client_format_statistics
                        )
                    )

                return DataStatisticsModelV1_0(
                    version="1.0",
                    statistics=statistics,
                    rows_count=total_rows,
                    columns_count=total_columns,
                    numerical_columns_count=numerical_col_count,
                    categorical_columns_count=categorical_col_count,
                )

        except Exception as e:
            logger.exception(
                "Exception occured while fetching statistics of the dataset: ",
            )

    @classmethod
    def from_dataset(cls, dataset: Dataset) -> DataSourceModel:
        path = (
            environment.datasets_cache_folder / dataset.id / "statistics" / hash_obj(1)
        )
        path.parent.mkdir(exist_ok=True, parents=True)
        if not path.exists():
            statistics = cls.from_data_source(
                DataSourceModel.from_dataset(dataset),
            )
            with path.open("w") as file:
                file.write(statistics.model_dump_json())
        else:
            with path.open("r") as file:
                statistics = DataStatistics.model_validate_json(file.read())
        return statistics

    @staticmethod
    async def get_unique_column_values(
        dataset: Dataset,
        column_name: str,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        dataset_service: DatasetsService = None,
        action_service: ActionService = None,
        redis_async_client: AsyncRedis = None,
    ):
        dataset_id = dataset.id
        redis_key = f"{dataset_id}:{column_name}"

        logger.info(
            f"Fetching unique values for column '{column_name}' in dataset '{dataset_id}'"
        )

        if page and page_size:
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
        else:
            start_index, end_index = None, None

        exists = await redis_async_client.exists(redis_key)
        if exists:
            logger.info(
                f"Found cached unique values for column '{column_name}' in Redis"
            )
            # 1. Retrieve the compressed data from Redis
            compressed_data = await redis_async_client.get(redis_key)

            # 2. Decompress the data using zlib
            decompressed_data = zlib.decompress(compressed_data)

            # 3. Deserialize the decompressed data back to a NumPy array
            retrieved_arr: ndarray = pickle.loads(decompressed_data)

            return {
                "total": retrieved_arr.size,
                "values": retrieved_arr[start_index:end_index].tolist(),
            }

        logger.info(
            f"No cached data found for column '{column_name}', checking for existing background job"
        )
        # Check if background job exists and is running
        search_query = {
            "dataset_id": dataset_id,
            "column_name": column_name,
            "api_job_type": ApiJobType.UNIQUE_VALUES,
        }
        job_record = await asyncio.to_thread(
            dataset_service.get_api_job_record, search_query=search_query
        )
        api_job_id = job_record.id if job_record else None
        action_record = await asyncio.to_thread(
            dataset_service.get_api_job_action_record_sync, api_job_id=api_job_id
        )

        if action_record and action_record.status == ActionRunStatus.RUNNING:
            logger.info(
                f"Background job is already running for column '{column_name}' in dataset '{dataset_id}', api_job_id: {api_job_id}"
            )
            return {"api_job_id": api_job_id}
        elif action_record and action_record.status == ActionRunStatus.FAILED:
            logger.error(
                f"Background job failed for column '{column_name}' in dataset '{dataset_id}', api_job_id: {api_job_id}"
            )
            raise Exception(
                f"Failed to compute unique values for column {column_name} in dataset {dataset.name}, api_job_id: {api_job_id}"
            )
        elif action_record:
            logger.info(
                f"Deleting old job record for column '{column_name}' in dataset '{dataset_id}', api_job_id: {api_job_id}"
            )
            # Delete the old record and create a new one as data is not present in Redis
            await asyncio.to_thread(
                dataset_service.delete_api_jobs_record_sync, api_job_id=api_job_id
            )

        logger.info(
            f"Creating new background job for column '{column_name}' in dataset '{dataset_id}'"
        )

        # Create a new background job to compute unique values for the column
        action_config = Widget(
            urn="",
            name=f"UniqueValues_{dataset.name}_{column_name}",
            description=f"Unique values computation for column {column_name} in dataset {dataset.name}, dataset_id: {dataset.id}",
            type=WidgetType.API_JOBS,
            config=ApiJobsConfig(
                job_type=ApiJobType.UNIQUE_VALUES,
                config=UniqueValuesConfig(
                    dataset_id=str(dataset.id), column_name=column_name
                ),
                widget_type=WidgetType.API_JOBS,
            ),
        )

        action = Action(
            run_id="",
            action_config=action_config,
            status=ActionRunStatus.IDLE,
        )

        action_ids = await asyncio.to_thread(
            action_service.create_actions_sync, actions=[action]
        )
        api_job_id = await asyncio.to_thread(
            dataset_service.save_api_jobs_record_sync,
            dataset_id=dataset.id,
            user_id=dataset.user_id,
            action_id=action_ids[0],
            column_name=column_name,
            job_type=ApiJobType.UNIQUE_VALUES,
        )

        celery_app = create_celery_app("eda_generator")
        celery_app.send_task(
            "task_eda_generate_unique_values",
            kwargs={"action_id": action_ids[0]},
            queue=API_JOBS_QUEUE,
            routing_key=API_JOBS_RK,
        )

        logger.info(
            f"Task sent to Celery for column '{column_name}' in dataset '{dataset_id}', action_id: {action_ids[0]}"
        )

        return {"api_job_id": api_job_id}
