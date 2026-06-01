import json
from pathlib import Path
import math


def load_index(path='outputs/debug/pos_gallery/index.json'):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    return json.loads(p.read_text(encoding='utf-8'))


def load_zones(path='outputs/layout/zones.json'):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    return json.loads(p.read_text(encoding='utf-8'))


def load_tracking(path='outputs/tracking/tracking_results.json'):
    p = Path(path)
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding='utf-8'))


def find_detection_bbox(tracks, camera, frame_number, track_id):
    # camera may be 'CAM 1.mp4'
    for video in tracks:
        if video.get('video_filename') == camera or video.get('video_filename') == camera.replace('.mp4',''):
            for fr in video.get('frames', []):
                if fr.get('frame_number') == frame_number:
                    for det in fr.get('detections', []):
                        if det.get('track_id') == track_id:
                            return det.get('bbox')
    return None


def centroid(points):
    if not points:
        return None
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (sum(xs)/len(xs), sum(ys)/len(ys))


def euclidean(a,b):
    return math.hypot(a[0]-b[0], a[1]-b[1])


def main():
    idx = load_index()
    zones = load_zones()
    tracks = load_tracking()

    # build zone centers map
    zone_centers = {}
    for z in zones:
        poly = z.get('polygon', [])
        if not poly:
            continue
        cx = sum(p[0] for p in poly)/len(poly)
        cy = sum(p[1] for p in poly)/len(poly)
        zone_centers[z['zone_id']] = (cx, cy)

    centers = []
    enriched = []
    for item in idx:
        cam = item.get('camera')
        frame = item.get('frame')
        tid = item.get('track_id')
        bbox = None
        # attempt to find bbox in tracking
        bbox = find_detection_bbox(tracks, cam, frame, tid)
        if bbox is None:
            # try to extract center from filename or skip
            enriched.append({**item, 'center': None, 'bbox': None})
            continue
        cx = (bbox[0]+bbox[2])/2.0
        cy = (bbox[1]+bbox[3])/2.0
        centers.append((cx,cy))
        enriched.append({**item, 'center': (cx,cy), 'bbox': bbox})

    if not centers:
        print('No POS detection centers found')
        return

    centroid_pos = centroid(centers)
    print('POS centroid:', centroid_pos)

    # compute stats per zone
    stats = []
    total_samples = len(centers)
    for zid, zc in zone_centers.items():
        dists = [euclidean(c, zc) for c in centers]
        avg_d = sum(dists)/len(dists)
        near_count = sum(1 for d in dists if d <= 150.0)  # threshold pixels
        stats.append({'zone_id': zid, 'avg_distance': avg_d, 'near_count': near_count, 'dists': dists})

    # scoring: combine normalized near_count and inverse avg distance
    max_near = max(s['near_count'] for s in stats) if stats else 1
    max_avgd = max(s['avg_distance'] for s in stats) if stats else 1
    candidates = []
    for s in stats:
        norm_count = s['near_count'] / max_near if max_near>0 else 0
        inv_dist = 1.0 / (1.0 + s['avg_distance'])
        # score weights: 0.7 count, 0.3 inv_dist
        score = 0.7 * norm_count + 0.3 * inv_dist
        candidates.append({'zone_id': s['zone_id'], 'score': round(score, 3), 'avg_distance': round(s['avg_distance'],1), 'near_count': s['near_count']})

    candidates.sort(key=lambda x: x['score'], reverse=True)

    outp = Path('outputs/debug/billing_zone_candidates.json')
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(candidates, indent=2), encoding='utf-8')

    # recommendation
    best = candidates[0] if candidates else None
    if best:
        explanation = f"Recommend {best['zone_id']} as BILLING (score={best['score']}, near_count={best['near_count']}, avg_distance={best['avg_distance']})"
    else:
        explanation = 'No candidate found'

    print('\nTop candidates:')
    for c in candidates[:10]:
        print(c)

    print('\nRecommendation:')
    print(explanation)

    # visualization
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except Exception:
        print('matplotlib required for visualization')
        return

    fig, ax = plt.subplots(figsize=(10,6))
    xs = [c[0] for c in centers]
    ys = [c[1] for c in centers]
    ax.scatter(xs, ys, c='red', label='POS detections')
    ax.scatter([centroid_pos[0]], [centroid_pos[1]], c='yellow', marker='*', s=200, label='centroid')
    # plot zone centers
    for zid, zc in zone_centers.items():
        ax.scatter([zc[0]], [zc[1]], c='blue')
        ax.text(zc[0], zc[1], zid, fontsize=8)

    # highlight top 3 candidates
    for c in candidates[:3]:
        zid = c['zone_id']
        zc = zone_centers[zid]
        ax.scatter([zc[0]], [zc[1]], c='green', s=100)
        ax.annotate(zid + f' ({c["score"]})', (zc[0], zc[1]), color='green')

    ax.set_title('POS detection cluster and zone centers')
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.invert_yaxis()
    outv = Path('outputs/debug/pos_candidates.png')
    outv.parent.mkdir(parents=True, exist_ok=True)
    plt.legend()
    plt.savefig(outv, bbox_inches='tight')
    plt.close(fig)
    print('Wrote candidates JSON and visualization')


if __name__ == '__main__':
    main()
