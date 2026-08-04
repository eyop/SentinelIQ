from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_query_endpoint_returns_reply():
    response = client.post(
        "/query",
        json={"question": "What CVE should I look at for a buffer overflow?", "k": 2},
    )
    assert response.status_code == 200
    assert "answer" in response.json()
