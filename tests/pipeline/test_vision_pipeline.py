from datetime import datetime, timezone

from retail_intelligence.infrastructure.vision.pipeline import RetailVisionPipeline


def test_vision_pipeline_processes_frame_end_to_end() -> None:
    pipeline = RetailVisionPipeline(zone_mapper=RetailVisionPipeline.build_default_zone_mapper())
    frame = {
        "camera_id": 1,
        "detections": [
            {
                "bbox": [120, 40, 180, 160],
                "confidence": 0.96,
            }
        ],
    }

    result = pipeline.process_frame(store_id=7, frame=frame, timestamp=datetime.now(timezone.utc))

    assert len(result.detections) == 1
    assert len(result.tracks) == 1
    assert result.reidentified_tracks[0].visitor_id.startswith("visitor-")
    assert result.zone_assignments[0].zone_id == "QUEUE"
    assert result.queue_snapshot.queue_depth == 1
    event_types = {event["event_type"] for event in result.events}
    assert "person_entered" in event_types
    assert "queue_joined" in event_types