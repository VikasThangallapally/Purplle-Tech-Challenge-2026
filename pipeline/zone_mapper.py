import json
from pathlib import Path
from typing import List, Optional, Dict, Any


def _point_in_poly(x: float, y: float, poly: List[List[float]]) -> bool:
    # Ray casting algorithm for point in polygon
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        intersect = ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi)
        if intersect:
            inside = not inside
        j = i
    return inside


class ZoneMapper:
    def __init__(self, zones_path: str = 'outputs/layout/zones.json'):
        p = Path(zones_path)
        if not p.exists():
            raise FileNotFoundError(zones_path)
        with open(p, 'r', encoding='utf-8') as f:
            self.zones = json.load(f)

    def map_point(self, x: float, y: float) -> Optional[str]:
        for z in self.zones:
            poly = z.get('polygon')
            if not poly:
                continue
            if _point_in_poly(x, y, poly):
                return z.get('zone_id')
        return None

    def map_bbox_center(self, bbox: List[float]) -> Optional[Dict[str, Any]]:
        # bbox: [x1,y1,x2,y2]
        x1, y1, x2, y2 = bbox
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        zone = self.map_point(cx, cy)
        return {'center_x': cx, 'center_y': cy, 'zone_id': zone}


def map_detection(detection: Dict, zones_path: str = 'outputs/layout/zones.json') -> Dict:
    zm = ZoneMapper(zones_path)
    bbox = detection.get('bbox')
    track_id = detection.get('track_id')
    res = zm.map_bbox_center(bbox)
    return {'track_id': track_id, 'zone_id': res.get('zone_id'), 'center_x': res.get('center_x'), 'center_y': res.get('center_y')}


if __name__ == '__main__':
    zm = ZoneMapper()
    print('Loaded', len(zm.zones), 'zones')
