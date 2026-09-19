from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from app.config.env_vars import environment
from app.core.db.db_utils import close_db_sync, get_db_async, get_db_sync


class DaoBase:

    def __init__(
        self,
        db_sync_client: Optional[MongoClient] = None,
        db_async_client: Optional[AsyncIOMotorClient] = None,
    ):
        self.db_sync_client = db_sync_client
        self.db_async_client = db_async_client
        self._db_sync_client_created = False
        self._db_async_client_created = False

        if self.db_sync_client is None:
            self.db_sync_client = get_db_sync()
            self._db_sync_client_created = True
        self.db_sync = self.db_sync_client[environment.hexaind3_database_name]

        if self.db_async_client is None:
            self.db_async_client = get_db_async()
            self._db_async_client_created = True
        self.db_async = self.db_async_client[environment.hexaind3_database_name]

    def __del__(self):
        if self.db_sync_client and self._db_sync_client_created:
            close_db_sync(self.db_sync_client)
