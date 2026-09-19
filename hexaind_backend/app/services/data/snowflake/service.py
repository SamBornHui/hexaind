import logging
from typing import Union

import snowflake.connector as snow
from Crypto.PublicKey import RSA
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from app.services.admin.connectors.schemas import (
    Connector,
    SnowflakeConnectorAuthentication,
    SnowflakeConnectorDefaultAuthentication,
    SnowflakeConnectorKeyPairAuthentication,
)
from app.services.data.assets.datasets.dao import DatasetsDao
from app.services.data.snowflake.schemas import (
    AuthenticationResponse,
    SFPreviewRequest,
    SnowFlakeDatasetTypes,
)
from app.services.workflows.designer.schemas import DataCopyActivityConfig

logger = logging.getLogger(__package__)


class SnowflakeService:
    def __init__(
        self,
        db_sync_client: MongoClient = None,
        db_async_client: AsyncIOMotorClient = None,  # type: ignore
    ) -> None:
        self.datasets_dao = DatasetsDao(
            db_sync_client=db_sync_client, db_async_client=db_async_client
        )

    # def return_private_key(self, private_key_path: str):
    #     with open(private_key_path, "rb") as pem_in:
    #         pem_lines = pem_in.read()
    #         key = RSA.import_key(pem_lines)

    #     # Export the key in DER format
    #     der = key.export_key(format="DER")
    #     return der

    def snowflake_connection(self, authentication: SnowflakeConnectorAuthentication):
        match authentication_config := authentication.root:
            case SnowflakeConnectorDefaultAuthentication():
                conn = snow.connect(
                    user=authentication.root.sf_user,
                    password=authentication.root.sf_password,
                    account=authentication.root.sf_account,
                    warehouse=authentication.root.sf_warehouse,
                    database=authentication.root.sf_database,
                    schema=authentication.root.sf_schema,
                    role=authentication.root.sf_role
                    # **authentication_config.model_dump(
                    #     by_alias=True, exclude=["authentication_type"]
                    # )
                )

            case SnowflakeConnectorKeyPairAuthentication():
                conn = snow.connect(
                    **authentication_config.model_dump(
                        by_alias=True,
                        exclude=["private_key_type", "authentication_type"],
                    )
                )

            case _:
                raise NotImplementedError(
                    "Requested method is not implemented at this moment."
                )

        cursor = conn.cursor()
        return conn, cursor

    def snowflake_authentication(
        self, authentication: SnowflakeConnectorAuthentication
    ):
        try:
            connection = None
            cursor = None
            connection, cursor = self.snowflake_connection(
                authentication=authentication
            )

            # Execute a SQL query against Snowflake to get the current_version
            cursor.execute("SELECT current_version()")
            one_row = cursor.fetchone()

            if one_row[0] is not None:
                return AuthenticationResponse(
                    status=True, message="Authentication Success"
                )

        except snow.errors.Error as e:
            return AuthenticationResponse(
                status=False, message=f"Authentication Failed (SF): {str(e)}"
            )

        except Exception as e:
            return AuthenticationResponse(
                status=False, message=f"Authentication Failed v1: {str(e)}"
            )

        finally:
            try:
                cursor.close()
                connection.close()

            except Exception as e:
                return AuthenticationResponse(
                    status=False, message=f"Authentication Failed v2: {str(e)}"
                )

    async def get_databases_list(self, connector: Connector):
        try:
            connection, cursor = self.snowflake_connection(
                authentication=connector.configuration.authentication
            )
            query = """SHOW DATABASES"""
            cursor.execute(command=query)
            results = cursor.fetchall()
            databases_list = [row[1] for row in results]

            return databases_list

        except snow.errors.Error as e:
            raise ValueError(f"Unable to fetch databases: {str(e)}")

        finally:
            cursor.close()
            connection.close()

    async def get_schemas_list(self, database_name: str, connector: Connector):
        try:
            connection, cursor = self.snowflake_connection(
                authentication=connector.configuration.authentication
            )
            query = f"""SHOW SCHEMAS IN DATABASE {database_name.upper()}"""
            cursor.execute(command=query)
            results = cursor.fetchall()
            schemas_list = [row[1] for row in results]

            return schemas_list

        except snow.errors.Error as e:
            raise ValueError(
                f"Unable to fetch schemas from database {database_name}: {str(e)}"
            )

        finally:
            cursor.close()
            connection.close()

    async def get_tables_list(
        self, database_name: str, schema_name: str, connector: Connector
    ):
        try:
            connection, cursor = self.snowflake_connection(
                authentication=connector.configuration.authentication
            )
            query = f"""SHOW SCHEMAS IN DATABASE {database_name.upper()}.{schema_name.upper()}"""
            cursor.execute(command=query)
            results = cursor.fetchall()
            tables_list = [row[1] for row in results]

            return tables_list

        except snow.errors.Error as e:
            raise ValueError(
                f"Unable to fetch tables for schema {database_name}.{schema_name}: {str(e)}"
            )

        finally:
            cursor.close()
            connection.close()

    async def get_data_preview(self, connector: Connector, config: SFPreviewRequest):
        try:
            connection, cursor = self.snowflake_connection(
                authentication=connector.configuration.authentication
            )

            if not config.query_config:
                query = f"SELECT * FROM {config.database_name.upper()}.{config.schema_name.upper()}.{config.table_name.upper()} LIMIT 20"
                cursor.execute(command=query)
            else:
                if not any(
                    word.lower() == "limit"
                    for word in config.query_config.query.split()
                ):
                    config.query_config.query = f"{config.query_config.query} LIMIT 20"
                    cursor.execute(
                        command=config.query_config.query,
                        params=config.query_config.query_params,
                    )

            data = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return columns, data

        except snow.errors.Error as e:
            raise ValueError(f"Unable to fetch preview data: {str(e)}")

        finally:
            cursor.close()
            connection.close()

    def snowflake_data_copy_handler(
        self,
        snowflake_connector_obj: Connector,
        snowflake_config: DataCopyActivityConfig,
        dest_path: str,
    ):
        try:
            configuration = snowflake_connector_obj.configuration
            dataset_configuration = (
                snowflake_config.source.configuration.dataset_configuration
            )

            connection, cursor = self.snowflake_connection(authentication=configuration)
            dataset = dataset_configuration.dataset

            match dataset_configuration.dataset_type:
                case SnowFlakeDatasetTypes.TABLE:
                    query = f"SELECT * FROM {dataset.database_name}.{dataset.schema_name.upper()}.{dataset.table_name.upper()}"
                    cursor.execute(command=query)

                case SnowFlakeDatasetTypes.QUERY:
                    query = dataset.query
                    query_params = dataset.query_params
                    cursor.execute(command=query, params=query_params)

                case _:
                    raise NotImplementedError(
                        "Requested method is not implemented at this moment."
                    )

            df = cursor.fetch_pandas_all()

            # Write the DataFrame to a file
            if dest_path.endswith(".csv"):
                df.to_csv(dest_path, index=False)

            elif dest_path.endswith(".parquet"):
                df.to_parquet(dest_path, index=False)
            else:
                raise ValueError("Unsupported file format. Use .csv or .parquet")

            return dest_path

        except snow.errors.Error as e:
            raise ValueError(f"Unable to pull data: {str(e)}")

        finally:
            cursor.close()
            connection.close()
