from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_token_endpoint_returns_token():
    response = client.post("/token", json={"username": "analyst", "password": "change-me"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_token_endpoint_rejects_bad_password():
    response = client.post("/token", json={"username": "analyst", "password": "wrong"})
    assert response.status_code == 401


def test_alerts_correlate_extracts_cve():
    response = client.post(
        "/alerts/correlate",
        json={"event_text": "RDP brute force toward host - CVE-2019-0708"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "CVE-2019-0708" in data["explicit_ids"]
    assert data["correlated"]


def test_siem_client_sample_events():
    from siem.client import sample_events

    events = sample_events()
    assert len(events) > 0
    assert "message" in events[0]