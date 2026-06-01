from retail_intelligence.infrastructure.vision.event_generator import EventGenerator


def test_event_generator_returns_payload() -> None:
    generator = EventGenerator()
    event = generator.generate(1, "person_entered", {"track_id": "t1"})
    assert event["store_id"] == 1
