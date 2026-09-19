import asyncio
import logging
import re
from datetime import datetime, timezone, timedelta
import time
from typing import List, Tuple, Optional, Union
import msal
import bcrypt
from google.auth.transport import requests
from google.oauth2 import id_token
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import parse_obj_as
from pymongo import MongoClient
from pytz import UTC
import threading
import requests as gen_requests
import base64
from fastapi.responses import JSONResponse
from app.core.services.cloud_utils.azure_secrets import AzureSecretManager

from app.config.env_vars import environment
from app.core.services.azure_utils.token_utils import AzureTokenUtilsService
from app.core.services.email_utils.email_utils import send_simple_mail
from app.core.services.jwt_token_utils.jwt_token_utils import getAccessToken, getRefreshToken, decodeJWT, \
    getMailVerificationToken, decode_jwt_ignore_expiry
from app.services.admin.authentication.dao import AuthenticationDao, get_utc_date_time
from app.services.admin.authentication.schemas import (
    SuperSetData,
    User,
    LoginResponse,
    UserLoginSchema,
    InviteUserSchema,
    RegisterUserSchema,
    TokensSchema,
    SiteRoleSchema,
    ChangePasswordSchema,
    ChangeUserNamesSchema,
    SSOLoginSchema,
    AzureTokensSchema,
    GcpTokensSchema,
    InviteBulkUsersSchema,
    InviteUsersResponse,
    RoleEnum,
    SSOEnum,
    UserStatus,
    ActivateUserSchema,
    GenericResponse,
    UpdateUserByAdminSchema,
    UserIdRoleValueMap,
    RefreshTokenSchema,
    ServerRole,
    PasswordResetResponse,
    UserEmail,
    ActiveDirectoryUsers,
    ADUser,
    ServerBasedRoleNames,
    DeleteUserResponse,
)
from app.services.admin.authentication.utils import get_object_id_sync, http_err_unauthorized, get_object_id, http_err_conflict
from app.services.access_controls.roles.schemas import SystemGeneratedProjectRoles
from app.services.access_controls.roles.utils import get_system_generated_role_features_map
from prometheus_client import Counter
from app.core.services.cloud_utils.utils import get_secret_manager

HEXAIND_FE_URL = None
ACTIVATE_AC_FR_END_URL = None
RESET_PWD_FR_END_URL = None
active_users=Counter('active_user','Count of unique active users')
def get_hexaind_front_end_url():
    global HEXAIND_FE_URL
    if HEXAIND_FE_URL is None:
        if environment.hexaind_front_end_url != None and len(environment.hexaind_front_end_url.strip()) > 0:
            HEXAIND_FE_URL = environment.hexaind_front_end_url
        else:
            HEXAIND_FE_URL = 'http://localhost:4200'
    return HEXAIND_FE_URL

def get_activate_ac_url():
    global ACTIVATE_AC_FR_END_URL
    if ACTIVATE_AC_FR_END_URL is None:
        front_end_url = get_hexaind_front_end_url()
        ACTIVATE_AC_FR_END_URL = front_end_url + '/users/register-account'

    return ACTIVATE_AC_FR_END_URL

def get_reset_pwd_url():
    global RESET_PWD_FR_END_URL
    if RESET_PWD_FR_END_URL is None:
        front_end_url = get_hexaind_front_end_url()
        RESET_PWD_FR_END_URL = front_end_url + '/users/password/edit'

    return RESET_PWD_FR_END_URL


logger = logging.getLogger(__package__)
active_user_ids = set()    

