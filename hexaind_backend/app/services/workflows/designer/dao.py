from datetime import timezone as tz
from bson import ObjectId
from typing import List, Tuple
from bson import ObjectId

from app.services.workflows.workflow_utils import WFConfigService

from .schemas import Workflow
from app.core.dao.dao_base import *
from app.services.admin.connectors.schemas import *

import logging
logger = logging.getLogger(__package__)

class WorkflowDesignerDao(DaoBase):
    def __init__(
        self,
        db_sync_client: Optional[MongoClient] = None,
        db_async_client: Optional[AsyncIOMotorClient] = None,
    ):
        super().__init__(db_sync_client=db_sync_client, db_async_client=db_async_client)
        self.config_service = WFConfigService()

    async def get_all_workflows_async(
        self, projectId: str, search_term: str, page_number: int, page_limit: int
    ) -> Tuple[List[Workflow], int]:

        offset = (page_number - 1) * page_limit
        query = {"project_id": projectId, "interactive_mode": False}

        if search_term:
            search_query = {
                "$regex": search_term,
                "$options": "i",
            }  # Case-insensitive search
            query["$or"] = [
                {"name": search_query},
                {"description": search_query},
                {"owner_name": search_query},
            ]

        workflows_cursor = self.db_async.workflows.aggregate(
            [
                {"$match": query},
                {
                    "$addFields": {
                        "_id": {"$toString": "$_id"},
                        "created_at": {
                            "$dateToString": {
                                "format": "%Y-%m-%dT%H:%M:%S.%LZ",
                                "date": "$created_at",
                            }
                        },
                        "last_modified_at": {
                            "$dateToString": {
                                "format": "%Y-%m-%dT%H:%M:%S.%LZ",
                                "date": "$last_modified_at",
                            }
                        },
                    }
                },
                {"$skip": offset},
                {"$limit": page_limit},
            ]
        )

        workflows = await workflows_cursor.to_list(length=page_limit)

        for workflow in workflows:
            widgets = workflow.get("widgets", [])
            # workflow["widgets"] = [self.config_service.load_widget_from_json(widget) for widget in widgets]

        workflows = [Workflow(**workflow) for workflow in workflows]

        total_count = await self.db_async.workflows.count_documents(query)

        return workflows, total_count

    async def fetch_workflows_with_custom_query(
        self, query, page_number: int = 1, page_size=1000
    ) -> Tuple[List[Workflow], int]:

        skip = (page_number - 1) * page_size
        total_count = await self.db_async.workflows.count_documents(query)

        workflows = []
        async for workflow in (
            self.db_async.workflows.find(query).skip(skip).limit(page_size)
        ):
            workflow["_id"] = str(workflow["_id"])
            # workflow["widgets"] = [self.config_service.load_widget_from_json(widget) for widget in workflow["widgets"]]
            workflows.append(Workflow(**workflow))

        return workflows, total_count

    async def create_workflow_async(self, workflow: Workflow) -> str:

        workflow.widgets = [self.config_service.dump_config_to_json(widget) for widget in workflow.widgets]

        result = await self.db_async.workflows.insert_one(workflow.model_dump())
        if not result:
            raise Exception("not able to create workflow")

        workflow_id = str(result.inserted_id)

        return workflow_id

    async def is_workflow_present_async(self, workflow_id: str) -> bool:

        workflow = await self.db_async.workflows.find_one(
            {"_id": ObjectId(workflow_id)}
        )
        if not workflow:
            return False
        return True

    async def get_workflow_by_id_async(self, workflow_id: str) -> Workflow:

        workflow = await self.db_async.workflows.find_one(
            {"_id": ObjectId(workflow_id)}
        )
        if not workflow:
            raise Exception("workflow not found")

        workflow["_id"] = str(workflow["_id"])
        # workflow["widgets"] = [self.config_service.load_widget_from_json(widget) for widget in workflow["widgets"]]
        if "last_modified_at" in workflow and not workflow["last_modified_at"].tzinfo:
            workflow["last_modified_at"] = workflow["last_modified_at"].replace(
                tzinfo=tz.utc
            )
            # todo: above can be acheived by creating timeaware mongoclient, explore it in future.
            # since we are already storing times as UTC so converting to UTC instead of retrieving

        workflow = Workflow(**workflow)

        return workflow

    async def get_last_run_details(self, workflow_id: str):
        wf_latest_run_det = await self.db_async.runs.find_one({"workflow_id": workflow_id },
                                                          {"run_status":1, "last_modified_at":1},
                                                          sort=[("created_at", -1)])
        return wf_latest_run_det

    async def update_workflow_async(self, workflow_id: str, updated_workflow: Workflow):

        updated_workflow.widgets = [self.config_service.dump_config_to_json(widget) for widget in updated_workflow.widgets]

        result = await self.db_async.workflows.find_one_and_update(
            {"_id": ObjectId(workflow_id)},
            {"$set": updated_workflow.model_dump()},
            return_document=True,
        )

        if not result:
            raise Exception("failed to update the workflow")

        return True

    async def delete_workflow_async(self, workflow_id: str):

        print(type(workflow_id))
        logger.info(f"Workflow ID type {type(workflow_id)}")

        await self.db_async.workflow_sessions.update_one(
            {"saved_workflows.workflow_id": workflow_id},
            {"$pull": {"saved_workflows": {"workflow_id": workflow_id}}},
        )
        result = await self.db_async.workflows.delete_one(
            {"_id": ObjectId(workflow_id)}
        )

        if result.deleted_count != 1:
            raise Exception("workflow not found")

        return True

    def get_workflow_by_id(self, workflow_id: str) -> Workflow:

        workflow = self.db_sync.workflows.find_one({"_id": ObjectId(workflow_id)})
        if not workflow:
            raise Exception("workflow not found")

        workflow["_id"] = str(workflow["_id"])
        # workflow["widgets"] = [self.config_service.load_widget_from_json(widget) for widget in workflow["widgets"]]
        
        workflow = Workflow(**workflow)

        return workflow
