from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import datetime

from retail_intelligence.domain.entities.anomaly import ZoneLastActivity
from retail_intelligence.domain.entities.event import Event


class AnomalyRepository(ABC):
    @abstractmethod
    def list_events_since(self, store_id: int, since: datetime) -> Sequence[Event]:
        raise NotImplementedError

    @abstractmethod
    def list_zone_last_activity(self, store_id: int) -> Sequence[ZoneLastActivity]:
        raise NotImplementedError