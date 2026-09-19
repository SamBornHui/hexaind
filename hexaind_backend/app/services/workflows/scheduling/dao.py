from datetime import datetime, timezone
from typing import List, Tuple

from app.core.dao.dao_base import DaoBase
from app.services.workflows.scheduling.schemas import (
    WFSchedule,
    WfScheduleInfo,
)
from bson import ObjectId
import logging
logger = logging.getLogger(__package__)


class ScheduleDao(DaoBase):

    async def create_schedule_async(self, schedule: WFSchedule) -> str:

        result = await self.db_async.scheduling.insert_one(
            schedule.model_dump(exclude={"_id"})
        )
        if not result:
            raise Exception("not able to create schedule")

        schedule_id = str(result.inserted_id)

        return schedule_id

    def get_schedules_triggered_by(self, workflow_id) -> List[WFSchedule]:
        schedules = self.db_sync.scheduling.find(
            {"event_based_config.config.workflow_id": workflow_id}
        )
        results = []
        for schedule in schedules:
            schedule["_id"] = str(schedule["_id"])
            results.append(WFSchedule(**schedule))

        return results

    async def get_schedule_by_id_async(self, schedule_id: str) -> WFSchedule:

        schedule = await self.db_async.scheduling.find_one(
            {"_id": ObjectId(schedule_id)}
        )

        if not schedule:
            raise Exception("WFSchedule not found")

        schedule["_id"] = str(schedule["_id"])

        return WFSchedule(**schedule)

    async def get_schedule_by_workflow_id_async(self, workflow_id: str) -> List[WFSchedule]:

        schedule_cursor = self.db_async.scheduling.find({"workflow_id": workflow_id})
        all_schedules = await schedule_cursor.to_list(length=100)

        if not schedule_cursor:
            raise Exception("WFSchedule not found")
        
        schedules = []
        for schedule in all_schedules:
            schedule["_id"] = str(schedule["_id"])
            schedules.append(WFSchedule(**schedule))
            # logger.info(f"schedule {schedule}")

        logger.info(f"schedules length {len(schedules)}")

        return schedules

    async def fetch_wf_schedules_with_custom_query(
        self, query, page_number: int = 1, page_size=1000
    ) -> Tuple[List[WFSchedule], int]:

        skip = (page_number - 1) * page_size
        total_count = await self.db_async.scheduling.count_documents(query)

        wf_schedules = []
        async for workflow_schedule in (
            self.db_async.scheduling.find(query).skip(skip).limit(page_size)
        ):
            workflow_schedule["_id"] = str(workflow_schedule["_id"])
            wf_schedules.append(WFSchedule(**workflow_schedule))

        return wf_schedules, total_count

    async def get_all_schedule_async(
        self, project_id: str, search_term: str, page_number: int, page_limit: int
    ) -> Tuple[List[WFSchedule], int]:

        query = {"project_id": project_id}

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

        offset = (page_number - 1) * page_limit if page_number and page_limit else 0

        schedule_cursor = self.db_async.scheduling.aggregate(
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

        schedules = await schedule_cursor.to_list(length=page_limit)

        total_count = await self.db_async.scheduling.count_documents(query)

        return (schedules, total_count)

    async def get_schedule_with_runs_and_workflows_async(
        self,
        project_id: str,
        search_term: str,
        page_number: int,
        page_limit: int,
        max_runs_fetch_limit: int = 5,
    ) -> Tuple[List[WfScheduleInfo], int]:

        query = {"project_id": project_id}

        if search_term:
            search_query = {
                "$regex": search_term,
                "$options": "i",  # Case-insensitive search
            }
            query["$or"] = [{"name": search_query}]

        offset = (page_number - 1) * page_limit if page_number and page_limit else 0

        pipeline = [
            {"$match": query},
            {
                "$lookup": {
                    "from": "runs",
                    "let": {"schedule_id": {"$toString": "$_id"}},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$eq": [
                                        "$run_source_details.schedule_id",
                                        "$$schedule_id",
                                    ]
                                }
                            }
                        },
                        {
                            "$project": {
                                "_id": 0,
                                "run_id": {"$toString": "$_id"},
                                "created_at": 1,
                                "run_status": 1,
                            }
                        },
                        {"$limit": max_runs_fetch_limit},
                    ],
                    "as": "run_details",
                }
            },
            {"$unwind": {"path": "$run_details", "preserveNullAndEmptyArrays": True}},
            {
                "$lookup": {
                    "from": "workflows",
                    "let": {"workflow_id": {"$toObjectId": "$workflow_id"}},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$_id", "$$workflow_id"]}}},
                        {
                            "$project": {
                                "_id": 0,
                                "workflow_name": "$name",
                                "workflow_version": "$workflow_version",
                            }
                        },
                    ],
                    "as": "workflow_details",
                }
            },
            {
                "$unwind": {
                    "path": "$workflow_details",
                    "preserveNullAndEmptyArrays": True,
                }
            },
            {
                "$set": {
                    "workflow_name": {
                        "$ifNull": ["$workflow_details.workflow_name", "NotFound"]
                    },
                    "workflow_version": {
                        "$ifNull": ["$workflow_details.workflow_version", "NotFound"]
                    },
                    "run_id": {"$ifNull": ["$run_details.run_id", "Unknown"]},
                    "run_status": {
                        "$ifNull": ["$run_details.run_status", "Unknown"]
                    },  # Include run_status
                    "run_created_at": {
                        "$cond": {
                            "if": {"$eq": ["$run_details.created_at", None]},
                            "then": "",
                            "else": {
                                "$dateToString": {
                                    "format": "%Y-%m-%d %H:%M:%S %z",
                                    "date": "$run_details.created_at",
                                }
                            },
                        }
                    },
                    "schedule_status": {
                        "$cond": {
                            "if": {"$eq": ["$is_active", False]},
                            "then": {
                                "$cond": {
                                    "if": {
                                        "$eq": [
                                            {"$type": "$run_details.run_status"},
                                            "missing",
                                        ]
                                    },
                                    "then": "CANCELED",
                                    "else": {
                                        "$switch": {
                                            "branches": [
                                                {
                                                    "case": {
                                                        "$eq": [
                                                            "$run_details.run_status",
                                                            "IDLE",
                                                        ]
                                                    },
                                                    "then": "RUNNING",
                                                },
                                                {
                                                    "case": {
                                                        "$eq": [
                                                            "$run_details.run_status",
                                                            "RUNNING",
                                                        ]
                                                    },
                                                    "then": "RUNNING",
                                                },
                                                {
                                                    "case": {
                                                        "$eq": [
                                                            "$run_details.run_status",
                                                            "SUCCEEDED",
                                                        ]
                                                    },
                                                    "then": "COMPLETED",
                                                },
                                                {
                                                    "case": {
                                                        "$eq": [
                                                            "$run_details.run_status",
                                                            "FAILED",
                                                        ]
                                                    },
                                                    "then": "FAILED",
                                                },
                                                {
                                                    "case": {
                                                        "$eq": [
                                                            "$run_details.run_status",
                                                            "PAUSED",
                                                        ]
                                                    },
                                                    "then": "RUNNING",
                                                },
                                            ],
                                            "default": "UNKNOWN",
                                        }
                                    },
                                }
                            },
                            "else": {
                                "$cond": {
                                    "if": {
                                        "$eq": [
                                            {"$type": "$run_details.run_status"},
                                            "missing",
                                        ]
                                    },
                                    "then": "SCHEDULED",
                                    "else": {
                                        "$switch": {
                                            "branches": [
                                                {
                                                    "case": {
                                                        "$eq": [
                                                            "$run_details.run_status",
                                                            "IDLE",
                                                        ]
                                                    },
                                                    "then": "SCHEDULED",
                                                },
                                                {
                                                    "case": {
                                                        "$eq": [
                                                            "$run_details.run_status",
                                                            "RUNNING",
                                                        ]
                                                    },
                                                    "then": "RUNNING",
                                                },
                                                {
                                                    "case": {
                                                        "$eq": [
                                                            "$run_details.run_status",
                                                            "SUCCEEDED",
                                                        ]
                                                    },
                                                    "then": "COMPLETED",
                                                },
                                                {
                                                    "case": {
                                                        "$eq": [
                                                            "$run_details.run_status",
                                                            "FAILED",
                                                        ]
                                                    },
                                                    "then": "FAILED",
                                                },
                                                {
                                                    "case": {
                                                        "$eq": [
                                                            "$run_details.run_status",
                                                            "PAUSED",
                                                        ]
                                                    },
                                                    "then": "RUNNING",
                                                },
                                            ],
                                            "default": "UNKNOWN",
                                        }
                                    },
                                }
                            },
                        }
                    },
                }
            },
            # Include all scheduling details
            {
                "$project": {
                    "_id": {"$toString": "$_id"},
                    "dag_id": {"$toString": "$_id"},
                    "name": 1,
                    "project_id": 1,
                    "schedule_interval_metadata": 1,
                    "site_id": 1,
                    "workflow_id": 1,
                    "version": 1,
                    "start_date": 1,
                    "end_date": 1,
                    "scheduled_interval": 1,
                    "schedule_type": 1,
                    "is_active": 1,
                    "dag_file_path": 1,
                    "created_by_id": 1,
                    "created_at": {
                        "$dateToString": {
                            "format": "%Y-%m-%d %H:%M:%S",
                            "date": "$created_at",
                        }
                    },
                    "last_modified_by_id": 1,
                    "last_modified_at": {
                        "$dateToString": {
                            "format": "%Y-%m-%d %H:%M:%S",
                            "date": "$last_modified_at",
                        }
                    },
                    "run_id": 1,
                    "run_status": 1,
                    "run_created_at": 1,
                    "workflow_name": 1,
                    "workflow_version": 1,
                    "schedule_status": 1,
                    "repeat_type": 1,
                    "repeat_value": 1,
                    "cron_week_days": 1,
                    "job_trigger_dt_times": 1,
                }
            },
            {"$skip": offset},
            {"$limit": page_limit},
        ]

        schedule_cursor = self.db_async.scheduling.aggregate(pipeline)
        schedules_with_runs = await schedule_cursor.to_list(length=page_limit)
        schedules_with_runs_info = [
            WfScheduleInfo(**schedule) for schedule in schedules_with_runs
        ]

        # Get the total count of schedules matching the query
        total_count = await self.db_async.scheduling.count_documents(query)

        return schedules_with_runs_info, total_count

    async def update_schedule_async(
        self, schedule_id: str, schedule: WFSchedule
    ) -> bool:

        result = await self.db_async.scheduling.find_one_and_update(
            {"_id": ObjectId(schedule_id)},
            {"$set": schedule.model_dump(exclude={"_id"})},
        )

        if result:
            return True
        else:
            return False

    async def update_file_path_async(self, schedule_id: str, dag_path: str):
        result = await self.db_async.scheduling.find_one_and_update(
            {"_id": ObjectId(schedule_id)}, {"$set": {"dag_file_path": dag_path}}
        )

        if not result:
            raise Exception("Failed to Update the schedules dag path")

    async def update_is_active_async(
        self, schedule_id: str, is_paused: bool, last_modified_id: str
    ):
        result = await self.db_async.scheduling.find_one_and_update(
            {"_id": ObjectId(schedule_id)},
            {
                "$set": {
                    "is_active": not is_paused,
                    "last_modified_by_id": last_modified_id,
                    "last_modified_at": datetime.now(timezone.utc),
                }
            },
        )

        if not result:
            raise Exception("Failed to Update the pause status")

        return result

    async def delete_schedule_async(self, schedule_id: str) -> bool:

        result = await self.db_async.scheduling.delete_one(
            {"_id": ObjectId(schedule_id)}
        )

        return result.deleted_count > 0
