import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("sqlalchemy")
pytest.importorskip("redis")

from fastapi.testclient import TestClient

from retail_intelligence.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)
