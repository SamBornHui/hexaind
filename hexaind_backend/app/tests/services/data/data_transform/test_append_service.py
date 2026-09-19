from datetime import datetime
import pytest

from app.services.workflows.designer.schemas import ColumnAndType, ColumnType
from app.core.services.data_transformation.tabular.schemas import AppendModel
from app.services.data.assets.datasets.service import DatasetsService
from app.core.services.data_transformation.tabular.service import DataTransformAppendService

from mongomock_motor import AsyncMongoMockClient
import pandas as pd
def get_sample_dataset():
    return {'version': '1.0', 
            'user_id': '65967ecac48951a0928b7dac',
            'project_id': 'p1', 
            'site_id': 's1', 
            'action_id': '', 
            'name': 'append_01', 
            'description': 'append_01', 
            'dataset_type': 'TABULAR', 
            'dataset_information': [{'preview': None, 'statistics': None, 'visualize': None, 'schema': None}], 
            'upload_status': 'COMPLETED', 'upload_stats': {'percentage': '100%'}, 'metadata': {}, 
            'created_at': datetime(2024, 1, 2, 13, 30, 59, 350000), 
            'dataset_location': [{'isfolder': False, 'size': '3139', 'extension': '.csv', 'path': '', 
                                  'last_modified_by': None, 'last_modified_at': datetime(2024, 1, 2, 13, 30, 59, 336000)}], 
                                  'access_mode': 'EXTERNAL', 'tags': []}




@pytest.fixture
def mocked_async_client():
    return AsyncMongoMockClient()

@pytest.mark.asyncio
@pytest.mark.fixme
async def test_transform_append(mocked_async_client):

    csv1_path = 'app/tests/resources/input1.csv'
    csv2_path = 'app/tests/resources/input1_1.csv'
    dataset_json = get_sample_dataset()
    dataset_json['dataset_location'][0]['path'] = csv1_path
    
    ds1_ins = await mocked_async_client.Hexaind.datasets.insert_one(dataset_json)

    dataset_json.pop('_id')
    dataset_json['dataset_location'][0]['path'] = csv2_path
    dataset_json['name'] = 'append_01'
    ds2_ins = await mocked_async_client.Hexaind.datasets.insert_one(dataset_json)

    datasets_service = DatasetsService(db_async_client=mocked_async_client)
   
    dset1 = await datasets_service.get_dataset_by_id(ds1_ins.inserted_id)
    dset2 = await datasets_service.get_dataset_by_id(ds2_ins.inserted_id)

    data_transform_service = DataTransformAppendService()


    max_rows = 0
    col_name = "Age"
    col_type = ColumnType.INT_TYPE
    age_as_int = ColumnAndType(column_name=col_name,pref_type=col_type)
    append_model = AppendModel(datasets_list=[dset1, dset2], max_rows=max_rows, ignore_index=True, column_type_pref_list = [age_as_int], convert_words_to_number= True)
    appended_file_path = await data_transform_service.transform_append(append_model, dataset_json['user_id'], "/hexaind-data/datasets/results")

    df = pd.read_csv(appended_file_path)
    if col_name  in df.columns:
        assert df[col_name].dtype==col_type

    len_res_df = len(df)

    df = pd.read_csv(csv1_path)
    len_df1 = len(df)

    df = pd.read_csv(csv2_path)
    len_df2 = len(df)

    tot_rows = len_df1 + len_df2

    exp_res_rows = tot_rows
    if max_rows > 0 and max_rows < tot_rows:
        exp_res_rows = max_rows

    assert len_res_df == exp_res_rows

 
