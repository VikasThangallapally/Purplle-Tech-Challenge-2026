from __future__ import annotations

from pipeline.tracker import PersonTracker


def test_person_tracker_keeps_ids_across_motion_and_occlusion() -> None:
    tracker = PersonTracker()

    frame_1 = [
        {"bbox": [10, 10, 60, 110], "confidence": 0.98},
        {"bbox": [200, 20, 260, 120], "confidence": 0.95},
    ]
    tracks_1 = tracker.update(frame_1)
    assert [track["track_id"] for track in tracks_1] == [1, 2]

    frame_2 = [
        {"bbox": [14, 12, 64, 112], "confidence": 0.97},
        {"bbox": [204, 24, 264, 124], "confidence": 0.94},
    ]
    tracks_2 = tracker.update(frame_2)
    assert [track["track_id"] for track in tracks_2] == [1, 2]

    assert tracker.update([]) == []

    frame_4 = [
        {"bbox": [18, 15, 68, 115], "confidence": 0.96},
        {"bbox": [208, 28, 268, 128], "confidence": 0.93},
        {"bbox": [390, 40, 450, 140], "confidence": 0.92},
    ]
    tracks_4 = tracker.update(frame_4)
    assert [track["track_id"] for track in tracks_4] == [1, 2, 3]


def test_person_tracker_returns_empty_for_empty_input() -> None:
    tracker = PersonTracker()

    assert tracker.update([]) == []