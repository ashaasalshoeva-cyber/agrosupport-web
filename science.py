"""Server-owned evidence, bounded remote requests and provenance-preserving snapshots."""
import json
import calendar
import statistics
import hashlib
import threading
from datetime import datetime, timezone, date, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from agro_calc import finite, gdd, frost_window, precipitation_anomaly, climate_similarity
ROOT=Path(__file__).resolve().parent
SNAP=ROOT/'data_snapshots'
YEAR=datetime.now(timezone.utc).year-1
PARAMS='T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,ALLSKY_SFC_SW_DWN,RH2M,WS2M,GWETROOT'
SITES={
 'USA-NE-SCAL':{'lat':40.575256,'lon':-98.137824,'name':'UNL SCAL · Nebraska','kind':'research_reference'},
 'TJK-SUG-001':{'lat':40.275,'lon':69.635,'name':'Sughd · Тоҷикистон','kind':'regional_reference'},
 'TJK-KHT-002':{'lat':37.833,'lon':68.782,'name':'Khatlon · Тоҷикистон','kind':'regional_reference'},
 'TJK-DRS-003':{'lat':38.526,'lon':68.563,'name':'RRP · Тоҷикистон','kind':'regional_reference'},
 'TJK-GBA-004':{'lat':37.49,'lon':71.55,'name':'GBAO · Тоҷикистон','kind':'regional_reference'}}
MEM={}; LOCK=threading.RLock()

def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')

def request_json(url):
    with urlopen(Request(url,headers={'Accept':'application/json','User-Agent':'AgroSupport/0.2.0-demo educational research'}),timeout=50) as r:
        data=r.read(4_000_001)
    if len(data)>4_000_000: raise ValueError('Response too large')
    return json.loads(data)

def snapshot(key, producer, refresh=False):
    """Bundled data are explicitly snapshots, never mislabeled as live responses."""
    path=SNAP/(key+'.json')
    with LOCK:
        if not refresh and key in MEM: return MEM[key]
    if not refresh and path.exists():
        result=json.loads(path.read_text());result['delivery']='snapshot'
        with LOCK: MEM[key]=result
        return result
    try:
        result=producer();result['retrieved_at']=now();result['delivery']='live'
    except Exception:
        if not path.exists(): raise
        result=json.loads(path.read_text());result['delivery']='snapshot';result['upstream_unavailable']=True
    with LOCK: MEM[key]=result
    return result

def power_url(site,first=YEAR-10,last=YEAR):
    s=SITES[site]
    return 'https://power.larc.nasa.gov/api/temporal/daily/point?'+urlencode({
     'latitude':s['lat'],'longitude':s['lon'],'start':f'{first}0101','end':f'{last}1231',
     'community':'AG','parameters':PARAMS,'format':'JSON','time-standard':'LST'})

def get_power(site,refresh=False):
    if site not in SITES: raise ValueError('Unknown site')
    def produce():
        url=power_url(site);raw=request_json(url)
        if not all(p in raw.get('properties',{}).get('parameter',{}) for p in PARAMS.split(',')): raise ValueError('Incomplete POWER response')
        return {'source':'NASA POWER','source_url':url,'type':'model_reanalysis',
                'resolution':'Meteorology: 0.5° × 0.625°; solar: 1° × 1° (native products)',
                'period':[YEAR-10,YEAR],'site_id':site,'raw':raw}
    return snapshot(f'power_{site}_{YEAR}',produce,refresh)

