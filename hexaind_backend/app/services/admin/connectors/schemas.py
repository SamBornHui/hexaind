from datetime import datetime
from enum import Enum, auto
from pathlib import Path
import token
from typing import Any, Dict, List, Literal, Optional, Union, Annotated

from pydantic import BaseModel, Field, RootModel, model_validator
from Crypto.PublicKey import RSA

from app.services.data.bigquery.schemas import QueryParam

class ConnectorType(str, Enum):
    BIGQUERY = "BIGQUERY"
    RESCALE = "RESCALE"
    THERMOCALC = "THERMOCALC"
    SNOWFLAKE = "SNOWFLAKE"
    SQLALCHEMY = "SQLALCHEMY"


class BigQueryServiceAccountConfig(BaseModel):

    type: str

    project_id: str

    private_key_id: str

    private_key: str

    client_email: str

    client_id: str

    auth_uri: str

    token_uri: str

    auth_provider_x509_cert_url: str

    client_x509_cert_url: str

    # gcs_bucket_name: Optional[str] = None


class BigQueryUserAuthConfig(BaseModel):
    client_id: str
    client_secret: str
    refresh_token: str
    project_id: Optional[str]


class FileDetails(BaseModel):
    file_name: str
    file_path: Path


class UploadRescale(BaseModel):
    id: str
    file_name: str


class UploadRescaleResponse(BaseModel):
    rescale_files: List[UploadRescale]


class RescalePlatformFiles(BaseModel):
    connector_id: str
    rescale_files: Optional[UploadRescaleResponse] = Field(default=None)
    platform_files: Optional[List[FileDetails]] = Field(default=[])


class ThermocalcConnectorConfiguration(BaseModel):
    method: str = Field(..., description="Method for calling")
    host: str = Field(..., description="Host IP")
    path: str = Field(..., description="Application path")
    connector_type: Literal[ConnectorType.THERMOCALC]


class BigQueryAuthType(str, Enum):
    USER_AUTH = "USER_AUTH"
    SERVICE_ACCOUNT = "SERVICE_ACCOUNT"


class BigQueryConnectorConfiguration(BaseModel):
    authentication_type: BigQueryAuthType
    authentication_details: Union[BigQueryUserAuthConfig, BigQueryServiceAccountConfig]
    connector_type: Literal[ConnectorType.BIGQUERY]
    gcs_bucket_name: Optional[str] = None


class BigQueryServiceAccount(BaseModel):
    auth_type: Literal["SERVICE_ACCOUNT_FILE"]
    auth_object: BigQueryServiceAccountConfig


class BigQueryDefaultAuth(BaseModel):
    auth_type: Literal["GOOGLE_DEFAULT_LOGIN"]
    gcp_project_id: str


class BigQueryBrowserAuth(BaseModel):
    auth_type: Literal["BROWSER_LOGIN"]
    gcp_project_id: str


class BigQueryAuthentication(RootModel):
    root: Union[
        BigQueryServiceAccount,
        BigQueryDefaultAuth,
        BigQueryBrowserAuth,
        BigQueryUserAuthConfig,
    ]
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "auth_type": "SERVICE_ACCOUNT_FILE",
                    "auth_object": {
                        "type": "string",
                        "project_id": "string",
                        "private_key_id": "string",
                        "private_key": "string",
                        "client_email": "string",
                        "client_id": "string",
                        "auth_uri": "string",
                        "token_uri": "string",
                        "auth_provider_x509_cert_url": "string",
                        "client_x509_cert_url": "string",
                    },
                },
                {"auth_type": "GOOGLE_DEFAULT_LOGIN", "gcp_project_id": "healthy-saga"},
                {"auth_type": "BROWSER_LOGIN", "gcp_project_id": "healthy-saga"},
            ]
        }
    }


class BigQueryAuthResponse(BaseModel):
    status: int
    message: str


# class SnowflakeAuthMethods(str, Enum):
#     DEFAULT_METHOD = "DEFAULT_METHOD"
#     KEY_PAIR_METHOD = "KEY_PAIR_METHOD"


# class PrivateKeyType(str, Enum):
#     PEM = "PEM"
#     DER = "DER"


