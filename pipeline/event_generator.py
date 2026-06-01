from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List

from pipeline.session_manager import SessionManager


EVENTS_DIR = Path("outputs/events")


def _make_event(event_type: str, visitor_id: int, camera_id: str, store_id: str, timestamp_ms: float, confidence: float = 1.0, metadata: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "visitor_id": int(visitor_id),
        "camera_id": camera_id,
        "store_id": store_id,
        "event_type": event_type,
        "timestamp": float(timestamp_ms),
        "confidence": float(confidence),
        "metadata": metadata or {},
    }


class EventGenerator:
    def __init__(self, exit_frame_threshold: int = 30, store_id: str = "store") -> None:
        self.sessions = SessionManager(exit_frame_threshold=exit_frame_threshold)
        self.store_id = store_id
        EVENTS_DIR.mkdir(parents=True, exist_ok=True)

    def generate_from_tracking(self, tracking_results: Iterable[Dict[str, Any]], fps_default: float = 30.0) -> List[Dict[str, Any]]:
        """tracking_results: list of per-video dicts (matching tracking_results.json)

        Returns list of generated event dicts and writes events.jsonl to outputs/events.
        """
        events: List[Dict[str, Any]] = []

        for video in tracking_results:
            video_name = video.get("video_filename")
            camera_id = Path(video.get("video_path", video_name)).stem
            fps = float(video.get("fps") or fps_default)

            frames = video.get("frames", [])
            # identify tracks present in the very first frame of this video
            initial_seen: set[int] = set()
            initial_frame_num = None
            if frames:
                first_frame = frames[0]
                initial_frame_num = int(first_frame.get("frame_number", 0))
                initial_seen = {int(tid) for tid in first_frame.get("track_ids", [])}

            for frame in frames:
                frame_index = int(frame.get("frame_number", 0))
                timestamp_ms = frame.get("timestamp_ms")
                if timestamp_ms is None:
                    timestamp_ms = frame_index / fps * 1000.0

                seen_ids = [int(tid) for tid in frame.get("track_ids", [])]
                detections = frame.get("detections", [])
                # map id -> confidence
                conf_map = {int(d["track_id"]): float(d.get("confidence", 1.0)) for d in detections}

                # touch sessions for seen ids
                for vid in seen_ids:
                    is_initial = (initial_frame_num is not None and frame_index == initial_frame_num and vid in initial_seen)
                    s = self.sessions.touch(vid, frame_index, timestamp_ms, metadata={"camera": camera_id}, is_initial=is_initial, camera_id=camera_id)
                    # ENTRY: only when not an initial/pre-existing session and not already emitted
                    if not s.is_initial and not s.has_entry_event and s.first_frame == frame_index and frame_index == s.last_frame:
                        ev = _make_event("ENTRY", vid, camera_id, self.store_id, timestamp_ms, confidence=conf_map.get(vid, 1.0), metadata={"frame_index": frame_index})
                        events.append(ev)
                        s.has_entry_event = True

                # check for exits (for sessions that were not seen in this frame)
                all_sessions_items = list(self.sessions.all_sessions().items())
                for (vid_key, cam_key), s in all_sessions_items:
                    # only consider sessions for the current camera
                    if cam_key != camera_id:
                        continue
                    if s.visitor_id in seen_ids:
                        continue
                    exited = self.sessions.maybe_exit(s.visitor_id, frame_index, camera_id=cam_key)
                    if exited is not None and exited.has_entry_event:
                        ev = _make_event("EXIT", exited.visitor_id, cam_key, self.store_id, exited.last_seen_ms, confidence=1.0, metadata={"last_frame": exited.last_frame})
                        events.append(ev)

        # sort events globally by timestamp, camera_id, event_id then write
        def _etype_rank(ev: Dict[str, Any]) -> int:
            t = ev.get("event_type", "")
            return 0 if t == "ENTRY" else 1

        events.sort(key=lambda e: (float(e.get("timestamp", 0.0)), str(e.get("camera_id", "")), _etype_rank(e), str(e.get("event_id", ""))))
        out_path = EVENTS_DIR / "events.jsonl"
        with out_path.open("w", encoding="utf-8") as f:
            for ev in events:
                f.write(json.dumps(ev, ensure_ascii=False) + "\n")

        return events
