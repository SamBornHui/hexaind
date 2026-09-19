from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from typing import List, Optional, Union, Tuple
from app.core.dao.dao_base import *
from app.services.data.assets.modules.schemas import Module

class ModulesDao(DaoBase):

    async def insert_module_record_async(self, module: Module) -> str:
        """
        For inserting a record in mongo collection
        """
        result = await self.db_async.modules.insert_one(module.model_dump())
        if not result:
             raise Exception("not able to create modules record")
        
        module_id = str(result.inserted_id)
        
        return module_id
    
    def insert_module_record_sync(self, module: Module) -> str:
        """
        For inserting a record in mongo collection
        """
        result = self.db_sync.modules.insert_one(module.model_dump())
        if not result:
             raise Exception("not able to create modules record")
        
        module_id = str(result.inserted_id)
        
        return module_id

    async def get_all_modules_async(self, projectId: str, search_term: str, page_number: int, page_limit: int, access_mode: str) -> Tuple[List[Module], int]:

        offset = (page_number - 1) * page_limit
        query = {"project_id": projectId, "access_mode": access_mode}

        if search_term:
            search_query = {"$regex": search_term, "$options": "i"} # Case-insensitive search
            query["$or"] = [{"name": search_query}, {"description": search_query},  {"owner_name": search_query}]

        modules_cursor = self.db_async.modules.aggregate(
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

        modules = await modules_cursor.to_list(length=page_limit)

        modules = [Module(**module) for module in modules]

        total_count = await self.db_async.modules.count_documents(query)

        return modules, total_count
    
    def get_module_record_by_id(self, module_id: str) -> Module:

        result = self.db_sync.modules.find_one({"_id": ObjectId(module_id)})
        if not result:
            raise Exception("unable to fetch the module at this moment")
        
        result["_id"] = str(result["_id"])

        return Module(**result)

    async def get_module_records_by_ids_async(self, module_ids: List[str]) -> List[Module]:
        modules_cursor = self.db_async.modules.find({"_id": {"$in": [ObjectId(module_id) for module_id in module_ids]}})
        modules = await modules_cursor.to_list(length=len(module_ids))
        for module in modules:
            module["_id"] = str(module["_id"])
        modules = [Module(**module) for module in modules]
        return modules
    
    async def get_module_record_by_id_async(self, module_id: str) -> Module:

        result = await self.db_async.modules.find_one({"_id": ObjectId(module_id)})
        if not result:
            raise KeyError(f"No modules found with id: {module_id}")

        result["_id"] = str(result["_id"])

        return Module(**result)
    
    async def update_module_record_async(self, module_id: str, module: Module) -> bool:
        result = await self.db_async.modules.update_one({"_id": ObjectId(module_id)}, {"$set": module.model_dump()})
        if result.modified_count == 0:
            raise Exception("unable to update module record")
        
        return True