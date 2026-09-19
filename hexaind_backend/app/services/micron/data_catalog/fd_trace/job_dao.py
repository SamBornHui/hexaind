from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from pymongo import MongoClient
from pymongo.collection import Collection
from bson import ObjectId

from app.config.env_vars import environment

from .schemas import *

from datetime import timezone


class FdTraceJobDao:

    def __init__(self,
                 db_sync_client: MongoClient=None, 
                 db_async_client: AsyncIOMotorClient=None):
        
        self.db_sync_client = db_sync_client
        self.db_async_client = db_async_client
        self.DC_TL_cache = "DC_TL_cache"

    __collection_name: str = "fd_trace_jobs"

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
    
    async def create_fd_stage_job(self, fd_data_pull_job: FdDataPullJobConfig) -> str:

        result = await self.async_collection.insert_one(fd_data_pull_job.model_dump(mode="json", exclude=["id"], by_alias=True))
        return str(result.inserted_id)
    
    async def create_fd_data_pull_job_record_async(self, job_record: FdDataPullConfig) -> str:

        result = await self.async_collection.insert_one(job_record.model_dump(mode="json", exclude=["id"], by_alias=True))
        return str(result.inserted_id)
    
    async def get_fd_data_pull_job_record_async(self, job_id:str) -> FdDataPullConfig:
        
        record = await self.async_collection.find_one({"_id":ObjectId(job_id)})
        record["_id"] = str(record["_id"])
        return FdDataPullConfig(**record)
    
    def get_fd_data_pull_job_record_sync(self, job_id:str) -> FdDataPullConfig:
        
        record = self.sync_collection.find_one({"_id":ObjectId(job_id)})
        record["_id"] = str(record["_id"])
        return FdDataPullConfig(**record)
    
    async def get_multiple_fd_data_pull_job_config_records_async(self, job_config_ids: List[str]) -> List[FdTracePullFullStatusResponse]:

        documents, results = [], []

        object_ids = [ObjectId(id) for id in job_config_ids]

        fields_to_retrieve = {'stage': 1,
                              'stage_config.status.status': 1,
                              'stage_config.inputs': 1
                              }

        documents_cursor = self.async_collection.find({'_id': {'$in': object_ids}}, fields_to_retrieve)
        async for document in documents_cursor:
            documents.append(document)

        for document in documents:
            extracted_data = {
                'stage': document.get('stage'),
                'status': document.get('stage_config', {}).get('status', {}).get('status'),
                'inputs': document.get('stage_config', {}).get('inputs')
            }
            results.append(FdTracePullFullStatusResponse(**extracted_data))

        return results
    
    async def get_fd_data_pull_job_config_record_async(self, job_config_id: str) -> FdDataPullJobConfig:

        record = await self.async_collection.find_one({"_id":ObjectId(job_config_id)})
        record["_id"] = str(record["_id"])
        return FdDataPullJobConfig(**record)
    
    def get_fd_data_pull_job_config_record_sync(self, job_config_id: str) -> FdDataPullJobConfig:

        record = self.sync_collection.find_one({"_id":ObjectId(job_config_id)})
        record["_id"] = str(record["_id"])
        return FdDataPullJobConfig(**record)
    
    async def update_fd_data_pull_job_record_current_stage_async(self, job_id: str, current_stage:FDDataPullStages, current_stage_status:DataCatalogStatus) -> bool:

        result = await self.async_collection.update_one({'_id': ObjectId(job_id)}, 
                                               {'$set': {'current_stage': current_stage,
                                                         'data_pull_status': current_stage_status
                                                         }
                                                })  
        return True #result.modified_count > 0  #TODO Modify the return statement  


    def update_fd_data_pull_job_record_current_stage_sync(self, job_id: str, current_stage:FDDataPullStages, current_stage_status:DataCatalogStatus) -> bool:
        
        result = self.sync_collection.update_one({'_id': ObjectId(job_id)}, 
                                                  {'$set': {'current_stage': current_stage,
                                                            'data_pull_status': current_stage_status
                                                            }
                                                   })  
        return True #result.modified_count > 0  #TODO Modify the return statement                                                  

    async def update_fd_data_pull_job_config_record_async(self, job_config_id:str, job_config_record: FdDataPullJobConfig) -> bool:

        updated_document = job_config_record.model_dump(mode="json", by_alias=True)
        updated_document.pop("_id")
        result = await self.async_collection.update_one({'_id': ObjectId(job_config_id)},
                                                        {'$set': updated_document})
        return result.modified_count > 0
    
    def update_fd_data_stage_job_record_current_status_sync(self, job_id: str, new_status: DataPullStatus) -> bool:

        result = self.sync_collection.update_one({'_id': ObjectId(job_id)}, 
                                                  {'$set': {'stage_config.status.status': new_status}}
                                                )  
        return True #result.modified_count > 0  #TODO Modify the return statement
    
    async def update_fd_data_stage_job_record_current_status_and_inputs_async(
        self, job_id: str, new_status: DataPullStatus, inputs: dict
    ) -> bool:
        result = await self.async_collection.update_one(
            {"_id": ObjectId(job_id)},
            {
                "$set": {
                    "stage_config.status.status": new_status,
                    "stage_config.inputs": inputs,
                }
            },
        )
        return True  # result.modified_count > 0  #TODO Modify the return statement
    
    def update_fd_data_stage_job_record_bigquery_status_sync(self, job_id: str, new_status: BigQueryDataPullJobStatus) -> bool:

        result = self.sync_collection.update_one({'_id': ObjectId(job_id)}, 
                                                  {'$set': {'stage_config.status.job_config.job_status': new_status.model_dump()}}
                                                )  
        return True #result.modified_count > 0  #TODO Modify the return statement
    
    def update_fd_data_stage_job_record_current_status_and_result_sync(self, job_id: str, new_status:DataPullStatus, result: dict) -> bool:

        result = self.sync_collection.update_one({'_id': ObjectId(job_id)}, 
                                                  {'$set': {'stage_config.status.status': new_status, 'stage_config.outputs':result}}
                                                )  
        return True #result.modified_count > 0  #TODO Modify the return statement

    async def update_fd_data_pull_job_record_async(self, fd_data_pull_job_id: str, session_id: str) -> str:

        result = await self.async_collection.update_one({"_id":ObjectId(fd_data_pull_job_id)},
                                                        {"$set": {"session_id": session_id}}
                                                        )
        return result.modified_count > 0
    
    def update_top_level_cache_sync(self, cache_key: str, value: str):

        collection = self.db_sync_client[environment.hexaind3_database_name][self.DC_TL_cache]

        filter_query = {"cache_key": cache_key}

        update_data = {
            "$set": {
                "value": value,
                "createdAt": datetime.now(timezone.utc) # Updates createdAt on every upsert
            }
        }

        result = collection.update_one(filter_query, update_data, upsert=True)
    
        if result.matched_count > 0:
            print(f"Updated record with cache_key: {cache_key} and updated createdAt timestamp")
        else:
            print(f"Inserted new record with cache_key: {cache_key} and createdAt timestamp")
        
        return True
    
    def fetch_top_level_cache_with_ttl_sync(self, cache_key: str, ttl_days: int):

        collection = self.db_sync_client[environment.hexaind3_database_name][self.DC_TL_cache]

        record = collection.find_one({"cache_key": cache_key})

        if record is None:
            # Record not found
            return None
        
        # created_at = record.get("createdAt")
        # if created_at is None:
        #     # No createdAt field present
        #     return None
        
        # if created_at.tzinfo is None:
        #     created_at = created_at.replace(tzinfo=timezone.utc)
        
        # expiration_time = created_at + timedelta(days=ttl_days)

        # if expiration_time > datetime.now(timezone.utc):
        #     return record
        # else:
        #     # Record is expired
        #     return None

        return record


