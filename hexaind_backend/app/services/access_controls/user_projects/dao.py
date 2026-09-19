import datetime
from bson import ObjectId
from typing import List
from app.core.dao.dao_base import DaoBase
from app.services.access_controls.user_projects.schemas import AppPermission, EditAppPermission, UsersProjectsMapping, UserProjectsMappingWithDetails
from app.services.admin.authentication.schemas import UserStatus
from app.services.access_controls.roles.schemas import SystemGeneratedProjectRoles, RolesFeaturesMap
from app.services.access_controls.roles.utils import get_system_generated_role_features_map
from app.services.admin.authentication.utils import mongo_list_json_async 
from app.services.admin.authentication.dao import get_utc_date_time


class UsersProjectsMappingsDao(DaoBase):

    @staticmethod
    def create_composite_key(user_id: str, project_id: str) -> str:
        if user_id and project_id:
            return f"{user_id}_{project_id}"
        raise ValueError(f"{user_id} , {project_id} must be present to create composite key")

    async def insert_users_projects_mapping(self, mapping: UsersProjectsMapping) -> str:
        payload = mapping.model_dump()
        payload["_id"] = self.create_composite_key(mapping.user_id, mapping.project_id)
        result = await self.db_async.users_projects_mappings.insert_one(payload)
        if not result:
            raise Exception("Unable to create UsersProjectsMapping record")

        mapping_id = str(result.inserted_id)
        return mapping_id

    async def update_users_projects_mapping(self, mapping: UsersProjectsMapping) -> str:
        _id = self.create_composite_key(mapping.user_id, mapping.project_id)
        result = await self.db_async.users_projects_mappings.update_one(
            {"_id": _id},
            {"$set": mapping.model_dump(exclude={'id'})},
        )
        if result.matched_count == 0:
            raise Exception("No users projects mapping found")
        if result.modified_count == 0:
            raise Exception("No users projects mapping was modified")
        return mapping.id

    async def get_users_projects_mapping_by_user_id(self, user_id: str) -> List[UsersProjectsMapping]:
        mappings_cursor = self.db_async.users_projects_mappings.find({"user_id": user_id})
        mappings = await mappings_cursor.to_list(None)
        results = []
        for mapping in mappings:
            mapping['_id'] = str(mapping['_id'])
            results.append(UsersProjectsMapping(**mapping))
        return results
    
    async def get_users_projects_mapping_details_by_user_id(self, user_id: str) -> List[UsersProjectsMapping]:
        pipeline = [
            {
                "$match": {'user_id': user_id}  # Add your query conditions here
            },
            {
                "$lookup": {
                    "from": "users",
                    "let": {"user_id_obj": {"$toObjectId": "$user_id"}},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$eq": ["$_id", "$$user_id_obj"]
                                }
                            }
                        },
                        {
                            "$project": {"_id": 1,"name": 1, "server_role_value": 1}
                        }
                    ],
                    "as": "mapping_user"
                }
            },
            {
                "$lookup": {
                    "from": "projects",
                    "let": {"project_id": {"$toObjectId": "$project_id"}},
                    "pipeline": [
                        {
                            "$match": {
                                "$and": [
                                    {
                                        "$expr": {
                                            "$eq": ["$_id", "$$project_id"]
                                        }
                                    },
                                    {
                                        "is_active": True
                                    }
                                ]
                            }
                        },
                        {
                            "$project": {
                                "_id": 1,
                                "name": 1,
                                "owner_id": 1,
                                "owner_name": 1,
                                "description": 1,
                                "last_accessed_at": 1,
                                "favorited_by": 1,
                                "created_at": 1
                            }
                        }
                    ],
                    "as": "mapped_project"
                }
            },
            {
                "$lookup": {
                    "from": "roles_features_mapping",
                    "let": {"role_id_obj": {"$toObjectId": "$role_id"}},

                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$eq": ["$_id", "$$role_id_obj"]
                                }
                            }
                        },
                        {
                            "$project": {
                                "_id": 1,
                                "name": 1
                            }
                        }
                    ],
                    "as": "role"
                }
            },
            {
                "$unwind": "$mapping_user"
            },
            {
                "$unwind": "$mapped_project"
            },
            {'$sort': {'mapped_project.name': 1 }},
            {
                "$unwind": "$role"
            },
            {
                "$lookup": {
                    "from": "users",
                    "let": {"created_by_obj": {"$toObjectId": "$created_by"}},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$eq": ["$_id", "$$created_by_obj"]
                                }
                            }
                        },
                        {
                            "$project": {"_id": 1, "name": 1}
                        }
                    ],
                    "as": "created_by_user"
                }
            },
            {
                "$unwind": "$created_by_user"
            },
            {
                "$lookup": {
                    "from": "users",
                    "let": {"last_modified_by_obj": {"$toObjectId": "$last_modified_by"}},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$eq": ["$_id", "$$last_modified_by_obj"]
                                }
                            }
                        },
                        {
                            "$project": {"_id": 1, "name": 1}
                        }
                    ],
                    "as": "last_modified_by_user"
                }
            },
            {
                "$unwind": "$last_modified_by_user"
            },
            {
                "$project": {
                    "_id": 1,
                    "user_id": 1,
                    "project_id": 1,
                    "role_id": 1,
                    "is_active": 1,
                    "created_at": "$mapped_project.created_at",
                    "created_by": 1,
                    "last_modified_at": 1,
                    "last_modified_by": 1,
                    "user_name": "$mapping_user.name",
                    "project_name": "$mapped_project.name",
                    "project_owner_id": "$mapped_project.owner_id",
                    "project_owner_name": "$mapped_project.owner_name",
                    "description": "$mapped_project.description",
                    "last_accessed_at": {
                        "$dateToString": {
                            "format": "%Y-%m-%dT%H:%M:%S.%LZ",
                            "date": { "$ifNull": ["$mapped_project.last_accessed_at", "$mapped_project.created_at"] }
                        }
                    },
                    "created_by_name": "$created_by_user.name",
                    "last_modified_by_name": "$last_modified_by_user.name",
                    "role_name": "$role.name",
                    "favorited_by": "$mapped_project.favorited_by",
                    "server_role_value": "$mapping_user.server_role_value"
                }
            }
        ]
        mappings_cursor = self.db_async.users_projects_mappings.aggregate(pipeline)
        mappings = await mappings_cursor.to_list(None)
        results = []
        for mapping in mappings:
            mapping['_id'] = str(mapping['_id'])
            results.append(UserProjectsMappingWithDetails(**mapping))
        return results

    async def get_users_projects_mapping_by_project_id(self, project_id: str, get_server_admins: bool = True) -> List[
        UsersProjectsMapping]:
        mappings_cursor = self.db_async.users_projects_mappings.find({"project_id": project_id})
        mappings = await mappings_cursor.to_list(None)
        results = []
        for mapping in mappings:
            mapping['_id'] = str(mapping['_id'])
            if not mapping['last_modified_at'].tzinfo:
                mapping['last_modified_at'] = mapping['last_modified_at'].replace(tzinfo=datetime.timezone.utc)
            results.append(UsersProjectsMapping(**mapping))

        if get_server_admins:
            serv_admins_as_proj_admins_list = await self.get_server_role_admins_as_project_admins_for_project(
                project_id)
            # Add All Server Admins as Project Admins
            results.extend(serv_admins_as_proj_admins_list)
        return results
    
    async def get_server_role_admins_as_project_admins_for_project(self, project_id: str) -> List[UsersProjectsMapping]:
        proj_admin_role: RolesFeaturesMap = get_system_generated_role_features_map(SystemGeneratedProjectRoles.PROJECT_ADMINISTRATOR)
        project = await self.db_async.projects.find_one({'_id': ObjectId(project_id)})
        proj_users = await (self.db_async.users_projects_mappings.find({'project_id': project_id}, {'user_id':1})).to_list(None)
        proj_user_ids = list(map(lambda user: ObjectId(user['user_id']), proj_users))
        # get not inactive & ignore server admins exists as project users        
        admin_users_cur = self.db_async.users.find({'server_role_value': 1, 'status': {'$ne':UserStatus.INACTIVE}, '_id': {'$nin': proj_user_ids}}, {'_id': 1})
        admin_users = await admin_users_cur.to_list(None)
        serv_admins_as_proj_admins_list = []
        if not project['created_at'].tzinfo:
                project['created_at'] = project['created_at'].replace(tzinfo=datetime.timezone.utc)
        for user in admin_users:
            user_proj_map_id = self.create_composite_key(str(user['_id']), project_id)
            proj_users_mapping = UsersProjectsMapping(_id=user_proj_map_id,
                                 user_id=str(user['_id']),
                                 project_id=project_id,
                                 role_id=proj_admin_role.id,
                                 is_active=True,
                                 created_at=project['created_at'],
                                 created_by=project['created_by'],
                                 last_modified_at=project['created_at'],
                                 last_modified_by=project['created_by'])
            serv_admins_as_proj_admins_list.append(proj_users_mapping)
        return serv_admins_as_proj_admins_list

    async def get_users_projects_mapping_by_user_id_and_project_id(self, user_id: str,
                                                                   project_id: str) -> UsersProjectsMapping:
        _id = self.create_composite_key(user_id, project_id)
        mapping = await self.db_async.users_projects_mappings.find_one({"_id": _id})
        return UsersProjectsMapping(**mapping)

    async def delete_users_projects_mappings(self, user_id: str, project_id: str = None) -> int:
        filter_ = {"user_id": user_id}
        if project_id:
            filter_["project_id"] = project_id

        existing_record_count = await self.db_async.users_projects_mappings.count_documents(filter_)

        if existing_record_count >= 0:
            result = await self.db_async.users_projects_mappings.delete_many(filter_)
            if result.deleted_count != existing_record_count:
                raise Exception(
                    f"Found {existing_record_count} records, but was able to delete only {result.deleted_count}")
            return existing_record_count
        else:
            raise Exception(f"Deleting a non existing records {user_id} , {project_id}")

    async def get_all_apps_permissions(self)->List[AppPermission]:
        app_permissions_cur = self.db_async.app_permissions.find({'is_active': True})
        app_permissions_dict_list = await mongo_list_json_async(app_permissions_cur)
        app_permissions_list = [AppPermission(**app_perm_dict) for app_perm_dict in app_permissions_dict_list]
        return app_permissions_list
    
    async def update_app_permission(self, app_perm: EditAppPermission, user_id):
        tz_dt = await get_utc_date_time()
        app_perm_dict = await self.db_async.app_permissions.find_one({"app_name": app_perm.app_name})
        if app_perm_dict == None:
            await self.db_async.app_permissions.insert_one({"app_name": app_perm.app_name, "default_user": app_perm.default_user, "is_active": True, "last_modified_at":tz_dt, "last_updated_by": user_id})
        else:
            await self.db_async.app_permissions.update_one({"app_name": app_perm.app_name}, {"$set":{"default_user": app_perm.default_user, "last_modified_at":tz_dt, "last_updated_by": user_id}})
    
    async def update_app_permissions(self, app_perms_list: List[EditAppPermission], user_id):
        tz_dt = await get_utc_date_time()
        for app_perm  in app_perms_list:
            app_perm_dict = await self.db_async.app_permissions.find_one({"app_name": app_perm.app_name})
            if app_perm_dict == None:
                await self.db_async.app_permissions.insert_one({"app_name": app_perm.app_name, "default_user": app_perm.default_user, "is_active": True, "last_modified_at":tz_dt, "last_updated_by": user_id})
            else:
                await self.db_async.app_permissions.update_one({"app_name": app_perm.app_name}, {"$set":{"default_user": app_perm.default_user, "last_modified_at":tz_dt, "last_updated_by": user_id}})


