from __future__ import annotations

import logging
import traceback
from pathlib import Path
from typing import Annotated, List

import pandas as pd
import polars as pl
from pydantic import Field, PositiveInt, RootModel

from app.core.celery.celery_worker import create_celery_app
from app.core.celery.global_config import API_JOBS_QUEUE, API_JOBS_RK
from app.core.services.action.schemas import Action, ActionRunStatus
from app.core.services.action.service import ActionService
from app.services.data.assets.datasets.schemas import ApiJobType
from app.services.data.assets.datasets.service import DatasetsService
from app.services.workflows.designer.base_schemas import WidgetType
from app.services.workflows.designer.schemas import (
    ApiJobsConfig,
    PreviewStatsConfig,
    Widget,
)

from ......config.env_vars import environment
from ....assets.datasets.schemas import ColumnStatistics, Dataset
from ...data.source.model import DataSourceModel
from ..utils import hash_obj
from .v1_0.model import DataPreview as DataPreviewV1_0

logger = logging.getLogger(__package__)


class DataPreview(RootModel):
    root: Annotated[DataPreviewV1_0, Field(discriminator="version")]

    @classmethod
    def from_data_source(
        cls,
        data_source: DataSourceModel,
        page: PositiveInt = 1,
        page_size: PositiveInt = 100,
    ) -> DataPreview:
        return DataPreview(
            root=DataPreviewV1_0.from_data_source(
                data_source=data_source, page=page, page_size=page_size
            )
        )

    @staticmethod
    def from_db(
        dataset: Dataset,
        page: PositiveInt = 1,
        page_size: PositiveInt = 100,
        dataset_service: DatasetsService = None,
        action_service: ActionService = None,
    ):

        try:

            if not dataset:
                return None

            # If dataset record does not have the preview stored in db then create and update statistics, total_row_count, preview in db
            action_record = dataset_service.get_api_job_action_record_sync(
                api_job_id=dataset.api_job_id
            )
            if action_record and action_record.status == ActionRunStatus.RUNNING:
                return {"api_job_id": dataset.api_job_id}

            if action_record and action_record.status == ActionRunStatus.FAILED:
                raise Exception(
                    f"Failed to compute preview for dataset {dataset.name}, api_job_id: {dataset.api_job_id}"
                )

            if dataset.dataset_information:
                preview_exists = dataset.dataset_information[0].preview or (dataset.dataset_information[0].preview_file and Path(dataset.dataset_information[0].preview_file).exists())

                if not preview_exists:
                    action_config = Widget(
                        urn="",
                        name=f"Preview_{dataset.name}",
                        description=f"Preview data generation for dataset id {dataset.id}",
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
                        # TODO: add new dockerfile and changes to reflect
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

                    if dataset.dataset_information[0].preview:
                        start_index = (page - 1) * page_size
                        end_index = start_index + page_size

                        preview_data = dataset.dataset_information[0].preview
                        preview = preview_data.get("data", [])

                        preview, column_names, total_rows = (
                            preview[start_index:end_index],
                            preview_data.get("columns", []),
                            dataset.dataset_information[0].row_count,
                        )
                        total_columns = dataset.dataset_information[0].col_count

                    else:
                        preview_data = DatasetsService.read_preview_from_file(
                            preview_file=dataset.dataset_information[0].preview_file,
                            page_size=page_size,
                            page_number=page,
                        )

                        preview, column_names, total_rows = (
                            preview_data.get("data", []),
                            preview_data.get("columns", []),
                            dataset.dataset_information[0].row_count,
                        )
                        total_columns = dataset.dataset_information[0].col_count

                logger.info(f"total_columns {total_columns}")

                return DataPreview(
                    version="1.0",
                    column_names=column_names,
                    data=preview,
                    total_rows=total_rows,
                    page=page,
                    page_size=page_size,
                    total_columns=total_columns,
                )
        except Exception as e:
            print(
                "Exception occured while fetching preview of the dataset: ",
                traceback.format_exc(),
            )

    @classmethod
    def from_dataset(
        cls,
        dataset: Dataset,
        page: PositiveInt = 1,
        page_size: PositiveInt = 100,
    ) -> DataSourceModel:

        if page > 100:
            page = 1

        path = (
            environment.datasets_cache_folder
            / dataset.id
            / "preview"
            / hash_obj((page, page_size))
        )
        path.parent.mkdir(exist_ok=True, parents=True)
        if not path.exists():
            preview = cls.from_data_source(
                DataSourceModel.from_dataset(dataset),
                page=page,
                page_size=page_size,
            )
            with path.open("w") as file:
                file.write(preview.model_dump_json())
        else:
            with path.open("r") as file:
                preview = DataPreview.model_validate_json(file.read())
        return preview
