import logging
from bson import ObjectId
from typing import List, Optional, Union, Tuple

from .schemas import SAMUseCase

from app.core.dao.dao_base import *
from app.services.data.assets.datasets.schemas import Dataset, AccessMode, Visualization

logger = logging.getLogger(__package__)


class SAMDao(DaoBase):
    async def get_baselines_async(
        self,
        site_id: str,
        project_id: str,
        search_term: Optional[str] = None,
        access_mode=AccessMode.INTERNAL.value,
    ) -> Tuple[List[Dataset], int]:
        """
        Retrieve all baseline datasets based on the provided site and project identifiers,
        with an optional search term. Pagination is not applied, so all matching documents
        are returned.

        Args:
            site_id (str): The identifier for the site.
            project_id (str): The identifier for the project.
            search_term (Optional[str], optional): A term to search within dataset names and descriptions. Defaults to None.
            access_mode (str, optional): The access mode for the datasets. Defaults to AccessMode.INTERNAL.value.

        Returns:
            Tuple[List[Dataset], int]: A tuple containing a list of Dataset objects and the total count of matching datasets.
        """
        # Base query conditions
        query = {
            "access_mode": access_mode,
            "dataset_type": "TABULAR",
            "$and": [
                {
                    "$or": [
                        {"tags": "admin_upload"},
                        {
                            "tags": {"$all": ["sam", "scrap_analysis"]},
                            "project_id": project_id,
                            "site_id": site_id,
                        },
                    ]
                },
            ],
        }

        # Handle search term
        if search_term:
            search_query = {
                "$regex": search_term,
                "$options": "i",
            }
            query["$and"].append(
                {"$or": [{"name": search_query}, {"description": search_query}]}
            )

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

        # Execute query
        datasets_cursor = self.db_async.datasets.aggregate(pipeline)
        datasets = await datasets_cursor.to_list(length=None)
        total_count = len(datasets)

        # Process results
        datasets_list = []
        for dataset in datasets:
            dataset["_id"] = str(dataset["_id"])
            datasets_list.append(Dataset(**dataset))

        return datasets_list, total_count

    async def get_scenario_by_usecase_id(self, project_id: str, usecase_id: str):
        return await self.db_async.scrap_analysis.find_one(
            {"project_id": project_id, "_id": ObjectId(usecase_id)}
        )

    async def get_scenario_by_usecase_name(self, project_id: str, usecase_name: str):
        return await self.db_async.scrap_analysis.find_one(
            {"project_id": project_id, "usecase_name": usecase_name}
        )

    async def update_scenario(
        self, project_id: str, usecase_id: str, scenarios_data: dict
    ):
        return await self.db_async.scrap_analysis.update_one(
            {"project_id": project_id, "_id": ObjectId(usecase_id)},
            {"$set": scenarios_data},
        )

    async def create_new_scenario(self, project_id: str, scenarios_data: dict):
        scenarios_data["project_id"] = project_id
        result = await self.db_async.scrap_analysis.insert_one(scenarios_data)
        return str(result.inserted_id)

    async def get_scenarios_by_project_id(self, project_id: str) -> List:
        data = await self.db_async.scrap_analysis.find(
            {"project_id": project_id}
        ).to_list(None)
        if data:
            usecases = []
            for d in data:
                d["_id"] = str(d["_id"])
                usecases.append(SAMUseCase(**d))
            return usecases
        return []

    async def custom_update_dataset(
        self, dataset_id: str, new_tags: List[str], new_path: str, name: str
    ):
        """
        Updates a MongoDB document with the specified keys: dataset_information, tags, and path in dataset_location.

        Args:
            dataset_id: The unique identifier of the document to update.
            new_tags: The new list of tags to associate with the document.
            new_path: The new value for the 'path' key in the 'dataset_location' array.
            name: The new name for the document.

        Returns:
            None
        """
        try:
            # Define the update payload
            update_payload = {
                "$set": {
                    "dataset_information": [],
                    "tags": new_tags,
                    "dataset_location.0.path": new_path,  # Updates the path of the first item in the dataset_location array
                    "name": name,
                    "description": name,
                }
            }

            # Perform the update operation
            result = await self.db_async.datasets.update_one(
                {"_id": ObjectId(dataset_id)}, update_payload
            )

            if result.matched_count > 0:
                if result.modified_count > 0:
                    logger.info(
                        f"Document with ID {dataset_id} was successfully updated."
                    )
                else:
                    logger.info(
                        f"Document with ID {dataset_id} was found but no changes were made."
                    )
            else:
                logger.info(f"No document found with ID {dataset_id}.")

        except Exception as e:
            logger.error(
                f"An error occurred while updating the document: {e}", exc_info=True
            )

    async def delete_document(
        self, query: dict, col_name: str = "datasets"
    ) -> Optional[dict]:
        """
        Deletes a document from the MongoDB collection and returns the deleted document.

        Args:
            query (dict): The query to identify the document to delete.
            col_name (str, optional): The name of the collection to delete the document from. Defaults to "datasets".

        Returns:
            dict | None: The deleted document if found, otherwise None.
        """
        deleted_doc = await self.db_async[col_name].find_one_and_delete(query)
        return deleted_doc
