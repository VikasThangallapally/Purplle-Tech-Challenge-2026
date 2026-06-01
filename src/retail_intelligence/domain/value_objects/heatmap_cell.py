from dataclasses import dataclass


@dataclass(slots=True)
class HeatmapCell:
    x: float
    y: float
    intensity: float
