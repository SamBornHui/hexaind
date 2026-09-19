import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import logging

from app.services.access_controls.roles.schemas import SystemGeneratedProjectRoles
from app.services.access_controls.roles.service import RolesFeaturesMapService
from app.services.access_controls.user_projects.service import UsersProjectsMappingsService
from app.services.admin.projects.schemas import Project, CreateNewProjectResponse, CreateNewProjectRequest
from app.core.db.db_utils import get_db_async
from motor.motor_asyncio import AsyncIOMotorClient
from app.services.admin.projects.service import ProjectService
from app.services.admin.projects.schemas import CreateProjectResponse, ProjectListResponse, UpdateProjectResponse, \
    DeleteProjectResponse
from app.core.services.jwt_token_utils.jwt_token_utils import JWTBearer, decodeJWT
from app.api.rbac.end_points_v1_access_control import CheckNameRoute

logger = logging.getLogger(__package__)
projects_router = APIRouter(tags=['Projects'], route_class=CheckNameRoute)

class ProjectsRouter:

    def __init__(self):
        pass

    @staticmethod
    @projects_router.post('/v1/sites/{site_id}/create_new_project_with_user_mappings',
                          response_model=CreateNewProjectResponse)
    async def create_new_project(site_id: str,
                                 new_project_request: CreateNewProjectRequest,
                                 client: AsyncIOMotorClient = Depends(get_db_async),
                                 token: str = '') -> CreateNewProjectResponse:
        try:
            logger.info(f"Inside create project method. Project: {new_project_request}")

            project_handler = ProjectService(db_async_client=client)
            users_projects_mappings_service = UsersProjectsMappingsService(db_async_client=client)
            token = decodeJWT(token)

            if new_project_request.project_administrator_id is None or new_project_request.project_administrator_id.strip() == '':
                    new_project_request.project_administrator_id = token['user_id']

            project_id = await project_handler.create_new_project_async(site_id=site_id,
                                                                        new_project_request=new_project_request,
                                                                        user_id=token['user_id'])
            logger.info(f"Created project with project_id {project_id}")

            # add project_admin to maps
            roles_feature_service = RolesFeaturesMapService(db_async_client=client)
            custom_msg = ""
            try:
                users_list = await users_projects_mappings_service.get_users_dict(users_list=[token['user_id']])
                user = users_list[token['user_id']]
                if user.server_role_value != 1:
                    logger.info("Creating project administrator mapping as user is not a server admin.")
                    administrator_role = str(SystemGeneratedProjectRoles.PROJECT_ADMINISTRATOR.value)
                    project_administrator_role = await roles_feature_service.get_roles_features_map_by_name(
                        administrator_role)
                    
                    await users_projects_mappings_service.create_new_mapping(token['user_id'],
                                                                            new_project_request.project_administrator_id,
                                                                            project_id, project_administrator_role.id)
                else:
                    logger.info("Not creating the project administrator mapping as user is a server admin.")
                    
            except Exception as e:
                logger.exception(f"Created project. Error while mapping(so project can be only by server admin).{e}")
                custom_msg = "Mappings not formed properly(project can accessed only by server admin)"

            # TODO: once user mappings are sent mapp them here
            logger.info(f"Created project with project_id {project_id} with mappings")

            return CreateNewProjectResponse(succeeded=True, message=f"project created successfully. {custom_msg}",
                                            project_id=project_id)

        except Exception as e:
            logger.exception(f"Unable to create new project {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed with exception {e}"
            )

    @projects_router.post('/v1/sites/{siteId}/projects', response_model=CreateProjectResponse)
    async def create_project(siteId: str,
                             project: Project,
                             client: AsyncIOMotorClient = Depends(get_db_async),
                             token: str = '') -> CreateProjectResponse:
        try:
            logger.info(f"Inside create project method. Project: {project}")
            project_handler = ProjectService(db_async_client=client)
            token = decodeJWT(token)
            project_id = await project_handler.create_project_async(project=project, siteId=siteId,
                                                                    user_id=token['user_id'])
            logger.info(f"Created project with project_id {project_id}")

            return CreateProjectResponse(project_id=project_id)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}"
            )

    @projects_router.get('/v1/sites/{siteId}/projects/{projectId}', response_model=Project)
    async def get_project(siteId: str,
                          projectId: str,
                          client: AsyncIOMotorClient = Depends(get_db_async),
                          token: str = '') -> Project:

        try:
            logger.info(f"Inside get project by id.")

            project_service = ProjectService(db_async_client=client)
            project = await project_service.get_project_by_id_async(projectId)
            logger.info("Found project with given id.")

            if not project:
                logger.error("Project not found.", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project not found"
                )

            return project

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed with exception {e}"
            )

    @projects_router.get('/v1/sites/{siteId}/projects', response_model=ProjectListResponse)
    async def get_all_projects(siteId: str,
                               search_term: str = None,
                               page_number: int = 1,
                               page_limit: int = 100,
                               user_id: str = None,
                               client: AsyncIOMotorClient = Depends(get_db_async), token: str = '') -> \
    List[Project]:
        try:
            logger.info("inside get all projects.")
            project_service = ProjectService(db_async_client=client)
            projects, total_count = await project_service.get_all_projects_async(search_term=search_term,
                                                                                 page_number=page_number,
                                                                                 page_limit=page_limit,
                                                                                 user_id=user_id
                                                                                 )
            logger.info(f"got all the projects. total projects: {total_count}")

            return ProjectListResponse(projects=projects, total_count=total_count)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed with exception {e}"
            )

    @projects_router.patch('/v1/sites/{siteId}/projects/{projectId}', response_model=UpdateProjectResponse)
    async def update_project(siteId: str, projectId: str, project: Project,
                             client: AsyncIOMotorClient = Depends(get_db_async),
                             token: str = '') -> UpdateProjectResponse:
        try:
            logger.info("inside update project method.")
            project_handler = ProjectService(db_async_client=client)
            decoded_token = decodeJWT(token)
            update_proj_resp = await project_handler.update_project_async(projectId, project, decoded_token['user_id'])
            logger.info(f"updated project with update flag: {update_proj_resp.success}")
            return update_proj_resp

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}"
            )

    @projects_router.delete('/v1/sites/{siteId}/projects/{projectId}', response_model=DeleteProjectResponse)
    async def delete_project(siteId: str,
                             projectId: str,
                             client: AsyncIOMotorClient = Depends(get_db_async),
                             token: str = '') -> DeleteProjectResponse:

        try:
            logger.info("inside delete project method.")
            project_service = ProjectService(db_async_client=client)
            token = decodeJWT(token)
            delete_flag = await project_service.delete_project_async(projectId, token['user_id'])
            delete_resp_msg = f"deleted the selected project with flag {delete_flag}"
            logger.info(delete_resp_msg)
            return DeleteProjectResponse(success=delete_flag, message=delete_resp_msg)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}"
            )

    @projects_router.post('/v1/sites/{siteId}/projects/{projectId}', response_model=UpdateProjectResponse)
    async def activate_project(siteId: str,
                               projectId: str,
                               client: AsyncIOMotorClient = Depends(get_db_async),
                               token: str = '') -> UpdateProjectResponse:
        try:
            logger.info("inside activate project method.")
            project_service = ProjectService(db_async_client=client)
            token = decodeJWT(token)
            update_flag = await project_service.activate_project_async(projectId, token['user_id'],
                                                                       int(token['server_role_value']))
            logger.info(f"Activated the selected project with flag {update_flag}")

            return UpdateProjectResponse(success=update_flag)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}"
            )

    @projects_router.post('/v1/sites/{siteId}/shareProject/{projectId}', response_model=UpdateProjectResponse)
    async def share_project(siteId: str,
                            projectId: str,
                            user_ids: List[str],
                            client: AsyncIOMotorClient = Depends(get_db_async),
                            token: str = '') -> UpdateProjectResponse:
        try:
            logger.info("inside share project method.")
            project_service = ProjectService(db_async_client=client)
            token = decodeJWT(token)
            update_flag = await project_service.share_project_to_users(projectId, user_ids, token['user_id'],
                                                                       int(token['server_role_value']) & 3 > 0)
            logger.info(f"Shared the selected project with flag {update_flag}")

            return UpdateProjectResponse(success=update_flag)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}"
            )

    @projects_router.post('/v1/sites/{siteId}/updateFavoriteProject/{projectId}', response_model=UpdateProjectResponse)
    async def update_favorite_project(siteId: str,
                                      projectId: str,
                                      is_favorite: bool,
                                      client: AsyncIOMotorClient = Depends(get_db_async),
                                      token: str = '') -> UpdateProjectResponse:
        try:
            logger.info("inside share project method.")
            project_service = ProjectService(db_async_client=client)
            token = decodeJWT(token)
            update_flag = await project_service.update_favorite(projectId, is_favorite, token['user_id'])
            logger.info(f"Updated favourite for  selected project {projectId} with flag {update_flag}")

            return UpdateProjectResponse(success=update_flag)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}"
            )

    @staticmethod
    @projects_router.patch('/v1/sites/{site_id}/update_last_update_at/{project_id}', response_model=bool)
    async def update_last_update_at(project_id: str,
                                    client: AsyncIOMotorClient = Depends(get_db_async)) -> bool:
        try:
            logger.info("inside last updated at of  project method.")
            project_service = ProjectService(db_async_client=client)
            update_flag = await project_service.update_project_access_datetime(project_id)
            logger.info(f"Updated Last Accessed at for  selected project {project_id} - result{update_flag}")
            return update_flag
        except Exception as e:
            logger.exception(f"Faild to update last accessed at on project{project_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}"
            )


projects_router_obj = ProjectsRouter()
