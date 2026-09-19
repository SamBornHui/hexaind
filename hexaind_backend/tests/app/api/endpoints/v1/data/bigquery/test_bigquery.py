import pytest
from fastapi import status
from httpx import AsyncClient
from app.main import app  # Assuming your FastAPI app is created in app/main.py
from app.services.admin.connectors.schemas import CreateQueryRequest

@pytest.mark.asyncio
@pytest.mark.fixme
async def test_create_query(
    app_client, get_valid_server_admin_token, mongo_client, load_data_to_db
):

    query_params = {"token": get_valid_server_admin_token}
    create_data = {"name":"alpha", "connector_id":"6644939801eba81873b9f59b"}
    response = app_client.post(
        "/v1/sites/site123/projects/proj123/assets/bigquery/query",
        params=query_params,
        json=create_data,
    )


    # success
    assert response.json()["succeeded"] == True
    assert response.json()["message"] == "Deleted Succesfully"

    response_new = app_client.post(
        f"/v1/sites/site123/projects/proj123/assets/bigquery/query",
        params=query_params,
    )

    #failure
    assert response_new.status_code == 404
    assert response_new.json()["detail"] == "Failed with exception 'Query not found'"

@pytest.mark.asyncio
async def test_delete_query(
    app_client, get_valid_server_admin_token, mongo_client, load_data_to_db
):

    query_params = {"token": get_valid_server_admin_token}
    query_id = "66431493cc4766c7487407a7"
    response = app_client.delete(
        f"/v1/sites/site123/projects/proj123/assets/bigquery/query/{query_id}",
        params=query_params,
    )

    # success
    assert response.json()["succeeded"] == True
    assert response.json()["message"] == "Deleted Succesfully"

    response_new = app_client.delete(
        f"/v1/sites/site123/projects/proj123/assets/bigquery/query/{query_id}",
        params=query_params,
    )

    # failure
    assert response_new.status_code == 404
    assert response_new.json()["detail"] == "Failed with exception 'Query not found'"


