import json
from pathlib import Path
from typing import List, Dict, Any, Optional


def _load_events(events_path: str) -> List[Dict[str, Any]]:
    p = Path(events_path)
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()]


def normalize_camera(cam: str) -> str:
    if not cam:
        return cam
    return cam.replace('.mp4', '').strip()


def build_sessions(events: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    # sessions per camera -> list of (visitor_id, entry_ts, exit_ts, events list)
    sessions = {}
    # process events in order
    for e in events:
        ev = e.get('event_type')
        cam = normalize_camera(e.get('camera_id'))
        vid = e.get('visitor_id')
        ts = e.get('timestamp')
        if cam is None or vid is None or ts is None:
            continue
        cam_sessions = sessions.setdefault(cam, {})
        # use visitor per-camera list
        vs_list = cam_sessions.setdefault(vid, [])
        if ev == 'ENTRY':
            # start new session
            vs_list.append({'entry_ts': ts, 'exit_ts': None, 'events': [e]})
        elif ev == 'EXIT':
            # close the last open session if any
            if vs_list:
                last = vs_list[-1]
                if last.get('exit_ts') is None:
                    last['exit_ts'] = ts
                    last['events'].append(e)
                else:
                    # no open session, create a session with only exit
                    vs_list.append({'entry_ts': None, 'exit_ts': ts, 'events': [e]})
            else:
                vs_list.append({'entry_ts': None, 'exit_ts': ts, 'events': [e]})
        else:
            # other event types, attach to last session if exists
            if vs_list:
                vs_list[-1]['events'].append(e)
    return sessions


def map_zone_events_to_visitors(zone_events: List[Dict[str, Any]], sessions: Dict[str, Dict[int, List[Dict[str, Any]]]], tol: float = 50.0) -> List[Dict[str, Any]]:
    # tol: time units tolerance when matching
    mapped = []
    for ze in zone_events:
        cam_raw = ze.get('camera_id')
        cam = normalize_camera(cam_raw)
        ts = ze.get('timestamp_ms')
        if ts is None:
            continue
        # find visitor in sessions[cam] whose session interval contains ts (using numeric time scale)
        cand_vid = None
        if cam in sessions:
            for vid, vs_list in sessions[cam].items():
                for s in vs_list:
                    entry = s.get('entry_ts')
                    exit = s.get('exit_ts')
                    # if both present
                    if entry is not None and exit is not None:
                        if entry - tol <= ts <= exit + tol:
                            cand_vid = vid
                            break
                    elif entry is not None:
                        if entry - tol <= ts:
                            cand_vid = vid
                            break
                if cand_vid is not None:
                    break
        mapped.append({**ze, 'visitor_id': cand_vid})
    return mapped


def build_journeys(events_path: str = 'outputs/events/events.jsonl', zone_events_path: str = 'outputs/events/zone_events.jsonl') -> Dict[str, Any]:
    ev = _load_events(events_path)
    ze = _load_events(zone_events_path)

    sessions = build_sessions(ev)
    mapped_zone = map_zone_events_to_visitors(ze, sessions)

    # assemble per-visitor timelines
    journeys = {}
    # start with session events to create base timeline
    for cam, cam_sessions in sessions.items():
        for vid, vs_list in cam_sessions.items():
            for s in vs_list:
                key = f'VIS_{vid:03d}'
                j = journeys.setdefault(key, {'visitor_id': vid, 'camera_id': cam, 'events': []})
                # add ENTRY and EXIT events from s['events']
                for e in s.get('events', []):
                    t = e.get('timestamp')
                    j['events'].append({'time': float(t), 'type': e.get('event_type'), 'raw': e})

    # add zone events mapped to visitors
    for z in mapped_zone:
        vid = z.get('visitor_id')
        if vid is None:
            continue
        key = f'VIS_{vid:03d}'
        j = journeys.setdefault(key, {'visitor_id': vid, 'camera_id': normalize_camera(z.get('camera_id')), 'events': []})
        # use timestamp_ms as numeric time unit
        t = float(z.get('timestamp_ms'))
        j['events'].append({'time': t, 'type': z.get('event_type'), 'zone_id': z.get('zone_id'), 'raw': z})

    # sort events per journey
    for k, v in journeys.items():
        v['events'].sort(key=lambda x: x['time'])

    return {'journeys': journeys, 'mapped_zone_events': mapped_zone}


if __name__ == '__main__':
    out = build_journeys()
    p = Path('outputs/analytics/journeys.json')
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(out['journeys'], f, indent=2)
    print('Wrote journeys to outputs/analytics/journeys.json')
