from dataclasses import dataclass


@dataclass(slots=True)
class Store:
    id: int
    name: str
    location: str | None = None
