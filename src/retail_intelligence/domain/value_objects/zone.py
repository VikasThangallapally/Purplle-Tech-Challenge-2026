from dataclasses import dataclass


@dataclass(slots=True)
class Zone:
    id: int
    store_id: int
    name: str
    zone_type: str
