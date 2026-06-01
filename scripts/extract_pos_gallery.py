#!/usr/bin/env python
"""Extract gallery images of detections near the POS (checkout counter).

Saves annotated images and an index.json with metadata.
"""
import json
from pathlib import Path
from pipeline.zone_mapper import ZoneMapper


def load_tracking(path='outputs/tracking/tracking_results.json'):
    p = Path(path)
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding='utf-8'))


def imread(path):
    from PIL import Image
    return Image.open(path).convert('RGB')


def imsave(path, img):
    from PIL import Image
    if hasattr(img, 'astype'):
        import numpy as np
        img = Image.fromarray(img)
    img.save(path)


def draw_overlay_pil(img, bbox, track_id, zone_id):
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    x1, y1, x2, y2 = [int(v) for v in bbox]
    draw.rectangle([x1, y1, x2, y2], outline='red', width=3)
    try:
        font = ImageFont.truetype('arial.ttf', 16)
    except Exception:
        from PIL import ImageFont
        font = ImageFont.load_default()
    text = f'ID:{track_id} {zone_id}'
    draw.rectangle([x1, max(0, y1-20), x1+len(text)*8, y1], fill='black')
    draw.text((x1+2, max(0, y1-18)), text, fill='yellow', font=font)
    return img


def find_image_path(cam_name, frame_number, fr):
    # cam_name like 'CAM 1.mp4' -> folder 'CAM 1'
    folder = cam_name.replace('.mp4', '')
    candidate = Path('outputs/tracking') / folder / f'frame_{frame_number:04d}.jpg'
    if candidate.exists():
        return candidate
    if fr and fr.get('annotated_image'):
        p = Path(fr.get('annotated_image'))
        if p.exists():
            return p
    return None


def main():
    tracks = load_tracking()
    zm = ZoneMapper('outputs/layout/zones.json')
    fps = 30.0

    # scanning params: initial region
    regions = [
        (1000, 400, 100000, 550),
        (950, 350, 100000, 600),
        (900, 300, 100000, 700),
    ]

    out_dir = Path('outputs/debug/pos_gallery')
    out_dir.mkdir(parents=True, exist_ok=True)
    index = []

    samples_needed = 20
    found = []

    for xmin, ymin, xmax, ymax in regions:
        if len(found) >= samples_needed:
            break
        for video in tracks:
            cam = video.get('video_filename')
            for fr in video.get('frames', []):
                fn = fr.get('frame_number')
                for det in fr.get('detections', []):
                    bbox = det.get('bbox')
                    if not bbox:
                        continue
                    cx = (bbox[0] + bbox[2]) / 2.0
                    cy = (bbox[1] + bbox[3]) / 2.0
                    if cx >= xmin and xmin <= cx <= xmax and ymin <= cy <= ymax:
                        # candidate
                        found.append({'camera': cam, 'frame': fn, 'track_id': det.get('track_id'), 'bbox': bbox, 'frame_obj': fr})
                        if len(found) >= samples_needed:
                            break
                if len(found) >= samples_needed:
                    break
            if len(found) >= samples_needed:
                break

    # deduplicate by camera+frame+track
    unique = []
    seen = set()
    for s in found:
        key = (s['camera'], s['frame'], s['track_id'])
        if key in seen:
            continue
        seen.add(key)
        unique.append(s)
    found = unique[:samples_needed]

    for i, s in enumerate(found, start=1):
        cam = s['camera']
        fn = s['frame']
        track_id = s['track_id']
        bbox = s['bbox']
        fr = s.get('frame_obj')
        img_path = find_image_path(cam, fn, fr)
        if img_path is None:
            continue
        img = imread(str(img_path))
        zone_res = zm.map_bbox_center(bbox)
        zone_id = zone_res.get('zone_id')
        out_img = draw_overlay_pil(img, bbox, track_id, zone_id or 'NONE')
        out_file = out_dir / f'{i:02d}_{zone_id}_trk{track_id}_f{fn}.png'
        imsave(str(out_file), out_img)
        ts_ms = int((fn / fps) * 1000.0)
        index.append({'image': str(out_file), 'zone_id': zone_id, 'track_id': track_id, 'timestamp_ms': ts_ms, 'camera': cam, 'frame': fn})

    with open(out_dir / 'index.json', 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2)

    # summary counts
    counts = {}
    for it in index:
        zid = it.get('zone_id') or 'NONE'
        counts[zid] = counts.get(zid, 0) + 1
    # print summary
    for zid, cnt in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        print(zid, cnt)

    # Rank candidate billing zones
    ranked = sorted([(zid, cnt) for zid, cnt in counts.items()], key=lambda x: x[1], reverse=True)
    candidate = ranked[0] if ranked else (None, 0)
    top_zone, top_count = candidate
    total = sum(cnt for _, cnt in ranked) if ranked else 0
    confidence = (top_count / total) if total > 0 else 0.0

    rec = {
        'billing_zone_candidate': top_zone,
        'sample_count': top_count,
        'total_samples': total,
        'confidence': round(confidence, 2),
        'reason': 'Most detections near POS region mapped to this zone'
    }

    print('\nRecommendation:')
    print(json.dumps(rec, indent=2))


if __name__ == '__main__':
    main()
