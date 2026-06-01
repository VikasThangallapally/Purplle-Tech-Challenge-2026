import json
from pathlib import Path

def validate(events_path='outputs/events/zone_events.jsonl'):
    p = Path(events_path)
    if not p.exists():
        print('No events file found:', events_path)
        return False
    events = [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()]

    status = True
    # track enter state per (camera, track_id, zone)
    active = {}
    errors = []
    for e in events:
        t = e.get('event_type')
        key = (e.get('camera_id'), e.get('track_id'), e.get('zone_id'))
        if t == 'ZONE_ENTER':
            if active.get(key, False):
                errors.append(f'Duplicate ENTER for {key} at {e.get("timestamp_ms")}')
                status = False
            active[key] = True
        elif t == 'ZONE_EXIT':
            if not active.get(key, False):
                errors.append(f'EXIT without ENTER for {key} at {e.get("timestamp_ms")}')
                status = False
            active[key] = False
            # dwell duration check if present
            dur = e.get('duration_ms')
            if dur is not None and dur < 0:
                errors.append(f'Negative dwell for {key} at {e.get("timestamp_ms")}')
                status = False
        elif t == 'ZONE_DWELL':
            dur = e.get('duration_ms')
            if dur is None or dur < 0:
                errors.append(f'Invalid dwell duration for {key} at {e.get("timestamp_ms")}')
                status = False

    print('Validation result:', 'PASS' if status else 'FAIL')
    if errors:
        print('\nErrors:')
        for err in errors:
            print('-', err)
    else:
        print('No errors found')
    return status

if __name__ == '__main__':
    validate()
