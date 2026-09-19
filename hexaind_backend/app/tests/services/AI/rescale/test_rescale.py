import json
import warnings
from bson import ObjectId
from datetime import datetime, timezone
from app.services.AI.rescale.service import RescaleService
from app.services.AI.rescale.schemas import RescaleConfig
from app.core.dao.dao_base import get_db_sync
from app.config.env_vars import environment
import pytest

# Ignore warnings during testing
warnings.filterwarnings('ignore')


# Define pytest fixtures for reusable components
@pytest.fixture
def db_client():
    """Establish connection to the database."""
    client = get_db_sync()
    db_name = environment.hexaind3_database_name
    db = client[db_name]
    yield db, client
    client.close()  # Ensure connection is closed after the test


@pytest.fixture
def input_data():
    """Load input data from JSON file."""
    with open('app/tests/services/AI/rescale/rescale_values.json', 'r') as f:
        return json.load(f)


# Perform the actual Rescale service test
def perform_rescale(config, kw_args, client):
    """Run rescale process with given config and kwargs."""
    obj = RescaleService(db_sync_client=client)
    rescale_config = RescaleConfig(**config)
    result = obj.run_rescale(parameters=rescale_config, **kw_args)
    
    # Assert the result has a valid tabular path
    assert result.tabular_path is not None, "Tabular path should not be None"
    return result


@pytest.mark.fixme
def test_ingest_fetch_connector(db_client, input_data):
    """Insert or fetch connector data from the database."""
    db, _ = db_client
    connector_data = input_data['connector']
    
    connector_data['created_at'] = datetime.now(timezone.utc)
    connector_data['last_modified_at'] = datetime.now(timezone.utc)
    connector_data['_id'] = ObjectId(connector_data['_id'])
    
    # Check if the document already exists, otherwise insert it
    document = db.connectors.find_one({"_id": ObjectId(connector_data['_id'])})
    if not document:
        db.connectors.insert_one(connector_data)


@pytest.mark.fixme
def test_rescale(db_client, input_data):
    """Test the RescaleService without batch mode."""
    _, client = db_client
    test_ingest_fetch_connector(db_client, input_data)
    
    data = input_data
    configs = data['configs']
    kw_args = {'workflow_name': 'AICED_CUST',
               'user_id':'user_id',
               'mobo_output': 'app/tests/services/AI/rescale/AICED_TEST/mobo_output.csv'}
    
    # Perform the rescale and assert the result
    result = perform_rescale(configs, kw_args, client)
    assert result is not None, "Result should not be None"