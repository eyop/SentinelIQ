from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_alerts_endpoint_returns_payload():
    response = client.get('/alerts')
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_cve_endpoint_returns_payload():
    response = client.get('/cves')
    assert response.status_code == 200
    assert isinstance(response.json(), list)
