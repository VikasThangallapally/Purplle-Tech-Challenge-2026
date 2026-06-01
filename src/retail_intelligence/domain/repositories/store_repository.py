from abc import ABC, abstractmethod

from retail_intelligence.domain.entities.store import Store


class StoreRepository(ABC):
    @abstractmethod
    def get(self, store_id: int) -> Store | None:
        raise NotImplementedError
