import logging
from datetime import datetime, timezone
from email.policy import default
from typing import List, Tuple, Dict, Optional, Callable

import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from app.services.admin.connectors.schemas import (
    BigQueryAuthentication,
    BigQueryAuthType,
    BigQueryBrowserAuth,
    BigQueryConnectorConfiguration,
    BigQueryDefaultAuth,
    BigQueryServiceAccount,
    BigQueryServiceAccountConfig,
    BigQueryUserAuthConfig,
    Connector,
    CreateQueryRequest,
    Query,
    UpdateQueryRequest,
)

from app.services.admin.connectors.service import ConnectorService
from app.services.data.assets.datasets.dao import DatasetsDao
from app.services.workflows.runner.dao import RunDao
from app.services.data.bigquery.big_query_executor import (
    BqExecutorHelper,
    BqTableExecutorHelper,
    get_big_query_executor,
)
from app.services.data.bigquery.dao import BigQueryDao
from app.services.data.bigquery.dynamic_query_params_processing import (
    process_query_parameters,
)
from app.services.data.bigquery.schemas import (
    DryRunResponseModel,
    PreviewObj,
    SchemaField,
    SchemaFieldType,
    QueryParam,
)
from app.services.workflows.designer.schemas import (
    BigQueryDatasetConfiguration,
    BigQueryDatasetType,
    DataCopyActivityConfig,
)

from app.services.workflows.runner.schemas import Run

from .utils import (
    download_bigquery_data_using_service_account,
    download_bigquery_data_using_user_account,
)

logger = logging.getLogger(__package__)


