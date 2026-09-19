import datetime

import pytest
import pytest_mock
from bson import ObjectId

from mongomock_motor import AsyncMongoMockClient
from mongomock import MongoClient
from app.services.data.assets.custom_python_widgets.dao import CustomPythonWidgetsDao
from app.services.data.assets.custom_python_widgets.schemas import CustomPythonWidget
from app.services.data.assets.modules.schemas import AccessMode
from app.services.workflows.designer.base_schemas import WidgetType
from app.services.workflows.designer.schemas import CustomCodeActivityConfig


def get_sample_data(recipe_id="test"):
    return CustomPythonWidget(
        name="Test Widget",
        widget_version="1.0",
        recipe_id=recipe_id,
        description="Test Description",
        reference_links=[],
        config=CustomCodeActivityConfig(
            module_id="test_modul_id",
            widget_type=WidgetType.CUSTOM_CODE,
            function_inputs=[],
            function_outputs=[]
        ),
        tags=[],
        site_ids=[],
        project_ids=["project_id_1", "project_id_2"],
        published_at=datetime.datetime.now(datetime.timezone.utc),
        published_by="Test Owner",
        access_mode=AccessMode.INTERNAL,
        usage_count=0
    )



@pytest.mark.asyncio
async def test_insert_custom_python_widget(mocker, mocked_db_async_client, mocked_db_sync_client):
    mocker.patch("app.core.dao.dao_base.isinstance", return_value=True)
    dao = CustomPythonWidgetsDao(db_sync_client=mocked_db_sync_client, db_async_client=mocked_db_async_client)
    widget_data = get_sample_data()

    # Act
    widget_id = dao.insert_custom_python_widget(widget_data)

    # Assert
    assert widget_id is not None
    assert isinstance(widget_id, str)


@pytest.mark.asyncio
async def test_count_widgets(mocked_db_async_client, mocked_db_sync_client):
    # Arrange
    dao = CustomPythonWidgetsDao(db_sync_client=mocked_db_sync_client, db_async_client=mocked_db_async_client)

    widget_name = "Test Widget"

    # Act 113664118
    count = await dao.count_widgets(widget_name)

    # Assert
    assert count == 0  # Assuming no widgets with this name initially


@pytest.mark.asyncio
async def test_get_all_custom_python_widgets_async(mocked_db_async_client, mocked_db_sync_client):
    await mocked_db_async_client.Hexaind.custom_python_widgets.insert_one(get_sample_data().model_dump())
    await mocked_db_async_client.Hexaind.custom_python_widgets.insert_one(get_sample_data().model_dump())
    sample_data = get_sample_data()
    sample_data.project_ids = ["test"]
    await mocked_db_async_client.Hexaind.custom_python_widgets.insert_one(sample_data.model_dump())
    dao = CustomPythonWidgetsDao(db_sync_client=mocked_db_sync_client, db_async_client=mocked_db_async_client)
    project_id = "project_id_1"
    search_term = ""
    page_number = 1
    page_limit = 10
    widgets, total_count = await dao.get_all_custom_python_widgets_async(project_id, search_term, page_number,
                                                                         page_limit)

    assert isinstance(widgets, list)
    assert isinstance(total_count, int)
    assert len(widgets) == 2


@pytest.mark.asyncio
async def test_get_widget_by_id(mocked_db_async_client, mocked_db_sync_client):
    res = await mocked_db_async_client.Hexaind.custom_python_widgets.insert_one(get_sample_data().model_dump())
    dao = CustomPythonWidgetsDao(db_sync_client=mocked_db_sync_client, db_async_client=mocked_db_async_client)
    fetched_widget = await dao.get_widget_by_id(res.inserted_id)

    # Assert
    assert fetched_widget is not None
    assert fetched_widget.name == "Test Widget"
    assert fetched_widget.widget_version == "1.0"
    assert fetched_widget.published_by == "Test Owner"
    assert fetched_widget.description == "Test Description"
    assert fetched_widget.project_ids == ["project_id_1", "project_id_2"]
    assert fetched_widget.published_at is not None


@pytest.mark.asyncio
async def test_get_widget_by_id_not_found(mocked_db_async_client, mocked_db_sync_client):
    dao = CustomPythonWidgetsDao(db_sync_client=mocked_db_sync_client, db_async_client=mocked_db_async_client)
    with pytest.raises(Exception) as exc_info:
        await dao.get_widget_by_id(str(ObjectId()))
    assert "unable to fetch the custom python widget recipe at this moment" in str(exc_info.value)
