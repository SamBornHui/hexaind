from typing import List, Optional
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient

from bson import ObjectId

from app.core.dao.dao_base import DaoBase
from app.core.schemas.action_result import ActionResult
from app.core.services.action.schemas import Action, ActionRunStatus, Widget
from app.services.workflows.workflow_utils import WFConfigService


class ActionsDao(DaoBase):

    def __init__(
        self,
        db_sync_client: Optional[MongoClient] = None,
        db_async_client: Optional[AsyncIOMotorClient] = None,
    ):
        super().__init__(db_sync_client=db_sync_client, db_async_client=db_async_client)
        self.config_service = WFConfigService()

    async def create_action_async(self, action: Action) -> str:

        action.action_config = self.config_service.dump_config_to_json(widget=action.action_config)
        
        result = await self.db_async.actions.insert_one(action.model_dump())

        if not result:
            raise Exception("not able to create action")
        
        return str(result.inserted_id)

    async def get_action_by_action_id_async(self, action_id: str) -> Action:
        
        action_record: Optional[Action] = await self.db_async.actions.find_one({'_id': ObjectId(action_id)})
        if not action_record: 
            raise Exception("Action Record not found")
        
        # action_record["action_config"] = self.config_service.load_widget_from_json(widget=action_record["action_config"])
        action_record["_id"] = str(action_record["_id"])
        action_record = Action(**action_record)

        return action_record
    
    async def update_action_config_by_action_id_async(self, action_id: str, new_action_config: Widget):

        if new_action_config.config_file_path:
            new_action_config = self.config_service.dump_config_to_json(widget=new_action_config)

        await self.db_async.actions.find_one_and_update(
                                                        {"_id": ObjectId(action_id)},
                                                        {"$set": {"action_config": new_action_config.model_dump()}},
                                                        return_document=True
                                                        ) 
        
    async def delete_action_record_by_action_id_async(self, action_id: str) -> bool:

        result = await self.db_async.actions.delete_one({'_id': ObjectId(action_id)})
        
        return result.deleted_count > 0  
    
    async def update_action_record_by_action_id_async(self, action_id: str, action_record: Action) -> bool:

        if action_record.action_config.config_file_path:
            action_record.action_config = self.config_service.dump_config_to_json(widget=action_record.action_config)

        result = await self.db_async.actions.find_one_and_update(
                                                    {"_id": ObjectId(action_id)},
                                                    {"$set": action_record.model_dump()},
                                                    return_document=True
                                                    )
        
        if not result:
            raise Exception("failed to update the action")
        
        return True
    
    async def update_action_record_delete_on_complete_async(self, action_id: str,  delete_on_complete: bool) -> bool:
        
        result = await self.db_async.actions.find_one_and_update(
                                                    {"_id": ObjectId(action_id)},
                                                    {'$set': {'delete_on_complete': delete_on_complete}},
                                                    return_document=True
                                                    )
        
        if not result:
            raise Exception("failed to update the action")
        
        return True
    
    async def update_action_record_status_async(self, action_id: str, status: ActionRunStatus) -> bool:

        result = await self.db_async.actions.find_one_and_update(
                                                    {"_id": ObjectId(action_id)},
                                                    {'$set': {'status': status.value}},
                                                    return_document=True
                                                    )
        
        if not result:
            raise Exception("failed to update the action")
        
        return True
    
    async def get_actions_by_run_id_async(self, run_id: str) -> List[Action]:

        actions_cursor = self.db_async.actions.find({'run_id': run_id}) 
        
        actions = []
        async for action in actions_cursor:
            action["_id"] = str(action["_id"])
            # action["action_config"] = self.config_service.load_widget_from_json(widget=action["action_config"])
            actions.append(Action(**action))
            
        return actions
    
    async def get_action_by_urn_async(self, run_id: str, urn: str) -> Action:

        action_record = await self.db_async.actions.find_one({'run_id': run_id, "action_config.urn": urn})

        if not action_record: 
            raise Exception("Action Record not found")
        
        # action_record["action_config"] = self.config_service.load_widget_from_json(widget=action_record["action_config"])
        action_record["_id"] = str(action_record["_id"])
        action_record = Action(**action_record)

        return action_record
    
    async def get_action_record_by_run_id_and_urn_async(self, run_id: str, urn: str) -> Action:
        
        action_record: Action = await self.db_async.actions.find_one({'run_id': run_id, "action_config.urn": urn})

        if not action_record: 
            raise Exception("Action Record not found")
        
        # action_record["action_config"] = self.config_service.load_widget_from_json(widget=action_record["action_config"])
        action_record["_id"] = str(action_record["_id"])
        action_record = Action(**action_record)
        
        return action_record
    
    async def get_action_results_by_ids_async(self, result_ids: List[str]) -> List[ActionResult]:

        action_results_cursor = self.db_async.action_results.find({'_id': {'$in': [ObjectId(id) for id in result_ids]}})

        action_results_records = []
        async for record in action_results_cursor:
            record["_id"] = str(record["_id"])
            action_results_records.append(ActionResult(**record))

        if not action_results_records:
            raise Exception("Failed to get the action results")
    
        return action_results_records

    async def get_actions_from_list_of_action_ids_async(self, action_ids: List[str]) -> List[Action]:
        """Get the actions from the list of action ids.

        Args:
            action_ids (List[str]): List of action ids.

        Returns:
            List[Action]: List of actions.
        """
        cursor = self.db_async.actions.find({'_id': {'$in': [ObjectId(id) for id in action_ids]}})
        
        actions = []
        async for action in cursor:
            action["_id"] = str(action["_id"])
            # action["action_config"] = self.config_service.load_widget_from_json(widget=action["action_config"])
            actions.append(Action(**action))
        
        if len(actions) != len(action_ids):
            raise Exception("Failed to get the actions.")
        
        return actions