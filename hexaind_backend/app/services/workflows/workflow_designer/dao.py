import copy
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient

from bson import ObjectId

from app.core.dao.dao_base import DaoBase
from app.core.services.action.schemas import Action
from app.services.workflows.workflow_utils import WFConfigService

logger = logging.getLogger(__package__)


class InteractiveWorkflowDesginerServiceDao(DaoBase):

    def __init__(
        self,
        db_sync_client: Optional[MongoClient] = None,
        db_async_client: Optional[AsyncIOMotorClient] = None,
    ):
        super().__init__(db_sync_client=db_sync_client, db_async_client=db_async_client)
        self.config_service = WFConfigService()

    async def save_workflow_in_session(self, action_id: str) -> Action:

        action_record = await self.db_async.actions.find_one(
            {"_id": ObjectId(action_id)}
        )

        if not action_record:
            raise Exception("Action Record not found")

        action_record["_id"] = str(action_record["_id"])
        action_record["action_config"] = self.config_service.load_widget_from_json(
            widget=action_record["action_config"]
        )
        action_record = Action(**action_record)

        return action_record

    async def duplicate_run(
        self, run_id: str, workflow_id: str, duplicate_workflow_obj
    ) -> str:
        original_run = await self.db_async.runs.find_one({"_id": ObjectId(run_id)})
        current_timestamp = datetime.now(timezone.utc)
        if not original_run:
            raise ValueError("Run not found")

        new_run = copy.deepcopy(original_run)
        new_run["name"] = duplicate_workflow_obj.name
        new_run["description"] = duplicate_workflow_obj.description
        new_run["created_at"] = current_timestamp
        new_run["actions"] = []
        new_run["last_modified_at"] = current_timestamp
        new_run["owner_id"] = duplicate_workflow_obj.user_id
        new_run["owner_name"] = duplicate_workflow_obj.user_name
        new_run["workflow_id"] = workflow_id
        new_run["is_template"] = duplicate_workflow_obj.is_template
        new_run["run_status"] = "IDLE"
        new_run.pop("_id", None)  # Allow MongoDB to generate a new ID
        new_run.pop("id", None)  # Allow MongoDB to generate a new ID

        result = await self.db_async.runs.insert_one(new_run)
        return str(result.inserted_id)

    async def duplicate_actions(
        self, run_id: str, new_run_id: str, workflow_id: str, duplicate_workflow_obj
    ) -> str:

        actions = await self.db_async.actions.find({"run_id": run_id}).to_list(None)
        if not actions:
            return []

        new_action_ids = []
        new_actions = []
        # Iterate through all the matching actions
        for action in actions:
            action["action_config"] = self.config_service.load_widget_from_json(
                widget=action["action_config"]
            )
            new_action = copy.deepcopy(action)
            new_action["run_id"] = new_run_id
            new_action["status"] = "IDLE"
            new_action["action_config"] = self.config_service.dump_config_to_json(
                widget=new_action["action_config"]
            ).model_dump()
            new_action.pop("_id", None)  # Allow MongoDB to generate a new ID
            new_action.pop("id", None)
            result = await self.db_async.actions.insert_one(new_action)
            new_action_ids.append(str(result.inserted_id))
            new_actions.append(
                {
                    "action_id": str(result.inserted_id),
                    "urn": new_action["action_config"]["urn"],
                }
            )
            await self.db_async.runs.update_one(
                {"_id": ObjectId(new_run_id)}, {"$set": {"actions": new_actions}}
            )  # TODO Not dumping here to json
        return new_action_ids

    async def duplicate_workflow(self, workflow_id: str, duplicate_workflow_obj) -> str:

        original_workflow = await self.db_async.workflows.find_one(
            {"_id": ObjectId(workflow_id)}
        )
        current_timestamp = datetime.now(timezone.utc)
        if not original_workflow:
            raise ValueError("Workflow not found")

        original_workflow["widgets"] = [
            self.config_service.load_widget_from_json(widget)
            for widget in original_workflow["widgets"]
        ]

        new_workflow = copy.deepcopy(original_workflow)

        new_workflow.pop("_id", None)
        new_workflow.pop("id", None)

        new_workflow["name"] = duplicate_workflow_obj.name
        new_workflow["description"] = duplicate_workflow_obj.description
        new_workflow["created_at"] = current_timestamp
        new_workflow["last_modified_at"] = current_timestamp
        new_workflow["owner_id"] = duplicate_workflow_obj.user_id
        new_workflow["owner_name"] = duplicate_workflow_obj.user_name
        new_workflow["widgets"] = [
            self.config_service.dump_config_to_json(widget).model_dump()
            for widget in new_workflow["widgets"]
        ]
        result = await self.db_async.workflows.insert_one(
            new_workflow
        )  # TODO not dumping here
        return str(result.inserted_id)

    async def create_workflow_session(self, session_data: dict[str, Any]) -> str:
        result = await self.db_async.workflow_sessions.insert_one(
            session_data.model_dump()
        )
        return str(result.inserted_id)

    async def update_rescale_running_info_async(
        self, wf_run_id: str, rescale_running_info: Dict
    ):
        await self.db_async.rescale_runs.update_one(
            {"run_id": wf_run_id}, {"$set": rescale_running_info}
        )
