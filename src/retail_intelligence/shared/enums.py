from enum import StrEnum


class EventType(StrEnum):
    PERSON_ENTERED = "person_entered"
    PERSON_EXITED = "person_exited"
    QUEUE_JOINED = "queue_joined"
    QUEUE_LEFT = "queue_left"
    DWELL_STARTED = "dwell_started"
    DWELL_ENDED = "dwell_ended"
    ANOMALY = "anomaly"


class ZoneType(StrEnum):
    ENTRANCE = "entrance"
    AISLE = "aisle"
    CHECKOUT = "checkout"
    QUEUE = "queue"
    EXIT = "exit"
