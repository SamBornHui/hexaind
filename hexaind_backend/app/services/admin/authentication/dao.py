from datetime import datetime,timezone, timedelta
import time
from bson.objectid import ObjectId
import os
import random
import string
from typing import List, Dict, Optional, Tuple
import asyncio
import logging

from pymongo import UpdateOne, MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.env_vars import environment
from app.core.services.jwt_token_utils.jwt_token_utils import is_email_token_time_expired

from app.core.dao.dao_base import DaoBase
from app.services.admin.authentication.schemas import (
    InviteUserSchema,
    ChangeUserNamesSchema,
    InviteBulkUsersSchema,
    SuperSetData,
    UserEmail,
    UserStatus,
    UpdateUserByAdminSchema,
    GenericResponse,
    User,
)
from app.services.admin.authentication.utils import http_err_unauthorized, get_object_id, mongo_list_json_async

ACCOUNT_UNLOCK_WAIT_TIME_IN_MINS  = os.getenv('ACCOUNT_UNLOCK_WAIT_TIME_IN_MINS', '1')
MAX_LOGIN_FAIL_ATTEMPTS = os.getenv('MAX_FAIL_ATTEMPTS', '3')

logger = logging.getLogger(__package__)

acc_lock_time = None
def get_acc_loc_time():
    global acc_lock_time
    if acc_lock_time is None:
        try:
            acc_lock_time = int(ACCOUNT_UNLOCK_WAIT_TIME_IN_MINS)
        except:
            acc_lock_time = 1

    return acc_lock_time

max_login_atmpts = None
def get_max_login_atmpts():
    global max_login_atmpts
    if max_login_atmpts is None:
        try:
            max_login_atmpts = int(MAX_LOGIN_FAIL_ATTEMPTS)
        except:
            max_login_atmpts = 3

    return max_login_atmpts


async def get_utc_date_time():
    dt = datetime.now(timezone.utc)
    tz_dt = dt.astimezone()
    return tz_dt

users_fld_names = None

