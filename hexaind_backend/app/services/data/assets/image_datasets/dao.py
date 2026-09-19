from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import json
from datetime import datetime, timezone
import pymongo
from typing import List, Optional, Union, Tuple
from app.core.dao.dao_base import *
from app.services.data.assets.datasets.schemas import Dataset, DatasetType, AccessMode, DatasetDeleteType
from app.services.data.assets.image_datasets.schemas import (FileUploadDetails)

class ImageDatasetsDao(DaoBase):
    
    async def get_dataset_with_path_async(self, base_path) -> Dataset:
        dataset = await self.get_dataset_with_simple_qry_async({"dataset_location.0.path":base_path})
        if not dataset:
            raise KeyError(f"Unable to find dataset with dataset path {base_path}")
        return dataset
    
    async def is_image_dataset_exists_with_path_async(self, base_path) -> bool:
        doc_cnt = await self.db_async.datasets.count_documents({"dataset_location.0.path":base_path, "dataset_type": DatasetType.IMAGE_DATASET})
        return doc_cnt > 0
    
    async def get_dataset_with_simple_qry_async(self, simple_query) -> Union[None, Dataset]:
        dataset = await self.db_async.datasets.find_one(simple_query)
        if not dataset:
            return dataset
        dataset["_id"] = str(dataset["_id"])
        return Dataset(**dataset)

    async def is_dataset_exists_with_path(self, base_path) -> bool:
        doc_cnt = await self.db_async.datasets.count_documents({"dataset_location.0.path":base_path})
        return doc_cnt > 0
    
    async def insert_image_records(self, dataset_id: str, uploaded_file_det_list: List[FileUploadDetails]):
        file_det_dict_list = []
        for file_det in uploaded_file_det_list:
            file_det_dict = file_det.dict()
            file_det_dict['dataset_id'] = dataset_id
            file_det_dict_list.append(file_det_dict)

        await self.db_async.image_datasets_files.insert_many(file_det_dict_list)
        

    async def update_images_file_info(self, dataset_id: str, uploaded_file_det_list: List[FileUploadDetails], user_name: str):
        for file_det in uploaded_file_det_list:
            await self.db_async.image_datasets_files.update_one({'uid': file_det.uid}, {'$set':{'file_path': file_det.file_path}})
        
        await self.update_image_dataset_updation(dataset_id, user_name)
    
    async def delete_images_file_info(self, dataset_id: str, uploaded_file_det_list: List[FileUploadDetails], user_name: str, folder_size:str = None):
        for file_det in uploaded_file_det_list:
            await self.db_async.image_datasets_files.delete_one({'uid': file_det.uid})
        
        await self.update_image_dataset_updation(dataset_id, user_name, folder_size)
    
    async def update_image_dataset_updation(self, dataset_id, user_name: str, folder_size:str = None):
        last_modified_at = datetime.now(timezone.utc)
        dict_to_update =  {"dataset_location.0.last_modified_by": user_name, 
                        "dataset_location.0.last_modified_at": last_modified_at}
        if folder_size != None:
            dict_to_update["dataset_location.0.size"] = folder_size

        await self.db_async.datasets.update_one({"_id": ObjectId(dataset_id)}, {"$set": dict_to_update})

    
    async def delete_image_dataset(self, dataset_id: ObjectId):
        await self.db_async.image_datasets_files.delete_many({"dataset_id": str(dataset_id)})
        result = await self.db_async.datasets.delete_one({"_id": dataset_id})
        return result

    async def get_image_datasets(self, project_id: str):
        result = await self.db_async.datasets.find({"dataset_type": "IMAGE_DATASET", "project_id": project_id}).to_list(length=None)
        return result
    
    async def sampleworkflows(self, dataset_id: str):
        return await self.db_async.sampleworkflows.find_one({"dataset_id": str(dataset_id)}) is not None
    
    async def update_dataset(self, dataset_id, file_path):
        return await self.db_async.datasets.update_one(
            {"_id": dataset_id},
            {"$set": {"defect_metadata": file_path}},
        ) is not None
