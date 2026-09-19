import os, uuid, datetime, time, logging
import httpx
from pymongo import MongoClient
from app.services.admin.projects.service import ProjectService
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Tuple, Mapping, Any, Optional, Dict
import aiohttp
from datetime import datetime, timezone
import logging
from sympy import det
from yarl import URL
import json
import requests
from Crypto.PublicKey import RSA
from pathlib import Path

from app.services.admin.projects.schemas import SupersetRoleData
from .schemas import (
    BigQueryAuthType,
    BigQueryConnectorConfiguration,
    BigQueryServiceAccountConfig,
    Connector,
    ConnectorType,
    RescaleAuth,
    FileDetails,
    RescaleConnectorConfiguration,
    SQLAlchemyConnectorConfiguration,
    SnowflakeConnectorConfiguration,
    SnowflakeConnectorDefaultAuthentication,
    UploadRescaleResponse,
    UploadRescale,
    ThermocalcConnectorConfiguration, DeleteConnectorResponse, SnowflakeConnectorAuthenticationType
)
from .dao import ConnectorDao

from app.config.env_vars import thermocalc_environment as tc_env
from app.config.env_vars import rescale_environment, gateway_environment
from app.services.admin.connectors.schemas import RescalePlatformFiles
from app.services.superset.service import SupersetService

logger = logging.getLogger(__package__)
logger.setLevel(logging.DEBUG)

