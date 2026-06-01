import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("sqlalchemy")

from retail_intelligence.application.use_cases.get_heatmap import GetStoreHeatmapUseCase


def test_store_heatmap_endpoint(monkeypatch, client) -> None:
    def fake_execute(self, store_id):
        return {
            "store_id": store_id,
            "zones": [
                {
                    "zone_id": "SKINCARE",
                    "visits": 100,
                    "avg_dwell": 45.0,
                    "normalized_score": 90,
                }
            ],
            "data_confidence": "HIGH",
        }

    monkeypatch.setattr(GetStoreHeatmapUseCase, "execute", fake_execute)
    response = client.get("/stores/1/heatmap")
    assert response.status_code == 200
    assert response.json()["data_confidence"] == "HIGH"