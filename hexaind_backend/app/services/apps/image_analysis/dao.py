from bson import ObjectId
from datetime import datetime, timezone
from typing import List, Optional, Union, Tuple, Any
import json
from app.core.dao.dao_base import *
from app.services.admin.connectors.schemas import *
from app.services.data.folder_management.dao import FolderManagementDao
import pymongo

class ImageAnalysisDao(FolderManagementDao):
    
    async def insert_annotation(self, annotation: dict) -> str:
        result = await self.db_async.ImageAnnotations.insert_one(annotation)
        if not result.inserted_id:
            raise Exception("not able to save annotation record")

        return str(result.inserted_id)
    
    async def find_annotations_by_dataset_id(self, dataset_id: str) -> List[Dict[str, Any]]:
        cursor = self.db_async.ImageAnnotations.find({"dataset_id": dataset_id})
        annotations = await cursor.to_list(length=None)
        for annotation in annotations:
            annotation['_id'] = str(annotation['_id'])

        return annotations


    async def find_cat_data_by_dataset_id(self, dataset_id: str):
        dataset_cursor =  self.db_async.categorizeddata.find({'dataset_id':dataset_id},{'_id' :1 , 'folderId' : 1 , 'dataset_id' : 1})
        dataset = await dataset_cursor.to_list(length=None) 
        return dataset
    
    async def find_DM_dataset_by_id(self, dataset_id: str):
        dataset = await self.db_async.DMCreatedDatasets.find_one({"_id": ObjectId(dataset_id)})
        dataset['_id'] = str(dataset['_id'])
        return dataset
    
    async def find_and_delete_annotation_by_id(self, annotation_id: str) -> Optional[Dict]:
        annotation = await self.db_async.ImageAnnotations.find_one({"_id": ObjectId(annotation_id)})
        if annotation:
            await self.db_async.ImageAnnotations.delete_one({"_id": ObjectId(annotation_id)})
            return annotation
        return None
    
    async def find_annotation_by_id(self, annotation_id: str):
        return await self.db_async.ImageAnnotations.find_one({"_id": ObjectId(annotation_id)})

    async def update_annotation_field(self, annotation_id: str, field: str, value: any):
        result = await self.db_async.ImageAnnotations.update_one({"_id": ObjectId(annotation_id)}, {"$set": {field: value}})
        return result

    async def update_annotation_fields(self, annotation_id: str, fields: dict):
        result = await self.db_async.ImageAnnotations.update_one({"_id": ObjectId(annotation_id)}, {"$set": fields})
        return result
    
    async def update_annotation_name(self, annotation_id: str, annotation_name: str):
        result = await self.db_async.ImageAnnotations.update_one(
            {"_id": ObjectId(annotation_id)},
            {"$set": {"annotation_name": annotation_name}}
        )
        return result

    async def update_annotation_label(self, annotation_id: str, label: str, color: str):
        result = await self.db_async.ImageAnnotations.update_one(
            {"_id": ObjectId(annotation_id)},
            {"$set": {"label": label, "color": color}}
        )
        return result

    async def update_coordinates(self, annotation_id: str, coordinates: Dict[str, float]):
        result = await self.db_async.ImageAnnotations.update_one(
            {"_id": ObjectId(annotation_id)},
            {"$set": {"coordinates": coordinates}}
        )
        return result
    
    def get_document_sort(self, filter_document: dict = None, collection: str = None):
        model_document = self.db_sync[collection].find_one(filter_document,sort= [('_id', pymongo.DESCENDING)])
        return model_document
    

    async def delete_segmented_annotation(self, delete_query, update_query): 
        result = await self.db_async.seg_image_annotations.update_one(delete_query, update_query)
        return result
        

    async def update_label(self, label_name: str):
        result = await self.db_async.seg_image_annotations.update_many(
            { 
                "annotation_data.Label": label_name
            },
            {
                "$set": {
                    "annotation_data.$[elem].Label": "blank"
                }
            },
            array_filters=[
                { "elem.Label": label_name }
            ]
        )


        return result

        