class AuthenticationService:

    def __init__(self, db_sync_client: Optional[MongoClient] = None, db_async_client: Optional[AsyncIOMotorClient] = None) -> None:
        self.authentication_dao = AuthenticationDao(db_sync_client=db_sync_client, db_async_client=db_async_client)
        logger.info("inside authentication service")

    async def get_active_user(self, email: str):
        return await self.authentication_dao.get_active_user(email=email)
    
    def get_user_sync(self, user_id: str):
        return self.authentication_dao.get_user_by_id_sync(user_id)
    
    async def update_user_async(self, user_id: str, user_data: SuperSetData):
        return self.authentication_dao.update_user_record(user_id, user_data)
    
    async def delete_user_with_id(self, user_id: str):
        result = self.authentication_dao.delete_user_record(user_id=user_id)
        if not result:
            return DeleteUserResponse(status=False, msg=f"Unable to delete user {user_id}", user_id=user_id)
        
        return DeleteUserResponse(status=True, msg=f"User {user_id} deleted successfully.", user_id=user_id)

    async def validate_user_and_return_token(self, data: UserLoginSchema) -> Union[JSONResponse, LoginResponse]:
        logger.info("validate_user_and_return_token")
        user = await self.authentication_dao.get_active_user(data.email)

        if not user:
            logger.exception("User not found")
            return http_err_unauthorized('User not found')

        if user['is_sso_user']:
            return http_err_unauthorized(f'Invalid Login attempt. SSO Login only for the user with email:{data.email}')

        if 'password' in user:
            is_pwd_matched = await self.check_pwd(data.password, user['password'])
            if is_pwd_matched is False:
                await self.authentication_dao.handle_failed_login(user)
                logger.warning("invalid id or password.")
                return http_err_unauthorized('Invalid id or password')

            elif 'account_locked_until' in user and user['account_locked_until']  != None and UTC.localize(user['account_locked_until']) > datetime.now(timezone.utc):
                logger.warning('Account Locked. Try after some time.')
                return http_err_unauthorized('Account Locked. Try after some time.')

            else:
                await self.authentication_dao.handle_success_login(user['_id'])
                last_updt_time = await self.authentication_dao.update_last_activity_time(user['email'], False)
                user['last_activity_at'] = last_updt_time
                return await self.return_login_response(user)
        else:
            logger.warning('User registration not completed')
            return http_err_unauthorized('User registration not completed')

    async def logout_user(self, email: str) -> Union[JSONResponse, str]:
        logger.info(f"Attempting to logout the user {email}")
        resp_str = await self.authentication_dao.mark_logout(email)
        await self.update_last_activity_time(email, is_logout=True)
        logger.info(f"User {email} logged out")
        return resp_str
    
    async def force_logout_user(self, users: List[User]) -> Union[JSONResponse, str]:
        logger.info("Validating users to force logout")
        current_time = int(time.time())

        # Filter users who need to be logged out
        users_to_logout = [
            user
            for user in users
            if current_time - user.last_activity_at
            >= environment.user_logout_after_secs
            and user.login_status
        ]

        if not users_to_logout:
            return "User is active. Not logged out."

        # Logout all filtered users concurrently
        await asyncio.gather(
            *(self.logout_user(user.email) for user in users_to_logout)
        )

        return JSONResponse(content={"message": "Users logged out successfully."})

    async def deactivate_user(self, email: str, token: str) -> Union[JSONResponse, str]:
        logger.info("deactivate user")
        decoded_token = decodeJWT(token)
        if decoded_token == None or int(decoded_token['server_role_value']) & 3 == 0:
            logger.exception("Don't have permission to delete user")
            return http_err_unauthorized("Don't have permission to delete user")

        resp_str = await self.authentication_dao.deactivate_user(email)
        return resp_str

    async def activate_user_by_admin(self, email: str, token: str) -> Union[JSONResponse, str]:
        logger.info(f"Activate user:{email}")
        decoded_token = decodeJWT(token)
        if decoded_token is None:
            raise ValueError("Not authorized to activate the user")
        admin_user = await self.authentication_dao.get_user(decoded_token['email'])
        if admin_user is None or admin_user['status'] != UserStatus.ACTIVE or admin_user['server_role_value'] != 1:
            raise ValueError("Not authorized to activate the user")
        
        resp_str = await self.authentication_dao.activate_user_by_admin(email)
        return resp_str

    async def check_pwd(self, password, pwd_hash):
        logger.info("check pwd")
        password = password.encode('utf-8')
        if type(pwd_hash) == dict and pwd_hash.get("$binary", {}).get("base64", None) != None:
            base64_data = pwd_hash["$binary"]["base64"]
            pwd_hash = base64.b64decode(base64_data)

        return bcrypt.checkpw(password, pwd_hash)

    async def invite_users(self, invite_users_list: List[InviteUserSchema], invited_by_id: str) -> Union[JSONResponse, InviteUsersResponse]:

        emails_list = []
        for inv_user in invite_users_list:
            emails_list.append(inv_user.email)

        existing_emails = await self.authentication_dao.get_existing_users_with_mail_ids(emails_list)

        if existing_emails is not None and len(existing_emails) > 0:
            return http_err_conflict(f"Users already exists with emails {existing_emails}")

        dupl_list = self.get_duplicates(emails_list)
        if len(dupl_list) > 0:
             return http_err_conflict(f"Duplicate emails in the provided users list {dupl_list}")

        await self.authentication_dao.insert_users(invite_users_list, invited_by_id)

        sent_list = []
        failed_list = []
        for inv_user in invite_users_list:
            is_mail_sent = await self.send_inv_mail(inv_user.email, inv_user.is_sso_user)
            logger.info("sent password creation email.")

            if is_mail_sent is False:
                failed_list.append(inv_user.email)
            else:
                sent_list.append(inv_user.email)

        resp_msg = InviteUsersResponse(message='Successfully added users', inv_email_sent_to=sent_list, inv_email_failed_to=failed_list)

        return resp_msg

    def get_duplicates(self, items_list):
        duplicates = []
        unique = set()
        for item in items_list:
            if item in unique:
                duplicates.append(item)
            else:
                unique.add(item)
        return duplicates

    async def send_inv_mail(self, email: str, is_sso_user: bool):
        email_token = getMailVerificationToken(email)
        is_mail_sent = False
        if is_sso_user:
            is_mail_sent = send_sso_inv_mail(email, email_token)
        else:
            is_mail_sent = send_pwd_creation_mail(email, email_token)

        await self.authentication_dao.insert_mail_verification_token(email, email_token)

        return is_mail_sent

    async def is_already_registered(self, email: str) -> Union[JSONResponse, bool]:
        logger.info("inside is already registered.")
        user = await self.authentication_dao.get_user(email)
        if user is None:
            logger.warning('There is no user available with the given email id')
            return http_err_unauthorized('There is no user available with the given email id')

        if user['status'] == UserStatus.INVITED:
            return False
        else:
            return True

    async def register_user(self, register_user_sch: RegisterUserSchema) -> Union[JSONResponse, GenericResponse]:
        logger.info("inside is is registered user")
        if len(register_user_sch.first_name.strip()) == 0 or len(register_user_sch.last_name .strip()) == 0:
            logger.warning('User first name and/ or last name are blank')
            return http_err_unauthorized('User first name and/ or last name are blank')
        return await self.change_pwd_fname_lname(register_user_sch)

    async def change_password_using_email_token(self, register_user_sch: RegisterUserSchema) -> Union[JSONResponse, GenericResponse]:
        return await self.change_pwd_fname_lname(register_user_sch)

    async def activate_user(self, activate_user_schema: ActivateUserSchema):
        user = await self.authentication_dao.get_user(activate_user_schema.email)
        if user is None:
            return http_err_unauthorized('User not found')

        if user['status'] == UserStatus.ACTIVE:
            return GenericResponse(status= True, message=f"User status already {UserStatus.ACTIVE}")

        is_valid_token = is_valid_email_token(activate_user_schema.email, activate_user_schema.email_verification_token)

        if not is_valid_token:
            return http_err_unauthorized('Invalid Email token or email id')

        token_doc = await self.authentication_dao.get_mail_token(activate_user_schema.email_verification_token)

        if token_doc is None:
            return http_err_unauthorized('Token already utilized. Please try with fresh token')

        is_activated = await self.authentication_dao.activate_user(activate_user_schema.email, activate_user_schema.email_verification_token)
        if is_activated is False:
            return GenericResponse(status= False, message=f"Failed to Activate due to DB connection or some other issue")

        return GenericResponse(status= True, message=f"User status changed to {UserStatus.ACTIVE}")

    async def change_pwd_fname_lname(self, register_user_sch: RegisterUserSchema):
        register_user_sch = register_user_sch.dict()
        email = register_user_sch['email']
        password = register_user_sch['password']
        conf_password = register_user_sch['conf_password']
        email_verification_token = register_user_sch['email_verification_token']
        user = user = await self.authentication_dao.get_user(email)
        if user is None:
            logger.error('User not found')
            return http_err_unauthorized('User not found')

        if password != conf_password:
            logger.error("Password and Confirm Password didn't Match")
            return http_err_unauthorized("Password and Confirm Password didn't Match")

        if not self.is_strong_password(password):
            logger.error("Password is not strong, password should be at least 12 chars, contain at least a uppercase, lowercase, digit and a special char.")
            return http_err_unauthorized("Password is not strong, password should be at least 12 chars, contain at least a uppercase, lowercase, digit and a special char.")


        is_valid_token = is_valid_email_token(email, email_verification_token)

        if is_valid_token is True:
            token_doc = await self.authentication_dao.get_mail_token(email_verification_token)

            if token_doc is None:
                logger.error('Token already utilized. Please try with fresh token')
                return http_err_unauthorized('Token already utilized. Please try with fresh token')

            is_updated = await self.authentication_dao.update_pwd_fname_lname(register_user_sch, user['name'])
            if is_updated is False:
                logger.error('Failed to create/ update password')
                return http_err_unauthorized('Failed to create/ update password')

            await self.authentication_dao.delete_mail_token(email_verification_token)
            return GenericResponse(status=True, message="Account updated successfully. Please login with updated credentials.")
        else:
            logger.exception('Invalid Email token or email id')
            return http_err_unauthorized('Invalid Email token or email id')

    def is_strong_password(self, password):
        # Check if the password contains at least one lowercase letter
        if not re.search(r'[a-z]', password):
            return False

        # Check if the password contains at least one uppercase letter
        if not re.search(r'[A-Z]', password):
            return False

        # Check if the password contains at least one digit
        if not re.search(r'\d', password):
            return False

        # Check if the password contains at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False

        if len(password) < 12:
            return False

        return True

    async def get_paginated_users_list(self, search_term: str = '', page_number: int = 1, page_limit: int = 100,
                                       custom_query=None, fetch_role_details:bool=False) -> Tuple[List[User], int]:
        return await self.authentication_dao.get_paginated_users_list_async(search_term,page_number,page_limit,
                                                                            custom_query,fetch_role_details)

    async def get_users_list(self) -> List[User]:
        users = await self.authentication_dao.get_all_users_list()
        users = parse_obj_as(List[User], users)
        if environment.show_all_ad_users and environment.sso_login_allowed:
            ADSyncService.sync_users_with_azure_ad(users)
        return users

    async def get_user_details_with_roles(self, user_id, token):
        token = decodeJWT(token)
        if token['user_id'] == user_id or int(token['server_role_value']) & 3:
            user = await self.authentication_dao.get_user_with_roles(user_id)
            return User(**user)
        else:
            logger.warning('Only Organization Admin can get other users details')
            return http_err_unauthorized('Only Organization Admin can get other users details')
    
    async def get_user_with_id(self,user_id):
        user = await self.authentication_dao.get_user_by_id(user_id)
        if user is None:
            raise KeyError(f"User {user_id} not found")
        return User(**user)

    
    async def get_user_by_token_or_id(self, token, user_id = None) -> Union[JSONResponse, User]:
        token = decodeJWT(token)
        if token is None:
            logger.warning('Not authorized to get user data')
            return http_err_unauthorized('Not authorized to get user data')

        if user_id is None:
            user_id = token['user_id']

        uid_obj_id = await get_object_id(user_id)
        if uid_obj_id is None:
                logger.error('Invalid user id')
                return http_err_unauthorized('Invalid user id')
        user = await self.authentication_dao.get_user_by_id(user_id)
        if user == None:
            return http_err_unauthorized('No user Exists with provided user id')

        if user_id not in active_user_ids:
            active_user_ids.add(user_id)
            active_users.inc()
            logger.info(f"Active user count incremented: {active_users._value.get()}")
        return User(**user)
    
    def get_user_by_token_or_id_sync(self, token, user_id = None) -> Union[JSONResponse, User]:
        token = decodeJWT(token)
        if token is None:
            logger.warning('Not authorized to get user data')
            return http_err_unauthorized('Not authorized to get user data')

        if user_id is None:
            user_id = token['user_id']

        uid_obj_id = get_object_id_sync(user_id)
        if uid_obj_id is None:
            logger.error('Invalid user id')
            return http_err_unauthorized('Invalid user id')

        user = self.authentication_dao.get_user_by_id_sync(user_id)
        if user == None:
             return http_err_unauthorized('User does not exists with provide user id')
        return user

    async def get_user_access_roles(self, user_id):
        access_roles = await self.authentication_dao.get_user_access_roles(user_id)
        return parse_obj_as(List[SiteRoleSchema], access_roles)

    async def change_password_from_profile(self, change_pwd_schema: ChangePasswordSchema, token):
        change_pwd_schema_dict = change_pwd_schema.dict()
        decoded_token = decodeJWT(token)
        if decoded_token is None:
            return http_err_conflict("Invalid User")
        
        if decoded_token['email'] != change_pwd_schema_dict['email']:
            logger.error("Invalid attempt. You are trying to change other's password")
            return http_err_conflict("Invalid attempt. You are trying to change other's password")

        if change_pwd_schema_dict['password'] != change_pwd_schema_dict['conf_password']:
            logger.warning("Password and confirm password didn't match")
            return http_err_conflict("Password and confirm password didn't match")

        if not self.is_strong_password(change_pwd_schema_dict['password']):
            logger.error("Password is not strong, password should be at least 12 chars, contain at least a uppercase, lowercase, digit and a special char.")
            return http_err_conflict("Password is not strong, password should be at least 12 chars, contain at least a uppercase, lowercase, digit and a special char.")

        change_pwd_user = await self.authentication_dao.get_user(change_pwd_schema_dict['email'])
        if change_pwd_user is None:
            logger.error('User Does not exists')
            return http_err_conflict('User Does not exists')

        if change_pwd_user['status'] == UserStatus.INACTIVE:
            return http_err_conflict('User is not active. Please activate user then attempt after activate and login')

        if await self.check_pwd(change_pwd_schema_dict['old_password'], change_pwd_user['password']) is False:
            logger.error('Invalid credentials')
            return http_err_conflict('Invalid credentials')

        await self.authentication_dao.update_password(change_pwd_schema_dict['email'], change_pwd_schema_dict['password'])

        send_pwd_creation_mail(change_pwd_schema_dict['email'], '', is_reset=True)

        return True

    async def get_refreshed_tokens(self, refresh_token_schema: RefreshTokenSchema) -> Union[JSONResponse, TokensSchema]:
        try:
            logger.info("get refreshed tokens")
            refresh_token_schema_dict = refresh_token_schema.dict()
            refresh_schema_email = refresh_token_schema_dict['email']
            acc_tok_in = refresh_token_schema_dict['access_token']
            refresh_tok_in = refresh_token_schema_dict['refresh_token']

            acc_tok_in = decode_jwt_ignore_expiry(acc_tok_in)
            if acc_tok_in is None or acc_tok_in['email'] != refresh_schema_email:
                return http_err_unauthorized('Invalid email to generate fresh tokens')

            decoded_refresh_token = is_valid_refresh_token(refresh_tok_in)
            #body_token = decodeJWT(body_token)

            if decoded_refresh_token and decoded_refresh_token['email'] == refresh_schema_email:
                access_token = getAccessToken(refresh_schema_email, acc_tok_in['server_role_value'], acc_tok_in['user_id'])
                refresh_token = getRefreshToken(refresh_schema_email)

                if access_token == None or refresh_token == None:
                    http_err_unauthorized('Invalid email to generate fresh tokens')

                return TokensSchema(access_token=access_token, refresh_token=refresh_token)
            else:
                logger.error('Invalid Refresh Token presented')
                return http_err_unauthorized('Invalid Refresh Token presented')
        except Exception as e:
            logger.exception('Unknown Issue while tryig to fetch Refreshed Tokens')
            return http_err_unauthorized('Unknown Issue while tryig to fetch Refreshed Tokens')

    async def reset_password(self, email, reason, token=None) -> Union[JSONResponse, PasswordResetResponse]:
        logger.info("inside reset password.")
        # if token is not none, it is initiated by admin for another user's password reset
        # if token is none, it is initiated by user himself from login page--> forgot/ reset password section
        try:
            reset_init_by = email
            if token is not None:
                decoded_token = decodeJWT(token)

                if decoded_token is None or int(decoded_token['server_role_value']) & 1 == 0:
                    logger.error("You don't have Permissions to reset password.")
                    return http_err_unauthorized("You don't have Permissions to reset password.")
                reset_init_by = decoded_token['email']

            reset_user = await self.authentication_dao.get_user(email)

            if reset_user is None:
                logger.error('There is no user exists with given email id.')
                return http_err_unauthorized('There is no user exists with given email id.')

            if reset_user.get('is_sso_user', False):
                return http_err_unauthorized('Cannot reset password for SSO user')

            if token is None and reset_user['status'] == UserStatus.INACTIVE:
                logger.error('Account is not active. Please get it activated or password reset by Admin.')
                return http_err_unauthorized('Account is not active. Please get it activated or password reset by Admin.')

            logger.info("activate user apply rand password.")
            new_rand_pwd = await self.authentication_dao.activate_user_apply_rand_pwd(email)
            new_password = ""
            if token is not None:
                new_password = f"{new_rand_pwd}"

            email_token = getMailVerificationToken(reset_user['email'])
            await self.authentication_dao.insert_mail_verification_token(reset_user['email'], email_token)
            await self.authentication_dao.log_password_change_details(email, reset_init_by, reason)
            is_mail_sent = send_pwd_creation_mail(email, email_token, is_reset=True)
            logger.info('Password reset Email sent. Please click on link in the email sent to create password')
            email_sent_info = 'Password reset Email sent. Please click on link in the email sent to create password'
            if is_mail_sent is False:
                logger.error('But failed to send mail.')
                email_sent_info = 'But failed to send mail.'

            # Added new password info for Server admin. This is work around for email sending issues.
            # TODO: Remove adding pwd in Future.
            #return f"Password Reset Done. {email_sent_info}. {new_password}"
            return PasswordResetResponse(status = True, message=f"Password Reset Done. {email_sent_info}", new_pwd=new_password)
        except Exception as e:
            logger.exception(f"Unknown Issue while tryig to reset password. Error:{e}")
            return http_err_unauthorized(f"Unknown Issue while tryig to reset password. Error:{e}")

    async def toggle_user_active_status(self, email, token):
        logger.info("toggle user active status.")
        token = decodeJWT(token)
        if int(token['server_role_value']) & 3 == 0:
            return False

        return await self.authentication_dao.toggle_user_active_status(email)

    # TODO: remove if not needed
    async def update_user_roles(self, changes: List[UserIdRoleValueMap], user_id: str):
        # TODO: optimize this without loop if possible(post 3-31)
        users = [User(**await self.authentication_dao.get_user_by_id(change.user_id)) for change in changes]
        if len(users) != len(changes):
            raise ValueError(f"Fetched users count not matching with changes count {len(users)}")
        for i, user in enumerate(users):
            logger.info(f"{changes[i]}")
            user.server_role_value = changes[i].server_role_value
            user.server_role = changes[i].server_role
            user.role_updated_at = datetime.now(timezone.utc)
            user.role_updated_by_id = user_id
            logger.info(f"updating userid {user.id} to server_role {user.server_role} by {user_id}")

        return await self.authentication_dao.update_users(users)

    async def update_user_names(self, changeUserNameSchema: ChangeUserNamesSchema, token: str):
        logger.info("update user names")
        user = await self.authentication_dao.get_active_user(changeUserNameSchema.email)
        if user is None:
            logger.error('User does not exists')
            return http_err_unauthorized('User does not exists')

        decoded_token = decodeJWT(token)
        if decoded_token is None:
            return http_err_unauthorized('Authentication failed')

        if decoded_token['email'] != changeUserNameSchema.email and int(decoded_token['server_role_value']) & 3 == 0:
            logger.error('Authentication failed. You are not allowed to change the name(s).')
            return http_err_unauthorized('Authentication failed. You are not allowed to change the name(s).')

        if len(changeUserNameSchema.name.strip()) == 0 and len(changeUserNameSchema.first_name.strip()) == 0 and len(changeUserNameSchema.name.strip()) == 0:
            logger.error('Could not get value for any part of name to update')
            return http_err_unauthorized('Could not get value for any part of name to update')

        return await self.authentication_dao.update_user_names(changeUserNameSchema)

    async def validate_sso_token_and_return_jwt_token(self, sso_tokens: SSOLoginSchema) -> LoginResponse:
        sso_tok_det = None
        if sso_tokens.root.type == SSOEnum.AZURE:
            sso_tok_det = await self.__validate_azure_token_and_return_user_det(sso_tokens.root)
        elif sso_tokens.root.type == SSOEnum.GCP:
            sso_tok_det  = await self.__validate_gcp_token_and_return_user_det(sso_tokens.root)

        if not sso_tok_det or len(sso_tok_det.email.strip()) == 0:
            logger.error(f'Unable to get details from {sso_tokens.root.type} SSO login')
            return http_err_unauthorized(f'Unable to get details from {sso_tokens.root.type} SSO login')

        user = await self.authentication_dao.get_user(sso_tok_det.email)
        if user and user['is_sso_user'] == False:
            return http_err_unauthorized(f'Email {sso_tok_det.email} login type is not SSO, Please login using other methods like form login.')
        
        await self.authentication_dao.update_user_names(sso_tok_det)

        return await self.__authenticate_sso_user_and_send_login_response(sso_tok_det.email)

    async def __validate_azure_token_and_return_user_det(self, azure_tokens: AzureTokensSchema) -> ChangeUserNamesSchema:
        try:
            sso_tok_det = None
            decoded_token = AzureTokenUtilsService.decode_azure_access_token(azure_tokens.access_token)
            email = None
            name = ''
            last_name = ''
            first_name = ''
            if decoded_token:
                logger.info("Azure Access Token Decoded")
                email = decoded_token['unique_name']
                if 'name' in decoded_token:
                    name = decoded_token['name']
                if 'given_name' in decoded_token:
                    first_name = decoded_token['given_name']
                if 'family_name' in decoded_token:
                    last_name = decoded_token['family_name']
            else:
                decoded_token = AzureTokenUtilsService.decode_azure_id_token(azure_tokens.raw_token)
                if not decoded_token:
                    raise Exception("Failed to Decode Access and Raw Token. Please check the configurations")
                
                logger.info("Azure Access Token Decoding failed, but Raw Token Decoded")
                email = decoded_token['preferred_username']
                name = decoded_token['name']
                name_parts = name.split(' ')
                if len(name_parts) > 1:
                    first_name = ' '.join(name_parts[:-1])
                    last_name = name_parts[-1]
                else:
                    first_name = name
                    last_name = ''
            sso_tok_det = ChangeUserNamesSchema(email=email, name=name, first_name=first_name, last_name=last_name)
            return sso_tok_det
        except Exception:
            logger.exception("Failed to decode Azure Tokens.")
            return None

    async def __validate_gcp_token_and_return_user_det(self, gcp_token_sch: GcpTokensSchema) -> ChangeUserNamesSchema:
        try:
            id_info = id_token.verify_oauth2_token(gcp_token_sch.gcp_id_token, requests.Request(), environment.gcp_client_id)
            family_name = ''
            if 'family_name' in id_info:
                family_name = id_info['family_name']
            sso_tok_det = ChangeUserNamesSchema(email= id_info['email'], name= id_info['name'], first_name=id_info['given_name'], last_name= family_name)
            return sso_tok_det #id_info.get('email')
        except Exception:
            gcp_client_id_error = ''
            if environment.gcp_client_id is None or len(environment.gcp_client_id.strip()) == 0:
                gcp_client_id_error = 'GCP Client ID not configured. Please check the env_vars & .env'
            logger.exception(f"Failed to decode GCP Token. {gcp_client_id_error}")
            return None

    async def __authenticate_sso_user_and_send_login_response(self, email: str) -> LoginResponse:
        email = email.strip()
        user = await self.authentication_dao.get_user_by_email(email)

        if user is None:
            logger.error(f'Could not find any user with email:{email}')
            return http_err_unauthorized(f'Could not find any user with email:{email}')

        if not user['status'] or user['status'] == UserStatus.INACTIVE:
            logger.error(f'User is not active with email:{email}')
            return http_err_unauthorized('User is not active with email:{email}')

        return await self.return_login_response(user)

    async def return_login_response(self, user):
        user.pop('password', None)
        user.pop('plainpassword', None)
        acc_tok = getAccessToken(user['email'], user['server_role_value'], user['_id'])
        refr_tok = getRefreshToken(user['email'])
        #await self.db_async.users.update_one({'email': email}, {'$set': {'login_status': True, 'last_login_date': utc_time}})
        utc_time = await get_utc_date_time()
        user['login_status'] = True
        user['last_login_date'] = utc_time
        await self.authentication_dao.log_login_details(user)
        login_resp = {'user_data': user, 'access_token': acc_tok, 'refresh_token': refr_tok}
        return LoginResponse(**login_resp)

    async def update_last_activity_time(self, email: str, is_logout: bool = False):
        await self.authentication_dao.update_last_activity_time(email, is_logout)

    async def invite_bulk_users(self, invite_bulk_usrs_sch: InviteBulkUsersSchema, token: str):
        token = decodeJWT(token)
        if int(token['server_role_value']) & 1 == 0:
            logger.error("Don't have permission to create new users")
            return http_err_unauthorized("Don't have permission to create new users")

        existing_emails = await self.authentication_dao.get_existing_users_with_mail_ids(invite_bulk_usrs_sch.email_ids)

        if existing_emails and len(existing_emails) > 0:
            logger.error(f"Users already exists with emails {existing_emails}")
            return http_err_conflict(f"Users already exists with emails {existing_emails}")

        dupl_list = self.get_duplicates(invite_bulk_usrs_sch.email_ids)
        if len(dupl_list) > 0:
             return http_err_conflict(f"Duplicate emails in the provided users list {dupl_list}")

        ins_users_emails_list = await self.authentication_dao.insert_bulk_users(invite_bulk_usrs_sch, token['user_id'])

        sent_list = []
        failed_list = []
        for email in ins_users_emails_list:
            is_mail_sent = await self.send_inv_mail(email, invite_bulk_usrs_sch.is_sso_user)

            if is_mail_sent is False:
                failed_list.append(email)
            else:
                sent_list.append(email)

        resp_msg = InviteUsersResponse(message='Successfully added users', inv_email_sent_to=sent_list, inv_email_failed_to=failed_list)

        return resp_msg

    async def resend_invitation_mail(self, email:str, invited_by_id: str):
        user = await self.authentication_dao.get_user(email)
        if user is None:
            if environment.sso_login_allowed == False:
                return  http_err_unauthorized(f"Users does not exists with email {email}")
            
            ad_user = ADSyncService.get_user_with_email(email)
            if ad_user is None:
                return  http_err_unauthorized(f"Users does not exists with email {email} even in Active Directory")
            is_sso_user=True
            inv_user_schema = InviteUserSchema(name = ad_user.name, email=ad_user.email, server_role_id=RoleEnum.default_user, is_sso_user=is_sso_user)
            await self.authentication_dao.insert_users([inv_user_schema], invited_by_id)
        else:
            is_sso_user = user['is_sso_user']

        # if user['status'] == UserStatus.INACTIVE:
        #     return  http_err_unauthorized(f"Users is status is:{UserStatus.INACTIVE}, Not allowed to send invitation")
        is_inv_sent = await self.send_inv_mail(email, is_sso_user)
        msg = 'Successfully sent the invitation mail'
        if is_inv_sent == False:
            msg = 'Failed to send the invitation mail'
        return GenericResponse(status=is_inv_sent, message=msg)

    async def update_user_by_admin(self, updt_user_by_admin_sch: UpdateUserByAdminSchema, server_admin_user_id: str):
        user = await self.authentication_dao.get_user_by_id(updt_user_by_admin_sch.user_id)
        if user is None:
            return  http_err_conflict(f"Users does not exists with email {updt_user_by_admin_sch.email}")

        if 'is_sso_user' in user and user['is_sso_user'] and \
            (user['email'] != updt_user_by_admin_sch.email or user['name'] != updt_user_by_admin_sch.name):
            return  http_err_conflict("Change of name or email of SSO user is not is not allowed")

        if not UserStatus.has_member_value(updt_user_by_admin_sch.status):
            return  http_err_conflict(f"Invalid user status {updt_user_by_admin_sch.status}")
        
        admin_user = await self.authentication_dao.get_user_by_id(server_admin_user_id)
        if admin_user is None:
            return  http_err_unauthorized("Server Admin User not found in the DB. Please re-login & try")
        
        if updt_user_by_admin_sch.server_role_id == RoleEnum.default_user:
            if await self.is_project_admin_to_any_project(updt_user_by_admin_sch.user_id):
                return http_err_conflict("User already project admin for one or more projects. Revert to full/ limited & try again")

        need_to_send_inv_mail = False
         
        if updt_user_by_admin_sch.is_sso_user != None:
            if updt_user_by_admin_sch.is_sso_user == False and 'password' not in user:
                need_to_send_inv_mail = True
        elif user['email'] != updt_user_by_admin_sch.email:
            need_to_send_inv_mail = True

        update_user_resp = await self.authentication_dao.update_user_by_admin(updt_user_by_admin_sch, admin_user['_id'], admin_user['name'])

        if update_user_resp.status  and need_to_send_inv_mail:
            is_mail_sent = await self.send_inv_mail(updt_user_by_admin_sch.email, updt_user_by_admin_sch.is_sso_user)
            email_sent_resp = "Email too sent as is_sso_user / email changed."
            if not is_mail_sent:
                email_sent_resp = 'is_sso_user / email changed, need to send invitation mail, but failed.'
            update_user_resp.message = update_user_resp.message + '.' + email_sent_resp

        return update_user_resp

    async def is_project_admin_to_any_project(self, user_id: str) -> bool:
        project_admin_roles_features_map = get_system_generated_role_features_map(SystemGeneratedProjectRoles.PROJECT_ADMINISTRATOR)
        count =  await self.authentication_dao.get_projects_count_with_role(user_id, project_admin_roles_features_map.id)
        return count > 0

    async def is_default_server_admin(self, email: str) -> bool:
        return await self.authentication_dao.is_default_server_admin(email)

    async def get_server_roles(self) -> List[ServerRole]:
        roles_dict = await self.authentication_dao.get_server_roles()
        return  parse_obj_as(List[ServerRole], roles_dict)

