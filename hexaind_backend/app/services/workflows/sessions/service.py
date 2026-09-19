import asyncio

from click import Option
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Tuple
from datetime import datetime, timezone
from app.services.workflows.designer.service import WorkflowDesignerService, Workflow
from app.services.workflows.runner.service import RunService
from app.services.workflows.actions.service import ActionServiceNew
from app.services.workflows.action_results.service import *
from .dao import WorkflowSessionDao
from .schemas import (
    CreateWorkflowSessionRequest,
    WorkflowSessionDB,
    SavedWorkflowsFromSession,
    FavouriteWorkflow
)
from app.services.workflows.runner.schemas import Run, RunState, RunStatus


class WorkflowSessionService:

    def __init__(
        self,
        db_sync_client: MongoClient = None,
        db_async_client: AsyncIOMotorClient = None,
    ) -> None:

        self.sessions_dao = WorkflowSessionDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )

        self.workflow_designer_service = WorkflowDesignerService(
            db_async_client=db_async_client,
            db_sync_client=db_sync_client
        )

        self.run_service = RunService(db_async_client=db_async_client)

        self.action_results_service = ActionResultsService(
            db_async_client=db_async_client, db_sync_client=db_sync_client
        )

    async def create_workflow_session_async(
        self,
        user_id: str,
        user_name: str,
        site_id: str,
        project_id: str,
        create_session_req_obj: CreateWorkflowSessionRequest,
    ) -> str:
        logger.info("Inside create_workflow_session_async function")
        current_timestamp = datetime.now(timezone.utc)

        # creating empty workflow record
        workflow = Workflow(
            name=create_session_req_obj.name,
            description=create_session_req_obj.description,
            workflow_version="v0",
            owner_id=user_id,
            owner_name=user_name,
            created_at=current_timestamp,
            last_modified_by_id=user_id,
            last_modified_at=current_timestamp,
            project_id=project_id,
            site_id=site_id,
            interactive_mode=True,
            favourited_by=[]
        )

        workflow_id = await self.workflow_designer_service.create_workflow_async(
            workflow=workflow
        )

        # creating run for the session
        run = Run(
            name=create_session_req_obj.name,
            description=create_session_req_obj.description,
            interactive_mode=True,
            run_state=RunState.START,
            run_status=RunStatus.IDLE,
            actions=[],
            owner_id=user_id,
            owner_name=user_name,
            created_at=current_timestamp,
            last_modified_at=current_timestamp,
            last_modified_by_id=user_id,
            project_id=project_id,
            site_id=site_id,
            workflow_id=workflow_id,
        )
        run_id = await self.run_service.create_run_async(run_obj=run)

        # creating workflow session record
        session_obj = WorkflowSessionDB(
            name=create_session_req_obj.name,
            description=create_session_req_obj.description,
            workflow_id=workflow_id,
            saved_workflows=[],
            run_id=run_id,
            owner_id=user_id,
            owner_name=user_name,
            created_at=current_timestamp,
            last_modified_at=current_timestamp,
            last_modified_by_id=user_id,
            project_id=project_id,
            site_id=site_id,
            favourited_by=[]
        )
        session_id = await self.sessions_dao.cerate_workflow_session_async(
            workflow_session_obj=session_obj
        )

        logger.info(f"session_created_id: {session_id}")
        return session_id

    async def delete_workflow_session_async(self, session_id: str, saved_workflow_ids: Optional[List[str]]=None) -> bool:
        logger.info("Inside delete_workflow_session_async function")
        logger.info(f"Session to be deleted: {session_id}")
        # get the workflow-session record
        session_record = await self.sessions_dao.get_workflow_session_async(
            session_id=session_id
        )

        session_run_id = session_record.run_id

        # delete the run record associated with workflow-session

        await self.run_service.delete_run_by_id_async(run_id=session_run_id)

        # delete workflow record associated with workflow-session

        await self.workflow_designer_service.delete_workflow_async(
            workflow_id=session_record.workflow_id
        )
        
        # delete saved (published) workflows associated with workflow-session
        if saved_workflow_ids:
            tasks = [
                self.workflow_designer_service.delete_workflow_async(workflow_id=saved_workflow_id)
                for saved_workflow_id in saved_workflow_ids
            ]
            await asyncio.gather(*tasks)
        
        return await self.sessions_dao.delete_workflow_session_async(
            session_id=session_id
        )

    async def get_workflow_session_async(self, session_id: str) -> WorkflowSessionDB:
        logger.info("Inside get_workflow_session_async function")
        if not await self.sessions_dao.is_session_present_async(session_id=session_id):
            logger.error("Session not found")
            raise Exception("Session not found")

        session: WorkflowSessionDB = await self.sessions_dao.get_workflow_session_async(
            session_id=session_id
        )

        return session

    def get_workflow_session(self, session_id: str) -> WorkflowSessionDB:
        logger.info("Inside get_workflow_session function")
        if not self.sessions_dao.is_session_present(session_id=session_id):
            logger.error("Session not found")
            raise Exception("Session not found")

        session: WorkflowSessionDB = self.sessions_dao.get_workflow_session(
            session_id=session_id
        )
        return session

    async def check_existing_published_workflow_in_session_async(
        self, session_id: str, workflow_name: str, workflow_version_tag: str
    ) -> bool:

        return (
            await self.sessions_dao.check_existing_published_workflow_in_session_async(
                session_id=session_id,
                workflow_name=workflow_name,
                workflow_version_tag=workflow_version_tag,
            )
        )

    async def update_session_record_with_latest_published_workflow(
        self, session_id: str, saveas_workflow: SavedWorkflowsFromSession
    ) -> bool:

        return await self.sessions_dao.update_session_record_with_latest_published_workflow(
            session_id=session_id, saveas_workflow=saveas_workflow
        )

    async def get_all_workflow_sessions_async(
        self, projectId: str, search_term: str, page_number: int, page_limit: int
    ) -> Tuple[List[WorkflowSessionDB], int]:

        return await self.sessions_dao.get_all_workflow_sessions_async(
            projectId=projectId,
            search_term=search_term,
            page_number=page_number,
            page_limit=page_limit,
        )

    async def get_all_workflow_templates_async(
        self, projectId: str, search_term: str, page_number: int, page_limit: int
    ) -> Tuple[List[WorkflowSessionDB], int]:

        return await self.sessions_dao.get_all_workflow_templates_async(
            projectId=projectId,
            search_term=search_term,
            page_number=page_number,
            page_limit=page_limit,
        )

    async def update_workflow_session_async(
        self,
        user_id: str,
        user_name: str,
        site_id: str,
        project_id: str,
        sesssion_id: str,
        new_session: CreateWorkflowSessionRequest,
    ) -> bool:
        logger.info("Inside update_workflow_session_async function")

        prev_workflow_session: WorkflowSessionDB = (
            await self.get_workflow_session_async(session_id=sesssion_id)
        )

        # prev_workflow_session.owner_id = user_id
        # prev_workflow_session.owner_name = user_name
        prev_workflow_session.site_id = site_id
        prev_workflow_session.project_id = project_id
        prev_workflow_session.name = new_session.name
        prev_workflow_session.description = new_session.description
        prev_workflow_session.last_modified_at = datetime.now(timezone.utc)
        prev_workflow_session.last_modified_by_id = user_id

        return await self.sessions_dao.update_workflow_session_async(
            workflow_session_id=sesssion_id, workflow_session_obj=prev_workflow_session
        )

    async def get_sessions_from_workflow(self, published_wf_id):
        logger.info("Inside get session with given workflow id")
        session_record = (
            await self.sessions_dao.get_session_from_workflow_async(
                published_workflow_id=published_wf_id
            )
        )

        return session_record
    
    def get_sessions_from_workflow_sync(self, published_wf_id):
        logger.info("Inside get session with given workflow id")
        session_record = (
            self.sessions_dao.get_session_from_workflow(
                published_workflow_id=published_wf_id
            )
        )

        return session_record
    
    async def favourite_workflow(self, favourite_workflow:FavouriteWorkflow):
        logger.info("Inside favouriting workflow")

        if favourite_workflow.is_favourite == True:
            update_data = {
                    "$addToSet": {"favourited_by": favourite_workflow.user_id}
                }
        else:
            update_data = {
                "$pull": {"favourited_by": favourite_workflow.user_id}
            }
        await self.sessions_dao.update_favourite_workflow(favourite_value=update_data,
                                                    workflow_id=favourite_workflow.workflow_id)
        
        
        

        
