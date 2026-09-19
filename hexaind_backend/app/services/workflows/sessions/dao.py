from bson import ObjectId
from typing import List, Tuple
from typing import List
from datetime import datetime, timezone

from fastapi import HTTPException
from app.core.dao.dao_base import DaoBase
from .schemas import WorkflowSessionDB, SavedWorkflowsFromSession


class WorkflowSessionDao(DaoBase):

    async def cerate_workflow_session_async(
        self, workflow_session_obj: WorkflowSessionDB
    ) -> str:
        """
        creating new session object record in db
        """

        result = await self.db_async.workflow_sessions.insert_one(
            workflow_session_obj.model_dump()
        )
        if not result:
            raise Exception("Unable to create workflow session")

        session_id = str(result.inserted_id)

        return session_id

    async def is_session_present_async(self, session_id: str) -> bool:

        session = await self.db_async.workflow_sessions.find_one(
            {"_id": ObjectId(session_id)}
        )
        return False if not session else True

    def is_session_present(self, session_id: str) -> bool:

        session = self.db_sync.workflow_sessions.find_one(
            {"_id": ObjectId(session_id)}
        )
        return False if not session else True

    async def get_workflow_session_async(self, session_id: str) -> WorkflowSessionDB:

        workflow_session = await self.db_async.workflow_sessions.find_one(
            {"_id": ObjectId(session_id)}
        )

        if not workflow_session:
            raise Exception("workflow-session not found")

        workflow_session["_id"] = str(workflow_session["_id"])

        workflow_session = WorkflowSessionDB(**workflow_session)

        return workflow_session

    def get_workflow_session(self, session_id: str) -> WorkflowSessionDB:

        workflow_session = self.db_sync.workflow_sessions.find_one(
            {"_id": ObjectId(session_id)}
        )

        if not workflow_session:
            raise Exception("workflow-session not found")

        workflow_session["_id"] = str(workflow_session["_id"])

        workflow_session = WorkflowSessionDB(**workflow_session)

        return workflow_session

    async def check_existing_published_workflow_in_session_async(
        self, session_id: str, workflow_name: str, workflow_version_tag: str
    ) -> bool:

        existing_record = await self.db_async.workflow_sessions.find_one(
            {
                "_id": ObjectId(session_id),
                "saved_workflows": {
                    "$elemMatch": {
                        "name": {
                            "$regex": f"^{workflow_name}$",
                            "$options": "i",
                        },  # Case-insensitive match for name
                        "workflow_version": {
                            "$regex": f"^{workflow_version_tag}$",
                            "$options": "i",
                        },  # Case-insensitive match for version
                    }
                },
            }
        )

        return True if existing_record else False

    async def update_session_record_with_latest_published_workflow(
        self, session_id: str, saveas_workflow: SavedWorkflowsFromSession
    ) -> bool:

        updated = await self.db_async.workflow_sessions.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$push": {
                    "saved_workflows": saveas_workflow.model_dump(
                        exclude={
                            "last_modified_by",
                            "last_modified_at",
                            "created_at",
                            "created_by",
                            "last_run_status",
                            "last_run_at",
                        }
                    )
                }
            },
        )

        return updated.modified_count > 0

    async def get_all_workflow_sessions_async(
        self, projectId: str, search_term: str, page_number: int, page_limit: int
    ) -> Tuple[List[WorkflowSessionDB], int]:

        offset = (page_number - 1) * page_limit
        query = {"project_id": projectId}

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

        workflow_session_cursor = self.db_async.workflow_sessions.aggregate(
            [
                {"$match": query},
                {
                    "$addFields": {
                        "_id": {"$toString": "$_id"},
                        "created_at": {
                            "$dateToString": {
                                "format": "%Y-%m-%dT%H:%M:%S.%LZ",
                                "date": "$created_at",
                            }
                        },
                        "last_modified_at": {
                            "$dateToString": {
                                "format": "%Y-%m-%dT%H:%M:%S.%LZ",
                                "date": "$last_modified_at",
                            }
                        },
                    }
                },
                {"$skip": offset},
                {"$limit": page_limit},
            ]
        )

        workflow_sessions = await workflow_session_cursor.to_list(length=page_limit)

        workflow_session_db_records = [
            WorkflowSessionDB(**workflow_session)
            for workflow_session in workflow_sessions
        ]

        total_count = await self.db_async.workflow_sessions.count_documents(query)

        return workflow_session_db_records, total_count
    
    async def get_all_workflow_templates_async(
        self, projectId: str, search_term: str, page_number: int, page_limit: int
    ) -> Tuple[List[WorkflowSessionDB], int]:

        offset = (page_number - 1) * page_limit
        query = {"project_id": projectId,  "is_template": True}

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

        workflow_session_cursor = self.db_async.workflow_sessions.aggregate(
            [
                {"$match": query},
                {
                    "$addFields": {
                        "_id": {"$toString": "$_id"},
                        "created_at": {
                            "$dateToString": {
                                "format": "%Y-%m-%dT%H:%M:%S.%LZ",
                                "date": "$created_at",
                            }
                        },
                        "last_modified_at": {
                            "$dateToString": {
                                "format": "%Y-%m-%dT%H:%M:%S.%LZ",
                                "date": "$last_modified_at",
                            }
                        },
                    }
                },
                {"$skip": offset},
                {"$limit": page_limit},
            ]
        )

        workflow_sessions = await workflow_session_cursor.to_list(length=page_limit)

        workflow_session_db_records = [
            WorkflowSessionDB(**workflow_session)
            for workflow_session in workflow_sessions
        ]

        total_count = await self.db_async.workflow_sessions.count_documents(query)

        return workflow_session_db_records, total_count

    async def delete_workflow_session_async(self, session_id: str) -> bool:

        result = await self.db_async.workflow_sessions.delete_one(
            {"_id": ObjectId(session_id)}
        )

        if result.deleted_count != 1:
            raise Exception("Session not found")

        return True

    async def update_workflow_session_async(
        self, workflow_session_id: str, workflow_session_obj: WorkflowSessionDB
    ) -> bool:

        result = await self.db_async.workflow_sessions.find_one_and_update(
            {"_id": ObjectId(workflow_session_id)},
            {"$set": workflow_session_obj.model_dump(
                exclude={
                            "last_run_status",
                            "last_run_at",
                        }
            )},
            return_document=True,
        )

        if not result:
            raise Exception("failed to update the workflow-session")

        return True

    async def get_session_from_workflow_async(
        self, published_workflow_id: str
    ) -> WorkflowSessionDB:
        existing_records = self.db_async.workflow_sessions.find(
            {
                "saved_workflows.workflow_id": published_workflow_id,
            }
        )
        session_records = await existing_records.to_list(length=None)
        if len(session_records) != 1:
            raise Exception(
                f"Found 0 or more than 1 session for the given workflow. Count: {len(session_records)} - workflow_id: {published_workflow_id}",
            )
        session_records[0]["_id"] = str(session_records[0]["_id"])
        return WorkflowSessionDB(**session_records[0])

    def get_session_from_workflow(
        self, published_workflow_id: str
    ) -> WorkflowSessionDB:
        existing_records = list(
            self.db_sync.workflow_sessions.find(
                {
                    "saved_workflows.workflow_id": published_workflow_id,
                }
            )
        )
        if len(existing_records) == 0:
            existing_records = list(
                self.db_sync.workflow_sessions.find(
                    {
                        "workflow_id": published_workflow_id,
                    }
                )
            )
        session_records = existing_records
        if len(session_records) != 1:
            raise Exception(
                f"Found 0 or more than 1 session for the given workflow. Count: {len(session_records)} - workflow_id: {published_workflow_id}",
            )
        session_records[0]["_id"] = str(session_records[0]["_id"])
        return WorkflowSessionDB(**session_records[0])

    async def update_favourite_workflow(self, favourite_value, workflow_id):
        result = await self.db_async.workflow_sessions.find_one_and_update(
                {"_id": ObjectId(workflow_id) },
                favourite_value,
                return_document = True
                )
        