class ADSyncService:
    """Service for syncing with Active Directory"""
    
    # Get cloud environment and secret manager
    __secret_manager = AzureSecretManager()
    __env = __secret_manager.env
    
    # Get secrets using cloud-agnostic secret manager
    _client_id = __secret_manager.get_secret('hexaind3app-client-id')
    _client_secret = __secret_manager.get_secret('hexaind3app-client-secret')
    
    # Get Azure-specific settings from environment
    # Note: In future, this could be made provider-agnostic for different directory services
    _tenant_id = __env.azure_tenant_id if hasattr(__env, 'azure_tenant_id') else None
    _azure_sync_interval = __env.azure_users_sync_in_mins if hasattr(__env, 'azure_users_sync_in_mins') else 1
    
    # Azure Graph API endpoints
    _GRAPH_API_ENDPOINT = 'https://graph.microsoft.com/v1.0/users'
    _SCOPE = ['https://graph.microsoft.com/.default']
    
    # Sync state
    _azure_last_sync_time = datetime.now() - timedelta(minutes=_azure_sync_interval)
    _ad_users = ActiveDirectoryUsers(azure_ad_users_list=None, gcp_ad_users_list=None)
    _azure_list_lock = threading.Lock()

    @classmethod
    def fetch_azure_users(cls):
        """
        Note: This method is Azure-specific. In future, we could have different 
        implementations for different directory services.
        """
        if cls.is_time_to_sync_azure() or cls._ad_users.azure_ad_users_list is None:
            with cls._azure_list_lock:
                cls.get_users_from_azure_ad()
            cls._azure_last_sync_time = datetime.now()

    @classmethod
    def get_users_from_azure_ad(cls):
        if not all([cls._tenant_id, cls._client_id, cls._client_secret]):
            logger.warning("Azure AD sync not configured - missing required settings")
            return

        # Connect to AD and retrieve user groups
        app = msal.ConfidentialClientApplication(
            cls._client_id,
            authority=f'https://login.microsoftonline.com/{cls._tenant_id}',
            client_credential=cls._client_secret
        )

        token_response = app.acquire_token_for_client(scopes=cls._SCOPE)
        if 'access_token' in token_response:
            access_token = token_response['access_token']

            # Make a GET request to the Microsoft Graph API
            headers = {
                'Authorization': f'Bearer {access_token}'
            }
            response = gen_requests.get(cls._GRAPH_API_ENDPOINT, headers=headers)

            # Check if the request was successful
            if response.status_code == 200:
                users = response.json().get('value', [])
                azure_ad_users_list = []
                for user in users:
                    if user['mail'] is not None:
                        try:
                            ad_user = ADUser(email=user['mail'], name=user.get("displayName") or "", first_name=user.get("givenName") or "", last_name=user.get("surname") or "")
                            azure_ad_users_list.append(ad_user)
                        except Exception as e:
                            logger.exception("Error while trying to add Azure User to users list")

                cls._ad_users.azure_ad_users_list = azure_ad_users_list

    @classmethod
    def is_time_to_sync_azure(cls): 
        return (datetime.now() - cls._azure_last_sync_time).total_seconds() / 60 >= cls._azure_sync_interval

    @staticmethod
    def sync_users_with_azure_ad(hexaind_users: List[User]): 
        ADSyncService.fetch_azure_users()
        user_emails = []
        for hexaind_user in hexaind_users:
            user_emails.append(hexaind_user.email)
        with ADSyncService._azure_list_lock:
            def_user = ServerBasedRoleNames.DEFAULT_USER
            for azure_user in ADSyncService._ad_users.azure_ad_users_list:
                if  azure_user.email not in user_emails:
                    hexaind_users.append(User(name=azure_user.name, email=azure_user.email,
                                           first_name=azure_user.first_name, last_name=azure_user.last_name,
                                           invited_by_id="", invited_by="", status=UserStatus.NOT_INVITED,
                                           server_role_value=def_user.get_server_role_value(), 
                                           is_sso_user=True, server_role = def_user.value,
                                           server_role_id=def_user.get_server_role_id()))

    @staticmethod
    def get_user_with_email(email: UserEmail) -> Optional[ADUser]:
        ADSyncService.fetch_azure_users()

        if ADSyncService._ad_users.azure_ad_users_list is None or len(ADSyncService._ad_users.azure_ad_users_list) == 0:
            return None
        
        for ad_user in ADSyncService._ad_users.azure_ad_users_list:
            if ad_user.email == email:
                return ad_user
        
        return None

