import pytest

pytest.importorskip("sqlalchemy")

from datetime import datetime, timezone

from retail_intelligence.domain.entities.event import Event
from retail_intelligence.domain.value_objects.bounding_box import BoundingBox


def test_bounding_box_dimensions() -> None:
    box = BoundingBox(x1=10, y1=15, x2=40, y2=55)
    assert box.width == 30
    assert box.height == 40


def test_event_entity_defaults() -> None:
    event = Event(
        event_id="evt-1",
        store_id=1,
        camera_id=None,
        visitor_id=None,
        event_type="person_entered",
        timestamp=datetime.now(timezone.utc),
        zone_id=None,
        dwell_ms=None,
        is_staff=False,
        confidence=None,
    )
    assert event.metadata == {}
