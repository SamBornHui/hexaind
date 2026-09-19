from bson import ObjectId
from typing import List, Tuple
from datetime import datetime, timezone
from app.core.dao.dao_base import DaoBase
from app.services.admin.projects.schemas import Project
import logging

logger = logging.getLogger(__package__)

class ProjectDao(DaoBase):

    async def create_project_async(self, project: Project) -> str:

        result = await self.db_async.projects.insert_one(project.model_dump())
        if not result:
            raise Exception("not able to create projects")

        project_id = str(result.inserted_id)

        return project_id

    async def get_project_by_id_async(self, project_id: str) -> Project:

        project = await self.db_async.projects.find_one({"_id": ObjectId(project_id), "is_active": True})
        if not project:
            raise ValueError(f"Active project not found with project_id {project_id}")

        project["_id"] = str(project["_id"])

        return Project(**project)

    async def get_all_projects_async(self, search_term: str, page_number: int, page_limit: int, user_id: str = None) -> Tuple[List[Project], int]:

        query = {}
        is_active_cond = {"is_active": True}
        user_cond = {}
        if user_id:
            user_cond = {"$or": [{"owner_id":user_id}, {"shared_with":user_id}]}

        if search_term:
            search_query = {"$regex": search_term, "$options": "i"} # Case-insensitive search
            search_qry = {}
            search_qry["$or"] = [{"name": search_query}, {"description": search_query},  {"owner_name": search_query}]
            query = {"$and":[is_active_cond, search_qry, user_cond]}
        else:
            query = {"$and": [is_active_cond, user_cond]}

        offset = (page_number - 1) * page_limit if page_number and page_limit else 0

        date_to_str = "$dateToString"
        date_format = "%Y-%m-%dT%H:%M:%S.%LZ"
        projects_cursor = self.db_async.projects.aggregate(
            [
                {"$match": query},
                {'$sort': {'name': 1 }},
                {"$addFields": {"_id": {"$toString": "$_id"},
                                "created_at": {date_to_str: {"format": date_format, "date": "$created_at"}},
                                "last_modified_at": {date_to_str: {"format": date_format, "date": "$last_modified_at"}},
                                "last_accessed_at": {
                                    "$ifNull": [  # If last_accessed_at is null
                                        {date_to_str : {"format": date_format, "date": "$last_accessed_at"}},
                                        {date_to_str : {"format": date_format, "date": "$last_modified_at"}}]
                                    }
                                }},
                {"$skip": offset},
                {"$limit": page_limit}
            ]
        )

        projects = await projects_cursor.to_list(length=page_limit)

        total_count = await self.db_async.projects.count_documents(query)

        return (projects, total_count)

    async def update_project_async(self, project_id: str, project: Project) -> bool:

        # TODO : currently doing selective update only(3-31)
        proj_dump = project.model_dump(include={'name', 'description', 'last_modified_by_id', 'last_modified_at', 'superset_data'})

        result = await self.db_async.projects.find_one_and_update(
            {"_id": ObjectId(project_id)},
            {"$set": proj_dump}
            )
        if result != None:
            return True
        else:
            return False

    async def delete_project_async(self, project_id: str) -> bool:

        result = await self.db_async.projects.update_one({"_id": ObjectId(project_id)}, {"$set":{"is_active": False}})
        if result != None and result.matched_count >0 and result.modified_count > 0:
            return True
        else:
            return False

    def get_project(self, project_id: str) -> Project:

        result = self.db_sync.projects.find_one({"_id": ObjectId(project_id), "is_active": True})

        if not result:
            raise Exception("project not found")

        result["_id"] = str(result["_id"])

        return Project(**result)

    async def activate_project_async(self, project_id: str, user_id: str) -> bool:

        result = await self.db_async.projects.update_one({"_id": ObjectId(project_id)}, {"$set":{"is_active": True, 'last_modified_by_id': user_id, "last_modified_at": datetime.now(timezone.utc)}})

        if result != None and result.matched_count >0 and result.modified_count > 0:
            return True
        else:
            return False

    # TODO: below method might not be required. need to check and cleanup
    async def share_project_to_users(self, project_id: str, user_ids: List[str]):
        if not user_ids or len(user_ids) == 0:
            raise Exception("There is no User IDS provided")

        project = await self.db_async.projects.find_one({"_id": ObjectId(project_id)})
        if not project:
            raise Exception("There is no project with Given id")

        existing_users_set = set(project['shared_with'])
        given_users_set = set(user_ids)
        new_users_list = list(given_users_set - existing_users_set)
        if len(new_users_list) == 0:
            raise Exception("There is no New users list provided to share")

        all_users_list = list(existing_users_set.union(given_users_set))

        result = await self.db_async.projects.update_one({"_id": ObjectId(project_id)}, {"$set": {"shared_with": all_users_list}})

        if result != None and result.matched_count >0 and result.modified_count > 0:
            return True
        else:
            return False

    async def update_favorite(self, project_id: str, user_id: str, is_favorite: bool):
        query = {"_id": ObjectId(project_id), "favorited_by": user_id}
        rec_cnt =  await self.db_async.projects.count_documents(query)
        result = None
        status_matches = False
        if is_favorite:
            if rec_cnt == 0:
                result = await self.db_async.projects.update_one({"_id": ObjectId(project_id)}, {"$addToSet": {"favorited_by": user_id}})
            else:
                status_matches = True
        else:
            if rec_cnt > 0:
                result = await self.db_async.projects.update_one({"_id": ObjectId(project_id)}, {"$pull": {"favorited_by": user_id}})
            else:
                status_matches = True
        if status_matches is True or (result != None and result.matched_count > 0 and result.modified_count > 0):
            return True
        else:
            return False

    async def update_project_access_datetime(self, project_id: str):
        result = await self.db_async.projects.update_one({"_id": ObjectId(project_id)}, {"$set":{"last_accessed_at": datetime.now(timezone.utc)}})
        if result is None or result.matched_count == 0:
            logger.info("Failed to update project access datetime.")
            return False
        else:
            return True


