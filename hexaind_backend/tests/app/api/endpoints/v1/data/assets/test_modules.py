import pytest
import pytest_mock
import pytest_asyncio


@pytest.mark.asyncio
async def test_get_module_happy_case(
    app_client, get_valid_server_admin_token, mongo_client, load_data_to_db
):

    query_params = {"token": get_valid_server_admin_token}
    inserted_id = "663096598d7aacb7039f6a27"
    response = app_client.get(
        f"/v1/sites/site123/projects/proj123/assets/modules/{inserted_id}",
        params=query_params,
    )
    assert response.status_code == 200
    assert response.json()["_id"] == inserted_id


@pytest.mark.asyncio
async def test_get_module_unhappy_case(
    app_client, get_valid_server_admin_token, mongo_client, load_data_to_db
):

    query_params = {"token": get_valid_server_admin_token}
    inserted_id = "663096598d7aacb7039f6a20"
    response = app_client.get(
        f"/v1/sites/site123/projects/proj123/assets/modules/{inserted_id}",
        params=query_params,
    )
    assert response.status_code == 400
