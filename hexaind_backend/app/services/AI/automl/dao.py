from bson import ObjectId
from typing import List, Any

from app.core.dao.dao_base import *

class AutoMLDao(DaoBase):
    def insert_automl_record_sync(self, data, col_name: str='model_temp') -> str:
        """
        For inserting a record in mongo collection
        """
        result = self.db_sync[col_name].insert_one(data)
        if not result:
             raise Exception("not able to ingest data into model_temp col")

    async def save_model(self, data, col_name: str=None) -> str:
        """
        For inserting a record in mongo collection
        """

        model_name = data['model']['name']
    
        # Check if a model with the same name already exists
        existing_model = await self.db_async[col_name].find_one({"model.name": model_name})
        if existing_model:
            raise
        
        result = await self.db_async[col_name].insert_one(data)
        if not result:
             raise Exception("not able to ingest data into model_temp col") 
    
    async def get_models_by_run_id(self, run_id, project_id, col_name: str='model_temp') -> List:
        """
        For inserting a record in mongo collection
        """
        results = self.db_async[col_name].find({'wf_run_id': run_id, 'project_id': project_id})

        model_results = await results.to_list(length=None)  # Fetch all documents; adjust 'length' as needed.
        if not model_results:
             raise Exception("not able to fetch data from model_temp col")

        return model_results
    
    async def get_all_models(self, project_id: str, search_term: str, page_number: int, page_limit: int) -> List:

        query = {"project_id": project_id}

        if search_term:
            search_query = {"$regex": search_term, "$options": "i"} # Case-insensitive search
            query["$or"] = [{"name": search_query}, {"description": search_query},  {"owner_name": search_query}]

        offset = (page_number - 1) * page_limit if page_number and page_limit else 0

        models_cursor = self.db_async.models.aggregate(
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

        models = await models_cursor.to_list(length=page_limit)

        return models

    async def delete_all_models(self, project_id: str) -> Any:

        query = {"project_id": project_id}

        result = await self.db_async.models.delete_many(query)

        return result

    async def delete_model_by_id(self, project_id: str, model_id: str) -> Any:

        query = {"project_id": project_id, '_id': ObjectId(model_id)}

        result = await self.db_async.models.delete_many(query)

        return result