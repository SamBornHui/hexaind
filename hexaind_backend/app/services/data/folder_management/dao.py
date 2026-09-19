from typing import Tuple, List
from bson import ObjectId
from app.core.dao.dao_base import DaoBase
from app.services.data.assets.datasets.schemas import Dataset, DatasetType, AccessMode
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.env_vars import environment


class FolderManagementDao(DaoBase):

    # TODO: optimize this method to improve performance
    def get_datasets_based_on_path_prefix(
        self,
        path_prefix: str,
        page_number: int,
        page_length: int,
        additional_filters: dict = None,
    ) -> Tuple[List[Dataset], int]:
        query = {
            "dataset_location": {"$elemMatch": {"path": {"$regex": f"^{path_prefix}"}}}
        }
        if additional_filters is not None:
            query.update(additional_filters)
        skip_count = (page_number - 1) * page_length
        datasets = self.db_sync.datasets.find(
            query
        )  # .skip(skip_count).limit(page_length) ignore skip and limit temporaryly
        total_count = self.db_sync.datsets.count_documents(query)
        datasets_list = []
        for dataset in datasets:
            dataset["_id"] = str(dataset["_id"])
            datasets_list.append(Dataset(**dataset))
        return (datasets_list, total_count)

    async def get_document(self, filter_document: dict = None, collection: str = None):
        model_document = await self.db_async[collection].find_one(filter_document)
        return model_document

    async def update_document(
        self,
        filter_document: dict = None,
        new_value: dict = None,
        collection: str = None,
    ):
        await self.db_async[collection].update_one(filter_document, {"$set": new_value})

    def update_document_sync(
        self,
        filter_document: dict = None,
        new_value: dict = None,
        collection: str = None,
    ):
        self.db_sync[collection].update_one(filter_document, {"$set": new_value})

    async def get_all_document(
        self, filter_document: dict = None, collection: str = None
    ):
        cursor = self.db_async[collection].find(filter_document)
        model_documents = await cursor.to_list(length=None)
        return model_documents

    async def insert_document(self, value: dict = None, collection: str = None):
        await self.db_async[collection].insert_one(value)

    def insert_document_sync(self, value: dict = None, collection: str = None):
        self.db_sync[collection].insert_one(value)

    async def delete_document(
        self, filter_document: dict = None, collection: str = None
    ):
        result = await self.db_async[collection].delete_one(filter_document)
        return result

    def delete_document_sync(
        self, filter_document: dict = None, collection: str = None
    ):
        result = self.db_sync[collection].delete_one(filter_document)
        return result

    # sync functions
    def get_document_sync(self, filter_document: dict = None, collection: str = None):
        model_document = self.db_sync[collection].find_one(filter_document)
        return model_document

    def get_all_document_sync(
        self, filter_document: dict = None, collection: str = None
    ):
        if filter_document is None:
            filter_document = {}

        if collection is None:
            raise ValueError("Collection name must be provided")

        # Retrieve the documents using pymongo's synchronous API
        cursor = self.db_sync[collection].find(filter_document)

        # Convert cursor to a list (this is synchronous in pymongo)
        model_documents = list(cursor)

        return model_documents