def is_valid_email_token(email: str, token: str):
    try:
        decoded_token = decodeJWT(token)
        if decoded_token is not None and email == decoded_token['email'] and decoded_token['type'] == 'mail_verification':
            return True
        else:
            return False

    except Exception as e:
        logger.exception("Failed to decode email token")
        return False

def is_valid_refresh_token(token):
    decoded_token = decodeJWT(token)
    if decoded_token and decoded_token['type'] == 'refresh_token':
        return decoded_token
    else:
        return None

def send_pwd_creation_mail(email, email_token, is_reset=False):
    try:
        mail_list = [email]
        sender = 'Databrick Technologies'
        link = get_activate_ac_url() + '?email=' + email + '&email_verification_token=' + email_token + "&user_type=FORM"
        pwd_set_reason = ' Join Databrick HEXAIND Platform'
        mail_sub = 'Invitation to Databrick HEXAIND'
        btn_caption = 'Accept Invite'
        if is_reset is True:
            link = get_reset_pwd_url() + '?email=' + email + '&email_verification_token=' + email_token
            pwd_set_reason = 'Reset password request of Databrick HEXAIND Platform'
            mail_sub = 'Password reset link for HEXAIND platform'
            btn_caption = 'Click to Reset'
        if len(email_token.strip()) == 0:
            link = ''
            pwd_set_reason = 'informing you as your password is changed on Databrick HEXAIND Platform. Please contact Admin if it is not done by you'

        html = get_inv_mail_body(sender, link, pwd_set_reason, btn_caption)
        is_mail_sent = send_simple_mail(mail_list, html_content=html, mail_subject=mail_sub, from_mail_id=environment.invite_from_email)
        return is_mail_sent
    except Exception as e:
        logger.exception("Faild to send Welcome / PW reset mail")
        return False

