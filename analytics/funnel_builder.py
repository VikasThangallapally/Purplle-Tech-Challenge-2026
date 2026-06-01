import json
from pathlib import Path
from typing import List, Dict, Any


def load_events(path: str) -> List[Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()]


def build_funnel(events_path='outputs/events/events.jsonl', zone_events_path='outputs/events/zone_events.jsonl') -> Dict[str, Any]:
    ev = load_events(events_path)
    ze = load_events(zone_events_path)

    entries = sum(1 for e in ev if e.get('event_type') == 'ENTRY')
    exits = sum(1 for e in ev if e.get('event_type') == 'EXIT')
    zone_visits = sum(1 for z in ze if z.get('event_type') == 'ZONE_ENTER')

    # detect billing zone visits (zone_id contains 'billing' case-insensitive)
    billing_zone_visits = sum(1 for z in ze if z.get('event_type') == 'ZONE_ENTER' and z.get('zone_id') and 'bill' in z.get('zone_id').lower())

    funnel = {
        'entries': entries,
        'zone_visits': zone_visits,
        'billing_zone_visits': billing_zone_visits,
        'exits': exits,
    }

    p = Path('outputs/analytics/funnel.json')
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(funnel, f, indent=2)

    return funnel


if __name__ == '__main__':
    f = build_funnel()
    print('Funnel:', f)
