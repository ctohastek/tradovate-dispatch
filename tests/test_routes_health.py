import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_health_check():
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_includes_version():
    client = TestClient(app)
    response = client.get("/health")

    data = response.json()
    assert "version" in data
    assert "timestamp" in data
