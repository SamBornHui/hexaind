from contextlib import asynccontextmanager
import time
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
import logging
from fastapi.responses import JSONResponse
from typing import AsyncGenerator, List
import traceback
from app.core.celery.celery_worker import create_celery_app
from app.core.celery.global_config import ACTION_WORKER_DEFAULT_QUEUE, ACTION_WORKER_RK
from app.core.services.action.schemas import Action, ActionRunStatus
from app.core.services.action.service import ActionService
from app.core.services.jwt_token_utils.jwt_token_utils import decodeJWT
from app.services.admin.authentication.service import AuthenticationService
from app.services.admin.connectors.schemas import Connector, DataPullConfig
from app.core.db.db_utils import get_db_async
from motor.motor_asyncio import AsyncIOMotorClient
from app.services.admin.connectors.service import ConnectorService
from app.services.admin.connectors.schemas import (
    RescaleAuth,
    FileDetails,
    ThermocalcConnectorConfiguration,
    UploadRescale,
)
from app.services.admin.connectors.schemas import (
    CreateConnectorResponse,
    ConnectorListResponse,
    UpdateConnectorResponse,
    DeleteConnectorResponse,
    RescalePlatformFiles,
)
from app.api.rbac.end_points_v1_access_control import CheckNameRoute
from app.services.data.assets.datasets.schemas import ApiJobType
from app.services.superset.service import SupersetService
from app.services.workflows.designer.base_schemas import WidgetType
from app.services.workflows.designer.schemas import (
    ApiJobsConfig,
    ExtDataPullConfig,
    Widget,
)
from app.config.env_vars import gateway_environment

logger = logging.getLogger(__package__)

connectors_router = APIRouter(tags=["Connectors"], route_class=CheckNameRoute)



async def generate_superset_service() -> SupersetService:
    return await SupersetService.authenticate_and_create_client(
        url=str(gateway_environment.superset_url),
        username=gateway_environment.username,
        password=gateway_environment.password,
    )


