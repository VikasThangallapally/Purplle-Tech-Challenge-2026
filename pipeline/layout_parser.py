import zipfile
import xml.etree.ElementTree as ET
import json
from pathlib import Path
from typing import List, Dict, Tuple

NS = {
    'xdr': 'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
}


def _png_size(data: bytes) -> Tuple[int, int]:
    # Parse PNG IHDR chunk for width/height
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError('not a PNG')
    width = int.from_bytes(data[16:20], 'big')
    height = int.from_bytes(data[20:24], 'big')
    return width, height


def parse_xlsx_zones(xlsx_path: str) -> List[Dict]:
    p = Path(xlsx_path)
    if not p.exists():
        raise FileNotFoundError(xlsx_path)

    with zipfile.ZipFile(p, 'r') as z:
        names = z.namelist()
        # read drawing xml
        if 'xl/drawings/drawing1.xml' not in names:
            raise RuntimeError('drawing1.xml not found in xlsx')
        drawing_xml = z.read('xl/drawings/drawing1.xml').decode('utf-8')
        # read drawing rels to locate media
        rels_path = 'xl/drawings/_rels/drawing1.xml.rels'
        media_map = {}
        if rels_path in names:
            rels_xml = z.read(rels_path).decode('utf-8')
            rel_root = ET.fromstring(rels_xml)
            for rel in rel_root:
                rid = rel.attrib.get('Id')
                target = rel.attrib.get('Target')
                media_map[rid] = target

        # find first media image and its size
        img_width = img_height = None
        # try to resolve rId from drawing (picture blip r:embed)
        root = ET.fromstring(drawing_xml)
        pic_extents = None
        for pic in root.findall('.//xdr:pic', NS):
            xfrm = pic.find('.//a:xfrm', NS)
            if xfrm is None:
                continue
            ext = xfrm.find('a:ext', NS)
            off = xfrm.find('a:off', NS)
            if ext is not None:
                try:
                    cx = int(ext.attrib.get('cx'))
                    cy = int(ext.attrib.get('cy'))
                    pic_extents = (cx, cy)
                    break
                except Exception:
                    pass

        # read first media image (image1.png) if present
        media_candidates = [n for n in names if n.startswith('xl/media/')]
        if media_candidates:
            data = z.read(media_candidates[0])
            try:
                img_width, img_height = _png_size(data)
            except Exception:
                img_width = img_height = None

        if pic_extents and img_width:
            emu_cx, emu_cy = pic_extents
            scale_x = img_width / emu_cx
            scale_y = img_height / emu_cy
        else:
            scale_x = scale_y = 1.0

        zones = []
        idx = 1
        for anchor in root.findall('xdr:twoCellAnchor', NS):
            sp = anchor.find('xdr:sp', NS)
            if sp is None:
                continue
            xfrm = sp.find('.//a:xfrm', NS)
            if xfrm is None:
                continue
            off = xfrm.find('a:off', NS)
            ext = xfrm.find('a:ext', NS)
            if off is None or ext is None:
                continue
            try:
                off_x = int(off.attrib.get('x', '0'))
                off_y = int(off.attrib.get('y', '0'))
                ext_cx = int(ext.attrib.get('cx', '0'))
                ext_cy = int(ext.attrib.get('cy', '0'))
            except Exception:
                continue

            # read text if present
            txt = None
            txBody = sp.find('a:txBody', NS)
            if txBody is not None:
                # collect all text runs
                texts = [t.text for t in txBody.findall('.//a:t', NS) if t.text]
                if texts:
                    txt = ' '.join(texts).strip()

            zone_id = txt if txt else f'ZONE_{idx}'
            idx += 1

            # convert EMU -> pixels using scale
            x_px = round(off_x * scale_x)
            y_px = round(off_y * scale_y)
            w_px = round(ext_cx * scale_x)
            h_px = round(ext_cy * scale_y)

            polygon = [
                [x_px, y_px],
                [x_px + w_px, y_px],
                [x_px + w_px, y_px + h_px],
                [x_px, y_px + h_px],
            ]

            zones.append({'zone_id': zone_id, 'polygon': polygon, 'meta': {'emu': {'off': (off_x, off_y), 'ext': (ext_cx, ext_cy)}, 'pixels': {'x': x_px, 'y': y_px, 'w': w_px, 'h': h_px}}})

        return zones


def write_zones(zones: List[Dict], out_path: str):
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(zones, f, indent=2)


if __name__ == '__main__':
    import sys
    xlsx = sys.argv[1] if len(sys.argv) > 1 else 'Brigade Road - Store layoutc5f5d56.xlsx'
    out = sys.argv[2] if len(sys.argv) > 2 else 'outputs/layout/zones.json'
    zones = parse_xlsx_zones(xlsx)
    write_zones(zones, out)
    print(f'Wrote {len(zones)} zones to {out}')
