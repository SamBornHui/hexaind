from pymongo import MongoClient
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List
import itertools
from .dao import ActionResultsDao
from .schemas import *
from app.services.workflows.actions.dao import ActionsDao
from app.services.data.assets.datasets.schemas import *
from app.services.data.assets.datasets.service import *
import logging

logger =logging.getLogger(__package__)

class ActionResultsService:
    def __init__(self, db_sync_client: MongoClient = None, db_async_client: AsyncIOMotorClient = None) -> None:
        
        self.action_results_dao = ActionResultsDao(db_sync_client=db_sync_client, db_async_client=db_async_client)

        self.actions_dao = ActionsDao(db_sync_client=db_sync_client, db_async_client=db_async_client)

        self.dataset_service = DatasetsService(db_sync_client=db_sync_client,db_async_client=db_async_client)
    
    async def get_action_result_by_id_async(self, result_id: str) -> ActionResult:
        
        return await self.action_results_dao.get_action_result_by_id_async(result_id=result_id) 
    
    async def delete_action_result_by_id_async(self, result_id: str, force_delete: bool = False) -> bool:
        logger.info("inside delete_action_result_by_id_async function")
        try:
            result_record: ActionResult = await self.get_action_result_by_id_async(result_id=result_id)
        except Exception as e:
            return

        if result_record.type == ActionResultType.DATASET:
            
            dataset_id = result_record.result.dataset_id
            
            await self.dataset_service.delete_dataset_by_id_async(dataset_id=dataset_id, force_delete=force_delete)


        elif result_record.type == ActionResultType.MODEL:

            machine_learning_model_record_id = result_record.result.dataset_id

            await self.dataset_service.delete_machine_learning_model_by_id_async(machine_learning_model_record_id=machine_learning_model_record_id)

        elif result_record.type in [ActionResultType.FAILURE, ActionResultType.STRING]:
            pass

        else:
            logger.error(f"delete_action_result_by_id_async got unknown result record type: {result_record.type}")
            Exception(f"delete_action_result_by_id_async got unknown result record type: {result_record.type}")
            
        return await self.action_results_dao.delete_action_result_by_id_async(result_id=result_id) 
