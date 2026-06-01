from analytics.journey_builder import build_journeys
from analytics.funnel_builder import build_funnel
from analytics.store_metrics import compute_metrics
import json


def main():
    print('Building journeys...')
    jb = build_journeys()
    import os
    os.makedirs('outputs/analytics', exist_ok=True)
    with open('outputs/analytics/journeys.json', 'w', encoding='utf-8') as f:
        json.dump(jb['journeys'], f, indent=2)
    print('Wrote outputs/analytics/journeys.json')

    print('Building funnel...')
    funnel = build_funnel()
    print('Funnel:', funnel)

    print('Computing store metrics...')
    metrics = compute_metrics()
    print('Store metrics:', metrics)


if __name__ == '__main__':
    main()
