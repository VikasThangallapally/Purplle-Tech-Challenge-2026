import zipfile
from pathlib import Path
p = Path('Brigade Road - Store layoutc5f5d56.xlsx')
with zipfile.ZipFile(p, 'r') as z:
    for name in z.namelist():
        if name.startswith('xl/'):
            print(name)
    print('\n--- sheet1.xml head ---')
    try:
        print(z.read('xl/worksheets/sheet1.xml').decode('utf-8')[:2000])
    except KeyError:
        print('no sheet1')
    print('\n--- sharedStrings.xml head ---')
    try:
        print(z.read('xl/sharedStrings.xml').decode('utf-8')[:2000])
    except KeyError:
        print('no sharedStrings')
