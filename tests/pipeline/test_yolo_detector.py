from __future__ import annotations

from retail_intelligence.infrastructure.vision import detector as detector_module
from retail_intelligence.infrastructure.vision.detector import YOLODetector


class FakeTensor:
    def __init__(self, data):
        self._data = data

    def cpu(self):
        return self

    def numpy(self):
        return self

    def tolist(self):
        return self._data


class FakeBoxes:
    def __init__(self):
        self.xyxy = FakeTensor([[10, 20, 110, 220], [0, 0, 50, 50]])
        self.conf = FakeTensor([0.95, 0.88])
        self.cls = FakeTensor([0, 2])


class FakeResult:
    def __init__(self):
        self.boxes = FakeBoxes()


class FakeModel:
    names = {0: "person", 2: "car"}

    def predict(self, source, conf, verbose):
        return [FakeResult()]


def test_yolo_detector_filters_person_class(monkeypatch) -> None:
    monkeypatch.setattr(detector_module, "YOLO", lambda model_path: FakeModel())

    detector = YOLODetector(model_path="fake-model.pt", confidence_threshold=0.5)
    detections = detector.detect(frame=object())

    assert len(detections) == 1
    assert detections[0]["class_id"] == 0
    assert detections[0]["class_name"] == "person"
    assert detections[0]["confidence"] == 0.95
    assert detections[0]["bbox"] == [10.0, 20.0, 110.0, 220.0]