def send_sso_inv_mail(email, email_token):
    try:
        mail_list = [email]
        sender = 'Databrick Technologies'
        link = get_activate_ac_url() + '?email=' + email + '&email_verification_token=' + email_token+ "&user_type=SSO"
        pwd_set_reason = ' Join Databrick HEXAIND Platform'
        mail_sub = 'Invitation to Databrick HEXAIND'
        btn_caption = 'Accept Invite'
        html = get_inv_mail_body(sender, link, pwd_set_reason, btn_caption)
        is_mail_sent = send_simple_mail(mail_list, html_content=html, mail_subject=mail_sub,from_mail_id=environment.invite_from_email)
        return is_mail_sent
    except Exception as e:
        logger.exception("Failed to send SSO invitation mail")
        return False


def get_inv_mail_body(sender, inv_link, email_reason, btn_caption='Accept Invite'):
    logger.info("get invitation mail body.")
    mail_link = f""
    if len(inv_link) > 0:
        mail_link = f"""<div style="padding-bottom: 40px"><a href='{inv_link}' style="display: inline-block; border: 3px solid #0e757b; color: #0e757b; font-weight: bold; text-decoration: none; font-size: 20px; padding: 15px 30px;">{btn_caption}</a></div>"""

    html = f"""
      <!DOCTYPE html>
                <html>
                  <head>
                    <meta http-equiv="Content Type" content="text/html; charset=UTF-8" />
                  </head>
                  <body>
                  <table width="100%" border="0" cellspacing="0" cellpadding="0">
                    <tr>
                      <td align="center"><link rel="preconnect" href="https://fonts.googleapis.com">
                        <link rel="preconnect" href="https://fonts.googleapis.com">
                        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
                        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" rel="stylesheet">
                        <div style="max-width: 875px; margin: 0 auto; font-family: 'Roboto', arial, helvetica, sans-serif; font-size: 24px; display: block; padding: 15px;">
                          <div style="background-color: #FFFFFF; border: 1px solid #7f7f7f; padding: 30px; margin-bottom: 20px">
                            <div style="text-align: left">
                            <img src="{databrick_img_data}"
                              width="140" alt="Databrick">

                            </div>
                            <div style="text-align: center; padding-top: 60px; padding-bottom: 60px;">
                              <div style="font-weight: bold;">{sender}</div>
                              <div>{email_reason}</div>
                            </div>
                            {mail_link}
                          </div>
                          <div style="font-size: 12px; text-align: center; padding-bottom: 20px; display: block">This is a system generated email, please do not reply to this message.</div>
                        </div></td>
                    </tr>
                  </table>
              </div>
            </body>
          </html>
      """
    return html

