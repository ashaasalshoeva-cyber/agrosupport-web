"""Export public read-only snapshot edition. No Python or LLM runs on this host."""
import sys,json,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import science,server
from assistant_template import template
from image_checks import CROP_IDS
root=science.ROOT;out=root/'dist'
if out.exists():shutil.rmtree(out)
out.mkdir()
for name in ['index.html','styles.css','map.css','science.css','integration.css','assets','js','tools']:
 source=root/name
 if source.is_dir():shutil.copytree(source,out/name)
 else:shutil.copy2(source,out/name)
# Original unverified background photos are not published.
shutil.rmtree(out/'assets/bg',ignore_errors=True)
api=out/'snapshot-api';api.mkdir()
def save(name,data):(api/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')))
save('health',{'ok':True,'version':'0.2.0-demo','mode':'cloud-demo','delivery':'snapshot-static'})
save('sites',{'sites':[server.SITE]});save('science_sites',science.SITES);save('photos',{'photos':{},'backgrounds':{}});save('community',{'photos':[]})
for name in ['power','forecast','soil']:
 p=science.SNAP/('legacy_'+name+'.json')
 if p.exists():save('data_'+name,json.loads(p.read_text()))
for site in science.SITES:
 save('twin_'+site,science.twin(site))
 p=science.SNAP/f'modis_{site}_{science.YEAR}.json'
 if p.exists():
  m=json.loads(p.read_text());m.pop('raw',None);m['delivery']='snapshot';save('modis_'+site,m)
 for crop in CROP_IDS:
  b=science.bundle(site,crop);save('evidence_'+site+'_'+crop,b)
  for lang in ['en','ru','tg']:
   save('summary_'+site+'_'+crop+'_'+lang,dict(template(b,lang),evidence=b))
html=(out/'index.html').read_text().replace('<script src="./js/initial-state.js">','<script src="./js/snapshot-adapter.js"></script><script src="./js/initial-state.js">')
(out/'index.html').write_text(html)
# No admin/upload routes in static: no writable server or persistent community photo service.
print('Static build: custom coordinate API and NPK POST are disabled; historical snapshots remain viewable.')
print('Exported snapshot edition:',out)
# Static deployments enforce headers at the asset host where supported.
(out/'_headers').write_text("/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https://*.tile.openstreetmap.org https://server.arcgisonline.com https://gibs.earthdata.nasa.gov; font-src 'self'; connect-src 'self' https://raw.githubusercontent.com; object-src 'none'; frame-ancestors 'none'\n")
