from typing import List, Tuple

from app.core.dao.dao_base import DaoBase
from app.services.access_controls.roles.schemas import RolesFeaturesMap
from bson import ObjectId
import logging

from app.services.admin.authentication.dao import get_utc_date_time, encrypt_password, mongo_list_json_async
from app.config.env_vars import environment
from app.services.access_controls.roles.schemas import (
    AppNames)

logger = logging.getLogger(__package__)

class RolesFeaturesMapDao(DaoBase):

    # used only for generating system generated roles
    async def insert_or_update_roles_features_with_id(
            self, roles_features: RolesFeaturesMap, skip_fields: List = None
    ):
        payload = roles_features.model_dump(exclude={"id"})
        if skip_fields:
            for field in skip_fields:
                payload.pop(field)
        update_result = await self.db_async.roles_features_mapping.update_one({'_id': ObjectId(roles_features.id)},
                                                                              {"$set": payload}, upsert=True)
        return {
            'matched_count': update_result.matched_count,
            'modified_count': update_result.modified_count,
            'upserted_id': update_result.upserted_id,
            'acknowledged': update_result.acknowledged
        }

    async def insert_roles_features(
            self, roles_features: RolesFeaturesMap
    ) -> str:

        existing_record = await self.db_async.roles_features_mapping.find_one(
            {"name": roles_features.name}
        )
        if existing_record:
            raise Exception(
                f"A role with name '{roles_features.name}' already exists."
            )

        result = await self.db_async.roles_features_mapping.insert_one(
            roles_features.model_dump(exclude={"id"})
        )
        if not result:
            raise Exception(
                "not able to create roles features record")

        roles_features_id = str(result.inserted_id)

        return roles_features_id

    async def update_roles_features(
            self, roles_features: RolesFeaturesMap
    ) -> str:

        result = await self.db_async.roles_features_mapping.update_one(
            {"_id": ObjectId(roles_features.id)},
            {"$set": roles_features.model_dump(exclude={"id"})},
        )
        if result.matched_count == 0:
            raise Exception("No role feature mapping found")
        if result.modified_count == 0:
            raise Exception("No role feature mapping Modified")
        return roles_features.id

    async def get_all_roles_features_async(
            self, search_term: str, page_number: int, page_limit: int
    ) -> Tuple[List[RolesFeaturesMap], int]:

        offset = (page_number - 1) * page_limit
        query = {}

        if search_term:
            search_query = {
                "$regex": search_term,
                "$options": "i",
            }  # Case-insensitive search
            query["$or"] = [
                {"name": search_query},
                {"description": search_query},
                {"owner_name": search_query},
            ]

        roles_features_curser = (
            self.db_async.roles_features_mapping.aggregate(
                [
                    {"$match": query},
                    {
                        "$addFields": {
                            "_id": {"$toString": "$_id"},
                            "created_at": {
                                "$dateToString": {
                                    "format": "%Y-%m-%dT%H:%M:%S",
                                    "date": "$created_at",
                                }
                            },
                            "last_modified_at": {
                                "$dateToString": {
                                    "format": "%Y-%m-%dT%H:%M:%S",
                                    "date": "$last_modified_at",
                                }
                            },
                        }
                    },
                    {"$skip": offset},
                    {"$limit": page_limit},
                ]
            )
        )

        roles_features_mapping = await roles_features_curser.to_list(
            length=page_limit
        )
        roles_features_mapping_list = [
            RolesFeaturesMap(**role_feature_map)
            for role_feature_map in roles_features_mapping
        ]

        total_count = await self.db_async.roles_features_mapping.count_documents(
            query
        )
        return roles_features_mapping_list, total_count

    async def get_role_feature_map_id_async(self, role_id: str
                                            ) -> RolesFeaturesMap:

        result = await self.db_async.roles_features_mapping.find_one(
            {"_id": ObjectId(role_id)}
        )
        if not result:
            raise Exception(
                "unable to fetch the role feature mapping at this moment"
            )

        result["_id"] = str(result["_id"])

        return RolesFeaturesMap(**result)

    async def get_role_by_name_async(
            self, role_name: str
    ) -> RolesFeaturesMap:

        existing_record = await self.db_async.roles_features_mapping.find_one(
            {"name": role_name}
        )
        if not existing_record:
            raise KeyError(f"role with name {role_name} not found")

        existing_record['_id'] = str(existing_record['_id'])
        return RolesFeaturesMap(**existing_record)

    async def insert_or_update_server_roles(self):
        logger.info("Insert or Update roles method")
        roles_cur = self.db_async.roles.find({})
        roles_list = await mongo_list_json_async(roles_cur)

        logger.info(f"Existing foles list:{roles_list}")

        if roles_list is None or len(roles_list) == 0:
            logger.info("Didn't fine any roles. going to insert")
            self.db_async.roles.insert_many(
                [{"_id": "1", "role_name": "Server Admin", "role_value": 1},
                 {"_id": "2", "role_name": "Project Admin", "role_value": 2},
                 {"_id": "3","role_name": "Default User","role_value": 4}])
        else:
            logger.info("Going to make correction like changing rol_value float/string to int if any such")
            for role in roles_list:

                if role['_id'] == '1':
                    role_value = 1
                elif role['_id'] == '2':
                    role_value = 2
                else:
                    role_value = 4

                await self.db_async.roles.update_one({'_id':role['_id']}, {'$set':{'role_value': role_value}})

    async def create_server_admin_user(self):
        server_admin_email = environment.server_admin_email_to_create_if_no_server_admin.strip()
        server_admin_pwd = environment.server_admin_password.strip()

        logger.info("Going to check any users exists")
        users_cnt = await self.db_async.users.count_documents({})
        if users_cnt > 0:
            logger.info(f"Found users. Number of users found{users_cnt}")
            users_cur = self.db_async.users.find({})
            users_list = await mongo_list_json_async(users_cur)
            logger.info("Goint to change users server_role_value to int if any found like string/ float")
            for user in users_list:
                if isinstance(user['server_role_value'], int) == False:
                    await self.db_async.users.update_one({'email': user['email']}, {'$set':{'server_role_value': int(user['server_role_value'])}})

        tz_dt = await get_utc_date_time()
        pwd_hash  = encrypt_password(server_admin_pwd)

        is_sso_user = False

        if (environment.server_admin_is_sso_user and environment.sso_login_allowed) or (environment.sso_login_allowed and environment.form_login_allowed == False):
                is_sso_user = True

        admin_user = await self.db_async.users.find_one({'email': server_admin_email})
        if admin_user:
            update_flds_dict = {'password': pwd_hash, 'updated_at': tz_dt, 'account_locked_until': None, 'failed_login_attempts': 0, 'status': 'Active', 'is_sso_user': is_sso_user}
            if 'role_updated_by_id' not in admin_user:
                update_flds_dict['role_updated_by_id'] = str(admin_user['_id'])

            if 'server_role' not in admin_user:
                update_flds_dict['server_role'] = 'Server Role'

            user_names_dict = self.get_user_names_dict(admin_user['email'], admin_user['name'], admin_user['first_name'], admin_user['last_name'])
            update_flds_dict.update(user_names_dict)

            await self.db_async.users.update_one({'email': admin_user['email']}, {'$set': update_flds_dict})
        else:
            user_names_dict = self.get_user_names_dict(server_admin_email)

            admin_user_dict = {'email': server_admin_email, 
                            'password': pwd_hash, 
                            'created_at': tz_dt, 'updated_at': tz_dt, 'status': 'Active', 'login_status': True, 
                            'server_role_value': 1, 'last_login_date': tz_dt, 
                            'is_sso_user': is_sso_user, 'server_role': 'Server Admin', 'role_updated_at':tz_dt}
            
            admin_user_dict.update(user_names_dict)

            insert_resp = await self.db_async.users.insert_one(admin_user_dict)
            inserted_id = str(insert_resp.inserted_id)
            await self.db_async.users.update_one({'email':server_admin_email}, {'$set':{'invited_by_id': inserted_id, 'role_updated_by_id': inserted_id}})
        await self.db_async.users.update_one({'email':server_admin_email}, {'$set':{'default_server_admin': True}})

   
    def get_user_names_dict(self, email: str, existing_name: str = '', existing_fname:str = '', existing_lname:str = ''):
        first_name = environment.first_name.strip()
        last_name = environment.last_name.strip()
        user_first_name = ''
        user_last_name = ''
        user_name = ''

        # Treat environment values as first name & last name
        if first_name and len(first_name) > 0:
            user_first_name = first_name

        if last_name and len(last_name) > 0:
            user_last_name = last_name

        # if configuration names not provided, existing names present, Keep them as it is.
        if len(user_first_name) == 0:
            if  len(existing_fname) == 0 and len(existing_name) > 0:
                user_first_name = existing_name
            elif len(existing_fname) > 0 and len(existing_name) == 0:
                user_first_name = existing_fname
            else:
                user_first_name = email
    
        if len(user_last_name) == 0 and len(existing_lname) > 0:
            user_last_name = existing_lname
            

        user_name = f"{user_first_name} {user_last_name}"
        user_names_dict = {}
        user_names_dict['first_name'] = user_first_name
        user_names_dict['last_name'] = user_last_name
        user_names_dict['name'] = user_name
        return user_names_dict

    async def generate_app_permisssions_table(self) -> int:
        values_list =  [app.value for app in AppNames]
        permissions_created = 0
        apps_to_ins_list = []
        tz_dt = await get_utc_date_time()
        for app_name in values_list:
            app = await self.db_async.app_permissions.find_one({"app_name": app_name})
            if app == None:
                apps_to_ins_list.append({"app_name": app_name, "default_user": False, "is_active": True, "last_modified_at":tz_dt, "last_updated_by": "SYSTEM"})
                
        if len(apps_to_ins_list) > 0:
            logger.info(f"Inserted {len(apps_to_ins_list)} number of App Permissions")
            await self.db_async.app_permissions.insert_many(apps_to_ins_list)
            permissions_created = len(apps_to_ins_list)
        return permissions_created