import json
from pathlib import Path
from typing import Dict, Any, List


def load_json_lines(path: str) -> List[Dict]:
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()]


def compute_metrics(events_path='outputs/events/events.jsonl', zone_events_path='outputs/events/zone_events.jsonl') -> Dict[str, Any]:
    events = load_json_lines(events_path)
    zone_events = load_json_lines(zone_events_path)

    # unique visitors by visitor_id
    visitor_ids = set(e.get('visitor_id') for e in events if e.get('visitor_id') is not None)
    unique_visitors = len(visitor_ids)

    # visit durations per visitor (matching ENTRY->EXIT)
    sessions = {}
    for e in events:
        vid = e.get('visitor_id')
        if vid is None:
            continue
        sessions.setdefault(vid, []).append(e)

    durations = []
    zone_counts = []
    for vid, evs in sessions.items():
        evs_sorted = sorted(evs, key=lambda x: x.get('timestamp', 0))
        entry_ts = None
        exit_ts = None
        zones_visited = set()
        for e in evs_sorted:
            if e.get('event_type') == 'ENTRY':
                entry_ts = e.get('timestamp')
            elif e.get('event_type') == 'EXIT' and entry_ts is not None:
                exit_ts = e.get('timestamp')
                durations.append(max(0, exit_ts - entry_ts))
                entry_ts = None

        # count zones from mapped zone events where visitor_id matches
        zv = [z for z in zone_events if z.get('visitor_id') == vid and z.get('event_type') == 'ZONE_ENTER']
        for z in zv:
            zones_visited.add(z.get('zone_id'))
        zone_counts.append(len(zones_visited))

    avg_visit_duration = 0
    if durations:
        avg_visit_duration = sum(durations) / len(durations)

    avg_zone_count = 0
    if zone_counts:
        avg_zone_count = sum(zone_counts) / len(zone_counts)

    # most/least visited zones by counting ZONE_ENTER in zone_events
    zone_enter_counts = {}
    for z in zone_events:
        if z.get('event_type') != 'ZONE_ENTER':
            continue
        zid = z.get('zone_id')
        zone_enter_counts[zid] = zone_enter_counts.get(zid, 0) + 1

    most_visited_zone = None
    least_visited_zone = None
    if zone_enter_counts:
        sorted_z = sorted(zone_enter_counts.items(), key=lambda x: x[1], reverse=True)
        most_visited_zone = {'zone_id': sorted_z[0][0], 'visits': sorted_z[0][1]}
        least_visited_zone = {'zone_id': sorted_z[-1][0], 'visits': sorted_z[-1][1]}

    metrics = {
        'unique_visitors': unique_visitors,
        'avg_visit_duration': avg_visit_duration,
        'avg_zone_count': avg_zone_count,
        'most_visited_zone': most_visited_zone,
        'least_visited_zone': least_visited_zone,
    }

    p = Path('outputs/analytics/store_metrics.json')
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)

    return metrics


if __name__ == '__main__':
    m = compute_metrics()
    print('Store metrics:', m)
