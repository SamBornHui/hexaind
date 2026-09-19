from typing import List, AsyncGenerator

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from pymongo import MongoClient
from pymongo.collection import Collection

from app.config.env_vars import environment

from .schemas import JupyterServer, PydanticObjectId


class JupyterServerDao:

    def __init__(
        self, db_sync_client: MongoClient, db_async_client: AsyncIOMotorClient
    ):
        self.db_sync_client = db_sync_client
        self.db_async_client = db_async_client

    __collection_name: str = "jupyter_server"

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

    def get_jupyter_server_by_id(self, _id: PydanticObjectId) -> JupyterServer | None:
        document = self.sync_collection.find_one({"_id": _id})
        if document is None:
            return None
        return JupyterServer(**document)

    async def get_jupyter_server_by_id_async(
        self, _id: PydanticObjectId
    ) -> JupyterServer | None:
        document = await self.async_collection.find_one({"_id": _id})
        if document is None:
            return None
        return JupyterServer(**document)

    def create_jupyter_server(self, jupyter_server: JupyterServer) -> PydanticObjectId:
        result = self.sync_collection.insert_one(
            jupyter_server.model_dump(
                by_alias=True,
                exclude=list(jupyter_server.model_computed_fields),
            )
        )
        return PydanticObjectId(result.inserted_id)

    async def create_jupyter_server_async(
        self, jupyter_server: JupyterServer
    ) -> PydanticObjectId:
        result = await self.async_collection.insert_one(
            jupyter_server.model_dump(
                by_alias=True,
                exclude=list(jupyter_server.model_computed_fields),
            )
        )
        return PydanticObjectId(result.inserted_id)

    def get_jupyter_server_by_project_id(
        self, project_id: PydanticObjectId
    ) -> JupyterServer | None:
        document = self.sync_collection.find_one({"project_id": str(project_id)})
        if document is None:
            return None
        return JupyterServer(**document)

    async def get_jupyter_server_by_project_id_async(
        self, project_id: PydanticObjectId
    ) -> JupyterServer | None:
        document = await self.async_collection.find_one({"project_id": str(project_id)})
        if document is None:
            return None
        return JupyterServer(**document)

    def replace_jupyter_server(self, jupyter_server: JupyterServer):
        self.sync_collection.replace_one(
            {"project_id": jupyter_server.project_id},
            jupyter_server.model_dump(
                by_alias=True,
                exclude=list(jupyter_server.model_computed_fields),
            ),
        )

    async def replace_jupyter_server_async(self, jupyter_server: JupyterServer):
        await self.async_collection.replace_one(
            {"project_id": jupyter_server.project_id},
            jupyter_server.model_dump(
                by_alias=True,
                exclude=list(jupyter_server.model_computed_fields),
            ),
        )

    def delete_jupyter_server_by_project_id(self, project_id: PydanticObjectId):
        self.sync_collection.delete_many({"project_id": str(project_id)})

    async def delete_jupyter_server_by_project_id_async(
        self, project_id: PydanticObjectId
    ):
        await self.async_collection.delete_one({"project_id": str(project_id)})

    def get_jupyter_servers(self) -> List[JupyterServer]:
        return list(self.sync_collection.find({}))

    async def get_jupyter_servers_async(self) -> AsyncGenerator[JupyterServer, None]:
        async for jupyter_server in self.async_collection.find({}):
            yield JupyterServer(**jupyter_server)

    async def get_jupyter_servers_in_project_async(
        self, project_id: PydanticObjectId
    ) -> AsyncGenerator[JupyterServer, None]:
        async for jupyter_server in self.async_collection.find(
            {"project_id": str(project_id)}
        ):
            yield JupyterServer(**jupyter_server)
