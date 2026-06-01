from abc import ABC, abstractmethod
from collections.abc import Sequence

from retail_intelligence.domain.entities.event import Event


class StoreAnalyticsRepository(ABC):
    @abstractmethod
    def list_store_events(self, store_id: int) -> Sequence[Event]:
        raise NotImplementedError