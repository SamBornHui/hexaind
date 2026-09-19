import logging

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from app.services.apps.thermocalc_web_service.dao import ThermoCalcJobDao
from app.services.apps.thermocalc_web_service.schemas import (
    ThermoCalcJobStatus,
    ThermoCalcJob,
    ThermoCalcJobRegisterationRequest,
)

logger = logging.getLogger(__package__)


class ThermoCalcAPIService:

    def __init__(
        self,
        db_sync_client: MongoClient = None,
        db_async_client: AsyncIOMotorClient = None,

    ) -> None:
        self.thermo_calc_job_dao = ThermoCalcJobDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )

    async def create_job(self, module_path: str, run_id: str, action_id: str) -> str:
        result = await self.thermo_calc_job_dao.create_job(
            module_path, run_id, action_id
        )
        logger.info(f"thermocalc job got created {result}")
        return result

    async def register_job(
        self,
        parent_job_id: str,
        registration_request: ThermoCalcJobRegisterationRequest,
    ):
        await self.thermo_calc_job_dao.register_job(
            parent_job_id,
            registration_request.expected_tasks,
            registration_request.input_features,
            registration_request.output_features,
            registration_request.connector_id,
        )
        logger.info(f"thermocalc job got registerd {parent_job_id}")

    async def receive_task(self, parent_job_id: str):
        await self.thermo_calc_job_dao.increment_received_tasks(parent_job_id)
        logger.info(f"thermocalc job got new task {parent_job_id}")

    async def complete_task(self, parent_job_id: str):
        await self.thermo_calc_job_dao.increment_processed_tasks(parent_job_id)
        logger.info(f"thermocalc job got 1 task completed {parent_job_id}")

        job = await self.thermo_calc_job_dao.get_job(parent_job_id)
        if (
            job.status != ThermoCalcJobStatus.COMPLETED
            and job.expected_tasks == job.processed_tasks
        ):
            # all jobs completed update status too
            await self.thermo_calc_job_dao.update_status(
                parent_job_id, ThermoCalcJobStatus.COMPLETED
            )
            logger.info(f"thermocalc job changed to completed, {parent_job_id}")

    async def complete_job(self, parent_job_id: str):
        await self.thermo_calc_job_dao.update_status(
            parent_job_id, ThermoCalcJobStatus.COMPLETED
        )
        logger.info(f"thermocalc job changed to completed, {parent_job_id}")

    async def get_job(self, parent_job_id) -> ThermoCalcJob:
        return await self.thermo_calc_job_dao.get_job(parent_job_id)

    def get_job_sync(self, parent_job_id) -> ThermoCalcJob:
        return self.thermo_calc_job_dao.get_job_sync(parent_job_id)

    def update_results_path(self, parent_job_id, results_path):
        return self.thermo_calc_job_dao.update_results_path( parent_job_id, results_path)

    def complete_task_sync(self, parent_job_id: str):
        self.thermo_calc_job_dao.increment_processed_tasks_sync(parent_job_id)
        logger.info(f"thermocalc job got 1 task completed {parent_job_id}")

        job = self.thermo_calc_job_dao.get_job_sync(parent_job_id)
        if (
            job.status != ThermoCalcJobStatus.COMPLETED
            and job.expected_tasks == job.processed_tasks
        ):
            # all jobs completed update status too
            self.thermo_calc_job_dao.update_status_sync(
                parent_job_id, ThermoCalcJobStatus.COMPLETED
            )
            logger.info(f"thermocalc job changed to completed, {parent_job_id}")