def year_metrics(params,year,crop='corn'):
    days=(date(year+1,1,1)-date(year,1,1)).days
    keys=[(date(year,1,1)+timedelta(days=i)).strftime('%Y%m%d') for i in range(days)]
    def vals(p): return [params.get(p,{}).get(k) for k in keys]
    def complete(p): return all(finite(v) for v in vals(p))
    rain=sum(vals('PRECTOTCORR')) if complete('PRECTOTCORR') else None
    gs=[gdd(a,b) for a,b in zip(vals('T2M_MIN'),vals('T2M_MAX'))]
    window=frost_window(params.get('T2M_MIN',{}),year)
    mean=lambda p: statistics.mean(vals(p)) if complete(p) else None
    return {'year':year,'rain_mm':round(rain,2) if rain is not None else None,
            'gdd':round(sum(gs),2) if crop=='corn' and all(v is not None for v in gs) else None,
            'frost_free_days':window['days'],'frost':window,
            'mean_c':round(mean('T2M'),2) if mean('T2M') is not None else None,
            'radiation':round(mean('ALLSKY_SFC_SW_DWN'),3) if mean('ALLSKY_SFC_SW_DWN') is not None else None,
            'root_wetness':round(mean('GWETROOT'),3) if mean('GWETROOT') is not None else None,
            'hot_days_30c':sum(v>30 for v in vals('T2M_MAX')) if complete('T2M_MAX') else None,
            'valid_days':sum(finite(v) for v in vals('T2M')), 'expected_days':days}

def monthly_climatology(params):
    """Only complete source months contribute; missing months remain null."""
    import calendar
    fields=('PRECTOTCORR','T2M','ALLSKY_SFC_SW_DWN','WS2M','GWETROOT')
    def month_record(year,month):
        dates=[f'{year:04d}{month:02d}{d:02d}' for d in range(1,calendar.monthrange(year,month)[1]+1)]
        record={'month':month,'year':year}
        for field in fields:
            vals=[params.get(field,{}).get(day) for day in dates]
            if any(not finite(v) for v in vals):record[field]=None
            else:record[field]=round(sum(vals) if field=='PRECTOTCORR' else sum(vals)/len(vals),3)
        return record
    last=[month_record(YEAR,m) for m in range(1,13)]
    baseline=[]
    for month in range(1,13):
        samples=[month_record(y,month) for y in range(YEAR-10,YEAR)]
        record={'month':month,'period':[YEAR-10,YEAR-1]}
        for field in fields:
            vals=[row[field] for row in samples]
            record[field]=round(sum(vals)/10,3) if all(v is not None for v in vals) else None
        baseline.append(record)
    return {'last_complete_year':last,'baseline_10_years':baseline,'units':{
     'PRECTOTCORR':'mm/month','T2M':'°C','ALLSKY_SFC_SW_DWN':'kWh/m²/day',
     'WS2M':'m/s','GWETROOT':'0–1 (modelled root-zone wetness)'},'baseline_years':[YEAR-10,YEAR-1]}

def bundle(site,crop):
    base={'site_id':site,'site':SITES[site],'crop':crop,'metrics':{},'sources':[], 'status':'unavailable'}
    try:
        p=get_power(site);params={k:dict(v) for k,v in p['raw']['properties']['parameter'].items()}
        solar_unit=p['raw'].get('parameters',{}).get('ALLSKY_SFC_SW_DWN',{}).get('units','')
        if solar_unit.startswith('MJ'):
            params['ALLSKY_SFC_SW_DWN']={k:v/3.6 if finite(v) else v for k,v in params['ALLSKY_SFC_SW_DWN'].items()}
        years=[year_metrics(params,y,crop) for y in range(YEAR-10,YEAR+1)]
        metrics=years[-1];anom=precipitation_anomaly(metrics['rain_mm'],[y['rain_mm'] for y in years[:-1]])
        metrics['rain_anomaly']= {k:round(v,2) if v is not None else None for k,v in anom.items()}
        weekly=[]
        for week in range(1,54):
            rows=[]
            for k,v in params['T2M_MIN'].items():
                d=date.fromisoformat(k[:4]+'-'+k[4:6]+'-'+k[6:])
                if d.year < YEAR and d.isocalendar().week==week and finite(v): rows.append(v)
            weekly.append({'week':week,'frost_probability':round(sum(v<=0 for v in rows)/len(rows),3) if rows else None,'n':len(rows)})
        base.update(status='available',metrics=metrics,years=years,weeks=weekly,monthly=monthly_climatology(params),
         sources=[p['source_url']],provenance={k:p[k] for k in ('source','type','resolution','retrieved_at','period','delivery')},
         units=p['raw'].get('parameters',{}),baseline=[YEAR-10,YEAR-1],
         thresholds=json.loads((ROOT/'data/crop_thresholds.json').read_text()).get(crop),
         calculated_at=now())
    except (OSError,ValueError,KeyError,TypeError): pass
    return base

