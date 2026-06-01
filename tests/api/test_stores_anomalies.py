import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("sqlalchemy")

from retail_intelligence.application.use_cases.get_anomalies import GetStoreAnomaliesUseCase


def test_store_anomalies_endpoint(monkeypatch, client) -> None:
    def fake_execute(self, store_id):
        return {
            "store_id": str(store_id),
            "anomalies": [
                {
                    "type": "QUEUE_SPIKE",
                    "severity": "WARN",
                    "message": "Current queue depth exceeds historical average",
                    "suggested_action": "Open additional billing counters",
                    "detected_at": "2026-05-30T12:00:00Z",
                }
            ],
        }

    monkeypatch.setattr(GetStoreAnomaliesUseCase, "execute", fake_execute)
    response = client.get("/stores/1/anomalies")
    assert response.status_code == 200
    assert response.json()["anomalies"][0]["type"] == "QUEUE_SPIKE"