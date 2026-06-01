from collections.abc import Sequence

from sqlalchemy.orm import Session

from retail_intelligence.domain.entities.analytics_snapshot import AnalyticsSnapshot
from retail_intelligence.infrastructure.db.models.analytics_snapshot import AnalyticsSnapshotModel


class AnalyticsRepositoryImpl:
    def __init__(self, db: Session) -> None:
        self._db = db

    def upsert_snapshot(self, snapshot: AnalyticsSnapshot) -> AnalyticsSnapshot:
        model = AnalyticsSnapshotModel(
            store_id=snapshot.store_id,
            generated_at=snapshot.generated_at,
            metrics=snapshot.metrics,
        )
        self._db.add(model)
        self._db.commit()
        self._db.refresh(model)
        return snapshot

    def list_snapshots(self, store_id: int) -> Sequence[AnalyticsSnapshot]:
        return []
