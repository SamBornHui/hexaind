import os
import shutil
import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from app.api.endpoints.v1.data.folder_management.routes import FolderManagementRouter
from app.config.env_vars import environment
from app.services.data.folder_management.schema import *
from app.core.db.db_utils import get_db_sync
from app.services.data.assets.datasets.service import DatasetsService
from app.services.data.assets.datasets.schemas import  AccessMode
from bson import ObjectId


@pytest.mark.fixme
@pytest.mark.asyncio
async def test_create_folder():
    # prepare data
    db_client = AsyncIOMotorClient()
    params = {"destination_folder":str(environment.hexaind_data),
              "folder_name":"new_folder"}
    data = CreateFolder(**params)

    router = FolderManagementRouter()
    result = await router.create_folder(siteId="site123",projectId= "project_id",create_folder= data
                                        ,client=db_client)
    assert isinstance(result, dict)
    shutil.rmtree(result['folder_created_path'])



@pytest.mark.asyncio
@pytest.mark.fixme
async def test_move_assets():
    # prepare data

    source = "app/tests/api/v1/data/folder_management/move_assets_test_dir"
    destination = "app/tests/api/v1/data/folder_management/move_here"
    os.makedirs(source,exist_ok=True)
    db_client = AsyncIOMotorClient()
    os.makedirs(destination,exist_ok=True)
    params = {"source":source,
              "destination":destination}
    data = MoveAssets(**params)
    router = FolderManagementRouter()
    result = await router.move_assets(siteId="site123",projectId= "project_id",
                                      move_assets = data,client=db_client)
    assert isinstance(result, dict)

    shutil.rmtree(destination)

@pytest.mark.asyncio
@pytest.mark.fixme
async def test_rename_assets():
    rename_assets_test_dir = "app/tests/api/v1/data/folder_management/rename_assets_test_dir"
    os.makedirs(rename_assets_test_dir,exist_ok=True)
    params = {"source":rename_assets_test_dir,
              "new_name":"new_name_of_dir"}
    data = RenameAssets(**params)
    db_client = AsyncIOMotorClient()
    router = FolderManagementRouter()
    result = await router.rename_assets(siteId="site123",projectId= "project_id",
                                      rename_assets = data,client=db_client)
    assert isinstance(result, dict)
    shutil.rmtree("app/tests/api/v1/data/folder_management/new_name_of_dir")

@pytest.mark.asyncio
@pytest.mark.fixme
async def test_create_dataset_duplicate():
    client = get_db_sync()
    dataset_service_obj =  DatasetsService(db_sync_client=client)
    dataset_id = dataset_service_obj.save_tabular_dataset_helper_sync(input_data=str('app/tests/api/v1/data/folder_management/test_data.csv'),
                                                                  project_id='pro123', site_id='site123', user_id='user123',
                                                                action_id='action123', run_id='run_id', workflow_id='123',
                                                                  name='test_name', description='test_desc', access_mode=AccessMode.INTERNAL)

    params = {"user_id":"6627ea19552fed109188ddab",
              "datasetId":dataset_id,
              "datasetName":"duplicate_dataset",
              "folderPath":"app/tests/api/v1/data/folder_management"}
    data = CreateDatasetDuplicate(**params)
    db_client = AsyncIOMotorClient()
    router = FolderManagementRouter()
    result = await router.create_dataset_duplicate(siteId = "site123", projectId = "project_id",
                                      create_dataset = data, client = db_client)
    new_dataset_path = result['message'].split("at ")[-1]
    print(new_dataset_path)
    assert isinstance(result, dict)

    db = client[environment.hexaind3_database_name]
    document = db.datasets.find_one({'_id':ObjectId(dataset_id)})
    path = document["dataset_location"][0]["path"]
    db.datasets.delete_one({'_id':ObjectId(dataset_id)})
    db.datasets.delete_one({"dataset_location.0.path":new_dataset_path})
    os.remove(new_dataset_path)



@pytest.mark.asyncio
@pytest.mark.fixme
async def test_delete_assets():
    delete_assets_test_dir = "app/tests/api/v1/data/folder_management/delete_assets_test_dir"
    os.makedirs(delete_assets_test_dir,exist_ok=True)

    params = {"source":delete_assets_test_dir}
    data = DeleteAssets(**params)
    router = FolderManagementRouter()
    db_client = AsyncIOMotorClient()
    result = await router.delete_asset(siteId = "site123", projectId = "project_id",
                                      delete_assets = data, client = db_client)
    assert isinstance(result, dict)

