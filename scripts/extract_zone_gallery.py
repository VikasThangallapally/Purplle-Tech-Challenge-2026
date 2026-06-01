import json
from pathlib import Path
from statistics import mean
import math

def load_zone_events(path='outputs/events/zone_events.jsonl'):
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()]

def load_tracking(path='outputs/tracking/tracking_results.json'):
    p = Path(path)
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding='utf-8'))

def find_detection_for_event(tracks, camera_filename, frame_number, track_id):
    # camera_filename like 'CAM 1.mp4'
    for video in tracks:
        if video.get('video_filename') == camera_filename or video.get('video_filename') == camera_filename.replace('.mp4',''):
            for fr in video.get('frames', []):
                if fr.get('frame_number') == frame_number:
                    for det in fr.get('detections', []):
                        if det.get('track_id') == track_id:
                            return det, fr
    return None, None

def imread_with_matplotlib(path):
    try:
        import matplotlib.image as mimg
        img = mimg.imread(path)
        return img
    except Exception:
        from PIL import Image
        return Image.open(path)

def imsave_with_matplotlib(path, arr):
    try:
        import matplotlib.pyplot as plt
        plt.imsave(path, arr)
    except Exception:
        from PIL import Image
        if hasattr(arr, 'astype'):
            import numpy as np
            arr = (arr * 255).astype('uint8') if arr.max() <= 1.0 else arr.astype('uint8')
        Image.fromarray(arr).save(path)


def draw_overlay(img, bbox, track_id, zone_id):
    # use matplotlib to draw on image and return RGB array
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    fig, ax = plt.subplots(1)
    ax.imshow(img)
    x1, y1, x2, y2 = bbox
    w = x2 - x1
    h = y2 - y1
    rect = Rectangle((x1, y1), w, h, linewidth=2, edgecolor='red', facecolor='none')
    ax.add_patch(rect)
    ax.text(x1, max(0,y1-8), f'ID:{track_id} {zone_id}', color='yellow', fontsize=10, backgroundcolor='black')
    ax.axis('off')
    fig.canvas.draw()
    import numpy as np
    # Some backends provide tostring_argb — use it and convert to RGB
    w_fig, h_fig = fig.canvas.get_width_height()
    try:
        buf = fig.canvas.tostring_rgb()
        data = np.frombuffer(buf, dtype=np.uint8).reshape((h_fig, w_fig, 3))
    except Exception:
        buf = fig.canvas.tostring_argb()
        arr = np.frombuffer(buf, dtype=np.uint8).reshape((h_fig, w_fig, 4))
        # arr is ARGB => convert to RGB
        data = arr[:, :, 1:4]
    plt.close(fig)
    return data


def main():
    zones = load_zone_events()
    if not zones:
        print('No zone events found at outputs/events/zone_events.jsonl')
        return

    # filter for ZONE_ENTER
    enters = [z for z in zones if z.get('event_type') == 'ZONE_ENTER']
    if not enters:
        print('No ZONE_ENTER events found')
        return

    samples = enters[:5]
    tracks = load_tracking()

    out_dir = Path('outputs/debug/zone_gallery')
    out_dir.mkdir(parents=True, exist_ok=True)
    index = []

    fps = 30.0
    for i, ev in enumerate(samples, start=1):
        cam = ev.get('camera_id')  # e.g., 'CAM 1.mp4'
        track_id = ev.get('track_id')
        ts_ms = ev.get('timestamp_ms')
        # estimate frame number
        frame_number = int(round((ts_ms * fps) / 1000.0))
        if frame_number < 1:
            frame_number = 1

        det, fr = find_detection_for_event(tracks, cam, frame_number, track_id)
        # if not found, try nearby frames
        if det is None:
            for delta in [1, -1, 2, -2, 3, -3]:
                det, fr = find_detection_for_event(tracks, cam, frame_number + delta, track_id)
                if det is not None:
                    frame_number = frame_number + delta
                    break

        camera_folder = cam.replace('.mp4', '')
        img_path = Path('outputs/tracking') / camera_folder / f'frame_{frame_number:04d}.jpg'
        if not img_path.exists():
            # try annotated_image from fr
            if fr and fr.get('annotated_image'):
                img_path = Path(fr.get('annotated_image'))
        if not img_path.exists():
            print(f'Image for {cam} frame {frame_number} not found; skipping sample')
            continue

        img = imread_with_matplotlib(str(img_path))

        if det is None:
            # No detection found for the track in this frame; draw only zone label
            import numpy as np
            h, w = img.shape[0], img.shape[1]
            out_img = img
        else:
            bbox = det.get('bbox')
            out_img = draw_overlay(img, bbox, track_id, ev.get('zone_id'))

        out_file = out_dir / f'{i:02d}_{ev.get("zone_id")}_trk{track_id}_f{frame_number}.png'
        imsave_with_matplotlib(str(out_file), out_img)

        index.append({'image': str(out_file), 'zone_id': ev.get('zone_id'), 'track_id': track_id, 'timestamp_ms': ts_ms})

    # write index.json
    with open(out_dir / 'index.json', 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2)

    # print summary counts
    counts = {}
    for it in index:
        counts[it['zone_id']] = counts.get(it['zone_id'], 0) + 1
    for zid, cnt in counts.items():
        print(zid, cnt)

    print('Wrote', len(index), 'samples to', str(out_dir))


if __name__ == '__main__':
    main()
