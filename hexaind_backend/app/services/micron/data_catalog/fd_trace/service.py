import glob
import logging
import os
import shutil
import uuid
from collections.abc import MutableMapping, MutableSequence
from ctypes import Array
from datetime import datetime, timezone
from functools import reduce
from itertools import chain
from operator import or_
from pathlib import Path
from typing import Tuple, TypedDict

import pandas as pd
import polars as pl
from bson import ObjectId
from dateutil.parser import parse
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from app.config.env_vars import environment
from app.core.celery.celery_worker import create_celery_app
from app.services.micron.data_catalog import query

from .dao import FdTraceDao
from .dummy_files import DUMMY_FILES
from .job_dao import FdTraceJobDao
from .schemas import *
from .utils import DirectoryMapping

logger = logging.getLogger(__package__)

DATA_CATALOG_APPLICATION_CREDENTIALS_FILE = Path(
    os.environ.get(
        "DATA_CATALOG_APPLICATION_CREDENTIALS_FILE",
        "/hexaind-data/json_files/staging-405018-ad97bb300216.json",
    )
)

GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "gdw-team-tdam-vpm")

DATA_CATALOG_GCS_BUCKET = os.environ.get(
    "DATA_CATALOG_GCS_BUCKET", "gdw-team-tdam-vpm-default"
)

SUPPORTED_FACILITIES = ["4", "10", "15", "16", "6", "11", "7"]

DUMMY_FD_CATALOG_FILE_PATH = (
    Path(__file__).parent / "remove_dummy_fd_catalog.pqt"
).absolute()

DUMMY_FD_TRACE_FILE_PATH = (
    Path(__file__).parent / "remove_dummy_fd_trace.pqt"
).absolute()

STAGE_AND_STAGE_JOB_ID_KEY_DICT = {
    "IDLE": ("", 0, "IDLE"),
    "FACILITIES": ("facility_stage_job_id", 1, "IDLE"),
    "TECH_NODE": ("tech_node_stage_job_id", 2, "FACILITIES"),
    "DESIGN_ID": ("design_ids_stage_job_id", 3, "TECH_NODE"),
    "TRAVELER_ID": ("traveler_id_step_stage_job_id", 4, "DESIGN_ID"),
    "TRAVELER_STEP": ("traveler_step_stage_job_id", 5, "TRAVELER_ID"),
    "SAVE_HIGH_LEVEL_DC_DETAILS": (
        "save_high_level_dc_details_job_id",
        5,
        "TRAVELER_STEP",
    ),
    "FD_CONTEXT": ("fd_context_stage_job_id", 6, "TRAVELER_STEP"),
    "FD_SENSOR": ("sensors_stage_job_id", 7, "FD_CONTEXT"),
    "FD_TRACE": ("fd_trace_stage_job_id", 8, "FD_SENSOR"),
    "LOT_ID": ("lot_ids_stage_job_id", 9, "TRAVELER_STEP"),
    "WAFER_ID": ("wafer_ids_stage_job_id", 9, "LOT_ID"),
    "UC2_SIGMA_DATA": ("uc2_sigma_job_id", 11, "UC2_SIGMA_DATA"),
    "UC3_FD_CONTEXT_APPLY_FILTERS": (
        "uc3_fd_context_apply_filters_job_id",
        10,
        "WAFER_ID",
    ),
    "FINAL_DATA_AGGREGATE": ("final_data_aggregate_stage_job_id", 11, "FD_CONTEXT"),
    "UC3_SIGMA_DATA": ("uc3_sigma_job_id", 12, "UC3_SIGMA_DATA"),
    "LOT_WAFER_SAVE": ("lot_wafer_stage_job_id", 9, "LOT_ID"),
    "PROBE_CONTEXT": ("probe_context_job_id", 20, "TRAVELER_STEP"),
    "PROBE_DATA_PULL": ("probe_data_pull_job_id", 21, "PROBE_CONTEXT"),
}

UC2_SIGMA_DROPDOWN_FOLDER_NAMES = {
    # DROPDOWN_NAME   : (SOURCE , DESTINATION) #will parse source and write a parquet file to destination
    "measurement_steps": (
        "sigma_measurement_catalog/{}/test_ids",
        "measurement_steps.parquet",
    ),  # fab
    "point_steps": ("sigma_point_catalog/{}/test_ids", "point_steps.parquet"),
    "run_parameters": ("SIGMA/{}/RUN_PARAMS", "run_parameters.parquet"),
    "measurement_parameters": (
        "SIGMA/{}/MEASUREMENT_PARAMS",
        "measurement_parameters.parquet",
    ),
    "point_parameters": ("SIGMA/{}/POINT_PARAMS", "point_parameters.parquet"),
    "wafer_parameters": ("SIGMA/{}/WAFER_PARAMS", "wafer_parameters.parquet"),
}


def submit_data_pull_job(task_id: str, data_pull_job_id: str, stage_job_id: str):
    # inserting the start task in queue
    celeryApp = create_celery_app("run_workflow")
    celeryApp.send_task(
        "task_data_pull_stage",
        task_id=task_id,
        kwargs={"data_pull_job_id": data_pull_job_id, "stage_job_id": stage_job_id},
        queue="data_catalog",
        routing_key="fd_trace",
    )


class Tool(TypedDict):
    tool_name: str
    tool_id: str