class AuthenticationDao(DaoBase):

    role_id_roles_dict = None
    _lock = asyncio.Lock()

    def get_user_by_id_sync(self, user_id: str) -> Optional[User]:
        user_document = self.db_sync.users.find_one({"_id":ObjectId(user_id)})
        if user_document is None:
            return None
        user_document['_id'] = str(user_document['_id'])
        return User(**user_document)
    
    def delete_user_record(self, user_id: str):
        result = self.db_sync.users.delete_one({"_id":ObjectId(user_id)})
        if not result.deleted_count > 0:
            return False
        
        return True
    
    def update_user_record(self, user_id: str, user_rec: SuperSetData):
        result = self.db_sync.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"data_superset": user_rec.model_dump(mode="json")}},
        )
        if not result.matched_count > 0:
            return False

        return True

    async def get_role_value_by_id(self, role_id: str):
        role_value = None
        await AuthenticationDao._lock.acquire()
        try:
            if AuthenticationDao.role_id_roles_dict is None:
                await self.load_roles_to_dict()

            if AuthenticationDao.role_id_roles_dict and role_id in AuthenticationDao.role_id_roles_dict:
                role_value =  AuthenticationDao.role_id_roles_dict[role_id]['role_value']
        finally:
            AuthenticationDao._lock.release()
        return role_value

    async def get_role_by_id(self, role_id: str):
        server_role = None
        await AuthenticationDao._lock.acquire()
        try:
            if AuthenticationDao.role_id_roles_dict is None:
                await self.load_roles_to_dict()

            if AuthenticationDao.role_id_roles_dict and role_id in AuthenticationDao.role_id_roles_dict:
                server_role =  AuthenticationDao.role_id_roles_dict[role_id]
        finally:
            AuthenticationDao._lock.release()
        return server_role

    async def load_roles_to_dict(self):
        roles_cursor = self.db_async.roles.find({})
        roles_list = await mongo_list_json_async(roles_cursor)
        AuthenticationDao.role_id_roles_dict = {}
        for role in roles_list:
            AuthenticationDao.role_id_roles_dict[str(role['_id'])] = {'role_name': role['role_name'], 'role_value': role['role_value']}

    async def add_new_role_to_roles_dict(self, role_dict: dict):

        await AuthenticationDao._lock.acquire()
        try:
            role_name_val_dict = {'role_name': role_dict['role_name'], 'role_value': role_dict['role_value']}
            if AuthenticationDao.role_id_roles_dict != None:
                AuthenticationDao.role_id_roles_dict[str(role_dict['_id'])] = role_name_val_dict
            else:
                AuthenticationDao.role_id_roles_dict = {str(role_dict['_id']): role_name_val_dict}
        finally:
            AuthenticationDao._lock.release()

    async def get_paginated_users_list_async(self, search_term: str, page_number: int, page_limit: int,
                                             custom_query=None, fetch_role_details:bool=False) -> Tuple[List[User], int]:
        query = {} if custom_query is None else custom_query
        if search_term:
            search_query = {"$regex": search_term, "$options": "i"}  # Case-insensitive search
            query["$or"] = [{"name": search_query}, {"email": search_query}]

        offset = (page_number - 1) * page_limit if page_number and page_limit else 0
        aggregate_pipe_line = [{"$match": query if query else {}}]
        if fetch_role_details:
            aggregate_pipe_line.extend([
                {
                    "$set": {
                        "roleUpdatedById": {
                            "$cond": {
                                "if": {"$in": ["$role_updated_by_id", [None, ""]]},
                                "then": None,  # Explicitly set to None to skip the lookup
                                "else": {"$toObjectId": "$role_updated_by_id"}
                            }
                        }
                    }
                },
                {
                    "$lookup": {
                        "from": "users",
                        "localField": "roleUpdatedById",
                        "foreignField": "_id",
                        "as": "role_updated_by_name"
                    }
                },
                {
                    "$unwind": {
                        "path": "$role_updated_by_name",
                        "preserveNullAndEmptyArrays": True  # Important to keep documents without matches
                    }
                },
                {
                    "$set": {
                        "role_updated_by_name": {
                            "$cond": {
                                "if": {"$eq": ["$role_updated_by_name", {}]},
                                "then": "Not Found",
                                "else": "$role_updated_by_name.name"
                            }
                        }
                    }
                }
            ])

        aggregate_pipe_line.extend(
            [
                {"$addFields": {"_id": {"$toString": "$_id"},
                                "created_at": {
                                    "$dateToString": {"format": "%Y-%m-%dT%H:%M:%S",
                                                      "date": "$created_at"}},
                                "last_modified_at": {
                                    "$dateToString": {"format": "%Y-%m-%dT%H:%M:%S",
                                                      "date": "$last_modified_at"}},
                                "role_updated_at":{
                                    "$dateToString": {"format": "%Y-%m-%dT%H:%M:%S",
                                                      "date": "$role_updated_at"}}
                                }},
                {"$skip": offset},
                {"$limit": page_limit}
            ]
        )
        cursor = self.db_async.users.aggregate(aggregate_pipe_line)
        users_dicts = await cursor.to_list(length=page_limit)
        users = [User(**user_dict) for user_dict in users_dicts]
        total_count = await self.db_async.users.count_documents(query)
        return users, total_count

    async def get_users_with_ref_data(self, query: dict):
        # Extract the field names from the sample document
        global users_fld_names
        if users_fld_names is None:
            template_document = await self.db_async.users.find_one({})
            users_fld_names = list(template_document.keys())

        pipeline = [
            {"$match": query},  # {"status": UserStatus.ACTIVE, 'email': email}
            {'$sort': {'name': 1 }},
            {
                '$addFields': {
                    'user_id_str': {'$toString': '$_id'}
                }
            },
            {
                '$lookup': {
                    'from': 'users_projects_mappings',
                    'let': {'user_id_str': '$user_id_str'},
                    'pipeline': [
                        {'$match': {'$expr': {'$eq': ['$user_id', '$$user_id_str']}}},
                        {'$count': 'count'}
                    ],
                    'as': 'user_projects'
                }
            },
            {
                '$addFields': {
                    'user_projs_count': {
                        '$arrayElemAt': ['$user_projects.count', 0]
                    }
                }
            },
            {
                '$lookup': {
                    'from': 'projects',
                    'pipeline': [
                        {'$count': 'projs_count'}
                    ],
                    'as': 'all_projects'
                }
            },
            {
                '$addFields': {
                    'all_projects_count': {
                        '$arrayElemAt': ['$all_projects.projs_count', 0]
                    }
                }
            },
            {
                '$addFields': {
                    'user_projects_count': {
                        '$cond': {
                            'if': {'$eq': ['$server_role_value', 1]},
                            'then': '$all_projects_count',
                            'else': '$user_projs_count'
                        }
                    }
                }
            },
            {
                "$set": {
                    "invitedByObjId": {"$toObjectId": "$invited_by_id"},
                    "last_login_date": {
                        "$dateToString": {
                            "format": "%Y-%m-%dT%H:%M:%S.%LZ",                            
                            "date": { "$ifNull": ["$last_login_date", None] }
                        }
                    },
                    "created_at": {
                        "$dateToString": {
                            "format": "%Y-%m-%dT%H:%M:%S.%LZ",                            
                            "date": { "$ifNull": ["$created_at", None] }
                        }
                    }
                }
            },
            {
                "$lookup": {
                    "from": "users",
                    "localField": "invitedByObjId",
                    "foreignField": "_id",
                    "pipeline": [
                        {
                            "$project": {"name": 1}
                        }
                    ],
                    "as": "invited"
                }
            },
            {
                "$set": {
                    "invited_by": {"$arrayElemAt": ["$invited.name", 0]}
                }
            },

            {"$unwind": "$invited"},

            {
                "$lookup": {
                    "from": "roles",
                    "localField": "server_role_value",
                    "foreignField": "role_value",
                    "as": "roles",
                }
            },
            {
                "$set": {
                    "server_role": {"$arrayElemAt": ["$roles.role_name", 0]},
                    "server_role_id": {"$arrayElemAt": [str("$roles._id"), 0]}
                }
            },
            {"$unwind": "$roles"},
            {
                "$project":{
                    "user_projects":0,
                    "user_projs_count":0,
                    "all_projects":0,
                    "all_projects_count":0,
                    "invited":0,
                    "roles":0
                    
                }
            }
        ]

        cursor  = self.db_async.users.aggregate(pipeline)
        users_list  = await mongo_list_json_async(cursor)
        return users_list

    async def get_active_user(self, email: str):
        users_list = await self.get_users_with_ref_data({"status": {"$ne": UserStatus.INACTIVE}, 'email': email})
        user = None
        if len(users_list) > 0:
            user = users_list[0]

        if user:
            user['_id'] = str(user['_id'])
        return user

    async def get_user_by_email(self, email: str):
        users_list = await self.get_users_with_ref_data({'email': email})
        user = None
        if len(users_list) > 0:
            user = users_list[0]

        if user:
            user['_id'] = str(user['_id'])
        return user

    async def get_user(self, email: str):
        user = await self.db_async.users.find_one({'email': email})
        if user:
            user['_id'] = str(user['_id'])

        return user

    async def handle_success_login(self, user_id):
        await self.db_async.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'failed_login_attempts': 0, 'account_locked_until': None}})

    async def handle_failed_login(self, user):
        await self.db_async.users.update_one({'_id': ObjectId(user['_id'])}, {'$inc': {'failed_login_attempts': 1}})

        if 'failed_login_attempts' in user and user['failed_login_attempts'] >= get_max_login_atmpts():
            lock_until = datetime.now(timezone.utc) + timedelta(minutes=get_acc_loc_time())
            await self.db_async.users.update_one({'_id': ObjectId(user['_id'])},{'$set': {'account_locked_until': lock_until}})

    async def get_user_by_id(self, user_id):
        users_list = await self.get_users_with_ref_data({'_id': ObjectId(user_id)})
        user = None

        if users_list and len(users_list) > 0:
            user = users_list[0]
            user['_id'] = str(user['_id'])

        return user

    async def deactivate_user(self, email: str):
        user = await self.db_async.users.find_one({'email': email})

        if not user:
            return http_err_unauthorized('User not found')

        utc_time = await get_utc_date_time()
        await self.db_async.users.update_one({'email': email}, {'$set': {'login_status': False, 'status': UserStatus.INACTIVE,  'updated_at': utc_time}})

        return 'User Deactivated.'

    async def activate_user_by_admin(self, email: str):
        user = await self.db_async.users.find_one({'email': email})

        if not user:
            return http_err_unauthorized(f'User not found with email {email}')

        utc_time = await get_utc_date_time()
        await self.db_async.users.update_one({'email': email}, {'$set': {'login_status': False, 'status': UserStatus.ACTIVE,  'updated_at': utc_time}})

        return 'User Activated'

    async def log_login_details(self, user: dict):
        update_dict = {'login_status': user['login_status'], 'last_login_date': user['last_login_date'], 'status': UserStatus.ACTIVE.value}
        reset_pwd_mails_cnt = await self.db_async.password_change_log.count_documents({'email':user['email'], 'pwd_reset_by_admin': True})
        if reset_pwd_mails_cnt > 0:
            user['is_pwd_reset'] = True
        await self.db_async.users.update_one({'email': user['email']}, {'$set': update_dict})

    async def mark_logout(self, email: str):
        user = await self.db_async.users.find_one({'email': email})

        if not user:
            return http_err_unauthorized('User not found')

        await self.db_async.users.update_one({'email': email}, {'$set': {'login_status': False}})
        return 'Logout Successful'

    async def insert_users(self, inv_users_list: List[InviteUserSchema], invited_by_id: str):
        tz_dt = await get_utc_date_time()
        ins_usr_rec_dict_list = []
        for invited_user in inv_users_list:
            ins_usr_rec_dict_list.append({'name': invited_user.name, 'email': invited_user.email, 'created_at': tz_dt, 'updated_at': tz_dt, 'invited_by_id': invited_by_id,
                                          'status': UserStatus.INVITED, 'server_role_value': await self.get_role_value_by_id(invited_user.server_role_id), 
                                          'is_sso_user': invited_user.is_sso_user, 'login_status': False, 'last_invite_sent_at': int(time.time())})
        await self.db_async.users.insert_many(ins_usr_rec_dict_list)

    async def insert_mail_verification_token(self, email, token):
        tz_dt = await get_utc_date_time()
        await self.db_async.tokens_email.insert_one({'email': email, 'token': token, 'created_at': tz_dt})
        await self.db_async.users.update_one({'email':email},{'$set':{'status': UserStatus.INVITED, 'last_invite_sent_at': int(time.time())}})

    async def get_mail_token(self, token):
        return await self.db_async.tokens_email.find_one({'token': token})

    async def delete_mail_token(self, token):
        return await  self.db_async.tokens_email.delete_one({'token': token})

    async def update_users(self, modified_users: List[User]):
        # Bulk write operation list
        operations = []
        for user in modified_users:
            filter_condition = {"_id": ObjectId(user.id)}
            update_data = {"$set": user.model_dump()}
            operations.append(UpdateOne(filter_condition, update_data))

        # Execute bulk update operation
        if operations:
            result = await self.db_async.users.bulk_write(operations)
            return result

    async def update_user_roles(self, site_id: str, user_id, role_id):
        # Open Site Remove any role, Add this role
        # Open User Remove that site if any, Then add Site under that role
        try:
            user_obj_id = await get_object_id(user_id)
            if user_obj_id is None:
                return http_err_unauthorized('Invalid user id')

            user = await self.db_async.users.find_one({'_id': user_obj_id})

            if user is None:
                return http_err_unauthorized('There is no user with provide user id')

            user_roles_acc = await self.db_async.user_access_roles.find_one({'user_id': user_id, 'site_id': site_id})

            if role_id == 'R1':
                await self.db_async.users.update_one({'_id': user_obj_id}, {'$set': {'server_role_value': 1}})
                if user_roles_acc is not None:
                    await self.db_async.user_access_roles.remove({'user_id': user_id})
            else:
                await self.db_async.users.update_one({'_id': user_obj_id}, {'$set': {'server_role_value': 3}})
                time_stamp = await get_utc_date_time()
                if user_roles_acc is None:
                    await self.db_async.user_access_roles.insert_one({'user_id': user_id, 'site_id': site_id, 'role_id': role_id, 'created_date': time_stamp, 'updated_date': time_stamp})
                else:
                    await self.db_async.user_access_roles.update_one({'site_id': site_id, 'user_id': user_id}, {'$set': {'role_id': role_id, 'updated_date': time_stamp}})

                return user_id
        except Exception as e:
            return http_err_unauthorized(f"Error while trying to update user roles. Exception:{e}")

    async def update_pwd_fname_lname(self, create_pwd_schema, user_name: str =''):
        try:
            email = create_pwd_schema['email']
            password = create_pwd_schema['password']
            dict_to_set = {'status': UserStatus.ACTIVE, 'password': encrypt_password(password)}

            fname_lname = ''

            if 'first_name' in create_pwd_schema and len(create_pwd_schema['first_name'].strip()) > 0:
                dict_to_set['first_name'] = create_pwd_schema['first_name']
                fname_lname = create_pwd_schema['first_name']

            if 'last_name' in create_pwd_schema and len(create_pwd_schema['last_name'].strip()) > 0:
                dict_to_set['last_name'] = create_pwd_schema['last_name']
                if len(fname_lname) > 0:
                    fname_lname = fname_lname +' '
                fname_lname = fname_lname + create_pwd_schema['last_name']

            if user_name.strip()  == '' or len(fname_lname.strip()) > 0:
                dict_to_set['name'] = fname_lname

            update_resp = await self.db_async.users.update_one({'email': email}, {'$set': dict_to_set})
            if update_resp and  update_resp.matched_count >0 and update_resp.modified_count > 0:
                return True
            else:
                http_err_unauthorized("Unable to update the password etc.. details due to un expected inputs.")
        except Exception as e:
            logger.exception("Failed to update password, first and last names.")
            return http_err_unauthorized(f"Error while trying to create/ update password. Exception:{e}")

    async def activate_user(self, email, email_verfication_token):
        is_activated = False
        try:
            update_resp = await self.db_async.users.update_one({'email': email}, {'$set': {'status': UserStatus.ACTIVE}})
            if update_resp and  update_resp.matched_count >0 and update_resp.modified_count > 0:
                is_activated = True
                await self.delete_mail_token(email_verfication_token)
            return is_activated
        except Exception:
            logger.exception('Failed to activate.')
            return False

    async def get_all_users_list(self):
        users_list = await self.get_users_with_ref_data({})
        for user in users_list:
            if user['status'] == UserStatus.INVITED and 'last_invite_sent_at' in user and \
                is_email_token_time_expired(user['last_invite_sent_at']):
                user['status'] = 'Invite Expired'

        return users_list

    async def get_user_with_roles(self, user_id):
        user = await self.db_async.users.find_one({'_id': ObjectId(user_id), 'status': UserStatus.ACTIVE}, {'password': 0})
        if user is None:
            return http_err_unauthorized('User not found')

        user['_id'] = str(user['_id'])
        user_roles = await self.get_user_access_roles(user_id)
        user['sites_and_roles'] = user_roles
        return user

    async def get_user_access_roles(self, user_id):
        user_roles_cur = self.db_async.user_access_roles.find({'user_id': user_id}, {'_id': 0, 'site_id': 1, 'role_id': 1})
        user_roles = await mongo_list_json_async(user_roles_cur)
        return user_roles

    async def update_password(self, email, new_password):
        hashpwd = encrypt_password(new_password)
        tz_dt = await get_utc_date_time()
        await self.db_async.users.update_one({'email': email}, {'$set': {'password': hashpwd, 'status': UserStatus.ACTIVE, 'updated_at': tz_dt}})
        await self.log_password_change_details(email, email, 'Password changed of their own')

    async def log_password_change_details(self, email, initiator_email, reason):
        tz_dt = await get_utc_date_time()
        insert_dict = {'email': email, 'created_by': initiator_email, 'reason': reason, 'created_date_time': tz_dt, 'pwd_reset_by_admin': False}
        if email != initiator_email:
            insert_dict['pwd_reset_by_admin'] = True
        else:
            self.db_async.password_change_log.delete_many({'email': email, 'pwd_reset_by_admin': True})
        await self.db_async.password_change_log.insert_one(insert_dict)

    async def activate_user_apply_rand_pwd(self, email):
        rand_pwd = get_rand_pwd()
        hashpwd = encrypt_password(rand_pwd)
        tz_dt = await get_utc_date_time()
        await self.db_async.users.update_one({'email': email}, {'$set': {'password': hashpwd, 'status': UserStatus.ACTIVE, 'updated_at': tz_dt}})
        return rand_pwd

    async def toggle_user_active_status(self, email):
        user = await self.get_user(email)
        if not user:
            return http_err_unauthorized("User not found")

        act_stat_val = UserStatus.INACTIVE
        if user['status'] == UserStatus.INACTIVE:
            act_stat_val = UserStatus.ACTIVE
        tz_dt = await get_utc_date_time()
        await self.db_async.users.update_one({'email': email}, {'$set': {'status': act_stat_val, 'updated_at': tz_dt}})
        return True

    async def update_user_names(self, changeUserNameSchema: ChangeUserNamesSchema):
        user = await self.get_user(changeUserNameSchema.email)
        if user is None:
            return http_err_unauthorized(f'User does not exists with email:{changeUserNameSchema.email}')
        change_flds_dict = {}
        if len(changeUserNameSchema.name.strip()) > 0:
            change_flds_dict['name'] = changeUserNameSchema.name

        if len(changeUserNameSchema.first_name.strip()) > 0:
            change_flds_dict['first_name'] = changeUserNameSchema.first_name

        if len(changeUserNameSchema.last_name.strip()) > 0:
            change_flds_dict['last_name'] = changeUserNameSchema.last_name

        tz_dt = await get_utc_date_time()
        change_flds_dict['updated_at'] = tz_dt
        await self.db_async.users.update_one({'email': changeUserNameSchema.email}, {'$set': change_flds_dict})
        return True

    async def get_existing_users_with_mail_ids(self, email_ids: list):
        users_cursor = self.db_async.users.find({'email': {'$in': email_ids}}, {'_id': 0, 'email': 1})
        users_list = await mongo_list_json_async(users_cursor)
        users_email_list = None
        if users_list:
            users_email_list = []
            for user in users_list:
                users_email_list.append(user["email"])

        return users_email_list

    async def get_site_to_add_roles(self, site_id):
        """
        if site_id provided try to get site, if it is blank get default site
        """
        site = None

        if site_id is None or site_id.strip() == '1' or site_id.strip() == '':
            site = await self.get_default_site()
        else:
            site_obj_id = await get_object_id(site_id.strip())

            if site_obj_id is not None:
                site = await self.db_async.Site.find_one({'_id': site_obj_id})

        return site

    async def insert_bulk_users(self, invite_bulk_users: InviteBulkUsersSchema, invited_by_id: str):
        tz_dt = await get_utc_date_time()
        create_usrs_dict = invite_bulk_users.dict()

        ins_usr_rec_dict_list = []

        for email_id in create_usrs_dict['email_ids']:
            # ins_usr_rec_dict_list.append({'name': '', 'email': email_id, 'created_at': tz_dt, 'updated_at': tz_dt, 'created_by': token['email'],
            #                               'is_active': 1, 'server_role_value': 3, 'is_sso_user': create_usrs_dict['is_sso_user'], 'login_status': False})
            ins_usr_rec_dict_list.append({'name': email_id, 'email': email_id, 'created_at': tz_dt, 'updated_at': tz_dt, 'invited_by_id': invited_by_id,
                                          'status': UserStatus.INVITED, 'server_role_value': await self.get_role_value_by_id(invite_bulk_users.server_role_id),
                                          'is_sso_user': invite_bulk_users.is_sso_user, 'login_status': False, 'last_invite_sent_at': int(time.time())})

        await self.db_async.users.insert_many(ins_usr_rec_dict_list)

        return create_usrs_dict['email_ids']

    async def get_default_site(self):
        site = await self.db_async.Site.find_one({'name': 'DefaultSite'})
        if not site:
            site_created_resp = await self.db_async.Site.insert_one({'name': 'DefaultSite', 'organization_id': '1001', 'description': 'DefaultSite Desc',
                                                                   'storage_destination': 'None', 'date_created': datetime.now(timezone.utc).strftime('%Y-%m-%d')})
            site = await self.db_async.Site.find_one({'name': 'DefaultSite'})
        return site

    async def update_user_by_admin(self, updt_user_by_admin_sch: UpdateUserByAdminSchema, updated_by_id: str, updated_by_name: str) -> GenericResponse:
        dt_tz = await get_utc_date_time()

        role_id = updt_user_by_admin_sch.server_role_id 
        server_role_dict = None
        if role_id != None:
            server_role =  await self.get_role_by_id(updt_user_by_admin_sch.server_role_id)
            user = await self.get_user_by_id(updt_user_by_admin_sch.user_id)
            if user['server_role_value'] != server_role['role_value']:
                server_role_dict = {'server_role_value':server_role['role_value'], 
                                    'role_updated_by_id':updated_by_id,
                                    'role_updated_by_name': updated_by_name,
                                    'role_updated_at': dt_tz,
                                    'server_role': server_role['role_name'] }

        user_updt_dict = {'name': updt_user_by_admin_sch.name, 'email': updt_user_by_admin_sch.email,
                          'status': updt_user_by_admin_sch.status, 'updated_at': dt_tz}

        if server_role_dict != None:
            user_updt_dict.update(server_role_dict)

        if updt_user_by_admin_sch.is_sso_user:
            user_updt_dict['is_sso_user'] = updt_user_by_admin_sch.is_sso_user

        update_resp = await self.db_async.users.update_one({'_id': ObjectId(updt_user_by_admin_sch.user_id)},
                                                {'$set': user_updt_dict})

        if update_resp and  update_resp.matched_count > 0 and update_resp.modified_count > 0:
            return GenericResponse(status=True, message='Successfully updated the User')
        else:
            return GenericResponse(status=False, message='Failed to update user, due to no changes requested')

    async def get_server_roles(self) -> list[dict]:
        server_roles_cur = self.db_async.roles.find({})
        server_roles_list = await mongo_list_json_async(server_roles_cur)
        return server_roles_list

    async def get_projects_count_with_role(self, user_id, proj_role_id) -> int:
        count = await self.db_async.users_projects_mappings.count_documents({"user_id": user_id, "role_id":proj_role_id})
        return count

    async def is_default_server_admin(self, email) -> bool:
        count = await self.db_async.users.count_documents({'email':email, 'default_server_admin': True, "status": {"$ne": UserStatus.INACTIVE}})
        return count > 0

    async def update_last_activity_time(self, email: str, is_logout: bool) -> int:
        last_updt_time = int(time.time())
        await self.db_async.users.update_one({"email": email}, {"$set": {"last_activity_at": last_updt_time}})
        return last_updt_time

def get_rand_pwd():
    length = 13
    chars = string.ascii_letters + string.digits + '!@#$%^&*()'
    random.seed = (os.urandom(1024))
    rand_pwd = ''.join(random.choice(chars) for i in range(length))
    return rand_pwd

def encrypt_password(pwd):
    import bcrypt

    bytePwd = pwd.encode('utf-8')
    pwd_hash = bcrypt.hashpw(bytePwd, bcrypt.gensalt())
    return pwd_hash
