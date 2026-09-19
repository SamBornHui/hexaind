import os
import shutil
import traceback
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional
from uuid import uuid4

import aiofiles
import pandas as pd
import polars as pl
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import FilePath
from pymongo import MongoClient

from app.actions import Actions
from app.config.env_vars import environment
from app.core.celery.celery_worker import create_celery_app
from app.core.db.db_utils import get_db_async, get_db_sync
from app.core.services.jwt_token_utils.jwt_token_utils import JWTBearer, decodeJWT
from app.services.data.assets.datasets.schemas import (
    AccessMode,
    DatasetMetadata,
    DatasetSourceFormats,
    DatasetUploadResponse,
    TabularDatasetInformationAndMetadata,
)
from app.services.data.assets.datasets.service import DatasetsService
from app.services.micron.data_catalog.fd_trace.dummy_files import DUMMY_FILES
from app.services.micron.data_catalog.fd_trace.schemas import (
    DataPullResult,
    DataPullStatus,
    DesignIdDataPullConfig,
    DesignIdDataPullInput,
    FacilitesDataPullConfig,
    FacilitesDataPullInput,
    FdContextDataPullConfig,
    FdContextDataPullInput,
    FdDataPullConfig,
    FdDataPullJobConfig,
    FDDataPullStages,
    FdDataPullStausResponse,
    FdDataPullStausResult,
    FdTraceDataPullInput,
    FdTracePullFullStatusResponse,
    FinalDataAggregateContextInput,
    FinalDataAggregateContextOutput,
    FinalDataAggregateInput,
    LotIdsDataPullConfig,
    LotIdsDataPullInput,
    LotWaferInput,
    ProbeContextDataPullInput,
    ProbeDataPullInputs,
    SensorsDataPullConfig,
    SensorsDataPullInput,
    TechNodeDataPullConfig,
    TechNodesDataPullInput,
    TravelersIdDataPullConfig,
    TravelersIdDataPullInput,
    TravelerStepDataPullConfig,
    TravelerStepDataPullInput,
    UC2SigmaDataPullInput,
    UC2SigmaGQLFileParsedContentFile,
    UC2SigmaMeasurementParametersFetchInput,
    UC2SigmaMeasurementStepsDependentParameters,
    UC2SigmaPointParameters,
    UC2SigmaSteps,
    UC3FDContextApplyFiltersInput,
    UC3SigmaCommonTestIdInput,
    UC3SigmaInput,
    UC3SigmaMetroStepsCommonTestIds,
    UploadCsvResponse,
    WaferIdsDataPullInput,
)
from app.services.micron.data_catalog.fd_trace.service import FdTraceDataPullService
from app.services.micron.data_catalog.helper import get_excel_columns
from app.services.micron.data_catalog.schemas import (
    DataCatalogStatus,
    DataPullStatus,
    DataSourceType,
)


def submit_data_pull_job(
    task_id: str, data_pull_job_id: str, stage_job_id: str, user_name: str
):
    # inserting the start task in queue
    celeryApp = create_celery_app("run_workflow")
    celeryApp.send_task(
        "task_data_pull_stage",
        task_id=task_id,
        kwargs={
            "data_pull_job_id": data_pull_job_id,
            "stage_job_id": stage_job_id,
            "user_name": user_name,
        },
        queue="data_catalog",
        routing_key="fd_trace",
    )


def submit_data_processing_job(
    task_id: str, data_pull_job_id: str, stage_job_id: str, user_name: str
):
    # inserting the start task in queue
    celeryApp = create_celery_app("run_workflow")
    celeryApp.send_task(
        "task_data_processing_stage",
        task_id=task_id,
        kwargs={
            "data_pull_job_id": data_pull_job_id,
            "stage_job_id": stage_job_id,
            "user_name": user_name,
        },
        queue="data_catalog",
        routing_key="fd_trace",
    )


router = APIRouter(prefix="/fd")


def get_user_name(token: Annotated[str, Depends(JWTBearer())]) -> str:
    decoded_token: Optional[Dict[str, str]] = decodeJWT(token)
    if decoded_token is None:
        raise ValueError("invalid token")
    email = decoded_token["email"]
    return email.split("@")[0].replace(".", "_")


def get_user_id_from_token(token: Annotated[str, Depends(JWTBearer())]) -> str:
    decoded_token: Optional[Dict[str, str]] = decodeJWT(token)
    if decoded_token is None:
        raise ValueError("invalid token")
    return decoded_token["user_id"]


def get_fdtrace_data_pull_service(
    async_client: AsyncIOMotorClient = Depends(get_db_async),
    sync_client: MongoClient = Depends(get_db_sync),
) -> FdTraceDataPullService:
    return FdTraceDataPullService(
        db_async_client=async_client, db_sync_client=sync_client
    )


