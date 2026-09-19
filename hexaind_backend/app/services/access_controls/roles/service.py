import logging
from datetime import datetime, timezone
from typing import List, Tuple

from app.services.access_controls.roles.dao import RolesFeaturesMapDao
from app.services.access_controls.roles.schemas import (
    AppNames,
    RolesFeaturesMap,
    RolesFeaturesMapCreateRequest,
    RolesFeaturesMapUpdateRequest, SystemGeneratedProjectRoles, RoleType, RoleCreationType
)
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from app.services.access_controls.roles.utils import get_system_generated_role_features_map
from app.config.env_vars import environment

logger = logging.getLogger(__package__)


class RolesFeaturesMapService:
    def __init__(
            self,
            db_sync_client: MongoClient = None,
            db_async_client: AsyncIOMotorClient = None,
    ) -> None:
        self.roles_features_map_dao = RolesFeaturesMapDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )
        logger.info("Initialized Roles Features Map Dao")

    async def insert_roles_features_map(
            self,
            user_id: str,
            roles_features_map_data: RolesFeaturesMapCreateRequest,
    ) -> str:
        map_data = RolesFeaturesMap(
            version=roles_features_map_data.version,
            name=roles_features_map_data.name,
            description=roles_features_map_data.description,
            role_type=roles_features_map_data.role_type,
            features=roles_features_map_data.features,
            created_at=datetime.now(timezone.utc),
            created_by=user_id,
            is_active=True,
            last_modified_at=datetime.now(timezone.utc),
            last_modified_by=user_id,
            source_type=roles_features_map_data.source_type
        )
        logger.info("Inserting a new roles and features map")
        return await self.roles_features_map_dao.insert_roles_features(roles_features=map_data)

    async def update_roles_features_map(
            self, role_feature_map_id: str, roles_features_map_update_request: RolesFeaturesMapUpdateRequest
    ) -> str:
        logger.info("Updating roles and features map")
        raise NotImplementedError("Update is currently not supported.")

    async def fetch_all_roles_features_maps(
            self, search_term: str = "", page_number: int = 1, page_limit: int = 100
    ) -> Tuple[List[RolesFeaturesMap], int]:
        logger.info("Fetching all roles and features maps")
        return await self.roles_features_map_dao.get_all_roles_features_async(
            search_term=search_term,
            page_number=page_number,
            page_limit=page_limit,
        )

    async def get_roles_features_map_by_id(
            self, roles_features_map_id: str
    ) -> RolesFeaturesMap:
        logger.info(
            f"Fetching roles and features map by ID: {roles_features_map_id}")
        return await self.roles_features_map_dao.get_role_feature_map_id_async(roles_features_map_id)

    async def get_roles_features_map_by_name(
            self, roles_name: str
    ) -> RolesFeaturesMap:
        logger.info(
            f"Fetching roles and features map by name: {roles_name}")
        return await self.roles_features_map_dao.get_role_by_name_async(role_name=roles_name)

    async def generate_or_update_system_generated_project_roles(self):
        for role in [SystemGeneratedProjectRoles.PROJECT_ADMINISTRATOR, SystemGeneratedProjectRoles.FULL_ACCESS,
                     SystemGeneratedProjectRoles.LIMITED_ACCESS]:
            role_features = get_system_generated_role_features_map(role)
            try:
                results = await self.roles_features_map_dao.insert_or_update_roles_features_with_id(role_features)
                logger.info(f"Updating system generated roles for {role}: {results}")
            except Exception as e:
                logger.exception(f"Unknown exception during update/add. {e}")

    async def create_user_and_roles(self):
        import traceback
        server_role_email = environment.server_admin_email_to_create_if_no_server_admin
        server_admin_pwd = environment.server_admin_password
        
        roles_creation_error = ''
        try:
            await self.roles_features_map_dao.insert_or_update_server_roles()
        except Exception as e:
            traceback.print_exc()
            error_str = 'Failed to create/ update Server Roles collection roles'
            logger.exception(error_str)
            roles_creation_error = error_str

        server_admin_create_error = ''
        if not server_role_email or not server_admin_pwd or len(server_role_email.strip()) == 0 or len(server_admin_pwd.strip()) == 0:
            server_admin_create_error = 'Did not get any env vars "SERVER_ADMIN_EMAIL_TO_CREATE_IF_NO_SERVER_ADMIN", "SERVER_ADMIN_PASSWORD"  to create a server admin user'
        else:
            try:
                await self.roles_features_map_dao.create_server_admin_user()
            except Exception as e:
                traceback.print_exc()
                error_str = f"Failed to create/ update Server Admin user with email {server_role_email.strip()}. Exception:{e}"
                server_admin_create_error = error_str
                logger.exception(error_str)

        if len(roles_creation_error) or len(server_admin_create_error) > 0:
            raise Exception(f"{roles_creation_error}\n{server_admin_create_error}")

    async def generate_app_permisssions_table(self) -> int:
        return await self.roles_features_map_dao.generate_app_permisssions_table()
