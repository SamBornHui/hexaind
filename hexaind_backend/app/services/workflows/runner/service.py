from pymongo import MongoClient
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Tuple
from datetime import datetime, timezone
from app.services.workflows.designer.service import WorkflowDesignerService, Workflow
from app.services.workflows.actions.service import ActionServiceNew
from app.core.services.action.service import ActionService
from .dao import RunDao, WorkflowCopyDao
from .schemas import Run, RunState, RunSource, RunActionsConfig, RunStatus, WorkflowCopy
import logging

logger = logging.getLogger(__package__)


class RunService:

    def __init__(
        self,
        db_sync_client: MongoClient = None,
        db_async_client: AsyncIOMotorClient = None,
    ) -> None:

        self.run_dao = RunDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )

        self.action_service = ActionServiceNew(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )

    def is_valid_run(self, run: Run):
        return True

    async def create_run_async(self, run_obj: Run) -> str:
        logger.info("Inside create_run_async function")
        # validate connector
        if not self.is_valid_run(run_obj):
            logger.error("Not a valid run")
            raise Exception("Not a valid run")

        run_id = await self.run_dao.create_run(run_obj)

        return run_id

    async def update_run_async(self, run_id: str, run_record: Run):

        return await self.run_dao.update_run_async(run_id=run_id, run_record=run_record)

    async def update_run_state_async(
        self, run_id: str, user_id: str, state: RunState
    ) -> bool:

        return await self.run_dao.update_run_state_async(
            run_id=run_id, user_id=user_id, state=state
        )

    async def update_run_action_config_async(
        self, run_id: str, run_action_config_list: List[RunActionsConfig]
    ):

        return await self.run_dao.update_run_action_config_async(
            run_id=run_id, run_action_config_list=run_action_config_list
        )

    async def get_all_runs_in_project_async(
        self,
        projectId: str,
        search_term: str,
        page_number: int,
        page_limit: int,
        workflowId: str = None,
        source: RunSource = None,
        state: RunState = None,
    ) -> Tuple[List[Run], int]:

        return await self.run_dao.get_all_runs_in_project_async(
            projectId=projectId,
            search_term=search_term,
            page_number=page_number,
            page_limit=page_limit,
            workflowId=workflowId,
            source=source,
            state=state,
        )

    def get_run_by_id(self, run_id: str) -> Run:

        return self.run_dao.get_runs_by_id(run_id=run_id)

    async def get_run_by_id_async(self, run_id: str) -> Run:

        return await self.run_dao.get_run_by_id_async(run_id=run_id)

    async def delete_run_by_id_async(self, run_id: str) -> bool:
        logger.info("Inside delete_run_by_id_async function")
        # get run record
        run_record = await self.run_dao.get_run_by_id_async(run_id=run_id)

        if run_record.run_status == RunStatus.RUNNING:
            logger.error(
                "Widgets execution in-progress, can not perform deletion operation at this moment."
            )
            raise Exception(
                "Widgets execution in-progress, can not perform deletion operation at this moment."
            )

        # get all actions and delete all actions associated to current run
        action_ids = [record.action_id for record in run_record.actions]

        results = await asyncio.gather(
            *[
                self.action_service.delete_action_record_by_action_id_async(
                    action_id=action_id
                )
                for action_id in action_ids
            ]
        )

        return await self.run_dao.delete_run_by_id_async(run_id=run_id)

    def update_run_status(self, run_id: str, status: RunStatus) -> bool:

        return self.run_dao.update_run_status(run_id=run_id, status=status)

    async def update_run_status_async(self, run_id: str, status: RunStatus) -> bool:

        return await self.run_dao.update_run_status_async(run_id=run_id, status=status)

    async def update_run_state_async(self, run_id: str, state: RunState) -> bool:

        return await self.run_dao.update_run_state_async(run_id=run_id, state=state)


class WorkflowCopyService:

    def __init__(
        self,
        db_sync_client: MongoClient = None,
        db_async_client: AsyncIOMotorClient = None,
    ) -> None:

        self.workflow_copy_dao = WorkflowCopyDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )

    async def create_workflow_copy_async(self, workflow: Workflow, run_id: str) -> str:

        return await self.workflow_copy_dao.create_workflow_copy_async(
            workflow=workflow, run_id=run_id
        )

    async def get_workflow_copy_by_run_id_async(self, run_id: str) -> WorkflowCopy:

        return await self.workflow_copy_dao.get_workflow_copy_by_run_id_async(
            run_id=run_id
        )
