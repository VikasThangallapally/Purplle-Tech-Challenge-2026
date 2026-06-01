import zipfile
from pathlib import Path
p = Path('Brigade Road - Store layoutc5f5d56.xlsx')
with zipfile.ZipFile(p, 'r') as z:
    print('\n--- drawing1.xml ---')
    print(z.read('xl/drawings/drawing1.xml').decode('utf-8')[:8000])
    print('\n--- drawing rels ---')
    print(z.read('xl/drawings/_rels/drawing1.xml.rels').decode('utf-8')[:4000])
    print('\n--- sheet1 rels ---')
    print(z.read('xl/worksheets/_rels/sheet1.xml.rels').decode('utf-8')[:4000])
