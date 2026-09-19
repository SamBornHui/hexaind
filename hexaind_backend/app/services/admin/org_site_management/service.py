import logging
from typing import List

from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import parse_obj_as
from pymongo import MongoClient

from app.core.services.jwt_token_utils.jwt_token_utils import decodeJWT
from app.services.admin.authentication.utils import http_err_unauthorized
from app.services.admin.org_site_management.dao import OrgSiteManagementDao
from app.services.admin.org_site_management.schemas import Site, Role

logger = logging.getLogger(__package__)

class OrgSiteManagementService:

    def __init__(self, db_sync_client: MongoClient = None, db_async_client: AsyncIOMotorClient = None) -> None:
        self.org_site_mngt_dao = OrgSiteManagementDao(db_sync_client=db_sync_client, db_async_client=db_async_client)
        logger.info("initiated org site management service.")

    async def create_site(self, site: Site, token) -> Site:
        logger.info("created site")
        token = decodeJWT(token)
        if int(token['server_role_value']) & 3 == 0:
            return http_err_unauthorized("Don't have permission to create new Site")
        site_created = await self.org_site_mngt_dao.create_site(site)
        logger.info("created site.")
        return Site(**site_created)

    async def get_roles_list(self) -> List[Role]:
        logger.info("get roles list")
        roles_list_dict = await self.org_site_mngt_dao.get_roles_list()
        logger.info("returning the roles list")
        return parse_obj_as(List[Role], roles_list_dict)

    async def get_sites_list(self, token) -> List[Site]:
        logger.info("inside get sites list")
        token = decodeJWT(token)
        if int(token['server_role_value']) & 3 > 0:
            sites_list_dict = await self.org_site_mngt_dao.get_sites_list()
        else:
            sites_list_dict = await self.org_site_mngt_dao.get_user_sites_list(token['email'])

        return parse_obj_as(List[Site], sites_list_dict)
