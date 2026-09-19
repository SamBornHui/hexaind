import datetime
import pytest
from app.services.data.assets.custom_python_widget_recipes.service import (
    CustomPythonWidgetRecipeService,
)
from app.services.data.assets.custom_python_widget_recipes.schemas import (
    CustomPythonWidgetRecipeUpdateRequest,
    CustomPythonWidgetRecipe,
)


@pytest.fixture
def service(mocked_db_sync_client, mocked_db_async_client):
    return CustomPythonWidgetRecipeService(
        db_sync_client=mocked_db_sync_client, db_async_client=mocked_db_async_client
    )


def get_sample_custom_python_widget_recipe_dump():
    return {
        "_id": "65d8678b270f9bbe714d6e9f",
        "id": "65d8678b270f9bbe714d6e9f",
        "version": "1.0",
        "name": "join_recipe",
        "recipe_name": "abc",
        "description": "abc",
        "reference_links": [],
        "tags": [],
        "widget_inputs_rules": {
            "count": 2,
            "config": [
                {
                    "count": 1,
                    "expected_type": "DATASET",
                    "expected_type_constraints": {
                        "sub_type": "TABULAR",
                        "constraints": None,
                    },
                    "optional": False,
                },
                {
                    "count": 1,
                    "expected_type": "DATASET",
                    "expected_type_constraints": {
                        "sub_type": "TABULAR",
                        "constraints": None,
                    },
                    "optional": False,
                },
            ],
        },
        "widget_outputs_rules": {
            "count": 1,
            "config": [
                {
                    "count": 1,
                    "expected_type": "DATASET",
                    "expected_type_constraints": {
                        "sub_type": "TABULAR",
                        "constraints": None,
                    },
                    "optional": False,
                }
            ],
        },
        "module_id": "65d852d4f97c867ed1c08986",
        "inputs_map": [
            {
                "arg_name": "df1",
                "type": "<class 'pandas.core.frame.DataFrame'>",
                "default_value": "",
                "is_mandatory": True,
                "source": "INPUT_SELECTED_FROM_PRIOR_WIDGET",
                "mapped_input": None,
            },
            {
                "arg_name": "df2",
                "type": "<class 'pandas.core.frame.DataFrame'>",
                "default_value": "",
                "is_mandatory": True,
                "source": "INPUT_SELECTED_FROM_PRIOR_WIDGET",
                "mapped_input": None,
            },
            {
                "arg_name": "column_names",
                "type": "<class 'str'>",
                "default_value": "",
                "is_mandatory": True,
                "source": "INPUT_ENTERED_MANUALLY_ON_WIDGET",
                "mapped_input": None,
            },
            {
                "arg_name": "how",
                "type": "<class 'str'>",
                "default_value": "inner",
                "is_mandatory": True,
                "source": "INPUT_ENTERED_MANUALLY_ON_WIDGET",
                "mapped_input": None,
            },
        ],
        "outputs_map": [
            {
                "type": "<class 'pandas.core.frame.DataFrame'>",
                "mapped_output": {
                    "reference_name": "output1",
                    "type": "DATASET",
                    "sub_type": "TABULAR",
                },
            }
        ],
        "settings": {
            "color_code": "#121312",
            "allow_users_to_modify_configurations": True,
        },
        "project_id": "1",
        "site_id": "1",
        "user_id": "1",
        "access_mode": "INTERNAL",
        "created_by": "",
        "created_at": "2024-02-23T15:08:19.613Z",
        "last_modified_by": "",
        "last_modified_at": "2024-02-23T15:08:19.613Z",
    }


@pytest.mark.asyncio
async def test_insert_or_update_insert(mocker, service, mocked_db_async_client):

    # Mock insert_custom_python_widget_recipe method
    mocked_insert_method = mocker.patch.object(
        service.custom_python_widget_recipe_dao, "insert_custom_python_widget_recipe"
    )
    mocked_insert_method.return_value = "new_recipe_id"

    # Mock request data
    request = get_sample_custom_python_widget_recipe_dump()
    request["id"] = request["_id"] = ""

    # Call insert_or_update method
    res = await mocked_db_async_client.Hexaind.custom_python_widget_recipes.insert_one(
        get_sample_custom_python_widget_recipe_dump()
    )
    inserted_recipe_id = await service.insert_or_update(
        CustomPythonWidgetRecipeUpdateRequest.model_validate(request), "1", "1", "1"
    )

    # Assertions
    assert inserted_recipe_id == "new_recipe_id"


@pytest.mark.asyncio
async def test_insert_or_update_update(mocker, service):

    # Mock update_custom_python_widget_recipe method
    mocked_update_method = mocker.patch.object(
        service.custom_python_widget_recipe_dao, "update_custom_python_widget_recipe"
    )
    mocked_update_method.return_value = "updated_recipe_id"

    # Mock request data
    request = get_sample_custom_python_widget_recipe_dump()

    # Call insert_or_update method
    updated_recipe_id = await service.insert_or_update(
        CustomPythonWidgetRecipeUpdateRequest.model_validate(request), "1", "1", "1"
    )

    # Assertions
    assert updated_recipe_id == "updated_recipe_id"


@pytest.mark.asyncio
async def test_fetch_recipes(mocker, service):
    # Mock get_all_custom_python_widget_recipes_async method
    mocked_fetch_method = mocker.patch.object(
        service.custom_python_widget_recipe_dao,
        "get_all_custom_python_widget_recipes_async",
    )
    mocked_fetch_method.return_value = (
        [CustomPythonWidgetRecipe(**get_sample_custom_python_widget_recipe_dump())],
        1,
    )

    # Call fetch_recipes method
    recipes, total_count = await service.fetch_recipes(
        "project_id", "name_prefix", 100, 1
    )

    # Assertions
    assert len(recipes) == 1
    assert total_count == 1
    mocked_fetch_method.assert_called_once_with(
        project_id="project_id",
        search_term="name_prefix",
        page_number=1,
        page_limit=100,
        access_mode=None,
    )


@pytest.mark.asyncio
async def test_get_recipe(mocker, service):
    # Mock get_custom_python_widget_recipe_by_id_async method
    mocked_get_method = mocker.patch.object(
        service.custom_python_widget_recipe_dao,
        "get_custom_python_widget_recipe_by_id_async",
    )
    mocked_get_method.return_value = CustomPythonWidgetRecipe(
        **get_sample_custom_python_widget_recipe_dump()
    )

    # Call get_recipe method
    recipe = await service.get_recipe("1")

    # Assertions
    assert recipe.id == "65d8678b270f9bbe714d6e9f"
    assert recipe.name == "join_recipe"
    mocked_get_method.assert_called_once_with("1")