class FdTraceDataPullRoutes:
    def __init__(self):
        pass

    @staticmethod
    @router.get("/fd_trace_pull_stop", status_code=status.HTTP_200_OK)
    async def fd_trace_pull_stop_route(
        data_pull_job_id: str, client: AsyncIOMotorClient = Depends(get_db_async)
    ):
        try:
            fd_trace_service = FdTraceDataPullService(db_async_client=client)
            await fd_trace_service.stop_stage(data_pull_job_id=data_pull_job_id)
            return {}

        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "fd_trace_pull_full_status_error", "message": str(e)},
            )

    @staticmethod
    @router.get("/fd_trace_pull_full_status", status_code=status.HTTP_200_OK)
    async def fd_trace_pull_full_status(
        data_pull_job_id: str, client: AsyncIOMotorClient = Depends(get_db_async)
    ) -> list[FdTracePullFullStatusResponse]:
        try:
            fd_trace_service = FdTraceDataPullService(db_async_client=client)
            return await fd_trace_service.fd_trace_pull_full_status_async(
                data_pull_job_id=data_pull_job_id
            )

        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "fd_trace_pull_full_status_error", "message": str(e)},
            )

    @staticmethod
    @router.get("/fd_data_pull_status", status_code=status.HTTP_200_OK)
    async def get_fd_data_pull_status(
        data_pull_job_id: str,
        stage: Optional[FDDataPullStages] = None,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> FdDataPullStausResponse:
        try:
            fd_trace_service = FdTraceDataPullService(db_async_client=client)
            if stage is None:
                return await fd_trace_service.get_last_ran_stage_status_async(
                    data_pull_job_id=data_pull_job_id
                )
            else:
                return await fd_trace_service.get_stage_status_async(
                    data_pull_job_id=data_pull_job_id, stage=stage
                )

        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "get_fd_data_pull_status_error", "message": str(e)},
            )

    @staticmethod
    @router.get("/fd_data_pull_results", status_code=status.HTTP_200_OK)
    async def get_fd_data_pull_results(
        data_pull_job_id: str,
        stage: FDDataPullStages,
        ignore_last_run_level: bool = False,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> FdDataPullStausResult:
        try:
            fd_trace_service = FdTraceDataPullService(db_async_client=client)

            return await fd_trace_service.get_stage_results_async(
                data_pull_job_id=data_pull_job_id,
                stage=stage,
                ignore_last_run_level=ignore_last_run_level,
            )

        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "get_fd_data_pull_results_error", "message": str(e)},
            )

    @staticmethod
    @router.post("/save_stage", status_code=status.HTTP_200_OK)
    async def save_stage_inputs(
        data_pull_job_id: str = Query(..., description="ID of the data pull job"),
        stage: FDDataPullStages = Query(
            ..., description="Stage of the data pull process"
        ),
        inputs: Dict[str, Any] = {},
        client: AsyncIOMotorClient = Depends(get_db_async),
    ):
        try:
            fd_trace_service = FdTraceDataPullService(db_async_client=client)

            await fd_trace_service.save_stage_inputs_async(
                data_pull_job_id=data_pull_job_id, stage=stage, inputs=inputs
            )

            return {}

        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "get_fd_data_pull_results_error", "message": str(e)},
            )

    @staticmethod
    @router.post("/check_if_inputs_got_changes", status_code=status.HTTP_200_OK)
    async def check_if_inputs_got_changes(
        data_pull_job_id: str,
        stage: FDDataPullStages,
        inputs: dict,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> dict:
        try:
            if stage == FDDataPullStages.IDLE or stage == FDDataPullStages.FACILITIES:
                return {"is_changed": False}

            fd_trace_service = FdTraceDataPullService(db_async_client=client)

            data_pull_job_record: FdDataPullConfig = (
                await fd_trace_service.fetch_data_pull_job_record(
                    job_id=data_pull_job_id
                )
            )
            if data_pull_job_record.data_pull_status == DataCatalogStatus.RUNNING:
                return {"is_changed": False}

            stage_config_record: FdDataPullJobConfig = (
                await fd_trace_service.fetch_stage_config_record(
                    data_pull_job_record=data_pull_job_record, stage=stage
                )
            )

            if stage_config_record.stage_config is None:
                raise ValueError("stage not initialize")

            if (
                stage_config_record.stage_config.status.status
                == DataPullStatus.NOT_CONFIGURED
            ):
                return {"is_changed": True}

            print("inputs")
            print(inputs)

            if stage == FDDataPullStages.TECH_NODE:
                stage_inputs = TechNodesDataPullInput.model_validate(inputs)
            elif stage == FDDataPullStages.DESIGN_ID:
                stage_inputs = DesignIdDataPullInput.model_validate(inputs)
            elif stage == FDDataPullStages.TRAVELER_ID:
                stage_inputs = TravelersIdDataPullInput.model_validate(inputs)
            elif stage == FDDataPullStages.TRAVELER_STEP:
                stage_inputs = TravelerStepDataPullInput.model_validate(inputs)
            elif stage == FDDataPullStages.FD_CONTEXT:
                stage_inputs = FdContextDataPullInput.model_validate(inputs)
            elif stage == FDDataPullStages.FD_SENSOR:
                stage_inputs = SensorsDataPullInput.model_validate(inputs)
            elif stage == FDDataPullStages.FD_TRACE:
                stage_inputs = FdTraceDataPullInput.model_validate(inputs)
            else:
                return {"is_changed": True}

            print("new inputs:")
            print(stage_inputs.model_dump_json(indent=2))

            print("old inputs:")
            print(stage_config_record.model_dump_json(indent=2))

            if fd_trace_service.check_if_stage_triggered_with_same_inputs(
                new_inputs=stage_inputs, existing_job_config=stage_config_record
            ):
                return {"is_changed": False}

            # reset all the stages including current stage
            await fd_trace_service.reset_all_forward_stage_configs(
                data_pull_job_record_id=data_pull_job_id,
                data_pull_job_record=data_pull_job_record,
                stage=stage,
            )

            # reset the last ran previous stage

            return {"is_changed": True}

        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "tech_nodes_error", "message": str(e)},
            )

    @staticmethod
    @router.post("/facilities", status_code=status.HTTP_200_OK)
    async def get_facilities_route(
        inputs: FacilitesDataPullInput,
        data_pull_job_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
        user_name: str = Depends(get_user_name),
    ) -> dict:
        try:
            fd_trace_service = FdTraceDataPullService(db_async_client=client)
            fd_data_pull_job_record: FdDataPullConfig = (
                await fd_trace_service.get_fd_data_pull_job_record_async(
                    job_id=data_pull_job_id
                )
            )

            if fd_data_pull_job_record.data_source_type != DataSourceType.FD_TRACE:
                raise Exception("Invalid source type for getting facilities")

            if fd_data_pull_job_record.data_pull_status == DataCatalogStatus.RUNNING:
                raise Exception(
                    "Data pull job is already in execusion. Please try after the current pull is done"
                )

            await fd_trace_service.get_facilities(
                inputs=inputs,
                job_config_id=fd_data_pull_job_record.facility_stage_job_id,
            )

            # update data_pull_job_id current stage as facilities
            await fd_trace_service.update_fd_data_pull_job_record_current_stage_async(
                job_id=data_pull_job_id,
                current_stage=FDDataPullStages.FACILITIES,
                current_stage_status=DataCatalogStatus.IDLE,
            )

            return {}

        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "facilities_error", "message": str(e)},
            )

    @staticmethod
    @router.post("/tech_nodes", status_code=status.HTTP_200_OK)
    async def get_tech_nodes_route(
        inputs: TechNodesDataPullInput,
        data_pull_job_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
        user_name: str = Depends(get_user_name),
    ) -> dict:
        try:
            # initlialize stage
            stage = FDDataPullStages.TECH_NODE

            # initialize service
            fd_trace_service = FdTraceDataPullService(db_async_client=client)

            # fetch required records from DB
            data_pull_job_record: FdDataPullConfig = (
                await fd_trace_service.fetch_data_pull_job_record(
                    job_id=data_pull_job_id
                )
            )
            stage_config_record: FdDataPullJobConfig = (
                await fd_trace_service.fetch_stage_config_record(
                    data_pull_job_record=data_pull_job_record, stage=stage
                )
            )
            prev_stage_config_record: FdDataPullJobConfig = (
                await fd_trace_service.fetch_prev_stage_config_record(
                    data_pull_job_record=data_pull_job_record, stage=stage
                )
            )

            # initialize job config id
            job_config_id = data_pull_job_record.tech_node_stage_job_id

            # check if current stage can be triggered
            fd_trace_service.check_if_stage_can_be_triggered_async(
                stage=stage,
                data_pull_job_record=data_pull_job_record,
                prev_stage_config_record=prev_stage_config_record,
            )

            # check if it has same inputs as before
            if fd_trace_service.check_if_stage_triggered_with_same_inputs(
                new_inputs=inputs, existing_job_config=stage_config_record
            ):
                print("already ran with same inputs")
                return {}

            # submit job to worker
            task_id = await fd_trace_service.get_tech_nodes_async(
                inputs=inputs,
                job_config_id=job_config_id,
                job_config=stage_config_record,
            )

            # update previous job config record with selected values
            if (
                not isinstance(
                    prev_stage_config_record.stage_config, FacilitesDataPullConfig
                )
                or not prev_stage_config_record.stage_config.outputs
                or not prev_stage_config_record.stage_config.outputs.facilities
            ):
                raise ValueError("invalid previous stage config")
            if not inputs.facilities:
                raise ValueError("no facilities is selected")
            prev_stage_config_record.stage_config.outputs.facilities.selected_values = (
                inputs.facilities.selected_values
            )
            await fd_trace_service.update_prev_stage_selected_values_with_current_stage_inputs(
                stage=stage,
                data_pull_job_record=data_pull_job_record,
                prev_stage_config_record=prev_stage_config_record,
            )

            # update data_pull_job_id current stage as facilities
            await fd_trace_service.update_fd_data_pull_job_record_current_stage_async(
                job_id=data_pull_job_id,
                current_stage=stage,
                current_stage_status=DataCatalogStatus.RUNNING,
            )

            # submit this stage job to worker
            submit_data_pull_job(
                task_id=task_id,
                data_pull_job_id=data_pull_job_id,
                stage_job_id=job_config_id,
                user_name=user_name,
            )

            return {}

        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "tech_nodes_error", "message": str(e)},
            )

    @staticmethod
    @router.post("/design_ids", status_code=status.HTTP_200_OK)
    async def get_design_ids_route(
        inputs: DesignIdDataPullInput,
        data_pull_job_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
        user_name: str = Depends(get_user_name),
    ) -> dict:
        try:
            # initlialize stage
            stage = FDDataPullStages.DESIGN_ID

            # initialize service
            fd_trace_service = FdTraceDataPullService(db_async_client=client)

            # fetch required records from DB
            data_pull_job_record: FdDataPullConfig = (
                await fd_trace_service.fetch_data_pull_job_record(
                    job_id=data_pull_job_id
                )
            )
            stage_config_record: FdDataPullJobConfig = (
                await fd_trace_service.fetch_stage_config_record(
                    data_pull_job_record=data_pull_job_record, stage=stage
                )
            )
            prev_stage_config_record: FdDataPullJobConfig = (
                await fd_trace_service.fetch_prev_stage_config_record(
                    data_pull_job_record=data_pull_job_record, stage=stage
                )
            )

            # initialize job config id
            job_config_id = data_pull_job_record.design_ids_stage_job_id

            # check if current stage can be triggered
            fd_trace_service.check_if_stage_can_be_triggered_async(
                stage=stage,
                data_pull_job_record=data_pull_job_record,
                prev_stage_config_record=prev_stage_config_record,
            )

            # check if it has same inputs as before
            if fd_trace_service.check_if_stage_triggered_with_same_inputs(
                new_inputs=inputs, existing_job_config=stage_config_record
            ):
                print("already ran with same inputs")
                return {}

            # submit job to worker
            task_id = await fd_trace_service.get_desgin_ids(
                inputs=inputs,
                job_config_id=job_config_id,
                job_config=stage_config_record,
            )

            # update previous job config record with selected values
            if (
                not isinstance(
                    prev_stage_config_record.stage_config, TechNodeDataPullConfig
                )
                or not prev_stage_config_record.stage_config.outputs
                or not prev_stage_config_record.stage_config.outputs.tech_nodes
            ):
                raise ValueError("invalid previous stage config")
            if not inputs.tech_nodes:
                raise ValueError("no tech_nodes is selected")
            prev_stage_config_record.stage_config.outputs.tech_nodes.selected_values = (
                inputs.tech_nodes.selected_values
            )
            await fd_trace_service.update_prev_stage_selected_values_with_current_stage_inputs(
                stage=stage,
                data_pull_job_record=data_pull_job_record,
                prev_stage_config_record=prev_stage_config_record,
            )

            # update data_pull_job_id current stage as facilities
            await fd_trace_service.update_fd_data_pull_job_record_current_stage_async(
                job_id=data_pull_job_id,
                current_stage=stage,
                current_stage_status=DataCatalogStatus.RUNNING,
            )

            # submit this stage job to worker
            submit_data_pull_job(
                task_id=task_id,
                data_pull_job_id=data_pull_job_id,
                stage_job_id=job_config_id,
                user_name=user_name,
            )

            return {}

        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "design_ids_error", "message": str(e)},
            )

    @staticmethod
    @router.post("/traveler_ids", status_code=status.HTTP_200_OK)
    async def get_traveler_ids_route(
        inputs: TravelersIdDataPullInput,
        data_pull_job_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
        user_name: str = Depends(get_user_name),
    ) -> dict:
        try:
            # initlialize stage
            stage = FDDataPullStages.TRAVELER_ID

            # initialize service
            fd_trace_service = FdTraceDataPullService(db_async_client=client)

            # fetch required records from DB
            data_pull_job_record: FdDataPullConfig = (
                await fd_trace_service.fetch_data_pull_job_record(
                    job_id=data_pull_job_id
                )
            )
            stage_config_record: FdDataPullJobConfig = (
                await fd_trace_service.fetch_stage_config_record(
                    data_pull_job_record=data_pull_job_record, stage=stage
                )
            )
            prev_stage_config_record: FdDataPullJobConfig = (
                await fd_trace_service.fetch_prev_stage_config_record(
                    data_pull_job_record=data_pull_job_record, stage=stage
                )
            )

            # initialize job config id
            job_config_id = data_pull_job_record.traveler_id_step_stage_job_id

            # check if current stage can be triggered
            fd_trace_service.check_if_stage_can_be_triggered_async(
                stage=stage,
                data_pull_job_record=data_pull_job_record,
                prev_stage_config_record=prev_stage_config_record,
            )

            # check if it has same inputs as before
            if fd_trace_service.check_if_stage_triggered_with_same_inputs(
                new_inputs=inputs, existing_job_config=stage_config_record
            ):
                print("already ran with same inputs")
                return {}

            # submit job to worker
            task_id = await fd_trace_service.get_traveler_ids_async(
                inputs=inputs,
                job_config_id=job_config_id,
                job_config=stage_config_record,
            )

            # update previous job config record with selected values
            if (
                not isinstance(
                    prev_stage_config_record.stage_config, DesignIdDataPullConfig
                )
                or not prev_stage_config_record.stage_config.outputs
                or not prev_stage_config_record.stage_config.outputs.design_ids
            ):
                raise ValueError("invalid previous stage config")
            if not inputs.design_ids:
                raise ValueError("no design_ids is selected")
            prev_stage_config_record.stage_config.outputs.design_ids.selected_values = (
                inputs.design_ids.selected_values
            )
            await fd_trace_service.update_prev_stage_selected_values_with_current_stage_inputs(
                stage=stage,
                data_pull_job_record=data_pull_job_record,
                prev_stage_config_record=prev_stage_config_record,
            )

            # update data_pull_job_id current stage as facilities
            await fd_trace_service.update_fd_data_pull_job_record_current_stage_async(
                job_id=data_pull_job_id,
                current_stage=stage,
                current_stage_status=DataCatalogStatus.RUNNING,
            )

            # submit this stage job to worker
            submit_data_pull_job(
                task_id=task_id,
                data_pull_job_id=data_pull_job_id,
                stage_job_id=job_config_id,
                user_name=user_name,
            )

            return {}

        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "traveler_steps_error", "message": str(e)},
            )

    @staticmethod
    @router.post("/traveler_steps", status_code=status.HTTP_200_OK)
    async def get_travelers_step_route(
        inputs: TravelerStepDataPullInput,
        data_pull_job_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
        user_name: str = Depends(get_user_name),
    ) -> dict:
        try:
            # initlialize stage
            stage = FDDataPullStages.TRAVELER_STEP

            # initialize service
            fd_trace_service = FdTraceDataPullService(db_async_client=client)

            # fetch required records from DB
            data_pull_job_record: FdDataPullConfig = (
                await fd_trace_service.fetch_data_pull_job_record(
                    job_id=data_pull_job_id
                )
            )
            stage_config_record: FdDataPullJobConfig = (
                await fd_trace_service.fetch_stage_config_record(
                    data_pull_job_record=data_pull_job_record, stage=stage
                )
            )
            prev_stage_config_record: FdDataPullJobConfig = (
                await fd_trace_service.fetch_prev_stage_config_record(
                    data_pull_job_record=data_pull_job_record, stage=stage
                )
            )

            # initialize job config id
            job_config_id = data_pull_job_record.traveler_step_stage_job_id

            # check if current stage can be triggered
            fd_trace_service.check_if_stage_can_be_triggered_async(
                stage=stage,
                data_pull_job_record=data_pull_job_record,
                prev_stage_config_record=prev_stage_config_record,
            )

            # check if it has same inputs as before
            if fd_trace_service.check_if_stage_triggered_with_same_inputs(
                new_inputs=inputs, existing_job_config=stage_config_record
            ):
                print("already ran with same inputs")
                return {}

            # submit job to worker
            task_id = await fd_trace_service.get_travelers_steps_async(
                inputs=inputs,
                job_config_id=job_config_id,
                job_config=stage_config_record,
            )

            # update previous job config record with selected values
            if (
                not isinstance(
                    prev_stage_config_record.stage_config, TravelersIdDataPullConfig
                )
                or not prev_stage_config_record.stage_config.outputs
                or not prev_stage_config_record.stage_config.outputs.traveler_ids
            ):
                raise ValueError("invalid previous stage config")
            if not inputs.traveler_ids:
                raise ValueError("no traveler_ids is selected")
            prev_stage_config_record.stage_config.outputs.traveler_ids.selected_values = inputs.traveler_ids.selected_values
            await fd_trace_service.update_prev_stage_selected_values_with_current_stage_inputs(
                stage=stage,
                data_pull_job_record=data_pull_job_record,
                prev_stage_config_record=prev_stage_config_record,
            )

            # update data_pull_job_id current stage as facilities
            await fd_trace_service.update_fd_data_pull_job_record_current_stage_async(
                job_id=data_pull_job_id,
                current_stage=stage,
                current_stage_status=DataCatalogStatus.RUNNING,
            )

            # submit this stage job to worker
            submit_data_pull_job(
                task_id=task_id,
                data_pull_job_id=data_pull_job_id,
                stage_job_id=job_config_id,
                user_name=user_name,
            )

            return {}

        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "traveler_steps_error", "message": str(e)},
            )

    @staticmethod
    @router.post(
        "/probe_context",
        status_code=status.HTTP_200_OK,
        openapi_extra={"actions": Actions.DC_data_download.value},
    )
    async def get_probe_context_route(
        inputs: ProbeContextDataPullInput,
        data_pull_job_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
        user_name: str = Depends(get_user_name),
    ) -> dict:
        try:
            # initlialize stage
            stage = FDDataPullStages.PROBE_CONTEXT

            # initialize service
            fd_trace_service = FdTraceDataPullService(db_async_client=client)

            # fetch required records from DB
            data_pull_job_record: FdDataPullConfig = (
                await fd_trace_service.fetch_data_pull_job_record(
                    job_id=data_pull_job_id
                )
            )
            stage_config_record: FdDataPullJobConfig = (
                await fd_trace_service.fetch_stage_config_record(
                    data_pull_job_record=data_pull_job_record,
                    stage=stage,
                    ignore_last_run_level=True,
                )
            )

            if (
                data_pull_job_record.data_pull_status == DataCatalogStatus.RUNNING
                and data_pull_job_record.current_stage == stage
            ):
                raise Exception("Download in-progress")

            # initialize job config id
            job_config_id = data_pull_job_record.probe_context_job_id

            # check if it has same inputs as before
            if fd_trace_service.check_if_stage_triggered_with_same_inputs(
                new_inputs=inputs, existing_job_config=stage_config_record
            ):
                print("already ran with same inputs")
                return {}

            # submit job to worker
            task_id = await fd_trace_service.get_probe_context_async(
                inputs=inputs,
                job_config_id=job_config_id,
                job_config=stage_config_record,
            )

            # update data_pull_job_id current stage as facilities
            await fd_trace_service.update_fd_data_pull_job_record_current_stage_async(
                job_id=data_pull_job_id,
                current_stage=stage,
                current_stage_status=DataCatalogStatus.RUNNING,
            )

            # submit this stage job to worker
            submit_data_pull_job(
                task_id=task_id,
                data_pull_job_id=data_pull_job_id,
                stage_job_id=job_config_id,
                user_name=user_name,
            )

            return {}

        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "probe_context_error", "message": str(e)},
            )

    @staticmethod
    @router.post(
        "/probe_data_pull_no_token/{user_name}", status_code=status.HTTP_200_OK
    )
    async def get_probe_data_pull_route_no_token(
        inputs: ProbeDataPullInputs,
        data_pull_job_id: str,
        user_name: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> dict:
        return await FdTraceDataPullRoutes.get_probe_data_pull_route(
            inputs, data_pull_job_id, client, user_name, to_worker=False
        )

    @staticmethod
    @router.post("/probe_data_pull", status_code=status.HTTP_200_OK)
    async def get_probe_data_pull_route(
        inputs: ProbeDataPullInputs,
        data_pull_job_id: str,
        client: AsyncIOMotorClient = Depends(dependency=get_db_async),
        user_name: str = Depends(get_user_name),
        to_worker: bool = True,
    ) -> dict:
        try:
            # initlialize stage
            stage = FDDataPullStages.PROBE_DATA_PULL

            # initialize service
            fd_trace_service = FdTraceDataPullService(db_async_client=client)

            # fetch required records from DB
            data_pull_job_record: FdDataPullConfig = (
                await fd_trace_service.fetch_data_pull_job_record(
                    job_id=data_pull_job_id
                )
            )
            stage_config_record: FdDataPullJobConfig = (
                await fd_trace_service.fetch_stage_config_record(
                    data_pull_job_record=data_pull_job_record,
                    stage=stage,
                    ignore_last_run_level=True,
                )
            )

            if (
                data_pull_job_record.data_pull_status == DataCatalogStatus.RUNNING
                and data_pull_job_record.current_stage == stage
            ):
                raise Exception("Download in-progress")

            # initialize job config id
            job_config_id = data_pull_job_record.probe_data_pull_job_id

            # # check if it has same inputs as before
            # if fd_trace_service.check_if_stage_triggered_with_same_inputs(
            #     new_inputs=inputs, existing_job_config=stage_config_record
            # ):
            #     print("already ran with same inputs")
            #     return {}

            # submit job to worker
            task_id = await fd_trace_service.get_probe_data_pull_async(
                inputs=inputs,
                job_config_id=job_config_id,
                job_config=stage_config_record,
            )

            # update data_pull_job_id current stage as facilities
            await fd_trace_service.update_fd_data_pull_job_record_current_stage_async(
                job_id=data_pull_job_id,
                current_stage=stage,
                current_stage_status=DataCatalogStatus.RUNNING,
            )

            if to_worker:
                # submit this stage job to worker
                submit_data_pull_job(
                    task_id=task_id,
                    data_pull_job_id=data_pull_job_id,
                    stage_job_id=job_config_id,
                    user_name=user_name,
                )
                return {}
            else:
                return dict(
                    data_pull_job_id=data_pull_job_id,
                    stage_job_id=job_config_id,
                    user_name=user_name,
                )

        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "probe_data_pull_error", "message": str(e)},
            )

    @staticmethod
    @router.post("/fd_context", status_code=status.HTTP_200_OK)
    async def get_fd_context_route(
        inputs: FdContextDataPullInput,
        data_pull_job_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
        user_name: str = Depends(get_user_name),
    ) -> dict:
        try:
            # initlialize stage
            stage = FDDataPullStages.FD_CONTEXT

            # initialize service
            fd_trace_service = FdTraceDataPullService(db_async_client=client)

            # fetch required records from DB
            data_pull_job_record: FdDataPullConfig = (
                await fd_trace_service.fetch_data_pull_job_record(
                    job_id=data_pull_job_id
                )
            )
            stage_config_record: FdDataPullJobConfig = (
                await fd_trace_service.fetch_stage_config_record(
                    data_pull_job_record=data_pull_job_record, stage=stage
                )
            )
            prev_stage_config_record: FdDataPullJobConfig = (
                await fd_trace_service.fetch_prev_stage_config_record(
                    data_pull_job_record=data_pull_job_record, stage=stage
                )
            )

            # initialize job config id
            job_config_id = data_pull_job_record.fd_context_stage_job_id

            # check if current stage can be triggered
            fd_trace_service.check_if_stage_can_be_triggered_async(
                stage=stage,
                data_pull_job_record=data_pull_job_record,
                prev_stage_config_record=prev_stage_config_record,
            )

            # check if it has same inputs as before
            if fd_trace_service.check_if_stage_triggered_with_same_inputs(
                new_inputs=inputs, existing_job_config=stage_config_record
            ):
                print("already ran with same inputs")
                return {}

            # submit job to worker
            task_id = await fd_trace_service.get_fd_context_async(
                inputs=inputs,
                job_config_id=job_config_id,
                job_config=stage_config_record,
            )

            # update previous job config record with selected values
            if (
                not isinstance(
                    prev_stage_config_record.stage_config, TravelerStepDataPullConfig
                )
                or not prev_stage_config_record.stage_config.outputs
                or not prev_stage_config_record.stage_config.outputs.traveler_steps
            ):
                raise ValueError("invalid previous stage config")
            if not inputs.traveler_steps:
                raise ValueError("no traveler_steps is selected")
            prev_stage_config_record.stage_config.outputs.traveler_steps.selected_values = inputs.traveler_steps.selected_values
            await fd_trace_service.update_prev_stage_selected_values_with_current_stage_inputs(
                stage=stage,
                data_pull_job_record=data_pull_job_record,
                prev_stage_config_record=prev_stage_config_record,
            )

            # update data_pull_job_id current stage as facilities
            await fd_trace_service.update_fd_data_pull_job_record_current_stage_async(
                job_id=data_pull_job_id,
                current_stage=stage,
                current_stage_status=DataCatalogStatus.RUNNING,
            )

            # submit this stage job to worker
            submit_data_pull_job(
                task_id=task_id,
                data_pull_job_id=data_pull_job_id,
                stage_job_id=job_config_id,
                user_name=user_name,
            )

            return {}

        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "fd_context_error", "message": str(e)},
            )

    @staticmethod
    @router.post("/fd_context_new", status_code=status.HTTP_200_OK)
    async def get_fd_context_data(
        inputs: FdContextDataPullInput,
        data_pull_job_id: str,
        user_name: Optional[str] = None,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> dict:
        try:
            stage = FDDataPullStages.FD_CONTEXT
            fd_trace_service = FdTraceDataPullService(db_async_client=client)
            data_pull_job_record: FdDataPullConfig = (
                await fd_trace_service.fetch_data_pull_job_record(
                    job_id=data_pull_job_id
                )
            )
            stage_config_record: FdDataPullJobConfig = (
                await fd_trace_service.fetch_stage_config_record(
                    data_pull_job_record=data_pull_job_record, stage=stage
                )
            )
            job_config_id = data_pull_job_record.fd_context_stage_job_id
            task_id = await fd_trace_service.get_fd_context_async(
                inputs=inputs,
                job_config_id=job_config_id,
                job_config=stage_config_record,
            )
            await fd_trace_service.update_fd_data_pull_job_record_current_stage_async(
                job_id=data_pull_job_id,
                current_stage=stage,
                current_stage_status=DataCatalogStatus.RUNNING,
            )
            return dict(task_id=task_id,
                data_pull_job_id=data_pull_job_id,
                stage_job_id=job_config_id,
                user_name=user_name if user_name else "default")
        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "fd_context_error", "message": str(e)},
            )

    @staticmethod
    @router.post("/fd_sensors", status_code=status.HTTP_200_OK)
    async def get_fd_sensor_route(
        inputs: SensorsDataPullInput,
        data_pull_job_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
        user_name: str = Depends(get_user_name),
    ) -> dict:
        try:
            # initlialize stage
            stage = FDDataPullStages.FD_SENSOR

            # initialize service
            fd_trace_service = FdTraceDataPullService(db_async_client=client)

            # fetch required records from DB
            data_pull_job_record: FdDataPullConfig = (
                await fd_trace_service.fetch_data_pull_job_record(
                    job_id=data_pull_job_id
                )
            )
            stage_config_record: FdDataPullJobConfig = (
                await fd_trace_service.fetch_stage_config_record(
                    data_pull_job_record=data_pull_job_record, stage=stage
                )
            )
            prev_stage_config_record: FdDataPullJobConfig = (
                await fd_trace_service.fetch_prev_stage_config_record(
                    data_pull_job_record=data_pull_job_record, stage=stage
                )
            )

            # initialize job config id
            job_config_id = data_pull_job_record.sensors_stage_job_id

            # check if current stage can be triggered
            fd_trace_service.check_if_stage_can_be_triggered_async(
                stage=stage,
                data_pull_job_record=data_pull_job_record,
                prev_stage_config_record=prev_stage_config_record,
            )

            # check if it has same inputs as before
            if fd_trace_service.check_if_stage_triggered_with_same_inputs(
                new_inputs=inputs, existing_job_config=stage_config_record
            ):
                print("already ran with same inputs")
                return {}

            # submit job to worker
            task_id = await fd_trace_service.get_fd_sensors_async(
                inputs=inputs,
                job_config_id=job_config_id,
                job_config=stage_config_record,
            )

            # update previous job config record with selected values
            if (
                not isinstance(
                    prev_stage_config_record.stage_config, FdContextDataPullConfig
                )
                or not prev_stage_config_record.stage_config.outputs
                or not prev_stage_config_record.stage_config.outputs.fd_contexts
            ):
                raise ValueError("invalid previous stage config")
            if not inputs.fd_contexts:
                raise ValueError("no fd_contexts is selected")
            prev_stage_config_record.stage_config.outputs.fd_contexts.selected_values = inputs.fd_contexts.selected_values
            await fd_trace_service.update_prev_stage_selected_values_with_current_stage_inputs(
                stage=stage,
                data_pull_job_record=data_pull_job_record,
                prev_stage_config_record=prev_stage_config_record,
            )

            # update data_pull_job_id current stage as facilities
            await fd_trace_service.update_fd_data_pull_job_record_current_stage_async(
                job_id=data_pull_job_id,
                current_stage=stage,
                current_stage_status=DataCatalogStatus.RUNNING,
            )

            # submit this stage job to worker
            submit_data_pull_job(
                task_id=task_id,
                data_pull_job_id=data_pull_job_id,
                stage_job_id=job_config_id,
                user_name=user_name,
            )

            return {}

        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "fd_sensors_error", "message": str(e)},
            )

    @staticmethod
    @router.post("/fd_trace", status_code=status.HTTP_200_OK)
    async def get_fd_trace_route(
        inputs: FdTraceDataPullInput,
        data_pull_job_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
        user_name: str = Depends(get_user_name),
    ) -> dict:
        try:
            # initlialize stage
            stage = FDDataPullStages.FD_TRACE

            # initialize service
            fd_trace_service = FdTraceDataPullService(db_async_client=client)

            # fetch required records from DB
            data_pull_job_record: FdDataPullConfig = (
                await fd_trace_service.fetch_data_pull_job_record(
                    job_id=data_pull_job_id
                )
            )
            stage_config_record: FdDataPullJobConfig = (
                await fd_trace_service.fetch_stage_config_record(
                    data_pull_job_record=data_pull_job_record, stage=stage
                )
            )
            prev_stage_config_record: FdDataPullJobConfig = (
                await fd_trace_service.fetch_prev_stage_config_record(
                    data_pull_job_record=data_pull_job_record, stage=stage
                )
            )

            # initialize job config id
            job_config_id = data_pull_job_record.fd_trace_stage_job_id

            # check if current stage can be triggered
            fd_trace_service.check_if_stage_can_be_triggered_async(
                stage=stage,
                data_pull_job_record=data_pull_job_record,
                prev_stage_config_record=prev_stage_config_record,
            )

            # check if it has same inputs as before
            if fd_trace_service.check_if_stage_triggered_with_same_inputs(
                new_inputs=inputs, existing_job_config=stage_config_record
            ):
                print("already ran with same inputs")
                return {}

            # submit job to worker
            task_id = await fd_trace_service.get_fd_trace_async(
                inputs=inputs,
                job_config_id=job_config_id,
                job_config=stage_config_record,
            )

            # update previous job config record with selected values
            if (
                not isinstance(
                    prev_stage_config_record.stage_config, SensorsDataPullConfig
                )
                or not prev_stage_config_record.stage_config.outputs
                or not prev_stage_config_record.stage_config.outputs.sensors
            ):
                raise ValueError("invalid previous stage config")
            if not inputs.sensors:
                raise ValueError("no sensors is selected")
            prev_stage_config_record.stage_config.outputs.sensors.selected_values = (
                inputs.sensors.selected_values
            )
            await fd_trace_service.update_prev_stage_selected_values_with_current_stage_inputs(
                stage=stage,
                data_pull_job_record=data_pull_job_record,
                prev_stage_config_record=prev_stage_config_record,
            )

            # update data_pull_job_id current stage as facilities
            await fd_trace_service.update_fd_data_pull_job_record_current_stage_async(
                job_id=data_pull_job_id,
                current_stage=stage,
                current_stage_status=DataCatalogStatus.RUNNING,
            )

            # submit this stage job to worker
            submit_data_pull_job(
                task_id=task_id,
                data_pull_job_id=data_pull_job_id,
                stage_job_id=job_config_id,
                user_name=user_name,
            )

            return {}

        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "fd_trace_error", "message": str(e)},
            )

    @staticmethod
    @router.get("/traveler_steps")
    async def get_traveler_steps(path: Path) -> Dict[str, Dict[str, List[str]]]:
        df = pd.read_parquet(path)
        df["module_ids"] = df["traveler_steps"].str[:4]
        result = defaultdict(lambda: defaultdict(list))
        for (mfg_area, module_id), traveler_steps in (
            df.groupby(["mfg_areas", "module_ids"])["traveler_steps"]
            .apply(set)
            .to_dict()
            .items()
        ):
            result[mfg_area][module_id].extend(traveler_steps)
        return result  # type: ignore

    @staticmethod
    @router.post(
        "/upload_csv_file_convert_to_parquet", response_model=UploadCsvResponse
    )
    async def upload_csv_pareto_file(
        file: UploadFile = File(...),
        read_columns: bool = True,
        convert_to_parquet: bool = False,
    ) -> UploadCsvResponse:
        try:
            if file.filename is None:
                raise ValueError("filename not provided")
            file_extension = file.filename.split(".")[-1]

            unique_identifier = f"{uuid4()}"
            unique_filename = f"{unique_identifier}.{file_extension}"

            upload_folder = environment.tdam_upload_path / "uploaded_csv_files"
            upload_folder.mkdir(parents=True, exist_ok=True)

            # save gql file path
            uploaded_file_path = os.path.join(upload_folder, unique_filename)
            parquet_file_path = os.path.join(
                upload_folder, f"{unique_identifier}.parquet"
            )
            columns_file_path = os.path.join(
                upload_folder, f"{unique_identifier}_columns.parquet"
            )
            print(f"uploading file to {uploaded_file_path} location.")
            async with aiofiles.open(uploaded_file_path, "wb") as out_file:
                while content := await file.read(1024):  # Read in chunks
                    await out_file.write(content)
            if read_columns:
                if uploaded_file_path.endswith(".csv"):
                    try:
                        columns = pd.read_csv(
                            uploaded_file_path, nrows=0
                        ).columns.tolist()
                        pd.DataFrame({"COLUMNS": columns}).to_parquet(columns_file_path)
                        print(f"Column metadata written to {columns_file_path}")
                    except Exception as e:
                        print(f"Error processing CSV file: {e}")
                elif uploaded_file_path.endswith(".xls") or uploaded_file_path.endswith(
                    ".xlsx"
                ):  # or excel
                    get_excel_columns(uploaded_file_path).to_parquet(columns_file_path)

            if convert_to_parquet:
                raise Exception("Currently handling conversion async way")

            return UploadCsvResponse(
                uploaded_file_path=uploaded_file_path,
                columns_file_path=columns_file_path,
            )
        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @staticmethod
    @router.post(
        "/convert_gql_file_to_parquet", response_model=UC2SigmaGQLFileParsedContentFile
    )
    async def convert_gql_file_to_parquet(
        file: UploadFile = File(...),
    ) -> UC2SigmaGQLFileParsedContentFile:
        try:
            if file.filename is None:
                raise ValueError("filename not provided")
            file_extension = file.filename.split(".")[-1]

            unique_identifier = f"{uuid4()}"
            unique_filename = f"{unique_identifier}.{file_extension}"

            upload_folder = environment.tdam_upload_path / "uploaded_gql_files"
            upload_folder.mkdir(parents=True, exist_ok=True)

            # save gql file path
            gql_file_path = os.path.join(upload_folder, unique_filename)
            parquet_file_path = os.path.join(
                upload_folder, f"{unique_identifier}.parquet"
            )
            gql_structure_file_path = os.path.join(
                upload_folder, f"{unique_identifier}_structured.parquet"
            )
            print(f"uploading file to {gql_file_path} location.")
            async with aiofiles.open(gql_file_path, "wb") as out_file:
                while content := await file.read(1024):  # Read in chunks
                    await out_file.write(content)

            fd = open(gql_file_path, "r")
            sql_file = fd.read()
            fd.close()
            data = sql_file.split("\n")

            # TODO: move this code to utils
            def get_structured_dataframe_from_gql(x):
                tables = []
                step_names = []
                parameter_names = []

                itr = [i for i in x if i.rstrip("").lstrip("") != ""][1:]
                for i in itr:
                    req = i.split("\x7f")
                    table = None
                    if req[1] == "Wafer":
                        table = "idl_sigma_wafer_summary"
                    elif (req[1] == "Run") or (req[1] == "RunWafer"):
                        table = "idl_sigma_run_summary"
                    elif req[1] == "Point":
                        table = "idl_sigma_point"
                    elif req[1] == "Measurement":
                        table = "idl_sigma_measurement_summary"
                    step_name = req[2]
                    if req[3] == "Run Complete Datetime":
                        parameter_name = "RUN_COMPLETE_DATETIME"
                    elif req[3] == "EquipmentId":
                        parameter_name = "EQUIPMENT_ID"
                    else:
                        parameter_name = req[3]
                    tables.append(table)
                    step_names.append(step_name)
                    parameter_names.append(parameter_name)

                data = {
                    "table": tables,
                    "step_names": step_names,
                    "parameter_names": parameter_names,
                }
                data_structure = pd.DataFrame(data)

                return data_structure

            def read_gql_as_dataframe(x):
                itr = [i for i in x if i.rstrip("").lstrip("") != ""][1:]
                sigma_run_parameters = []
                sigma_wafer_parameters = []
                sigma_measurement_steps = []
                sigma_measurement_parameters = []
                sigma_point_steps = []
                sigma_point_parameters = []

                for i in itr:
                    req = i.split("\x7f")
                    if "Sigma" in req[0]:
                        if req[1] == "Measurement":
                            if req[2] not in sigma_measurement_steps:
                                sigma_measurement_steps.append(req[2])
                            if req[3] not in sigma_measurement_parameters:
                                sigma_measurement_parameters.append(req[3])
                        elif req[1] == "Point":
                            if req[2] not in sigma_point_steps:
                                sigma_point_steps.append(req[2])
                            if req[3] not in sigma_point_parameters:
                                sigma_point_parameters.append(req[3])
                        elif (req[1] == "Run") or (req[1] == "RunWafer"):
                            if req[-2] not in sigma_run_parameters:
                                sigma_run_parameters.append(req[-2])
                        elif req[1] == "Wafer":
                            if req[-2] not in sigma_wafer_parameters:
                                sigma_wafer_parameters.append(req[-2])

                df_data = {
                    "run_parameters": sigma_run_parameters,
                    "wafer_parameters": sigma_wafer_parameters,
                    "measurement_steps": sigma_measurement_steps,
                    "measurement_parameters": sigma_measurement_parameters,
                    "point_steps": sigma_point_steps,
                    "point_parameters": sigma_point_parameters,
                }

                # Convert the dictionary to a DataFrame
                return pd.DataFrame({k: pd.Series(v) for k, v in df_data.items()})

            df = read_gql_as_dataframe(data)
            df.to_parquet(parquet_file_path)

            df = get_structured_dataframe_from_gql(data)
            df.to_parquet(gql_structure_file_path)

            return UC2SigmaGQLFileParsedContentFile(
                parquet_file_path=parquet_file_path,
                gql_file_path=gql_file_path,
                gql_structure_file_path=gql_structure_file_path,
            )
        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @staticmethod
    @router.post("/save_hl_dc_inputs", status_code=status.HTTP_200_OK)
    async def save_high_level_data_catalog_items(
        inputs: FdContextDataPullInput,
        data_pull_job_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
        user_name: str = Depends(get_user_name),
    ):
        try:
            stage = FDDataPullStages.SAVE_HIGH_LEVEL_DC_DETAILS
            fd_trace_service = FdTraceDataPullService(db_async_client=client)

            # fetch required records from DB
            data_pull_job_record: FdDataPullConfig = (
                await fd_trace_service.fetch_data_pull_job_record(
                    job_id=data_pull_job_id
                )
            )
            stage_config_record: FdDataPullJobConfig = (
                await fd_trace_service.fetch_stage_config_record(
                    data_pull_job_record=data_pull_job_record, stage=stage
                )
            )
            # NOTE: Ignoring the previous stage config [hldc items need to be saved w/wo traveler steps/traveler ids]
            # prev_stage_config_record: FdDataPullJobConfig = (
            #     await fd_trace_service.fetch_prev_stage_config_record(
            #         data_pull_job_record=data_pull_job_record, stage=stage
            #     )
            # )

            # initialize job config id
            job_config_id = data_pull_job_record.save_high_level_dc_details_job_id

            # if (
            #     not isinstance(
            #         prev_stage_config_record.stage_config, TravelerStepDataPullConfig
            #     )
            #     or not prev_stage_config_record.stage_config.outputs
            #     or not prev_stage_config_record.stage_config.outputs.traveler_steps
            # ):
            #     raise ValueError("invalid previous stage config")
            # if not inputs.traveler_steps:
            #     raise ValueError("no traveler_steps is selected")
            # prev_stage_config_record.stage_config.outputs.traveler_steps.selected_values = (
            #     inputs.traveler_steps.selected_values
            # )
            # await fd_trace_service.update_prev_stage_selected_values_with_current_stage_inputs(
            #     stage=stage,
            #     data_pull_job_record=data_pull_job_record,
            #     prev_stage_config_record=prev_stage_config_record,
            # )

            # updates inputs in new stage
            await fd_trace_service.update_fd_data_pull_job_details_async(
                inputs=inputs,
                job_config_id=job_config_id,
                job_config=stage_config_record,
            )
            return "saved"
        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "saving high level datacatalog error",
                    "message": str(e),
                },
            )

    @staticmethod
    @router.post("/save_lot_wafer_inputs", status_code=status.HTTP_200_OK)
    async def save_lot_wafer_datacatalog_items(
        inputs: LotWaferInput,
        data_pull_job_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
        user_name: str = Depends(get_user_name),
    ):
        try:
            stage = FDDataPullStages.LOT_WAFER_SAVE
            fd_trace_service = FdTraceDataPullService(db_async_client=client)

            # fetch required records from DB
            data_pull_job_record: FdDataPullConfig = (
                await fd_trace_service.fetch_data_pull_job_record(
                    job_id=data_pull_job_id
                )
            )
            stage_config_record: FdDataPullJobConfig = (
                await fd_trace_service.fetch_stage_config_record(
                    data_pull_job_record=data_pull_job_record, stage=stage
                )
            )
            prev_stage_config_record: FdDataPullJobConfig = (
                await fd_trace_service.fetch_prev_stage_config_record(
                    data_pull_job_record=data_pull_job_record, stage=stage
                )
            )

            # initialize job config id
            job_config_id = data_pull_job_record.lot_wafer_stage_job_id

            await fd_trace_service.update_prev_stage_selected_values_with_current_stage_inputs(
                stage=stage,
                data_pull_job_record=data_pull_job_record,
                prev_stage_config_record=prev_stage_config_record,
            )

            # updates inputs in new stage
            await fd_trace_service.update_fd_data_pull_job_details_async(
                inputs=inputs,
                job_config_id=job_config_id,
                job_config=stage_config_record,
            )
            return "saved"
        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "saving high level datacatalog error",
                    "message": str(e),
                },
            )

    @staticmethod
    @router.post("/lot_ids", status_code=status.HTTP_200_OK)
    async def get_lot_ids(
        inputs: LotIdsDataPullInput,
        data_pull_job_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
        user_name: str = Depends(get_user_name),
    ) -> dict:
        try:
            # initlialize stage
            stage = FDDataPullStages.LOT_ID

            # initialize service
            fd_trace_service = FdTraceDataPullService(db_async_client=client)

            # fetch required records from DB
            data_pull_job_record: FdDataPullConfig = (
                await fd_trace_service.fetch_data_pull_job_record(
                    job_id=data_pull_job_id
                )
            )
            stage_config_record: FdDataPullJobConfig = (
                await fd_trace_service.fetch_stage_config_record(
                    data_pull_job_record=data_pull_job_record, stage=stage
                )
            )
            prev_stage_config_record: FdDataPullJobConfig = (
                await fd_trace_service.fetch_prev_stage_config_record(
                    data_pull_job_record=data_pull_job_record, stage=stage
                )
            )

            # initialize job config id
            job_config_id = data_pull_job_record.lot_ids_stage_job_id

            # # check if current stage can be triggered
            # fd_trace_service.check_if_stage_can_be_triggered_async(stage=stage, data_pull_job_record=data_pull_job_record, prev_stage_config_record=prev_stage_config_record)

            # # check if it has same inputs as before
            # if fd_trace_service.check_if_stage_triggered_with_same_inputs(new_inputs=inputs, existing_job_config=stage_config_record):
            #     print("already ran with same inputs")
            #     return {}

            # submit job to worker
            task_id = await fd_trace_service.get_lot_ids_async(
                inputs=inputs,
                job_config_id=job_config_id,
                job_config=stage_config_record,
            )

            # update previous job config record with selected values
            if (
                not isinstance(
                    prev_stage_config_record.stage_config, TravelerStepDataPullConfig
                )
                or not prev_stage_config_record.stage_config.outputs
                or not prev_stage_config_record.stage_config.outputs.traveler_steps
            ):
                raise ValueError("invalid previous stage config")
            if not inputs.traveler_steps:
                raise ValueError("no traveler_steps is selected")
            prev_stage_config_record.stage_config.outputs.traveler_steps.selected_values = inputs.traveler_steps.selected_values
            await fd_trace_service.update_prev_stage_selected_values_with_current_stage_inputs(
                stage=stage,
                data_pull_job_record=data_pull_job_record,
                prev_stage_config_record=prev_stage_config_record,
            )

            # update data_pull_job_id current stage as facilities
            await fd_trace_service.update_fd_data_pull_job_record_current_stage_async(
                job_id=data_pull_job_id,
                current_stage=stage,
                current_stage_status=DataCatalogStatus.RUNNING,
            )

            # submit this stage job to worker
            submit_data_pull_job(
                task_id=task_id,
                data_pull_job_id=data_pull_job_id,
                stage_job_id=job_config_id,
                user_name=user_name,
            )

            return {}

        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "tech_nodes_error", "message": str(e)},
            )

    @staticmethod
    @router.post("/wafer_ids", status_code=status.HTTP_200_OK)
    async def get_wafer_ids(
        inputs: WaferIdsDataPullInput,
        data_pull_job_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
        user_name: str = Depends(get_user_name),
    ) -> dict:
        try:
            # initlialize stage
            stage = FDDataPullStages.WAFER_ID

            # initialize service
            fd_trace_service = FdTraceDataPullService(db_async_client=client)

            # fetch required records from DB
            data_pull_job_record: FdDataPullConfig = (
                await fd_trace_service.fetch_data_pull_job_record(
                    job_id=data_pull_job_id
                )
            )
            stage_config_record: FdDataPullJobConfig = (
                await fd_trace_service.fetch_stage_config_record(
                    data_pull_job_record=data_pull_job_record, stage=stage
                )
            )
            prev_stage_config_record: FdDataPullJobConfig = (
                await fd_trace_service.fetch_prev_stage_config_record(
                    data_pull_job_record=data_pull_job_record, stage=stage
                )
            )

            # initialize job config id
            job_config_id = data_pull_job_record.wafer_ids_stage_job_id

            # # check if current stage can be triggered
            # fd_trace_service.check_if_stage_can_be_triggered_async(stage=stage, data_pull_job_record=data_pull_job_record, prev_stage_config_record=prev_stage_config_record)

            # # check if it has same inputs as before
            # if fd_trace_service.check_if_stage_triggered_with_same_inputs(new_inputs=inputs, existing_job_config=stage_config_record):
            #     print("already ran with same inputs")
            #     return {}

            # submit job to worker
            task_id = await fd_trace_service.get_wafer_ids_async(
                inputs=inputs,
                job_config_id=job_config_id,
                job_config=stage_config_record,
            )

            # update previous job config record with selected values
            if (
                not isinstance(
                    prev_stage_config_record.stage_config, LotIdsDataPullConfig
                )
                or not prev_stage_config_record.stage_config.outputs
                or not prev_stage_config_record.stage_config.outputs.lot_ids
            ):
                raise ValueError("invalid previous stage config")
            if not inputs.lot_ids:
                raise ValueError("no lot_id is selected")
            prev_stage_config_record.stage_config.outputs.lot_ids.selected_values = (
                inputs.lot_ids.selected_values
            )
            await fd_trace_service.update_prev_stage_selected_values_with_current_stage_inputs(
                stage=stage,
                data_pull_job_record=data_pull_job_record,
                prev_stage_config_record=prev_stage_config_record,
            )

            # update data_pull_job_id current stage as facilities
            await fd_trace_service.update_fd_data_pull_job_record_current_stage_async(
                job_id=data_pull_job_id,
                current_stage=stage,
                current_stage_status=DataCatalogStatus.RUNNING,
            )

            # submit this stage job to worker
            submit_data_pull_job(
                task_id=task_id,
                data_pull_job_id=data_pull_job_id,
                stage_job_id=job_config_id,
                user_name=user_name,
            )

            return {}

        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "tech_nodes_error", "message": str(e)},
            )

    @staticmethod
    @router.post("/uc2_sigma_dropdowns_files", status_code=status.HTTP_200_OK)
    async def generate_sigma_dropdowns_files(
        inputs: FdContextDataPullInput,
        data_pull_job_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
        user_name: str = Depends(get_user_name),
    ) -> UC2SigmaSteps:
        if environment.dev_mode:
            return UC2SigmaSteps(
                run_parameters=DataPullResult.model_validate(
                    dict(file_path=DUMMY_FILES["uc2_sigma"])
                ),
                measurement_steps=DataPullResult.model_validate(
                    dict(file_path=DUMMY_FILES["uc2_sigma"])
                ),
                point_steps=DataPullResult.model_validate(
                    dict(file_path=DUMMY_FILES["uc2_sigma"])
                ),
            )

        # if result folder doesnt exist create
        result_folder = (
            Path(
                environment.tdam_datacatalog_databrick_session_path_format.format(
                    data_pull_job_id
                )
            )
            / "uc2/sigma"
        )
        result_folder.mkdir(exist_ok=True, parents=True)

        measurement_steps_file = FdTraceDataPullService.generate_measurement_steps(
            inputs, result_folder
        )
        point_steps_file = FdTraceDataPullService.generate_point_steps(
            inputs, result_folder
        )
        run_parameters_file = FdTraceDataPullService.generate_run_parameters(
            inputs, result_folder
        )

        return UC2SigmaSteps(
            run_parameters=DataPullResult.model_validate(
                dict(file_path=run_parameters_file)
            ),
            measurement_steps=DataPullResult.model_validate(
                dict(file_path=measurement_steps_file)
            ),
            point_steps=DataPullResult.model_validate(dict(file_path=point_steps_file)),
        )

    @staticmethod
    @router.post(
        "/uc2_sigma_fetch_based_on_measurement_steps", status_code=status.HTTP_200_OK
    )
    async def uc2_sigma_fetch_based_on_measurement_steps(
        inputs: UC2SigmaMeasurementParametersFetchInput,
        data_pull_job_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
        user_name: str = Depends(get_user_name),
    ) -> UC2SigmaMeasurementStepsDependentParameters:
        if environment.dev_mode:
            return UC2SigmaMeasurementStepsDependentParameters(
                wafer_parameters=DataPullResult.model_validate(
                    dict(file_path=DUMMY_FILES["uc2_sigma"])
                ),
                measurement_parameters=DataPullResult.model_validate(
                    dict(file_path=DUMMY_FILES["uc2_sigma"])
                ),
            )
        # if result folder doesnt exist create
        result_folder = (
            Path(
                environment.tdam_datacatalog_databrick_session_path_format.format(
                    data_pull_job_id
                )
            )
            / "uc2/sigma"
        )
        result_folder.mkdir(exist_ok=True, parents=True)
        measurement_parameters_file = (
            FdTraceDataPullService.generate_measurement_parameters(
                inputs, result_folder
            )
        )
        wafer_parameters_file = FdTraceDataPullService.generate_wafer_parameters(
            inputs, result_folder
        )
        return UC2SigmaMeasurementStepsDependentParameters(
            wafer_parameters=DataPullResult.model_validate(
                dict(file_path=wafer_parameters_file)
            ),
            measurement_parameters=DataPullResult.model_validate(
                dict(file_path=measurement_parameters_file)
            ),
        )

    @staticmethod
    @router.post(
        "/uc2_sigma_fetch_based_on_point_steps", status_code=status.HTTP_200_OK
    )
    async def uc2_sigma_fetch_based_on_point_steps(
        inputs: UC2SigmaMeasurementParametersFetchInput,
        data_pull_job_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
        user_name: str = Depends(get_user_name),
    ) -> UC2SigmaPointParameters:
        if environment.dev_mode:
            return UC2SigmaPointParameters(
                point_parameters=DataPullResult.model_validate(
                    dict(file_path=DUMMY_FILES["uc2_sigma"])
                )
            )

        # if result folder doesnt exist create
        result_folder = (
            Path(
                environment.tdam_datacatalog_databrick_session_path_format.format(
                    data_pull_job_id
                )
            )
            / "uc2/sigma"
        )
        result_folder.mkdir(exist_ok=True, parents=True)
        point_parameters_file = FdTraceDataPullService.generate_point_parameters(
            inputs, result_folder
        )
        return UC2SigmaPointParameters(
            point_parameters=DataPullResult.model_validate(
                dict(file_path=point_parameters_file)
            )
        )

    @staticmethod
    @router.post("/uc2_sigma_stage_job", status_code=status.HTTP_201_CREATED)
    async def uc2_sigma_stage_job(
        inputs: UC2SigmaDataPullInput,
        data_pull_job_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
        user_name: str = Depends(get_user_name),
    ) -> dict:
        try:
            # initlialize stage
            stage = FDDataPullStages.UC2_SIGMA_DATA

            # initialize service
            fd_trace_service = FdTraceDataPullService(db_async_client=client)

            # fetch required records from DB
            data_pull_job_record: FdDataPullConfig = (
                await fd_trace_service.fetch_data_pull_job_record(
                    job_id=data_pull_job_id
                )
            )
            stage_config_record: FdDataPullJobConfig = (
                await fd_trace_service.fetch_stage_config_record(
                    data_pull_job_record=data_pull_job_record, stage=stage
                )
            )
            # todo: will call prev stage config record later
            # prev_stage_config_record: FdDataPullJobConfig = await fd_trace_service.fetch_prev_stage_config_record(
            #     data_pull_job_record=data_pull_job_record, stage=stage)

            # initialize job config id
            job_config_id = data_pull_job_record.uc2_sigma_job_id

            # # check if current stage can be triggered
            # fd_trace_service.check_if_stage_can_be_triggered_async(stage=stage, data_pull_job_record=data_pull_job_record, prev_stage_config_record=prev_stage_config_record)

            # # check if it has same inputs as before
            # if fd_trace_service.check_if_stage_triggered_with_same_inputs(new_inputs=inputs, existing_job_config=stage_config_record):
            #     print("already ran with same inputs")
            #     return {}

            # submit job to worker
            task_id = await fd_trace_service.get_uc2_sigma_data_task_id_async(
                inputs=inputs,
                job_config_id=job_config_id,
                job_config=stage_config_record,
            )

            # update previous job config record with selected values
            # prev_stage_config_record.stage_config.outputs.traveler_steps.selected_values = inputs.traveler_steps.selected_values
            # await fd_trace_service.update_prev_stage_selected_values_with_current_stage_inputs(stage=stage, data_pull_job_record=data_pull_job_record, prev_stage_config_record=prev_stage_config_record)

            # update data_pull_job_id current stage as facilities
            await fd_trace_service.update_fd_data_pull_job_record_current_stage_async(
                job_id=data_pull_job_id,
                current_stage=stage,
                current_stage_status=DataCatalogStatus.RUNNING,
            )

            # submit this stage job to worker
            submit_data_pull_job(
                task_id=task_id,
                data_pull_job_id=data_pull_job_id,
                stage_job_id=job_config_id,
                user_name=user_name,
            )

            return {}

        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "tech_nodes_error", "message": str(e)},
            )

    @staticmethod
    @router.post(
        "/sigma_data_pull_no_token/{user_name}", status_code=status.HTTP_200_OK
    )
    async def get_sigma_data_pull_route_no_token(
        inputs: UC3SigmaInput,
        data_pull_job_id: str,
        user_name: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> dict:
        return await FdTraceDataPullRoutes.uc3_sigma_stage_job(
            inputs, data_pull_job_id, client, user_name, False
        )

    @staticmethod
    @router.post(
        "/uc3_sigma_stage_job",
        status_code=status.HTTP_201_CREATED,
        openapi_extra={"actions": Actions.DC_data_download.value},
    )
    async def uc3_sigma_stage_job(
        inputs: UC3SigmaInput,
        data_pull_job_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
        user_name: str = Depends(get_user_name),
        to_worker: bool = True,
    ) -> dict:
        try:
            stage = FDDataPullStages.UC3_SIGMA_DATA
            fd_trace_service = FdTraceDataPullService(db_async_client=client)
            data_pull_job_record: FdDataPullConfig = (
                await fd_trace_service.fetch_data_pull_job_record(
                    job_id=data_pull_job_id
                )
            )
            stage_config_record: FdDataPullJobConfig = (
                await fd_trace_service.fetch_stage_config_record(
                    data_pull_job_record=data_pull_job_record, stage=stage
                )
            )
            # todo: will call prev stage config record later
            # prev_stage_config_record: FdDataPullJobConfig = await fd_trace_service.fetch_prev_stage_config_record(
            #     data_pull_job_record=data_pull_job_record, stage=stage)

            job_config_id = data_pull_job_record.uc3_sigma_job_id
            task_id = await fd_trace_service.get_uc3_sigma_data_task_id_async(
                inputs=inputs,
                job_config_id=job_config_id,
                job_config=stage_config_record,
            )

            # update previous job config record with selected values
            # prev_stage_config_record.stage_config.outputs.traveler_steps.selected_values = inputs.traveler_steps.selected_values
            # await fd_trace_service.update_prev_stage_selected_values_with_current_stage_inputs(stage=stage, data_pull_job_record=data_pull_job_record, prev_stage_config_record=prev_stage_config_record)

            # update data_pull_job_id current stage as facilities
            await fd_trace_service.update_fd_data_pull_job_record_current_stage_async(
                job_id=data_pull_job_id,
                current_stage=stage,
                current_stage_status=DataCatalogStatus.RUNNING,
            )

            if to_worker:
                # submit this stage job to worker
                submit_data_pull_job(
                    task_id=task_id,
                    data_pull_job_id=data_pull_job_id,
                    stage_job_id=job_config_id,
                    user_name=user_name,
                )
                return {}
            else:
                return dict(
                    data_pull_job_id=data_pull_job_id,
                    stage_job_id=job_config_id,
                    user_name=user_name,
                )

        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "tech_nodes_error", "message": str(e)},
            )

    @staticmethod
    @router.post("/generate_final_data_aggregate_context")
    async def generate_final_data_aggregate_context(
        inputs: FinalDataAggregateContextInput,
        data_pull_job_id: str,
    ) -> FinalDataAggregateContextOutput:
        result_path = (
            environment.tdam_upload_path
            / data_pull_job_id
            / "uc2"
            / "fd_aggregate"
            / f"final_data_aggregate_context_{datetime.now().timestamp}.parquet"
        )
        if result_path.exists():
            result_path.unlink()
        result_path.parent.mkdir(exist_ok=True, parents=True)

        if not inputs.facilities or not inputs.facilities.selected_values:
            raise ValueError("no facility not selected")
        if len(inputs.facilities.selected_values) > 1:
            raise ValueError("only one facility is supported")
        if not inputs.design_ids or not inputs.design_ids.selected_values:
            raise ValueError("no design_id is selected")
        if len(inputs.design_ids.selected_values) > 1:
            raise ValueError("only one design_id is supported")
        if not inputs.traveler_steps or not inputs.traveler_steps.selected_values:
            raise ValueError("no traveler_steps are selected")

        ldf = FdTraceDataPullService.generate_aggeragated_context(
            facility=inputs.facilities.selected_values[0],
            design_id=inputs.design_ids.selected_values[0],
            traveler_steps=inputs.traveler_steps.selected_values,
            start_date=inputs.start_date,
            end_date=inputs.end_date,
        )

        df = await ldf.collect_async()
        df.write_parquet(result_path)

        return FinalDataAggregateContextOutput(
            recipes=DataPullResult.model_validate(dict(file_path=result_path)),
            tool_ids=DataPullResult.model_validate(dict(file_path=result_path)),
            step_ids=DataPullResult.model_validate(dict(file_path=result_path)),
            sensors=DataPullResult.model_validate(dict(file_path=result_path)),
        )

    @staticmethod
    @router.post("/final_data_aggregate", status_code=status.HTTP_201_CREATED)
    async def generate_final_data_aggregate(
        inputs: FinalDataAggregateInput,
        data_pull_job_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
        user_name: str = Depends(get_user_name),
    ) -> dict:
        try:
            # initlialize stage
            stage = FDDataPullStages.FINAL_DATA_AGGREGATE

            # initialize service
            fd_trace_service = FdTraceDataPullService(db_async_client=client)

            # fetch required records from DB
            data_pull_job_record: FdDataPullConfig = (
                await fd_trace_service.fetch_data_pull_job_record(
                    job_id=data_pull_job_id
                )
            )
            stage_config_record: FdDataPullJobConfig = (
                await fd_trace_service.fetch_stage_config_record(
                    data_pull_job_record=data_pull_job_record, stage=stage
                )
            )
            prev_stage_config_record: FdDataPullJobConfig = (
                await fd_trace_service.fetch_prev_stage_config_record(
                    data_pull_job_record=data_pull_job_record, stage=stage
                )
            )

            # initialize job config id
            job_config_id = data_pull_job_record.final_data_aggregate_stage_job_id

            # # check if current stage can be triggered
            # fd_trace_service.check_if_stage_can_be_triggered_async(stage=stage, data_pull_job_record=data_pull_job_record, prev_stage_config_record=prev_stage_config_record)

            # # check if it has same inputs as before
            # if fd_trace_service.check_if_stage_triggered_with_same_inputs(new_inputs=inputs, existing_job_config=stage_config_record):
            #     print("already ran with same inputs")
            #     return {}

            # submit job to worker
            task_id = await fd_trace_service.get_final_data_aggregate_async(
                inputs=inputs,
                job_config_id=job_config_id,
                job_config=stage_config_record,
            )

            # update previous job config record with selected values
            # prev_stage_config_record.stage_config.outputs.traveler_steps.selected_values = inputs.traveler_steps.selected_values
            # await fd_trace_service.update_prev_stage_selected_values_with_current_stage_inputs(stage=stage, data_pull_job_record=data_pull_job_record, prev_stage_config_record=prev_stage_config_record)

            # update data_pull_job_id current stage as facilities
            await fd_trace_service.update_fd_data_pull_job_record_current_stage_async(
                job_id=data_pull_job_id,
                current_stage=stage,
                current_stage_status=DataCatalogStatus.RUNNING,
            )

            # submit this stage job to worker
            submit_data_pull_job(
                task_id=task_id,
                data_pull_job_id=data_pull_job_id,
                stage_job_id=job_config_id,
                user_name=user_name,
            )

            return {}

        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "tech_nodes_error", "message": str(e)},
            )

    @staticmethod
    @router.post("/uc3_fd_context_apply_filters", status_code=status.HTTP_200_OK)
    async def apply_filters_stage_uc3_fd_context(
        inputs: UC3FDContextApplyFiltersInput,
        data_pull_job_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
        user_name: str = Depends(get_user_name),
    ) -> dict:
        try:
            # initlialize stage
            stage = FDDataPullStages.UC3_FD_CONTEXT_APPLY_FILTERS

            # initialize service
            fd_trace_service = FdTraceDataPullService(db_async_client=client)

            # fetch required records from DB
            data_pull_job_record: FdDataPullConfig = (
                await fd_trace_service.fetch_data_pull_job_record(
                    job_id=data_pull_job_id
                )
            )
            stage_config_record: FdDataPullJobConfig = (
                await fd_trace_service.fetch_stage_config_record(
                    data_pull_job_record=data_pull_job_record, stage=stage
                )
            )
            prev_stage_config_record: FdDataPullJobConfig = (
                await fd_trace_service.fetch_prev_stage_config_record(
                    data_pull_job_record=data_pull_job_record, stage=stage
                )
            )

            # initialize job config id
            job_config_id = data_pull_job_record.uc3_fd_context_apply_filters_job_id

            # # check if current stage can be triggered
            # fd_trace_service.check_if_stage_can_be_triggered_async(stage=stage, data_pull_job_record=data_pull_job_record, prev_stage_config_record=prev_stage_config_record)

            # # check if it has same inputs as before
            # if fd_trace_service.check_if_stage_triggered_with_same_inputs(new_inputs=inputs, existing_job_config=stage_config_record):
            #     print("already ran with same inputs")
            #     return {}

            # submit job to worker
            task_id = await fd_trace_service.get_aggregated_results_async(
                inputs=inputs,
                job_config_id=job_config_id,
                job_config=stage_config_record,
            )

            # update previous job config record with selected values
            # prev_stage_config_record.stage_config.outputs.lot_ids.selected_values = inputs.lot_ids.selected_values
            # await fd_trace_service.update_prev_stage_selected_values_with_current_stage_inputs(stage=stage,
            #                                                                                    data_pull_job_record=data_pull_job_record,
            #                                                                                    prev_stage_config_record=prev_stage_config_record)

            # update data_pull_job_id current stage as facilities
            await fd_trace_service.update_fd_data_pull_job_record_current_stage_async(
                job_id=data_pull_job_id,
                current_stage=stage,
                current_stage_status=DataCatalogStatus.RUNNING,
            )

            # submit this stage job to worker
            submit_data_processing_job(
                task_id=task_id,
                data_pull_job_id=data_pull_job_id,
                stage_job_id=job_config_id,
                user_name=user_name,
            )

            return {}

        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "uc3_fd_context_aggregated_results ",
                    "message": str(e),
                },
            )

    @staticmethod
    @router.post(
        "/add_to_dataset/{projectId}",
        response_model=DatasetUploadResponse,
    )
    async def add_parquet_file_to_dataset(
        projectId: str,
        name: str,
        description: str,
        file: FilePath,
        destination_folder: str = "",
        user_id: str = Depends(get_user_id_from_token),
        user_email_prefix: str = Depends(get_user_name),
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> DatasetUploadResponse:
        # needed for creating dataset with spl path permissions. #TODO: create a generalised API for creating datasets from tdam spock share
        try:
            file_extension = file.suffix.lstrip(".")
            unique_id = f"{uuid4()}"
            unique_filename = f"{unique_id}.{file_extension}"
            print(f"Generated unique file name - {unique_filename} - {user_id}")
            upload_folder = (
                destination_folder
                if destination_folder != ""
                else environment.datasets_folder
            )
            # TODO: create sub function, this below code repeated 2 times in just this method
            file_path = os.path.join(upload_folder, unique_filename)
            original_umask = None
            try:
                # this is needed as this containers are not running as root but others are
                original_umask = os.umask(0)
                os.makedirs(upload_folder, exist_ok=True)
                shutil.copy(file, file_path)
                os.umask(original_umask)
            except Exception as e:
                if original_umask:
                    os.umask(original_umask)
                raise Exception(f"Error while copying file with umasks: {e}") from e

            datasets_service = DatasetsService(db_async_client=client)
            metadata = DatasetMetadata(
                data_source=DatasetSourceFormats.GENERATED_IN_DATA_CATALOG_FORMAT
            )

            dataset_information = None
            json_fpath = file.parent / f"{file.name.split('.')[0]}.json"
            if json_fpath.exists():
                with json_fpath.open("r") as json_file:
                    td_info_and_metdata = (
                        TabularDatasetInformationAndMetadata.model_validate_json(
                            json_file.read()
                        )
                    )
                dataset_information = [td_info_and_metdata.tabular_dataset_info]
                # copy num stats file and cat stats file
                try:
                    original_umask = os.umask(
                        0
                    )  # this is needed as this containers are not running as root but others are
                    os.makedirs(upload_folder, exist_ok=True)
                    num_stats_file_path = os.path.join(
                        upload_folder, f"{unique_id}_num_stats.json"
                    )
                    if dataset_information[0].numerical_statistics_file:
                        shutil.copy(
                            dataset_information[0].numerical_statistics_file,
                            num_stats_file_path,
                        )
                    cat_stats_file_path = os.path.join(
                        upload_folder, f"{unique_id}_cat_stats.json"
                    )
                    if dataset_information[0].categorical_statistics_file:
                        shutil.copy(
                            dataset_information[0].categorical_statistics_file,
                            cat_stats_file_path,
                        )
                    preview_file_path = os.path.join(
                        upload_folder, f"{unique_id}_preview.json"
                    )
                    if dataset_information[0].preview_file:
                        shutil.copy(
                            dataset_information[0].preview_file, preview_file_path
                        )
                    dataset_information[
                        0
                    ].numerical_statistics_file = num_stats_file_path
                    dataset_information[
                        0
                    ].categorical_statistics_file = cat_stats_file_path
                    dataset_information[0].preview_file = preview_file_path
                    os.umask(original_umask)
                except Exception as e:
                    if original_umask:
                        os.umask(original_umask)
                    raise Exception(
                        f"Error while copying json files with umasks: {e}"
                    ) from e
                metadata.columns_metadata = (
                    td_info_and_metdata.metadata.columns_metadata
                )
            else:
                raise Exception(
                    "preview not calculated prior therefore avoiding creating dataset"
                )

            dataset_id = await datasets_service.save_tabular_dataset_helper_async(
                input_data=file_path,
                project_id=projectId,
                site_id="1",
                created_by=user_email_prefix,
                user_id=user_id,
                action_id="",
                run_id="",
                workflow_id="",
                name=name,
                description=description,
                access_mode=AccessMode.EXTERNAL,
                metadata=metadata,
                dataset_information=dataset_information,
            )

            return DatasetUploadResponse(dataset_id=dataset_id)
        except Exception as e:
            print(f"exception raised in add to datasets : {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    # TODO: not required after fe change
    @staticmethod
    @router.post(
        "/uc3_sigma_get_metro_step_prefixes",
        status_code=status.HTTP_200_OK,
        deprecated=True,
    )
    async def uc3_sigma_get_metro_step_prefixes(
        data_pull_job_id: str,
        reset: bool,
        fd_trace_service: FdTraceDataPullService = Depends(
            get_fdtrace_data_pull_service
        ),
    ) -> dict:
        try:
            module_ids = []
            if reset:
                traveller_steps_results = (
                    await fd_trace_service.get_stage_results_async(
                        data_pull_job_id=data_pull_job_id,
                        stage=FDDataPullStages.TRAVELER_STEP,
                    )
                )
                if (
                    traveller_steps_results.current_stage_status
                    != DataPullStatus.SUCCESS
                ):
                    raise Exception("TraverllerSteps Stage not completed")
                path = traveller_steps_results.current_stage_results["traveler_steps"][
                    "file_path"
                ]
                df = pd.read_parquet(path)
                df["module_ids"] = df["traveler_steps"].str[:4]
                module_ids = list(df["module_ids"].unique())
            else:
                uc3_sigma_results = await fd_trace_service.get_stage_results_async(
                    data_pull_job_id=data_pull_job_id,
                    stage=FDDataPullStages.UC3_SIGMA_DATA,
                )
                module_ids = uc3_sigma_results.current_stage_inputs[
                    "all_metro_step_prefixes"
                ]

            module_ids = [
                module_id for module_id in module_ids if str(module_id).startswith("12")
            ]
            print(f"received module id's count {len(module_ids)}")
            module_ids_names_path = (
                environment.tdam_datacatalog_path / "module_ids_names.json"
            )
            if module_ids_names_path.exists():
                module_ids_names_from_file = {}  # read from file
                return {
                    module_id: module_ids_names_from_file.get(module_id, "unknown")
                    for module_id in module_ids
                }
            else:
                return {module_id: "unknown" for module_id in module_ids}
        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "get_fd_data_pull_results_error", "message": str(e)},
            )

    @staticmethod
    @router.post("/uc3_sigma_fetch_based_on_measurement_steps")
    async def uc3_sigma_fetch_based_on_steps_prefix(
        inputs: UC3SigmaCommonTestIdInput,
        data_pull_job_id: str,
    ) -> UC3SigmaMetroStepsCommonTestIds:
        uc3_sigma_folder = (
            environment.tdam_datacatalog_sessions_path(data_pull_job_id)
            / "uc3"
            / "sigma"
            / uuid4().hex
        )
        uc3_sigma_folder.mkdir(exist_ok=True, parents=True)
        metro_steps_file = uc3_sigma_folder / "metro_steps.paruqet"
        common_test_ids_file = uc3_sigma_folder / "common_test_ids.parquet"
        pl.DataFrame(
            inputs.uc3_sigma_metro_steps, schema=(("metro_steps", str),)
        ).write_parquet(metro_steps_file)
        if environment.dev_mode:
            pl.DataFrame(
                ["A", "B", "C", "D"], schema=(("COMMON_TEST_ID", str),)
            ).write_parquet(common_test_ids_file)
        else:
            ldf = FdTraceDataPullService.generate_uc3_step_parameters(inputs)
            df = await ldf.collect_async()
            df.write_parquet(common_test_ids_file)
        return UC3SigmaMetroStepsCommonTestIds(
            uc3_sigma_metro_steps=DataPullResult.model_validate(
                dict(
                    file_path=metro_steps_file,
                    selected_values=inputs.uc3_sigma_metro_steps,
                )
            ),
            common_test_ids=DataPullResult.model_validate(
                dict(file_path=common_test_ids_file)
            ),
        )
