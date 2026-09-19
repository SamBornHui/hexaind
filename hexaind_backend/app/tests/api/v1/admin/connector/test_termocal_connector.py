from fastapi.testclient import TestClient
from app.main import app
import pytest
client = TestClient(app)


def test_thermocalc_authenticate_success():
    # Mocking thermocalc_obj
    thermocalc_obj = {"method": "server_ip", "path": "/apps/Thermo-Calc/Thermo-Calc/2023b/", "host": "KSWNNAWPLICAP01.novelis.biz"}
    site_id = "1"
    project_id = "1"

    response = client.post(f"/v1/sites/{site_id}/projects/{project_id}/thermocalc_authentication/", json=thermocalc_obj)

    assert response.status_code == 200
    assert response.json() == {"message": "Authentication Successful"}

@pytest.mark.fixme
def test_thermocalc_authenticate_failed():
    # Mocking thermocalc_obj
    thermocalc_obj = {"method": "server_ip", "path": "/apps/somthing_else/Thermo-Calc/2023b/", "host": "wrong_data"}
    site_id = "1"
    project_id = "1"

    response = client.post(f"/v1/sites/{site_id}/projects/{project_id}/thermocalc_authentication/", json=thermocalc_obj)

    assert response.status_code == 401
    assert response.json() == {"message": "Authentication Failed"}
