from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Tuple
from datetime import datetime, timezone
import logging

from .schemas import Project, CreateNewProjectRequest, UpdateProjectResponse
from .dao import ProjectDao
from app.services.admin.authentication.dao import AuthenticationDao
from .utils import convert_create_new_project_request_to_project

logger = logging.getLogger(__package__)

class ProjectService:

    def __init__(self, db_sync_client: MongoClient = None, db_async_client: AsyncIOMotorClient = None) -> None:
        
        self.project_dao = ProjectDao(db_sync_client=db_sync_client, db_async_client=db_async_client)
        self.auth_dao = AuthenticationDao(db_sync_client=db_sync_client, db_async_client=db_async_client)
        logger.info("Initiated projects dao and authentication dao")

    def is_valid_project(self, project: Project):
        return True

    async def create_new_project_async(self, site_id: str, new_project_request: CreateNewProjectRequest, user_id: str):
        logger.info("inside create project method.")

        project = convert_create_new_project_request_to_project(site_id,
                                                                user_id,
                                                                new_project_request)
        project_administrator = await self.auth_dao.get_user_by_id(new_project_request.project_administrator_id)
        project.owner_name = project_administrator['name']
        # validate project
        if not self.is_valid_project(project):
            raise Exception("Not a valid project")

        project_id = await self.project_dao.create_project_async(project)
        logger.info(f"created project with id {project_id} - need to apply mappings now")

        return project_id

    async def create_project_async(self, siteId: str, project: Project, user_id: str) -> str:
        logger.info("inside create project method.")

        # validate project
        if not self.is_valid_project(project):
            logger.exception("Not a valid project.")
            raise Exception("Not a valid project")
        
        curr_user = await self.auth_dao.get_user_by_id(user_id)

        # updating the record(json body)
        project.site_id = siteId
        project.owner_id = user_id
        project.owner_name = curr_user['name']
        project.created_at = datetime.now(timezone.utc)
        project.last_modified_by_id = user_id
        project.last_modified_at = project.created_at 
        
        project_id = await self.project_dao.create_project_async(project)
        logger.info(f"created project with id {project_id}")

        return project_id
    
    async def get_project_by_id_async(self, project_id: str) -> Project:
        logger.info(f"Getting project based on id {project_id}")

        project = await self.project_dao.get_project_by_id_async(project_id)
        # validate project
        if not self.is_valid_project(project):
            logger.exception("Not a valid project.")
            raise Exception("Not a valid project")
        
        return project
    
    async def get_all_projects_async(self, search_term: str, page_number: int, page_limit: int, user_id: str = None) -> Tuple[List[Project], int]:
        logger.info("getting all the projects.")

        projects, total_count = await self.project_dao.get_all_projects_async(
                                                                                    search_term=search_term,
                                                                                    page_number=page_number,
                                                                                    page_limit=page_limit,
                                                                                    user_id=user_id
                                                                                    )
        logger.info(f"Found {total_count} number of projects.")
        return (projects, total_count)
    
    async def update_project_async(self, project_id: str, project: Project, user_id: str) -> UpdateProjectResponse:
        logger.info("inside update project method.")

        # find the project using project_id
        existing_project = await self.get_project_by_id_async(project_id=project_id)
        logger.info("got existing projects")

        if not existing_project:
            logger.exception("Project not found.")
            raise Exception("Project not found")
        
        # validate the new project
        if not self.is_valid_project(project):
            logger.exception("Not a valid project")
            raise Exception("Not a valid project")
        
        project.last_modified_by_id = user_id
        project.last_modified_at = datetime.now(timezone.utc)
        
        update_flag = await self.project_dao.update_project_async(project_id, project)
        status_msg = f"Updated project. status: {update_flag}"
        logger.info(status_msg)
        return UpdateProjectResponse(success=update_flag, message=status_msg)
    
    async def delete_project_async(self, project_id: str, user_id: str) -> bool:
        logger.info("inside delete project method.")

        # find the project using project_id
        existing_project = await self.get_project_by_id_async(project_id=project_id)
        if not existing_project:
            logger.exception("Project not found")
            raise Exception("Project not found")
        delete_flag = False

        delete_flag = await self.project_dao.delete_project_async(project_id)
        return delete_flag
    
    def get_project_by_id(self, project_id: str) -> Project:
        logger.info("inside get project by id")

        project = self.project_dao.get_project(project_id)
        logger.info("received project.")
        # validate project
        if not self.is_valid_project(project):
            logger.exception("Not a valid project")
            raise Exception("Not a valid project")
        
        return project
    
    async def activate_project_async(self, project_id, user_id: str):
        logger.info("inside activate project async")
        existing_project = await self.get_project_by_id_async(project_id=project_id)
        logger.info("got the project.")
        if not existing_project:
            logger.exception("Project not found")
            raise Exception("Project not found")
        
        update_flag = await self.project_dao.activate_project_async (project_id, user_id)
        logger.info(f"Updated the project. status: {update_flag}")
        return update_flag
    
    async def share_project_to_users(self, project_id: str, user_ids: List[str], user_id: str, is_super_admin: bool):
        logger.info("inside share project to users methods")

        existing_project = await self.get_project_by_id_async(project_id=project_id)
        if not existing_project:
            logger.exception("project not found.")
            raise Exception("Project not found")
        if is_super_admin or user_id == existing_project.owner_id:
            is_shared = await self.project_dao.share_project_to_users(project_id, user_ids)
            logger.info("Shared the project.")
        else:
            logger.exception("You are not the owner of this Project to share with others.")
            raise Exception("You are not the owner of this Project to share with others.")
        
        return is_shared
    
    async def update_favorite(self, project_id: str, is_favorite: bool, user_id: str):
        logger.info("inside update favourite.")
        existing_project = await self.get_project_by_id_async(project_id=project_id)
        if not existing_project:
            logger.exception("Project not found")
            raise Exception("Project not found")
        is_updated = False
        if user_id in existing_project.shared_with or existing_project.owner_id == user_id:
            is_updated = await self.project_dao.update_favorite( project_id, user_id, is_favorite)
            logger.info("Updated the favourite.")
        else:
            logger.exception("User dont have access to the project")
            raise Exception("User dont have access to the project")
        
        return is_updated

    async def update_project_access_datetime(self, project_id: str):
        return await self.project_dao.update_project_access_datetime(project_id)
