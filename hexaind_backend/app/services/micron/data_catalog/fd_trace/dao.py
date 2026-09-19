from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from pymongo import MongoClient
from pymongo.collection import Collection
from app.config.env_vars import environment

from .schemas import *


class FdTraceDao:

    def __init__(
        self, db_sync_client: MongoClient, db_async_client: AsyncIOMotorClient
    ):
        self.db_sync_client = db_sync_client
        self.db_async_client = db_async_client

    __collection_name: str = "fd_trace_data_pull"

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
    
    async def create_fd_data_pull_config_async(self, fd_data_pull_config: FdDataPullConfig) -> str:
        result = await self.sync_collection.insert_one(fd_data_pull_config.model_dump(mode="json", exclude=["id"], by_alias=True))
        return str(result.inserted_id)
