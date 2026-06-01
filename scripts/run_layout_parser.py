from pipeline.layout_parser import parse_xlsx_zones, write_zones
import sys

xlsx = sys.argv[1] if len(sys.argv) > 1 else 'Brigade Road - Store layoutc5f5d56.xlsx'
out = sys.argv[2] if len(sys.argv) > 2 else 'outputs/layout/zones.json'

zones = parse_xlsx_zones(xlsx)
write_zones(zones, out)
print(f'Wrote {len(zones)} zones to {out}')
for z in zones[:20]:
    print(z['zone_id'], z['polygon'])
