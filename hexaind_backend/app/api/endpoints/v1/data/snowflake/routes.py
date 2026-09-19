import logging

from fastapi import APIRouter, Depends, HTTPException, Response
from motor.motor_asyncio import AsyncIOMotorClient

from app.api.rbac.end_points_v1_access_control import CheckNameRoute
from app.core.db.db_utils import get_db_async
from app.services.admin.connectors.schemas import (
    Connector,
    SnowflakeConnectorAuthentication,
)
from app.services.admin.connectors.service import ConnectorService
from app.services.data.snowflake.schemas import (
    AuthenticationResponse,
    SFGetDbSchemasRequest,
    SFGetDbSchemasResponse,
    SFGetDbsRequest,
    SFGetDbsResponse,
    SFGetDbTablesRequest,
    SFGetDbTablesResponse,
    SFPreviewRequest,
    SFPreviewResponse,
)
from app.services.data.snowflake.service import SnowflakeService

snowflake_router = APIRouter(tags=["SnowFlake"], route_class=CheckNameRoute)

logger = logging.getLogger(__package__)


class SnowFlakeRouter:

    def __init__(self):
        """
        Class init
        """

    @staticmethod
    @snowflake_router.post(
        "/v1/sites/{site_id}/projects/{project_id}/assets/data/snowflake/authenticate",
        response_model=AuthenticationResponse,
    )
    async def authenticate(
        config: SnowflakeConnectorAuthentication,
        site_id: str,
        project_id: str,
        response: Response,
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ) -> AuthenticationResponse:
        snowflake_service = SnowflakeService(db_async_client=client)
        authenticated = snowflake_service.snowflake_authentication(
            authentication=config
        )
        return authenticated

    @staticmethod
    @snowflake_router.post(
        "/v1/sites/{site_id}/projects/{project_id}/assets/data/snowflake/get_databases",
        response_model=SFGetDbsResponse,
    )
    async def get_snowflake_dbs(
        site_id: str,
        project_id: str,
        request: SFGetDbsRequest,
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ) -> SFGetDbsResponse:

        try:
            connector_service = ConnectorService(db_async_client=client)
            snowflake_service = SnowflakeService(db_async_client=client)

            connector_obj: Connector = (
                await connector_service.get_connector_by_id_async(
                    connector_id=request.snowflake_connector_id
                )
            )

            databases = await snowflake_service.get_databases_list(
                connector=connector_obj
            )

            return SFGetDbsResponse(
                status=True,
                message="Databases fetched successfully.",
                databases_list=databases,
            )

        except Exception as e:
            logger.exception(f"Failed with exception: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Unable to fetch. {str(e)}")

    @staticmethod
    @snowflake_router.post(
        "/v1/sites/{site_id}/projects/{project_id}/assets/data/snowflake/get_db_schemas",
        response_model=SFGetDbSchemasResponse,
    )
    async def get_snowflake_db_schemas(
        site_id: str,
        project_id: str,
        request: SFGetDbSchemasRequest,
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ) -> SFGetDbSchemasResponse:

        try:
            connector_service = ConnectorService(db_async_client=client)
            snowflake_service = SnowflakeService(db_async_client=client)

            connector_obj: Connector = (
                await connector_service.get_connector_by_id_async(
                    connector_id=request.snowflake_connector_id
                )
            )

            schemas = await snowflake_service.get_schemas_list(
                connector=connector_obj, database_name=request.database_name
            )

            return SFGetDbSchemasResponse(
                status=True,
                message="Schemas fetched successfully.",
                schemas_list=schemas,
            )

        except Exception as e:
            logger.exception(f"Failed with exception: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Unable to fetch. {str(e)}")

    @staticmethod
    @snowflake_router.post(
        "/v1/sites/{site_id}/projects/{project_id}/assets/data/snowflake/get_tables",
        response_model=SFGetDbTablesResponse,
    )
    async def get_snowflake_db_tables(
        site_id: str,
        project_id: str,
        request: SFGetDbTablesRequest,
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ) -> SFGetDbTablesResponse:

        try:
            connector_service = ConnectorService(db_async_client=client)
            snowflake_service = SnowflakeService(db_async_client=client)

            connector_obj: Connector = (
                await connector_service.get_connector_by_id_async(
                    connector_id=request.snowflake_connector_id
                )
            )

            schemas = await snowflake_service.get_tables_list(
                connector=connector_obj,
                database_name=request.database_name,
                schema_name=request.schema_name,
            )

            return SFGetDbTablesResponse(
                status=True,
                message="Tables fetched successfully.",
                schemas_list=schemas,
            )

        except Exception as e:
            logger.exception(f"Failed with exception: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Unable to fetch. {str(e)}")

    @staticmethod
    @snowflake_router.post(
        "/v1/sites/{site_id}/projects/{project_id}/assets/data/snowflake/get_preview",
        response_model=SFPreviewResponse,
    )
    async def get_snowflake_db_tables(
        site_id: str,
        project_id: str,
        request: SFPreviewRequest,
        client: AsyncIOMotorClient = Depends(get_db_async),  # type: ignore
    ) -> SFPreviewResponse:

        try:
            connector_service = ConnectorService(db_async_client=client)
            snowflake_service = SnowflakeService(db_async_client=client)

            connector_obj: Connector = (
                await connector_service.get_connector_by_id_async(
                    connector_id=request.snowflake_connector_id
                )
            )

            columns, data = await snowflake_service.get_data_preview(
                connector=connector_obj, config=request
            )

            return SFPreviewResponse(
                status=True,
                message="Tables fetched successfully.",
                columns=columns,
                data=data,
            )

        except Exception as e:
            logger.exception(f"Failed with exception: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Unable to fetch. {str(e)}")


snowflake_router_obj = SnowFlakeRouter()