import zipfile
import sys
from pathlib import Path
p = Path(__file__).resolve().parents[1] / 'Brigade Road - Store layoutc5f5d56.xlsx'
print('xlsx:', p)
with zipfile.ZipFile(p, 'r') as z:
    names = z.namelist()
    for n in names:
        if n.startswith('xl/drawings/') or n.startswith('xl/media/') or n.startswith('xl/worksheets/') or n.startswith('xl/drawings/'):
            print(n)
    # show drawing xml
    try:
        drawing = z.read('xl/drawings/drawing1.xml')
        print('\n--- drawing1.xml snippet ---')
        print(drawing.decode('utf-8')[:2000])
    except KeyError:
        print('no drawing1.xml')
    # show drawing rels
    try:
        rels = z.read('xl/drawings/_rels/drawing1.xml.rels')
        print('\n--- drawing1.xml.rels snippet ---')
        print(rels.decode('utf-8')[:2000])
    except KeyError:
        print('no drawing rels')
    # list media files and show PNG IHDR
    for name in names:
        if name.startswith('xl/media/'):
            data = z.read(name)
            print(f'\n--- {name} size={len(data)} bytes ---')
            # PNG IHDR width/height are bytes 16-24
            if data[:8] == b'\x89PNG\r\n\x1a\n' and len(data) >= 24:
                width = int.from_bytes(data[16:20], 'big')
                height = int.from_bytes(data[20:24], 'big')
                print('PNG width,height =', width, height)
            else:
                print('not a PNG or too small')
print('\nDone')
