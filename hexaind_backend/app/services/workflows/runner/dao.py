from bson import ObjectId
from typing import List, Tuple
from typing import List, Optional
from datetime import datetime, timezone
from app.services.workflows.designer.service import Workflow
from app.core.dao.dao_base import DaoBase
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.env_vars import environment
from app.services.workflows.workflow_utils import WFConfigService
from .schemas import RunSource, Run, RunState, RunActionsConfig, RunStatus, WorkflowCopy

class RunDao(DaoBase):
    
    async def get_all_runs_in_project_async(self, projectId: str, search_term: str, page_number: int, page_limit: int, workflowId: str = None, source: RunSource = None, state: RunState = None) -> Tuple[List[Run], int]:

        offset = (page_number - 1) * page_limit

        query = {"project_id": projectId}
        
        if workflowId:
            query["workflow_id"] = workflowId
        
        if isinstance(source, RunSource):
            query["run_source"] = source.value
        
        if isinstance(state, RunState):
            query["run_state"] = state.value

        if search_term:
            search_query = {"$regex": search_term, "$options": "i"} # Case-insensitive search
            query["$or"] = [{"name": search_query}, {"description": search_query},  {"owner_name": search_query}]

        workflow_runs_cursor = self.db_async.runs.aggregate(
            [   
                {"$match": query},
                {"$addFields": {"_id": {"$toString": "$_id"},
                                "created_at": {"$dateToString": {"format": "%Y-%m-%dT%H:%M:%S.%LZ", "date": "$created_at"}},
                                "last_modified_at": {"$dateToString": {"format": "%Y-%m-%dT%H:%M:%S.%LZ", "date": "$last_modified_at"}}
                                }},
                {"$skip": offset},
                {"$limit": page_limit}
            ]
        )

        workflow_runs = await workflow_runs_cursor.to_list(length=page_limit)

        workflow_runs = [Run(**workflow_run) for workflow_run in workflow_runs]
        total_count = await self.db_async.runs.count_documents(query)

        return workflow_runs, total_count
    
    async def get_run_by_id(self, run_id: str):

        run = await self.db_async.runs.find_one({"_id": ObjectId(run_id)})
        if not run:
            raise Exception('run not found')
        
        run = Run(**run)

        return run
    
    async def delete_run_by_id_async(self, run_id: str):
        
        result = await self.db_async.runs.delete_one({"_id": ObjectId(run_id)})

        if result.deleted_count != 1:
            raise Exception("run record not found")
        
        return True

    async def create_run(self, run: Run) -> str:

        result = await self.db_async.runs.insert_one(run.model_dump())
        if not result:
            raise Exception("not able to create run")
        
        run_id = str(result.inserted_id)

        return run_id
    
    async def update_run_async(self, run_id: str, run_record: Run):
        
        result = await self.db_async.runs.find_one_and_update(
                            {"_id": ObjectId(run_id)},
                            {"$set": run_record.model_dump()},
                            return_document=True
                        )
        
        if not result:
            raise Exception("failed to update the run record")
        
        return True
    
    async def update_run_state_async(self, run_id: str, user_id: str, state: RunState):

        result = await self.db_async.runs.find_one_and_update(
            {"_id": ObjectId(run_id)},
            {"$set": {"run_state": state.value, "last_modified_by_id": user_id, "last_modified_at": datetime.now(timezone.utc)}},
            return_document=True
        )

        if not result:
            raise Exception("failed to update the run")
        
        return True
    
    async def update_run_action_config_async(self, run_id: str, run_action_config_list: List[RunActionsConfig]) -> bool:

        result = await self.db_async.runs.find_one_and_update(
            {"_id": ObjectId(run_id)},
            {"$set": {"actions": [run_action_config.model_dump() for run_action_config in run_action_config_list]}},
            return_document=True
        )

        if not result:
            raise Exception("unable to update the run action")
        
        return True

    def get_runs_by_id(self, run_id: str) -> Run:

        run = self.db_sync.runs.find_one({"_id": ObjectId(run_id)})

        if not run:
            raise Exception("run not found")
        
        run["_id"] = str(run["_id"])
        
        run = Run(**run)

        return run 
    
    async def get_run_by_id_async(self, run_id: str) -> Run:

        run = await self.db_async.runs.find_one({"_id": ObjectId(run_id)})

        if not run:
            raise Exception("run not found")
        
        run["_id"] = str(run["_id"])
        
        run = Run(**run)

        return run
    
    def update_run_status(self, run_id: str, status: RunStatus):

        result = self.db_sync.runs.find_one_and_update(
            {"_id": ObjectId(run_id)},
            {"$set": {"run_status": status.value, "last_modified_at": datetime.now(timezone.utc)}},
            return_document=True
        )

        if not result:
            raise Exception("failed to update the run status")
        
        return True
    
    async def update_run_status_async(self, run_id: str, status: RunStatus):

        result = await self.db_async.runs.find_one_and_update(
            {"_id": ObjectId(run_id)},
            {"$set": {"run_status": status.value, "last_modified_at": datetime.now(timezone.utc)}},
            return_document=True
        )

        if not result:
            raise Exception("failed to update the run status")
        
        return True
    
    async def update_run_state_async(self, run_id:str, state:RunState):

        result = await self.db_async.runs.find_one_and_update(
            {"_id": ObjectId(run_id)},
            {"$set": {"run_state": state.value, "last_modified_at": datetime.now(timezone.utc)}},
            return_document=True
        )

        if not result:
            raise Exception("failed to update the run status")
        
        return True

    def get_recent_run(self, run: Run) -> Optional[Run]:
        runs = list(self.db_sync.runs.find({
            "run_source": "SCHEDULE",
            "workflow_id": run.workflow_id,
        }).sort([("created_at", -1)]).limit(2))
        if len(runs) != 2:
            return None
        else:
            return self.get_runs_by_id(str(runs[-1]["_id"]))



class WorkflowCopyDao(DaoBase):

    def __init__(
        self,
        db_sync_client: Optional[MongoClient] = None,
        db_async_client: Optional[AsyncIOMotorClient] = None,
    ):
        super().__init__(db_sync_client=db_sync_client, db_async_client=db_async_client)
        self.config_service = WFConfigService()
    
    async def create_workflow_copy_async(self, workflow: Workflow, run_id: str) -> str:


        workflow_copy = WorkflowCopy(run_id=run_id, workflow=workflow.model_dump())
        workflow_copy.workflow["widgets"] = [self.config_service.dump_config_to_json(widget) for widget in workflow_copy.workflow["widgets"]]
        result = await self.db_async.workflow_copy.insert_one(workflow_copy.model_dump())
        
        if not result:
            raise Exception("not able to create workflow copy record")
        
        workflow_copy_id = str(result.inserted_id)

        return workflow_copy_id
    
    async def get_workflow_copy_by_run_id_async(self, run_id: str) -> WorkflowCopy:

        workflow_copy = await self.db_async.workflow_copy.find_one({"run_id": run_id})
        if not workflow_copy:
            raise Exception('workflow copy not found')
        
        workflow_copy["_id"] = str(workflow_copy["_id"])
        workflow_copy["workflow"]["_id"] = str(workflow_copy["workflow"]["id"])
        # workflow_copy["workflow"]["widgets"] = [self.config_service.load_widget_from_json(widget) for widget in workflow_copy["workflow"]["widgets"]]
        workflow_copy = WorkflowCopy(**workflow_copy)

        return workflow_copy







