from bson import ObjectId
from datetime import datetime, timezone
from typing import List, Optional, Union, Tuple, Any
import json
from app.core.dao.dao_base import *
from app.services.admin.connectors.schemas import *
from .schemas import Datasheets
import pymongo
from pymongo import ReturnDocument

class DatasheetGeneratorDao(DaoBase):
    
    def insert_datasheet_record(self, datasheet: Datasheets) -> str:
        """
        For inserting a record in mongo collection
        """
        result = self.db_sync.datasheets.insert_one(datasheet.model_dump())
        if not result:
            raise Exception("not able to create datasheet record")

        dataset_id = str(result.inserted_id)
        return dataset_id

    async def insert_datasheet_record_async(self, datasheet: Datasheets) -> str:
        """
        For inserting a record in mongo collection
        """
        result = await self.db_async.datasheets.insert_one(datasheet.model_dump())
        if not result:
            raise Exception("not able to create datasheet record")

        datasheet_id = str(result.inserted_id)
        return {"datasheet_id": str(datasheet_id),"datasheet": datasheet.datasheet, "datasheet_path":datasheet.datasheet_path,"nomianl_ages": datasheet.tensile_ages}
    
    async def upsert_datasheet_record_async(self, datasheet: Datasheets) -> dict:
        """
        Insert or update a record in the mongo collection based on `project_id` and `datasheet`.
        - Updates all provided keys in the incoming object.
        - Appends new values to existing arrays instead of replacing them.
        """
        filter_query = {"project_id": datasheet.project_id, "datasheet": datasheet.datasheet}
        update_data = {"$set": {}, "$addToSet": {}}

        # Convert incoming object to dictionary and update fields dynamically
        datasheet_dict = datasheet.model_dump()
        for key, value in datasheet_dict.items():
            if value is not None:
                if isinstance(value, list):  # Append to arrays
                    update_data["$addToSet"].setdefault(key, {"$each": list(set(value))})
                else:  # Update scalar values
                    update_data["$set"][key] = value
        
        # Remove empty $set and $addToSet if they have no values
        update_data = {key: value for key, value in update_data.items() if value}

        result = await self.db_async.datasheets.update_one(filter_query, update_data, upsert=True)
        
        if result.upserted_id:
            datasheet_id = str(result.upserted_id)  # Newly inserted record
        else:
            existing_doc = await self.db_async.datasheets.find_one(filter_query, {"_id": 1})
            if existing_doc:
                datasheet_id = str(existing_doc["_id"])  # Existing record updated
            else:
                raise Exception("Failed to retrieve the updated record ID")
        
        return {"datasheet_id": datasheet_id, **datasheet_dict}

    async def update_datasheet_record_async(self, datasheet_id: str, update_data: dict) -> dict:
        """
        Updates a datasheet record in the MongoDB collection by its datasheet_id.
        """
        # Convert datasheet_id to ObjectId if it's in string format
        datasheet_object_id = ObjectId(datasheet_id)
        
        # Perform the update
        result = await self.db_async.datasheets.find_one_and_update(
            {"_id": datasheet_object_id},  # Search criteria
            {"$set": update_data},  # Set updated fields
            return_document=ReturnDocument.AFTER  # Return the updated document
        )
        result['_id'] = str(result['_id'])
        # datasheet['_id'] = str(result['_id'])  # Convert ObjectId to string
        result['id'] = result.pop('_id')
        if not result:
            raise Exception("Failed to update datasheet record")
        
        # Return the updated datasheet object
        return result
    
    async def get_datasheets_by_project_id(self, project_id: str) -> List[Dict]:
        """
        Fetches datasheets based on project_id from the database.

        :param project_id: The ID of the project to filter datasheets.
        :return: A list of datasheets as dictionaries.
        """
        try:
            # Query the datasheets collection by project_id
            datasheets_cursor = self.db_async.datasheets.find({"project_id": project_id})

            # Convert the cursor to a list
            datasheets = await datasheets_cursor.to_list(length=None)

            # Convert ObjectId to string for each datasheet
            for datasheet in datasheets:
                datasheet['_id'] = str(datasheet['_id'])  # Convert ObjectId to string
                datasheet['id'] = datasheet.pop('_id')  
            return datasheets

        except Exception as e:
            # Raise exception to the caller with a descriptive error
            raise RuntimeError(f"Failed to fetch datasheets: {str(e)}")
        
    async def get_datasheet_for_converter(self, project_id: str, datasheet:str) -> List[Dict]:
        """
        Fetches datasheets based on project_id from the database.

        :param project_id: The ID of the project to filter datasheets.
        :return: A list of datasheets as dictionaries.
        """
        try:
            # Query the datasheets collection by project_id
            datasheet = await self.db_async.datasheets.find_one({"project_id": project_id,"datasheet": str(datasheet)})
            if not datasheet:
                return None
            datasheet['_id'] = str(datasheet['_id']) 
            datasheet['id'] = datasheet.pop('_id')  
            return datasheet

        except Exception as e:
            # Raise exception to the caller with a descriptive error
            raise RuntimeError(f"Failed to fetch datasheets: {str(e)}")
        
 
    async def upsert_datasheet_params(
            self, 
            projectId: str, 
            datasheetId: int, 
            nominalAge: int, 
            selectedDataSheetId: str, 
            save_payload: dict
        ) -> str:
        """
        Upsert a document in the datasheet_params collection.

        If a matching document exists (based on projectId, datasheet, datasheet_id, and nominal_age), update it.
        If no matching document exists, insert a new one.
        """
        try:
            collection = self.db_async.datasheet_params
            
            query = {
                "project_id": projectId,
                "datasheet": datasheetId,
                "nominal_age": nominalAge,
                "datasheet_id": selectedDataSheetId
            }

            result = await collection.find_one_and_update(
                query,                         # Search criteria
                {"$set": save_payload},        # Fields to update
                upsert=True,                   # Insert if not found
                return_document=ReturnDocument.AFTER  # Return updated/inserted document
            )

            if result and "_id" in result:
                return str(result["_id"])
            else:
                raise Exception("Upsert failed; no document ID returned.")

        except Exception as e:
            raise Exception(f"Error during upsert operation: {str(e)}")

    async def delete_datasheet(self, project_id: str, datasheet_name: str) -> bool:
        result = await  self.db_async.datasheets.delete_one({"project_id": project_id, "datasheet": datasheet_name})
        return result.deleted_count > 0
    
    async def delete_datasheet_params(self, filter: dict) -> bool:
        result = await  self.db_async.datasheet_params.delete_one(filter)
        return result.deleted_count > 0

    async def delete_datasheet_params_many(self, filter: dict) -> bool:
        result = await  self.db_async.datasheet_params.delete_many(filter)
        return result.deleted_count > 0
    
    async def get_datasheet_params(self, project_id: str, datasheet_name: str) -> bool:
        try:
            pipeline = [
                {
                    "$match": {
                        "project_id": project_id,  # Replace with your projectId
                        "datasheet": int(datasheet_name)  # Replace with your datasheetId
                    }
                },
                {
                    "$group": {
                        "_id": "$datasheet", 
                        "nominalAges": {"$push": "$nominal_age"}
                    }
                }
            ]
            collection = self.db_async.datasheet_params
            cursor = collection.aggregate(pipeline)
            result = await cursor.to_list(length=None)  # Convert cursor to a list
            if result:
                # Build the desired result object
                result_object = {
                    "datasheet": str(result[0]['_id']),  # Datasheet ID from grouping
                    "nominal_age": result[0]['nominalAges'],
                    "processed":True
                }
            else: 
                result_object = {
                    "datasheet": datasheet_name,  # Datasheet ID from grouping
                    "nominal_age": [],
                    "processed":False
                }
            return result_object
            
            return None
            
        except Exception as e:
            # Raise exception to the caller with a descriptive error
            raise RuntimeError(f"Failed to fetch datasheets: {str(e)}")
