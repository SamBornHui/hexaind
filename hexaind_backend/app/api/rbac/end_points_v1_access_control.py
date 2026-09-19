from fastapi import Request
from fastapi.routing import APIRoute 
from typing import Callable
from fastapi.responses import JSONResponse
from typing import List
import logging
from functools import cache
import http.client
from fastapi import Request, Response
from pathlib import Path

from app.core.services.jwt_token_utils.jwt_token_utils import decodeJWT
from app.services.access_controls.features.service import EndPointsFeatureMappingsService
from app.services.access_controls.user_projects.service import UsersProjectsMappingsService
from app.services.access_controls.roles.service import RolesFeaturesMapService
from app.services.access_controls.roles.schemas import RolesFeaturesMap
from app.services.admin.authentication.service import AuthenticationService
from app.core.db.db_utils import get_db_sync, get_db_async
from app.services.access_controls.features.schemas import EndPointsFeatureMappings, HTTPEndPointMethodType

logger = logging.getLogger(__package__)

@cache
def get_token_exclusion_endpoints():
    token_excluded_endpoints: List[str] = []
    try:
        endpoints_feature_map_serv = EndPointsFeatureMappingsService(db_sync_client=get_db_sync())
        token_excluded_endpoints = endpoints_feature_map_serv.get_token_excluded_endpoint_method_list()
        logger.info(f"Token Excluded endpoints loaded into cache. Found {len(token_excluded_endpoints)} numbers.")
    except Exception:
        logger.exception("Failed to fetch Token excluded endpoints list form endpoints_feature_mappings collection")
    return token_excluded_endpoints

@cache
def get_endpoint_db_details_list():
    all_endpoint_method_details = {}
    try:
        endpoints_feature_map_serv = EndPointsFeatureMappingsService(db_sync_client=get_db_sync())
        all_endpoint_method_details = endpoints_feature_map_serv.get_all_endpoint_method_details()
        logger.info(f"Endpoints and featurs maps loaded into cache. Found {len(all_endpoint_method_details)} numbers.")
    except Exception:
        logger.exception("Failed to fetch endpoints list form endpoints_feature_mappings collection")
    return all_endpoint_method_details

def is_token_excluded_end_point(endpoint_method:str) -> bool:
    token_excluded_endpoints = get_token_exclusion_endpoints()
    if token_excluded_endpoints:
        return endpoint_method in token_excluded_endpoints
    else:
        return False

def get_endpoint_features(endpoint: str, method: str) ->EndPointsFeatureMappings:
    all_endpoint_method_details = get_endpoint_db_details_list()
    endpoint_method = endpoint+'_'+method
    if endpoint_method in all_endpoint_method_details:
        return all_endpoint_method_details[endpoint_method]
    else:
        return None

def is_subfolder(parent_path: str, child_path: str) -> bool:
    try:
        parent_path = Path(parent_path).resolve()
        child_path = Path(child_path).resolve()
        return parent_path in child_path.parents
    except:
        logger.error(f"Error while trying to resolve the parent child checking with user choice folder{child_path}, Expected Parent:{parent_path}")
        return False

