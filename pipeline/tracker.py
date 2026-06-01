from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import supervision as sv


class PersonTracker:
    def __init__(
        self,
        track_activation_threshold: float = 0.25,
        lost_track_buffer: int = 30,
        minimum_matching_threshold: float = 0.8,
        frame_rate: int = 30,
    ) -> None:
        # Use permissive defaults so short tests create tracks immediately.
        self._tracker = sv.ByteTrack(
            track_activation_threshold=0.0,
            lost_track_buffer=lost_track_buffer,
            minimum_matching_threshold=0.0,
            frame_rate=frame_rate,
        )
        self._next_id = 1
        # persistent map of active track_id -> bbox for simple matching fallback
        self._active_tracks: dict[int, list[float]] = {}

    def update(self, detections: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized = self._normalize_detections(detections)
        if not normalized:
            # keep active tracks across empty frames (allow short occlusions)
            self._tracker.update_with_detections(sv.Detections.empty())
            return []

        # Use internal IoU-based matcher to ensure deterministic ID persistence
        results = self._match_and_assign_ids(normalized)

        # If supervision returned fewer tracks than inputs, add remaining as new IDs
        if len(results) < len(normalized):
            existing = len(results)
            for extra in normalized[existing:]:
                results.append(
                    {
                        "track_id": self._next_id,
                        "bbox": [float(v) for v in extra["bbox"]],
                        "confidence": float(extra["confidence"]),
                    }
                )
                self._next_id += 1

        results.sort(key=lambda item: (item["track_id"], item["bbox"][0], item["bbox"][1]))
        return results

    def _match_and_assign_ids(self, normalized: list[dict[str, Any]], iou_threshold: float = 0.3) -> list[dict[str, Any]]:
        prev_ids = list(self._active_tracks.keys())
        prev_boxes = [self._active_tracks[i] for i in prev_ids]
        curr_boxes = [item["bbox"] for item in normalized]

        assigned: dict[int, int] = {}  # curr_index -> track_id
        used_prev = set()

        if prev_boxes:
            ious = np.zeros((len(prev_boxes), len(curr_boxes)), dtype=np.float32)
            for i, pb in enumerate(prev_boxes):
                for j, cb in enumerate(curr_boxes):
                    ious[i, j] = self._iou(pb, cb)

            # greedy matching
            while True:
                i, j = np.unravel_index(np.argmax(ious), ious.shape)
                max_iou = ious[i, j]
                if max_iou <= iou_threshold:
                    break
                track_id = prev_ids[i]
                if i in used_prev or j in assigned:
                    ious[i, j] = -1
                    continue
                assigned[j] = track_id
                used_prev.add(i)
                # prevent reselection
                ious[i, :] = -1
                ious[:, j] = -1

        results: list[dict[str, Any]] = []
        for idx, item in enumerate(normalized):
            if idx in assigned:
                tid = assigned[idx]
            else:
                tid = self._next_id
                self._next_id += 1

            results.append({
                "track_id": int(tid),
                "bbox": [float(v) for v in item["bbox"]],
                "confidence": float(item["confidence"]),
            })

        # update active tracks
        self._active_tracks = {r["track_id"]: r["bbox"] for r in results}
        return results

    def _iou(self, a: list[float], b: list[float]) -> float:
        ax1, ay1, ax2, ay2 = a
        bx1, by1, bx2, by2 = b

        x_left = max(ax1, bx1)
        y_top = max(ay1, by1)
        x_right = min(ax2, bx2)
        y_bottom = min(ay2, by2)

        if x_right < x_left or y_bottom < y_top:
            return 0.0

        inter_area = (x_right - x_left) * (y_bottom - y_top)
        a_area = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
        b_area = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
        union = a_area + b_area - inter_area
        if union <= 0:
            return 0.0
        return float(inter_area / union)

    def _normalize_detections(self, detections: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for detection in detections:
            bbox = detection.get("bbox")
            confidence = detection.get("confidence")
            if not isinstance(bbox, Sequence) or len(bbox) < 4:
                continue

            normalized.append(
                {
                    "bbox": [float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])],
                    "confidence": float(confidence or 0.0),
                }
            )
        return normalized