FEATURES=['rain_mm','mean_c','hot_days_30c','frost_free_days','gdd','radiation']
SCALES=[300,10,30,60,1000,2] # explicit exploratory scales, not fitted weights

def twin(site):
    a=bundle(site,'corn');b=bundle('USA-NE-SCAL','corn')
    def vector(item):
        years=item.get('years',[])[:-1]
        return [statistics.mean([y[k] for y in years]) if len(years)==10 and all(y[k] is not None for y in years) else None for k in FEATURES]
    va,vb=vector(a),vector(b)
    if any(v is None for v in va+vb): return {'status':'unavailable','features':FEATURES}
    result=climate_similarity(va,vb,SCALES)
    return dict(result,status='available',features=FEATURES,selected=va,reference=vb,
                reference_id='USA-NE-SCAL',baseline=[YEAR-10,YEAR-1],
                provenance=[a['provenance'],b['provenance']],period='calendar_year',
                limitation='Exploratory annual climate comparison, not crop suitability. One reference only.')


def get_modis(site,refresh=False):
    s=SITES[site];base='https://modis.ornl.gov/rst/api/v1/MOD13Q1/'
    def produce():
        coords={'latitude':s['lat'],'longitude':s['lon']}
        bands=request_json(base+'bands')['bands']
        band=next(b for b in bands if b['band']=='250m_16_days_NDVI')
        dates=request_json(base+'dates?'+urlencode(coords))['dates']
        dates=[d for d in dates if d['calendar_date'].startswith(str(YEAR))]
        if not dates: raise ValueError('No MODIS dates')
        responses=[];rows=[]
        # Maximum ten composites per request; quality band must match same pixel/date.
        for i in range(0,len(dates),5):
            q=dict(coords,startDate=dates[i]['modis_date'],endDate=dates[min(i+4,len(dates)-1)]['modis_date'],kmAboveBelow=0,kmLeftRight=0)
            chunk_path=SNAP/f'modis_chunk_{site}_{YEAR}_{i}.json'
            if chunk_path.exists(): raw=json.loads(chunk_path.read_text())['raw']
            else:
                try: raw=request_json(base+'subset?'+urlencode(q))
                except (OSError,ValueError):
                    rows.extend({'date':d['calendar_date'],'ndvi':None,'valid_pixels':0,'total_pixels':None,'status':'source_unavailable'} for d in dates[i:i+5])
                    continue
                if refresh: chunk_path.write_text(json.dumps({'source_url':base+'subset?'+urlencode(q),'retrieved_at':now(),'raw':raw}))
            responses.append(raw)
            quality={x['calendar_date']:x['data'] for x in raw['subset'] if x['band']=='250m_16_days_pixel_reliability'}
            for x in raw['subset']:
                if x['band']!=band['band']:continue
                numbers=x['data'];qa=quality.get(x['calendar_date'],[])
                valid=[float(v)*float(band['scale_factor']) for j,v in enumerate(numbers) if -2000<=float(v)<=10000 and j<len(qa) and qa[j]==0]
                rows.append({'date':x['calendar_date'],'ndvi':round(statistics.mean(valid),4) if valid else None,
                             'valid_pixels':len(valid),'total_pixels':len(numbers)})
        return {'source':'NASA MODIS MOD13Q1 / ORNL DAAC','source_url':base,'type':'satellite',
                'resolution':'250 m nominal · 16-day composite · QA reliability = 0 only',
                'site_id':site,'year':YEAR,'rows':rows,'band_metadata':band,'raw':responses,
                'status':'partial' if any(x.get('status')=='source_unavailable' for x in rows) else 'complete',
                'valid_composites':sum(x['ndvi'] is not None for x in rows)}
    return snapshot(f'modis_{site}_{YEAR}',produce,refresh)
