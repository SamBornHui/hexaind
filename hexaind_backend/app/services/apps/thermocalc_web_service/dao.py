from datetime import datetime, timezone
from typing import List
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from bson import ObjectId

from app.core.dao.dao_base import DaoBase
from app.services.apps.thermocalc_web_service.schemas import (
    ThermoCalcJob,
    ThermoCalcJobStatus,
)


class ThermoCalcJobDao():

    def __init__(self, db_sync_client: MongoClient=None, db_async_client: AsyncIOMotorClient=None):
        if db_async_client:
            self.db_async_client = db_async_client
            self.db_async = self.db_async_client["thermocalc_db"]
        if db_sync_client:
            self.db_sync_client  = db_sync_client
            self.db_sync =  self.db_sync_client["thermocalc_db"]



    async def create_job(self, module_path: str, run_id: str, action_id: str) -> str:

        job = ThermoCalcJob(
            module_path=module_path,
            run_id=run_id,
            action_id=action_id,
            created_at=datetime.now(timezone.utc),
        )
        result = await self.db_async.thermo_calc_jobs.insert_one(job.model_dump())
        return str(result.inserted_id)

    async def register_job(
        self,
        parent_job_id: str,
        expected_tasks_count: int,
        input_features: List[str],
        output_features: List[str],
        connector_id: str
    ):
        result = await self.db_async.thermo_calc_jobs.update_one(
            {"_id": ObjectId(parent_job_id)},
            {
                "$set": {
                    "expected_tasks": expected_tasks_count,
                    "input_features": input_features,
                    "output_features": output_features,
                    "connector_id": connector_id,
                    "status": ThermoCalcJobStatus.REGISTERED,
                    "last_modified_at": datetime.now(timezone.utc),
                }
            },
        )
        if result.matched_count == 0:
            raise ValueError(f"ThermoCalc Job not found with id {parent_job_id}")

    async def increment_received_tasks(self, parent_job_id: str):
        job = await self.db_async.thermo_calc_jobs.find_one(
            {"_id": ObjectId(parent_job_id)}
        )
        if not job:
            raise ValueError(f"ThermoCalc Job not found with id {parent_job_id}")
        job["_id"] = str(job["_id"])
        job = ThermoCalcJob(**job)

        if job.status in [
            ThermoCalcJobStatus.UNREGISTERED,
            ThermoCalcJobStatus.COMPLETED,
        ]:
            raise Exception(
                f"Invalid job status to increment received tasks {job.status}"
            )

        new_status = job.status
        if (
            job.status == ThermoCalcJobStatus.REGISTERED
        ):  # upgrade status to in progress
            new_status = ThermoCalcJobStatus.IN_PROGRESS

        result = await self.db_async.thermo_calc_jobs.update_one(
            {"_id": ObjectId(parent_job_id)},
            {
                "$inc": {"received_tasks": 1},
                "$set": {
                    "status": new_status,
                    "last_modified_at": datetime.now(timezone.utc),
                },
            },
        )
        if result.matched_count == 0:
            raise ValueError(f"ThermoCalc Job not found with id {parent_job_id}")
        if result.modified_count == 0:
            raise ValueError(
                f"ThermoCalc Job not updated received tasks {parent_job_id}"
            )

    async def increment_processed_tasks(self, parent_job_id: str):
        job = await self.db_async.thermo_calc_jobs.find_one(
            {"_id": ObjectId(parent_job_id)}
        )
        if not job:
            raise ValueError(f"ThermoCalc Job not found with id {parent_job_id}")
        job["_id"] = str(job["_id"])
        job = ThermoCalcJob(**job)

        if job.status != ThermoCalcJobStatus.IN_PROGRESS:
            raise Exception(
                f"Invalid job status to increment processed tasks {job.status}"
            )

        result = await self.db_async.thermo_calc_jobs.update_one(
            {"_id": ObjectId(parent_job_id)},
            {
                "$inc": {"processed_tasks": 1},
                "$set": {"last_modified_at": datetime.now(timezone.utc)},
            },
        )
        if result.matched_count == 0:
            raise ValueError(f"ThermoCalc Job not found with id {parent_job_id}")
        if result.modified_count == 0:
            raise ValueError(
                f"ThermoCalc Job not updated processed tasks, {parent_job_id}"
            )

    async def update_status(self, parent_job_id: str, status: ThermoCalcJobStatus):
        result = await self.db_async.thermo_calc_jobs.update_one(
            {"_id": ObjectId(parent_job_id)},
            {
                "$set": {
                    "status": status,
                    "last_modified_at": datetime.now(timezone.utc),
                },
            },
        )
        if result.matched_count == 0:
            raise ValueError(f"ThermoCalc Job not found with id {parent_job_id}")

    async def get_job(self, parent_job_id: str) -> ThermoCalcJob:
        job = await self.db_async.thermo_calc_jobs.find_one(
            {"_id": ObjectId(parent_job_id)}
        )
        if not job:
            raise ValueError(f"ThermoCalc Job not found with id {parent_job_id}")
        job["_id"] = str(job["_id"])
        return ThermoCalcJob(**job)

    def get_job_sync(self, parent_job_id: str) -> ThermoCalcJob:
        job = self.db_sync.thermo_calc_jobs.find_one(
            {"_id": ObjectId(parent_job_id)}
        )
        if not job:
            raise ValueError(f"ThermoCalc Job not found with id {parent_job_id}")
        job["_id"] = str(job["_id"])
        return ThermoCalcJob(**job)

    def update_results_path(self, parent_job_id, results_path):
        result = self.db_sync.thermo_calc_jobs.update_one(
            {
                "_id": ObjectId(parent_job_id),
                "status": ThermoCalcJobStatus.COMPLETED,
                "results_file_path": None
            },
            {
                "$set": {
                    "results_file_path": results_path,
                    "last_modified_at": datetime.now(timezone.utc),
                },
            },
        )
        if result.matched_count == 0:
            raise ValueError(f"could not find completed and results_file_path empty record with {parent_job_id}")

    def increment_processed_tasks_sync(self, parent_job_id: str):
        job = self.db_sync.thermo_calc_jobs.find_one(
            {"_id": ObjectId(parent_job_id)}
        )
        if not job:
            raise ValueError(f"ThermoCalc Job not found with id {parent_job_id}")
        job["_id"] = str(job["_id"])
        job = ThermoCalcJob(**job)

        if job.status != ThermoCalcJobStatus.IN_PROGRESS:
            raise Exception(
                f"Invalid job status to increment processed tasks {job.status}"
            )

        result = self.db_sync.thermo_calc_jobs.update_one(
            {"_id": ObjectId(parent_job_id)},
            {
                "$inc": {"processed_tasks": 1},
                "$set": {"last_modified_at": datetime.now(timezone.utc)},
            },
        )
        if result.matched_count == 0:
            raise ValueError(f"ThermoCalc Job not found with id {parent_job_id}")
        if result.modified_count == 0:
            raise ValueError(
                f"ThermoCalc Job not updated processed tasks, {parent_job_id}"
            )

    def update_status_sync(self, parent_job_id: str, status: ThermoCalcJobStatus):
        result = self.db_sync.thermo_calc_jobs.update_one(
            {"_id": ObjectId(parent_job_id)},
            {
                "$set": {
                    "status": status,
                    "last_modified_at": datetime.now(timezone.utc),
                },
            },
        )
        if result.matched_count == 0:
            raise ValueError(f"ThermoCalc Job not found with id {parent_job_id}")
