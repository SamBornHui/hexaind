import json
import logging
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from app.services.access_controls.user_projects.schemas import AppPermission, EditAppPermission

from app.core.db.db_utils import get_db_async
from app.core.services.jwt_token_utils.jwt_token_utils import JWTBearer, decodeJWT
from app.services.access_controls.features.schemas import EndPointsFeatureMappings
from app.services.access_controls.features.service import EndPointsFeatureMappingsService
from app.services.access_controls.user_projects.schemas import (
    CreateMappingResponse,
    CreateMappingRequest,
    CreateMappingRequestMultiple,
    GetRolesBasedOnIdRequest,
    GetRolesBasedOnIdResponse,
    UserProjectsMappingWithDetails, GetUnmappedUsersToProjectRequest,
)
from app.services.access_controls.user_projects.schemas import (
    UsersAccessControlDetailsBaseResponse,
    DeleteUserProjMappingRequest
)
from app.services.access_controls.roles.service import RolesFeaturesMapService
from app.services.access_controls.roles.schemas import (
    RolesFeaturesMapUpdateRequest,
    RolesFeaturesMapGetRequest,
    RoleFeaturesMapRequestName,
    RolesFeaturesMapGetResponse,
    RolesFeaturesMapCreateRequest,
    RolesFeaturesMapCreateResponse,
    GetAllRolesResponse,
    RoleIdRoleName, SystemGeneratedProjectRoles,
)
from app.services.access_controls.user_projects.service import UsersProjectsMappingsService
from app.services.admin.authentication.schemas import UserDetailsResponse, UpdateUserRolesRequest, \
    UpdateUserRolesResponse, ServerBasedRoleNames
from app.utils.file_utils import FileUtils
from app.api.rbac.end_points_v1_access_control import CheckNameRoute
from app.services.admin.authentication.service import AuthenticationService
from app.config.env_vars import environment
logger = logging.getLogger(__package__)

users_access_control_details_router = APIRouter(tags=["UsersAccessControlDetails"], route_class=CheckNameRoute)


