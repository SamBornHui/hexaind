from pathlib import Path

import pytest
import pytest_mock
import pytest_asyncio
from mongomock.mongo_client import MongoClient
from mongomock_motor import AsyncMongoMockClient

from app.services.data.assets.custom_python_widget_recipes.schemas import (CustomPythonWidgetRecipe)
from app.services.data.assets.custom_python_widgets.schemas import CustomPythonWidget

from app.services.data.assets.custom_python_widgets.service import CustomPythonWidgetServiceHelper


@pytest.fixture
def mocked_async_client():
    return AsyncMongoMockClient()


@pytest.fixture
def mocked_sync_client():
    return MongoClient()


@pytest.fixture
def helper(mocker, mocked_sync_client, mocked_async_client):
    mocker.patch("app.core.dao.dao_base.isinstance", return_value=True)
    return CustomPythonWidgetServiceHelper(db_sync_client=mocked_sync_client, db_async_client=mocked_async_client)


@pytest.mark.fixme
@pytest.mark.asyncio
async def test_convert_recipe_to_widget(helper, mocked_async_client, mocked_sync_client):
    dataset_kwargs = {
        "project_id": "project_123",
        "user_id": "user_456",
        "site_id": "site_789",
        "name": "Test Dataset"
    }
    recipe_file = str(
        Path(__file__).parent.parent.parent.parent.parent / "resources/samples/custom_python_widget_recipe_sample.json")
    with open(recipe_file, 'r') as file:
        recipe = CustomPythonWidgetRecipe.model_validate_json(file.read())

    recipe.inputs_map[2].default_value = str(Path(__file__).parent.parent.parent.parent.parent / "resources/output.csv")
    result = helper.convert_recipe_to_widget(recipe, widget_version="1", dataset_kwargs=dataset_kwargs,dry_run=True)

    recipe_file = str(
        Path(__file__).parent.parent.parent.parent.parent / "resources/samples/custom_python_widget.json")
    with open(recipe_file, 'r') as file:
        widget = CustomPythonWidget.model_validate_json(file.read())
    record = mocked_sync_client.Hexaind.datasets.find_one({})
    widget.config.widget_parameters[1].default_value.result.dataset_id = str(record["_id"])
    widget.config.widget_parameters[1].value.result.dataset_id = str(record["_id"])
    assert result.model_dump(exclude=("published_at")) == widget.model_dump(exclude=("published_at"))