from bson import ObjectId
from typing import List, Any, Dict

from app.core.dao.dao_base import *


class ModelDao(DaoBase):

    def insert_record_sync(self, data, col_name: str = "models") -> str:
        """
        For inserting a record in mongo collection
        """
        result = self.db_sync[col_name].insert_one(data)
        if not result:
            raise Exception("not able to ingest data")

    async def save_model(self, data, col_name: str = None) -> str:
        """
        For inserting a record in mongo collection
        """

        result = await self.db_async[col_name].insert_one(data)
        if not result:
            raise Exception("not able to ingest data into model_temp col")

    async def get_model_by_id_async(self, model_id, project_id) -> List:
        """
        For getting a record in mongo collection
        """
        result = await self.db_async.models.find_one(
            {"_id": model_id, "project_id": project_id}
        )
        return result

    async def update_model_async(
        self, query: Dict, data: Dict, col_name: str = "model_temp"
    ) -> None:
        """
        For updating a record in mongo collection
        """
        await self.db_async[col_name].update_one(query, {"$set": data})

    async def get_models_by_run_id(
        self, run_id, project_id, col_name: str = "models"
    ) -> List:
        """
        For inserting a record in mongo collection
        """
        results = self.db_async[col_name].find(
            {"wf_run_id": run_id, "project_id": project_id}
        )

        model_results = await results.to_list(
            length=None
        )  # Fetch all documents; adjust 'length' as needed.
        if not model_results:
            raise Exception("not able to fetch data")

        return model_results

    async def get_all_models(
        self, project_id: str, search_term: str, page_number: int, page_limit: int
    ) -> List:

        query = {"project_id": project_id, "access_mode": "EXTERNAL"}

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

        offset = (page_number - 1) * page_limit if page_number and page_limit else 0

        models_cursor = self.db_async.models.aggregate(
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

        models = await models_cursor.to_list(length=page_limit)

        return models

    async def delete_all_models(self, project_id: str, query=None) -> Any:

        if query is None:
            query = {"project_id": project_id}

        result = await self.db_async.models.delete_many(query)

        return result

    async def delete_model_by_id(
        self, project_id: str, model_id: str, col_name: str = "models"
    ) -> Any:

        query = {"project_id": project_id, "_id": ObjectId(model_id)}

        result = await self.db_async[col_name].delete_many(query)

        return result

    async def unlink_wf_run_id_from_models(self, query) -> None:
        """
        For unlinking workflow run id from models record in mongo collection
        """
        await self.db_async.models.update_many(
            query, {"$set": {"wf_run_id": ""}}, upsert=True
        )
