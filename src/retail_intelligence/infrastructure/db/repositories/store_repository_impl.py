from sqlalchemy.orm import Session

from retail_intelligence.domain.entities.store import Store
from retail_intelligence.infrastructure.db.models.store import StoreModel


class StoreRepositoryImpl:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, store_id: int) -> Store | None:
        model = self._db.get(StoreModel, store_id)
        if model is None:
            return None
        return Store(id=model.id, name=model.name, location=model.location)
