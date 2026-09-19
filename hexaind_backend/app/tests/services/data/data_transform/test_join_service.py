from datetime import datetime
import pytest

from pathlib import Path
from app.services.workflows.designer.schemas import JoinType
from app.core.services.data_transformation.tabular.schemas import JoinModel
from app.services.data.assets.datasets.service import DatasetsService
from app.core.services.data_transformation.tabular.service import DataTransformJoinService
from app.config.env_vars import environment

from mongomock_motor import AsyncMongoMockClient
import pandas as pd
def get_sample_dataset():
    return {'version': '1.0', 
            'user_id': '65967ecac48951a0928b7dac',
            'project_id': 'p1', 
            'site_id': 's1', 
            'action_id': '', 
            'name': 'join_01', 
            'description': 'join_01', 
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
async def test_transform_join(mocked_async_client):

    csv1_path = 'app/tests/resources/input1.csv'
    csv2_path = 'app/tests/resources/input_join_2.csv'
    dataset_json = get_sample_dataset()
    dataset_json['dataset_location'][0]['path'] = csv1_path
    
    ds1_ins = await mocked_async_client.Hexaind.datasets.insert_one(dataset_json)

    dataset_json.pop('_id')
    dataset_json['dataset_location'][0]['path'] = csv2_path
    dataset_json['name'] = 'join_02'
    dataset_json['description'] = 'join_02'
    ds2_ins = await mocked_async_client.Hexaind.datasets.insert_one(dataset_json)

    datasets_service = DatasetsService(db_async_client=mocked_async_client)
   
    dset1 = await datasets_service.get_dataset_by_id(ds1_ins.inserted_id)
    dset2 = await datasets_service.get_dataset_by_id(ds2_ins.inserted_id)

    data_transform_service = DataTransformJoinService()
    
    left_columns = ['ID']
    right_columns = ['ID']
    join_model = JoinModel(left_dataset=dset1, right_dataset=dset2, join_type=JoinType.INNER.value, left_columns=left_columns, right_columns=right_columns)
    file_path_prefix = str(Path(__file__).parent.parent.parent.parent/'resources')
    joined_file_path = await data_transform_service.transform_join(join_model, dataset_json['user_id'], file_path_prefix)

    df_res = pd.read_csv(joined_file_path)
    col_cnt_res_df = len(df_res.columns)

    df1 = pd.read_csv(csv1_path)
    left_ds_cols = df1.columns
    col_cnt_df1 = len(left_ds_cols)

    df2 = pd.read_csv(csv2_path)
    right_ds_cols = (df2.columns)
    col_cnt_df2 = len(right_ds_cols)

    right_cols_dupl_of_left = list(set(right_columns) - set(left_columns))
    right_ds_cols = set(df1.columns) - set(right_cols_dupl_of_left)


    exp_col_res_cols_cnt = col_cnt_df1 + col_cnt_df2 - len(left_columns)
    assert col_cnt_res_df == exp_col_res_cols_cnt

    for col in left_ds_cols:
        if col not in df_res.columns:
            assert False

    for col in right_ds_cols:
        if col not in df_res.columns:
            assert False
