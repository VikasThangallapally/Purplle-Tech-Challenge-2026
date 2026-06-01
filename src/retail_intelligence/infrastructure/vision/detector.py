from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import Any, TypedDict

from retail_intelligence.domain.entities.detection import Detection
from retail_intelligence.domain.value_objects.bounding_box import BoundingBox

try:
    from ultralytics import YOLO
except ImportError:  # pragma: no cover - exercised only when dependency is unavailable
    YOLO = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class PersonDetection(TypedDict):
    bbox: list[float]
    confidence: float
    class_id: int
    class_name: str


class YOLODetector:
    def __init__(self, model_path: str = "yolo11n.pt", confidence_threshold: float = 0.5) -> None:
        if YOLO is None:
            raise RuntimeError("ultralytics is required for YOLO detection")
        self._model_path = model_path
        self._model = YOLO(model_path)
        self._confidence_threshold = confidence_threshold
        logger.info("Initialized YOLO detector", extra={"model_path": model_path, "confidence_threshold": confidence_threshold})

    def detect(self, frame: Any) -> list[PersonDetection]:
        logger.debug("Running YOLO inference")
        results = self._model.predict(source=frame, conf=self._confidence_threshold, verbose=False)
        detections: list[PersonDetection] = []

        for result in results:
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue

            xyxy_values = self._to_sequence(getattr(boxes, "xyxy", []))
            confidence_values = self._to_sequence(getattr(boxes, "conf", []))
            class_values = self._to_sequence(getattr(boxes, "cls", []))

            for bbox, confidence, class_id in zip(xyxy_values, confidence_values, class_values):
                class_index = int(class_id)
                if class_index != 0:
                    continue

                class_name = self._class_name(class_index)
                detections.append(
                    {
                        "bbox": [float(value) for value in bbox[:4]],
                        "confidence": float(confidence),
                        "class_id": class_index,
                        "class_name": class_name,
                    }
                )

        logger.info("YOLO inference complete", extra={"person_detections": len(detections)})
        return detections

    def _class_name(self, class_id: int) -> str:
        names = getattr(self._model, "names", {})
        if isinstance(names, Mapping):
            return str(names.get(class_id, "person" if class_id == 0 else f"class_{class_id}"))
        if isinstance(names, Sequence) and class_id < len(names):
            return str(names[class_id])
        return "person" if class_id == 0 else f"class_{class_id}"

    def _to_sequence(self, value: Any) -> list[Any]:
        if hasattr(value, "cpu"):
            value = value.cpu()
        if hasattr(value, "numpy"):
            value = value.numpy()
        if hasattr(value, "tolist"):
            value = value.tolist()
        if isinstance(value, Sequence):
            return list(value)
        return []


class YOLOv11Detector:
    def __init__(self, backend: object | None = None, confidence_threshold: float = 0.5, model_path: str = "yolo11n.pt") -> None:
        self._backend = backend
        self._yolo = YOLODetector(model_path=model_path, confidence_threshold=confidence_threshold) if backend is None else None
        self._confidence_threshold = confidence_threshold

    def detect(self, frame: object) -> list[Detection]:
        if self._backend is not None and hasattr(self._backend, "detect"):
            logger.info("Running YOLOv11 backend detection")
            return list(self._normalize_backend_output(self._backend.detect(frame)))

        if isinstance(frame, Mapping):
            return self._detect_from_mapping(frame)

        if self._yolo is None:
            logger.debug("YOLO model unavailable")
            return []

        person_detections = self._yolo.detect(frame)
        return [
            Detection(
                camera_id=0,
                bbox=BoundingBox(
                    x1=det["bbox"][0],
                    y1=det["bbox"][1],
                    x2=det["bbox"][2],
                    y2=det["bbox"][3],
                ),
                confidence=det["confidence"],
            )
            for det in person_detections
        ]

    def _detect_from_mapping(self, frame: Mapping[str, object]) -> list[Detection]:
        detections: list[Detection] = []
        camera_id = int(frame.get("camera_id", 0) or 0)
        raw_detections = frame.get("detections") or frame.get("objects") or frame.get("boxes") or []

        if isinstance(raw_detections, Mapping):
            raw_detections = [raw_detections]

        if not isinstance(raw_detections, Sequence):
            return detections

        for item in raw_detections:
            if not isinstance(item, Mapping):
                continue
            confidence = float(item.get("confidence", 0.0) or 0.0)
            if confidence < self._confidence_threshold:
                continue

            bbox_values = item.get("bbox") or item.get("box") or item.get("xyxy")
            if not isinstance(bbox_values, Sequence) or len(bbox_values) < 4:
                continue

            detections.append(
                Detection(
                    camera_id=camera_id,
                    bbox=BoundingBox(
                        x1=float(bbox_values[0]),
                        y1=float(bbox_values[1]),
                        x2=float(bbox_values[2]),
                        y2=float(bbox_values[3]),
                    ),
                    confidence=confidence,
                )
            )

        return detections

    def _normalize_backend_output(self, output: object) -> list[Detection]:
        if isinstance(output, Sequence):
            normalized: list[Detection] = []
            for item in output:
                if isinstance(item, Detection):
                    normalized.append(item)
                    continue
                if isinstance(item, Mapping):
                    normalized.extend(self._detect_from_mapping(item))
            return normalized
        return []


PersonDetector = YOLOv11Detector