class BigQueryService:

    def __init__(
        self,
        db_sync_client: MongoClient = None,
        db_async_client: AsyncIOMotorClient = None,  # type: ignore
    ) -> None:

        self.datasets_dao = DatasetsDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )
        self.bigquery_dao = BigQueryDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )

    def bigquery_data_copy_handler(
        self,
        bigquery_connector_obj: Connector,
        bigquery_config: DataCopyActivityConfig,
        dest_path: str,
    ):
        configuration = bigquery_connector_obj.configuration
        dataset_configuration = (
            bigquery_config.source.configuration.dataset_configuration
        )
        connection = BigQueryService.connection(configuration)
        job_config = bigquery.QueryJobConfig(dry_run=False)

        dataset = dataset_configuration.dataset
        queries = []
        match dataset_configuration.dataset_type:
            case BigQueryDatasetType.TABLE:
                query = f"SELECT * FROM `{configuration.authentication_details.project_id}.{dataset.dataset_name}.{dataset.table_name}`"
                queries = [query]

            case BigQueryDatasetType.QUERY:
                query = dataset.query
                queries = process_query_parameters(config=dataset)
            case _:
                raise NotImplementedError(
                    "Requested method is not implemented at this moment."
                )

        if not queries:
            raise ValueError("No Queries found.")
        df = None
        for query in queries:
            query_job = connection.query(query, job_config=job_config)
            results = query_job.result()  # Waits for the query to finish

            # Convert to DataFrame
            pdf = results.to_dataframe()
            if df is None:
                df = pdf
            else:
                df = pd.concat([df, pdf])

        df.to_csv(dest_path)

        return dest_path

    def bigquery_dryrun(
        self,
        bigquery_connector_config: BigQueryConnectorConfiguration,
        bigquery_config: BigQueryDatasetConfiguration,
    ):

        kwargs = {
            "auth_info": bigquery_connector_config.authentication_details.model_dump()
        }
        bq_executor = get_big_query_executor(
            bigquery_connector_config.authentication_type, kwargs
        )

        if (
            bigquery_config.dataset_configuration.dataset_type
            == BigQueryDatasetType.TABLE
        ):
            dataset_name = bigquery_config.dataset_configuration.dataset.dataset_name
            table_name = bigquery_config.dataset_configuration.dataset.table_name
            executor_helper = BqTableExecutorHelper(
                bq_executor, table_id=table_name, dataset_id=dataset_name
            )
        elif (
            bigquery_config.dataset_configuration.dataset_type
            == BigQueryDatasetType.QUERY
        ):
            query = bigquery_config.dataset_configuration.dataset.query
            executor_helper = BqExecutorHelper(bq_executor, query)
        else:
            raise ValueError("Unknown value for BigQueryDatasetType")

        results_schema, total_bytes_processed = executor_helper.dryrun()

        fields = [
            SchemaField(
                name=item.name,
                field_type=SchemaFieldType.from_bigquery_type(item.field_type),
            )
            for item in results_schema
        ]

        return DryRunResponseModel(fields=fields, size=total_bytes_processed)

    @staticmethod
    def connection(config: BigQueryConnectorConfiguration) -> bigquery.Client:
        match config.authentication_details:
            case BigQueryServiceAccountConfig() as service_config:
                credentials = service_account.Credentials.from_service_account_info(
                    service_config.model_dump(),
                    scopes=["https://www.googleapis.com/auth/cloud-platform"],
                )

            case BigQueryUserAuthConfig() as user_config:
                credentials = Credentials.from_authorized_user_info(
                    user_config.model_dump(),
                    token_uri="https://oauth2.googleapis.com/token",
                )

            case _:
                raise NotImplementedError(
                    "Requested method is not implemented at this moment."
                )

        return bigquery.Client(
            credentials=credentials,
            project=credentials.project_id,
        )

    def bigquery_authenticate(self, config: BigQueryAuthentication) -> bool:

        try:
            conn = None
            match config.root:
                case BigQueryServiceAccount() as service_config:
                    credentials = service_account.Credentials.from_service_account_info(
                        service_config.auth_object.model_dump(),
                        scopes=["https://www.googleapis.com/auth/cloud-platform"],
                    )
                    conn = bigquery.Client(
                        credentials=credentials,
                        project=credentials.project_id,
                    )
                case BigQueryDefaultAuth() as default_config:
                    conn = bigquery.Client(default_config.gcp_project_id)

                case BigQueryBrowserAuth() as browser_config:
                    conn = bigquery.Client(browser_config.gcp_project_id)

                case _:
                    raise NotImplementedError(
                        f"This authentication {config} is not implemented."
                    )

            return conn is not None

        except NotImplementedError as e:
            print(f"This authentication {config.root} is not implemented.")
            raise e

        except Exception as e:
            return False

    def get_connection_with_connector(self, connector: Connector):

        match connector.configuration.authentication_type:
            case BigQueryAuthType.SERVICE_ACCOUNT:
                service_auth_details: BigQueryServiceAccountConfig = (
                    connector.configuration.authentication_details
                )
                credentials_obj = service_account.Credentials.from_service_account_info(
                    service_auth_details.model_dump(),
                    scopes=["https://www.googleapis.com/auth/cloud-platform"],
                )

                conn = bigquery.Client(
                    credentials=credentials_obj,
                    project=credentials_obj.project_id,
                )

            case BigQueryAuthType.USER_AUTH:
                user_auth_details: BigQueryUserAuthConfig = (
                    connector.configuration.authentication_details
                )
                credentials_obj = Credentials.from_authorized_user_info(
                    {
                        "client_id": user_auth_details.client_id,
                        "client_secret": user_auth_details.client_secret,
                        "refresh_token": user_auth_details.refresh_token,
                        "token_uri": "https://oauth2.googleapis.com/token",
                    }
                )

                conn = bigquery.Client(
                    credentials=credentials_obj, project=user_auth_details.project_id
                )
        return conn

    async def bigquery_dataset_list(self, connector: Connector, project_id: str):

        try:
            conn = self.get_connection_with_connector(connector)
            datasets = conn.list_datasets(project_id)
            datasets_list = []

            if datasets:
                for dataset in datasets:
                    datasets_list.append(dataset.dataset_id)
            else:
                raise ValueError(f"No datasets found in  {project_id}")

            return datasets_list

        except Exception as e:
            return str(e)

    async def bigquery_table_list(
        self, connector: Connector, project_id: str, dataset_name: str
    ):

        try:
            conn = self.get_connection_with_connector(connector)

            tables_list = []

            dataset_id = str(project_id + "." + dataset_name)

            tables = conn.list_tables(dataset_id)

            if tables:
                for table in tables:

                    tables_list.append(table.table_id)

            else:
                raise ValueError(f"No tables found in  {dataset_name}")

            return tables_list

        except Exception as e:
            return str(e)

    async def bigquery_data_preview(
        self, connector: Connector, project_id: str, config: PreviewObj
    ):

        conn = self.get_connection_with_connector(connector)

        if not config.query_config:
            queries = [
                f"SELECT * FROM `{project_id}.{config.dataset_name}.{config.table_name}` LIMIT 20"
            ]
        else:
            # Check if query already contains LIMIT clause (case-insensitive)
            if not any(word.lower() == "limit" for word in config.query_config.query.split()):
                config.query_config.query = f"{config.query_config.query} LIMIT 20"
            queries = process_query_parameters(config=config.query_config)
        query_job = conn.query(query=queries[0])
        results = query_job.result()
        data_preview = []
        for row in results:
            row_dict = dict(row.items())
            data_preview.append(row_dict)

        columns = list(data_preview[0].keys())
        data = [[row[column] for column in columns] for row in data_preview]

        return columns, data

    async def create_query_async(
        self,
        site_id: str,
        project_id: str,
        user_id: str,
        user_name: str,
        query_data: CreateQueryRequest,
    ) -> str:
        logger.info("Inside create query_data.")

        new_query = Query(
            name=query_data.name,
            query=query_data.query,
            connector_id=query_data.connector_id,
            owner_id=user_id,
            owner_name=user_name,
            created_at=datetime.now(timezone.utc),
            last_modified_by_id=user_id,
            last_modified_at=datetime.now(timezone.utc),
            project_id=project_id,
            site_id=site_id,
            query_params=query_data.query_params,
            query_type=query_data.query_type,
        )

        query_id = await self.bigquery_dao.create_query_async(new_query)
        logger.info(f"Created the Query with query_data id {query_id}")

        return query_id

    async def get_query_by_id_async(self, query_id: str):
        logger.info("returning the fetched query")

        return await self.bigquery_dao.get_query_by_id_async(query_id=query_id)

    async def update_query_async(self, user_id: str, query_data: UpdateQueryRequest):

        query_record = await self.get_query_by_id_async(query_id=query_data.query_id)
        query_record.query_params = query_data.query_params
        query_record.query = query_data.query
        query_record.last_modified_at = datetime.now(timezone.utc)
        query_record.last_modified_by_id = user_id

        result = await self.bigquery_dao.update_query_async(
            query_id=query_data.query_id, query=query_record
        )
        logger.info("Updated query succesfully")

        return result

    async def get_all_queries_async(
        self, project_id: str, search_term: str, page_number: int, page_limit: int
    ) -> Tuple[List[Query], int]:
        logger.info("inside get all queries.")

        queries, total_count = await self.bigquery_dao.get_all_queries_async(
            project_id=project_id,
            search_term=search_term,
            page_number=page_number,
            page_limit=page_limit,
        )
        logger.info(f"Retrieved all the queries from db. total count: {total_count}")
        return (queries, total_count)

    async def delete_query_async(self, query_id: str) -> bool:
        existing_query = await self.bigquery_dao.get_query_by_id_async(
            query_id=query_id
        )
        if not existing_query:
            logger.exception("Query not found")
            raise ValueError("Query not found")

        delete_flag = await self.bigquery_dao.delete_query_async(query_id=query_id)
        logger.info("Deleted query succesfully")
        return delete_flag

    @staticmethod
    def get_last_run_date(run: Run, dry_run: bool) -> QueryParam:
        if dry_run:
            date = datetime.now(timezone.utc).isoformat()
        else:
            dao = RunDao()
            recent_run = dao.get_recent_run(run)
            date = recent_run.created_at.isoformat() if recent_run else datetime.fromtimestamp(0).isoformat()
        details = run.run_source_details
        return QueryParam.model_validate(
            {"type": "SCALAR", "value": {"type": "STRING", "data": date}}
        )

    DYNAMIC_QUERY_PARAM_MAPPING: Dict[
        str, Optional[Callable[[Run, bool], QueryParam]]
    ] = {"last_run_date": get_last_run_date}

    @staticmethod
    def get_dyanmic_query_params(
        run_record: Run, dry_run: bool = False
    ) -> Dict[str, QueryParam]:
        return {
            param: func(run_record, dry_run)
            for param, func in BigQueryService.DYNAMIC_QUERY_PARAM_MAPPING.items()
            if func
        }