class ConnectorService:

    def __init__(
        self,
        db_sync_client: Optional[MongoClient] = None,
        db_async_client: Optional[AsyncIOMotorClient] = None,
    ) -> None:  # type: ignore
        self.connector_dao = ConnectorDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )
        self.rescale_url = URL(rescale_environment.uri)

        self.connector_dao = ConnectorDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )
        self.project_service = ProjectService(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )

    async def thermocal_authenticate(
        self, obj: ThermocalcConnectorConfiguration
    ) -> bool:
        logger.info("inside thermocalc authenticate")

        try:
            # TODO authentication verification:
            # If we are able to reach the server given LSHOST from the current instance then authentication will be successful.

            # Normalize the user-provided path
            normalized_obj_path = os.path.normpath(obj.path)

            # Split the environment variable into multiple paths and normalize each one
            env_paths = [os.path.normpath(path.strip()) for path in tc_env.thermocalc_path.split(',')]

            # Check if the normalized user path is in the list of normalized environment paths
            if tc_env.thermocalc_host.lower() == obj.host.lower():
                logger.info("Thermocalc host validated successfully.")

                if normalized_obj_path in env_paths:
                    logger.info("Thermocalc path validated successfully.")
                    return True

            logger.info("Thermocalc path validation failed.")
            return False

        except Exception as e:
            logger.exception(f"Failed with Exception,: {str(e)}")
            return False

    async def authorization_header_async(self, token: str) -> Mapping[str, str]:
        return {"Authorization": f"Token {token}"}

    def authorization_header(self, token: str) -> Mapping[str, str]:
        return {"Authorization": f"Token {token}"}

    async def rescale_authenticate(self, rescale_auth: RescaleAuth) -> bool:
        logger.info("Inside Rescale authentication")

        async with aiohttp.ClientSession() as session:
            try:
                response = await session.get(
                    self.rescale_url / "jobs",
                    headers=await self.authorization_header_async(rescale_auth.token),
                )
                logger.info(f"Rescale authentication response status: {response.status}")
                return response.status == 200
            except aiohttp.ClientError as e:
                logger.error(f"HTTP request to Rescale failed: {e}")
                return False
            except Exception as e:
                logger.error(f"Unexpected error during Rescale authentication: {e}")
                return False
    
    def upload_file(self, api_token: str, path: Path) -> Mapping[str, Any]:
        logger.info("Inside upload file.")

        with path.open("rb") as fileio:
            response = requests.post(
                "https://platform.rescale.com/api/v2/files/contents/",
                headers=self.authorization_header(api_token),
                files={"file": (path.name, fileio)},
            )

            if response.text:
                return {"id": json.loads(response.text)["id"], "file_name": path.name}
            else:
                return {"id": None, "file_name": path.name}

    async def upload_file_async(
        self, api_token: str, path: Path
    ) -> Optional[Dict[str, str]]:
        try:
            logger.info("inside upload file")
            async with aiohttp.ClientSession() as session:
                async with path.open("rb") as file_data:
                    response = await session.post(
                        self.rescale_url.join(URL("files/contents/")),
                        headers=await self.authorization_header_async(api_token),
                        data={"file": file_data},
                    )

                    if response.status == 201:
                        data = await response.json()  # Use response.json() for JSON parsing
                        return {"id": data["id"], "file_name": path.name}
                    else:
                        return None

        except Exception as e:
            # Handle potential exceptions here
            logger.exception(f"Error during file upload: {e}")
            return None

    def upload_files_to_rescale(
        self, rescale_data: List[FileDetails], connector_id: str
    ) -> List[UploadRescale]:
        logger.info("inside upload files to rescale.")
        upload_response = list()
        connector_detail = self.connector_dao.get_connector(connector_id=connector_id)
        rescale_auth_token = connector_detail.configuration.token
        try:
            record_detail = self.connector_dao.fetch_rescale_record(
                connector_id=connector_id
            )
        except:
            record_detail = RescalePlatformFiles(connector_id=connector_id)
        if record_detail.rescale_files:
            rescale_files = record_detail.rescale_files.model_dump()["rescale_files"]

        else:
            rescale_files = []

        for i in rescale_data:
            temp = next(
                (
                    item
                    for item in rescale_files
                    if item["file_name"] == i.file_path.name
                ),
                None,
            )
            if not temp:
                temp = self.upload_file(rescale_auth_token, i.file_path)
            upload_response.append(UploadRescale(**temp))
        record_detail.rescale_files = UploadRescaleResponse(
            rescale_files=upload_response
        )
        db_data = record_detail.model_dump()
        db_data["platform_files"] = [
            {
                "file_name": file["file_name"],
                "file_path": str(file["file_path"]),  # Convert PosixPath to str
            }
            for file in db_data["platform_files"]
        ]

        self.connector_dao.insert_rescale_record(db_data)
        logger.info("Returning the upload response.")
        return upload_response

    async def upload_files_to_rescale_async(
        self, rescale_data: List[FileDetails], connector_id: str
    ) -> List[UploadRescale]:
        logger.info("inside upload files to rescale.")
        upload_response = list()
        connector_detail = await self.connector_dao.get_connector_by_id_async(
            connector_id=connector_id
        )
        rescale_auth_token = connector_detail.configuration.token
        record_detail = await self.connector_dao.fetch_rescale_record_async(
            connector_id=connector_id
        )
        if record_detail.rescale_files:
            rescale_files = record_detail.rescale_files.model_dump()["rescale_files"]

        else:
            rescale_files = []

        for i in rescale_data:
            temp = next(
                (
                    item
                    for item in rescale_files
                    if item["file_name"] == i.file_path.name
                ),
                None,
            )
            if not temp:
                temp = self.upload_file(rescale_auth_token, i.file_path)
            upload_response.append(UploadRescale(**temp))
        record_detail.rescale_files = UploadRescaleResponse(
            rescale_files=upload_response
        )
        db_data = record_detail.model_dump()
        db_data["platform_files"] = [
            {
                "file_name": file["file_name"],
                "file_path": str(file["file_path"]),  # Convert PosixPath to str
            }
            for file in db_data["platform_files"]
        ]

        await self.connector_dao.insert_rescale_record_async(db_data)
        logger.info("returning the rescale record.")
        return upload_response

    def is_valid_connector(self, connector: Connector):
        return True

    async def create_connector_async(
        self,
        siteId: str,
        projectId: str,
        user_id: str,
        user_name: str,
        connector: Connector,
        superset_service: SupersetService,
    ) -> str:
        logger.info("Inside create connector.")

        # Validate connector
        if not self.is_valid_connector(connector):
            logger.exception("Not a valid connector")
            raise Exception("Not a valid connector")

        # Update the record (JSON body)
        connector.site_id = siteId
        connector.project_id = projectId
        connector.owner_id = user_id
        connector.owner_name = user_name
        connector.created_at = datetime.now(timezone.utc)
        connector.last_modified_by_id = connector.owner_id
        connector.last_modified_at = connector.created_at

        # superset changes
        superset_flag: bool = False
        match connector.configuration:
            case SnowflakeConnectorConfiguration() as config if isinstance(
                config.authentication.root, SnowflakeConnectorDefaultAuthentication
            ):
                superset_flag = True
                creds = config.authentication.root
                connection_string = (
                    f"snowflake://{creds.sf_user}:{creds.sf_password}@{creds.sf_account}/"
                    f"{creds.sf_database}/{creds.sf_schema}?warehouse={creds.sf_warehouse}&role={creds.sf_role}"
                )
                connector.configuration.connection_string = connection_string
                payload = {
                    "database_name": connector.name,
                    "sqlalchemy_uri": connection_string,
                    "expose_in_sqllab": True,
                    "allow_multi_schema_metadata_fetch": True,
                }
            case SQLAlchemyConnectorConfiguration():
                superset_flag = True
                connection_string = connector.configuration.connection_string
                payload = {
                    "database_name": connector.name,
                    "sqlalchemy_uri": connection_string,
                    "expose_in_sqllab": True,
                    "allow_multi_schema_metadata_fetch": True,
                }
            case BigQueryConnectorConfiguration() as config if isinstance(
                config.authentication_details, BigQueryServiceAccountConfig
            ):
                superset_flag = True
                # Prepare the payload
                details = config.authentication_details
                cred_obj = {
                    "type": details.type,
                    "project_id": details.project_id,
                    "client_email": details.client_email,
                    "client_id": details.client_id,
                    "auth_uri": details.auth_uri,
                    "token_uri": details.token_uri,
                    "auth_provider_x509_cert_url": details.auth_provider_x509_cert_url,
                    "client_x509_cert_url": details.client_x509_cert_url,
                    "private_key": details.private_key,
                    "universe_domain": "googleapis.com",
                }
                payload = {
                    "database_name": connector.name,
                    "engine": "bigquery",
                    "configuration_method": "dynamic_form",
                    "engine_information": {
                        "disable_ssh_tunneling": True,
                        "supports_dynamic_catalog": True,
                        "supports_file_upload": True,
                    },
                    "driver": "bigquery",
                    "sqlalchemy_uri_placeholder": "bigquery://{project_id}",
                    "extra": '{"allows_virtual_table_explore":true}',
                    "expose_in_sqllab": True,
                    "parameters": {"credentials_info": json.dumps(cred_obj)},
                    "masked_encrypted_extra": json.dumps(
                        {"credentials_info": cred_obj}
                    ),
                }
            case _:
                superset_flag = False
                payload = {}
        if superset_flag:
            # add database
            database = await superset_service.database.create(payload)

            logger.info("Database created successfully.")
            connector.database_id = database.id

            resource_id = (
                await superset_service.resource.from_database_id(database.id)
            )[0].id
            permission_id = (
                await superset_service.permision.from_name("database_access")
            )[0].id
            database_permission_resource = (
                await superset_service.permission_resource.from_permission_resource(
                    permission_id, resource_id
                )
            )[0]

            default_permission_resources = [
                (
                    await superset_service.permission_resource.from_id(
                        permission_resource_id
                    )
                )
                for permission_resource_id in (
                    12,  # can write x dataset
                    145,  # can post x table schema view
                    146,  # can exapnd x table schem view
                    147,  # can delete x table schema view
                )
            ]

            # get or create superset role for the project
            current_project = await self.project_service.get_project_by_id_async(
                connector.project_id
            )
            if current_project.superset_data is None:
                role = await superset_service.role.create(projectId)
                current_project.superset_data = SupersetRoleData(role_id=role.id)
            else:
                try:
                    role = await superset_service.role.from_id(
                        current_project.superset_data.role_id
                    )
                except KeyError:
                    role = await superset_service.role.create(projectId)
                    current_project.superset_data = SupersetRoleData(role_id=role.id)

            # update role permissions
            permission_resources = await superset_service.role.get_permissions(role.id)
            permission_resources.append(database_permission_resource)
            permission_resources.extend(default_permission_resources)
            await superset_service.role.update_permissions(
                role.id, permission_resources
            )

            # update hexaind project
            await self.project_service.update_project_async(
                connector.project_id, current_project, connector.owner_id
            )

        connector_id = await self.connector_dao.create_connector_async(connector)
        logger.info(f"Created the connector with connector id {connector_id}")

        return connector_id

    async def get_connector_by_id_async(self, connector_id: str) -> Connector:
        logger.info(f"inside get connector. connector id: {connector_id}")

        connector = await self.connector_dao.get_connector_by_id_async(connector_id)
        logger.info("Retrieved the connector from db.")

        # validate connector
        if not self.is_valid_connector(connector):
            logger.exception(f"Not a valid connector. {connector}")
            raise Exception("Not a valid connector")

        return connector
    
    async def get_connector_by_database_id_async(self, database_id: int) -> Connector:
        logger.info(f"inside get connector. connector id: {database_id}")

        connector = await self.connector_dao.get_connector_by_superset_id_async(
            database_id
        )
        logger.info("Retrieved the connector from db.")

        # validate connector
        if not self.is_valid_connector(connector):
            logger.exception(f"Not a valid connector. {connector}")
            raise Exception("Not a valid connector")

        return connector

    async def get_all_connectors_async(
        self, project_id: str, search_term: str, page_number: int, page_limit: int
    ) -> Tuple[List[Connector], int]:
        logger.info("inside get all connectors.")

        connectors, total_count = await self.connector_dao.get_all_connectors_async(
            project_id=project_id,
            search_term=search_term,
            page_number=page_number,
            page_limit=page_limit,
        )
        logger.info(f"Retrieved all the connectors from db. total count: {total_count}")
        return (connectors, total_count)

    async def update_connector_async(
        self, user_id: str, connector_id: str, connector: Connector
    ) -> bool:
        logger.info("inside update connector.")

        # find the connector using connector_id
        existing_connector = self.get_connector_by_id_async(connector_id=connector_id)
        logger.info("Found requested connector.")

        if not existing_connector:
            logger.exception("Connector not found.")
            raise Exception("Connector not found")

        # validate the new connector
        if not self.is_valid_connector(connector):
            logger.exception(f"Not a valid connector. {connector}")
            raise Exception("Not a valid connector")

        connector.last_modified_by_id = user_id
        connector.last_modified_at = datetime.now(timezone.utc)

        update_flag = await self.connector_dao.update_connector_async(
            connector_id, connector
        )
        logger.info(f"Updated the connector with flag {update_flag}")

        return update_flag

    async def delete_connector_async(
        self, connector_id: str, user_id: str, superset_service: SupersetService
    ) -> DeleteConnectorResponse:
        logger.info("Inside delete connector.")

        # find the connector using connector_id
        existing_connector = await self.get_connector_by_id_async(
            connector_id=connector_id
        )
        logger.info("found connector to delete.")

        # if existing_connector.type in [
        #     ConnectorType.BIGQUERY,
        #     ConnectorType.SQLALCHEMY,
        #     ConnectorType.SNOWFLAKE,
        # ]:
        #     await superset_service.delete_database(existing_connector.database_id)
        #     logger.info(
        #         f"Deleted db {existing_connector.database_id} from superset also,"
        #     )

        if not existing_connector:
            logger.exception("Connector not found.")
            raise Exception("Connector not found")

        delete_conn_resp = await self.connector_dao.delete_connector_async(existing_connector, user_id)
        logger.info(f"{delete_conn_resp.message}")

        return delete_conn_resp

    def get_connector_by_id(self, connector_id: str) -> Connector:
        logger.info("inside get connector by id.")

        connector = self.connector_dao.get_connector(connector_id)
        logger.info("Found requested connector.")

        # validate connector
        if not self.is_valid_connector(connector):
            logger.exception(f"Not a valid connector. {connector}")
            raise Exception("Not a valid connector")

        return connector
