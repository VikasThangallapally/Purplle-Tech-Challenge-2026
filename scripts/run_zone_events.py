from pipeline.zone_event_generator import ZoneEventGenerator
from pathlib import Path
import json

def main():
    teg = ZoneEventGenerator()
    events = teg.process_tracking_results('outputs/tracking/tracking_results.json', out_events_path='outputs/events/zone_events.jsonl')
    print(f'Wrote {len(events)} zone events to outputs/events/zone_events.jsonl')

    # analytics
    summary = {}
    for e in events:
        zid = e.get('zone_id')
        if zid is None:
            continue
        rec = summary.setdefault(zid, {'zone_id': zid, 'visits': 0, 'total_dwell_ms': 0, 'dwell_count': 0})
        if e.get('event_type') == 'ZONE_ENTER':
            rec['visits'] += 1
        if e.get('event_type') == 'ZONE_DWELL' and e.get('duration_ms') is not None:
            rec['total_dwell_ms'] += e.get('duration_ms')
            rec['dwell_count'] += 1

    out_summary = []
    for zid, rec in summary.items():
        avg = 0
        if rec['dwell_count']:
            avg = rec['total_dwell_ms'] / rec['dwell_count']
        out_summary.append({'zone_id': zid, 'visits': rec['visits'], 'avg_dwell_ms': int(avg)})

    outp = Path('outputs/events/zone_summary.json')
    outp.parent.mkdir(parents=True, exist_ok=True)
    with open(outp, 'w', encoding='utf-8') as f:
        json.dump(out_summary, f, indent=2)

    # report
    if out_summary:
        sorted_by_visits = sorted(out_summary, key=lambda x: x['visits'], reverse=True)
        most = sorted_by_visits[0]
        least = sorted_by_visits[-1]
        top_dwell = sorted(out_summary, key=lambda x: x['avg_dwell_ms'], reverse=True)[:5]
        print('Most visited zone:', most)
        print('Least visited zone:', least)
        print('Top 5 zones by avg dwell:', top_dwell)
    else:
        print('No zone events to summarize')

if __name__ == '__main__':
    main()
