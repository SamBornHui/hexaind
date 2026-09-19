from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from random import randint

import logging

from app.services.data.assets.datasets.dao import DatasetsDao
from app.services.data.assets.datasets.schemas import DatasetMetadata, DatasetSourceFormats
from app.services.data.assets.datasets.service import DatasetsService
from app.services.data.datasets_conversion.helper import DatasetsConversionFactory
from app.services.data.datasets_conversion.schemas import DatasetsConversionRequest

logger = logging.getLogger(__package__)


class DatasetsConversionsService:

    def __init__(self, db_sync_client: MongoClient = None, db_async_client: AsyncIOMotorClient = None) -> None:
        self.datasets_dao = DatasetsDao(db_sync_client=db_sync_client, db_async_client=db_async_client)
        self.datasets_service = DatasetsService(db_sync_client=db_sync_client, db_async_client=db_async_client)

    async def convert_dataset(self, datasets_conversion_request: DatasetsConversionRequest, user_id):
        converter = DatasetsConversionFactory().get_factory(datasets_conversion_request.conversion_type)
        dataset_id = datasets_conversion_request.from_config.dataset_id

        actual_dataset = await self.datasets_dao.get_dataset_by_id_async(dataset_id)
        conversion_kwargs = {
            "last_modified_by": user_id,
            "name":f"{actual_dataset.name}_CSV_{randint(2, 10000)}"
        }
        converted_dataset = converter.convert(actual_dataset,conversion_kwargs)
        converted_dataset.metadata = DatasetMetadata(
            data_source=DatasetSourceFormats.GENERATED_FROM_EXISTING_DATASET_FORMAT.format(
                datasets_conversion_request.conversion_type.value.lower()))


        # results = await self.datasets_dao.insert_dataset_record_async(converted_dataset)
        results = await self.datasets_service.save_tabular_dataset_helper_async(
            input_data=converted_dataset.dataset_location[0].path,
            project_id=converted_dataset.project_id,
            user_id=converted_dataset.user_id,
            site_id=converted_dataset.site_id,
            created_by=converted_dataset.created_by,
            name=converted_dataset.name,
            description=converted_dataset.description,
            access_mode=converted_dataset.access_mode,
            metadata=converted_dataset.metadata,
            # dataset_information=converted_dataset.dataset_information
        )
        logger.info(f"Inserting new converted dataset record {results}")
        if not datasets_conversion_request.retain_existing_data:
            raise NotImplementedError(
                f"retain_existing_data == {datasets_conversion_request.retain_existing_data} is not supported now")
