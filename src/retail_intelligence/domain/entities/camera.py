from dataclasses import dataclass


@dataclass(slots=True)
class Camera:
    id: int
    store_id: int
    name: str
    stream_url: str | None = None
