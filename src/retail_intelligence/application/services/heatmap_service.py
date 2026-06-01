from collections import defaultdict

from retail_intelligence.domain.repositories.store_analytics_repository import StoreAnalyticsRepository
from retail_intelligence.infrastructure.db.repositories.store_analytics_repository_impl import StoreAnalyticsRepositoryImpl
from retail_intelligence.schemas.analytics import HeatmapResponse, HeatmapZone


class HeatmapService:
    def __init__(self, repository: StoreAnalyticsRepository) -> None:
        self._repository = repository

    @classmethod
    def from_session(cls, db) -> "HeatmapService":
        return cls(StoreAnalyticsRepositoryImpl(db))

    def get_heatmap(self, store_id: int) -> HeatmapResponse:
        events = list(self._repository.list_store_events(store_id))
        zone_visitors: dict[str, set[str]] = defaultdict(set)
        zone_dwell: dict[str, list[int]] = defaultdict(list)
        all_visitors: set[str] = set()

        for event in events:
            if not event.visitor_id or not event.zone_id:
                continue
            all_visitors.add(event.visitor_id)
            zone_visitors[event.zone_id].add(event.visitor_id)
            if event.dwell_ms is not None:
                zone_dwell[event.zone_id].append(event.dwell_ms)

        max_visits = max((len(visitors) for visitors in zone_visitors.values()), default=0)
        zones = [
            HeatmapZone(
                zone_id=zone_id,
                visits=len(visitors),
                avg_dwell=self._average_dwell(zone_dwell.get(zone_id, [])),
                normalized_score=self._normalized_score(len(visitors), max_visits),
            )
            for zone_id, visitors in zone_visitors.items()
        ]
        zones.sort(key=lambda zone: (-zone.visits, zone.zone_id))

        return HeatmapResponse(
            store_id=store_id,
            zones=zones,
            data_confidence="HIGH" if len(all_visitors) >= 20 else "LOW",
        )

    def _average_dwell(self, dwell_values: list[int]) -> float:
        if not dwell_values:
            return 0.0
        return round(sum(dwell_values) / len(dwell_values) / 1000.0, 2)

    def _normalized_score(self, visits: int, max_visits: int) -> int:
        if max_visits == 0:
            return 0
        return int(round((visits / max_visits) * 100))
