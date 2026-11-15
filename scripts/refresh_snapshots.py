"""Run from project root. Only successful, actual service responses are saved."""
import sys,json,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import science
from concurrent.futures import ThreadPoolExecutor
p=argparse.ArgumentParser();p.add_argument('--site',choices=list(science.SITES));p.add_argument('--modis',action='store_true');args=p.parse_args()
science.SNAP.mkdir(exist_ok=True)
def save(site):
    try:
        data=science.get_power(site,True)
        if data['delivery']!='live':raise ValueError('Upstream failed; retained previous snapshot')
        (science.SNAP/f'power_{site}_{science.YEAR}.json').write_text(json.dumps(data,separators=(',',':')))
        print('POWER saved',site,flush=True)
        if args.modis:
            data=science.get_modis(site,True)
            if data['delivery']=='live':
                (science.SNAP/f'modis_{site}_{science.YEAR}.json').write_text(json.dumps(data,separators=(',',':')))
                print('MODIS saved',site,flush=True)
    except Exception as e:print('UNAVAILABLE',site,type(e).__name__,str(e),flush=True)
with ThreadPoolExecutor(2) as pool:list(pool.map(save,[args.site] if args.site else science.SITES))

# Supplementary NOAA forecast and NRCS map units; preserve actual responses only.
import server
for name,fn in [('power',server.power_summary),('forecast',server.forecast_summary),('soil',server.soil_summary)]:
 try:
  data=fn();data['delivery']='snapshot'
  (science.SNAP/('legacy_'+name+'.json')).write_text(json.dumps(data))
  print(name,'saved')
 except Exception as e:print(name,'unavailable',type(e).__name__)
