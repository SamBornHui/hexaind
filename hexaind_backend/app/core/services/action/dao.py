from app.core.dao.dao_base import *
from app.services.workflows.workflow_utils import WFConfigService
from .schemas import *
from app.core.schemas.action_result import *
from bson import ObjectId

class ActionsDao(DaoBase):

    def __init__(
        self,
        db_sync_client: Optional[MongoClient] = None,
        db_async_client: Optional[AsyncIOMotorClient] = None,
    ):
        super().__init__(db_sync_client=db_sync_client, db_async_client=db_async_client)
        self.config_service = WFConfigService()
    
    def update_and_get_action_status(self, id: str, status: ActionRunStatus) -> Action:

        action_record = self.db_sync.actions.find_one_and_update({'_id': ObjectId(id)}, {'$set': {'status': status.value}}, return_document=True)
        if not action_record: 
            raise Exception("Unable to change the action state")
        
        action_record["_id"] = str(action_record["_id"])
        # action_record["action_config"] = self.config_service.load_widget_from_json(widget=action_record["action_config"])

        action_record = Action(**action_record)

        return action_record
    
    def update_action_custom_run_state(self, action_id: str, custom_run_state: CustomRunState) -> Action:

        action_record = self.db_sync.actions.find_one_and_update({'_id': ObjectId(action_id)}, 
                                                                 {'$set': {'custom_run_state': custom_run_state.model_dump()}},
                                                                 return_document=True
                                                                 )

        if not action_record: 
            raise Exception("Unable to change the action run state")
        
        action_record["_id"] = str(action_record["_id"])
        # action_record["action_config"] = self.config_service.load_widget_from_json(widget=action_record["action_config"])
        action_record = Action(**action_record)

        return action_record
    
    def get_action_by_id(self, id: str) -> Action:

        action_record = self.db_sync.actions.find_one({'_id': ObjectId(id)})

        if not action_record: 
            raise Exception("Action Record not found")
        
        action_record["_id"] = str(action_record["_id"])
        # action_record["action_config"] = self.config_service.load_widget_from_json(widget=action_record["action_config"])

        action_record = Action(**action_record)

        return action_record
    
    async def get_actions_by_run_id_async(self, run_id: str) -> List[Action]:

        actions_cursor = self.db_async.actions.find({'run_id': run_id}) 
        
        actions = []
        async for action in actions_cursor:
            action["_id"] = str(action["_id"])
            # action["action_config"] = self.config_service.load_widget_from_json(widget=action["action_config"])

            actions.append(Action(**action))
            
        return actions

    def get_action_by_urn(self, run_id: str, urn: str) -> Action:

        action_record = self.db_sync.actions.find_one({'run_id': run_id, "action_config.urn": urn})

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
    
    def get_action_record_by_run_id_and_urn(self, run_id: str, urn: str) -> Action:

        action_record: Action =  self.db_sync.actions.find_one({'run_id': run_id, "action_config.urn": urn})

        if not action_record: 
            raise Exception("Action Record not found")
        
        # action_record["action_config"] = self.config_service.load_widget_from_json(widget=action_record["action_config"])
        action_record["_id"] = str(action_record["_id"])
        action_record = Action(**action_record)
        
        return action_record
    
    def processed_subactions_update(self, action_id: str, processed_subactions: List=[]) -> Action:
        
        action_record = self.db_sync.actions.find_one_and_update({'_id': ObjectId(action_id)}, {'$push': {'processed_sub_action_ids': {'$each': processed_subactions}}}, return_document=True)
        action_record["_id"] = str(action_record["_id"])
        # action_record["action_config"] = self.config_service.load_widget_from_json(widget=action_record["action_config"])
        action_record = Action(**action_record)
        return action_record
        
    def update_action_status_and_result(self, id: str, status: ActionRunStatus, action_result_id: str or list, append_results: bool=True) -> Action:

        if append_results:
            if isinstance(action_result_id, str):
                action_record = self.db_sync.actions.find_one_and_update({'_id': ObjectId(id)}, {'$push': {'result_ids': action_result_id}, '$set': {'status': status.value}}, return_document=True)
            
            elif isinstance(action_result_id, list):
                action_record = self.db_sync.actions.find_one_and_update({'_id': ObjectId(id)}, {'$push': {'result_ids': {'$each': action_result_id}}, '$set': {'status': status.value}}, return_document=True)
        
        else:
            if isinstance(action_result_id, str):
                action_record = self.db_sync.actions.find_one_and_update({'_id': ObjectId(id)}, {'$set': {'result_ids': [action_result_id], 'status': status.value}}, return_document=True)
            
            elif isinstance(action_result_id, list):
                action_record = self.db_sync.actions.find_one_and_update({'_id': ObjectId(id)}, {'$set': {'result_ids':  action_result_id, 'status': status.value}}, return_document=True)

        if not action_record: 
            raise Exception("Unable to change the action status and result")
        
        action_record["_id"] = str(action_record["_id"])

        # action_record["action_config"] = self.config_service.load_widget_from_json(widget=action_record["action_config"])

        action_record = Action(**action_record)

        return action_record
    
    async def create_action(self, action: Action) -> str:

        action.action_config = self.config_service.dump_config_to_json(widget=action.action_config)

        result = await self.db_async.actions.insert_one(action.model_dump())

        if not result:
            raise Exception("not able to create action")
        
        return str(result.inserted_id)
    
    
    def create_actions_sync(self, actions: List[Action]) -> List[str]:

        for action in actions:
            action.action_config = self.config_service.dump_config_to_json(widget=action.action_config)

        actions_dicts = [action.model_dump() for action in actions]
        
        result = self.db_sync.actions.insert_many(actions_dicts)
        
        if not result:
            raise Exception("not able to create actions")
        
        return [str(id) for id in result.inserted_ids]
    
    def update_action_status_atomic(self, action_id: str, expected_status: ActionRunStatus, actual_status: ActionRunStatus):
        updated = self.db_sync.actions.find_one_and_update(
            {"_id": ObjectId(action_id), "status": expected_status},
            {"$set": {"status": actual_status}},
            return_document=True
        )

        if not updated:
            raise Exception("Failed to update the action status")
        
        return True
    
    def update_celery_task_id_in_action_record_sync(self, action_id: str, celery_task_id: str):

        self.db_sync.actions.find_one_and_update(
            {"_id": ObjectId(action_id)},
            {"$set": {"celery_task_id": celery_task_id}},
            return_document=True
            )
    
    def update_sub_actions_sync(self, action_id: str, sub_action_ids: List[str]) -> bool:

        updated = self.db_sync.actions.find_one_and_update(
            {"_id": ObjectId(action_id)},
            {'$push': {'sub_action_ids': {'$each': sub_action_ids}}},
            return_document=True
            )

        if not updated:
            raise Exception("Failed to update the action with sub_action_ids")
        
        return True

    def get_sub_actions_status(self, action_id: str) -> list[ActionRunStatus]:
        
        results = []
        action_record: Action = self.get_action_by_id(id=action_id)

        if not action_record.sub_action_ids:
            return []
        
        sub_action_records = self.db_sync.actions.find({
            '_id': {'$in': [ObjectId(sub_id) for sub_id in action_record.sub_action_ids]}
            })
        
        results = [str(sub_action['_id']) in action_record.sub_action_ids and sub_action['status'] for sub_action in sub_action_records]

        return results