import datetime
import logging
from datetime import datetime, timezone
from typing import List, Tuple, Dict
from functools import cache

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from app.services.access_controls.roles.dao import RolesFeaturesMapDao
from app.services.access_controls.roles.schemas import SystemGeneratedProjectRoles, RolesFeaturesMap
from app.services.access_controls.user_projects.dao import UsersProjectsMappingsDao
from app.services.access_controls.user_projects.schemas import AppPermission, CreateMappingRequestMultiple, EditAppPermission, UsersProjectsMapping, \
    CreateMappingRequest, \
    UserProjectsMappingWithDetails
from app.services.admin.authentication.dao import AuthenticationDao
from app.services.admin.authentication.schemas import UserStatus, UserDetails, User, UserIdRoleValueMap, \
    ServerBasedRoleNames
from app.services.admin.projects.dao import ProjectDao

logger = logging.getLogger(__package__)


class UsersProjectsMappingsService:
    def __init__(self, db_async_client: AsyncIOMotorClient = None) -> None:
        self.users_projects_mappings_dao = UsersProjectsMappingsDao(
            db_async_client=db_async_client)
        self.projects_dao = ProjectDao(db_async_client=db_async_client)
        self.authentication_dao = AuthenticationDao(
            db_async_client=db_async_client)
        self.roles_features_dao = RolesFeaturesMapDao(
            db_async_client=db_async_client)

    @staticmethod
    def generate_user_project_mapping(user_id: str, project_id: str, role_id: str, last_modified_by: str = ''):
        return UsersProjectsMapping(
            user_id=user_id,
            project_id=project_id,
            role_id=role_id,
            is_active=True,
            last_modified_at=datetime.now(timezone.utc),
            last_modified_by=last_modified_by,
            created_at=datetime.now(timezone.utc),
            created_by=last_modified_by
        )

    async def create_new_mapping(self, user_id: str, mapped_user_id: str, project_id: str, role_id: str) -> str:

        logger.info(
            f"Creating new mapping between {mapped_user_id} , {project_id} , {role_id}")
        mapping = self.generate_user_project_mapping(
            mapped_user_id, project_id, role_id, user_id)
        return await self.users_projects_mappings_dao.insert_users_projects_mapping(mapping)

    async def create_new_mappings(self, request_user_id: str, mappings_object: CreateMappingRequestMultiple):

        for mapping in mappings_object.mappings:
            payload = await self.create_new_mapping(
                user_id=request_user_id, mapped_user_id=mapping.user_id, project_id=mapping.project_id,
                role_id=mapping.role_id)

    @staticmethod
    def _validate_user_mappings_for_project(user_mappings: List[CreateMappingRequest]):
        project_ids = list(
            set([user_mapping.project_id for user_mapping in user_mappings]))
        if len(project_ids) != 1:
            raise ValueError(
                f"Expected only one unique project id, received {project_ids}")
        total_keys = [user_mapping.project_id +
                      user_mapping.user_id for user_mapping in user_mappings]
        unique_keys = list(set(total_keys))
        total_keys_len = len(unique_keys)
        unique_keys_len = len(list(set(total_keys)))
        if total_keys_len != unique_keys_len:
            raise ValueError(
                f"repeated user mappings total: {total_keys_len} unique only {unique_keys_len}")

    async def update_existing_mappings_for_project(self, user_mappings: List[CreateMappingRequest], user_id: str):
        # TODO: this method might not be used in UI
        self._validate_user_mappings_for_project(user_mappings)

        project_id = user_mappings[0].project_id
        logger.info(f"updating user mappings for project {project_id}")
        # fetch existing maps
        existing_maps = await self.users_projects_mappings_dao.get_users_projects_mapping_by_project_id(project_id,False)
        existing_map_dict = {
            existing_map.user_id: existing_map
            for existing_map in existing_maps
        }
        logger.info(
            f"Fetched existing mappings for project {project_id} , {len(existing_maps)}")
        for item in user_mappings:
            mapping = existing_map_dict.get(item.user_id)
            if mapping:
                if mapping.role_id != item.role_id:
                    mapping.role_id = item.role_id
                    mapping.last_modified_at = datetime.now(timezone.utc)
                    mapping.last_modified_by = user_id
                    await self.users_projects_mappings_dao.update_users_projects_mapping(mapping)
                    logger.info(
                        f"Updated existing user project map successfully {mapping.project_id} , {mapping.user_id} , {mapping.role_id}")
                del existing_map_dict[item.user_id]  # delete from existing map
            else:
                mapping = self.generate_user_project_mapping(
                    item.user_id, item.project_id, item.role_id, user_id)
                await self.users_projects_mappings_dao.insert_users_projects_mapping(mapping)
                logger.info(
                    f"Created user project map successfully {mapping.project_id} , {mapping.user_id} , {mapping.role_id}")

        # delete existing users who are not in new user_mappings
        for key, value in existing_map_dict.items():
            deleted_count = await self.users_projects_mappings_dao.delete_users_projects_mappings(value.user_id,
                                                                                                  project_id)
            logger.info(
                f"Deleted old existing user project successfully {value.user_id} , {project_id} : {deleted_count}")

    async def update_existing_mapping(self, user_id: str, mapped_user_id: str, project_id: str, role_id: str) -> str:

        existing_mapping = await self.users_projects_mappings_dao.get_users_projects_mapping_by_user_id_and_project_id(
            mapped_user_id, project_id)
        existing_mapping.role_id = role_id
        existing_mapping.last_modified_by = user_id
        existing_mapping.last_modified_at = datetime.now(timezone.utc)
        result = await self.users_projects_mappings_dao.update_users_projects_mapping(existing_mapping)
        return result

    async def get_mappings_by_user_id(self, user_id: str) -> List[UsersProjectsMapping]:
        return await self.users_projects_mappings_dao.get_users_projects_mapping_by_user_id(user_id)

    async def get_mappings_by_project_id(self, project_id: str, get_server_admins: bool = True) -> List[
        UsersProjectsMapping]:
        return await self.users_projects_mappings_dao.get_users_projects_mapping_by_project_id(project_id,
                                                                                               get_server_admins)

    async def get_users_dict(self, users_list: List[str]) -> Dict[str, User]:
        unique_users = list(set([user_id for user_id in users_list if user_id and user_id != '']))
        if len(unique_users) == 0:
            return {}
        custom_query_with_unique_users = {
            "_id": {"$in": [ObjectId(user_id) for user_id in unique_users]}
        }
        fetched_user_details, count = await self.authentication_dao.get_paginated_users_list_async(search_term='',
                                                                                                   page_limit=len(
                                                                                                       users_list),
                                                                                                   page_number=1,
                                                                                                   custom_query=custom_query_with_unique_users)
        if len(fetched_user_details) != len(unique_users):
            logger.error(f"unable to fetch users from db expected count {len(unique_users)}, fetched count {len(fetched_user_details)}")
        return {user.id: user for user in fetched_user_details}

    async def get_mapping_details_for_server_admin(self, user_id) -> List[UserProjectsMappingWithDetails]:
        # server admin fetched to fetch his projects
        projects, count = await self.projects_dao.get_all_projects_async(search_term='',
                                                                         page_number=1, page_limit=1000)
        if len(projects) != count:
            raise Exception(f'Got more than max limit projects {count}')
        results = [UserProjectsMappingWithDetails(
            user_id=user_id,
            project_id=project.get('_id', 'NotFound'),
            role_id='Not Applicable',
            role_name='Not Applicable',
            project_name=project.get('name', ''),
            description=project.get('description', ''),
            is_active=True,
            created_at=project.get('created_at', ''),
            last_modified_at=project.get('last_modified_at', ''),
            last_accessed_at=project.get('last_accessed_at', ''),
            last_modified_by=project.get('last_modified_by_id', ''),
            created_by=project.get('created_by', ''),
            project_owner_id=project.get('owner_id', ''),
            favourited_by=project.get('favorited_by', [])
        ) for project in projects if project.get('is_active', False)]
        fetch_user_names_for = []
        for result in results:
            fetch_user_names_for.append(result.last_modified_by)
            fetch_user_names_for.append(result.project_owner_id)
        users_dict = await self.get_users_dict(fetch_user_names_for)
        for result in results:
            result.last_modified_by_name = users_dict.get(
                result.last_modified_by).name if result.last_modified_by in users_dict else 'Not Found'
            result.project_owner_name = users_dict.get(
                result.project_owner_id).name if result.project_owner_id in users_dict else 'Not Found'
            result.server_role_value = users_dict.get(result.user_id).server_role_value if result.user_id in users_dict else 4
        return results
    
    @cache
    async def get_all_roles_features_dict(self) -> Dict[str, RolesFeaturesMap]:
        all_roles_features = (await self.roles_features_dao.get_all_roles_features_async(search_term='', page_number=1, page_limit=1000))[0]
        role_names_dict = {item.id: item.name for item in all_roles_features}
        return role_names_dict

    async def get_mapping_details_by_user_id(self, user_id: str) -> List[UserProjectsMappingWithDetails]:
        results = await self.users_projects_mappings_dao.get_users_projects_mapping_details_by_user_id(user_id)
        return results

    async def get_mapping_details_by_project_id(self, project_id: str) -> List[UserProjectsMappingWithDetails]:
        mappings = await self.users_projects_mappings_dao.get_users_projects_mapping_by_project_id(project_id)
        role_names_dict = await self.get_all_roles_features_dict()
        # fetch users details
        duplicate_users_ids = [mapping.user_id for mapping in mappings]
        duplicate_users_ids.extend([mapping.last_modified_by for mapping in mappings])
        duplicate_users_ids.extend([mapping.created_by for mapping in mappings])
        users_dict = await self.get_users_dict(duplicate_users_ids)
        results = []
        for mapping in mappings:
            if mapping.user_id in users_dict:
                user: User = users_dict.get(mapping.user_id)
                users_name = user.name
                is_inactive_user = user.status == UserStatus.INACTIVE.value
                if is_inactive_user:
                    continue  # skip sending inactive users
                last_modified_name = user.role_updated_by_name
                created_by_name = 'NotFound'
                if mapping.created_by in users_dict:
                    created_by_name = users_dict.get(mapping.created_by).name
                details = UserProjectsMappingWithDetails(**mapping.model_dump(),
                                                        role_name=role_names_dict.get(
                                                            mapping.role_id, 'NotFound'),
                                                        user_name=users_name, last_modified_by_name=last_modified_name,
                                                        created_by_name = created_by_name, server_role_value=user.server_role_value)
                results.append(details)

        return results

    async def get_users_who_are_not_in_project(self, project_id: str, search_term: str = '', page_number: int = 1,
                                               page_limit: int = 100) -> Tuple[List[UserDetails], int]:
        custom_query = {"server_role_value": {"$in": [2, 4]}, "status": {"$ne": UserStatus.INACTIVE.value}}
        users, total_count = await self.authentication_dao.get_paginated_users_list_async(
            search_term, page_number, page_limit, custom_query)
        mappings = await self.users_projects_mappings_dao.get_users_projects_mapping_by_project_id(project_id)
        mapped_user_ids = [mapping.user_id for mapping in mappings]
        total_unmapped_count = total_count - len(mapped_user_ids)
        user_details = [UserDetails(**user.model_dump(), user_id=user.id, user_name=user.name)
                        for user in users if user.id not in mapped_user_ids]
        return user_details, total_unmapped_count

    async def get_mapping(self, user_id: str, project_id: str) -> UsersProjectsMapping:
        return await self.users_projects_mappings_dao.get_users_projects_mapping_by_user_id_and_project_id(user_id,
                                                                                                           project_id)

    async def delete_user_proj_mappings(self, mapped_user_id: str, project_id: str, user_id: str = ''):
        deleted_count = await self.users_projects_mappings_dao.delete_users_projects_mappings(user_id=mapped_user_id,
                                                                                              project_id=project_id)
        return deleted_count

    async def update_user_roles(self, changes: List[UserIdRoleValueMap], user_id: str,
                                delete_existing_mappings: bool = True):

        users = [User(**await self.authentication_dao.get_user_by_id(change.user_id)) for change in changes]
        if len(users) != len(changes):
            raise ValueError(f"Fetched users count not matching with changes count {len(users)}, {len(changes)}")
        for i, user in enumerate(users):
            logger.info(f"{changes[i]}")
            user.server_role_value = changes[i].server_role_value
            user.server_role = changes[i].server_role
            user.role_updated_at = datetime.now(timezone.utc)
            user.role_updated_by_id = user_id
            # note: name who updated role is fetched dynamically
            logger.info(f"updating userid {user.id} to server_role {user.server_role} by {user_id}")
        await self.authentication_dao.update_users(users)  # updating users

        if delete_existing_mappings:
            for user in users:
                await self.users_projects_mappings_dao.delete_users_projects_mappings(user_id=user.id)
                logger.info(f"deleted user project mappings for user {user.id}")
    
    async def get_all_apps_permissions(self) -> List[AppPermission]:
        all_permissions = await self.users_projects_mappings_dao.get_all_apps_permissions()
        return all_permissions
    
    async def update_app_permission(self, app_perm: EditAppPermission, user_id):
        await self.users_projects_mappings_dao.update_app_permission(app_perm, user_id)

    async def update_app_permissions(self, app_perms_list: List[EditAppPermission], user_id):
        await self.users_projects_mappings_dao.update_app_permissions(app_perms_list, user_id)
