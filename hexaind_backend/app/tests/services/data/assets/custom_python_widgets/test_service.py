from pathlib import Path

import pytest
from bson import ObjectId
from mongomock.mongo_client import MongoClient
from mongomock_motor import AsyncMongoMockClient

from app.services.data.assets.custom_python_widget_recipes.schemas import CustomPythonWidgetRecipe
from app.services.data.assets.custom_python_widgets.schemas import CustomPythonWidget
from app.services.data.assets.custom_python_widgets.service import CustomPythonWidgetService


@pytest.fixture
def mocked_async_client():
    return AsyncMongoMockClient()


@pytest.fixture
def mocked_sync_client():
    return MongoClient()


@pytest.fixture
def service(mocker, mocked_async_client, mocked_sync_client):
    mocker.patch("app.core.dao.dao_base.isinstance", return_value=True)
    return CustomPythonWidgetService(db_sync_client=mocked_sync_client, db_async_client=mocked_async_client)


def get_sample_recipe():
    recipe_file = str(
        Path(__file__).parent.parent.parent.parent.parent / "resources/samples/custom_python_widget_recipe_sample.json")
    with open(recipe_file, 'r') as file:
        recipe = CustomPythonWidgetRecipe.model_validate_json(file.read())
    return recipe


def get_sample_widget():
    recipe_file = str(
        Path(__file__).parent.parent.parent.parent.parent / "resources/samples/custom_python_widget.json")
    with open(recipe_file, 'r') as file:
        widget = CustomPythonWidget.model_validate_json(file.read())
    return widget


@pytest.mark.asyncio
async def test_get_next_widget_version(service, mocked_sync_client, mocked_async_client):
    # insert test data
    i1 = get_sample_widget()
    i1.name = "test_sample_widget"
    await mocked_async_client.Hexaind.custom_python_widgets.insert_one(i1.model_dump())
    await mocked_async_client.Hexaind.custom_python_widgets.insert_one(i1.model_dump())
    count = len(await mocked_async_client.Hexaind.custom_python_widgets.find({'name': 'test_sample_widget'}).to_list(
        length=None))

    result = await service.get_next_widget_version("test_sample_widget")
    assert result == str(count + 1)


@pytest.mark.asyncio
@pytest.mark.fixme
async def test_publish_as_widget(service, mocked_sync_client, mocked_async_client):
    custom_python_widget_recipe = get_sample_recipe()
    custom_python_widget_recipe.inputs_map[2].default_value = str(
        Path(__file__).parent.parent.parent.parent.parent / "resources/output.csv")

    expected_widget = get_sample_widget()

    result_id = await service.publish_as_widget(custom_python_widget_recipe, "user_456", "project_123", 'site_789')

    res = mocked_sync_client.Hexaind.custom_python_widgets.find_one({"_id": ObjectId(result_id)})
    res["_id"] = str(res["_id"])
    actual_widget = CustomPythonWidget(**res)
    assert actual_widget.config.widget_parameters[1].default_value.result.dataset_id != \
           expected_widget.config.widget_parameters[1].default_value.result.dataset_id
    assert actual_widget.config.widget_parameters[1].value.result.dataset_id != \
           expected_widget.config.widget_parameters[1].value.result.dataset_id
    actual_widget.config.widget_parameters[1].default_value.result.dataset_id = \
        expected_widget.config.widget_parameters[1].default_value.result.dataset_id
    actual_widget.config.widget_parameters[1].value.result.dataset_id = expected_widget.config.widget_parameters[
        1].value.result.dataset_id

    assert actual_widget.model_dump(exclude=("published_at", "id")) == expected_widget.model_dump(
        exclude=("published_at", "id"))


@pytest.mark.asyncio
async def test_get_all_modules_async(mocker, service, mocked_sync_client, mocked_async_client):
    i1 = get_sample_widget()
    i1.project_ids = ["project_123", "project_231"]
    await mocked_async_client.Hexaind.custom_python_widgets.insert_one(i1.model_dump())
    await mocked_async_client.Hexaind.custom_python_widgets.insert_one(i1.model_dump())
    i1.project_ids = ["project_231"]
    await mocked_async_client.Hexaind.custom_python_widgets.insert_one(i1.model_dump())

    project_id = "project_123"
    search_term = ""
    page_number = 1
    page_limit = 10

    result = await service.get_all_widgets_async(project_id, search_term, page_number, page_limit)

    assert len(result[0]) == 2
    assert result[1] == 2


#
@pytest.mark.asyncio
async def test_get_widget_by_id(mocker, service, mocked_sync_client, mocked_async_client):
    i1 = get_sample_widget()
    widget_id = await mocked_async_client.Hexaind.custom_python_widgets.insert_one(i1.model_dump())

    result = await service.get_widget_by_id(widget_id.inserted_id)

    expected_widget = get_sample_widget()
    assert result.model_dump(exclude=("published_at", "id")) == expected_widget.model_dump(
        exclude=("published_at", "id"))
