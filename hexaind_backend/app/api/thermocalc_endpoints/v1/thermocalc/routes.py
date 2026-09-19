import os
from typing import Any
from uuid import uuid4
import json

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Body,Query
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorClient

from app.config.env_vars import thermocalc_environment
from app.core.celery.celery_worker import create_celery_app
from app.core.celery.global_config import THERMOCALC_SUB_ACTION_WORKER_DEFAULT_QUEUE, THERMOCALC_SUB_ACTION_WORKER_RK
from app.services.apps.thermocalc_web_service.service import ThermoCalcAPIService
from app.services.apps.thermocalc_web_service.schemas import ThermoCalcJob, ThermoCalcJobStatus, \
    ThermoCalcJobRegisterationRequest
from app.core.db.db_utils import get_thermocalc_db_async
import logging, traceback

thermocalc_router = APIRouter(tags=["Thermocalc"])

logger = logging.getLogger(__package__)


class ThermoCalcServiceRouter:

    def __init__(self):
        pass
    

    @staticmethod
    @thermocalc_router.post("/v1/thermocalc/jobs", response_model=ThermoCalcJob)
    async def create_job(
            run_id: str,
            action_id: str,
            file: UploadFile = File(...),
            client: AsyncIOMotorClient = Depends(get_thermocalc_db_async)
    ) -> ThermoCalcJob:
        try:
            destination_file_path = thermocalc_environment.thermocalc_home / f"modules/{uuid4()}_{file.filename}"
            destination_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(str(destination_file_path.absolute()), "wb") as f:
                content = await file.read()
                f.write(content)
            thermocalc_service = ThermoCalcAPIService(db_async_client=client)
            result = await thermocalc_service.create_job(str(destination_file_path.absolute()), run_id, action_id)
            job = await thermocalc_service.get_job(result)
            return job
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"Failed to create job with exception: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create job: {e}"
            )

    @staticmethod
    @thermocalc_router.post("/v1/thermocalc/jobs/{parent_job_id}/register", response_model=None)
    async def register_job(parent_job_id: str, registration_request: ThermoCalcJobRegisterationRequest, 
                           client: AsyncIOMotorClient = Depends(get_thermocalc_db_async)):
        try:
            thermocalc_service = ThermoCalcAPIService(db_async_client=client)
            await thermocalc_service.register_job(parent_job_id, registration_request)
            return None
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"Failed to register job with exception: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to register job: {e}"
            )

    @staticmethod
    @thermocalc_router.post("/v1/thermocalc/jobs/{parent_job_id}/receive_task", response_model=None)
    async def receive_task(parent_job_id: str, 
                            start_index: int = Query(...),
                            TC23A_HOME: str = Query(...), 
                            TC23B_HOME: str = Query(...), 
                            LSHOST: str = Query(...),
                            connection_type:str = Query(...), 
                            data: Any = Body(...),
                            client: AsyncIOMotorClient = Depends(get_thermocalc_db_async)):
        try:
            thermocalc_service = ThermoCalcAPIService(db_async_client=client)
            data_path = thermocalc_environment.thermocalc_home / f"task_inputs/{parent_job_id}/{uuid4()}_{start_index}.json"
            data_path.parent.mkdir(parents=True, exist_ok=True)
            with open(data_path, "w") as file:
                json.dump(data, file)
            celery_app = create_celery_app("thermocalc_task",default_queue=THERMOCALC_SUB_ACTION_WORKER_DEFAULT_QUEUE)
            celery_app.send_task(
                "task_thermocalc_sub_action",
                kwargs={"parent_job_id": parent_job_id, 
                        "data_path": str(data_path.absolute()),
                        "start_index": start_index,
                        "TC23A_HOME": TC23A_HOME, 
                        "TC23B_HOME": TC23B_HOME, 
                        "LSHOST": LSHOST,
                        "connection_type":connection_type},
                queue=THERMOCALC_SUB_ACTION_WORKER_DEFAULT_QUEUE,
                routing_key=THERMOCALC_SUB_ACTION_WORKER_RK,
            )
            await thermocalc_service.receive_task(parent_job_id)
            return None
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"Failed to receive task with exception: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to receive task: {e}"
            )

    @staticmethod
    @thermocalc_router.post("/v1/thermocalc/jobs/{parent_job_id}/complete_task", response_model=None)
    async def complete_task(parent_job_id: str, 
                            client: AsyncIOMotorClient = Depends(get_thermocalc_db_async)):
        try:
            thermocalc_service = ThermoCalcAPIService(db_async_client=client)
            await thermocalc_service.complete_task(parent_job_id)
            return None
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"Failed to complete task with exception: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to complete task: {e}"
            )

    @staticmethod
    @thermocalc_router.get("/v1/thermocalc/jobs/{parent_job_id}", response_model=ThermoCalcJob)
    async def get_status(parent_job_id: str, 
                         client: AsyncIOMotorClient = Depends(get_thermocalc_db_async)) -> ThermoCalcJob:
        try:
            thermocalc_service = ThermoCalcAPIService(db_async_client=client)
            job = await thermocalc_service.get_job(parent_job_id)

            if job.status != ThermoCalcJobStatus.COMPLETED and job.processed_tasks == job.expected_tasks:
                await thermocalc_service.complete_job(parent_job_id)
                job = await thermocalc_service.get_job(parent_job_id)

            return job
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"Failed to get job status with exception: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to get job status: {e}"
            )

    @thermocalc_router.get("/v1/thermocalc/results/{parent_job_id}")
    async def download_results(parent_job_id: str, 
                               client: AsyncIOMotorClient = Depends(get_thermocalc_db_async)):
        try:
            thermocalc_service = ThermoCalcAPIService(db_async_client=client)
            job = await thermocalc_service.get_job(parent_job_id)

            # Check if the results file path exists
            if not os.path.isfile(job.results_file_path):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Results file not found"
                )

            # Return the file as a response
            return FileResponse(
                path=job.results_file_path,
                media_type='application/octet-stream',
                filename=os.path.basename(job.results_file_path)
            )
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(f"Failed to download results with exception: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to download results: {e}"
            )
