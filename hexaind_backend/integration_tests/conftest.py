import pathlib
import json
import os
import requests
from bson import json_util, ObjectId
import pytest
import pytest_asyncio
import pytest_mock
from mongomock_motor import AsyncMongoMockClient
from mongomock import MongoClient
from fastapi.testclient import TestClient
import asyncio


from app.core.db.db_utils import get_db_async, get_db_sync


@pytest.fixture(scope="session")
def mongo_client():
    return get_db_sync()


@pytest.fixture(scope="session")
async def async_mongo_client():
    return get_db_async()


@pytest.fixture(scope="session")
def api_url():
    return os.getenv("TEST_BE_API", "https://localhost:8080")

@pytest.fixture(scope="session")
def test_project_id():
    return "664ee2ced73a5a44b61aadd9"



@pytest.fixture(scope="session", autouse=True)
def load_data_to_db(mongo_client):
    db = mongo_client["Hexaind"]
    data_details = {
        "users": "resources/insert_users.json",
        "projects": "resources/insert_projects.json",
        "users_projects_mappings": "resources/insert_users_projects_mappings.json",
        "connectors": "resources/insert_connectors.json",
        "workflows" : "resources/insert_workflows.json",
        "runs" : "resources/insert_runs.json",
        "workflow_sessions" : "resources/insert_workflow_sessions.json",        
    }
    cwd = pathlib.Path(str(__file__))
    for db_collection in data_details:
        file_path = str(cwd.parent.absolute() / data_details[db_collection])
        data = json.loads(open(file_path).read(), object_hook=json_util.object_hook)

        collection = db[db_collection]
        for record in data:            
            primary_key = {"_id": record["_id"]}
            # for workflows, sessions and runs directly replacing them, might create issues with actions
            # so for now not updating them directly, incase we need it in future we can remove corresponding actions records
            if collection.find_one(primary_key) and db_collection in ['workflows','workflow_sessions', 'runs']:
                continue
            collection.update_one(primary_key, {"$set": record}, upsert=True)
    
    #deleting previous actions corresponding to master wf run
    db["actions"].delete_many({'run_id': '668ac62745ca9c5bddcd65d7'})


@pytest.fixture(scope="session")
def get_server_admin_form_login_response(api_url):
    email = "test01-databrickadmin@databrick-test.tech"
    password = "KJliu3bs41rivbQr"
    login_url = f"{api_url}/v1/authentication/login"

    response = requests.post(login_url, json={"email": email, "password": password})
    response.raise_for_status()

    return response.json()


@pytest.fixture(scope="session")
def get_default_users_form_login_response(api_url):
    email = "test02-databrickadmin@databrick-test.tech"  # FULL ACCESS
    password = "KJliu3bs41rivbQr"
    login_url = f"{api_url}/v1/authentication/login"

    response = requests.post(login_url, json={"email": email, "password": password})
    response.raise_for_status()

    return response.json()

  
@pytest.fixture(scope="session", autouse=True)
def logout_at_end(api_url):
    yield  # This fixture will run the following code after all tests are done
    email = "test01-databrickadmin@databrick-test.tech"
    logout_url = f"{api_url}/v1/authentication/logout?email={email}"

    response = requests.post(logout_url)
    response.raise_for_status()
