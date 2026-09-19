from bson import ObjectId

from app.core.services.save_datasets.service import SaveService
from app.services.data.assets.datasets.dao import DatasetsDao
from app.services.workflows.designer.schemas import *
import pytest
import pytest_mock
import pytest_asyncio
from app.services.data.assets.datasets.service import DatasetsService
from app.services.data.assets.datasets.schemas import (
    AccessMode,
    DatasetSourceFormats,
    DatasetMetadata,
)
import datetime
from app.config.env_vars import environment
from pathlib import Path


@pytest.fixture
def common_setup_for_save_service(
    mocker, mocked_db_sync_client, mocked_db_async_client
):
    mocker.patch("app.core.dao.dao_base.isinstance", return_value=True)

    csv_file = Path(__file__).parent.absolute() / "test_data.csv"

    dataset_service_obj = DatasetsService(
        db_sync_client=mocked_db_sync_client, db_async_client=mocked_db_async_client
    )
    dataset_id = dataset_service_obj.save_tabular_dataset_helper_sync(
        input_data=str(csv_file),
        project_id="pro123",
        site_id="site123",
        user_id="user123",
        action_id="action123",
        run_id="run_id",
        workflow_id="123",
        name="test_name",
        description="test_desc",
        access_mode=AccessMode.INTERNAL,
    )
    timestamp = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"test_data{timestamp}"
    base_path = str(environment.base_path)

    kwargs = {
        "user_id": "1",
        "project_id": "1",
        "site_id": "1",
        "action_id": "1",
        "dataset_id": dataset_id,
    }

    return {"file_name": filename, "kwargs": kwargs, "base_path": base_path}


@pytest.mark.fixme
def test_save_success(
    mocker, mocked_db_sync_client, mocked_db_async_client, common_setup_for_save_service
):
    mocker.patch("app.core.dao.dao_base.isinstance", return_value=True)
    filename = common_setup_for_save_service["file_name"]
    kwargs = common_setup_for_save_service["kwargs"]
    obj = {
        "dataset_name": "test_Widget-CSV_FILE-6AxQ_Tabular",
        "destination_type": "HEXAIND_PLATFORM",
        "destination_config": {
            "file_Format": "CSV",
            "save_options": "SAVE_AS",
            "save_option_config": {"file_name": filename},
            "destination_folder_path": "",
        },
    }
    save_config = DatasetConfiguration(**obj)
    datasets_dao = DatasetsDao(
        db_sync_client=mocked_db_sync_client, db_async_client=mocked_db_async_client
    )
    save_service = SaveService(
        user_id="1",
        project_id="1",
        old_dataset_id=kwargs["dataset_id"],
        site_id="1",
        action_id="1",
        workflow_id="1",
        run_id="1",
        dataset_dao=datasets_dao,
    )
    metadata = DatasetMetadata(
        data_source=DatasetSourceFormats.GENERATED_IN_WORKFLOW_EXECUTION_FORMAT.format(
            "SAVE"
        )
    )
    dataset_id = save_service.save_dataset(save_config, metadata)

    dataset = mocked_db_sync_client["Hexaind"]["datasets"].find_one(
        {"_id": ObjectId(dataset_id)}
    )
    assert dataset["project_id"] == "1"
    assert dataset["dataset_type"] == "TABULAR"
    assert len(dataset["dataset_location"]) == 1


@pytest.mark.fixme
def test_save_failure(
    mocker, mocked_db_sync_client, mocked_db_async_client, common_setup_for_save_service
):
    mocker.patch("app.core.dao.dao_base.isinstance", return_value=True)
    filename = common_setup_for_save_service["file_name"]
    kwargs = common_setup_for_save_service["kwargs"]
    base_path = common_setup_for_save_service["base_path"]
    obj = {
        "dataset_name": "test_Widget-CSV_FILE-6AxQ_Tabular",
        "destination_type": "HEXAIND_PLATFORM",
        "destination_config": {
            "file_Format": "CSV",
            "save_options": "SAVE_AS",
            "save_option_config": {"file_name": filename},
            "destination_folder_path": "",
        },
    }

    def mocked_new_save_as_dataset(
        save_config: SaveAsConfig, dataset_name: str, custom_information=None
    ):
        raise Exception("raising mocked exception for testing")

    mocker.patch(
        "app.core.services.save_datasets.service.SaveService.new_save_as_dataset",
        side_effect=mocked_new_save_as_dataset,
    )
    save_config = DatasetConfiguration(**obj)
    datasets_dao = DatasetsDao(
        db_sync_client=mocked_db_sync_client, db_async_client=mocked_db_async_client
    )
    save_service = SaveService(
        user_id="1",
        project_id="1",
        old_dataset_id=kwargs["dataset_id"],
        site_id="1",
        action_id="1",
        workflow_id="1",
        run_id="1",
        dataset_dao=datasets_dao,
    )
    with pytest.raises(Exception):
        save_service.save_dataset(save_config)