# class SnowflakeDefaultConfiguration(BaseModel):
#     account: str
#     user: str
#     password: str  # update it to encrypted storage
#     warehouse: str
#     database: str
#     schema: str
#     role: str


# class SnowflakeKeyPairConfiguration(BaseModel):
#     account: str
#     user: str
#     private_key: str  # path of the private key
#     private_key_type: PrivateKeyType = PrivateKeyType.PEM  # default pem from  ui
#     warehouse: str
#     database: str
#     schema: str
#     role: str

#     @model_validator(mode="after")  # take care of this
#     def return_private_key(self):
#         match self.private_key_type:
#             case PrivateKeyType.PEM:
#                 with open(self.private_key, "rb") as pem_in:
#                     pem_lines = pem_in.read()
#                     key = RSA.import_key(pem_lines)

#                 # Export the key in DER format
#                 self.private_key = key.export_key(format="DER")
#                 self.private_key_type = PrivateKeyType.DER
#             case PrivateKeyType.DER:
#                 pass

#         return self


# # class SnowflakeConnectorConfiguration(BaseModel):
# #     authentication_type: SnowflakeAuthMethods
# #     authentication_details: Union[
# #         SnowflakeDefaultConfiguration, SnowflakeKeyPairConfiguration
# #     ]


# class SnowflakeDefaultMethodConfig(BaseModel):
#     auth_type: Literal["DEFAULT_METHOD"]
#     auth_object: SnowflakeDefaultConfiguration


# class SnowflakeKeyPairMethodConfig(BaseModel):
#     auth_type: Literal["KEY_PAIR_METHOD"]
#     auth_object: SnowflakeKeyPairConfiguration


# SnowflakeConnectorConfiguration = Annotated[
#     Union[SnowflakeDefaultMethodConfig, SnowflakeKeyPairMethodConfig],
#     Field(discriminator="auth_type"),
# ]


class SnowflakeConnectorAuthenticationType(str, Enum):
    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: List[Any]
    ) -> Any:
        return name.upper()

    DEFAULT = auto()
    KEYPAIR = auto()


class SnowflakeConnectorKeyPairAuthenticationKeyType(str, Enum):
    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: List[Any]
    ) -> Any:
        return name.upper()

    DER = auto()
    PEM = auto()


class SnowflakeConnectorBaseAuthentication(BaseModel):
    sf_account: str
    sf_user: str
    sf_warehouse: str
    sf_database: str
    sf_schema: str
    sf_role: str
    # sf_region: Optional[str] = "us-central1"


class SnowflakeConnectorDefaultAuthentication(SnowflakeConnectorBaseAuthentication):
    authentication_type: Literal[SnowflakeConnectorAuthenticationType.DEFAULT]
    sf_password: str

class SnowflakeConnectorKeyPairAuthentication(SnowflakeConnectorBaseAuthentication):
    authentication_type: Literal[SnowflakeConnectorAuthenticationType.KEYPAIR]
    private_key_type: SnowflakeConnectorKeyPairAuthenticationKeyType = (
        SnowflakeConnectorKeyPairAuthenticationKeyType.PEM
    )
    private_key: bytes | Path

    @model_validator(mode="after")
    def return_private_key(self):
        match self.private_key_type:
            case SnowflakeConnectorKeyPairAuthenticationKeyType.PEM:
                with open(self.private_key, "rb") as pem_in:
                    pem_lines = pem_in.read()
                    key = RSA.import_key(pem_lines)

                # Export the key in DER format
                self.private_key = key.export_key(format="DER")
                self.private_key_type = (
                    SnowflakeConnectorKeyPairAuthenticationKeyType.DER
                )
            case SnowflakeConnectorKeyPairAuthenticationKeyType.DER:
                pass

        return self


class SnowflakeConnectorAuthentication(RootModel):
    root: Union[
        SnowflakeConnectorDefaultAuthentication, SnowflakeConnectorKeyPairAuthentication
    ] = Field(discriminator="authentication_type")
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "auth_type": "DEFAULT_METHOD",
                    "auth_object": {
                        "user": "string",
                        "password": "string",
                        "account": "string",
                        "warehouse": "string",
                        "database": "string",
                        "schema": "string",
                        "role": "string",
                    },
                },
            ]
        }
    }


