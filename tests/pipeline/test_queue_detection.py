from retail_intelligence.infrastructure.vision.queue_detector import QueueDetector


def test_queue_detector_counts_tracks() -> None:
    detector = QueueDetector()
    assert detector.detect_queue([{"track_id": 1}, {"track_id": 2}]) == 2