class UsersAccessControlDetailsRouter:
    def __init__(self):
        pass


    @staticmethod
    @users_access_control_details_router.post("/v1/sites/{site_id}/roles_features_maps/create",
                                              response_model=RolesFeaturesMapCreateResponse)
    async def create_roles_features_map(site_id: str,
                                        roles_features_map_data: RolesFeaturesMapCreateRequest,
                                        db_async_client: AsyncIOMotorClient = Depends(
                                            get_db_async),
                                        token: str = ''):
        requesting_user = decodeJWT(token=token)
        try:
            service = RolesFeaturesMapService(db_async_client=db_async_client)
            if roles_features_map_data.name in list(SystemGeneratedProjectRoles):
                raise ValueError(f"Cannot insert with name {roles_features_map_data.name}, these names are restricted to server")
            role_id = await service.insert_roles_features_map(user_id=requesting_user["user_id"],
                                                              roles_features_map_data=roles_features_map_data)
            return RolesFeaturesMapCreateResponse(succeeded=True, message="Creation Successful", role_id=role_id)

        except Exception as e:
            logger.exception(f"Failed to create roles: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Failed to create roles:")

    @staticmethod
    @users_access_control_details_router.put("/v1/sites/{site_id}/roles_features_maps/{roles_features_map_id}/update",
                                             response_model=str)  # Adjust response model as needed
    async def update_roles_features_map(site_id: str,
                                        roles_features_map_id: str,
                                        roles_features_map_update_request: RolesFeaturesMapUpdateRequest,
                                        db_async_client: AsyncIOMotorClient = Depends(
                                            get_db_async),
                                        token: str = '') -> str:
        requesting_user = decodeJWT(token=token)
        try:
            service = RolesFeaturesMapService(db_async_client=db_async_client)
            return await service.update_roles_features_map(roles_features_map_id, roles_features_map_update_request)
        except Exception as e:
            logger.exception(f"Failed to update roles: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Failed to update roles:")

    @staticmethod
    @users_access_control_details_router.post("/v1/sites/{site_id}/roles_features_maps/get_role_feature_map_id",
                                              response_model=RolesFeaturesMapGetResponse)
    async def get_roles_features_map_id(site_id: str,
                                        config: RolesFeaturesMapGetRequest,
                                        db_async_client: AsyncIOMotorClient = Depends(
                                            get_db_async),
                                        token: str = ''):
        requesting_user = decodeJWT(token=token)
        try:
            service = RolesFeaturesMapService(db_async_client=db_async_client)
            data = await service.get_roles_features_map_by_id(roles_features_map_id=config.roles_id)
            return RolesFeaturesMapGetResponse(role_info=data, succeeded=True, message="Fetch successfull")

        except Exception as e:
            logger.exception(f"Failed to get roles details: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Failed to get roles details")

    @staticmethod
    @users_access_control_details_router.post("/v1/sites/{site_id}/roles_features_maps/get_role_feature_map_name",
                                              response_model=RolesFeaturesMapGetResponse)  # Adjust response model as needed
    async def get_roles_features_map_name(site_id: str,
                                          config: RoleFeaturesMapRequestName,
                                          db_async_client: AsyncIOMotorClient = Depends(
                                              get_db_async),
                                          token: str = ''):
        requesting_user = decodeJWT(token=token)
        try:
            service = RolesFeaturesMapService(db_async_client=db_async_client)
            data = await service.get_roles_features_map_by_name(roles_name=config.role_name)
            return RolesFeaturesMapGetResponse(role_info=data, succeeded=True, message="Fetch successfull")

        except Exception as e:
            logger.exception(f"Failed to get roles details by name: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Failed to get roles details")

    @staticmethod
    @users_access_control_details_router.post("/v1/sites/{site_id}/roles_features_maps/get_all_roles",
                                              response_model=GetAllRolesResponse)
    async def get_all_roles(site_id: str, db_async_client: AsyncIOMotorClient = Depends(get_db_async),
                            token: str = ''):
        requesting_user = decodeJWT(token=token)
        try:
            service = RolesFeaturesMapService(db_async_client=db_async_client)
            roles, count = await service.fetch_all_roles_features_maps()
            if len(roles) != count:
                raise Exception(
                    f"there are more roles {count} than pulled count{len(roles)}")
            data = [RoleIdRoleName(**role.model_dump()) for role in roles]
            return GetAllRolesResponse(results=data, succeeded=True, message="Fetch all successfull")

        except Exception as e:
            logger.exception(f"Failed to get all roles: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Failed to get all roles")

    @staticmethod
    @users_access_control_details_router.post("/v1/sites/{site_id}/users_projects_mappings/create_user_project_mappings",
                                              response_model=UsersAccessControlDetailsBaseResponse)
    async def create_user_project_mappings(site_id, create_mapping_requests: CreateMappingRequestMultiple,
                                          db_async_client: AsyncIOMotorClient = Depends(
                                              get_db_async),
                                          token: str = '') -> UsersAccessControlDetailsBaseResponse:
        try:
            requesting_user = decodeJWT(token=token)
            users_projects_mappings_service = UsersProjectsMappingsService(
                db_async_client)
            await users_projects_mappings_service.create_new_mappings(
                request_user_id=requesting_user['user_id'],
                mappings_object=create_mapping_requests
            )
            return UsersAccessControlDetailsBaseResponse(
                succeeded=True,
                message="Create mappings successfully"
            )
        except Exception as e:
            logger.exception(f"Failed to create new mapping: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Failed to create new user project mapping: {str(e)}")

    @staticmethod
    @users_access_control_details_router.post(
        "/v1/sites/{site_id}/users_projects_mappings/update_user_roles_for_project",
        response_model=UsersAccessControlDetailsBaseResponse)
    async def update_user_mappings_for_project(site_id, create_mapping_request: CreateMappingRequestMultiple,
                                               db_async_client: AsyncIOMotorClient = Depends(
                                                   get_db_async),
                                               token: str = Depends(
                                                   JWTBearer())) -> UsersAccessControlDetailsBaseResponse:
        try:
            requesting_user = decodeJWT(token=token)
            users_projects_mappings_service = UsersProjectsMappingsService(
                db_async_client)

            await users_projects_mappings_service.update_existing_mappings_for_project(
                user_mappings=create_mapping_request.mappings, user_id=requesting_user['user_id'])
            return UsersAccessControlDetailsBaseResponse(
                succeeded=True,
                message="Create mappings successfully"
            )
        except Exception as e:
            logger.exception(f"Failed to create new mapping: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Failed to create new user project mapping {e}")

    @staticmethod
    @users_access_control_details_router.post("/v1/sites/{site_id}/users_projects_mappings/update_user_project_mapping",
                                              response_model=CreateMappingResponse)
    async def modify_existing_user_project_mapping(site_id, create_mapping_request: CreateMappingRequest,
                                                   db_async_client: AsyncIOMotorClient = Depends(
                                                       get_db_async),
                                                   token: str = '') -> CreateMappingResponse:
        try:
            requesting_user = decodeJWT(token=token)
            auth_service = AuthenticationService(db_async_client=db_async_client)
            mapping_user = await auth_service.get_user_with_id(create_mapping_request.user_id)
            if not mapping_user:
                raise ValueError("Requested user does not exists")

            if mapping_user.server_role_value == 1:
                raise ValueError("Cannot create mapping for server admin. Server admin is Project admin for every project.")

            users_projects_mappings_service = UsersProjectsMappingsService(
                db_async_client)
            mapping_id = await users_projects_mappings_service.update_existing_mapping(
                requesting_user['user_id'],
                create_mapping_request.user_id,
                create_mapping_request.project_id,
                create_mapping_request.role_id
            )
            return CreateMappingResponse(
                mapping_id=mapping_id,
                succeeded=True,
                message="Updated mapping successfully"
            )
        except Exception as e:
            logger.exception(f"Failed to create new mapping: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Failed to create new user project mapping {e}")

    @staticmethod
    @users_access_control_details_router.post(
        "/v1/sites/{site_id}/users_projects_mappings/get_mappings_based_on_project_id",
        response_model=GetRolesBasedOnIdResponse)
    async def get_mapping_details_by_project_id(site_id: str, request: GetRolesBasedOnIdRequest,
                                                db_async_client: AsyncIOMotorClient = Depends(
                                                    get_db_async),
                                                token: str = '') -> GetRolesBasedOnIdResponse:
        try:
            decoded_token = decodeJWT(token=token)
            users_projects_mappings_service = UsersProjectsMappingsService(
                db_async_client)
            if request.get_details:
                final_mappings_with_details = await users_projects_mappings_service.get_mapping_details_by_project_id(
                    request.id)
                for item in final_mappings_with_details:
                    item.id = item.user_id
            else:
                mappings = await users_projects_mappings_service.get_mappings_by_project_id(request.id)
                final_mappings_with_details = [UserProjectsMappingWithDetails(
                    **mapping.model_dump()) for mapping in mappings]

            return GetRolesBasedOnIdResponse(
                mappings=final_mappings_with_details,
                succeeded=True,
                message="Mappings fetched successfully based on project id."
            )
        except Exception as e:
            logger.exception(f"Failed to fetch roles based on project ID: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Failed to fetch roles based on project ID{e}")

    @staticmethod
    @users_access_control_details_router.post(
        "/v1/sites/{site_id}/users_projects_mappings/get_mappings_based_on_user_id",
        response_model=GetRolesBasedOnIdResponse)
    async def get_projects_based_on_user_id(site_id,
                                            request: GetRolesBasedOnIdRequest,
                                            db_async_client: AsyncIOMotorClient = Depends(
                                                get_db_async),
                                            token: str = '') -> GetRolesBasedOnIdResponse:
        try:
            decoded_token = decodeJWT(token=token)
            users_projects_mappings_service = UsersProjectsMappingsService(
                db_async_client)

            if decoded_token.get('server_role_value', 4) == 1 and decoded_token.get('user_id') == request.id:
                final_mappings_with_details = await users_projects_mappings_service.get_mapping_details_for_server_admin(
                    request.id)
                # TODO: replacing id temporarily to unblock UI so giving same values for multiple keys.
                # TODO: later need to replace this once UI removed dependency on "_id"
                for item in final_mappings_with_details:
                    item.id = item.project_id
                return GetRolesBasedOnIdResponse(
                    mappings=final_mappings_with_details,
                    succeeded=True,
                    message="Mappings fetched successfully based on project id for server admin"
                )

            user_id = decoded_token['user_id'] if request.id == '' else request.id
            if request.get_details:
                final_mappings_with_details = await users_projects_mappings_service.get_mapping_details_by_user_id(user_id)
                for item in final_mappings_with_details:
                    item.id = item.project_id
            else:
                mappings = await users_projects_mappings_service.get_mappings_by_user_id(user_id)
                final_mappings_with_details = [UserProjectsMappingWithDetails(
                    **mapping.model_dump()) for mapping in mappings]

            return GetRolesBasedOnIdResponse(
                mappings=final_mappings_with_details,
                succeeded=True,
                message="Mappings fetched successfully based on user id."
            )
        except Exception as e:
            logger.exception(f"Failed to fetch projects based on user ID: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Failed to fetch projects based on user ID: {e}")

    @staticmethod
    @users_access_control_details_router.delete("/v1/sites/{site_id}/roles_features_maps/delete_user_project_mapping")
    async def delete_user_proj_map(site_id: str,
                                   config: DeleteUserProjMappingRequest,
                                   db_async_client: AsyncIOMotorClient = Depends(
                                       get_db_async),
                                   token: str = ''
                                   ):
        requesting_user = decodeJWT(token=token)
        try:
            service = UsersProjectsMappingsService(
                db_async_client=db_async_client)
            count = await service.delete_user_proj_mappings(mapped_user_id=config.user_id,
                                                            project_id=config.project_id,
                                                            user_id=requesting_user['user_id'])
            return UsersAccessControlDetailsBaseResponse(succeeded=True,
                                                         message=f"Deleted all the matching mappings. delete count: {count}")

        except Exception as e:
            logger.exception(f"Failed with exception: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Failed to delete mappings : {e}")

    @staticmethod
    @users_access_control_details_router.get("/v1/create_endpoints_features_mappings_based_db_dump",
                                             response_model=bool)
    async def create_endpoints_features_mapping(json_file_path: str = 'endpoints_features_mappings.json',
                                                db_async_client: AsyncIOMotorClient = Depends(get_db_async)):
        try:
            abs_file_path = Path(__file__).parent / json_file_path
            logger.info(f"reading json data from {abs_file_path}")
            endpoints_features_mappings_json = FileUtils.read_from_json(
                str(abs_file_path.absolute()))
            endpoints_feature_mappings_service = EndPointsFeatureMappingsService(
                db_async_client=db_async_client)
            for json_obj in endpoints_features_mappings_json:
                await endpoints_feature_mappings_service.create_or_replace_mapping(
                    EndPointsFeatureMappings(**json_obj))
            logger.info(f"updated db with endpoints from json file.")
            return True
        except Exception as e:
            logger.exception(e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Failed to create new user project mapping {e}")

    @staticmethod
    @users_access_control_details_router.post("/v1/sites/{site_id}/get_unmapped_users_for_project",
                                             response_model=UserDetailsResponse)
    async def get_unmapped_users_list_for_project(site_id,
                                            request: GetUnmappedUsersToProjectRequest,
                                            db_async_client: AsyncIOMotorClient = Depends(
                                                get_db_async),token: str = '') -> UserDetailsResponse:
        requesting_user = decodeJWT(token=token)
        try:
            service = UsersProjectsMappingsService(db_async_client=db_async_client)
            results, results_count = await service.get_users_who_are_not_in_project(request.id,
                                                                   search_term=request.search_term,
                                                                   page_number=request.page_number,
                                                                   page_limit=request.page_limit)

            return UserDetailsResponse(succeeded=True,message="successfully fetched unmapped users",
                                       results=results,results_count=results_count)

        except Exception as e:
            logger.exception(f"Failed with exception: {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Failed to fetch users {e}")

    @staticmethod
    @users_access_control_details_router.post("/v1/sites/{site_id}/update_server_based_roles_with_mappings")
    async def update_user_server_roles(site_id, request: UpdateUserRolesRequest, token: str = '',
                                       client: AsyncIOMotorClient = Depends(get_db_async)) -> UpdateUserRolesResponse:
        """
        updates user roles based on input
        """
        try:
            logger.info("attempting update user roles.")
            decoded_token = decodeJWT(token)
            service = UsersProjectsMappingsService(db_async_client=client)
            for i, change in enumerate(request.changes):
                request.changes[i].server_role = ServerBasedRoleNames.get_server_role(change.server_role_value).value
            logger.info(f"requested to change roles for {request.changes}")
            await service.update_user_roles(request.changes, decoded_token["user_id"], delete_existing_mappings=True)
            return UpdateUserRolesResponse(succeeded=True, message="updated these user roles")
        except Exception as e:
            logger.exception(f"updated user server roles failed {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed with exception {e}")
        
    @staticmethod
    @users_access_control_details_router.get("/v1/sites/{site_id}/feature_flags")
    async def get_features(site_id):
        path = environment.get_features_file
        if path:
            with path.open('r') as file:
                data = json.load(file)
        else:
            data = {}
        return data

    @staticmethod
    @users_access_control_details_router.get("/v1/sites/{site_id}/get_all_apps_permissions")
    async def get_all_apps_permissions(site_id: str, client: AsyncIOMotorClient = Depends(get_db_async)) -> List[AppPermission]:
        try:
            service = UsersProjectsMappingsService(db_async_client=client)
            return await service.get_all_apps_permissions()
        except Exception as e:
            error = "get_all_apps_permissions Failed"
            logger.exception(error)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{error} {e}")
    
    @staticmethod
    @users_access_control_details_router.post("/v1/sites/{site_id}/update_app_permission")
    async def update_app_permission(site_id: str, app_perm: EditAppPermission, token: str = '', client: AsyncIOMotorClient = Depends(get_db_async)) -> bool:
        try:
            service = UsersProjectsMappingsService(db_async_client=client)
            dec_token = decodeJWT(token)
            await service.update_app_permission(app_perm, dec_token["user_id"])
            return True
        except Exception as e:
            error = "update_app_permission Failed"
            logger.exception(error)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{error} {e}")
    
    @staticmethod
    @users_access_control_details_router.post("/v1/sites/{site_id}/update_app_permissions")
    async def update_app_permissions(site_id: str, app_perms_list: List[EditAppPermission], token: str = '', client: AsyncIOMotorClient = Depends(get_db_async)) -> bool:
        try:
            service = UsersProjectsMappingsService(db_async_client=client)
            dec_token = decodeJWT(token)
            await service.update_app_permissions(app_perms_list, dec_token["user_id"])
            return True
        except Exception as e:
            error = "update_app_permissions Failed"
            logger.exception(error)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{error} {e}")


users_access_control_details_obj = UsersAccessControlDetailsRouter()
