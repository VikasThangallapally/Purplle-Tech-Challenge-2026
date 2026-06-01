from __future__ import annotations

from datetime import datetime, timezone

from retail_intelligence.infrastructure.vision.detector import YOLOv11Detector
from retail_intelligence.infrastructure.vision.event_generator import EventGenerator
from retail_intelligence.infrastructure.vision.queue_detector import QueueDetector
from retail_intelligence.infrastructure.vision.reid import OSNetReIdentifier
from retail_intelligence.infrastructure.vision.state import PipelineResult, ZoneRegion
from retail_intelligence.infrastructure.vision.tracker import ByteTrackTracker
from retail_intelligence.infrastructure.vision.zone_mapper import ZoneMapper


class RetailVisionPipeline:
    def __init__(
        self,
        detector: YOLOv11Detector | None = None,
        tracker: ByteTrackTracker | None = None,
        re_identifier: OSNetReIdentifier | None = None,
        zone_mapper: ZoneMapper | None = None,
        queue_detector: QueueDetector | None = None,
        event_generator: EventGenerator | None = None,
    ) -> None:
        self._detector = detector or YOLOv11Detector()
        self._tracker = tracker or ByteTrackTracker()
        self._re_identifier = re_identifier or OSNetReIdentifier()
        self._zone_mapper = zone_mapper or ZoneMapper()
        self._queue_detector = queue_detector or QueueDetector()
        self._event_generator = event_generator or EventGenerator()

    def process_frame(self, store_id: int, frame: object, timestamp: datetime | None = None) -> PipelineResult:
        now = timestamp or datetime.now(timezone.utc)
        detections = self._detector.detect(frame)
        tracks = self._tracker.track(detections, timestamp=now)
        reidentified_tracks = self._re_identifier.identify(tracks)
        zone_assignments = self._zone_mapper.map(reidentified_tracks, timestamp=now)
        queue_snapshot = self._queue_detector.detect_queue(store_id, zone_assignments)
        assert not isinstance(queue_snapshot, int)
        events = self._event_generator.generate_events(store_id, zone_assignments, queue_snapshot, timestamp=now)

        return PipelineResult(
            detections=detections,
            tracks=tracks,
            reidentified_tracks=reidentified_tracks,
            zone_assignments=zone_assignments,
            queue_snapshot=queue_snapshot,
            events=[event.model_dump(mode="json") for event in events],
        )

    @staticmethod
    def build_default_zone_mapper() -> ZoneMapper:
        return ZoneMapper(
            zones=[
                ZoneRegion(zone_id="ENTRANCE", name="Entrance", zone_type="entrance", x1=0.0, y1=0.0, x2=100.0, y2=100.0),
                ZoneRegion(zone_id="QUEUE", name="Queue", zone_type="queue", x1=100.0, y1=0.0, x2=220.0, y2=220.0),
                ZoneRegion(zone_id="CHECKOUT", name="Checkout", zone_type="checkout", x1=220.0, y1=0.0, x2=320.0, y2=220.0),
            ]
        )
