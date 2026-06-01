from dataclasses import dataclass

from retail_intelligence.domain.value_objects.bounding_box import BoundingBox


@dataclass(slots=True)
class Detection:
    camera_id: int
    bbox: BoundingBox
    confidence: float

