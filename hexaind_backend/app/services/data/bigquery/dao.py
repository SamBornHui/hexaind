from typing import List, Tuple

from bson import ObjectId

from app.core.dao.dao_base import DaoBase
from app.services.admin.connectors.schemas import Query


class BigQueryDao(DaoBase):

    async def create_query_async(self, query: Query) -> str:

        result = await self.db_async.queries.insert_one(query.model_dump())
        if not result:
            raise ValueError("not able to create query")

        query_id = str(result.inserted_id)

        return query_id

    async def get_query_by_id_async(self, query_id: str) -> Query:

        query = await self.db_async.queries.find_one({"_id": ObjectId(query_id)})

        if not query:
            raise KeyError("Query not found")

        query["_id"] = str(query["_id"])

        return Query(**query)

    async def get_all_queries_async(
        self, project_id: str, search_term: str, page_number: int, page_limit: int
    ) -> Tuple[List[Query], int]:

        query = {"project_id": project_id}

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

        queries_cursor = self.db_async.queries.aggregate(
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

        queries = await queries_cursor.to_list(length=page_limit)

        total_count = await self.db_async.queries.count_documents(query)

        return (queries, total_count)

    async def update_query_async(self, query_id: str, query: Query) -> bool:

        result = await self.db_async.queries.find_one_and_update(
            {"_id": ObjectId(query_id)}, {"$set": query.model_dump()}
        )
        if not result:
            raise ValueError("Unable to update query")

        return True

    async def delete_query_async(self, query_id: str) -> bool:

        result = await self.db_async.queries.delete_one({"_id": ObjectId(query_id)})

        return result.deleted_count > 0

    def get_query(self, query_id: str) -> Query:

        result = self.db_sync.queries.find_one({"_id": ObjectId(query_id)})

        if not result:
            raise ValueError("query not found")

        result["_id"] = str(result["_id"])

        return Query(**result)
