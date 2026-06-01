#!/usr/bin/env python
"""Visualize zones from outputs/layout/zones.json and save PNG.

Usage: python scripts/visualize_zones.py [zones_json] [out_png]
Defaults: outputs/layout/zones.json -> outputs/layout/zones_visualized.png
"""
import json
import os
import sys
from pathlib import Path
from statistics import mean

def visualize(zones_path: str = 'outputs/layout/zones.json', out_path: str = 'outputs/layout/zones_visualized.png'):
    try:
        import matplotlib.pyplot as plt
        from matplotlib.patches import Polygon
        from matplotlib.collections import PatchCollection
    except Exception as e:
        print('matplotlib is required to run this script. Install with: pip install matplotlib')
        raise

    p = Path(zones_path)
    if not p.exists():
        raise FileNotFoundError(zones_path)

    with open(p, 'r', encoding='utf-8') as f:
        zones = json.load(f)

    # collect all points to determine canvas
    all_x = []
    all_y = []
    patches = []
    labels = []
    centers = []

    for z in zones:
        poly = z.get('polygon') or []
        if not poly:
            continue
        xs = [pt[0] for pt in poly]
        ys = [pt[1] for pt in poly]
        all_x.extend(xs)
        all_y.extend(ys)
        patches.append(Polygon(poly, closed=True))
        cx = mean(xs)
        cy = mean(ys)
        centers.append((z.get('zone_id'), cx, cy))
        labels.append((z.get('zone_id'), cx, cy))

    if not patches:
        print('No polygons found in', zones_path)
        return

    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)

    width = max_x - min_x
    height = max_y - min_y

    # create figure sized to content
    dpi = 100
    fig_w = max(6, width / dpi)
    fig_h = max(4, height / dpi)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)

    pcoll = PatchCollection(patches, cmap='tab20', alpha=0.4, edgecolor='black', linewidths=1)
    ax.add_collection(pcoll)

    # annotate labels
    for lab, cx, cy in labels:
        ax.text(cx, cy, lab, fontsize=10, ha='center', va='center', color='black', bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.7))

    # draw centers as small dots and print them
    for zid, cx, cy in centers:
        ax.plot(cx, cy, 'ro', markersize=4)
        print(zid, int(cx), int(cy))

    ax.set_xlim(min_x - 20, max_x + 20)
    ax.set_ylim(min_y - 20, max_y + 20)
    ax.set_aspect('equal')
    ax.invert_yaxis()  # coordinate origin likely top-left in layout image
    ax.axis('off')

    outp = Path(out_path)
    outp.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(outp, bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)
    print('Saved visualization to', str(outp))


if __name__ == '__main__':
    zones = sys.argv[1] if len(sys.argv) > 1 else 'outputs/layout/zones.json'
    out = sys.argv[2] if len(sys.argv) > 2 else 'outputs/layout/zones_visualized.png'
    visualize(zones, out)
