from typing import Optional, Tuple

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from pymongo import MongoClient
from pymongo.collection import Collection
from bson import ObjectId

from app.config.env_vars import environment

from .schemas import *

class DataCatalogMgntDao:

    def __init__(
        self, db_sync_client: MongoClient, db_async_client: AsyncIOMotorClient
    ):
        self.db_sync_client = db_sync_client
        self.db_async_client = db_async_client

    __collection_name: str = "data_catalog_sessions"

    @property
    def sync_collection(self) -> Collection:
        return self.db_sync_client[environment.hexaind3_database_name][
            self.__collection_name
        ]

    @property
    def async_collection(self) -> AsyncIOMotorCollection:
        return self.db_async_client[environment.hexaind3_database_name][
            self.__collection_name
        ]
    
    async def create_data_catalog_session_async( self, config: MicronDataCatalog) -> Optional[str]:
        
        document = config.model_dump(mode="json", exclude=["id"], by_alias=True)
        result = await self.async_collection.insert_one(document)
        return str(result.inserted_id)

    async def get_datacatalog_session_async(self, session_id: str) -> MicronDataCatalog:

        document = await self.async_collection.find_one({"_id":ObjectId(session_id)})

        document["_id"] = str(document["_id"])

        return MicronDataCatalog(**document)

    def get_datacatalog_session_sync(self, session_id: str) -> MicronDataCatalog:

        document = self.sync_collection.find_one({"_id":ObjectId(session_id)})

        document["_id"] = str(document["_id"])

        return MicronDataCatalog(**document)
        
    async def get_all_datacatalog_sessions_async(self, 
                                                projectId: str, 
                                                search_term: str, 
                                                page_number: int, 
                                                page_limit: int) -> Tuple[List[MicronDataCatalog], int]:
        
        offset = (page_number - 1) * page_limit
        query = {
            "project_id": projectId,
            "$or": [
                {
                    "$and": [
                        {"is_deleted": {"$exists": True}},
                        {"is_deleted": False},
                    ]
                },
                {"is_deleted": {"$exists": False}},
            ]
        }

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

        datacatalog_session_cursor = self.async_collection.aggregate(
            [
                {"$match": query},
                {
                    "$addFields": {
                        "_id": {"$toString": "$_id"},
                        # "created_at": {
                        #     "$dateToString": {
                        #         "format": "%Y-%m-%dT%H:%M:%S.%LZ",
                        #         "date": "$created_at",
                        #     }
                        # },
                    }
                },
                {"$skip": offset},
                {"$limit": page_limit},
            ]
        )

        datacatalog_sessions = await datacatalog_session_cursor.to_list(length=page_limit)

        datacatalog_session_db_records = [
            MicronDataCatalog(**datacatalog_session)
            for datacatalog_session in datacatalog_sessions
        ]

        total_count = await self.async_collection.count_documents(query)

        return datacatalog_session_db_records, total_count
    
    async def update_session_record_with_fd_data_pull_job_id(self, session_id: str, fd_data_pull_job_id: str) -> bool:

        result = await self.async_collection.update_one({"_id":ObjectId(session_id)},
                                                        {"$set": {"data_pull_job_id": fd_data_pull_job_id}}
                                                        )
        return result.modified_count > 0

    async def delete_session(self, session_id: str) -> bool:
        result = await self.async_collection.update_one(
            {"_id": ObjectId(session_id)},
            {"$set": {"is_deleted": True}}
        )
        return result.modified_count > 0