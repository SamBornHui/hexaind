import pytest
import pytest_mock
import pytest_asyncio

import pandas as pd

from app.services.admin.connectors.schemas import BigQueryAuthType
from app.services.data.bigquery.big_query_executor import (
    ServiceAccountQueryExecutor,
    UserAuthQueryExecutor,
    BqExecutorHelper,
    BqTableExecutorHelper,
    get_big_query_executor
)


@pytest.fixture
def service_account_query_executor(mocker):
    # Replace the build_query_job method with a simple function
    mocker.patch.object(ServiceAccountQueryExecutor, 'build_query_job', return_value="MockQueryJob")
    mocker.patch.object(ServiceAccountQueryExecutor, 'execute_query', return_value=pd.DataFrame([{"a": 1}]))

    auth_info = {}  # Replace with your actual service account info
    return ServiceAccountQueryExecutor(auth_info)


@pytest.fixture
def user_auth_query_executor(mocker):
    auth_info = {}  # Replace with your actual user auth info

    # Replace the build_query_job method with a simple function
    mocker.patch.object(UserAuthQueryExecutor, 'build_query_job',
                        side_effect=NotImplementedError("Bigquery UserAuth not yet implemented"))

    return UserAuthQueryExecutor(auth_info)


class SchemaField:
    def __init__(self, name, field_type):
        self.name = name
        self.field_type = field_type


class DummyResults:
    def to_dataframe(self):
        return pd.DataFrame([{"a": 1}])


class DryRunResults:
    def __init__(self, schema, tbp):
        self.schema = schema
        self.total_bytes_processed = tbp

    def result(self):
        return DummyResults()


@pytest.fixture
def bq_executor_helper(mocker):
    build_query_results = DryRunResults([SchemaField("col1", "FLOAT"), SchemaField("col2", "NUMERIC")], 1024)
    mocker.patch.object(ServiceAccountQueryExecutor, 'build_query_job', return_value=build_query_results)

    return BqExecutorHelper(ServiceAccountQueryExecutor({}), "SELECT * FROM table1")


@pytest.fixture
def bq_table_executor_helper(mocker):
    build_query_results = DryRunResults([SchemaField("col1", "FLOAT"), SchemaField("col2", "NUMERIC")], 1024)
    mocker.patch.object(ServiceAccountQueryExecutor, 'build_query_job', return_value=build_query_results)
    return BqTableExecutorHelper(ServiceAccountQueryExecutor, "table1", "dataset1")


@pytest.mark.asyncio
async def test_service_account_query_executor_build_query_job(service_account_query_executor):
    query_job = service_account_query_executor.build_query_job("SELECT * FROM table1")
    assert query_job == "MockQueryJob"


@pytest.mark.asyncio
async def test_service_account_query_executor_execute_query(service_account_query_executor):
    results = service_account_query_executor.execute_query("SELECT * FROM table1")
    assert results is not None
    assert results.shape == (1, 1)


@pytest.mark.asyncio
async def test_user_auth_query_executor_build_query_job(user_auth_query_executor):
    with pytest.raises(NotImplementedError):
        user_auth_query_executor.build_query_job("SELECT * FROM table1")


@pytest.mark.asyncio
async def test_user_auth_query_executor_execute_query(user_auth_query_executor):
    with pytest.raises(NotImplementedError):
        user_auth_query_executor.execute_query("SELECT * FROM table1")


@pytest.mark.asyncio
async def test_bq_executor_helper_execute(bq_executor_helper):
    results = bq_executor_helper.execute()
    assert results.shape == (1, 1)
    assert "a" in results.columns


@pytest.mark.asyncio
async def test_bq_executor_helper_dryrun(bq_executor_helper):
    # Mock the build_query_job method of the underlying executor

    schema, total_bytes_processed = bq_executor_helper.dryrun()

    res = {item.name: item.field_type for item in schema}
    assert set(res.keys()) == {"col1", "col2"}
    assert set(res.values()) == {"FLOAT", "NUMERIC"}
    assert total_bytes_processed == 1024


@pytest.mark.asyncio
async def test_bq_table_executor_helper_init(bq_table_executor_helper):
    assert bq_table_executor_helper.table_id == "table1"
    assert bq_table_executor_helper.dataset_id == "dataset1"
    assert bq_table_executor_helper.query == "SELECT * FROM `dataset1.table1`"


@pytest.mark.asyncio
async def test_get_big_query_executor():
    kwargs = {
        "auth_info": {}
    }

    res1 = get_big_query_executor(BigQueryAuthType.SERVICE_ACCOUNT, kwargs)
    res2 = get_big_query_executor(BigQueryAuthType.USER_AUTH, kwargs)

    assert "ServiceAccountQueryExecutor" in str(type(res1))
    assert "UserAuthQueryExecutor" in str(type(res2))
