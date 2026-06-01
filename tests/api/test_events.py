import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("sqlalchemy")
pytest.importorskip("redis")

from retail_intelligence.application.use_cases.ingest_event import IngestEventUseCase


def test_events_ingest_endpoint(monkeypatch, client) -> None:
    def fake_execute(self, payload):
        return {"received": len(payload), "saved": len(payload)}

    monkeypatch.setattr(IngestEventUseCase, "execute", fake_execute)
    response = client.post(
        "/events/ingest",
        json=[
            {
                "event_id": "evt-1",
                "store_id": 1,
                "camera_id": 10,
                "visitor_id": "v-1",
                "event_type": "person_entered",
                "timestamp": "2026-05-30T12:00:00Z",
                "zone_id": "entrance",
                "dwell_ms": 1200,
                "is_staff": False,
                "confidence": 0.98,
                "metadata": {"source": "camera-1"},
            }
        ],
    )
    assert response.status_code == 201
