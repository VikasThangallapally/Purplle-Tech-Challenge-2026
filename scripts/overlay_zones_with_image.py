import json
from pathlib import Path

def load_zones(path='outputs/layout/zones.json'):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    return json.loads(p.read_text(encoding='utf-8'))


def load_image(path='xl/media/image1.png'):
    p = Path(path)
    if p.exists():
        from PIL import Image
        return Image.open(p).convert('RGBA')
    # fallback: try to extract from the XLSX archive
    xlsx_candidate = Path('Brigade Road - Store layoutc5f5d56.xlsx')
    if xlsx_candidate.exists():
        import zipfile
        with zipfile.ZipFile(xlsx_candidate, 'r') as z:
            try:
                data = z.read('xl/media/image1.png')
                outp = Path('outputs/layout/image1_extracted.png')
                outp.parent.mkdir(parents=True, exist_ok=True)
                outp.write_bytes(data)
                from PIL import Image
                return Image.open(outp).convert('RGBA')
            except KeyError:
                pass
    raise FileNotFoundError(path)


def bbox_from_poly(poly):
    xs = [pt[0] for pt in poly]
    ys = [pt[1] for pt in poly]
    return min(xs), min(ys), max(xs), max(ys)


def rects_intersect(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    return not (ax2 < bx1 or bx2 < ax1 or ay2 < by1 or by2 < ay1)


def visualize(zones_path='outputs/layout/zones.json', image_path='xl/media/image1.png', out_path='outputs/layout/zones_overlay.png'):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.patches import Polygon
        from matplotlib.collections import PatchCollection
    except Exception:
        raise

    zones = load_zones(zones_path)
    img = load_image(image_path)
    img_w, img_h = img.size

    patches = []
    labels = []
    centers = []
    bboxes = []
    for z in zones:
        poly = z.get('polygon', [])
        if not poly:
            continue
        patches.append(Polygon(poly, closed=True))
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        cx = sum(xs) / len(xs)
        cy = sum(ys) / len(ys)
        centers.append((z['zone_id'], cx, cy))
        labels.append((z['zone_id'], cx, cy))
        bboxes.append(bbox_from_poly(poly))

    # define POS region (approx)
    pos_rect = (1000, 400, img_w, 550)

    # find overlapping polygons
    highlighted = set()
    for zid, bbox in zip([z['zone_id'] for z in zones], bboxes):
        if rects_intersect(bbox, pos_rect):
            highlighted.add(zid)

    fig, ax = plt.subplots(figsize=(img_w/100, img_h/100), dpi=100)
    ax.imshow(img)

    pc = PatchCollection(patches, cmap='tab20', alpha=0.4, edgecolor='black', linewidths=1)
    ax.add_collection(pc)

    # highlight overlays: draw red outlines for highlighted zones
    for z in zones:
        zid = z.get('zone_id')
        if zid in highlighted:
            poly = z.get('polygon')
            p = Polygon(poly, closed=True, fill=False, edgecolor='red', linewidth=3)
            ax.add_patch(p)

    for zid, cx, cy in labels:
        ax.text(cx, cy, zid, fontsize=10, ha='center', va='center', color='white', bbox=dict(boxstyle='round,pad=0.2', facecolor='black', alpha=0.6))
        print(zid, int(cx), int(cy))

    # draw POS rect
    from matplotlib.patches import Rectangle
    rx = Rectangle((pos_rect[0], pos_rect[1]), pos_rect[2]-pos_rect[0], pos_rect[3]-pos_rect[1], linewidth=2, edgecolor='yellow', facecolor='none')
    ax.add_patch(rx)

    ax.set_xlim(0, img_w)
    ax.set_ylim(img_h, 0)
    ax.axis('off')

    outp = Path(out_path)
    outp.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(outp, bbox_inches='tight', pad_inches=0)
    plt.close(fig)

    print('Saved overlay to', str(outp))
    print('Highlighted zones overlapping POS region:', sorted(list(highlighted)))


if __name__ == '__main__':
    visualize()