class SnowflakeConnectorConfiguration(BaseModel):
    connection_string: Optional[str] = ""
    connector_type: Literal[ConnectorType.SNOWFLAKE]
    authentication: SnowflakeConnectorAuthentication


class RescaleAuth(BaseModel):
    token: Optional[str] = Field(default=None, description="token Id")


class RescaleConnectorConfiguration(BaseModel):
    token: str
    connector_type: Literal[ConnectorType.RESCALE]

class SQLAlchemyConnectorConfiguration(BaseModel):
    connection_string: str
    connector_type: Literal[ConnectorType.SQLALCHEMY]


class Connector(BaseModel):

    id: Optional[str] = Field(default=None, description="Connector Id", alias="_id")

    name: str = Field(..., description="user defined name for a connector")

    description: str = Field(
        default="", description="user defined description for a connector"
    )

    type: ConnectorType = Field(..., description="Type of connector")

    configuration: Union[
        SnowflakeConnectorConfiguration,
        BigQueryConnectorConfiguration,
        RescaleConnectorConfiguration,
        ThermocalcConnectorConfiguration,
        SQLAlchemyConnectorConfiguration,
    ] = Field(..., description="Configuration for the connector", discriminator="connector_type")

    owner_id: str = Field(
        default=None, description="ID of the user who created the connector"
    )

    owner_name: str = Field(
        default=None, description="Name of the user who created the connector"
    )

    created_at: Optional[datetime] = Field(default=None, description="created datetime")

    last_modified_by_id: str = Field(
        default=None, description="ID of the user who recently modified the connector"
    )

    last_modified_at: datetime = Field(
        default=None, description="Created Date and Time UTC format"
    )

    project_id: str = Field(default=None, description="Project ID")

    site_id: str = Field(default=None, description="Project ID")

    version: str = Field(
        default="1.0", description="Version of the connector", read_only=True
    )

    is_active: Optional[bool] = Field(default=True, description="False to marked as deleted")

    database_id: Optional[int] = None


class CreateConnectorResponse(BaseModel):

    connector_id: str


class ConnectorListResponse(BaseModel):

    connectors: List[Connector]

    total_count: int


class UpdateConnectorResponse(BaseModel):

    success: bool


class DeleteConnectorResponse(BaseModel):

    success: bool
    message: str

class DataPullConfig(BaseModel):
    superset_connector_id: int
    batch_size: int = 1000
    query: str
    token: str


class Query(BaseModel):

    id: Optional[str] = Field(default=None, description="query Id", alias="_id")
    name: str = Field(..., description="user defined name for a query")
    query_type: ConnectorType = Field(
        description="Type of query", default=ConnectorType.BIGQUERY
    )
    query: str = Field(..., description="SQL Query")
    query_params: Dict[str, QueryParam] = {}
    connector_id: str = Field(..., description="BigQuery Connector id")
    owner_id: str = Field(
        default=None, description="ID of the user who created the query"
    )
    owner_name: str = Field(
        default=None, description="Name of the user who created the query"
    )
    created_at: Optional[datetime] = Field(default=None, description="created datetime")
    last_modified_by_id: str = Field(
        default=None, description="ID of the user who recently modified the query"
    )
    last_modified_at: datetime = Field(
        default=None, description="Created Date and Time UTC format"
    )
    project_id: str = Field(default=None, description="Project ID")
    site_id: str = Field(default=None, description="Site ID")
    version: str = Field(
        default="1.0", description="Version of the query", read_only=True
    )


class CreateQueryResponse(BaseModel):
    query_id: str


class CreateQueryRequest(BaseModel):
    dataset_name: Optional[str] = ""
    table_name: Optional[str] = ""
    query: Optional[str] = ""
    query_params: Optional[dict] = {}
    query_type: ConnectorType = ConnectorType.BIGQUERY
    name: str
    connector_id: str


class UpdateQueryRequest(BaseModel):
    query_id: str
    query: str
    query_params: Dict[str, QueryParam] = {}


class GenericQueryResponse(BaseModel):
    succeeded: bool
    message: str


class QueryListResponse(BaseModel):
    queries: List[Query]
    total_count: int
