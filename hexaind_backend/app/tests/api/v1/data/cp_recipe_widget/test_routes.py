from app.services.data.assets.custom_python_widget_recipes.schemas import CustomPythonWidgetRecipeUpdateRequest
from app.api.endpoints.v1.data.cp_recipe_widget.routes import CustomPythonRouter

import pytest
from mongomock_motor import AsyncMongoMockClient
from mongomock import MongoClient

from app.services.data.assets.datasets.schemas import AccessMode


@pytest.fixture
def mocked_async_client():
    return AsyncMongoMockClient()


@pytest.fixture
def mocked_sync_client():
    return MongoClient()


def mock_depends(x):
    if "db_sync" in str(x):
        return MongoClient()
    if "db_async" in str(x):
        return AsyncMongoMockClient()


def get_sample_recipe():
    return {
        "version": "1.0",
        "name": "join_recipe",
        "reference_links": [],
        "tags": [],
        "widget_inputs_rules": {
            "count": 2,
            "config": [
                {
                    "count": 1,
                    "expected_type": "DATASET",
                    "expected_type_constraints": {"sub_type": "TABULAR"}
                },
                {
                    "count": 1,
                    "expected_type": "DATASET",
                    "expected_type_constraints": {"sub_type": "TABULAR"}
                }
            ]
        },
        "widget_outputs_rules": {
            "count": 1,
            "config": [
                {
                    "count": 1,
                    "expected_type": "DATASET",
                    "expected_type_constraints": {"sub_type": "TABULAR"}
                }
            ]
        },
        "module_id": "65d852d4f97c867ed1c08986",
        "inputs_map": [
            {
                "arg_name": "df1",
                "type": "<class 'pandas.core.frame.DataFrame'>",
                "is_mandatory": True,
                "source": "INPUT_SELECTED_FROM_PRIOR_WIDGET"
            },
            {
                "arg_name": "df2",
                "type": "<class 'pandas.core.frame.DataFrame'>",
                "is_mandatory": True,
                "source": "INPUT_SELECTED_FROM_PRIOR_WIDGET"
            },
            {
                "arg_name": "column_names",
                "type": "<class 'str'>",
                "is_mandatory": True,
                "source": "INPUT_ENTERED_MANUALLY_ON_WIDGET"
            },
            {
                "arg_name": "how",
                "type": "<class 'str'>",
                "default_value": "inner",
                "is_mandatory": True,
                "source": "INPUT_ENTERED_MANUALLY_ON_WIDGET"
            }
        ],
        "outputs_map": [
            {
                "type": "<class 'pandas.core.frame.DataFrame'>",
                "mapped_output": {
                    "reference_name": "output1",
                    "type": "DATASET",
                    "sub_type": "TABULAR"
                }
            }
        ],
        "settings":
            {
                "color_code": "#121312",
                "allow_users_to_modify_configurations": True
            }
        ,
        "project_id": "1",
        "site_id": "1",
        "access_mode": "INTERNAL",
        "created_by": "ramkishan"
    }


@pytest.mark.asyncio
async def test_save_custom_python_widget_recipe_success(mocker, mocked_sync_client, mocked_async_client):
    request_body = get_sample_recipe()
    mocker.patch("app.core.dao.dao_base.isinstance", return_value=True)
    mocker.patch("app.api.endpoints.v1.data.cp_recipe_widget.routes.Depends", side_effect=mock_depends)

    mocker.patch(
        'app.services.data.assets.custom_python_widget_recipes.service.CustomPythonWidgetRecipeService.insert_or_update',
        return_value="result")
    mock_jwt_token = mocker.patch('app.api.endpoints.v1.data.cp_recipe_widget.routes.decodeJWT')
    mock_jwt_token.return_value = {"email": "admin@office.com", "user_id": "new_user_id"}

    router = CustomPythonRouter()
    response = await router.save_custom_python_widget_recipe("", "", request_body, mocked_sync_client,
                                                             mocked_async_client)
    print(response)

    # Assertions
    assert response.succeeded is True
    assert response.custom_python_widget_recipe_id == 'result'
    assert response.message == "Successfully saved custom python recipe"


@pytest.mark.fixme
@pytest.mark.asyncio
async def test_save_custom_python_widget_recipe_failure_invalid_request(mocker):
    # Mock parameters
    site_id = 'site_id'
    project_id = 'project_id'
    request_body = CustomPythonWidgetRecipeUpdateRequest(
        name="Test Recipe",
        project_id=project_id,
        site_id=site_id,
        access_mode=AccessMode.INTERNAL
    )


    mocker.patch('app.api.endpoints.v1.data.cp_recipe_widget.routes.CustomPythonWidgetRecipeService.insert_or_update',
                 side_effect=Exception("want this exception"))

    # Call the function
    response = await CustomPythonRouter.save_custom_python_widget_recipe(
        siteId=site_id,
        projectId=project_id,
        custom_python_widget_recipe_update_request=request_body,
        async_client=AsyncMongoMockClient()
    )

    # Assertions
    assert response.succeeded is False
    assert response.custom_python_widget_recipe_id is None


# ToDo: add tests for other routes