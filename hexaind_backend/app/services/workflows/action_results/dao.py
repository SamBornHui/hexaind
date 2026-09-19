from app.core.dao.dao_base import *
from .schemas import *
from bson import ObjectId

class ActionResultsDao(DaoBase):

    def create_result(self, result: ActionResult) -> str:

        result = self.db_sync.action_results.insert_one(result.model_dump())

        if not result:
            raise Exception("Failed to create dataset")
        
        return str(result.inserted_id)
    
    async def get_action_result_by_id_async(self, result_id: str) -> ActionResult:

        result_record = await self.db_async.action_results.find_one({'_id':ObjectId(result_id)})

        if not result_record:
            raise Exception("Failed to get the action result")
        
        result_record["_id"] = str(result_record["_id"])
        return ActionResult(**result_record)

    async def delete_action_result_by_id_async(self, result_id: str) -> bool:

        result = await self.db_async.action_results.delete_one({'_id': ObjectId(result_id)})
        
        return result.deleted_count > 0  
    
    def get_action_result_by_id(self, result_id: str) -> ActionResult:

        result_record =  self.db_sync.action_results.find_one({'_id':ObjectId(result_id)})

        if not result_record:
            raise Exception("Failed to get the action result")
        
        result_record["_id"] = str(result_record["_id"])
        return ActionResult(**result_record)
    
    async def get_action_results_by_ids_async(self, result_ids: List[str]) -> List[ActionResult]:

        action_results_cursor = self.db_async.action_results.find({'_id': {'$in': [ObjectId(id) for id in result_ids]}})

        action_results_records = []
        async for record in action_results_cursor:
            record["_id"] = str(record["_id"])
            action_results_records.append(ActionResult(**record))

        if not action_results_records:
            raise Exception("Failed to get the action results")
    
        return action_results_records
    
    def get_action_results_by_ids(self, result_ids: List[str]) -> List[ActionResult]:

        action_results_cursor = self.db_sync.action_results.find({'_id': {'$in': [ObjectId(id) for id in result_ids]}})

        action_results_records = []
        for record in action_results_cursor:
            record["_id"] = str(record["_id"])
            action_results_records.append(ActionResult(**record))

        if not action_results_records:
            raise Exception("Failed to get the action results")
    
        return action_results_records
        


