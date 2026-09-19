import pytest
import pytest_mock
import pytest_asyncio

from app.services.admin.connectors.schemas import BigQueryConnectorConfiguration
from app.services.data.bigquery.big_query_executor import BqExecutorHelper, QueryExecutor
from app.services.data.bigquery.schemas import SchemaField, DryRunResponseModel, SchemaFieldType
from app.services.data.bigquery.service import BigQueryService
from app.services.workflows.designer.schemas import BigQueryDatasetConfiguration
from app.tests.services.data.bigquery.test_big_query_executor import SchemaField as TestSchemaField
from mongomock import MongoClient
from mongomock_motor import AsyncMongoMockClient

@pytest.fixture
def sync_mongo_client():
    return MongoClient()


@pytest.fixture
def async_mongo_client():
    return AsyncMongoMockClient()

def get_mock_dry_run_results():
    return [TestSchemaField("col1", "FLOAT"),
            TestSchemaField("col2", "NUMERIC")], 1024


def get_mock_dry_run_response_model():
    return DryRunResponseModel(fields=[
        SchemaField(name="col1", field_type=SchemaFieldType.NUMERIC),
        SchemaField(name="col2", field_type=SchemaFieldType.NUMERIC)],
        size=1024)


def get_mock_bigquery_connector_config():
    return {
        "authentication_type": "SERVICE_ACCOUNT",
        "authentication_details": {
            "type": "service_account",
            "project_id": "healthy-saga-327423",
            "private_key_id": "1",
            "private_key": "2",
            "client_email": "3",
            "client_id": "117477604032134058122",
            "auth_uri": "4",
            "token_uri": "5",
            "auth_provider_x509_cert_url": "",
            "client_x509_cert_url": ""
        }
    }


def get_mock_bigquery_dataset_config():
    return {
        "bigquery_connector_id": "658aea3e9b4341f250e66888",
        "dataset_configuration": {
            "project_id": "healthy-saga-327423",
            "dataset_type": "TABLE",
            "dataset": {
                "dataset_name": "test_demo",
                "table_name": "BOSTONTRAIN"
            }
        }
    }


@pytest.fixture
def bq_executor_helper(mocker):
    mock_dryrun_results = get_mock_dry_run_results()
    mocker.patch.object(BqExecutorHelper, 'dryrun', return_value=mock_dryrun_results)

    class TempQueryExecutor(QueryExecutor):
        def build_query_job(self, query, kwargs=None):
            pass

        def execute_query(self, query, kwargs=None):
            pass

    return BqExecutorHelper(TempQueryExecutor(), "SELECT * FROM table1")


@pytest.mark.asyncio
@pytest.mark.fixme
def test_bigquery_dryrun(bq_executor_helper):
    expected = get_mock_dry_run_response_model()
    connector_config = BigQueryConnectorConfiguration(**get_mock_bigquery_connector_config())
    dataset_config = BigQueryDatasetConfiguration(**get_mock_bigquery_dataset_config())
    actual = BigQueryService(db_async_client=async_mongo_client).bigquery_dryrun(connector_config, dataset_config)
    assert actual == expected
