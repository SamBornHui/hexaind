import logging

from app.services.access_controls.features.dao import \
    EndPointsFeatureMappingsDao
from app.services.access_controls.features.schemas import (
    EndPointsFeatureMappings,
    HTTPEndPointMethodType
)
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

logger = logging.getLogger(__package__)


class EndPointsFeatureMappingsService:
    def __init__(self, db_async_client: AsyncIOMotorClient = None, db_sync_client: MongoClient = None) -> None:
        self.endpoints_feature_mappings_dao = EndPointsFeatureMappingsDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )

    async def create_or_replace_mapping(self, payload: EndPointsFeatureMappings) -> str:
        mapping_id = await self.endpoints_feature_mappings_dao.insert_mapping(payload)
        # logger.info(f"added to db {payload}")
        return mapping_id

    async def get_mapping(self, end_point: str, method: HTTPEndPointMethodType) -> EndPointsFeatureMappings:
        try:
            mapping = await self.endpoints_feature_mappings_dao.get_mapping_by_endpoint_and_method(end_point, method)
            return mapping
        except Exception as e:
            raise e

    def get_token_excluded_endpoint_method_list(self):
        return self.endpoints_feature_mappings_dao.get_token_excluded_endpoint_method_list()

    def get_all_endpoint_method_details(self):
        return self.endpoints_feature_mappings_dao.get_all_endpoint_method_details()
