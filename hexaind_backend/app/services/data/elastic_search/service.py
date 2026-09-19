from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from elasticsearch import Elasticsearch
from app.config.env_vars import ElasticEnvironment

from app.services.data.elastic_search.schemas import LogsResponse, LogEntry
from app.services.workflows.sessions.service import WorkflowSessionService
from app.services.workflows.runner.service import RunService
from app.services.workflows.runner.schemas import Run
from app.services.workflows.actions.service import ActionServiceNew
from app.core.services.action.schemas import Action


class ElasticSearchLogRetrievalService:
    def __init__(
        self,
        db_sync_client: MongoClient = None,
        db_async_client: AsyncIOMotorClient = None,
    ) -> None:
        elastic_environment = ElasticEnvironment()  # type: ignore

        self.elastic_server_connection = Elasticsearch(
            [str(elastic_environment.url)],
            basic_auth=(elastic_environment.username, elastic_environment.password),
            verify_certs=False,
        )

        self.workflow_session_service = WorkflowSessionService(
            db_async_client=db_async_client
        )

        self.run_service = RunService(db_async_client=db_async_client)

        self.action_service = ActionServiceNew(db_async_client=db_async_client)

    async def get_widget_activity_log_in_session(
        self,
        session_id: str,
        widget_urn: str,
        size: int,
        cursor_timestamp: str,
        cursor_record_id: str,
    ) -> LogsResponse:
        session_record = await self.workflow_session_service.get_workflow_session_async(
            session_id=session_id
        )

        action_record: Action = await self.action_service.get_action_by_urn_async(
            run_id=session_record.run_id, urn=widget_urn
        )

        run_record: Run = await self.run_service.get_run_by_id_async(
            run_id=session_record.run_id
        )

        # preparing the query body, NOTE: don't include search_after in search_body directly, it will throw an error
        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"hexaind3.run_id": session_record.run_id}},
                        {"match": {"hexaind3.action_id": action_record.id}},
                        {
                            "match": {
                                "hexaind3.recent_run": run_record.recent_run_created_at.isoformat()[
                                    :-3
                                ]
                                + "Z"
                            }
                        },
                        {"match": {"hexaind3.widget_urn": widget_urn}},
                    ]
                }
            },
            "sort": [{"@timestamp": "asc"}, {"_id": "asc"}],
        }

        if cursor_timestamp and cursor_record_id:
            search_body["search_after"] = [cursor_timestamp, cursor_record_id]

        # execute the query
        response = self.elastic_server_connection.search(
            index="logs-*", size=size, body=search_body
        )

        logs, new_cursor_timestamp, new_cursor_id = [], None, None

        # Extract desired fields from each log entry
        logs = [
            LogEntry(
                time=hit["_source"]["@timestamp"],
                log_level=hit["_source"]["hexaind3"]["levelname"],
                message=hit["_source"]["hexaind3"]["message"],
                exc_info=hit["_source"].get("hexaind3", {}).get("exc_info", "N/A"),
            )
            for hit in response["hits"]["hits"]
        ]

        # Update cursors if there are hits
        if response["hits"]["hits"]:
            last_hit = response["hits"]["hits"][-1]
            new_cursor_timestamp = last_hit["_source"]["@timestamp"]
            new_cursor_id = last_hit["_id"]

        return LogsResponse(
            logs=logs,
            new_cursor_timestamp=new_cursor_timestamp,
            new_cursor_id=new_cursor_id,
        )

    async def widget_activity_log_in_workflow_run(
        self,
        run_id: str,
        widget_urn: str,
        size: int,
        cursor_timestamp: str,
        cursor_record_id: str,
    ) -> LogsResponse:
        action_record: Action = await self.action_service.get_action_by_urn_async(
            run_id=run_id, urn=widget_urn
        )

        # preparing the query body, NOTE: don't include search_after in search_body directly, it will throw an error
        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"hexaind3.run_id": run_id}},
                        {"match": {"hexaind3.action_id": action_record.id}},
                        {"match": {"hexaind3.widget_urn": widget_urn}},
                    ]
                }
            },
            "sort": [{"@timestamp": "asc"}, {"_id": "asc"}],
        }

        if cursor_timestamp and cursor_record_id:
            search_body["search_after"] = [cursor_timestamp, cursor_record_id]

        # execute the query
        response = self.elastic_server_connection.search(
            index="logs-*", size=size, body=search_body
        )

        logs, new_cursor_timestamp, new_cursor_id = [], None, None

        # Extract desired fields from each log entry
        logs = [
            LogEntry(
                time=hit["_source"]["@timestamp"],
                log_level=hit["_source"]["hexaind3"]["levelname"],
                message=hit["_source"]["hexaind3"]["message"],
                exc_info=hit["_source"].get("hexaind3", {}).get("exc_info", "N/A"),
            )
            for hit in response["hits"]["hits"]
        ]

        # Update cursors if there are hits
        if response["hits"]["hits"]:
            last_hit = response["hits"]["hits"][-1]
            new_cursor_timestamp = last_hit["_source"]["@timestamp"]
            new_cursor_id = last_hit["_id"]

        return LogsResponse(
            logs=logs,
            new_cursor_timestamp=new_cursor_timestamp,
            new_cursor_id=new_cursor_id,
        )
