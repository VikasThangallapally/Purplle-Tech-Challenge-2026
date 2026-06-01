import json
import uuid
from pathlib import Path
from typing import Dict, Any
from pipeline.zone_mapper import ZoneMapper


class ZoneState:
    def __init__(self):
        # key: (track_id, camera_id)
        self.states: Dict[str, Dict[str, Any]] = {}

    def key(self, track_id: int, camera_id: str) -> str:
        return f'{camera_id}::{track_id}'

    def get(self, track_id: int, camera_id: str) -> Dict[str, Any]:
        k = self.key(track_id, camera_id)
        return self.states.setdefault(k, {'track_id': track_id, 'camera_id': camera_id, 'current_zone': None, 'previous_zone': None, 'enter_ts': None, 'dwell_emitted': False})


class ZoneEventGenerator:
    def __init__(self, zones_path: str = 'outputs/layout/zones.json', fps: float = 30.0):
        self.zm = ZoneMapper(zones_path)
        self.state = ZoneState()
        self.fps = fps
        self.events = []

    def _make_event(self, track_id: int, camera_id: str, zone_id: str, event_type: str, timestamp_ms: int, duration_ms: int = None) -> Dict:
        e = {
            'event_id': str(uuid.uuid4()),
            'track_id': track_id,
            'camera_id': camera_id,
            'zone_id': zone_id,
            'event_type': event_type,
            'timestamp_ms': int(timestamp_ms),
        }
        if duration_ms is not None:
            e['duration_ms'] = int(duration_ms)
        return e

    def process_frame(self, camera_id: str, frame_number: int, detections: list):
        # estimate timestamp
        timestamp_ms = int((frame_number / float(self.fps)) * 1000.0)
        for det in detections:
            track_id = det.get('track_id')
            bbox = det.get('bbox')
            if bbox is None:
                continue
            cx = (bbox[0] + bbox[2]) / 2.0
            cy = (bbox[1] + bbox[3]) / 2.0
            zone_id = self.zm.map_point(cx, cy)

            s = self.state.get(track_id, camera_id)
            prev = s['current_zone']

            # entered new zone
            if zone_id != prev:
                # emit EXIT for prev if existed
                if prev is not None:
                    # compute dwell
                    enter_ts = s.get('enter_ts')
                    duration = None
                    if enter_ts is not None:
                        duration = timestamp_ms - enter_ts
                        if duration < 0:
                            duration = 0
                    ev = self._make_event(track_id, camera_id, prev, 'ZONE_EXIT', timestamp_ms, duration)
                    self.events.append(ev)
                # emit ENTER for new zone
                if zone_id is not None:
                    ev2 = self._make_event(track_id, camera_id, zone_id, 'ZONE_ENTER', timestamp_ms, None)
                    self.events.append(ev2)
                    s['enter_ts'] = timestamp_ms
                    s['dwell_emitted'] = False
                else:
                    s['enter_ts'] = None
                    s['dwell_emitted'] = False
                s['previous_zone'] = prev
                s['current_zone'] = zone_id
            else:
                # stayed in same zone -> maybe emit dwell
                if zone_id is not None and not s.get('dwell_emitted', False) and s.get('enter_ts') is not None:
                    dwell = timestamp_ms - s['enter_ts']
                    if dwell >= 5000:
                        evd = self._make_event(track_id, camera_id, zone_id, 'ZONE_DWELL', timestamp_ms, dwell)
                        self.events.append(evd)
                        s['dwell_emitted'] = True

    def process_tracking_results(self, tracking_json_path: str, out_events_path: str = 'outputs/events/zone_events.jsonl', fps: float = None):
        p = Path(tracking_json_path)
        if not p.exists():
            raise FileNotFoundError(tracking_json_path)
        if fps is not None:
            self.fps = fps
        with open(p, 'r', encoding='utf-8') as f:
            tracks = json.load(f)
        for video in tracks:
            camera = video.get('video_filename')
            frames = video.get('frames', [])
            for fr in frames:
                fn = fr.get('frame_number')
                dets = fr.get('detections', [])
                self.process_frame(camera, fn, dets)

        # write events
        outp = Path(out_events_path)
        outp.parent.mkdir(parents=True, exist_ok=True)
        with open(outp, 'w', encoding='utf-8') as fo:
            for e in self.events:
                fo.write(json.dumps(e) + '\n')

        return self.events
