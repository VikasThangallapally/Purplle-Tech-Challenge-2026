import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("sqlalchemy")
pytest.importorskip("redis")

from retail_intelligence.application.use_cases.get_store_metrics import GetStoreMetricsUseCase


def test_store_metrics_endpoint(monkeypatch, client) -> None:
    def fake_execute(self, store_id):
        return {"store_id": store_id, "unique_visitors": 0, "conversion_rate": 0.0, "avg_dwell_time": 0.0, "queue_depth": 0, "abandonment_rate": 0.0}

    monkeypatch.setattr(GetStoreMetricsUseCase, "execute", fake_execute)
    response = client.get("/stores/1/metrics")
    assert response.status_code == 200
