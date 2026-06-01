import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("sqlalchemy")

from retail_intelligence.application.use_cases.get_funnel import GetStoreFunnelUseCase


def test_store_funnel_endpoint(monkeypatch, client) -> None:
    def fake_execute(self, store_id):
        return {
            "store_id": store_id,
            "entry": 100,
            "zone_visit": 80,
            "billing_queue": 50,
            "purchase": 35,
            "dropoff_percentages": {
                "entry_to_zone": 20.0,
                "zone_to_queue": 37.5,
                "queue_to_purchase": 30.0,
            },
        }

    monkeypatch.setattr(GetStoreFunnelUseCase, "execute", fake_execute)
    response = client.get("/stores/1/funnel")
    assert response.status_code == 200
    assert response.json()["purchase"] == 35