import traceback
import logging

import httpx

from fastapi import APIRouter, Depends, HTTPException, status, Response
from motor.motor_asyncio import AsyncIOMotorClient
from app.services.admin.connectors.service import ConnectorService
from app.services.admin.authentication.service import AuthenticationService
from app.services.data.bigquery.service import BigQueryService
from app.core.db.db_utils import get_db_async
from app.services.data.bigquery.schemas import (
    DatasetTableListResponse,
    DryRunResponseModel,
    PreviewObj,
    PreviewResponse,
    TablesList,
)
from app.services.workflows.designer.schemas import BigQueryDatasetConfiguration
from app.services.admin.connectors.schemas import (
    BigQueryAuthentication,
    BigQueryAuthResponse,
    Query,
    CreateQueryResponse,
    CreateQueryRequest,
    GenericQueryResponse,
    UpdateQueryRequest,
    QueryListResponse,
)
from app.api.rbac.end_points_v1_access_control import CheckNameRoute
from app.config.env_vars import gateway_environment

bigquery_router = APIRouter(tags=["BigQuery"], route_class=CheckNameRoute)

logger = logging.getLogger(__package__)


class BigQueryRouter:

    def __init__(self):
        """
        Class init
        """
        pass

    @staticmethod
    @bigquery_router.post(
        "/v1/sites/{site_id}/projects/{project_id}/assets/bigquery/dryrun",
        response_model=DryRunResponseModel,
    )
    async def bq_dryrun(
        site_id: str,
        project_id: str,
        config: BigQueryDatasetConfiguration,
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ) -> DryRunResponseModel:
        """
        Perform a dry run for a BigQuery dataset configuration.

        This endpoint allows you to simulate a BigQuery job without actually executing it.
        It takes a BigQueryDatasetConfiguration as input, including the dataset and query details,
        and returns the response in the form of a DryRunResponseModel.

        Parameters:
        - `site_id` (str): The identifier for the site.
        - `project_id` (str): The identifier for the project.
        - `config` (BigQueryDatasetConfiguration): The configuration for the BigQuery dataset.
        - `client` (AsyncIOMotorClient, optional): An asynchronous MongoDB client obtained from the dependency.

        Returns:
        - `DryRunResponseModel`: The response model containing information about the dry run.

        Raises:
        - HTTPException: If there is an issue with the request or the dry run cannot be performed.
        """
        logger.info("inside bigquery dryrun method.")
        try:
            connector_service = ConnectorService(db_async_client=client)
            connector_results = await connector_service.get_connector_by_id_async(
                config.bigquery_connector_id
            )
            bigquery_service = BigQueryService(db_async_client=client)
            return bigquery_service.bigquery_dryrun(
                connector_results.configuration, config
            )
        except Exception as e:
            # traceback.print_exc()
            logger.error(traceback.format_exc())
            logger.error(
                f"Failed with exception {e} : {site_id} , {project_id}, {config}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to fetch big query dry run response",
            )

    @staticmethod
    @bigquery_router.post(
        "/v1/sites/{site_id}/projects/{project_id}/assets/bigquery/authenticate"
    )
    async def authenticate(
        config: BigQueryAuthentication,
        site_id: str,
        project_id: str,
        response: Response,
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ) -> BigQueryAuthResponse:
        """
        API method for testing authentication status of bigquery

        Args:
            config (BigQueryAuthentication): authentication config such as project id or account file etc.
            site_id (str): site id
            project_id (str): project id of the user project
            response (Response): fast api response

        Returns:
            BigQueryAuthResponse: returns the status and message of auth status
        """
        bigquery_service = BigQueryService(db_async_client=client)
        authenticated = bigquery_service.bigquery_authenticate(config)
        if authenticated:
            response.status_code = status.HTTP_200_OK
            message = "Authentication Success"
        else:
            response.status_code = status.HTTP_401_UNAUTHORIZED
            message = "Authentication Failed"

        return BigQueryAuthResponse(status=response.status_code, message=message)

    @staticmethod
    @bigquery_router.post(
        "/v1/sites/{site_id}/projects/{project_id}/assets/bigquery/datasets_list"
    )
    async def get_datasets_list(
        site_id: str,
        project_id: str,
        connector_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ) -> DatasetTableListResponse:
        """
        This API fetches all the dataset names in the given project

        Args:
            site_id (str): site id of the user
            project_id (str): project id of the user
            connector_id (str): connector id of the bigquery connector
            client (AsyncIOMotorClient, optional): _description_. Defaults to Depends(get_db_async).

        Returns:
            DatasetListResponse: list of dataset names available in the project.
        """
        try:
            connector_service = ConnectorService(db_async_client=client)
            connector = await connector_service.get_connector_by_id_async(
                connector_id=connector_id
            )

            if not connector:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found"
                )

            bigquery_service = BigQueryService(db_async_client=client)

            datasets_list = await bigquery_service.bigquery_dataset_list(
                connector=connector,
                project_id=connector.configuration.authentication_details.project_id,
            )
            if not datasets_list:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No datasets found in the project {connector.configuration.authentication_details.project_id}",
                )

            return DatasetTableListResponse(data_list=datasets_list)

        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    @bigquery_router.post(
        "/v1/sites/{site_id}/projects/{project_id}/assets/bigquery/tables_list"
    )
    async def get_tables_list(
        site_id: str,
        project_id: str,
        connector_id: str,
        config: TablesList,
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ) -> DatasetTableListResponse:
        """
        This API fetches all the table names in the given dataset.

        Args:
            site_id (str): site id of the user
            project_id (str): project id of the user
            connector_id (str): connector id of the bigquery connector
            config (TablesList): takes dataset name as the config
            client (AsyncIOMotorClient, optional): _description_. Defaults to Depends(get_db_async).

        Returns:
            TableListResponse: returns a list of table names in the dataset provided.
        """
        try:

            connector_service = ConnectorService(db_async_client=client)
            connector = await connector_service.get_connector_by_id_async(
                connector_id=connector_id
            )

            if not connector:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found"
                )

            bigquery_service = BigQueryService(db_async_client=client)

            tables = await bigquery_service.bigquery_table_list(
                connector=connector,
                project_id=connector.configuration.authentication_details.project_id,
                dataset_name=config.dataset_name,
            )

            if type(tables) is not list:

                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No tables found in the dataset {config.dataset_name}",
                )

            return DatasetTableListResponse(data_list=tables)

        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    @staticmethod
    @bigquery_router.post(
        "/v1/sites/{site_id}/projects/{project_id}/assets/bigquery/preview"
    )
    async def get_preview_data(
        site_id: str,
        project_id: str,
        connector_id: str,
        config: PreviewObj,
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ) -> PreviewResponse:
        """
        This API is used to get the preview data of the bigquery.

        Args:
            site_id (str): site id of the user
            project_id (str): project id of the user
            connector_id (str): connector id of the bigquery connector
            config (PreviewObj): config as datasetname, tablename for getting the preview
            client (AsyncIOMotorClient, optional): _description_. Defaults to Depends(get_db_async).

        Returns:
            PreviewResponse: list of the objects of the preview data
        """
        try:
            connector_service = ConnectorService(db_async_client=client)
            connector = await connector_service.get_connector_by_id_async(
                connector_id=connector_id
            )
            if not connector:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found."
                )

            bigquery_service = BigQueryService(db_async_client=client)
            columns, data = await bigquery_service.bigquery_data_preview(
                connector=connector,
                project_id=connector.configuration.authentication_details.project_id,
                config=config,
            )

            return PreviewResponse(columns=columns, data=data)

        except Exception as e:
            logger.exception("Unable to fetch preview")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    @staticmethod
    @bigquery_router.post(
        "/v1/sites/{site_id}/projects/{project_id}/assets/bigquery/query",
        response_model=CreateQueryResponse,
    )
    async def create_query(
        site_id: str,
        project_id: str,
        query_data: CreateQueryRequest,
        token: str = "",
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ) -> CreateQueryResponse:
        """
        API to store a query and its details in the MongoDB

        Args:
            site_id (str): site id of the user
            project_id (str): project id of the current project
            query_data (CreateQueryRequest): data require to store: name, query etc...
            token (str, optional): _description_. Defaults to "".
            client (AsyncIOMotorClient, optional): _description_. Defaults to Depends(get_db_async).

        Raises:
            HTTPException: raises HTTP exception upon invalid data or other error
        Returns:
            CreateQueryResponse: returns query_id
        """
        try:
            logger.info("Started create query.")
            bigquery_service = BigQueryService(db_async_client=client)
            auth_serv = AuthenticationService(db_async_client=client)

            if not query_data.query:
                conn_serv = ConnectorService(db_async_client=client)
                connector = await conn_serv.get_connector_by_id_async(
                    query_data.connector_id
                )
                bq_project = connector.configuration.authentication_details.project_id
                query_data.query = f"SELECT * FROM `{bq_project}.{query_data.dataset_name}.{query_data.table_name}`"

            user = await auth_serv.get_user_by_token_or_id(token=token)
            query_id = await bigquery_service.create_query_async(
                query_data=query_data,
                site_id=site_id,
                project_id=project_id,
                user_id=user.id,
                user_name=user.name,
            )
            logger.info(f"created query with id {query_id}")

            return CreateQueryResponse(query_id=query_id)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @staticmethod
    @bigquery_router.get(
        "/v1/sites/{site_id}/projects/{project_id}/assets/bigquery/query/{query_id}",
        response_model=Query,
    )
    async def get_query_by_id(
        site_id: str,
        project_id: str,
        query_id: str,
        token: str = "",
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ) -> Query:
        try:
            logger.info("Get query provided id.")
            bigquery_service = BigQueryService(db_async_client=client)
            query = await bigquery_service.get_query_by_id_async(query_id)
            logger.info("Retrieved the query from source.")

            if not query:
                logger.error("Query not found.")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Query not found"
                )

            return query

        except Exception as e:
            logger.error(f"Exception: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed with exception {e}",
            )

    @staticmethod
    @bigquery_router.patch(
        "/v1/sites/{site_id}/projects/{project_id}/assets/bigquery/query",
        response_model=GenericQueryResponse,
    )
    async def update_query_async(
        site_id: str,
        project_id: str,
        request: UpdateQueryRequest,
        token: str = "",
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ) -> GenericQueryResponse:
        try:
            logger.info("Inside update query.")
            auth_serv = AuthenticationService(db_async_client=client)
            user = await auth_serv.get_user_by_token_or_id(token=token)
            bigquery_service = BigQueryService(db_async_client=client)
            result = await bigquery_service.update_query_async(
                user_id=user.id, query_data=request
            )
            logger.info("Retrieved all queries from db.")

            if not result:
                logger.error("Unable to update query")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Unable to update query",
                )

            return GenericQueryResponse(
                succeeded=True, message="Updated the query successfully"
            )

        except Exception as e:
            logger.error(f"Exception: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed with exception {e}",
            )

    @staticmethod
    @bigquery_router.get(
        "/v1/sites/{site_id}/projects/{project_id}/assets/bigquery/query",
        response_model=QueryListResponse,
    )
    async def get_all_queries_async(
        site_id: str,
        project_id: str,
        search_term: str = None,
        page_number: int = 1,
        page_limit: int = 10,
        token: str = "",
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ) -> QueryListResponse:
        try:
            logger.info("Getting all queries.")
            bigquery_service = BigQueryService(db_async_client=client)
            queries, total_count = await bigquery_service.get_all_queries_async(
                project_id=project_id,
                search_term=search_term,
                page_number=page_number,
                page_limit=page_limit,
            )
            logger.info("Retrieved queries.")

            return QueryListResponse(queries=queries, total_count=total_count)

        except Exception as e:
            logger.error(f"Exception: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed with exception {e}",
            )

    @staticmethod
    @bigquery_router.delete(
        "/v1/sites/{site_id}/projects/{project_id}/assets/bigquery/query/{query_id}",
        response_model=GenericQueryResponse,
    )
    async def delete_query(
        site_id: str,
        project_id: str,
        query_id: str,
        token: str = "",
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ) -> GenericQueryResponse:
        try:
            logger.info("Delete query provided id.")
            bigquery_service = BigQueryService(db_async_client=client)
            query = await bigquery_service.delete_query_async(query_id)

            if not query:
                logger.error("Unable to delete the query.")
                raise KeyError("Query not found for deleting")

            logger.info("Deleted the query successfully.")

            return GenericQueryResponse(succeeded=True, message="Deleted Succesfully")


        except KeyError as ke:
            logger.error(f"Exception: {str(ke)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Failed with exception {ke}",
            )
        
        except Exception as e:
            logger.error(f"Exception: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed with exception {e}",
            )
        
    @bigquery_router.get("/v1/sites/{site_id}/projects/{project_id}/assets/saved_queries")
    async def get_saved_queries(token: str = ""):
        """
        Fetch saved queries from Superset.
        """
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",  # Changed Accept header
            "Accept-Language": "en-US,en;q=0.9,en-IN;q=0.8",
            "Authorization": f"Bearer {token}",
            "Cookie": 'session=.eJwlzsuKAkEMheF3qbWLpC4m8WWaJJWg2IzQPa7Ed5-CWf4HPjifsuUR573cUvczLmV7zHIrwxoiEjWLnkKWkDSGUa_YoyGYuA0Om-HGIsbDZTYVmIADEjVXVJMaGMAgrA4hDaC65eye2a26WrKKMjr5zJoDrjWvOkYt68j7jOP_Da7088jt9_WMnzVwYggJO4gtMQNJzdQ7J3EXillnA8nl9pfrHsss-P0DS6hFUw.Z45rwQ.2TyhpiorXF2bkUsQn06kRgdA-og; project_id=""; hexaind-token="Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6Im11bHRpc2NhbGVhZG1pbkBtdWx0aXNjYWxlLnRlY2giLCJzZXJ2ZXJfcm9sZV92YWx1ZSI6MSwidHlwZSI6ImFjY2Vzc190b2tlbiIsInVzZXJfaWQiOiI2NzU5NzNjMTBhODVlOTdkNTk3Yjg4MzYiLCJleHBpcmVzIjoxNzM4MDM1NzQ5LjQ3Nzk2NDZ9.vIb8u7DIb0SXbzRq-UwYC64sUH28TWxQCYU7wrYOiwE"',
        }
        async with httpx.AsyncClient(
                base_url=str(gateway_environment.superset_url), timeout=None
            ) as client:
                # Call the create database API
                queries_url = "/api/v1/saved_query/?q=(order_column:changed_on_delta_humanized,order_direction:desc,page:0,page_size:25)"
                response = await client.get(queries_url, headers=headers)

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to fetch saved queries: {response.text}",
            )

        # Parse the response data
        data = response.json()
        saved_queries = [
            {
                "id": query["id"],
                "label": query["label"],
                "sql": query["sql"],
            }
            for query in data.get("result", [])
        ]
        return saved_queries


bigquery_router_obj = BigQueryRouter()