class FdTraceDataPullService:
    def __init__(
        self,
        db_sync_client: MongoClient = None,
        db_async_client: AsyncIOMotorClient = None,
    ) -> None:
        self.fd_trace_dao = FdTraceDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )

        self.fd_trace_job_dao = FdTraceJobDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )

    def sort_json(self, value):
        """
        Recursively sorts lists and dicts in the JSON object (Python dict).
        """
        if isinstance(value, MutableMapping):  # If it's a dictionary, sort its values
            return {k: self.sort_json(v) for k, v in sorted(value.items())}
        elif isinstance(value, MutableSequence):  # If it's a list, sort its items
            return sorted(self.sort_json(v) for v in value)
        return value

    def compare_json(self, json1, json2):
        """
        Compares two JSON objects, considering unordered lists as equal if they contain the same elements.
        """
        return self.sort_json(json1) == self.sort_json(json2)

    def is_inputs_changed(self, existing_inputs: dict | None, new_inputs: dict | None):
        if existing_inputs is None:
            json1 = {}
        else:
            json1 = existing_inputs

        if new_inputs is None:
            json2 = {}
        else:
            json2 = new_inputs

        return not (self.compare_json(json1=json1, json2=json2))

    def check_if_current_stage_is_next(
        self, last_ran_stage: FDDataPullStages, current_stage: FDDataPullStages
    ) -> bool:
        last_ran_stage_level = STAGE_AND_STAGE_JOB_ID_KEY_DICT.get(last_ran_stage)[1]
        current_stage_level = STAGE_AND_STAGE_JOB_ID_KEY_DICT.get(current_stage)[1]
        if (current_stage_level - last_ran_stage_level) != 1:
            return False

        return True

    def check_if_stage_config_is_valid(
        self, last_ran_stage: FDDataPullStages, current_stage: FDDataPullStages
    ) -> bool:
        last_ran_stage_level = STAGE_AND_STAGE_JOB_ID_KEY_DICT.get(last_ran_stage)[1]
        current_stage_level = STAGE_AND_STAGE_JOB_ID_KEY_DICT.get(current_stage)[1]

        if last_ran_stage_level >= current_stage_level:
            return True

        return False

    def check_if_prev_stage_is_executed_successfully(
        self,
        last_ran_stage: FDDataPullStages,
        prev_stage_job_config_record: FdDataPullJobConfig,
    ) -> bool:
        if not self.check_if_stage_config_is_valid(
            last_ran_stage=last_ran_stage,
            current_stage=prev_stage_job_config_record.stage,
        ):
            return False

        # check if previous state is success or not
        if (
            prev_stage_job_config_record.stage_config.status.status
            != DataPullStatus.SUCCESS
        ):
            return False

        return True

    async def fetch_data_pull_job_record(self, job_id: str) -> FdDataPullConfig:
        data_pull_job_record: FdDataPullConfig = (
            await self.get_fd_data_pull_job_record_async(job_id=job_id)
        )
        return data_pull_job_record

    async def reset_all_forward_stage_configs(
        self,
        data_pull_job_record_id: str,
        data_pull_job_record: FdDataPullConfig,
        stage: FDDataPullStages,
    ):
        stage_level = STAGE_AND_STAGE_JOB_ID_KEY_DICT.get(stage)[1]

        prev_stage = STAGE_AND_STAGE_JOB_ID_KEY_DICT.get(stage)[2]

        stages_to_be_reset = []
        remaining_stages = []
        for (
            current_stage_job_id_key,
            level,
            _,
        ) in STAGE_AND_STAGE_JOB_ID_KEY_DICT.values():
            if level >= stage_level:
                stages_to_be_reset.append(
                    ObjectId(
                        getattr(data_pull_job_record, current_stage_job_id_key, None)
                    )
                )
            else:
                remaining_stages.append((level,))

        await self.fd_trace_job_dao.async_collection.update_many(
            {"_id": {"$in": stages_to_be_reset}},
            {"$set": {"stage_config.status.status": "NOT_CONFIGURED"}},
        )

        await self.fd_trace_dao.async_collection.update_one(
            {"_id": ObjectId(data_pull_job_record_id)},
            {"$set": {"current_stage": prev_stage, "data_pull_status": "IDLE"}},
        )

    async def fetch_stage_config_record(
        self,
        data_pull_job_record: FdDataPullConfig,
        stage: FDDataPullStages,
        ignore_last_run_level: bool = False,
    ) -> FdDataPullJobConfig:
        if stage == FDDataPullStages.IDLE:
            raise Exception("Invalid stage IDLE cannot fetch the stage config record")

        current_stage_job_id_key = STAGE_AND_STAGE_JOB_ID_KEY_DICT.get(stage)[0]
        stage_config_record: FdDataPullJobConfig = (
            await self.get_fd_data_pull_job_config_record_async(
                job_config_id=getattr(
                    data_pull_job_record, current_stage_job_id_key, None
                )
            )
        )

        if not ignore_last_run_level:
            if not self.check_if_stage_config_is_valid(
                last_ran_stage=data_pull_job_record.current_stage, current_stage=stage
            ):
                # return default config record
                stage_config_record.stage_config.status = DataPullStatusConfig()
                stage_config_record.stage_config.inputs = None
                stage_config_record.stage_config.outputs = None

        return stage_config_record

    async def fetch_prev_stage_config_record(
        self, data_pull_job_record: FdDataPullConfig, stage: FDDataPullStages
    ) -> FdDataPullJobConfig:
        prev_stage = STAGE_AND_STAGE_JOB_ID_KEY_DICT.get(stage)[2]

        return await self.fetch_stage_config_record(
            data_pull_job_record=data_pull_job_record, stage=prev_stage
        )

    async def get_stage_status_async(
        self,
        data_pull_job_id: str,
        stage: FDDataPullStages,
        data_pull_job_record: FdDataPullConfig | None = None,
    ) -> FdDataPullStausResponse:
        if data_pull_job_record is None:
            data_pull_job_record = await self.fetch_data_pull_job_record(
                job_id=data_pull_job_id
            )

        if stage == FDDataPullStages.IDLE:
            stage_status = FdDataPullStausResponse(
                current_stage=stage,
                current_stage_status=DataPullStatus.NOT_CONFIGURED,
                fd_data_pull_job_status=data_pull_job_record.data_pull_status,
                job_status=None,
            )
            return stage_status

        stage_config_record: FdDataPullJobConfig = await self.fetch_stage_config_record(
            data_pull_job_record=data_pull_job_record, stage=stage
        )

        bq_job_config = BigqueryDataPullJobConfig(
            **stage_config_record.stage_config.status.job_config
        )

        stage_status = FdDataPullStausResponse(
            current_stage=stage,
            current_stage_status=stage_config_record.stage_config.status.status,
            fd_data_pull_job_status=data_pull_job_record.data_pull_status,
            job_status=bq_job_config.job_status,
        )

        return stage_status

    async def get_last_ran_stage_status_async(
        self,
        data_pull_job_id: str,
        data_pull_job_record: FdDataPullConfig | None = None,
    ) -> FdDataPullStausResponse:
        if data_pull_job_record is None:
            data_pull_job_record = await self.fetch_data_pull_job_record(
                job_id=data_pull_job_id
            )

        return await self.get_stage_status_async(
            data_pull_job_id=data_pull_job_id,
            stage=data_pull_job_record.current_stage,
            data_pull_job_record=data_pull_job_record,
        )

    async def save_stage_inputs_async(
        self, data_pull_job_id: str, stage: FDDataPullStages, inputs
    ):
        data_pull_job_record = await self.fetch_data_pull_job_record(
            job_id=data_pull_job_id
        )
        stage_config_record: FdDataPullJobConfig = await self.fetch_stage_config_record(
            data_pull_job_record=data_pull_job_record,
            stage=stage,
            ignore_last_run_level=True,
        )
        if stage_config_record.stage_config is None:
            raise Exception(
                f"Stage config record is malformed no stage config found : {data_pull_job_id}"
            )
        if stage_config_record.stage_config.status == DataPullStatus.RUNNING:
            raise ValueError(
                f"Unable to save inputs as {stage} is currently running, please halt the {stage}."
            )
        if inputs is None:
            raise ValueError("inputs cannot be None")

        stage_inputs = None
        match stage:
            case FDDataPullStages.UC2_SIGMA_DATA:
                stage_inputs = UC2SigmaDataPullInput(**inputs)
            case FDDataPullStages.UC3_FD_CONTEXT_APPLY_FILTERS:
                stage_inputs = UC3FDContextApplyFiltersInput(**inputs)
            case FDDataPullStages.UC3_SIGMA_DATA:
                stage_inputs = UC3SigmaInput(**inputs)
            case FDDataPullStages.PROBE_CONTEXT:
                stage_inputs = ProbeContextDataPullInput(**inputs)
            case FDDataPullStages.PROBE_DATA_PULL:
                stage_inputs = ProbeDataPullInputs(**inputs)
            case _:
                raise ValueError(f"Invalid stage: {stage}")

        await self.fd_trace_job_dao.update_fd_data_stage_job_record_current_status_and_inputs_async(
            stage_config_record.id,
            DataPullStatus.SAVED,
            stage_inputs.model_dump(mode="json", by_alias=True),
        )

    async def get_stage_results_async(
        self,
        data_pull_job_id: str,
        stage: FDDataPullStages,
        data_pull_job_record: FdDataPullConfig | None = None,
        ignore_last_run_level: bool = False,
    ):
        if data_pull_job_record is None:
            data_pull_job_record = await self.fetch_data_pull_job_record(
                job_id=data_pull_job_id
            )

        results = {}
        if (data_pull_job_record.current_stage == FDDataPullStages.IDLE) or (
            stage == FDDataPullStages.IDLE
        ):
            current_stage_status = DataPullStatus.NOT_CONFIGURED
        else:
            stage_config_record: FdDataPullJobConfig = (
                await self.fetch_stage_config_record(
                    data_pull_job_record=data_pull_job_record,
                    stage=stage,
                    ignore_last_run_level=ignore_last_run_level,
                )
            )
            current_stage_status = stage_config_record.stage_config.status.status
            if stage_config_record.stage_config.status.status == DataPullStatus.SUCCESS:
                results = stage_config_record.stage_config.outputs.model_dump()

        inputs = stage_config_record.stage_config.inputs
        if inputs is None:
            inputs = {}
        else:
            inputs = inputs.model_dump()

        stage_config_result = FdDataPullStausResult(
            current_stage=stage_config_record.stage,
            current_stage_status=current_stage_status,
            current_stage_results=results,
            current_stage_inputs=inputs,
        )

        return stage_config_result

    def check_if_stage_can_be_triggered_async(
        self,
        stage: FDDataPullStages,
        data_pull_job_record: FdDataPullConfig,
        prev_stage_config_record: FdDataPullJobConfig,
    ) -> bool:
        # check if any stage is running
        if data_pull_job_record.data_pull_status == DataCatalogStatus.RUNNING:
            raise Exception(
                f"cannot trigger {stage}: '{data_pull_job_record.current_stage}' execution in progress."
            )

        # check if prev stage is completed successfully
        if not self.check_if_prev_stage_is_executed_successfully(
            last_ran_stage=data_pull_job_record.current_stage,
            prev_stage_job_config_record=prev_stage_config_record,
        ):
            raise Exception(
                f"cannot trigger {stage}: please configure '{prev_stage_config_record.stage}' stage"
            )

        return True

    def check_if_stage_triggered_with_same_inputs(
        self, new_inputs: Any, existing_job_config: FdDataPullJobConfig | None
    ):
        if existing_job_config.stage_config.status.status != DataPullStatus.SUCCESS:
            return False

        if new_inputs is None or existing_job_config is None:
            raise Exception(
                "Invalid values to check_if_stage_triggered_with_same_inputs"
            )

        if existing_job_config.stage_config.inputs:
            json_existing = existing_job_config.stage_config.inputs.model_dump()
        else:
            json_existing = {}

        json_new = new_inputs.model_dump()

        if self.is_inputs_changed(existing_inputs=json_existing, new_inputs=json_new):
            return False

        return True

    async def update_prev_stage_selected_values_with_current_stage_inputs(
        self,
        stage: FDDataPullStages,
        data_pull_job_record: FdDataPullConfig,
        prev_stage_config_record: FdDataPullJobConfig,
    ):
        prev_stage = STAGE_AND_STAGE_JOB_ID_KEY_DICT.get(stage)[2]

        prev_stage_job_config_id = getattr(
            data_pull_job_record,
            STAGE_AND_STAGE_JOB_ID_KEY_DICT.get(prev_stage)[0],
            None,
        )

        await self.fd_trace_job_dao.update_fd_data_pull_job_config_record_async(
            job_config_id=prev_stage_job_config_id,
            job_config_record=prev_stage_config_record,
        )

    async def get_facilities(self, inputs: FacilitesDataPullInput, job_config_id: str):
        current_timestamp = datetime.now(timezone.utc)

        job_config: FdDataPullJobConfig = (
            await self.fd_trace_job_dao.get_fd_data_pull_job_config_record_async(
                job_config_id=job_config_id
            )
        )

        if job_config.stage_config.stage != FDDataPullStages.FACILITIES:
            raise Exception("Invalid job config id given to get_facilities service")

        job_config.stage_config.status.status = DataPullStatus.SUCCESS
        job_config.stage_config.inputs = inputs
        job_config.stage_config.outputs = FacilitiesDataPullOutput.model_validate(
            {"facilities": {"file_path": DUMMY_FILES["facilities"]}}
        )
        job_config.stage_config.status.job_triggered_at = current_timestamp
        job_config.stage_config.status.job_completed_at = current_timestamp

        is_updated: bool = (
            await self.fd_trace_job_dao.update_fd_data_pull_job_config_record_async(
                job_config_id=job_config_id, job_config_record=job_config
            )
        )
        if not is_updated:
            raise Exception("Unable to update the facilities job config record")

    async def get_tech_nodes_async(
        self,
        inputs: TechNodesDataPullInput,
        job_config_id: str,
        job_config: FdDataPullJobConfig,
    ):
        if inputs.facilities.selected_values is None:
            raise ValueError("No facility selected")
        elif len(inputs.facilities.selected_values) > 1:
            raise Exception("Currently support only one Fab.")

        fab = inputs.facilities.selected_values[0]

        multi_sql_queries, status_code, error_message = self.get_tech_nodes(
            facility=fab
        )
        if status_code != 200:
            raise Exception(f"Failed to get_tech_nodes: {error_message}")

        # task id creation (for worker):
        task_id = str(uuid.uuid4())
        current_timestamp = datetime.now(timezone.utc)
        job_config.stage_config.status.status = DataPullStatus.CONFIGURED
        job_config.stage_config.inputs = inputs
        job_config.stage_config.outputs = {}
        job_config.stage_config.status.job_triggered_at = current_timestamp
        job_config.stage_config.status.job_completed_at = current_timestamp
        job_config.stage_config.status.job_config = BigqueryDataPullJobConfig(
            gcs_bucket_name=DATA_CATALOG_GCS_BUCKET,
            sql_query=multi_sql_queries,
            task_id=task_id,
            job_status=BigQueryDataPullJobStatus(),
            authentication=BigQueryAuthentication(
                auth_type=BigQueryAuthType.APPLICATION_DEFAULT_CREDENTIALS,
                auth_config=BigQueryAppDefaultCredFile(
                    project_id=GCP_PROJECT_ID,
                    application_credentials_file_path=DATA_CATALOG_APPLICATION_CREDENTIALS_FILE,
                ),
            ),
        ).model_dump()

        is_updated: bool = (
            await self.fd_trace_job_dao.update_fd_data_pull_job_config_record_async(
                job_config_id=job_config_id, job_config_record=job_config
            )
        )
        if not is_updated:
            raise Exception("Unable to update the Tech node job config record")

        return task_id

    async def get_desgin_ids(
        self,
        inputs: DesignIdDataPullInput,
        job_config_id: str,
        job_config: FdDataPullJobConfig,
    ):
        if inputs.facilities.selected_values is None:
            raise ValueError("No facility selected")
        if len(inputs.facilities.selected_values) > 1:
            raise Exception("Currently support only one Fab.")

        fab = inputs.facilities.selected_values[0]
        tech_nodes = inputs.tech_nodes.selected_values

        multi_sql_queries, status_code, error_message = (
            self.get_design_ids_with_technodes(facility=fab, technodes=tech_nodes)
        )
        if status_code != 200:
            raise Exception(f"Failed to get_design_ids_with_technodes: {error_message}")

        # task id creation (for worker):
        task_id = str(uuid.uuid4())
        current_timestamp = datetime.now(timezone.utc)
        job_config.stage_config.status.status = DataPullStatus.CONFIGURED
        job_config.stage_config.inputs = inputs
        job_config.stage_config.outputs = {}
        job_config.stage_config.status.job_triggered_at = current_timestamp
        job_config.stage_config.status.job_completed_at = None
        job_config.stage_config.status.job_config = BigqueryDataPullJobConfig(
            gcs_bucket_name=DATA_CATALOG_GCS_BUCKET,
            sql_query=multi_sql_queries,
            task_id=task_id,
            job_status=BigQueryDataPullJobStatus(),
            authentication=BigQueryAuthentication(
                auth_type=BigQueryAuthType.APPLICATION_DEFAULT_CREDENTIALS,
                auth_config=BigQueryAppDefaultCredFile(
                    project_id=GCP_PROJECT_ID,
                    application_credentials_file_path=DATA_CATALOG_APPLICATION_CREDENTIALS_FILE,
                ),
            ),
        ).model_dump()

        is_updated: bool = (
            await self.fd_trace_job_dao.update_fd_data_pull_job_config_record_async(
                job_config_id=job_config_id, job_config_record=job_config
            )
        )
        if not is_updated:
            raise Exception("Unable to update the design IDs job config record")

        return task_id

    async def get_traveler_ids_async(
        self,
        inputs: TravelersIdDataPullInput,
        job_config_id: str,
        job_config: FdDataPullJobConfig,
    ):
        if inputs.facilities.selected_values is None:
            raise ValueError("No facility selected")

        if len(inputs.facilities.selected_values) > 1:
            raise Exception("Currently support only one Fab.")

        fab = inputs.facilities.selected_values[0]
        design_ids = inputs.design_ids.selected_values

        multi_sql_queries, status_code, error_message = self.get_traveler_ids(
            facility=fab, design_ids=design_ids
        )
        if status_code != 200:
            raise Exception(f"Failed to get_traveler_ids: {error_message}")

        # task id creation (for worker):
        task_id = str(uuid.uuid4())
        current_timestamp = datetime.now(timezone.utc)
        job_config.stage_config.status.status = DataPullStatus.CONFIGURED
        job_config.stage_config.inputs = inputs
        job_config.stage_config.outputs = {}
        job_config.stage_config.status.job_triggered_at = current_timestamp
        job_config.stage_config.status.job_completed_at = None
        job_config.stage_config.status.job_config = BigqueryDataPullJobConfig(
            gcs_bucket_name=DATA_CATALOG_GCS_BUCKET,
            sql_query=multi_sql_queries,
            task_id=task_id,
            job_status=BigQueryDataPullJobStatus(),
            authentication=BigQueryAuthentication(
                auth_type=BigQueryAuthType.APPLICATION_DEFAULT_CREDENTIALS,
                auth_config=BigQueryAppDefaultCredFile(
                    project_id=GCP_PROJECT_ID,
                    application_credentials_file_path=DATA_CATALOG_APPLICATION_CREDENTIALS_FILE,
                ),
            ),
        ).model_dump()

        is_updated: bool = (
            await self.fd_trace_job_dao.update_fd_data_pull_job_config_record_async(
                job_config_id=job_config_id, job_config_record=job_config
            )
        )
        if not is_updated:
            raise Exception("Unable to update the Travelers Step job config record")

        return task_id

    async def get_travelers_steps_async(
        self,
        inputs: TravelerStepDataPullInput,
        job_config_id: str,
        job_config: FdDataPullJobConfig,
    ):
        if inputs.facilities.selected_values is None:
            raise ValueError("No facility selected")
        if len(inputs.facilities.selected_values) > 1:
            raise Exception("Currently support only one Fab.")

        fab = inputs.facilities.selected_values[0]
        design_ids = inputs.design_ids.selected_values
        traveler_ids = inputs.traveler_ids.selected_values

        multi_sql_queries, status_code, error_message = self.get_traveler_steps_by_ids(
            facility=fab, design_ids=design_ids, traveler_ids=traveler_ids
        )
        if status_code != 200:
            raise Exception(f"Failed to get_traveler_steps_by_ids: {error_message}")

        # task id creation (for worker):
        task_id = str(uuid.uuid4())
        current_timestamp = datetime.now(timezone.utc)
        job_config.stage_config.status.status = DataPullStatus.CONFIGURED
        job_config.stage_config.inputs = inputs
        job_config.stage_config.outputs = {}
        job_config.stage_config.status.job_triggered_at = current_timestamp
        job_config.stage_config.status.job_completed_at = None
        job_config.stage_config.status.job_config = BigqueryDataPullJobConfig(
            gcs_bucket_name=DATA_CATALOG_GCS_BUCKET,
            sql_query=multi_sql_queries,
            task_id=task_id,
            job_status=BigQueryDataPullJobStatus(),
            authentication=BigQueryAuthentication(
                auth_type=BigQueryAuthType.APPLICATION_DEFAULT_CREDENTIALS,
                auth_config=BigQueryAppDefaultCredFile(
                    project_id=GCP_PROJECT_ID,
                    application_credentials_file_path=DATA_CATALOG_APPLICATION_CREDENTIALS_FILE,
                ),
            ),
        ).model_dump()

        is_updated: bool = (
            await self.fd_trace_job_dao.update_fd_data_pull_job_config_record_async(
                job_config_id=job_config_id, job_config_record=job_config
            )
        )
        if not is_updated:
            raise Exception("Unable to update the Travelers Step job config record")

        return task_id

    async def get_probe_context_async(
        self,
        inputs: ProbeContextDataPullInput,
        job_config_id: str,
        job_config: FdDataPullJobConfig,
    ):
        if inputs.facilities.selected_values is None:
            raise ValueError("No facility selected")
        if len(inputs.facilities.selected_values) > 1:
            raise Exception("Currently support only one Fab.")

        if len(inputs.design_ids.selected_values) > 1:
            raise Exception("Currently support only one Design.")

        fab = inputs.facilities.selected_values[0]
        design_id = inputs.design_ids.selected_values[0]

        multi_sql_queries, status_code, error_message = (
            self.get_probe_context_by_design(facility=fab, design_id=design_id)
        )
        if status_code != 200:
            raise Exception(f"Failed to get_traveler_steps_by_ids: {error_message}")

        # task id creation (for worker):
        task_id = str(uuid.uuid4())
        current_timestamp = datetime.now(timezone.utc)
        job_config.stage_config.status.status = DataPullStatus.CONFIGURED
        job_config.stage_config.inputs = inputs
        job_config.stage_config.outputs = {}
        job_config.stage_config.status.job_triggered_at = current_timestamp
        job_config.stage_config.status.job_completed_at = None
        job_config.stage_config.status.job_config = BigqueryDataPullJobConfig(
            gcs_bucket_name=DATA_CATALOG_GCS_BUCKET,
            sql_query=multi_sql_queries,
            task_id=task_id,
            job_status=BigQueryDataPullJobStatus(),
            authentication=BigQueryAuthentication(
                auth_type=BigQueryAuthType.APPLICATION_DEFAULT_CREDENTIALS,
                auth_config=BigQueryAppDefaultCredFile(
                    project_id=GCP_PROJECT_ID,
                    application_credentials_file_path=DATA_CATALOG_APPLICATION_CREDENTIALS_FILE,
                ),
            ),
        ).model_dump()

        is_updated: bool = (
            await self.fd_trace_job_dao.update_fd_data_pull_job_config_record_async(
                job_config_id=job_config_id, job_config_record=job_config
            )
        )
        if not is_updated:
            raise Exception("Unable to update the Probe Context job config record")

        return task_id

    async def get_probe_data_pull_async(
        self,
        inputs: ProbeDataPullInputs,
        job_config_id: str,
        job_config: FdDataPullJobConfig,
    ):
        if inputs.facilities.selected_values is None:
            raise ValueError("No facility selected")
        if len(inputs.facilities.selected_values) > 1:
            raise Exception("Currently support only one Fab.")

        if len(inputs.design_ids.selected_values) > 1:
            raise Exception("Currently support only one Design.")

        fab = inputs.facilities.selected_values[0]
        design_id = inputs.design_ids.selected_values[0]

        if (
            len(inputs.paretoname.selected_values) == 0
            and len(inputs.paretotitle.selected_values) == 0
        ) and (inputs.uploaded_probe_data is None):
            raise Exception(
                "Need to select atleast one pareto name or pareto title or file upload"
            )

        multi_sql_queries, status_code, error_message = [], 200, ""
        if status_code != 200:
            raise Exception(f"Failed to get_traveler_steps_by_ids: {error_message}")

        # task id creation (for worker):
        task_id = str(uuid.uuid4())
        current_timestamp = datetime.now(timezone.utc)
        job_config.stage_config.status.status = DataPullStatus.CONFIGURED
        job_config.stage_config.inputs = inputs
        job_config.stage_config.outputs = {}
        job_config.stage_config.status.job_triggered_at = current_timestamp
        job_config.stage_config.status.job_completed_at = None
        job_config.stage_config.status.job_config = BigqueryDataPullJobConfig(
            gcs_bucket_name=DATA_CATALOG_GCS_BUCKET,
            sql_query=multi_sql_queries,
            task_id=task_id,
            job_status=BigQueryDataPullJobStatus(),
            authentication=BigQueryAuthentication(
                auth_type=BigQueryAuthType.APPLICATION_DEFAULT_CREDENTIALS,
                auth_config=BigQueryAppDefaultCredFile(
                    project_id=GCP_PROJECT_ID,
                    application_credentials_file_path=DATA_CATALOG_APPLICATION_CREDENTIALS_FILE,
                ),
            ),
        ).model_dump()

        is_updated: bool = (
            await self.fd_trace_job_dao.update_fd_data_pull_job_config_record_async(
                job_config_id=job_config_id, job_config_record=job_config
            )
        )
        if not is_updated:
            raise Exception("Unable to update the Probe Context job config record")

        return task_id

    async def get_fd_context_async(
        self,
        inputs: FdContextDataPullInput,
        job_config_id: str,
        job_config: FdDataPullJobConfig,
    ):
        if inputs.facilities.selected_values is None:
            raise ValueError("No facility selected")
        if len(inputs.facilities.selected_values) > 1:
            raise Exception("Currently support only one Fab.")

        fab = inputs.facilities.selected_values[0]
        design_ids = inputs.design_ids.selected_values
        traveler_steps = inputs.traveler_steps.selected_values
        start_date = inputs.start_date
        end_date = inputs.end_date

        sql, status_code, error_message = self.get_fd_context(
            facility=fab,
            start_date=start_date,
            end_date=end_date,
            design_ids=design_ids,
            traveler_steps=traveler_steps,
        )
        if status_code != 200:
            raise Exception(f"Failed to get_fd_context: {error_message}")

        if job_config.stage_config.status.status == DataPullStatus.SUCCESS:
            pass  # TODO: REMOVE OLD RUN RESULTS FOR THIS STAGE AND ALSO RESET THE MONGO RECORD

        # task id creation (for worker):
        task_id = str(uuid.uuid4())
        current_timestamp = datetime.now(timezone.utc)
        job_config.stage_config.status.status = DataPullStatus.CONFIGURED
        job_config.stage_config.inputs = inputs
        job_config.stage_config.outputs = {}
        job_config.stage_config.status.job_triggered_at = current_timestamp
        job_config.stage_config.status.job_completed_at = None
        job_config.stage_config.status.job_config = BigqueryDataPullJobConfig(
            gcs_bucket_name=DATA_CATALOG_GCS_BUCKET,
            sql_query=sql,
            task_id=task_id,
            job_status=BigQueryDataPullJobStatus(),
            authentication=BigQueryAuthentication(
                auth_type=BigQueryAuthType.APPLICATION_DEFAULT_CREDENTIALS,
                auth_config=BigQueryAppDefaultCredFile(
                    project_id=GCP_PROJECT_ID,
                    application_credentials_file_path=DATA_CATALOG_APPLICATION_CREDENTIALS_FILE,
                ),
            ),
        ).model_dump()

        is_updated: bool = (
            await self.fd_trace_job_dao.update_fd_data_pull_job_config_record_async(
                job_config_id=job_config_id, job_config_record=job_config
            )
        )
        if not is_updated:
            raise Exception("Unable to update the FD Context job config record")

        return task_id

    async def get_fd_sensors_async(
        self,
        inputs: SensorsDataPullInput,
        job_config_id: str,
        job_config: FdDataPullJobConfig,
    ):
        sql, status_code, error_message = self.get_fd_sensors(
            path=inputs.fd_contexts.file_path,
            selections=inputs.fd_contexts.selected_values,
        )  # path=DUMMY_FD_CATALOG_FILE_PATH, selections=[0,1,2])
        if status_code != 200:
            raise Exception(f"Failed to get_fd_sensors: {error_message}")

        if job_config.stage_config.status.status == DataPullStatus.SUCCESS:
            pass  # TODO: REMOVE OLD RUN RESULTS FOR THIS STAGE AND ALSO RESET THE MONGO RECORD

        # task id creation (for worker):
        task_id = str(uuid.uuid4())
        current_timestamp = datetime.now(timezone.utc)
        job_config.stage_config.status.status = DataPullStatus.CONFIGURED
        job_config.stage_config.inputs = inputs
        job_config.stage_config.outputs = {}
        job_config.stage_config.status.job_triggered_at = current_timestamp
        job_config.stage_config.status.job_completed_at = None
        job_config.stage_config.status.job_config = BigqueryDataPullJobConfig(
            gcs_bucket_name=DATA_CATALOG_GCS_BUCKET,
            sql_query=sql,
            task_id=task_id,
            job_status=BigQueryDataPullJobStatus(),
            authentication=BigQueryAuthentication(
                auth_type=BigQueryAuthType.APPLICATION_DEFAULT_CREDENTIALS,
                auth_config=BigQueryAppDefaultCredFile(
                    project_id=GCP_PROJECT_ID,
                    application_credentials_file_path=DATA_CATALOG_APPLICATION_CREDENTIALS_FILE,
                ),
            ),
        ).model_dump()

        is_updated: bool = (
            await self.fd_trace_job_dao.update_fd_data_pull_job_config_record_async(
                job_config_id=job_config_id, job_config_record=job_config
            )
        )
        if not is_updated:
            raise Exception("Unable to update the FD Sensor job config record")

        return task_id

    async def get_fd_trace_async(
        self,
        inputs: FdTraceDataPullInput,
        job_config_id: str,
        job_config: FdDataPullJobConfig,
    ):
        # df = pd.read_parquet(inputs.fd_context_file_path).loc[inputs.selected_row_indices].astype(str)
        # inputs.selected_row_indices = [0,1,2]

        # df = pd.read_parquet(DUMMY_FD_CATALOG_FILE_PATH).loc[[0,1,2]].astype(str)
        df = (
            pd.read_parquet(inputs.fd_contexts.file_path)
            .loc[inputs.fd_contexts.selected_values]
            .astype(str)
        )

        multi_sql_queries_with_result_file_names, status_code, error_message = (
            self.get_fd_trace(
                data=df.to_dict(orient="records"),
                sensors=inputs.sensors.selected_values,
                datadir="/tmp/fd",
            )
        )
        if status_code != 200:
            raise Exception(f"Failed to get_fd_trace: {error_message}")

        if job_config.stage_config.status.status == DataPullStatus.SUCCESS:
            pass  # TODO: REMOVE OLD RUN RESULTS FOR THIS STAGE AND ALSO RESET THE MONGO RECORD

        # task id creation (for worker):
        task_id = str(uuid.uuid4())
        current_timestamp = datetime.now(timezone.utc)
        job_config.stage_config.status.status = DataPullStatus.CONFIGURED
        job_config.stage_config.inputs = inputs
        job_config.stage_config.outputs = {}
        job_config.stage_config.status.job_triggered_at = current_timestamp
        job_config.stage_config.status.job_completed_at = None
        job_config.stage_config.status.job_config = BigqueryDataPullJobConfig(
            gcs_bucket_name=DATA_CATALOG_GCS_BUCKET,
            sql_query=multi_sql_queries_with_result_file_names,
            task_id=task_id,
            job_status=BigQueryDataPullJobStatus(),
            authentication=BigQueryAuthentication(
                auth_type=BigQueryAuthType.APPLICATION_DEFAULT_CREDENTIALS,
                auth_config=BigQueryAppDefaultCredFile(
                    project_id=GCP_PROJECT_ID,
                    application_credentials_file_path=DATA_CATALOG_APPLICATION_CREDENTIALS_FILE,
                ),
            ),
        ).model_dump()

        is_updated: bool = (
            await self.fd_trace_job_dao.update_fd_data_pull_job_config_record_async(
                job_config_id=job_config_id, job_config_record=job_config
            )
        )
        if not is_updated:
            raise Exception("Unable to update the FD Trace job config record")

        return task_id

    async def get_lot_ids_async(
        self,
        inputs: LotIdsDataPullInput,
        job_config_id: str,
        job_config: FdDataPullJobConfig,
    ):
        if inputs.facilities.selected_values is None:
            raise ValueError("No facility selected")

        elif len(inputs.facilities.selected_values) > 1:
            raise Exception("Currently support only one Fab.")

        if (
            inputs.traveler_ids is not None
            and len(inputs.traveler_ids.selected_values) < 1
        ):
            raise Exception("Please select the traveler ids")

        if (
            inputs.traveler_steps is not None
            and len(inputs.traveler_steps.selected_values) < 1
        ):
            raise Exception("Please select the traveler steps")

        if inputs.start_date is None or inputs.end_date is None:
            raise Exception("Please select the start date and end date")

        fab = inputs.facilities.selected_values[0]

        multi_sql_queries, status_code, error_message = self.get_lot_ids(
            facility=fab,
            traveler_ids=inputs.traveler_ids.selected_values,
            selected_steps=inputs.traveler_steps.selected_values,
            start_date=inputs.start_date,
            end_date=inputs.end_date,
        )
        if status_code != 200:
            raise Exception(f"Failed to get_tech_nodes: {error_message}")

        # task id creation (for worker):
        task_id = str(uuid.uuid4())
        current_timestamp = datetime.now(timezone.utc)
        job_config.stage_config.status.status = DataPullStatus.CONFIGURED
        job_config.stage_config.inputs = inputs
        job_config.stage_config.outputs = {}
        job_config.stage_config.status.job_triggered_at = current_timestamp
        job_config.stage_config.status.job_completed_at = current_timestamp
        job_config.stage_config.status.job_config = BigqueryDataPullJobConfig(
            gcs_bucket_name=DATA_CATALOG_GCS_BUCKET,
            sql_query=multi_sql_queries,
            task_id=task_id,
            job_status=BigQueryDataPullJobStatus(),
            authentication=BigQueryAuthentication(
                auth_type=BigQueryAuthType.APPLICATION_DEFAULT_CREDENTIALS,
                auth_config=BigQueryAppDefaultCredFile(
                    project_id=GCP_PROJECT_ID,
                    application_credentials_file_path=DATA_CATALOG_APPLICATION_CREDENTIALS_FILE,
                ),
            ),
        ).model_dump()

        is_updated: bool = (
            await self.fd_trace_job_dao.update_fd_data_pull_job_config_record_async(
                job_config_id=job_config_id, job_config_record=job_config
            )
        )
        if not is_updated:
            raise Exception("Unable to update the Lotid node job config record")

        return task_id

    async def get_aggregated_results_async(
        self,
        inputs: UC3FDContextApplyFiltersInput,
        job_config_id: str,
        job_config: FdDataPullJobConfig,
    ):
        task_id = str(uuid.uuid4())
        current_timestamp = datetime.now(timezone.utc)
        job_config.stage_config.status.status = DataPullStatus.CONFIGURED
        job_config.stage_config.inputs = inputs
        job_config.stage_config.outputs = {}
        job_config.stage_config.status.job_triggered_at = current_timestamp
        job_config.stage_config.status.job_completed_at = current_timestamp
        job_config_dict = inputs.model_dump(include=("filters"))
        job_config_dict["task_id"] = task_id
        job_config.stage_config.status.job_config = job_config_dict

        is_updated: bool = (
            await self.fd_trace_job_dao.update_fd_data_pull_job_config_record_async(
                job_config_id=job_config_id, job_config_record=job_config
            )
        )
        if not is_updated:
            raise Exception("Unable to update the filtered files in job config record")

        return task_id

    async def update_fd_data_pull_job_details_async(
        self, inputs, job_config_id: str, job_config: FdDataPullJobConfig
    ):
        task_id = str(uuid.uuid4())
        current_timestamp = datetime.now(timezone.utc)
        job_config.stage_config.status.status = DataPullStatus.SUCCESS
        job_config.stage_config.inputs = inputs
        job_config.stage_config.outputs = {}
        job_config.stage_config.status.job_triggered_at = current_timestamp
        job_config.stage_config.status.job_completed_at = current_timestamp
        job_config_dict = inputs.model_dump()
        job_config_dict["task_id"] = task_id
        job_config.stage_config.status.job_config = job_config_dict

        is_updated: bool = (
            await self.fd_trace_job_dao.update_fd_data_pull_job_config_record_async(
                job_config_id=job_config_id, job_config_record=job_config
            )
        )
        if not is_updated:
            raise Exception("Unable to update the details in job config record")

        return task_id

    async def get_wafer_ids_async(
        self,
        inputs: WaferIdsDataPullInput,
        job_config_id: str,
        job_config: FdDataPullJobConfig,
    ):
        if inputs.facilities.selected_values is None:
            raise ValueError("No facility selected")

        elif len(inputs.facilities.selected_values) > 1:
            raise Exception("Currently support only one Fab.")

        if (
            inputs.traveler_ids is not None
            and len(inputs.traveler_ids.selected_values) < 1
        ):
            raise Exception("Please select the traveler ids")

        if (
            inputs.traveler_steps is not None
            and len(inputs.traveler_steps.selected_values) < 1
        ):
            raise Exception("Please select the traveler steps")

        if inputs.start_date is None or inputs.end_date is None:
            raise Exception("Please select the start date and end date")

        if inputs.lot_ids is None:
            raise ValueError("No lot is selected")

        fab = inputs.facilities.selected_values[0]

        multi_sql_queries, status_code, error_message = self.get_wafer_ids(
            facility=fab,
            traveler_ids=inputs.traveler_ids.selected_values,
            selected_steps=inputs.traveler_steps.selected_values,
            start_date=inputs.start_date,
            end_date=inputs.end_date,
            lot_ids=inputs.lot_ids.selected_values,
        )
        if status_code != 200:
            raise Exception(f"Failed to get_tech_nodes: {error_message}")

        # task id creation (for worker):
        task_id = str(uuid.uuid4())
        current_timestamp = datetime.now(timezone.utc)
        job_config.stage_config.status.status = DataPullStatus.CONFIGURED
        job_config.stage_config.inputs = inputs
        job_config.stage_config.outputs = {}
        job_config.stage_config.status.job_triggered_at = current_timestamp
        job_config.stage_config.status.job_completed_at = current_timestamp
        job_config.stage_config.status.job_config = BigqueryDataPullJobConfig(
            gcs_bucket_name=DATA_CATALOG_GCS_BUCKET,
            sql_query=multi_sql_queries,
            task_id=task_id,
            job_status=BigQueryDataPullJobStatus(),
            authentication=BigQueryAuthentication(
                auth_type=BigQueryAuthType.APPLICATION_DEFAULT_CREDENTIALS,
                auth_config=BigQueryAppDefaultCredFile(
                    project_id=GCP_PROJECT_ID,
                    application_credentials_file_path=DATA_CATALOG_APPLICATION_CREDENTIALS_FILE,
                ),
            ),
        ).model_dump()

        is_updated: bool = (
            await self.fd_trace_job_dao.update_fd_data_pull_job_config_record_async(
                job_config_id=job_config_id, job_config_record=job_config
            )
        )
        if not is_updated:
            raise Exception("Unable to update the Lotid node job config record")

        return task_id

    async def get_final_data_aggregate_async(
        self,
        inputs: FinalDataAggregateInput,
        job_config_id: str,
        job_config: FdDataPullJobConfig,
    ) -> str:
        multi_sql_queries, status_code, error_message = [], 200, None

        if status_code != 200:
            raise Exception(f"Failed to generate final data aggregate: {error_message}")

        # task id creation (for worker):
        task_id = str(uuid.uuid4())

        if (stage_config := job_config.stage_config) is None:
            raise ValueError("job config is not initailized")
        if not isinstance(stage_config, FinalDataAggregateConfig):
            raise TypeError("job config is initialized with wrong config")
        stage_config.status.status = DataPullStatus.CONFIGURED
        stage_config.inputs = inputs
        stage_config.outputs = None
        stage_config.status.job_triggered_at = datetime.now(timezone.utc)
        stage_config.status.job_completed_at = None
        stage_config.status.job_config = BigqueryDataPullJobConfig(
            gcs_bucket_name=DATA_CATALOG_GCS_BUCKET,
            sql_query=multi_sql_queries,
            task_id=task_id,
            job_status=BigQueryDataPullJobStatus(),
            authentication=BigQueryAuthentication(
                auth_type=BigQueryAuthType.APPLICATION_DEFAULT_CREDENTIALS,
                auth_config=BigQueryAppDefaultCredFile(
                    project_id=GCP_PROJECT_ID,
                    application_credentials_file_path=DATA_CATALOG_APPLICATION_CREDENTIALS_FILE,
                ),
            ),
        ).model_dump()

        if not await self.fd_trace_job_dao.update_fd_data_pull_job_config_record_async(
            job_config_id=job_config_id, job_config_record=job_config
        ):
            raise Exception(
                "unable to update the final data aggregate job config record"
            )

        return task_id

    async def get_uc2_sigma_data_task_id_async(
        self,
        inputs: UC2SigmaDataPullInput,
        job_config_id: str,
        job_config: FdDataPullJobConfig,
    ) -> str:
        if inputs.facilities is None or not inputs.facilities.selected_values:
            raise ValueError(f"no facility is selected")
        if len(inputs.facilities.selected_values) > 1:
            raise ValueError("currently only one facility is supported")
        facility = inputs.facilities.selected_values[0]

        start_date = inputs.start_date
        end_date = inputs.end_date

        multi_sql_queries, status_code, error_message = self.get_uc2_sigma_data_pull(
            facility=facility,
            traveler_ids=[],
            traveler_steps=[],
            tools=[],
            step_ids=[],
            sensors=[],
            start_date=start_date,
            end_date=end_date,
        )

        if status_code != 200:
            raise Exception(f"Failed to generate uc2 data pull data: {error_message}")

        # task id creation (for worker):
        task_id = str(uuid.uuid4())

        if (stage_config := job_config.stage_config) is None:
            raise ValueError("job config is not initailized")
        if not isinstance(stage_config, UC2SigmaDataPullConfig):
            raise TypeError("job config is initialized with wrong config")
        stage_config.status.status = DataPullStatus.CONFIGURED
        stage_config.inputs = inputs
        stage_config.outputs = None
        stage_config.status.job_triggered_at = datetime.now(timezone.utc)
        stage_config.status.job_completed_at = None
        stage_config.status.job_config = BigqueryDataPullJobConfig(
            gcs_bucket_name=DATA_CATALOG_GCS_BUCKET,
            sql_query=multi_sql_queries,
            task_id=task_id,
            job_status=BigQueryDataPullJobStatus(),
            authentication=BigQueryAuthentication(
                auth_type=BigQueryAuthType.APPLICATION_DEFAULT_CREDENTIALS,
                auth_config=BigQueryAppDefaultCredFile(
                    project_id=GCP_PROJECT_ID,
                    application_credentials_file_path=DATA_CATALOG_APPLICATION_CREDENTIALS_FILE,
                ),
            ),
        ).model_dump()

        if not await self.fd_trace_job_dao.update_fd_data_pull_job_config_record_async(
            job_config_id=job_config_id, job_config_record=job_config
        ):
            raise Exception("unable to update the uc2 sigma data pull stage record")

        return task_id

    # TODO: both get_uc3_sigma_data_task_id_async and get_uc2_sigma_data_task_id_async have almost same logic
    async def get_uc3_sigma_data_task_id_async(
        self, inputs: UC3SigmaInput, job_config_id: str, job_config: FdDataPullJobConfig
    ) -> str:
        if inputs.facilities is None or not inputs.facilities.selected_values:
            raise ValueError(f"no facility is selected")
        if len(inputs.facilities.selected_values) > 1:
            raise ValueError("currently only one facility is supported")
        facility = inputs.facilities.selected_values[0]

        start_date = inputs.start_date
        end_date = inputs.end_date

        multi_sql_queries, status_code, error_message = self.get_uc2_sigma_data_pull(
            facility=facility,
            traveler_ids=[],
            traveler_steps=[],
            tools=[],
            step_ids=[],
            sensors=[],
            start_date=start_date,
            end_date=end_date,
        )

        if status_code != 200:
            raise Exception(f"Failed to generate uc3 data pull data: {error_message}")

        # task id creation (for worker):
        task_id = str(uuid.uuid4())

        if (stage_config := job_config.stage_config) is None:
            raise ValueError("job config is not initailized")
        if not isinstance(stage_config, UC3SigmaDataPullConfig):
            raise TypeError("job config is initialized with wrong config")
        stage_config.status.status = DataPullStatus.CONFIGURED
        stage_config.inputs = inputs
        stage_config.outputs = None
        stage_config.status.job_triggered_at = datetime.now(timezone.utc)
        stage_config.status.job_completed_at = None
        stage_config.status.job_config = BigqueryDataPullJobConfig(
            gcs_bucket_name=DATA_CATALOG_GCS_BUCKET,
            sql_query=multi_sql_queries,
            task_id=task_id,
            job_status=BigQueryDataPullJobStatus(),
            authentication=BigQueryAuthentication(
                auth_type=BigQueryAuthType.APPLICATION_DEFAULT_CREDENTIALS,
                auth_config=BigQueryAppDefaultCredFile(
                    project_id=GCP_PROJECT_ID,
                    application_credentials_file_path=DATA_CATALOG_APPLICATION_CREDENTIALS_FILE,
                ),
            ),
        ).model_dump()

        if not await self.fd_trace_job_dao.update_fd_data_pull_job_config_record_async(
            job_config_id=job_config_id, job_config_record=job_config
        ):
            raise Exception("unable to update the uc3 sigma data pull stage record")

        return task_id

    async def initialize_fd_data_pull(self, session_id: str) -> str:
        # creating sub-jobs for fd data pull

        job_ids = dict()

        job_ids["facilities_job_id"] = await self.fd_trace_job_dao.create_fd_stage_job(
            fd_data_pull_job=FdDataPullJobConfig(
                session_id=session_id,
                stage=FDDataPullStages.FACILITIES,
                stage_config=FacilitesDataPullConfig(),
            )
        )

        job_ids["tech_nodes_job_id"] = await self.fd_trace_job_dao.create_fd_stage_job(
            fd_data_pull_job=FdDataPullJobConfig(
                session_id=session_id,
                stage=FDDataPullStages.TECH_NODE,
                stage_config=TechNodeDataPullConfig(),
            )
        )

        job_ids["designs_job_id"] = await self.fd_trace_job_dao.create_fd_stage_job(
            fd_data_pull_job=FdDataPullJobConfig(
                session_id=session_id,
                stage=FDDataPullStages.DESIGN_ID,
                stage_config=DesignIdDataPullConfig(),
            )
        )

        job_ids[
            "traveler_ids_job_id"
        ] = await self.fd_trace_job_dao.create_fd_stage_job(
            fd_data_pull_job=FdDataPullJobConfig(
                session_id=session_id,
                stage=FDDataPullStages.TRAVELER_ID,
                stage_config=TravelersIdDataPullConfig(),
            )
        )

        job_ids[
            "traveler_step_job_id"
        ] = await self.fd_trace_job_dao.create_fd_stage_job(
            fd_data_pull_job=FdDataPullJobConfig(
                session_id=session_id,
                stage=FDDataPullStages.TRAVELER_STEP,
                stage_config=TravelerStepDataPullConfig(),
            )
        )

        job_ids[
            "fd_context_step_job_id"
        ] = await self.fd_trace_job_dao.create_fd_stage_job(
            fd_data_pull_job=FdDataPullJobConfig(
                session_id=session_id,
                stage=FDDataPullStages.FD_CONTEXT,
                stage_config=FdContextDataPullConfig(),
            )
        )

        job_ids["sensors_job_id"] = await self.fd_trace_job_dao.create_fd_stage_job(
            fd_data_pull_job=FdDataPullJobConfig(
                session_id=session_id,
                stage=FDDataPullStages.FD_SENSOR,
                stage_config=SensorsDataPullConfig(),
            )
        )

        job_ids["fd_trace_job_id"] = await self.fd_trace_job_dao.create_fd_stage_job(
            fd_data_pull_job=FdDataPullJobConfig(
                session_id=session_id,
                stage=FDDataPullStages.FD_TRACE,
                stage_config=FdTraceDataPullConfig(),
            )
        )

        job_ids[
            "save_high_level_dc_details_job_id"
        ] = await self.fd_trace_job_dao.create_fd_stage_job(
            fd_data_pull_job=FdDataPullJobConfig(
                session_id=session_id,
                stage=FDDataPullStages.SAVE_HIGH_LEVEL_DC_DETAILS,
                stage_config=SaveHLDCConfig(),
            )
        )

        job_ids["lot_ids_job_id"] = await self.fd_trace_job_dao.create_fd_stage_job(
            fd_data_pull_job=FdDataPullJobConfig(
                session_id=session_id,
                stage=FDDataPullStages.LOT_ID,
                stage_config=LotIdsDataPullConfig(),
            )
        )

        job_ids["wafer_ids_job_id"] = await self.fd_trace_job_dao.create_fd_stage_job(
            fd_data_pull_job=FdDataPullJobConfig(
                session_id=session_id,
                stage=FDDataPullStages.WAFER_ID,
                stage_config=WaferIdsDataPullConfig(),
            )
        )
        job_ids[
            "lot_wafer_ids_job_id"
        ] = await self.fd_trace_job_dao.create_fd_stage_job(
            fd_data_pull_job=FdDataPullJobConfig(
                session_id=session_id,
                stage=FDDataPullStages.LOT_WAFER_SAVE,
                stage_config=LotWaferConfig(),
            )
        )

        job_ids[
            "final_data_aggregate_stage_job_id"
        ] = await self.fd_trace_job_dao.create_fd_stage_job(
            fd_data_pull_job=FdDataPullJobConfig(
                session_id=session_id,
                stage=FDDataPullStages.FINAL_DATA_AGGREGATE,
                stage_config=FinalDataAggregateConfig(),
            )
        )

        job_ids[
            "uc2_sigma_data_job_id"
        ] = await self.fd_trace_job_dao.create_fd_stage_job(
            fd_data_pull_job=FdDataPullJobConfig(
                session_id=session_id,
                stage=FDDataPullStages.UC2_SIGMA_DATA,
                stage_config=UC2SigmaDataPullConfig(),
            )
        )

        job_ids[
            "uc3_fd_context_apply_filters_job_id"
        ] = await self.fd_trace_job_dao.create_fd_stage_job(
            fd_data_pull_job=FdDataPullJobConfig(
                session_id=session_id,
                stage=FDDataPullStages.UC3_FD_CONTEXT_APPLY_FILTERS,
                stage_config=UC3FDContextApplyFiltersDataPullConfig(),
            )
        )

        job_ids[
            "probe_context_job_id"
        ] = await self.fd_trace_job_dao.create_fd_stage_job(
            fd_data_pull_job=FdDataPullJobConfig(
                session_id=session_id,
                stage=FDDataPullStages.PROBE_CONTEXT,
                stage_config=ProbeContextDataPullConfig(),
            )
        )

        job_ids[
            "probe_data_pull_job_id"
        ] = await self.fd_trace_job_dao.create_fd_stage_job(
            fd_data_pull_job=FdDataPullJobConfig(
                session_id=session_id,
                stage=FDDataPullStages.PROBE_DATA_PULL,
                stage_config=ProbeDataPullConfig(),
            )
        )

        job_ids[
            "uc3_sigma_data_job_id"
        ] = await self.fd_trace_job_dao.create_fd_stage_job(
            fd_data_pull_job=FdDataPullJobConfig(
                session_id=session_id,
                stage=FDDataPullStages.UC3_SIGMA_DATA,
                stage_config=UC3SigmaDataPullConfig(),
            )
        )

        fd_data_pull_job_id = (
            await self.fd_trace_job_dao.create_fd_data_pull_job_record_async(
                job_record=FdDataPullConfig(
                    session_id=session_id,
                    facility_stage_job_id=job_ids["facilities_job_id"],
                    tech_node_stage_job_id=job_ids["tech_nodes_job_id"],
                    design_ids_stage_job_id=job_ids["designs_job_id"],
                    traveler_id_step_stage_job_id=job_ids["traveler_ids_job_id"],
                    traveler_step_stage_job_id=job_ids["traveler_step_job_id"],
                    save_high_level_dc_details_job_id=job_ids[
                        "save_high_level_dc_details_job_id"
                    ],
                    fd_context_stage_job_id=job_ids["fd_context_step_job_id"],
                    sensors_stage_job_id=job_ids["sensors_job_id"],
                    fd_trace_stage_job_id=job_ids["fd_trace_job_id"],
                    lot_ids_stage_job_id=job_ids["lot_ids_job_id"],
                    wafer_ids_stage_job_id=job_ids["wafer_ids_job_id"],
                    lot_wafer_stage_job_id=job_ids["lot_wafer_ids_job_id"],
                    uc2_sigma_job_id=job_ids["uc2_sigma_data_job_id"],
                    final_data_aggregate_stage_job_id=job_ids[
                        "final_data_aggregate_stage_job_id"
                    ],
                    uc3_fd_context_apply_filters_job_id=job_ids[
                        "uc3_fd_context_apply_filters_job_id"
                    ],
                    uc3_sigma_job_id=job_ids["uc3_sigma_data_job_id"],
                    probe_context_job_id=job_ids["probe_context_job_id"],
                    probe_data_pull_job_id=job_ids["probe_data_pull_job_id"],
                )
            )
        )

        return fd_data_pull_job_id

    async def stop_stage(self, data_pull_job_id: str):
        fd_data_pull_job_record: FdDataPullConfig = (
            await self.fd_trace_job_dao.get_fd_data_pull_job_record_async(
                job_id=data_pull_job_id
            )
        )

        if fd_data_pull_job_record.data_pull_status != DataCatalogStatus.RUNNING:
            return

        if fd_data_pull_job_record.current_stage != FDDataPullStages.IDLE:
            current_stage_job_id_key = STAGE_AND_STAGE_JOB_ID_KEY_DICT.get(
                fd_data_pull_job_record.current_stage
            )[0]
            job_config_id = getattr(
                fd_data_pull_job_record, current_stage_job_id_key, None
            )
            fd_job_config: FdDataPullJobConfig = (
                await self.get_fd_data_pull_job_config_record_async(
                    job_config_id=job_config_id
                )
            )

            if fd_job_config.stage_config.status.status in [
                DataPullStatus.RUNNING,
                DataPullStatus.CONFIGURED,
            ]:
                current_timestamp = datetime.now(timezone.utc)
                fd_job_config.stage_config.status.status = DataPullStatus.FAILED
                fd_job_config.stage_config.outputs = {"error": "stopped"}
                fd_job_config.stage_config.status.job_completed_at = current_timestamp

            await self.fd_trace_job_dao.update_fd_data_pull_job_config_record_async(
                job_config_id=job_config_id, job_config_record=fd_job_config
            )

        if fd_data_pull_job_record.data_pull_status == DataCatalogStatus.RUNNING:
            await self.update_fd_data_pull_job_record_current_stage_async(
                job_id=data_pull_job_id,
                current_stage=fd_data_pull_job_record.current_stage,
                current_stage_status=DataCatalogStatus.IDLE,
            )

    async def fd_trace_pull_full_status_async(
        self, data_pull_job_id: str
    ) -> List[FdTracePullFullStatusResponse]:
        fd_data_pull_job_record: FdDataPullConfig = (
            await self.fd_trace_job_dao.get_fd_data_pull_job_record_async(
                job_id=data_pull_job_id
            )
        )

        job_config_ids = [
            fd_data_pull_job_record.facility_stage_job_id,
            fd_data_pull_job_record.tech_node_stage_job_id,
            fd_data_pull_job_record.design_ids_stage_job_id,
            fd_data_pull_job_record.traveler_step_stage_job_id,
            fd_data_pull_job_record.fd_context_stage_job_id,
            fd_data_pull_job_record.sensors_stage_job_id,
            fd_data_pull_job_record.fd_trace_stage_job_id,
            fd_data_pull_job_record.lot_ids_stage_job_id,
            fd_data_pull_job_record.wafer_ids_stage_job_id,
        ]

        full_status = await self.fd_trace_job_dao.get_multiple_fd_data_pull_job_config_records_async(
            job_config_ids=job_config_ids
        )

        return full_status

    async def get_fd_data_pull_job_record_async(self, job_id: str) -> FdDataPullConfig:
        job_record: FdDataPullConfig = (
            await self.fd_trace_job_dao.get_fd_data_pull_job_record_async(job_id=job_id)
        )

        return job_record

    def get_fd_data_pull_job_record_sync(self, job_id: str) -> FdDataPullConfig:
        job_record: FdDataPullConfig = (
            self.fd_trace_job_dao.get_fd_data_pull_job_record_sync(job_id=job_id)
        )

        return job_record

    async def update_fd_data_pull_job_record_current_stage_async(
        self,
        job_id: str,
        current_stage: FDDataPullStages,
        current_stage_status: DataCatalogStatus,
    ) -> bool:
        result: bool = await self.fd_trace_job_dao.update_fd_data_pull_job_record_current_stage_async(
            job_id=job_id,
            current_stage=current_stage,
            current_stage_status=current_stage_status,
        )
        if not result:
            raise Exception(
                "unable to update the fd_data_pull_job_record with stage and status"
            )

        return result

    def update_fd_data_pull_job_record_current_stage_sync(
        self,
        job_id: str,
        current_stage: FDDataPullStages,
        current_stage_status: DataCatalogStatus,
    ) -> bool:
        result: bool = (
            self.fd_trace_job_dao.update_fd_data_pull_job_record_current_stage_sync(
                job_id=job_id,
                current_stage=current_stage,
                current_stage_status=current_stage_status,
            )
        )
        if not result:
            raise Exception(
                "unable to update the fd_data_pull_job_record with stage and status"
            )

        return result

    async def get_fd_data_pull_job_config_record_async(
        self, job_config_id: str
    ) -> FdDataPullJobConfig:
        job_config_record: FdDataPullJobConfig = (
            await self.fd_trace_job_dao.get_fd_data_pull_job_config_record_async(
                job_config_id=job_config_id
            )
        )

        return job_config_record

    def get_fd_data_pull_job_config_record_sync(
        self, job_config_id: str
    ) -> FdDataPullJobConfig:
        job_config_record: FdDataPullJobConfig = (
            self.fd_trace_job_dao.get_fd_data_pull_job_config_record_sync(
                job_config_id=job_config_id
            )
        )

        return job_config_record

    def get_design_ids_with_technodes(
        self, facility: str = None, technodes: list = None
    ):
        """
        Description:
        - Get all the DesignIDs based on the facility and Technodes

        Input:
        - facility
        - technodes

        Output:
        - Returns SQL that will fetch the DesignIDs
        """
        if facility not in SUPPORTED_FACILITIES:
            sql = None
            status_code = 400
            error_message = (
                f"Supported Facilities: {SUPPORTED_FACILITIES}. Received {facility}"
            )
            return sql, status_code, error_message

        multi_sql_queries = []
        for technode in technodes:
            _technodes = [technode]

            if facility == "4":
                sql = f"""
                SELECT distinct
                rtrim(p.design_id) as design_ids
                FROM gdw-prod-data.fab_{facility}_ref.mfg_part_spec p
                INNER JOIN gdw-prod-data.fab_{facility}_ref.mfg_status ms
                    on ms.key_value = p.mfg_part_code
                    and ms.table_name = 'mfg_part_spec'
                    and rtrim(ms.key_value_status) = 'ACTIVE'
                INNER JOIN gdw-prod-data.fab_{facility}_trv.step_standard_design_id d
                    on rtrim(d.design_id) = rtrim(p.design_id)
                    and d.approved_flag = 'Y'
                INNER JOIN gdw-prod-data.fab_{facility}_trv.valid_part_for_trav vt
                    on p.mfg_part_code = vt.mfg_part_code
                INNER JOIN gdw-prod-data.fab_{facility}_ref.mfg_part_attribute a
                    on p.mfg_part_code = a.mfg_part_code
                    and rtrim(a.attribute_name) = 'TECHNOLOGY NODE'
                WHERE rtrim(a.attribute_value) IN UNNEST({str(_technodes)})
                """
            else:
                sql = f"""
                SELECT distinct
                rtrim(p.design_id) as design_ids
                FROM gdw-prod-data.fab_{facility}_ref.mfg_part_spec p
                INNER JOIN gdw-prod-data.fab_{facility}_ref.mfg_status ms
                    on ms.key_value = p.mfg_part_code
                    and ms.table_name = 'mfg_part_spec'
                    and rtrim(ms.key_value_status) = 'ACTIVE'
                INNER JOIN gdw-prod-data.fab_{facility}_trv.valid_part_for_trav vt
                    on p.mfg_part_code = vt.mfg_part_code
                INNER JOIN gdw-prod-data.fab_{facility}_ref.mfg_part_attribute a
                    on p.mfg_part_code = a.mfg_part_code
                    and rtrim(a.attribute_name) = 'TECHNOLOGY NODE'
                WHERE rtrim(a.attribute_value) IN UNNEST({str(_technodes)})
                """

            cache_keys = [f"fab_{facility}_technode_{technode}"]

            multi_sql_queries.append(
                MultiSqlQuery(sql_query=sql, cache_keys=cache_keys)
            )

        status_code = 200
        error_message = None

        return multi_sql_queries, status_code, error_message

    def get_traveler_ids(self, facility: str = None, design_ids: List[str] = None):
        if facility not in SUPPORTED_FACILITIES:
            sql = None
            status_code = 400
            error_message = (
                f"Supported Facilities: {SUPPORTED_FACILITIES}. Received {facility}"
            )
            return sql, status_code, error_message

        if not isinstance(design_ids, list):
            sql = None
            status_code = 400
            error_message = f"Expected a list for design_ids. Received {design_ids}, with type {type(design_ids)}"
            return sql, status_code, error_message

        multi_sql_queries = []
        for design_id in design_ids:
            sql = f"""
                        select distinct
                            rtrim(t.trav_id) as traveler_ids
                        from gdw-prod-data.fab_{facility}_trv.traveler t
                        where 1=1
                        and rtrim(t.trav_id) like '{design_id}%'
                        order by traveler_ids
                    """

            cache_keys = [f"fab_{facility}_designid_{design_id}"]

            multi_sql_queries.append(
                MultiSqlQuery(sql_query=sql, cache_keys=cache_keys)
            )

        status_code = 200
        error_message = None

        return multi_sql_queries, status_code, error_message

    @staticmethod
    def get_baseline_traveler_id(inputs: TravelerStepDataPullInput) -> Optional[str]:
        if inputs.facilities is None or not inputs.facilities.selected_values:
            raise Exception()
        if len(inputs.facilities.selected_values) > 1:
            raise Exception()
        facility = inputs.facilities.selected_values[0]
        if inputs.traveler_ids is None or not inputs.traveler_ids.selected_values:
            raise Exception()
        traveler_ids = inputs.traveler_ids.selected_values
        if len(traveler_ids) == 1:
            return traveler_ids[0]
        traveler_ids_mapping = DirectoryMapping(environment.tdam_pre_cache_path)[
            "HIGH_LEVEL"
        ][facility]["TRAVELER_STEPS"]
        paths: List[Path] = []
        for traveler_id in traveler_ids:
            if (
                traveler_id_mapping := traveler_ids_mapping.get(traveler_id)
            ) is not None:
                paths.extend(traveler_id_mapping.base_path.rglob("*.parquet"))
        df = pl.scan_parquet(paths)
        max_traveler_ids = (
            df.select("traveler_ids")
            .group_by("traveler_ids")
            .count()
            .max()
            .collect()["traveler_ids"]
            .to_list()
        )
        match max_traveler_ids:
            case [max_traveler_id]:
                return max_traveler_id
            case _:
                return None

    def get_probe_context_by_design(self, facility, design_id):
        if facility not in SUPPORTED_FACILITIES:
            sql = None
            status_code = 400
            error_message = (
                f"Supported Facilities: {SUPPORTED_FACILITIES}. Received {facility}"
            )
            return sql, status_code, error_message

        sql = f"""
                SELECT DISTINCT 
                fab,
                piid,
                paretotitle,
                pi_group,
                paretoid,
                dielosstype,
                paretoname
                FROM `gdw-prod-data.ww_dierbl.f{facility}_pi`
                WHERE 1=1
                AND paretoname LIKE '{design_id}%'
                """

        current_date_str = datetime.now().strftime("%Y-%m-%d")

        multi_sql_queries = [
            MultiSqlQuery(
                sql_query=sql,
                cache_keys=[f"probe_context_{design_id}_{current_date_str}"],
            )
        ]
        status_code = 200
        error_message = None

        return multi_sql_queries, status_code, error_message

    def get_traveler_steps_by_ids(
        self,
        facility: str = None,
        design_ids: List[str] = None,
        traveler_ids: List[str] = None,
    ):
        if facility not in SUPPORTED_FACILITIES:
            sql = None
            status_code = 400
            error_message = (
                f"Supported Facilities: {SUPPORTED_FACILITIES}. Received {facility}"
            )
            return sql, status_code, error_message

        if not isinstance(design_ids, list):
            sql = None
            status_code = 400
            error_message = f"Expected a list for design_ids. Received {design_ids}, with type {type(design_ids)}"
            return sql, status_code, error_message

        if not isinstance(traveler_ids, list):
            sql = None
            status_code = 400
            error_message = f"Expected a list for traveler_ids. Received {traveler_ids}, with type {type(traveler_ids)}"
            return sql, status_code, error_message

        multi_sql_queries = []

        for traveler_id in traveler_ids:
            # possible cache keys with design ids
            cache_keys = [f"fab_{facility}_travelerid_{traveler_id}"]
            # cache_keys = [f"fab_{facility}_designid_{design_id}_travelerid_{traveler_id}" for design_id in design_ids]

            sql = f"""
                    select distinct
                        rtrim(f.mfg_facility_id) as facilities
                        , substr(t.trav_id, 1, 4) as design_ids
                        , rtrim(t.trav_id) as traveler_ids
                        , ts.trav_step_seq_no as traveler_step_seq_no
                        , rtrim(s.masking_level_code) as masking_levels
                        , rtrim(s.step_name) as traveler_steps
                        , rtrim(a.mfg_area_id) as mfg_areas
                    from gdw-prod-data.fab_{facility}_trv.traveler t
                        inner join gdw-prod-data.fab_{facility}_trv.trav_step ts
                            on t.trav_OID = ts.trav_OID
                        inner join gdw-prod-data.fab_{facility}_ref.step s
                            on ts.step_OID = s.step_OID
                        inner join gdw-prod-data.fab_{facility}_ref.mfg_facility f
                            on f.mfg_facility_OID = t.mfg_facility_OID
                        left outer join gdw-prod-data.fab_{facility}_ref.step_data_for_fab sd
                            on sd.mfg_facility_OID = t.mfg_facility_OID
                            and sd.step_OID = s.step_OID
                        left outer join gdw-prod-data.fab_{facility}_ref.mfg_area a
                            on a.mfg_area_OID = sd.mfg_area_OID
                    where 1=1
                        and rtrim(t.trav_id) = '{traveler_id}'
                    order by traveler_ids, ts.trav_step_seq_no
                 """

            multi_sql_queries.append(
                MultiSqlQuery(sql_query=sql, cache_keys=cache_keys)
            )

        status_code = 200
        error_message = None

        return multi_sql_queries, status_code, error_message

    def get_fd_sensors(self, path: Path, selections: List[int]):
        lf: pl.LazyFrame = pl.scan_parquet(path).select(
            pl.int_range(pl.len(), dtype=pl.UInt32).alias("index"), pl.all()
        )
        lf: pl.LazyFrame = lf.filter(pl.col("index").is_in(selections))
        df = lf.collect().to_pandas()
        selection = df.to_dict(orient="records")

        # Construct dataframe for readability
        context_df = pd.DataFrame(selection)
        context_df["START_DATE"] = context_df["START_DATE"].astype(str)

        # Must grab facility, as fab10 also has fab10a which is not the case for others...
        facility = list(
            set(
                context_df["DWH_SRCID"]
                .str.replace("([^\s\d])", "", regex=True)
                .astype(int)
            )
        )[0]

        tool_gb = context_df.groupby("TOOL_ID")

        # Initiate the empty dataframe for compiling which data to pull for sensor list
        data_to_pull = pd.DataFrame()

        for tool, group in tool_gb:
            # Only sample from 3 waferids to get the sensor list, otherwise it is too costly!
            sampled_data = (
                group.sample(3, replace=True).drop_duplicates().reset_index(drop=True)
            )
            data_to_pull = pd.concat([data_to_pull, sampled_data])

        data_to_pull = (
            data_to_pull[["TOOL_ID", "RUN_ID", "START_DATE"]]
            .drop_duplicates()
            .reset_index(drop=True)
        )

        data_to_pull[["TOOL_ID", "RUN_ID"]] = data_to_pull[
            ["TOOL_ID", "RUN_ID"]
        ].astype(int)

        tool_ids = tuple(data_to_pull["TOOL_ID"].drop_duplicates())
        if len(tool_ids) <= 1:
            tool_ids = str(tool_ids).replace(",)", ")")

        run_ids = tuple(data_to_pull["RUN_ID"].drop_duplicates())
        if len(run_ids) <= 1:
            run_ids = str(run_ids).replace(",)", ")")

        run_dates = tuple(data_to_pull["START_DATE"].drop_duplicates())
        if len(run_dates) <= 1:
            run_dates = str(run_dates).replace(",)", ")")

        if facility == 10:
            sql = f"""
                    SELECT DISTINCT
                        TOOL_ID,
                        SENSOR AS sensors
                    FROM `gdw-prod-data.fab_{facility}_fd.run_data_point`
                    WHERE 1=1
                    AND TOOL_ID IN {tool_ids}
                    AND START_DATE IN {run_dates}
                    AND RUN_ID IN {run_ids}
                    
                    UNION ALL
                    
                    SELECT DISTINCT
                        TOOL_ID,
                        SENSOR AS sensors
                    FROM `gdw-prod-data.fab_{facility}a_fd.run_data_point`
                    WHERE 1=1
                    AND TOOL_ID IN {tool_ids}
                    AND START_DATE IN {run_dates}
                    AND RUN_ID IN {run_ids}
                """
        elif facility == 16:
            sql = f"""
                    SELECT DISTINCT
                        TOOL_ID,
                        SENSOR AS sensors 
                    FROM `gdw-prod-data.fab_{facility}_fd.run_data_point`
                    WHERE 1=1
                    AND TOOL_ID IN {tool_ids}
                    AND START_DATE IN {run_dates}
                    AND RUN_ID IN {run_ids}
                    
                    UNION ALL
                    
                    SELECT DISTINCT
                        TOOL_ID,
                        SENSOR AS sensors
                    FROM `gdw-prod-data.fab_{facility}c_fd.run_data_point`
                    WHERE 1=1
                    AND TOOL_ID IN {tool_ids}
                    AND START_DATE IN {run_dates}
                    AND RUN_ID IN {run_ids}
                """
        else:
            sql = f"""
                    SELECT DISTINCT
                        TOOL_ID,
                        SENSOR AS sensors
                    FROM `gdw-prod-data.fab_{facility}_fd.run_data_point`
                    WHERE 1=1
                    AND TOOL_ID IN {tool_ids}
                    AND START_DATE IN {run_dates}
                    AND RUN_ID IN {run_ids}
                """

        status_code = 200
        error_message = None

        return sql, status_code, error_message

    def get_fd_context(
        self,
        facility: str = None,
        start_date: str = None,
        end_date: str = None,
        design_ids: List[str] = None,
        traveler_steps: List[str] = None,
    ):
        if facility not in SUPPORTED_FACILITIES:
            sql = None
            status_code = 400
            error_message = (
                f"Supported Facilities: {SUPPORTED_FACILITIES}. Received {facility}"
            )
            return sql, status_code, error_message

        if not isinstance(design_ids, list):
            sql = None
            status_code = 400
            error_message = f"Expected a list for design_ids. Received {design_ids}, with type {type(design_ids)}"
            return sql, status_code, error_message

        if not isinstance(traveler_steps, list):
            sql = None
            status_code = 400
            error_message = f"Expected a list for traveler_steps. Received {traveler_steps}, with type {type(traveler_steps)}"
            return sql, status_code, error_message

        # The query messes up because python is stupid when it comes to creating tuple of length 1
        # So we have to correct for it here
        traveler_steps = tuple(traveler_steps)
        if len(traveler_steps) <= 1:
            traveler_steps = str(traveler_steps).replace(",)", ")")

        if facility == "10":
            sql = f"""
                    SELECT DISTINCT
                    DWH_SRCID,
                    DESIGN_ID,
                    RECIPE_NAME,
                    TOOL_NAME,
                    TOOL_ID,
                    RUN_ID,
                    CAST(LOT_ID AS STRING) AS LOT_ID,
                    WAFER_ID,
                    TRAVELER_STEP,
                    START_DATE
                    FROM `gdw-prod-data.fab_10_fd.fd_common_context_step` FD_CONTEXT
                    WHERE 1=1
                    AND START_DATE BETWEEN '{start_date}' AND '{end_date}'
                    AND TRAVELER_STEP IN {traveler_steps}
                    AND DESIGN_ID IN UNNEST({design_ids})

                    UNION ALL

                    SELECT DISTINCT
                    DWH_SRCID,
                    DESIGN_ID,
                    RECIPE_NAME,
                    TOOL_NAME,
                    TOOL_ID,
                    RUN_ID,
                    CAST(LOT_ID AS STRING) AS LOT_ID,
                    WAFER_ID,
                    TRAVELER_STEP,
                    START_DATE
                    FROM `gdw-prod-data.fab_10a_fd.fd_common_context_step` FD_CONTEXT
                    WHERE 1=1
                    AND START_DATE BETWEEN '{start_date}' AND '{end_date}'
                    AND TRAVELER_STEP IN {traveler_steps}
                    AND DESIGN_ID IN UNNEST({design_ids})
                """
        elif facility == "16":
            sql = f"""
                    SELECT DISTINCT
                    DWH_SRCID,
                    DESIGN_ID,
                    RECIPE_NAME,
                    TOOL_NAME,
                    TOOL_ID,
                    RUN_ID,
                    CAST(LOT_ID AS STRING) AS LOT_ID,
                    WAFER_ID,
                    TRAVELER_STEP,
                    START_DATE
                    FROM `gdw-prod-data.fab_16_fd.fd_common_context_step` FD_CONTEXT
                    WHERE 1=1
                    AND START_DATE BETWEEN '{start_date}' AND '{end_date}'
                    AND TRAVELER_STEP IN {traveler_steps}
                    AND DESIGN_ID IN UNNEST({design_ids})

                    UNION ALL

                    SELECT DISTINCT
                    DWH_SRCID,
                    DESIGN_ID,
                    RECIPE_NAME,
                    TOOL_NAME,
                    TOOL_ID,
                    RUN_ID,
                    CAST(LOT_ID AS STRING) AS LOT_ID,
                    WAFER_ID,
                    TRAVELER_STEP,
                    START_DATE
                    FROM `gdw-prod-data.fab_16c_fd.fd_common_context_step` FD_CONTEXT
                    WHERE 1=1
                    AND START_DATE BETWEEN '{start_date}' AND '{end_date}'
                    AND TRAVELER_STEP IN {traveler_steps}
                    AND DESIGN_ID IN UNNEST({design_ids})
                """
        else:
            sql = f"""
                    SELECT DISTINCT
                    DWH_SRCID,
                    DESIGN_ID,
                    RECIPE_NAME,
                    TOOL_NAME,
                    TOOL_ID,
                    RUN_ID,
                    CAST(LOT_ID AS STRING) AS LOT_ID,
                    WAFER_ID,
                    TRAVELER_STEP,
                    START_DATE
                    FROM `gdw-prod-data.fab_{facility}_fd.fd_common_context_step` FD_CONTEXT
                    WHERE 1=1
                    AND START_DATE BETWEEN '{start_date}' AND '{end_date}'
                    AND TRAVELER_STEP IN {traveler_steps}
                    AND DESIGN_ID IN UNNEST({design_ids})
                """

        status_code = 200
        error_message = None

        return sql, status_code, error_message

    def get_fd_trace(
        self, data: List = None, sensors: List[str] = None, datadir: str = None
    ) -> Tuple[List[MultiSqlQuery], int, str]:
        data_to_pull = pd.DataFrame(data)

        multi_sql_queries = []

        # Data is downloaded in small chunks
        for sensor in sensors:
            for row in range(len(data)):
                # Grab all of the parameters for each data pull
                fab = data_to_pull["DWH_SRCID"].iloc[row]
                designid = data_to_pull["DESIGN_ID"].iloc[row]
                lotid = data_to_pull["LOT_ID"].iloc[row]
                waferid = data_to_pull["WAFER_ID"].iloc[row]
                run_date = data_to_pull["START_DATE"].iloc[row]
                toolname = data_to_pull["TOOL_NAME"].iloc[row]
                toolid = data_to_pull["TOOL_ID"].iloc[row]
                runid = data_to_pull["RUN_ID"].iloc[row]
                travelerstep = data_to_pull["TRAVELER_STEP"].iloc[row]
                recipe_name = data_to_pull["RECIPE_NAME"].iloc[row]

                # Have to treat F10 and F16 separately
                if fab == "FAB_10A":
                    facility = "10a"
                    save_fab = "10"
                elif fab == "FAB_10":
                    facility = "10"
                    save_fab = "10"
                elif fab == "FAB_16":
                    facility = "16"
                    save_fab = "16"
                elif fab == "FAB_16C":
                    facility = "16c"
                    save_fab = "16"
                else:
                    facility = fab.split("_")[-1]
                    save_fab = facility

                # The data should be downloaded here with this data organization

                fname = f'/sensor_data/{lotid.replace(".", "_DOT_")}_{runid}_{toolname}_{sensor}/'

                recipe_name = recipe_name.replace("\\", "\\\\")

                # Only save the timestamp and value to minimize costs/storage/time
                # We are going to save per run so that sorting by timestamp is meaningful
                trace_sql = f"""
                                SELECT DISTINCT
                                '{fab}' AS DWH_SRCID,
                                '{designid}' AS DESIGN_ID,
                                '{lotid}' AS LOT_ID,
                                '{waferid}' AS WAFER_ID,
                                '{run_date}' AS START_DATE,
                                '{toolname}' AS TOOL_NAME,
                                '{toolid}' AS TOOL_ID,
                                '{runid}' AS RUN_ID,
                                '{travelerstep}' AS TRAVELER_STEP,
                                '{recipe_name}' AS RECIPE_NAME,
                                '{sensor}' AS SENSOR,
                                STEP_ID,
                                STEP_OCCURENCE,
                                STEP_SEQUENCE,
                                TIME_STAMP,
                                VALUE
                                FROM `gdw-prod-data.fab_{facility}_fd.run_data_point`
                                WHERE 1=1
                                AND START_DATE = '{run_date}'
                                AND TOOL_ID = {toolid}
                                AND RUN_ID = {runid}
                                AND SENSOR = '{sensor}'
                                ORDER BY TIME_STAMP
                            """

                multi_sql_queries.append(
                    MultiSqlQuery(sql_query=trace_sql, destination_folder_path=fname)
                )

        rdata = multi_sql_queries
        status_code = 200
        error_message = None

        return rdata, status_code, error_message

    def get_tech_nodes(self, facility: str = None):
        """
        Description:
        - Get all the tech nodes based on the facility

        Input:
        - facility

        Output:
        - Returns SQL that will fetch the TechNodes
        """
        if facility not in SUPPORTED_FACILITIES:
            sql = None
            status_code = 400
            error_message = (
                f"Supported Facilities: {SUPPORTED_FACILITIES}. Received {facility}"
            )
            return sql, status_code, error_message

        if facility == "4":
            sql = f"""
                    SELECT distinct
                    rtrim(a.attribute_value) as tech_nodes,
                    FROM gdw-prod-data.fab_{facility}_ref.mfg_part_spec p
                    INNER JOIN gdw-prod-data.fab_{facility}_ref.mfg_status ms
                        on ms.key_value = p.mfg_part_code
                        and ms.table_name = 'mfg_part_spec'
                        and rtrim(ms.key_value_status) = 'ACTIVE'
                    INNER JOIN gdw-prod-data.fab_{facility}_trv.step_standard_design_id d
                        on rtrim(d.design_id) = rtrim(p.design_id)
                        and d.approved_flag = 'Y'
                    INNER JOIN gdw-prod-data.fab_{facility}_trv.valid_part_for_trav vt
                        on p.mfg_part_code = vt.mfg_part_code
                    INNER JOIN gdw-prod-data.fab_{facility}_ref.mfg_part_attribute a
                        on p.mfg_part_code = a.mfg_part_code
                        and rtrim(a.attribute_name) = 'TECHNOLOGY NODE'
                """
        else:
            sql = f"""
                    SELECT distinct
                    rtrim(a.attribute_value) as tech_nodes,
                    FROM gdw-prod-data.fab_{facility}_ref.mfg_part_spec p
                    INNER JOIN gdw-prod-data.fab_{facility}_ref.mfg_status ms
                        on ms.key_value = p.mfg_part_code
                        and ms.table_name = 'mfg_part_spec'
                        and rtrim(ms.key_value_status) = 'ACTIVE'
                    INNER JOIN gdw-prod-data.fab_{facility}_trv.valid_part_for_trav vt
                        on p.mfg_part_code = vt.mfg_part_code
                    INNER JOIN gdw-prod-data.fab_{facility}_ref.mfg_part_attribute a
                        on p.mfg_part_code = a.mfg_part_code
                        and rtrim(a.attribute_name) = 'TECHNOLOGY NODE'
                """

        cache_keys = [f"fab_{facility}"]
        multi_sql_queries = [MultiSqlQuery(sql_query=sql, cache_keys=cache_keys)]

        status_code = 200
        error_message = None

        return multi_sql_queries, status_code, error_message

    def get_lot_ids(
        self,
        start_date: date,
        end_date: date,
        facility: str = None,
        traveler_ids: List[str] = [],
        selected_steps: List[str] = [],
    ):
        """
        Description:
        - Get all the lot ids based on the facility, traveler_ids, selected_steps, start_date, end_date

        Input:
        - start_date
        - end_date
        - facility
        - traveler_ids
        - selected_steps

        Output:
        - Returns SQL that will fetch the Lotidss
        """
        traveler_ids: str = f"( {', '.join(map(repr, traveler_ids))} )"
        selected_steps: str = f"( {', '.join(map(repr, selected_steps))} )"
        sql = f"""
            with traveler as (
                select distinct
                    rtrim(f.mfg_facility_id) as Facility
                    , substr(t.trav_id, 1, 4) as DesignId
                    , rtrim(t.trav_id) as TravelerId
                    , ts.trav_step_seq_no as StepSeqNo
                    , rtrim(s.masking_level_code) as MaskingLevel
                    , rtrim(s.step_name) as Step
                    , rtrim(a.mfg_area_id) as MfgArea
                    , trav_step_OID
                from gdw-prod-data.fab_{facility}_trv.traveler t
                    inner join gdw-prod-data.fab_{facility}_trv.trav_step ts
                        on t.trav_OID = ts.trav_OID
                    inner join gdw-prod-data.fab_{facility}_ref.step s
                        on ts.step_OID = s.step_OID
                    inner join gdw-prod-data.fab_{facility}_ref.mfg_facility f
                        on f.mfg_facility_OID = t.mfg_facility_OID
                    left outer join gdw-prod-data.fab_{facility}_ref.step_data_for_fab sd
                        on sd.mfg_facility_OID = t.mfg_facility_OID
                        and sd.step_OID = s.step_OID
                    left outer join gdw-prod-data.fab_{facility}_ref.mfg_area a
                        on a.mfg_area_OID = sd.mfg_area_OID
                where 1=1
                    and rtrim(t.trav_id) in {traveler_ids}
                    and rtrim(s.step_name) in {selected_steps}
                    order by TravelerId, ts.trav_step_seq_no
            ),
            lots as (
                select distinct
                    lot_id,
                    fab_lot_hist_OID,
                    traveler.TravelerId,
                    traveler.Step
                from `gdw-prod-data.fab_{facility}_ft.fab_lot_hist` flh
                inner join traveler
                on (
                    flh.trav_step_OID = traveler.trav_step_OID
                )
                where 1=1
                and tracked_out_datetime between '{start_date}' and '{end_date}'
            )
            select distinct
                lots.lot_id as lot_ids,
                ws.wafer_id as wafer_ids,
                DATETIME(wafers.updated_datetime) as run_date,
                lots.TravelerId as traveler_ids,
                lots.Step as traveler_steps
            from `gdw-prod-data.fab_{facility}_ft.wafer_hist` wafers
            inner join lots
            on (
                lots.fab_lot_hist_OID = wafers.fab_lot_hist_OID
            )
            inner join `gdw-prod-data.fab_{facility}_ft.wafer_status` ws
            on (
                wafers.wafer_OID = ws.wafer_OID
            )
            and wafers.updated_datetime between '{start_date}' and '{end_date}'
            order by run_date 
        """

        multi_sql_queries = [MultiSqlQuery(sql_query=sql)]

        status_code = 200
        error_message = None

        return multi_sql_queries, status_code, error_message

    def get_wafer_ids(
        self,
        start_date: date,
        end_date: date,
        facility: str = None,
        traveler_ids: List[str] = [],
        selected_steps: List[str] = [],
        lot_ids: List[str] = [],
    ):
        """
        Description:
        - Get all the lot ids based on the facility, traveler_ids, selected_steps, start_date, end_date

        Input:
        - start_date
        - end_date
        - facility
        - traveler_ids
        - selected_steps
        - lot_ids

        Output:
        - Returns SQL that will fetch the Waferidss
        """
        traveler_ids: str = f"( {', '.join(map(repr, traveler_ids))} )"
        selected_steps: str = f"( {', '.join(map(repr, selected_steps))} )"
        lot_ids: str = f"( {', '.join(map(repr, lot_ids))} )"
        sql = f"""
            with traveler as (
                select distinct
                    rtrim(f.mfg_facility_id) as Facility
                    , substr(t.trav_id, 1, 4) as DesignId
                    , rtrim(t.trav_id) as TravelerId
                    , ts.trav_step_seq_no as StepSeqNo
                    , rtrim(s.masking_level_code) as MaskingLevel
                    , rtrim(s.step_name) as Step
                    , rtrim(a.mfg_area_id) as MfgArea
                    , trav_step_OID
                from gdw-prod-data.fab_{facility}_trv.traveler t
                    inner join gdw-prod-data.fab_{facility}_trv.trav_step ts
                        on t.trav_OID = ts.trav_OID
                    inner join gdw-prod-data.fab_{facility}_ref.step s
                        on ts.step_OID = s.step_OID
                    inner join gdw-prod-data.fab_{facility}_ref.mfg_facility f
                        on f.mfg_facility_OID = t.mfg_facility_OID
                    left outer join gdw-prod-data.fab_{facility}_ref.step_data_for_fab sd
                        on sd.mfg_facility_OID = t.mfg_facility_OID
                        and sd.step_OID = s.step_OID
                    left outer join gdw-prod-data.fab_{facility}_ref.mfg_area a
                        on a.mfg_area_OID = sd.mfg_area_OID
                where 1=1
                    and rtrim(t.trav_id) in {traveler_ids}
                    and rtrim(s.step_name) in {selected_steps}
                    order by TravelerId, ts.trav_step_seq_no
            ),
            lots as (
                select distinct
                    lot_id,
                    fab_lot_hist_OID,
                    traveler.TravelerId,
                    traveler.Step
                from `gdw-prod-data.fab_{facility}_ft.fab_lot_hist` flh
                inner join traveler
                on (
                    flh.trav_step_OID = traveler.trav_step_OID
                )
                where 1=1
                and tracked_out_datetime between '{start_date}' and '{end_date}'
                and lot_ids {lot_ids}
            )
            select distinct
                lots.lot_id as lot_ids,
                ws.wafer_id as wafer_ids,
                DATETIME(wafers.updated_datetime) as run_date,
                lots.TravelerId as traveler_ids,
                lots.Step as traveler_steps
            from `gdw-prod-data.fab_{facility}_ft.wafer_hist` wafers
            inner join lots
            on (
                lots.fab_lot_hist_OID = wafers.fab_lot_hist_OID
            )
            inner join `gdw-prod-data.fab_{facility}_ft.wafer_status` ws
            on (
                wafers.wafer_OID = ws.wafer_OID
            )
            and wafers.updated_datetime between '{start_date}' and '{end_date}'
            order by run_date 
        """

        multi_sql_queries = [MultiSqlQuery(sql_query=sql)]

        status_code = 200
        error_message = None

        return multi_sql_queries, status_code, error_message

    @staticmethod
    def get_probe_data_queries(
        facility: str,
        design_id: str,
        paretonames: List[str],
        paretotitles: List[str],
        probe_context: Path,
        start_date: date,
        end_date: date,
    ) -> List[MultiSqlQuery]:
        probe_context_df = pd.read_parquet(probe_context)

    @staticmethod
    def get_final_data_aggregate_queries(
        facility: str,
        design_id: str,
        traveler_ids: List[str],
        traveler_steps: List[str],
        recipes: List[List[str]],
        tool_ids: List[List[str]],
        step_ids: List[List[str]],
        sensors: List[List[str]],
        start_date: date,
        end_date: date,
        final_data_aggregate_context_file: Path,
    ) -> List[MultiSqlQuery]:
        df = pl.scan_parquet(
            final_data_aggregate_context_file
        )  # filterd based on startdate and enddate.

        start_dates = [
            df.filter(
                pl.col("RECIPE").is_in(r_recipes)
                & pl.col("TOOL_ID").is_in(r_tool_ids)
                & pl.col("STEP_ID").is_in(r_step_ids)
                & pl.col("SENSOR").is_in(r_sensors)
            )
            .unique("START_DATE")
            .collect()
            .to_dict(as_series=False)["START_DATE"]
            for r_recipes, r_tool_ids, r_step_ids, r_sensors in zip(
                recipes, tool_ids, step_ids, sensors
            )
        ]
        # TODO: Tuplise instead of Unnest on tool_ids ,run_ids
        sql_query = (
            "(\n"
            "    WITH CONTEXT AS (\n"
            "        SELECT DISTINCT\n"
            "        DWH_SRCID,\n"
            "        TRAVELER_STEP,\n"
            "        RECIPE_NAME,\n"
            "        TOOL_NAME,\n"
            "        TOOL_ID,\n"
            "        RUN_ID,\n"
            "        LOT_ID,\n"
            "        WAFER_ID,\n"
            "        START_DATE\n"
            "        FROM `gdw-prod-data.fab_{facility}_fd.fd_common_context_step` FD_CONTEXT\n"
            "        WHERE 1=1\n"
            "        AND START_DATE = @start_date\n"
            "        AND TRAVELER_STEP IN (\n"
            "            SELECT DISTINCT\n"
            "            TRAVELER_STEP\n"
            "            FROM UNNEST(@traveler_steps) AS TRAVELER_STEP\n"
            "        )\n"
            "        AND DESIGN_ID = @design_id\n"
            "        AND RECIPE_NAME IS NOT NULL\n"
            "        AND LOT_ID IS NOT NULL\n"
            "        AND WAFER_ID IS NOT NULL\n"
            "        AND RUN_ID IS NOT NULL\n"
            "        AND TOOL_ID IN UNNEST(@tool_ids)\n"
            "        AND RECIPE_NAME IN UNNEST(@recipe_names)\n"
            "    )\n"
            "    SELECT DISTINCT\n"
            "    CONTEXT.DWH_SRCID,\n"
            "    @design_id AS DESIGN_ID,\n"
            "    CONTEXT.TRAVELER_STEP,\n"
            "    CONTEXT.RECIPE_NAME AS RECIPE,\n"
            "    CONTEXT.TOOL_NAME,\n"
            "    CONTEXT.TOOL_ID,\n"
            "    CONTEXT.RUN_ID,\n"
            "    CONTEXT.LOT_ID,\n"
            "    CONTEXT.WAFER_ID,\n"
            "    CONTEXT.START_DATE,\n"
            "    RUN_DATA_SUMMARY.SENSOR,\n"
            "    RUN_DATA_SUMMARY.STEP_ID,\n"
            "    RUN_DATA_SUMMARY.STEP_OCCURENCE,\n"
            "    RUN_DATA_SUMMARY.AGGREGATION_NAME,\n"
            "    RUN_DATA_SUMMARY.VALUE\n"
            "    FROM `gdw-prod-data.fab_{facility}_fd.run_data_summary` RUN_DATA_SUMMARY\n"
            "    INNER JOIN CONTEXT\n"
            "    ON (\n"
            "        CONTEXT.TOOL_ID = RUN_DATA_SUMMARY.TOOL_ID AND\n"
            "        CONTEXT.RUN_ID = RUN_DATA_SUMMARY.RUN_ID AND\n"
            "        CONTEXT.START_DATE = RUN_DATA_SUMMARY.START_DATE\n"
            "    )\n"
            "    WHERE 1=1\n"
            "    AND RUN_DATA_SUMMARY.START_DATE = @start_date\n"
            "    AND RUN_DATA_SUMMARY.AGGREGATION_NAME IN UNNEST(@aggregation_names)\n"
            "    AND RUN_DATA_SUMMARY.STEP_ID IN UNNEST(@step_ids)\n"
            "    AND RUN_DATA_SUMMARY.SENSOR IN UNNEST(@sensors)\n"
            "    AND RUN_DATA_SUMMARY.TOOL_ID IN (\n"
            "        SELECT DISTINCT\n"
            "        TOOL_ID\n"
            "        FROM CONTEXT\n"
            "    )\n"
            "    AND RUN_DATA_SUMMARY.RUN_ID IN (\n"
            "        SELECT DISTINCT\n"
            "        RUN_ID\n"
            "        FROM CONTEXT\n"
            "    )\n"
            ")\n"
        )
        match facility:
            case "10":
                facilities = ["10", "10a"]
            case "16":
                facilities = ["16", "16c"]
            case _:
                facilities = [facility]

        sql_query = "\n UNION ALL \n".join(
            sql_query.format(facility=facility) for facility in facilities
        )
        multi_sql_queries = []
        for r_recipes, r_tool_ids, r_step_ids, r_sensors, r_start_dates in zip(
            recipes, tool_ids, step_ids, sensors, start_dates
        ):
            sql_queries = [
                MultiSqlQuery(
                    sql_query=sql_query,
                    query_params={
                        "design_id": (
                            QueryParameterType.SCALAR,
                            QueryValueType.STRING,
                            design_id,
                        ),
                        "traveler_steps": (
                            QueryParameterType.ARRAY,
                            QueryValueType.STRING,
                            traveler_steps,
                        ),
                        "recipe_names": (
                            QueryParameterType.ARRAY,
                            QueryValueType.STRING,
                            r_recipes,
                        ),
                        "tool_ids": (
                            QueryParameterType.ARRAY,
                            QueryValueType.INTEGER,
                            r_tool_ids,
                        ),
                        "step_ids": (
                            QueryParameterType.ARRAY,
                            QueryValueType.STRING,
                            r_step_ids,
                        ),
                        "sensors": (
                            QueryParameterType.ARRAY,
                            QueryValueType.STRING,
                            r_sensors,
                        ),
                        "aggregation_names": (
                            QueryParameterType.ARRAY,
                            QueryValueType.STRING,
                            ["mean", "count"],
                        ),
                        "start_date": (
                            QueryParameterType.SCALAR,
                            QueryValueType.DATE,
                            start_date,
                        ),
                    },
                )
                for start_date in r_start_dates
            ]
            print(f"Added {len(sql_queries)} to fd addr queries")
            multi_sql_queries.extend(sql_queries)

        return multi_sql_queries

    @staticmethod
    def columnize_data(
        data: pd.DataFrame,
        columns_to_join_on=["LOT_ID", "WAFER_ID"],
        step_name_column="TRAVELER_STEP",
        categorical_id_column="COMMON_TEST_ID",
        numeric_value_column="TEST_VALUE",
        other_columns_to_keep=[],
        join_method="outer",
    ) -> pd.DataFrame:
        """
        Generalized function for transforming data (originally written for SIGMA, but generalized for FD)
        - Works based on the assumption that the lot/wafers are consistent across all different SIGMA tables
        - Collects the initial set of unique lot/wafers to build the transformed dataframe
        - Divides the flat data according to the different unique values in the step_name and test_id columns
        - Loops over all different combinations of step_name/test_id and structures the data based on wafer/lots
        - This function should work for all SIGMA tables that have COMMON_TEST_ID and TEST_VALUE as column name

        INPUTS:
        - data: pd.DataFrame(), the SIGMA table as a dataframe that has the COMMON_TEST_ID, and TEST_VALUE as columns
        - columns_to_join_on: List[str], list of columns to perform joins on (usually it is going to be lot/wafer id)
        - step_name_column: str, the column name that has the step name (either metro or process step) information
        - categorical_id_column: str, the column name that is the pivoting column, usually categorical (for FD, it is the SENSOR)
        - numeric_value_column: str, the column name that has the numeric data corresponding to the pivoting column
        - other_columns_to_keep: List[str], list of any additional columns that needs to be preserved, this is optional
        - join_method: str, the pandas join method, can be 'inner', 'left', 'right' or 'outer. By default, it is outer

        OUTPUTS:
        - lot_wafers: pd.DataFrame(), pivoted data that maps all of the measurement and point rows to unique LOT/WAFERs

        TO DO:
        - Assertion statements and error catching can be implemented for robustness
        """
        total_column_list = (
            columns_to_join_on
            + [step_name_column]
            + [categorical_id_column]
            + [numeric_value_column]
        )

        if len(other_columns_to_keep) > 0:
            total_column_list += other_columns_to_keep

        unique_step_test_ids = (
            data[[step_name_column, categorical_id_column]]
            .drop_duplicates()
            .reset_index(drop=True)
        )

        lot_wafers = data[columns_to_join_on].drop_duplicates().reset_index(drop=True)
        for index in range(len(unique_step_test_ids)):
            step_name = unique_step_test_ids[step_name_column].iloc[index]
            test_id = unique_step_test_ids[categorical_id_column].iloc[index]

            sub_data = data[
                (data[step_name_column] == step_name)
                & (data[categorical_id_column] == test_id)
            ].reset_index(drop=True)
            sub_data = sub_data[total_column_list]
            sub_data.rename(
                columns={numeric_value_column: f"{step_name}::{test_id}"}, inplace=True
            )

            if len(other_columns_to_keep) > 0:
                for column in other_columns_to_keep:
                    sub_data.rename(
                        columns={column: f"{step_name}::{test_id}::{column}"},
                        inplace=True,
                    )

            sub_data.drop(
                columns=[step_name_column, categorical_id_column], axis=1, inplace=True
            )

            # Need to drop duplicates, or else there is risk of exploding dataframes
            sub_data = sub_data.drop_duplicates().reset_index(drop=True)

            lot_wafers = lot_wafers.merge(
                sub_data, on=columns_to_join_on, how=join_method
            )

        return lot_wafers

    @staticmethod
    def get_final_data_aggregate(source: Path | List[Path], destination: Path):
        paths = []
        if isinstance(source, list):
            for path in source:
                paths.extend(path.rglob("*.parquet"))
        else:
            paths = source

        try:
            final_aggr_data = pl.read_parquet(paths).to_pandas()
            print("read with polars")
        except Exception as e:
            print(e)
            print("reading with pandas....")
            final_aggr_data = pd.read_parquet(paths)

        final_aggr_data["COMMON_TEST_ID"] = (
            "STEP_ID="
            + final_aggr_data["STEP_ID"]
            + "::"
            + final_aggr_data["AGGREGATION_NAME"]
        )

        # below processing inserted to handle multiple step occurrences [going with solution02: if multiple step occurrances pick the one with highest 'count' aggregation value]
        def remove_multiple_step_occurence(df):
            df_filtered = df[df["AGGREGATION_NAME"] == "count"]  # find all count
            df_f = df_filtered.loc[
                df_filtered.groupby(
                    [
                        "DWH_SRCID",
                        "DESIGN_ID",
                        "LOT_ID",
                        "WAFER_ID",
                        "TRAVELER_STEP",
                        "RECIPE",
                        "TOOL_NAME",
                        "SENSOR",
                        "STEP_ID",
                    ]
                )["VALUE"].idxmax()
            ]
            df_f = df_f[
                [
                    "DWH_SRCID",
                    "DESIGN_ID",
                    "LOT_ID",
                    "WAFER_ID",
                    "TRAVELER_STEP",
                    "RECIPE",
                    "TOOL_NAME",
                    "SENSOR",
                    "STEP_ID",
                    "STEP_OCCURENCE",
                ]
            ]
            return df.merge(df_f, on=df_f.columns.tolist(), how="inner")

        def remove_count_rows(df):
            # Filter out the rows where the metric is 'count'
            df_count = df[df["AGGREGATION_NAME"] == "count"].copy()
            df_filtered = df[df["AGGREGATION_NAME"] != "count"].copy()
            # Create/update the 'common_test_id' column
            df_filtered["COMMON_TEST_ID"] = df_filtered.apply(
                lambda row: f"STEP_ID={row['STEP_ID']}::{row['AGGREGATION_NAME']}::count={df_count[df_count['STEP_ID'] == row['STEP_ID']]['VALUE'].values[0]}",
                axis=1,
            )
            return df_filtered

        final_aggr_data = remove_multiple_step_occurence(final_aggr_data)
        final_aggr_data = remove_count_rows(final_aggr_data)
        # ------------------------------------

        final_aggr_data = FdTraceDataPullService.columnize_data(
            data=final_aggr_data,
            columns_to_join_on=["RECIPE", "LOT_ID", "WAFER_ID", "STEP_OCCURENCE"],
            step_name_column="SENSOR",
            categorical_id_column="COMMON_TEST_ID",
            numeric_value_column="VALUE",
        )
        final_aggr_data.to_parquet(destination)

    def get_uc2_sigma_data_pull(
        self,
        facility: str,
        traveler_ids: List[str],
        traveler_steps: List[str],
        tools: List[str],
        step_ids: List[str],
        sensors: List[str],
        start_date: date,
        end_date: date,
    ) -> Tuple[List[MultiSqlQuery], int, Optional[str]]:
        # TODO write actual query and change inputs
        return [], 200, None

    @staticmethod
    def file_names_generator(file_path, chunk_size=10000):
        with os.scandir(file_path) as entries:
            chunk = []
            for entry in entries:
                if entry.is_file():
                    chunk.append(entry.name.split(".")[0])
                    if len(chunk) == chunk_size:
                        yield chunk
                        chunk = []
            if chunk:
                yield chunk

    @staticmethod
    def generate_measurement_steps(inputs: FdContextDataPullInput, result_folder: Path):
        if inputs.facilities is None or not inputs.facilities.selected_values:
            raise ValueError("facility is not selected")
        if inputs.traveler_steps is None or not inputs.traveler_steps.selected_values:
            raise ValueError("traveler_steps are not selected")

        # TODO: currently we are parsing folder to get measurement steps, eventually we might get these from traveler steps
        # measurement_steps_folder = environment.tdam_shared_path/UC2_SIGMA_DROPDOWN_FOLDER_NAMES.get('measurement_steps')[0].format(inputs.facilities.selected_values[0])

        output_file = (
            result_folder / UC2_SIGMA_DROPDOWN_FOLDER_NAMES.get("measurement_steps")[1]
        )
        output_file.parent.mkdir(exist_ok=True, parents=True)
        if output_file.exists():
            output_file.unlink()
        # chunk_index = 0
        # data_frames = []
        # for file_chunk in FdTraceDataPullService.file_names_generator(measurement_steps_folder):
        #     df = pd.DataFrame(file_chunk, columns=['measurement_steps'])
        #     data_frames.append(df)
        #     chunk_index += 1
        # combined_df = pd.concat(data_frames, ignore_index=True)

        combined_df = pd.DataFrame(
            inputs.traveler_steps.selected_values, columns=["measurement_steps"]
        )
        combined_df.to_parquet(output_file)

        return output_file

    @staticmethod
    def generate_point_steps(inputs: FdContextDataPullInput, result_folder: Path):
        if inputs.facilities is None or not inputs.facilities.selected_values:
            raise ValueError("facility is not selected")

        # TODO: currently we are parsing folder to get point steps, eventually we might get these from traveler steps
        # points_steps_folder = environment.tdam_shared_path/UC2_SIGMA_DROPDOWN_FOLDER_NAMES.get('point_steps')[0].format(inputs.facilities.selected_values[0])

        output_file = (
            result_folder / UC2_SIGMA_DROPDOWN_FOLDER_NAMES.get("point_steps")[1]
        )
        output_file.parent.mkdir(exist_ok=True, parents=True)
        if output_file.exists():
            output_file.unlink()
        # chunk_index = 0
        # data_frames = []
        # for file_chunk in FdTraceDataPullService.file_names_generator(points_steps_folder):
        #     df = pd.DataFrame(file_chunk, columns=['point_steps'])
        #     data_frames.append(df)
        #     chunk_index += 1
        #
        # combined_df = pd.concat(data_frames, ignore_index=True)
        combined_df = pd.DataFrame(
            inputs.traveler_steps.selected_values, columns=["point_steps"]
        )
        combined_df.to_parquet(output_file)

        return output_file

    @staticmethod
    def generate_run_parameters(inputs: FdContextDataPullInput, result_folder: Path):
        if inputs.facilities is None or not inputs.facilities.selected_values:
            raise ValueError("facility is not selected")

        run_params_file = (
            environment.tdam_pre_cache_path
            / UC2_SIGMA_DROPDOWN_FOLDER_NAMES.get("run_parameters")[0].format(
                inputs.facilities.selected_values[0]
            )
        )

        output_file = (
            result_folder / UC2_SIGMA_DROPDOWN_FOLDER_NAMES.get("run_parameters")[1]
        )
        output_file.parent.mkdir(exist_ok=True, parents=True)
        if output_file.exists():
            output_file.unlink()
        df = pd.DataFrame(columns=["run_parameters"])
        if Path(run_params_file).exists():
            parquet_files = glob.glob(os.path.join(str(run_params_file), "*.parquet"))
            # Read the parquet files only in initial level
            df = pd.concat([pd.read_parquet(file) for file in parquet_files])
            df["run_parameters"] = df["COMMON_TEST_ID"]
        else:
            print(f"FILE {run_params_file} doesnt exist")
        df.to_parquet(output_file)
        return output_file

    @staticmethod
    def generate_measurement_parameters(
        inputs: UC2SigmaMeasurementParametersFetchInput, result_folder: Path
    ):
        if inputs.facilities is None or not inputs.facilities.selected_values:
            raise ValueError("facility is not selected")
        if (
            inputs.measurement_steps is None
            or not inputs.measurement_steps.selected_values
        ):
            raise ValueError("No measurement steps are selected")

        measurement_steps_folder = (
            environment.tdam_pre_cache_path
            / UC2_SIGMA_DROPDOWN_FOLDER_NAMES.get("measurement_parameters")[0].format(
                inputs.facilities.selected_values[0]
            )
        )

        output_file = (
            result_folder
            / UC2_SIGMA_DROPDOWN_FOLDER_NAMES.get("measurement_parameters")[1]
        )
        output_file.parent.mkdir(exist_ok=True, parents=True)
        if output_file.exists():
            output_file.unlink()

        data_frames = []
        for step in inputs.measurement_steps.selected_values:
            converted_step_folder_name = (
                step.replace(" ", "_SPACE_")
                .replace("/", "_SLASH_")
                .replace(".", "_DOT_")
            )
            step_file_path = measurement_steps_folder / f"{converted_step_folder_name}/"
            df = pd.DataFrame(columns=["COMMON_TEST_ID"])
            if Path(step_file_path).exists():
                df = pd.read_parquet(step_file_path)
            else:
                print(f"FILE {step_file_path} doesnt exist")
            data_frames.append(df)

        combined_df = pd.concat(data_frames, ignore_index=True)
        combined_df["measurement_parameters"] = combined_df["COMMON_TEST_ID"]
        combined_df.to_parquet(output_file)

        return output_file

    @staticmethod
    def generate_wafer_parameters(
        inputs: UC2SigmaMeasurementParametersFetchInput, result_folder: Path
    ):
        if inputs.facilities is None or not inputs.facilities.selected_values:
            raise ValueError("facility is not selected")
        if (
            inputs.measurement_steps is None
            or not inputs.measurement_steps.selected_values
        ):
            raise ValueError("No measurement steps are selected")

        wafer_parames_folder = (
            environment.tdam_pre_cache_path
            / UC2_SIGMA_DROPDOWN_FOLDER_NAMES.get("wafer_parameters")[0].format(
                inputs.facilities.selected_values[0]
            )
        )

        output_file = (
            result_folder / UC2_SIGMA_DROPDOWN_FOLDER_NAMES.get("wafer_parameters")[1]
        )
        output_file.parent.mkdir(exist_ok=True, parents=True)
        if output_file.exists():
            output_file.unlink()

        data_frames = []
        for step in inputs.measurement_steps.selected_values:
            converted_step_folder_name = (
                step.replace(" ", "_SPACE_")
                .replace("/", "_SLASH_")
                .replace(".", "_DOT_")
            )
            step_file_path = wafer_parames_folder / f"{converted_step_folder_name}/"
            df = pd.DataFrame(columns=["COMMON_TEST_ID"])
            if Path(step_file_path).exists():
                df = pd.read_parquet(step_file_path)
            else:
                print(f"FILE {step_file_path} doesnt exist")
            data_frames.append(df)

        combined_df = pd.concat(data_frames, ignore_index=True)
        combined_df["wafer_parameters"] = combined_df["COMMON_TEST_ID"]
        combined_df.to_parquet(output_file)

        return output_file

    @staticmethod
    def generate_point_parameters(
        inputs: UC2SigmaMeasurementParametersFetchInput, result_folder: Path
    ):
        if inputs.facilities is None or not inputs.facilities.selected_values:
            raise ValueError("facility is not selected")
        if inputs.point_steps is None or not inputs.point_steps.selected_values:
            raise ValueError("No point steps are selected")

        point_parameters_folder = (
            environment.tdam_pre_cache_path
            / UC2_SIGMA_DROPDOWN_FOLDER_NAMES.get("point_parameters")[0].format(
                inputs.facilities.selected_values[0]
            )
        )

        output_file = (
            result_folder / UC2_SIGMA_DROPDOWN_FOLDER_NAMES.get("point_parameters")[1]
        )
        output_file.parent.mkdir(exist_ok=True, parents=True)
        if output_file.exists():
            output_file.unlink()

        data_frames = []
        for step in inputs.point_steps.selected_values:
            converted_step_folder_name = (
                step.replace(" ", "_SPACE_")
                .replace("/", "_SLASH_")
                .replace(".", "_DOT_")
            )
            step_file_path = point_parameters_folder / f"{converted_step_folder_name}/"
            df = pd.DataFrame(columns=["COMMON_TEST_ID"])
            if Path(step_file_path).exists():
                df = pd.read_parquet(step_file_path)
            else:
                print(f"FILE {step_file_path} doesnt exist")
            data_frames.append(df)

        combined_df = pd.concat(data_frames, ignore_index=True)
        combined_df["point_parameters"] = combined_df["COMMON_TEST_ID"]
        combined_df.to_parquet(output_file)

        return output_file

    @staticmethod
    def get_overlapping_filepaths(
        directory: Path, start_date: date, end_date: date
    ) -> List[Path]:
        if not directory.is_dir():
            raise NotADirectoryError(directory)
        overlapping_files: List[Path] = []
        for filepath in directory.rglob("*.parquet"):
            filename = filepath.stem  # ["FD", "CONTEXT", "start_date", "end_date"]
            try:
                parts = filename.split("_")[2:]
                file_start_date, file_end_date = map(date.fromisoformat, parts)
                # Check if the date ranges overlap
                if max(file_start_date, start_date) <= min(file_end_date, end_date):
                    overlapping_files.append(filepath)
            except IndexError:
                # Skip files that don't match the pattern
                continue
        return overlapping_files

    @staticmethod
    def generate_fd_context(
        facility: str,
        design_id: str,
        traveler_steps: List[str],
        start_date: date,
        end_date: date,
    ) -> pl.LazyFrame:
        if environment.dev_mode:
            return pl.scan_parquet(DUMMY_FILES["contexts"])
        try:
            traveler_steps_mapping = DirectoryMapping(
                base_path=environment.tdam_pre_cache_path / "FD"
            )[facility][design_id]
            fd_context_paths = [
                fd_context_dir
                for traveler_step in traveler_steps
                if (traveler_step_mapping := traveler_steps_mapping.get(traveler_step))
                is not None
                and (fd_context_dir := traveler_step_mapping.base_path).exists()
            ]
            new_fd_context_paths: List[Path] = []
            for path in fd_context_paths:
                new_fd_context_paths.extend(
                    FdTraceDataPullService.get_overlapping_filepaths(
                        path, start_date, end_date
                    )
                )
            return (
                pl.scan_parquet(new_fd_context_paths)
                .drop("__index_level_0__", strict=False)
                .drop_nulls()
                .rename(str.upper)
                .cast({"START_DATE": pl.Date})
                .filter(pl.col("START_DATE").is_between(start_date, end_date))
            )
        except ValueError as e:
            logger.exception("empty data")
            print("empty data", e)
            return pl.scan_parquet(DUMMY_FILES["empty_context"])
        except KeyError as e:
            logger.exception("empty data")
            print("empty data", e)
            return pl.scan_parquet(DUMMY_FILES["empty_context"])

    @staticmethod
    def generate_aggeragated_context(
        facility: str,
        design_id: str,
        traveler_steps: List[str],
        start_date: date,
        end_date: date,
    ) -> pl.LazyFrame:
        if environment.dev_mode:
            return pl.scan_parquet(DUMMY_FILES["final_aggregate_data_context"])
        try:
            fd_context_df = FdTraceDataPullService.generate_fd_context(
                facility=facility,
                design_id=design_id,
                traveler_steps=traveler_steps,
                start_date=start_date,
                end_date=end_date,
            )
            tools_df = fd_context_df.select("TOOL_NAME", "TOOL_ID").unique()
            tools = tools_df.collect().to_dict()
            tools_mapping = DirectoryMapping(
                base_path=environment.tdam_pre_cache_path / "FD"
            )[facility]["TOOLS"]
            sensors_and_step_ids_paths = [
                sensors_and_step_ids_path
                for tool_name, tool_id in zip(tools["TOOL_NAME"], tools["TOOL_ID"])
                if (tool_mapping := tools_mapping.get(f"{tool_name}_{tool_id}"))
                is not None
                and (
                    sensors_and_step_ids_path := tool_mapping.base_path
                    / "stepid_sensors.parquet"
                ).exists()
            ]
            return pl.concat(
                [
                    pl.scan_parquet(path)
                    .unique()
                    .join(fd_context_df, on="TOOL_ID", how="inner")
                    .drop_nulls("TOOL_ID")
                    .drop(
                        "TOOL_ID_right",
                        "RUN_ID_right",
                        "__index_level_0__",
                        strict=False,
                    )
                    .unique(["RECIPE", "TOOL_NAME", "TOOL_ID", "SENSOR", "STEP_ID"])
                    for path in sensors_and_step_ids_paths
                ],
                how="vertical",
            )
        except ValueError as e:
            logger.exception("empty data")
            print("empty data", e)
            return pl.scan_parquet(DUMMY_FILES["empty_final_aggregate_data_context"])
        except KeyError as e:
            logger.exception("empty data")
            print("empty data", e)
            return pl.scan_parquet(DUMMY_FILES["empty_final_aggregate_data_context"])

    @staticmethod
    def generate_uc3_step_parameters(inputs: UC3SigmaCommonTestIdInput) -> pl.LazyFrame:
        if inputs.facilities is None or not inputs.facilities.selected_values:
            raise ValueError("facility is not selected")
        facility = inputs.facilities.selected_values[0]
        if not inputs.uc3_sigma_metro_steps:
            raise ValueError("No measurement steps are selected")
        # TODO: ADD CACHED TRAVELER STEPS OR GET FROM TRAVELER STAGE
        # if not inputs.cached_traveler_steps:
        #     raise ValueError('Missing Traveler steps (cached) so unable to filter common test ids')

        # NOTE: uc3_sigma_metro_steps is calculated from uc3_sigma_metro_steps_
        metro_steps_prefixes_temp = set(inputs.uc3_sigma_metro_steps)

        if inputs.cached_traveler_steps:
            metro_steps_prefixes = set(
                traveler_step
                for traveler_step in inputs.cached_traveler_steps
                if traveler_step[:4] in metro_steps_prefixes_temp
            )
        else:
            metro_steps_prefixes = metro_steps_prefixes_temp

        base_path = environment.tdam_pre_cache_path / "SIGMA" / facility
        folder_names: List[str] = []
        if inputs.wafer_level:
            folder_names.append("MEASUREMENT_PARAMS")
        if inputs.point_level:
            folder_names.append("POINT_PARAMS")
        steps_mappings = [
            DirectoryMapping(base_path=base_path / folder_name)
            for folder_name in folder_names
        ]
        parameters_folders = [
            mapping.base_path
            for steps_mapping in steps_mappings
            for metro_step_prefix in metro_steps_prefixes
            for mapping in steps_mapping.get_based_on_wildcards(metro_step_prefix + "*")
        ]

        dfs = [
            pl.scan_parquet(folder).select("COMMON_TEST_ID")
            for folder in parameters_folders
        ]
        if not dfs:
            return pl.LazyFrame([], schema=(("COMMON_TEST_ID", str),))
        return pl.concat(dfs, how="vertical")
