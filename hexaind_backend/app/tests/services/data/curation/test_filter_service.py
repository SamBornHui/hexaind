import pytest
from uuid import uuid4
import os

from app.services.workflows.designer.schemas import FilterActivityConfig, FilterType, FilterOperator, FilterConfig, FilterOperand, FilterValues
from app.services.data.curation.service import filter_data_by_column_handler

from mongomock_motor import AsyncMongoMockClient
from app.config.env_vars import environment
from app.services.workflows.designer.base_schemas import WidgetType
import dask.dataframe as dd


@pytest.fixture
def mocked_async_client():
    return AsyncMongoMockClient()

@pytest.mark.asyncio

async def test_filter_service(mocked_async_client):

    csv1_path = 'app/tests/resources/penguin.csv'
    dataframe = dd.read_csv(csv1_path)

    filter_vals = [FilterValues(column_name = 'culmen_length_mm', operator = FilterOperator.GT, value = 40),
                   FilterValues(column_name = 'culmen_depth_mm', operator = FilterOperator.GT, value = 20)]
    filter_config = FilterConfig(filter_operands = [FilterOperand.AND], filter_values = filter_vals)
    filter_act_config = FilterActivityConfig(widget_type = WidgetType.FILTER, type = FilterType.FILTER_BY_COLUMN_VALUES, config = filter_config)

    dir_path = environment.datasets_folder
    file_name = f"FL_dataset_{uuid4()}.csv"
    file_path = os.path.join(dir_path, file_name)


    file_path = filter_data_by_column_handler(dataframe=dataframe, filter_config=filter_act_config, dest_path=file_path)

    filtered_dataframe = (dd.read_csv(file_path)).compute()

    dataframe = (dataframe[(dataframe['culmen_length_mm'] > 40) & (dataframe['culmen_depth_mm'] > 20)]).reset_index(drop=True).compute()

    proposed_count = len(dataframe)
    result_cnt = len(filtered_dataframe)
    assert result_cnt == proposed_count
    assert dataframe.equals(filtered_dataframe)
