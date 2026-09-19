from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import pymongo
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.collection import Collection

from app.core.dao.dao_base import DaoBase
from app.services.data.assets.datasets.schemas import (
    AccessMode,
    ApiJob,
    Dataset,
    DatasetDeleteType,
    MachineLearningModel,
)


class DatasetsDao(DaoBase):
    __collection_name = "datasets"

    @property
    def __async_collection(self) -> AsyncIOMotorCollection:
        return self.db_async[self.__collection_name]

    @property
    def __sync_collection(self) -> Collection:
        return self.db_sync[self.__collection_name]

    async def get_datasets_async(
        self,
        site_id: str,
        project_id: str,
        dataset_type: str,
        search_term: Optional[str] = None,
        page_limit: Optional[int] = None,
        page_number: int = 1,
        access_mode: AccessMode = AccessMode.EXTERNAL,
        file_ext: Optional[str] = None,
    ) -> Tuple[List[Dataset], int]:
        query: Dict[str, Any] = {
            "project_id": project_id,
            "site_id": site_id,
            "access_mode": access_mode.value,
        }  # If no data_type mentioned then fetch all

        if dataset_type:
            query["dataset_type"] = dataset_type

        if file_ext and len(file_ext.strip()) > 0:
            file_ext = file_ext.strip().lower()
            if not file_ext.startswith("."):
                file_ext = "." + file_ext
            query["dataset_location.extension"] = file_ext

        if search_term:
            search_query = {
                "$regex": search_term,
                "$options": "i",
            }  # Case-insensitive search
            query["$or"] = [{"name": search_query}, {"description": search_query}]

        # Build the aggregate pipeline
        pipeline = [
            {"$match": query},
            {
                "$unwind": {
                    "path": "$dataset_location",
                    "preserveNullAndEmptyArrays": True,
                }
            },
            {
                "$addFields": {
                    "dataset_location.last_modified_at": {
                        "$dateToString": {
                            "format": "%Y-%m-%dT%H:%M:%S.%LZ",
                            "date": "$dataset_location.last_modified_at",
                        }
                    }
                }
            },
            {
                "$group": {
                    "_id": "$_id",
                    "root": {"$mergeObjects": "$$ROOT"},
                    "dataset_location": {"$push": "$dataset_location"},
                }
            },
            {
                "$replaceRoot": {
                    "newRoot": {
                        "$mergeObjects": [
                            "$root",
                            {"dataset_location": "$dataset_location"},
                        ]
                    }
                }
            },
            {
                "$addFields": {
                    "id": {"$toString": "$_id"},
                    "created_at": {
                        "$dateToString": {
                            "format": "%Y-%m-%dT%H:%M:%S.%LZ",
                            "date": "$created_at",
                        }
                    },
                }
            },
        ]

        if page_limit and page_limit > 0:
            pipeline.append({"$skip": (page_number - 1) * page_limit})
            pipeline.append({"$limit": page_limit})

        ## HEXAIND-13763 Misuse of await: The property was being awaited, but this is invalid for properties, leading to runtime errors.
        ## @property with async: Combining @property and async creates a coroutine object instead of directly returning the result.
        # datasets_cursor = await self.__async_collection.aggregate(pipeline)
        # total_count = await self.__async_collection.count_documents(query)

        ## to fix HEXAIND-13763 i have switched to using sync method
        datasets_cursor = self.__sync_collection.aggregate(pipeline)
        total_count = self.__sync_collection.count_documents(query)

        datasets_list: List[Dataset] = []
        for dataset in datasets_cursor:
            dataset["_id"] = str(dataset["_id"])
            datasets_list.append(Dataset(**dataset))

        return (datasets_list, total_count)

    async def get_dataset_by_id_async(self, dataset_id: str) -> Dataset:
        dataset = await self.__async_collection.find_one({"_id": ObjectId(dataset_id)})

        if not dataset:
            raise KeyError("not able to find the dataset")

        dataset["_id"] = str(dataset["_id"])
        dataset = Dataset(**dataset)
        return dataset

    def get_datasets_by_qry_sync(self, query: dict) -> Optional[List[Dataset]]:
        datasets_dict = self.db_sync.datasets.find(query)
        if datasets_dict is None:
            return None

        dataset_obj_list = []
        for dataset in datasets_dict:
            dataset["_id"] = str(dataset["_id"])
            dataset_obj_list.append(Dataset(**dataset))
        return dataset_obj_list

    def get_dataset_by_id(self, dataset_id: str) -> Dataset:
        dataset = self.__sync_collection.find_one({"_id": ObjectId(dataset_id)})

        if not dataset:
            raise Exception("not able to find the dataset")

        dataset["_id"] = str(dataset["_id"])
        dataset = Dataset(**dataset)
        return dataset

    async def get_dataset_by_name(self, name: str, project_id: str) -> Dataset:
        dataset = await self.__async_collection.find_one(
            {"name": name, "project_id": project_id}
        )
        if not dataset:
            raise KeyError(f"Unable to find dataset with {name} and {project_id}")
        dataset["_id"] = str(dataset["_id"])
        return Dataset(**dataset)

    def get_dataset_by_name_sync(self, name: str, project_id: str) -> Dataset:
        dataset = self.__sync_collection.find_one(
            {"name": name, "project_id": project_id}, sort=[("_id", pymongo.DESCENDING)]
        )
        if not dataset:
            raise KeyError(f"Unable to find dataset with {name} and {project_id}")
        dataset["_id"] = str(dataset["_id"])
        return Dataset(**dataset)

    async def delete_dataset_by_id_async(self, dataset_id: str) -> bool:
        result = await self.__async_collection.delete_one({"_id": ObjectId(dataset_id)})

        return result.deleted_count > 0

    async def delete_machine_learning_model_by_id_async(
        self, machine_learning_model_record_id: str
    ) -> bool:
        result = await self.db_async.machine_learning_models.delete_one(
            {"_id": ObjectId(machine_learning_model_record_id)}
        )

        return result.deleted_count > 0

    def insert_dataset_record(self, dataset: Dataset) -> str:
        """
        For inserting a record in mongo collection
        """
        result = self.__sync_collection.insert_one(dataset.model_dump())
        if not result:
            raise Exception("not able to create dataset record")

        dataset_id = str(result.inserted_id)
        return dataset_id

    async def insert_dataset_record_async(self, dataset: Dataset) -> str:
        """
        For inserting a record in mongo collection
        """

        result = await self.__async_collection.insert_one(dataset.model_dump())
        if not result:
            raise Exception("not able to create dataset record")

        dataset_id = str(result.inserted_id)

        return dataset_id

    async def delete_dataset_record_async(
        self, dataset_id: str, dataset_delete_type: DatasetDeleteType
    ):
        match dataset_delete_type:
            case DatasetDeleteType.HARD:
                raise NotImplementedError("Currently, HARD delete is not supported.")
            case DatasetDeleteType.SOFT:
                result = await self.__async_collection.update_one(
                    {"_id": ObjectId(dataset_id)},
                    {"$set": {"access_mode": AccessMode.INTERNAL}},
                )
                success = result.matched_count > 0 and result.modified_count > 0
        if not success:
            raise Exception(
                f"Unable to {dataset_delete_type} delete dataset: {dataset_id}, {result}"
            )

    async def delete_module_record_async(
        self, dataset_id: str, dataset_delete_type: DatasetDeleteType
    ):
        match dataset_delete_type:
            case DatasetDeleteType.HARD:
                raise NotImplementedError("Currently, HARD delete is not supported.")
            case DatasetDeleteType.SOFT:
                result = await self.db_async.modules.update_one(
                    {"_id": ObjectId(dataset_id)},
                    {"$set": {"access_mode": AccessMode.INTERNAL}},
                )
                success = result.matched_count > 0 and result.modified_count > 0
        if not success:
            raise Exception(
                f"Unable to {dataset_delete_type} delete module: {dataset_id}, {result}"
            )

    def insert_machine_learning_model_record(self, model: MachineLearningModel) -> str:
        """
        For inserting the machine learning model record
        """
        result = self.db_sync.machine_learning_models.insert_one(model.model_dump())

        if not result:
            raise Exception("not able to create machine learning model record")

        record_id = str(result.inserted_id)

        return record_id

    async def get_machine_learning_model_by_id_async(
        self, machine_learning_model_id: str
    ) -> MachineLearningModel:
        ml_model = await self.db_async.machine_learning_models.find_one(
            {"_id": ObjectId(machine_learning_model_id)}
        )

        if not ml_model:
            raise KeyError("not able to find the ml model")

        ml_model["_id"] = str(ml_model["_id"])
        ml_model = MachineLearningModel(**ml_model)
        return ml_model

    def update_dataset_record_access_mode(
        self, dataset_id: str, name: str, description: str, access_mode: AccessMode
    ) -> bool:
        """
        For updating the access mode of the record (INTERNAL: not visible on assests, EXTERNAL: visible on assests)
        """

        result = self.__sync_collection.update_one(
            {"_id": ObjectId(dataset_id)},
            {
                "$set": {
                    "access_mode": access_mode,
                    "name": name,
                    "description": description,
                }
            },
        )

        return result.matched_count > 0 and result.modified_count > 0

    async def update_dataset_name_async(
        self, dataset_id: str, name: str, last_modified_by: str
    ) -> bool:
        result = await self.__async_collection.update_one(
            {"_id": ObjectId(dataset_id)},
            {
                "$set": {
                    "name": name,
                    "dataset_location.0.last_modified_by": last_modified_by,
                    "dataset_location.0.last_modified_at": datetime.now(timezone.utc),
                }
            },
        )
        return result.matched_count > 0 and result.modified_count > 0

    def update_dataset_path_sync(self, dataset_id: str, updated_path: str):
        result = self.__sync_collection.update_one(
            {"_id": ObjectId(dataset_id)},
            {"$set": {"dataset_location.$[].path": updated_path}},
        )

        return result.matched_count > 0 and result.modified_count > 0

    def replace_dataset_record(self, dataset: Dataset) -> bool:
        result = self.__sync_collection.replace_one(
            {"_id": ObjectId(dataset.id)}, dataset.model_dump()
        )
        return result.matched_count > 0 and result.modified_count > 0

    def update_datset_statistics_preview_total_count(
        self,
        dataset_id: str,
        numerical_stats_file: Optional[str] = None,
        categorical_stats_file: Optional[str] = None,
        preview_file_path: Optional[str] = None,
        total_row_count: Optional[int] = None,
        total_col_count: Optional[int] = None,
        total_numeric_col_count: Optional[int] = None,
        total_categorical_count: Optional[int] = None,
    ) -> bool:
        # Prepare update fields
        update_fields = {}
        prefix = "dataset_information.0."
        if preview_file_path is not None:
            update_fields[prefix + "preview_file"] = preview_file_path

        if numerical_stats_file is not None or categorical_stats_file is not None:
            update_fields[prefix + "numerical_statistics_file"] = numerical_stats_file
            update_fields[prefix + "categorical_statistics_file"] = (
                categorical_stats_file
            )

        if total_row_count is not None:
            update_fields[prefix + "row_count"] = total_row_count

        if total_col_count is not None:
            update_fields[prefix + "col_count"] = total_col_count

        if total_numeric_col_count is not None:
            update_fields[prefix + "numerical_col_count"] = total_numeric_col_count

        if total_categorical_count is not None:
            update_fields[prefix + "categorical_col_count"] = total_categorical_count

        if not update_fields:
            return False
        result = self.__sync_collection.update_one(
            {"_id": ObjectId(dataset_id)}, {"$set": update_fields}
        )
        return result.matched_count > 0 and result.modified_count > 0

    def update_dataset_record_data(
        self, dataset_id: str, key_to_update: str, data: Any
    ) -> bool:
        result = self.__sync_collection.update_one(
            {"_id": ObjectId(dataset_id)},
            {"$set": {f"{str(key_to_update)}": data}},
        )
        return result.matched_count > 0 and result.modified_count > 0

    def insert_api_jobs_record(self, api_job: ApiJob) -> str:
        """
        For inserting the preview stats record
        """
        result = self.db_sync.api_jobs.insert_one(api_job.model_dump())

        if not result:
            raise Exception("not able to create preview stats record")

        record_id = str(result.inserted_id)

        return record_id

    def update_preview_stats_record(
        self, api_job_id: str, key_to_update: str, data: Any
    ) -> bool:
        result = self.db_sync.api_jobs.update_one(
            {"_id": ObjectId(api_job_id)},
            {"$set": {f"{str(key_to_update)}": data}},
        )
        return result.matched_count > 0 and result.modified_count > 0

    def get_api_job_record_by_id(
        self, api_job_id: Optional[str] = None, search_query: Optional[dict] = None
    ) -> Optional[ApiJob]:
        query = {}
        if api_job_id:
            query["_id"] = ObjectId(api_job_id)

        if search_query:
            query.update(search_query)

        if not query:
            return None

        job_record = self.db_sync.api_jobs.find_one(query)

        if not job_record:
            return None

        job_record["_id"] = str(job_record["_id"])
        job_record = ApiJob(**job_record)
        return job_record

    def delete_api_jobs_record(self, api_job_id: str) -> bool:
        result = self.db_sync.api_jobs.delete_one({"_id": ObjectId(api_job_id)})
        return result.deleted_count > 0
