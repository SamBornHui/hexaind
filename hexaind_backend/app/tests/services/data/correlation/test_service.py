import pytest
from app.services.data.correlation.service import CorrelationService
from app.services.data.correlation.schemas import CorrelationInputSchema, CorrelationResponse
from dask.dataframe import DataFrame
import dask.dataframe as dd
import pandas as pd
from mongomock_motor import AsyncMongoMockClient
from datetime import datetime, timezone

@pytest.fixture
def mocked_async_client():
    return AsyncMongoMockClient()

def get_sample_dataset():
    return {'version': '1.0', 'user_id': '',
            'project_id': 'p1', 
            'site_id': 's1', 
            'action_id': '', 
            'name': 'join1_100', 
            'description': 'join1_100', 
            'dataset_type': 'TABULAR', 
            'dataset_information': [{'preview': None, 'statistics': None, 'visualize': None, 'schema': None}], 
            'upload_status': 'COMPLETED', 'upload_stats': {'percentage': '100%'}, 'metadata': {}, 
            'created_at': datetime(2024, 1, 2, 13, 30, 59, 350000), 
            'dataset_location': [{'isfolder': False, 'size': '3139', 'extension': '.csv', 'path': 'app/tests/resources/penguin.csv',
                                  'last_modified_by': None, 'last_modified_at': datetime(2024, 1, 2, 13, 30, 59, 336000)}], 
                                  'access_mode': 'EXTERNAL', 'tags': []}

excepted_res = {'corr_heatmap': 
                {'heatmap_data_x': ['species', 'island', 'culmen_length_mm', 'culmen_depth_mm', 'flipper_length_mm', 'body_mass_g', 'sex'], 
                 'heatmap_data_y': ['species', 'island', 'culmen_length_mm', 'culmen_depth_mm', 'flipper_length_mm', 'body_mass_g', 'sex'], 
                 'heatmap_data_z': [[1.0, 0.66, 0.72, 0.7, 0.58, 0.75, 0.0], 
                                    [0.66, 1.0, 0.37, 0.53, 0.42, 0.58, 0.09], 
                                    [0.72, 0.37, 1.0, 0.12, 0.76, 0.67, 0.41], 
                                    [0.7, 0.53, 0.12, 1.0, 0.08, -0.16, 0.41], 
                                    [0.58, 0.42, 0.76, 0.08, 1.0, 0.82, 0.39], 
                                    [0.75, 0.58, 0.67, -0.16, 0.82, 1.0, 0.45], 
                                    [0.0, 0.09, 0.41, 0.41, 0.39, 0.45, 1.0]], 
                'heatmap_data_colorscale': [[0.0, 'rgb(103,0,31)'], 
                                            [0.1, 'rgb(178,24,43)'], 
                                            [0.2, 'rgb(214,96,77)'], 
                                            [0.3, 'rgb(244,165,130)'], 
                                            [0.4, 'rgb(253,219,199)'], 
                                            [0.5, 'rgb(247,247,247)'], 
                                            [0.6, 'rgb(209,229,240)'], 
                                            [0.7, 'rgb(146,197,222)'], 
                                            [0.8, 'rgb(67,147,195)'], 
                                            [0.9, 'rgb(33,102,172)'], 
                                            [1.0, 'rgb(5,48,97)']]}}


@pytest.mark.fixme
@pytest.mark.asyncio
async def test_correlation_service(mocked_async_client):

    ins_res = await mocked_async_client.Hexaind.datasets.insert_one(get_sample_dataset())

    corr_schema = CorrelationInputSchema(dataset_id=str(ins_res.inserted_id), columns=[])
    correlation_service = CorrelationService(db_async_client=mocked_async_client)
    result = await correlation_service.correlation(corr_schema)

    assert isinstance(result, CorrelationResponse)
    assert result.model_dump() == excepted_res

    # TODO: Need to add test cases for Failure scenarios

