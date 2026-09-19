import logging
import traceback
from typing import List

import aiohttp
from fastapi import APIRouter, Depends, HTTPException, status
import httpx
from motor.motor_asyncio import AsyncIOMotorClient

from app.api.rbac.end_points_v1_access_control import CheckNameRoute
from app.config.env_vars import environment, gateway_environment
from app.core.db.db_utils import get_db_async
from app.core.services.cloud_utils.utils import get_secret_manager
from app.core.services.jwt_token_utils.jwt_token_utils import decodeJWT
from app.services.admin.authentication.schemas import (
    LoginResponse,
    UserLoginSchema,
    InviteUserSchema,
    RegisterUserSchema,
    User,
    TokensSchema,
    ChangePasswordSchema,
    SiteRoleSchema,
    RefreshTokenSchema,
    ChangeUserNamesSchema,
    SSOLoginSchema,
    InviteBulkUsersSchema,
    InviteUsersResponse,
    ActivateUserSchema,
    GenericResponse,
    UpdateUserByAdminSchema,
    UserDetailsRequest,
    UserDetailsResponse,
    UserDetails,
    UpdateUserRolesResponse,
    UpdateUserRolesRequest,
    PlatformLoginMethodsSchema,
    ServerRole,
    PasswordResetSchema,
    PasswordResetResponse,
    UpdateUserName,
    DeleteUserResponse,
)
from app.services.admin.authentication.service import AuthenticationService
from app.services.admin.authentication.utils import http_err_unauthorized
from app.services.admin.org_site_management.schemas import Site
from app.services.admin.org_site_management.service import OrgSiteManagementService
from datetime import datetime, timezone, timedelta
from prometheus_client import Gauge
logger = logging.getLogger(__package__)
authentication_router = APIRouter(prefix='/v1/authentication', tags=["Authentication"], route_class=CheckNameRoute)
user_last_active = {}
active_users = Gauge('active_users', 'Count of unique active users')
class AuthenticationRouter:

    def __init__(self):
        pass

    @authentication_router.post('/login', response_model=LoginResponse)
    async def login(user_login_sch: UserLoginSchema,
                    client: AsyncIOMotorClient = Depends(get_db_async)) -> LoginResponse:
        """
        Verifies the User exists or not with given email. if exists then checks it is password matched or not.
        if active user not exists with given email returns 401 error with message User not found
        if active user exists and password don't match returns 401 error with message Invalid id or password
        if there is a active user with successful user id and password returns LoginResponse which have user details, access token and refresh token (JWT tokens).
        After successful login, from front end need to send the access token (in body) with every request for the services which are
        restricted with JWT dependency injection. if gets authorization fails, need to call getRefreshedTokens serice with access token and refresh token.
        if Refresh token still valid, FE can get new access & refresh token. if the refresh token too expired then FE need to notify the user for forced logout.
        """
        try:
            logger.info("using login method.")
            auth_service = AuthenticationService(db_async_client=client)
            if environment.form_login_allowed == False:
                if await auth_service.is_default_server_admin(user_login_sch.email) == False:
                    auth_service.is_default_server_admin()
                    return http_err_unauthorized('Form Login not allowed on the environment')

            login_resp = await auth_service.validate_user_and_return_token(user_login_sch)
            logger.info(f"login method.")

            if not login_resp:
                logger.exception("User not found.")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            user_email = login_resp.user_data.email
            user_id = login_resp.user_data.id
            if user_id not in user_last_active:
                active_users.inc()
            user_last_active[user_id] = datetime.now(timezone.utc)

            # hexaind 2.0 user login
            logger.info(f"creating user in hexaind 2.0 {(environment.hexaind_2_api_url is not None)}")
            try:
                if environment.hexaind_2_api_url and isinstance(login_resp, LoginResponse):
                    async with aiohttp.ClientSession(base_url=str(environment.hexaind_2_api_url)) as session:
                        response = await session.post(
                            "/user/hexaind3/login",
                            data={
                                "name": login_resp.user_data.name,
                                "firstName": login_resp.user_data.first_name,
                                "lastName": login_resp.user_data.last_name,
                                "email": str(login_resp.user_data.email),
                                "roleId": login_resp.user_data.server_role_value,
                                "accessToken": login_resp.access_token
                            }
                        )
                        match response.status:
                            case status.HTTP_200_OK | status.HTTP_201_CREATED:
                                logger.info("successfully created/updated user")
                            case status.HTTP_500_INTERNAL_SERVER_ERROR:
                                logger.error("unable to create/update user")
                            case _:
                                pass
            except Exception as e:
                # ignoring exceptions arising due to this failure
                logger.exception(f"Failed to create/update existing user via hexaind2 api : {str(e)}")


            return login_resp

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed with exception {e}")

    @authentication_router.post('/logout')
    async def logout(email: str, client: AsyncIOMotorClient = Depends(get_db_async)) -> str:
        """
        Marks the user as logged out.
        """
        try:
            logger.info("using logout method.")
            auth_service = AuthenticationService(db_async_client=client)
            logout_msg = await auth_service.logout_user(email)
            logger.info(f"logout authorised with response {logout_msg}")

            if not logout_msg:
                logger.exception("Failed to Logout")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Failed to Logout")
            user = await auth_service.authentication_dao.get_user_by_email(email)
            user_id = user['_id']
            # logger.info("========================")
            # logger.info(user_id)
            if user_id in user_last_active:
                del user_last_active[user_id]
                active_users.dec()
            # hexaind 2.0 user logout
            logger.info(f"logging out user in hexaind 2.0 {(environment.hexaind_2_api_url is not None)}")
            try:
                if environment.hexaind_2_api_url:
                    async with aiohttp.ClientSession(base_url=str(environment.hexaind_2_api_url)) as session:
                        await session.post(
                            "/user/hexaind3/logout", json={"email": email}
                        )
            except Exception as e:
                logger.exception(f"Failed to logout existing user via hexaind2 api : {str(e)}")


            return logout_msg

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed with exception {e}")

    @authentication_router.delete('/deleteUser')
    async def delete_user(email: str, client: AsyncIOMotorClient = Depends(get_db_async),
                          token: str = '') -> str:
        """
        Marks the user as deleted, but really it will not removes the record
        """
        try:
            logger.info("using delete user.")
            auth_service = AuthenticationService(db_async_client=client)
            resp_msg = await auth_service.deactivate_user(email, token)
            logger.info(f"deleted user with response as {resp_msg}")

            if not resp_msg:
                logger.exception("Failed to Delete User")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Failed to Delete User")

            return resp_msg

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed with exception {e}")

    @authentication_router.delete("/delete_user/{user_id}")
    async def user_permanent_delete(
        user_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
        token: str = "",
    ) -> DeleteUserResponse:
        """
        Marks the user as deleted, removes the record
        """
        try:
            logger.info("using delete user.")
            auth_service = AuthenticationService(db_async_client=client)
            user: User = await auth_service.get_user_with_id(user_id)

            # SuperSet User Deletion
            if user.data_superset is not None:
                async with httpx.AsyncClient(
                    base_url=str(gateway_environment.superset_url), timeout=None
                ) as http_client:
                    pk = user.data_superset.superset_user_id
                    delete_url = f"/api/v1/security/users/{pk}"

                    headers = {
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    }

                    create_response = await http_client.delete(
                        delete_url, headers=headers
                    )
                    user.data_superset.superset_user_id = create_response.json()["id"]

                    if create_response.status_code != 201:
                        logger.error(f"User deletion failed: {create_response.text}")
                        raise HTTPException(
                            status_code=500, detail="Superset user deletion failed."
                        )

                    logger.info("Superset user deleted successfully.")

            # HEXAIND user deletion
            resp_msg = await auth_service.delete_user_with_id(user_id=user_id)
            logger.info(f"deleted user with response as {resp_msg.msg}")

            return resp_msg

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed with exception {e}",
            )
    
    @authentication_router.patch('/activate_user_by_admin')
    async def activate_user_by_admin(email: str, client: AsyncIOMotorClient = Depends(get_db_async), token:str = '') -> str:
        """
        Marks the user as active
        """
        try:
            logger.info("using activate_user_by_admin.")
            auth_service = AuthenticationService(db_async_client=client)
            resp_msg = await auth_service.activate_user_by_admin(email, token)
            logger.info(f"activated user with response as {resp_msg}")

            if not resp_msg:
                logger.exception("Failed to Activate User")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Failed to Activate User")

            return resp_msg

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed with exception {e}")

    @staticmethod
    @authentication_router.post('/sso_login', response_model=LoginResponse)
    async def sso_login(sso_schema: SSOLoginSchema,
                        client: AsyncIOMotorClient = Depends(get_db_async)) -> LoginResponse:
        """
        FE application passes access_token & raw_token.
        Tries to decode access_token for email id, if fails, then decodes the raw_token. if fails with raw_token too, returns 401 error
        Verifies the User exists or not with given email.
        if there is a active user with the user id returns LoginResponse which have user details, access token and refresh token (JWT tokens).
        Remaining process same as normal login
        """
        try:
            logger.info("Using SSO login method.")

            if environment.sso_login_allowed == False:
                return http_err_unauthorized('SSO Login not allowed on this environment')

            auth_service = AuthenticationService(db_async_client=client)
            login_resp = await auth_service.validate_sso_token_and_return_jwt_token(sso_schema)
            logger.info("login authorization checked")

            if not login_resp:
                logger.exception("User not found.")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

            logger.info(f"creating user in hexaind 2.0 via sso {(environment.hexaind_2_api_url is not None)}")
            try:
                if environment.hexaind_2_api_url and isinstance(login_resp, LoginResponse):
                    async with aiohttp.ClientSession(base_url=str(environment.hexaind_2_api_url)) as session:
                        response = await session.post(
                            "/user/hexaind3/login",
                            data={
                                "name": login_resp.user_data.name,
                                "firstName": login_resp.user_data.first_name,
                                "lastName": login_resp.user_data.last_name,
                                "email": str(login_resp.user_data.email),
                                "roleId": login_resp.user_data.server_role_value,
                                "accessToken": login_resp.access_token
                            }
                        )
                        match response.status:
                            case status.HTTP_200_OK | status.HTTP_201_CREATED:
                                logger.info("successfully created/updated user")
                            case status.HTTP_500_INTERNAL_SERVER_ERROR:
                                logger.error("unable to create/update user")
                            case _:
                                pass
            except Exception as e:
                logger.exception(f"Failed to create/update existing user via hexaind2 api : {str(e)}")



            return login_resp

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed with exception {e}")

    @staticmethod
    @authentication_router.post('/invite_users')
    async def invite_users(invite_users_list: List[InviteUserSchema], token: str = '',
                           client: AsyncIOMotorClient = Depends(get_db_async)) -> InviteUsersResponse:
        """
        Creates the user in Users collection with the provided details like
        email,  name, list of sites & roles.
        Only Org Admin can create Users.
        Once User created successfully, send invitation mail. With mail link the user is landed to the Registration page.
        From there user need to provide password, first & last names.
        """
        try:
            logger.info("using invite users.")
            token = decodeJWT(token)
            if int(token['server_role_value']) & 3 == 0:
                return http_err_unauthorized("Don't have permission to create new user")

            if environment.sso_login_allowed == False or environment.form_login_allowed == False:
                sso_user_invited = False
                form_user_invited = False
                for user in invite_users_list:
                    if user.is_sso_user:
                        sso_user_invited = True
                    else:
                        form_user_invited = True
                if environment.sso_login_allowed == False and sso_user_invited:
                    return http_err_unauthorized(
                        "SSO type user cannot be added as SSO login not allowed on this environment")
                if environment.form_login_allowed == False and form_user_invited:
                    return http_err_unauthorized(
                        "Form type user cannot be added as Form login not allowed on this environment")

            auth_service = AuthenticationService(db_async_client=client)
            logger.info("returning created user.")
            resp = await auth_service.invite_users(invite_users_list, token['user_id'])
            return resp

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed with exception {e}")

    @authentication_router.post('/createSite', tags=["SiteManagement"])
    async def create_site(site: Site, token: str = '',
                          client: AsyncIOMotorClient = Depends(get_db_async)) -> Site:
        """
        Creates the Site of Organization.
        Only Org Admin can create a site.
        Returns Site object after successful creation. Else returns 401 error with the reason of failure
        """
        try:
            logger.info("in create site method.")
            org_mngt_service = OrgSiteManagementService(db_async_client=client)
            logger.info("Creating site and returning...")
            return await org_mngt_service.create_site(site, token)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed with exception {e}")

    @authentication_router.get("/isUserAlreadyRegistered")
    async def is_user_already_registered(email: str, token: str = '',
                                         client: AsyncIOMotorClient = Depends(get_db_async)) -> bool:
        """
        To test the user is already registered or not. FE can evaluate a registration request & reply already registred or not.
        """
        try:
            logger.info("using is user already registered method.")
            auth_service = AuthenticationService(db_async_client=client)
            logger.info("Verifying user registered or not and returned.")
            return await auth_service.is_already_registered(email)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed with exception {e}")

    @authentication_router.post("/registerUser")
    async def register_user(register_user_sch: RegisterUserSchema,
                            client: AsyncIOMotorClient = Depends(get_db_async)) -> GenericResponse:
        """
        Once user is created, an email sent to the provided email contains link to the FE application.
        using this service user can choose password, first name and last name.
        On successful registration, user is forwarded to the HEXAIND services offered to the user based on the roles added to the user.
        """
        try:
            logger.info("using update password with the email token.")
            auth_service = AuthenticationService(db_async_client=client)
            logger.info("updating the password.")
            return await auth_service.register_user(register_user_sch)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed with exception {e}")

    @authentication_router.post("/activate_user")
    async def register_user(activate_user_sch: ActivateUserSchema,
                            client: AsyncIOMotorClient = Depends(get_db_async)) -> GenericResponse:
        """
        Once user is created, an email sent to the provided email contains link to the FE application.
        using this service user can Activate the user status
        """
        try:
            logger.info("using actuvate user  with the email token.")
            auth_service = AuthenticationService(db_async_client=client)
            return await auth_service.activate_user(activate_user_sch)

        except Exception as e:
            logger.error("Exception at activate_user")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Failed with exception {e} At activate_user")

    @authentication_router.get("/get_users_list")
    async def get_users_list(token: str = '', client: AsyncIOMotorClient = Depends(get_db_async)) -> \
            List[User]:
        """
        Returns all the users along with their roles. Only accessed by Orgnization Admin
        """
        try:
            logger.info("getting users with roles.")
            token = decodeJWT(token)
            if int(token['server_role_value']) & 1 == 0:
                return http_err_unauthorized('Only Organization Admin can get All users list')
            auth_service = AuthenticationService(db_async_client=client)
            users_list = await auth_service.get_users_list()
            logger.info(f"fetched users with roles {len(users_list)}")
            #TODO Move it to another api to reduce the time taken for this api
            await auth_service.force_logout_user(users=users_list)

            return users_list

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed with exception {e}")

    @staticmethod
    @authentication_router.post("/get_user_details_based_on_filter")
    async def get_filtered_users_details(request: UserDetailsRequest, token: str = '',
                                         client: AsyncIOMotorClient = Depends(
                                             get_db_async)) -> UserDetailsResponse:
        """
        Returns all the users along with their roles based on filter
        """
        try:
            logger.info("getting users with roles.")
            token = decodeJWT(token)
            auth_service = AuthenticationService(db_async_client=client)
            custom_query = {"server_role_value": {"$in": request.server_role_values}, "status": {"$eq": "Active"}}
            users, results_count = await auth_service.get_paginated_users_list(search_term=request.search_term,
                                                                               page_number=request.page_number,
                                                                               page_limit=request.page_limit,
                                                                               custom_query=custom_query,
                                                                               fetch_role_details=request.fetch_role_details)
            results = []
            for user in users:
                if user.id == token['user_id'] and request.skip_own:
                    results_count = results_count - 1
                    continue
                results.append(UserDetails(**user.model_dump(), user_id=user.id, user_name=user.name))
            logger.info(f"fetched users based on filter {len(results)} {results_count}")
            return UserDetailsResponse(succeeded=True, message="fetched required users", results=results,
                                       results_count=results_count)
        except Exception as e:
            logger.exception(f"Got exception while fetching users based on server role {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed with exception {e}")

    @authentication_router.post("/getUserDetailsWithRoles")
    async def get_user_details_with_roles(user_id: str, token: str = '',
                                          client: AsyncIOMotorClient = Depends(get_db_async)) -> User:
        """
        Returns requested user record with List of roles. A role is combination of site_id and role_id
        """
        try:
            logger.info("getting user record with List of roles")
            auth_service = AuthenticationService(db_async_client=client)
            return await auth_service.get_user_details_with_roles(user_id, token)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed with exception {e}")

    @authentication_router.post("/getUserAccessRoles")
    async def get_user_access_roles(user_id: str, token: str = '',
                                    client: AsyncIOMotorClient = Depends(get_db_async)) -> List[SiteRoleSchema]:
        """
        Returns List of roles of requested user
        """
        try:
            logger.info("getting list of roles of requested user")
            auth_service = AuthenticationService(db_async_client=client)
            return await auth_service.get_user_access_roles(user_id)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed with exception {e}")

    @authentication_router.post("/changePassword")
    async def change_password(changePwdSchema: ChangePasswordSchema, token: str = '',
                              client: AsyncIOMotorClient = Depends(get_db_async)) -> bool:
        """
        A service to change the user password. This is invoked from user profile. So he need to provide existing password, new password & confirmation password
        """
        try:
            logger.info("attempting change the user password")
            auth_service = AuthenticationService(db_async_client=client)
            return await auth_service.change_password_from_profile(changePwdSchema, token)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed with exception {e}")

    @authentication_router.post("/getRefreshedTokens")
    async def get_refreshed_tokens(refreshTokenSchema: RefreshTokenSchema,
                                   client: AsyncIOMotorClient = Depends(get_db_async)) -> TokensSchema:
        """
        Returns Refreshed tokens (access token & refresh token)
        When a restricted service called woth access token, if the token expires then FE can request for fresh tokens by presenting access token and refresh tokens.
        if the refresh token too expires then FE application need to force the user to logout and login again
        """
        try:
            logger.info("getting the refreshed token.")
            auth_service = AuthenticationService(db_async_client=client)
            return await auth_service.get_refreshed_tokens(refreshTokenSchema)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed with exception {e}")

    @staticmethod
    @authentication_router.post("/reset_password_by_user")
    async def reset_password_by_user(pwd_reset_schema: PasswordResetSchema,
                                     client: AsyncIOMotorClient = Depends(get_db_async)) -> PasswordResetResponse:
        """
        Reset password for the user. By any chance user forgets password & assign strong password etc.., he can user reset password from the Login screen.
        User need to provide the email is & reason. Then a mail sent to the user which haves a token with expiry.
        User can click on link of email & can provide password & confirmation password.
        With a reset pwd from login screen not going to change existing password, as it can be done by some one else too.
        """
        try:
            logger.info("attempting reset password for the user.")
            auth_service = AuthenticationService(db_async_client=client)
            return await auth_service.reset_password(pwd_reset_schema.email, pwd_reset_schema.reason)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed with exception {e}")

    @staticmethod
    @authentication_router.post("/reset_password_by_server_admin")
    async def reset_password_by_org_admin(pwd_reset_schema: PasswordResetSchema, token: str = '',
                                          client: AsyncIOMotorClient = Depends(get_db_async)) -> PasswordResetResponse:
        """
        Reset password for the ORg Admin. Existing password replaced with a random password, So the password change can happen only from email link.
        This can be done when a request comes from the user as forgot password or Admin forces to change the password.
        Admin need to provide the email & reason. Then a mail sent to the user which haves a token with expiry.
        User can click on link of email & can provide password & confirmation password.
        """
        try:
            logger.info("attempting reset password from org admin.")
            auth_service = AuthenticationService(db_async_client=client)
            return await auth_service.reset_password(pwd_reset_schema.email, pwd_reset_schema.reason, token)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed with exception {e}")

    @staticmethod
    @authentication_router.post("/updatePasswordByEmailToken")
    async def update_pwd_using_email_token(register_user_sch: RegisterUserSchema,
                                           client: AsyncIOMotorClient = Depends(get_db_async)) -> GenericResponse:
        """
        When password reset by user/ Org Admin, A mail is sent with token haves mail id and expiry period.
        Once the token is presented to this service, it will validates. if valid the given password applied to the given email.
        """
        try:
            logger.info("attempting change password after reset password.")
            auth_service = AuthenticationService(db_async_client=client)
            return await auth_service.change_password_using_email_token(register_user_sch)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed with exception {e}")

    @authentication_router.post("/toggleUserActiveStatus")
    async def toggle_user_active_status(email: str, token: str = '',
                                        client: AsyncIOMotorClient = Depends(get_db_async)) -> bool:
        """
        To make a user to active to in-active vice versa
        """
        try:
            logger.info("toggling the user to active/in-active")
            auth_service = AuthenticationService(db_async_client=client)
            return await auth_service.toggle_user_active_status(email, token)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed with exception {e}")

    #TODO: delete this if FE doesnt use it.
    @staticmethod
    @authentication_router.post("/update_user_server_roles")
    async def update_user_server_roles(request: UpdateUserRolesRequest, token: str = '',
                                       client: AsyncIOMotorClient = Depends(get_db_async)) -> UpdateUserRolesResponse:
        """
        updates user roles based on input
        """
        try:
            logger.info("attempting update user roles.")
            decoded_token = decodeJWT(token)
            auth_service = AuthenticationService(db_async_client=client)
            for i, change in enumerate(request.changes):
                request.changes[i].server_role = "Server Admin" if change.server_role_value == 1 \
                    else "Project Admin" if change.server_role_value == 2 else "Default User"
            logger.info(f"requested to change roles for {request.changes}")
            await auth_service.update_user_roles(request.changes, decoded_token["user_id"])
            return UpdateUserRolesResponse(succeeded=True, message="updated these user roles")
        except Exception as e:
            logger.exception(f"updated user server roles failed {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed with exception {e}")

    @authentication_router.post("/updateUserNames")
    async def update_user_names(changeUserNameSchema: ChangeUserNamesSchema, token: str = '',
                                client: AsyncIOMotorClient = Depends(get_db_async)) -> UpdateUserName:
        """
        To update the user name, first name & last name.
        Need to present the valid token, user, first name & last name.
        """
        try:
            logger.info("attempting update usernames.")
            auth_service = AuthenticationService(db_async_client=client)
            await auth_service.update_user_names(changeUserNameSchema, token)
            user = await auth_service.get_active_user(email=changeUserNameSchema.email)
            return UpdateUserName(user_id=user['_id'], name=user['name'], email=user['email'])

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed with exception {e}")

    @staticmethod
    @authentication_router.post('/invite_bulk_users')
    async def create_multiple_users(invite_bulk_users: InviteBulkUsersSchema, token: str = '',
                                    client: AsyncIOMotorClient = Depends(get_db_async)):
        """
        Creates the users in Users collection with the provided details like email,  role & azure login yes/ no.
        Only Org Admin can create Users.
        Once Users created successfully, sends invitation mail. With the mail link, user is landed to the Registration page.
        From there user need to provide password, first & last names.
        if there is no site_id or site_id value is 1 then user roles are mapped to DefaultSite. if DefaultSite named site is not found then it is created
        """
        try:
            logger.info("Inviting bulk users")
            auth_service = AuthenticationService(db_async_client=client)
            return await auth_service.invite_bulk_users(invite_bulk_users, token)

        except Exception as e:
            logger.exception("Excepption while inviting Bulk users")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed with exception {e}")

    @staticmethod
    @authentication_router.post("/update_user_by_admin")
    async def update_user_by_admin(updt_user_by_admin_sch: UpdateUserByAdminSchema, token: str = '',
                                   client: AsyncIOMotorClient = Depends(get_db_async)) -> GenericResponse:
        """
        To update the user name, first name & last name.
        Need to present the valid token, user, first name & last name.
        """
        try:
            logger.info("attempting to update user details by Admin")
            token = decodeJWT(token)
            if int(token['server_role_value']) & 1 == 0:
                return http_err_unauthorized('Not authorized to update the user')

            auth_service = AuthenticationService(db_async_client=client)
            return await auth_service.update_user_by_admin(updt_user_by_admin_sch, token['user_id'])

        except Exception as e:
            logger.exception("Exception at update_user_by_admin")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed with exception {e}")

    @staticmethod
    @authentication_router.post("/resend_invitation_mail")
    async def resend_invitation_mail(email: str, token: str = '',
                                     client: AsyncIOMotorClient = Depends(get_db_async)) -> GenericResponse:
        """
        To update the user name, first name & last name.
        Need to present the valid token, user, first name & last name.
        """
        try:
            logger.info("attempting to resend invitation")
            token = decodeJWT(token)
            if int(token['server_role_value']) & 1 == 0:
                return http_err_unauthorized('Not authorized to resend the invitation')
            auth_service = AuthenticationService(db_async_client=client)
            return await auth_service.resend_invitation_mail(email, token['user_id'])

        except Exception as e:
            logger.exception("Exception at resend_invitation_mail")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed with exception {e}")

    @staticmethod
    @authentication_router.get("/get_login_methods_of_plotform")
    async def get_login_methods_of_plotform() -> PlatformLoginMethodsSchema:
        """
        Returns the environment variable values related to login methods such as 
        FORM_LOGIN_ALLOWED & SSO_LOGIN_ALLOWED
        """
        try:
            logger.info("attempting to send login methods of environment")

            paltform_login_method =  PlatformLoginMethodsSchema(form_login_allowed = environment.form_login_allowed,
                                                                sso_login_allowed = environment.sso_login_allowed)
            
            return paltform_login_method

        except Exception as e:
            logger.exception("Exception at get_login_methods_of_plotform")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed with exception {e}")

    @staticmethod
    @authentication_router.get("/reload_azure_keyvault_values", tags=["Healthcheck"])
    async def reload_azure_keyvault_values() -> GenericResponse:
        try:
            secret_manager = get_secret_manager()
            secret_manager.re_fetch_secrets_of_keys_available()
            return GenericResponse(status=True, message="Successfully reloaded the All keys which are loaded into memory")
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed with exception {e}")

    @staticmethod
    @authentication_router.get("/get_server_roles")
    async def get_server_roles(client: AsyncIOMotorClient = Depends(get_db_async)) -> List[ServerRole]:
        try:
            auth_service = AuthenticationService(db_async_client=client)
            return await auth_service.get_server_roles()
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed with exception {e}")