databrick_img_data = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAMgAAAAxCAYAAACfxeZPAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAyVpVFh0WE1MOmNvbS5hZG9iZS54bXAAAAAAADw/eHBhY2tldCBiZWdpbj0i77u/IiBpZD0iVzVNME1wQ2VoaUh6cmVTek5UY3prYzlkIj8+IDx4OnhtcG1ldGEgeG1sbnM6eD0iYWRvYmU6bnM6bWV0YS8iIHg6eG1wdGs9IkFkb2JlIFhNUCBDb3JlIDYuMC1jMDAyIDc5LjE2NDM2MCwgMjAyMC8wMi8xMy0wMTowNzoyMiAgICAgICAgIj4gPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4gPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9IiIgeG1sbnM6eG1wPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RSZWY9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZVJlZiMiIHhtcDpDcmVhdG9yVG9vbD0iQWRvYmUgUGhvdG9zaG9wIDIxLjEgKE1hY2ludG9zaCkiIHhtcE1NOkluc3RhbmNlSUQ9InhtcC5paWQ6MENCOTYxNzlBODA1MTFFQUI3RTJCMjYwMDI0RkY2MDAiIHhtcE1NOkRvY3VtZW50SUQ9InhtcC5kaWQ6MENCOTYxN0FBODA1MTFFQUI3RTJCMjYwMDI0RkY2MDAiPiA8eG1wTU06RGVyaXZlZEZyb20gc3RSZWY6aW5zdGFuY2VJRD0ieG1wLmlpZDowQ0I5NjE3N0E4MDUxMUVBQjdFMkIyNjAwMjRGRjYwMCIgc3RSZWY6ZG9jdW1lbnRJRD0ieG1wLmRpZDowQ0I5NjE3OEE4MDUxMUVBQjdFMkIyNjAwMjRGRjYwMCIvPiA8L3JkZjpEZXNjcmlwdGlvbj4gPC9yZGY6UkRGPiA8L3g6eG1wbWV0YT4gPD94cGFja2V0IGVuZD0iciI/Pl/Wj5AAAB0YSURBVHja7F0J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"
