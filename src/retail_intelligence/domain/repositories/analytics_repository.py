from abc import ABC, abstractmethod
from collections.abc import Sequence

from retail_intelligence.domain.entities.analytics_snapshot import AnalyticsSnapshot


class AnalyticsRepository(ABC):
    @abstractmethod
    def upsert_snapshot(self, snapshot: AnalyticsSnapshot) -> AnalyticsSnapshot:
        raise NotImplementedError

    @abstractmethod
    def list_snapshots(self, store_id: int) -> Sequence[AnalyticsSnapshot]:
        raise NotImplementedError
