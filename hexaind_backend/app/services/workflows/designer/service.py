from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Tuple
from datetime import datetime, timezone
from app.services.workflows.designer.widget_rules import *
import logging
from .schemas import Workflow
from .dao import WorkflowDesignerDao
from app.services.workflows.sessions.schemas import SavedWorkflowsFromSession, WorkflowSessionDB

logger = logging.getLogger(__package__)

class WorkflowDesignerService:

    def __init__(self, db_sync_client: MongoClient = None, db_async_client: AsyncIOMotorClient = None) -> None:
        
        self.workflow_designer_dao = WorkflowDesignerDao(db_sync_client=db_sync_client, db_async_client=db_async_client)

    def is_valid_workflow(self, workflow: Workflow):
        return True

    async def create_workflow_async(self, workflow: Workflow) -> str:
        logger.info("Inside create_workflow_async function")
        # validate workflow
        if not self.is_valid_workflow(workflow):
            logger.error("Not a valid workflow")
            raise Exception("Not a valid workflow")
        
        workflow_id = await self.workflow_designer_dao.create_workflow_async(workflow)

        return workflow_id
    
    async def get_all_workflows_async(self, projectId: str, search_term: str, page_number: int, page_limit: int) -> Tuple[List[Workflow], int]:

        return await self.workflow_designer_dao.get_all_workflows_async(projectId=projectId, search_term=search_term, page_number=page_number, page_limit=page_limit)
    
    async def get_workflow_by_id_without_schema_check_async(self, workflow_id: str) -> dict:

        logger.info("Inside get_workflow_by_id_without_schema_check_async function")
        if not await self.workflow_designer_dao.is_workflow_present_async(workflow_id=workflow_id):
            logger.error("Workflow not found")
            raise ValueError("Workflow not found")
        
        workflow: Workflow = await self.workflow_designer_dao.get_workflow_by_id_async(workflow_id=workflow_id)

        workflow_dict: dict = workflow.model_dump()
        workflow_dict['_id'] = workflow.id

        if not workflow.is_valid:
            workflow_dict["last_valid_widgets"] = workflow_dict["widgets"]
            workflow_dict["widgets"] = workflow_dict["widgets"] + workflow_dict["partial_widgets"]

        return workflow_dict

    
    async def get_workflow_by_id_async(self, workflow_id: str) -> Workflow:
        logger.info("Inside get_workflow_by_id_async function")
        if not await self.workflow_designer_dao.is_workflow_present_async(workflow_id=workflow_id):
            logger.error("Workflow not found")
            raise ValueError("Workflow not found")
        
        workflow: Workflow = await self.workflow_designer_dao.get_workflow_by_id_async(workflow_id=workflow_id)

        return workflow

    async def add_last_run_details_to(self, saved_wf: Union[SavedWorkflowsFromSession, WorkflowSessionDB]):
        wf_latest_run_det = await self.workflow_designer_dao.get_last_run_details(saved_wf.workflow_id)
        if wf_latest_run_det:
            saved_wf.last_run_status = wf_latest_run_det["run_status"]
            saved_wf.last_run_at = wf_latest_run_det["last_modified_at"]

    async def update_workflow_async(self, user_id: str, workflow_id: str, new_workflow: Workflow):
        logger.info("Inside update_workflow_async function")
        old_workflow: Workflow = await self.get_workflow_by_id_async(workflow_id=workflow_id)
        new_workflow.created_at = old_workflow.created_at
        new_workflow.project_id = old_workflow.project_id
        new_workflow.site_id = old_workflow.site_id
        new_workflow.owner_id = old_workflow.owner_id
        new_workflow.owner_name = old_workflow.owner_name

        new_workflow.last_modified_at = datetime.now(timezone.utc)
        new_workflow.last_modified_by_id = user_id
        
        return await self.workflow_designer_dao.update_workflow_async(workflow_id=workflow_id, updated_workflow=new_workflow)
    
    async def delete_workflow_async(self, workflow_id: str):

        return await self.workflow_designer_dao.delete_workflow_async(workflow_id=workflow_id)
    
    def get_workflow_by_id(self, workflow_id: str) -> Workflow:

        return self.workflow_designer_dao.get_workflow_by_id(workflow_id)
    
    @staticmethod
    def get_widget_schema(widget_type: UIWidgetType) -> WidgetRule:
        logger.info("Inside get_widget_schema function")
        if widget_type == UIWidgetType.CSV:
            return csv_widget_schema
        elif widget_type == UIWidgetType.BIGQUERY:
            return bigquery_widget_schema
        elif widget_type == UIWidgetType.LOOP_START:
            return loop_start_widget_schema
        elif widget_type == UIWidgetType.FILTER:
            return filter_widget_schema
        elif widget_type == UIWidgetType.CUSTOM_CODE:
            return custom_code_widget_schema
        elif widget_type == UIWidgetType.LGBM:
            return lgbm_widget_schema
        elif widget_type == UIWidgetType.LOOP_END:
            return loop_end_widget_schema
        elif widget_type == UIWidgetType.MOBO:
            return mobo_widget_schema
        elif widget_type == UIWidgetType.SAVE:
            return save_widget_schema
        elif widget_type == UIWidgetType.RESCALE:
            return rescale_widget_schema
        elif widget_type == UIWidgetType.APPEND:
            return append_widget_schema
        elif widget_type == UIWidgetType.JOIN:
            return join_widget_schema
        else:
            logger.error("invalid UI widget type")
            raise Exception("invalid UI widget type")
