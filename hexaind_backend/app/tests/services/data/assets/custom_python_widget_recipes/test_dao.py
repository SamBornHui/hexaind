import datetime
import pytest
import pytest_mock
from app.services.data.assets.custom_python_widget_recipes.dao import CustomPythonWidgetRecipeDao
from app.services.data.assets.custom_python_widget_recipes.schemas import CustomPythonWidgetRecipe
from mongomock_motor import AsyncMongoMockClient
from mongomock import MongoClient


@pytest.fixture
def mocked_async_client():
    return AsyncMongoMockClient()


@pytest.fixture
def mocked_sync_client():
    return MongoClient()


def get_sample_custom_python_widget_recipe_dump():
    return {
    # "_id": ObjectId('65d8678b270f9bbe714d6e9f'),
    "version": '1.0',
    "name": 'join_recipe',
    "recipe_name": 'abc',
    "description": 'abc',
    "reference_links": [],
    "tags": [],
    "widget_inputs_rules": {
        "count": 2,
        "config": [
            {
                "count": 1,
                "expected_type": 'DATASET',
                "expected_type_constraints": {
                    "sub_type": 'TABULAR',
                    "constraints": None
                },
                "optional": False
            },
            {
                "count": 1,
                "expected_type": 'DATASET',
                "expected_type_constraints": {
                    "sub_type": 'TABULAR',
                    "constraints": None
                },
                "optional": False
            }
        ]
    },
    "widget_outputs_rules": {
        "count": 1,
        "config": [
            {
                "count": 1,
                "expected_type": 'DATASET',
                "expected_type_constraints": {
                    "sub_type": 'TABULAR',
                    "constraints": None
                },
                "optional": False
            }
        ]
    },
    "module_id": '65d852d4f97c867ed1c08986',
    "inputs_map": [
        {
            "arg_name": 'df1',
            "type": "<class \'pandas.core.frame.DataFrame\'>",
            "default_value": '',
            "is_mandatory": True,
            "source": 'INPUT_SELECTED_FROM_PRIOR_WIDGET',
            "mapped_input": None
        },
        {
            "arg_name": 'df2',
            "type": "<class \'pandas.core.frame.DataFrame\'>",
            "default_value": '',
            "is_mandatory": True,
            "source": 'INPUT_SELECTED_FROM_PRIOR_WIDGET',
            "mapped_input": None
        },
        {
            "arg_name": 'column_names',
            "type": "<class \'str\'>",
            "default_value": '',
            "is_mandatory": True,
            "source": 'INPUT_ENTERED_MANUALLY_ON_WIDGET',
            "mapped_input": None
        },
        {
            "arg_name": 'how',
            "type": "<class \'str\'>",
            "default_value": 'inner',
            "is_mandatory": True,
            "source": 'INPUT_ENTERED_MANUALLY_ON_WIDGET',
            "mapped_input": None
        }
    ],
    "outputs_map": [
        {
            "type": "<class \'pandas.core.frame.DataFrame\'>",
            "mapped_output": {
                "reference_name": 'output1',
                "type": 'DATASET',
                "sub_type": 'TABULAR'
            }
        }
    ],
    "settings": 
        {
            "color_code": '#121312',
            "allow_users_to_modify_configurations": True
        },
    "project_id": '1',
    "site_id": '1',
    "access_mode": 'INTERNAL',
    'created_by': '',
    "created_at": '2024-02-23T15:08:19.613Z',
    "last_modified_by": '',
    "last_modified_at": '2024-02-23T15:08:19.613Z'
}


@pytest.mark.asyncio
async def test_insert_custom_python_widget_recipe(mocker, mocked_async_client, mocked_sync_client):
    mocker.patch("app.core.dao.dao_base.isinstance", return_value=True)
   
    custom_python_widget_recipe_dict = get_sample_custom_python_widget_recipe_dump()
    custom_python_widget_recipe_dao = CustomPythonWidgetRecipeDao(
        db_sync_client=mocked_sync_client, db_async_client=mocked_async_client
    )
    inserted_id = custom_python_widget_recipe_dao.insert_custom_python_widget_recipe(
        CustomPythonWidgetRecipe(**custom_python_widget_recipe_dict)
    )
    assert isinstance(inserted_id, str)


@pytest.mark.asyncio
async def test_update_custom_python_widget_recipe(mocker, mocked_async_client, mocked_sync_client):
    mocker.patch("app.core.dao.dao_base.isinstance", return_value=True)
    custom_python_widget_recipe_dict = get_sample_custom_python_widget_recipe_dump()
    custom_python_widget_recipe_dict['_id'] = '1'  # Adding a mock ID
    custom_python_widget_recipe_dao = CustomPythonWidgetRecipeDao(
        db_sync_client=mocked_sync_client, db_async_client=mocked_async_client
    )
    with pytest.raises(Exception) as exc_info:
        await custom_python_widget_recipe_dao.update_custom_python_widget_recipe(
            CustomPythonWidgetRecipe(**custom_python_widget_recipe_dict)
        )
    # assert "No custom python widget recipe is found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_all_custom_python_widget_recipes_async(mocker, mocked_async_client, mocked_sync_client):
    mocker.patch("app.core.dao.dao_base.isinstance", return_value=True)
    custom_python_widget_recipe_dao = CustomPythonWidgetRecipeDao(
        db_sync_client=mocked_sync_client, db_async_client=mocked_async_client
    )
    recipes, total_count = await custom_python_widget_recipe_dao.get_all_custom_python_widget_recipes_async(
        project_id='1', search_term='', page_number=1, page_limit=10
    )
    assert isinstance(recipes, list)
    assert isinstance(total_count, int)


@pytest.mark.asyncio
async def test_get_custom_python_widget_recipe_by_id_async(mocker, mocked_async_client, mocked_sync_client):
    mocker.patch("app.core.dao.dao_base.isinstance", return_value=True)
    custom_python_widget_recipe_dao = CustomPythonWidgetRecipeDao(
        db_sync_client=mocked_sync_client, db_async_client=mocked_async_client
    )
    # Insert a mock recipe into the database
    custom_python_widget_recipe_dict = get_sample_custom_python_widget_recipe_dump()
    res = await mocked_async_client.Hexaind.custom_python_widget_recipes.insert_one(custom_python_widget_recipe_dict)
    # Fetch the inserted recipe by its ID
    print(res.inserted_id , "inserted id")
    fetched_recipe = await custom_python_widget_recipe_dao.get_custom_python_widget_recipe_by_id_async(str(res.inserted_id))
    assert fetched_recipe is not None
    assert fetched_recipe.name == custom_python_widget_recipe_dict['name']
