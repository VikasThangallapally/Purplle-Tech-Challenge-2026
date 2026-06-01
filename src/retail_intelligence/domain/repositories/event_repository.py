from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import datetime

from retail_intelligence.domain.entities.event import Event


class EventRepository(ABC):
    @abstractmethod
    def create_event(self, event: Event) -> Event:
        raise NotImplementedError

    @abstractmethod
    def create_events_batch(self, events: Sequence[Event]) -> Sequence[Event]:
        raise NotImplementedError

    @abstractmethod
    def get_event_by_id(self, event_id: str) -> Event | None:
        raise NotImplementedError

    @abstractmethod
    def get_latest_event_timestamp(self) -> datetime | None:
        raise NotImplementedError