class ConnectorsRouter:
    def __init__(self):
        pass

    @connectors_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/thermocalc_authentication/",
        response_model=None,
    )
    async def thermocalc_authenticate(
        siteId: str,
        projectId: str,
        thermocalc_obj: ThermocalcConnectorConfiguration,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> JSONResponse:
        try:
            connector_handler = ConnectorService(db_async_client=client)
            if await connector_handler.thermocal_authenticate(obj=thermocalc_obj):
                return JSONResponse(
                    content={"message": "Authentication Successful"}, status_code=200
                )
            else:
                return JSONResponse(
                    content={"message": "Authentication Failed"}, status_code=400
                )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed thermCalc Auth with exception {str(e)}",
            )

    @connectors_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/rescale_authentication/",
        response_model=None,
    )
    async def rescale_authenticate(
        siteId: str,
        projectId: str,
        rescale_auth: RescaleAuth,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> JSONResponse:
        try:
            logger.info("Inside rescale authentication")
            connector_handler = ConnectorService(db_async_client=client)
            decision = await connector_handler.rescale_authenticate(
                rescale_auth=rescale_auth
            )
            logger.info(f"decision: {decision}")
            if decision:
                return JSONResponse(
                    content={"message": "Authentication Successfull"}, status_code=200
                )
            else:
                return JSONResponse(
                    content={"message": "Authentication Failed"}, status_code=400
                )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed Rescle Auth with exception {e}",
            )

    @connectors_router.get(
        "/v1/sites/{siteId}/projects/{projectId}/assets/rescale_information",
        response_model=RescalePlatformFiles,
    )
    async def get_platform_rescale_files(
        siteId: str,
        projectId: str,
        connector_id: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> RescalePlatformFiles:
        try:
            connector_handler = ConnectorService(db_async_client=client)
            rescale_data = (
                await connector_handler.connector_dao.fetch_rescale_record_async(
                    connector_id=connector_id
                )
            )
            return rescale_data

        except Exception as e:
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to get rescale data with exception {e}",
            )

    @connectors_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/upload_to_rescale/",
        response_model=List[UploadRescale],
    )
    async def upload_to_rescale(
        siteId: str,
        projectId: str,
        connector_id: str,
        rescale_data: List[FileDetails],
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> List[UploadRescale]:
        try:
            connector_handler = ConnectorService(db_async_client=client)
            upload_response = await connector_handler.upload_files_to_rescale_async(
                rescale_data=rescale_data, connector_id=connector_id
            )
            return upload_response
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed upload file/s Rescle with exception {e}",
            )

    @connectors_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/connector/",
        response_model=CreateConnectorResponse,
    )
    async def create_connector(
        siteId: str,
        projectId: str,
        connector: Connector,
        token: str = "",
        client: AsyncIOMotorClient = Depends(get_db_async),
        superset_service=Depends(generate_superset_service),
    ) -> CreateConnectorResponse:
        try:
            logger.info("Started create connector.")
            connector_handler = ConnectorService(db_async_client=client)
            auth_serv = AuthenticationService(db_async_client=client)
            user = await auth_serv.get_user_by_token_or_id(token=token)
            connector_id = await connector_handler.create_connector_async(
                connector=connector,
                siteId=siteId,
                projectId=projectId,
                user_id=user.id,
                user_name=user.name,
                superset_service=superset_service,
            )
            logger.info(f"created connector with id {connector_id}")

            return CreateConnectorResponse(connector_id=connector_id)

        except Exception as e:
            logger.error(f"{str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @connectors_router.get(
        "/v1/sites/{siteId}/projects/{projectId}/connectors/{connectorId}",
        response_model=Connector,
    )
    async def get_connector(
        siteId: str,
        projectId: str,
        connectorId: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> Connector:
        try:
            logger.info("Get connector provided id.")
            connector_service = ConnectorService(db_async_client=client)
            connector = await connector_service.get_connector_by_id_async(connectorId)
            logger.info("Retrieved the connector from source.")

            if not connector:
                logger.error("Connector not found.")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found"
                )

            return connector

        except Exception as e:
            logger.error(f"Exception: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed with exception {e}",
            )

    @connectors_router.get(
        "/v1/sites/{siteId}/projects/{projectId}/connectors",
        response_model=ConnectorListResponse,
    )
    async def get_all_connectors(
        siteId: str,
        projectId: str,
        search_term: str = None,
        page_number: int = 1,
        page_limit: int = 100,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> List[Connector]:
        try:
            connector_service = ConnectorService(db_async_client=client)
            logger.info(f"received connector service. {connector_service}")
            connectors, total_count = await connector_service.get_all_connectors_async(
                project_id=projectId,
                search_term=search_term,
                page_number=page_number,
                page_limit=page_limit,
            )
            logger.info(f"got all connectors from db. total count: {total_count}")

            return ConnectorListResponse(connectors=connectors, total_count=total_count)

        except Exception as e:
            logger.error(f"Exception: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed with exception {e}",
            )

    @connectors_router.post(
        "/v1/sites/{siteId}/projects/{projectId}/connector/{connectorId}",
        response_model=UpdateConnectorResponse,
    )
    async def update_connector(
        siteId: str,
        projectId: str,
        connectorId: str,
        connector: Connector,
        token: str,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ) -> UpdateConnectorResponse:
        try:
            logger.info("in update connector.")

            connector_handler = ConnectorService(db_async_client=client)

            auth_serv = AuthenticationService(db_async_client=client)
            user = await auth_serv.get_user_by_token_or_id(token=token)

            update_flag = await connector_handler.update_connector_async(
                user.id, connectorId, connector
            )
            logger.info(f"Updated the connector with flag {update_flag}")

            return UpdateConnectorResponse(success=update_flag)

        except Exception as e:
            logger.error(f"Exception: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )

    @connectors_router.delete(
        "/v1/sites/{siteId}/projects/{projectId}/connectors/{connectorId}",
        response_model=DeleteConnectorResponse,
    )
    async def delete_connector(
        siteId: str,
        projectId: str,
        connectorId: str,
        token: str = "",
        client: AsyncIOMotorClient = Depends(get_db_async),
        superset_service: SupersetService = Depends(generate_superset_service),
    ) -> DeleteConnectorResponse:
        try:
            logger.info("in delete connector")
            connector_service = ConnectorService(db_async_client=client)
            decoded_token = decodeJWT(token)
            delete_conn_resp = await connector_service.delete_connector_async(
                connectorId,
                decoded_token["user_id"],
                superset_service=superset_service,
            )
            logger.info(
                f"Connectror is deleted:{delete_conn_resp.success}.Response:{delete_conn_resp.message}"
            )

            return delete_conn_resp

        except Exception as e:
            logger.error(f"Exception: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed with exception {e}",
            )
        
    # @connectors_router.post(
    #     # "/v1/sites/{site_id}/projects/{project_id}/connectors/external_data_pull",
    #     "/v1/sites/{site_id}/projects/connectors/external_data_pull",
    # )
    # async def external_data_pull(
    #     site_id: str,
    #     external_data_config: DataPullConfig,
    #     client: AsyncIOMotorClient = Depends(get_db_async),
    # ):
    #     try:
    #         logger.info("Starting external data pull.")
    #         connector_service = ConnectorService(db_async_client=client)

    #         actual_token = external_data_config.token

    #         decoded_token = decodeJWT(actual_token.split(" ")[1])
    #         logger.info("Decoded token successfully.")
    #         connector_object = (
    #             await connector_service.get_connector_by_database_id_async(
    #                 external_data_config.superset_connector_id
    #             )
    #         )
    #         project_id = connector_object.project_id
    #         logger.info(f"Retrieved connector: {connector_object.name}.")

    #         action_config = Widget(
    #             urn="",
    #             name=f"EDP_{connector_object.type}_{connector_object.name}_{time.strftime('%Y%m%d%H%M%S')}",
    #             description=f"External Data Pull for {connector_object.name}",
    #             type=WidgetType.API_JOBS,
    #             config=ApiJobsConfig(
    #                 job_type=ApiJobType.EXTERNEL_DATA_PULL,
    #                 config=ExtDataPullConfig(
    #                     superset_db_id=external_data_config.superset_connector_id
    #                 ),
    #                 widget_type=WidgetType.API_JOBS,
    #             ),
    #         )
    #         action = Action(
    #             run_id="",
    #             action_config=action_config,
    #             status=ActionRunStatus.IDLE,
    #         )
    #         action_service = ActionService(db_async_client=client)
    #         action_id = await action_service.create_action_async(action)
    #         logger.info(f"Created action with ID: {action_id}.")

    #         sql_config_dict = {
    #             "connection_details": connector_object.configuration.model_dump(mode="json"),
    #             "query": external_data_config.query,
    #             "dataset_name": f"SQL_Dataset_{connector_object.name}_{connector_object.type}_{uuid.uuid4()}",
    #             "batch_size": external_data_config.batch_size,
    #             # "gcs_bucket": connector_object.configuration.authentication_details.gcs_bucket_name,
    #             # "gcs_path": external_data_config.gcs_path
    #         }

    #         celeryApp = create_celery_app("external_data_puller")
    #         celeryApp.send_task(
    #             "task_sql_data_pull",
    #             kwargs={
    #                 "action_id": action_id,
    #                 "project_id": project_id,
    #                 "user_id": decoded_token["user_id"],
    #                 "sql_config": sql_config_dict,
    #             },
    #             queue=ACTION_WORKER_DEFAULT_QUEUE,
    #             routing_key=ACTION_WORKER_RK,
    #         )
    #         logger.info("Task sent to Celery.")
    #     except Exception as e:
    #         logger.error(f"Exception during external data pull: {str(e)}", exc_info=True)
    #         raise HTTPException(
    #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             detail=f"Failed with exception {e}",
    #         )
        

    @connectors_router.post(
        # "/v1/sites/{site_id}/projects/{project_id}/connectors/external_data_pull",
        "/v1/sites/{site_id}/projects/connectors/external_data_pull",
    )
    async def external_data_pull(
        site_id: str,
        external_data_config: DataPullConfig,
        client: AsyncIOMotorClient = Depends(get_db_async),
    ):
        try:
            logger.info("Starting external data pull.")
            connector_service = ConnectorService(db_async_client=client)

            actual_token = external_data_config.token

            decoded_token = decodeJWT(actual_token.split(" ")[1])
            logger.info("Decoded token successfully.")
            connector_object = (
                await connector_service.get_connector_by_database_id_async(
                    external_data_config.superset_connector_id
                )
            )
            project_id = connector_object.project_id
            logger.info(f"Retrieved connector: {connector_object.name}.")

            action_config = Widget(
                urn="",
                name=f"EDP_{connector_object.type}_{connector_object.name}_{time.strftime('%Y%m%d%H%M%S')}",
                description=f"External Data Pull for {connector_object.name}",
                type=WidgetType.API_JOBS,
                config=ApiJobsConfig(
                    job_type=ApiJobType.EXTERNEL_DATA_PULL,
                    config=ExtDataPullConfig(
                        superset_db_id=external_data_config.superset_connector_id
                    ),
                    widget_type=WidgetType.API_JOBS,
                ),
            )
            action = Action(
                run_id="",
                action_config=action_config,
                status=ActionRunStatus.IDLE,
            )
            action_service = ActionService(db_async_client=client)
            action_id = await action_service.create_action_async(action)
            logger.info(f"Created action with ID: {action_id}.")

            sql_config_dict = {
                "connection_details": connector_object.configuration.model_dump(
                    mode="json"
                ),
                "query": external_data_config.query,
                "dataset_name": f"SQL_Dataset_{connector_object.name}_{connector_object.type}_{uuid.uuid4()}",
                "batch_size": external_data_config.batch_size,
                # "gcs_bucket": connector_object.configuration.authentication_details.gcs_bucket_name,
                # "gcs_path": external_data_config.gcs_path
            }

            celeryApp = create_celery_app("external_data_puller")
            celeryApp.send_task(
                "task_sql_data_pull",
                kwargs={
                    "action_id": action_id,
                    "project_id": project_id,
                    "user_id": decoded_token["user_id"],
                    "sql_config": sql_config_dict,
                },
                queue=ACTION_WORKER_DEFAULT_QUEUE,
                routing_key=ACTION_WORKER_RK,
            )
            logger.info("Task sent to Celery.")
        except Exception as e:
            logger.error(
                f"Exception during external data pull: {str(e)}", exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed with exception {e}",
            )


connectors_router_obj = ConnectorsRouter()
