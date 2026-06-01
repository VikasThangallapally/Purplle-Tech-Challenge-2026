from retail_intelligence.shared.enums import EventType


def is_funnel_progression(event_type: str) -> bool:
    return event_type in {
        EventType.PERSON_ENTERED,
        EventType.QUEUE_JOINED,
        EventType.DWELL_STARTED,
    }