class CheckNameRoute(APIRoute):
   
    def get_route_handler(self)-> Callable:
        original_route_handler = super().get_route_handler()
        async def custom_route_handler(request: Request) -> Response:

            #  Get the End point and method
            request_scope = request.scope
            endpoint = request_scope['route'].path
            method_type = request_scope['method']
            endpoint_method = f"{endpoint}_{method_type}"

            # if the endpoint in exclusion list of Token then continue to execute
            is_excluded = is_token_excluded_end_point(endpoint_method)
            if is_excluded:
                return await original_route_handler(request)
            
            # ignore the end points not available in database
            endpoint_features = get_endpoint_features(endpoint, method_type)
            if endpoint_features is None:
                return await original_route_handler(request)
            
            # if Authorization not present in Header throw error
            if ('authorization' in request.headers) == False:
                return JSONResponse(content={"error": "Not Authorized, Login and attempt again"}, status_code=http.client.FORBIDDEN)
            
            # Check Bearer  Token available, if not throw error
            authorization = request.headers['authorization']
            if not authorization.startswith('Bearer'):
                return JSONResponse(content={"error": "Invalid Authorization"}, status_code=http.client.FORBIDDEN)
            
            # Get the Bearer Token, Check is it valid & un-expired token
            token = request.headers['authorization'].split(' ')[1]
            decoded_token = decodeJWT(token)

            if not decoded_token:
                return JSONResponse(content={"error": "Authorization Expired"}, status_code=http.client.FORBIDDEN)

            await self.update_user_last_activity(decoded_token["email"])

            # assign Bearer Token to query parameter token. the end point can utilize to know the user details
            request.query_params._dict['token'] = token

            # For the Server Level user check, if not then Project Level permissions...
            tmp_server_role_value = decoded_token['server_role_value']

            if tmp_server_role_value in endpoint_features.bypassed_server_roles:
                 return await original_route_handler(request)
            else:
                project_id = await self.get_project_id(request, method_type)
                if project_id is None:
                    return JSONResponse(content={"error": "Not Authorized to use this feature"}, status_code=http.client.CONFLICT)
                else:
                    if await self.user_authorized_for_the_end_point(endpoint,method_type, decoded_token['user_id'], project_id, tmp_server_role_value):
                        return await original_route_handler(request)
                    else:
                        return JSONResponse(content={"error": "Not Authorized at Project Level."}, status_code=http.client.CONFLICT)
                    
        return custom_route_handler
    
    async def update_user_last_activity(self, email: str):
        db_async_client = get_db_async()
        auth_serv = AuthenticationService(db_async_client=db_async_client)
        await auth_serv.update_last_activity_time(email)

    #Get project id from the request parameters if available
    async def get_project_id(self, request: Request, method_type: str):
        methods_have_body = ['POST', 'PUT', 'PATCH', 'DELETE']
        project_id = None
        try:
            if 'project_id' in request.query_params._dict:
                project_id = request.query_params._dict['project_id']
            elif 'projectId' in request.query_params._dict:
                project_id = request.query_params._dict['projectId']
            elif 'project_id' in request.path_params:
                project_id = request.path_params['project_id']
            elif 'projectId' in request.path_params:
                project_id = request.path_params['projectId']

            if (project_id is None or len(project_id.strip()) == 0) and method_type in methods_have_body:
                body_json = await request.json()
                if 'project_id' in body_json:
                    project_id = body_json['project_id']
                elif 'projectId' in body_json:
                    project_id = body_json['projectId']
        except Exception:
            logging.exception("Exception while trying to search for project_id in the request")

        return project_id
    
    def check_access_rights(self, data_dict, access_paths):
        for path in access_paths:
            current_level = data_dict
            valid_path = True
            for key in path:
                # Proceed only if the current level is a dictionary and the key exists
                if isinstance(current_level, dict) and key in current_level:
                    current_level = current_level[key]
                else:
                    valid_path = False
                    break
            if valid_path and current_level is True:
                return True
        return False

    async def user_authorized_for_the_end_point(self, end_point: str, method_: str, user_id: str, project_id:str, server_role_value: int):
        db_async_client = get_db_async()
        user_projs_map_service = UsersProjectsMappingsService(db_async_client=db_async_client)
        mapping = await user_projs_map_service.get_mapping(user_id, project_id)
        roles_feature_map_service = RolesFeaturesMapService(db_async_client=db_async_client)
        roles_feat_map:RolesFeaturesMap = await roles_feature_map_service.get_roles_features_map_by_id(mapping.role_id)
        #features: ProjectBasedFeatures = roles_feat_map.features

        method = HTTPEndPointMethodType[method_]
        end_points_feature_mapping_service = EndPointsFeatureMappingsService(db_async_client=db_async_client)
        obj = await end_points_feature_mapping_service.get_mapping(end_point,method)
        features = obj.features_keys
        return self.check_access_rights(roles_feat_map.features.model_dump(),features)
