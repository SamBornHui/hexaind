from pymongo import MongoClient
import warnings
import pytest
warnings.filterwarnings('ignore')
import sys
sys.path.append('../')
sys.path.append('../../../../../')

from ..service import PostRescaleService


def perform_post_rescale(params):
    db_config = dict(db_address = '192.168.0.66' + ':27017', db_name = "Databrick", db_username = "Databrick", db_password = "test")
    client = MongoClient(db_config['db_address'],
                            username=db_config['db_username'],
                            password=db_config['db_password'],
                            authSource=db_config['db_name'])

    obj = PostRescaleService(db_sync_client=client)
    result = obj.run_post_rescale(params)
    assert type(result) == str

@pytest.mark.fixme
def test_post_rescale():
    payload = {'rescale_output': 'AICED_CUSTOM/batch_30/pytest_rescale_output.json',
           'post_rescale_dir': 'AICED_CUSTOM/'
    }
    perform_post_rescale(payload)
