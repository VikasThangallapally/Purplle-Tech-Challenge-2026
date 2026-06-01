import zipfile
p='Brigade Road - Store layoutc5f5d56.xlsx'
with zipfile.ZipFile(p) as z:
    s=z.read('xl/drawings/drawing1.xml').decode('utf-8')
    print(s)
