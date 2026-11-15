"""NASA POWER point-series interface, data QA, real-response-only persistence.

NASA weather is spatially gridded climate information, NOT lab soil chemistry.
Cache writes happen only following successful validation of a remote response.
"""
from __future__ import annotations
from datetime import datetime,date,timedelta,timezone
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlencode
import json
import math
import os
import threading
import time

PARAMS=('T2M','T2M_MAX','T2M_MIN','RH2M','PRECTOTCORR','WS2M','ALLSKY_SFC_SW_DWN')
SOURCE='https://power.larc.nasa.gov/api/temporal/daily/point'
STORE=Path(__file__).resolve().parent/'data_snapshots'
LOCK=threading.RLock()
MEM={}
LIFETIME=24*3600


def parse_request(raw):
    def one(k):
        x=raw.get(k)
        if isinstance(x,list):x=x[0] if len(x)==1 else None
        return x
    try:
        lat=float(one('lat'));lon=float(one('lon'))
    except (ValueError,TypeError):raise ValueError('Укажите корректные координаты lat / lon')
    if not all(map(math.isfinite,[lat,lon])) or not -90<=lat<=90 or not -180<=lon<=180:
        raise ValueError('Координаты находятся вне диапазона')
    try:
        start=date.fromisoformat(one('start'))
        end=date.fromisoformat(one('end'))
    except (ValueError,TypeError):raise ValueError('Используйте даты ГГГГ-ММ-ДД')
    if start<date(1981,1,1) or end>date.today()-timedelta(days=7) or start>end or (end-start).days>365:
        raise ValueError('Выберите завершённый исторический период до 366 дней (с 1981 года; без последних 7 дней)')
    return (round(lat,4),round(lon,4),start.isoformat(),end.isoformat())


def request_url(lat,lon,start,end):
    return SOURCE+'?'+urlencode({'parameters':','.join(PARAMS),'community':'AG',
       'latitude':lat,'longitude':lon,'start':start.replace('-',''),'end':end.replace('-',''),
       'format':'JSON','time-standard':'LST'})


def clean_number(x,low=-1e6,high=1e6):
    if isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or x<=-990 or x<low or x>high:return None
    return float(x)


def transform(raw,lat,lon,start,end,url):
    p=raw.get('properties',{}).get('parameter',{}) if isinstance(raw,dict) else {}
    if not isinstance(p,dict) or any(not isinstance(p.get(k),dict) for k in PARAMS):
        raise ValueError('NASA POWER returned incomplete fields; unavailable values were not filled')
    # AG community solar energy is MJ/m²/day; convert to kWh/m²/day for UI.
    units=str(raw.get('parameters',{}).get('ALLSKY_SFC_SW_DWN',{}).get('units','MJ/m^2/day')).lower()
    if 'mj' in units: solar_factor=1/3.6
    elif 'kw-hr' in units or 'kwh' in units: solar_factor=1
    else: raise ValueError('Unknown NASA solar radiation unit: '+units)
    first=date.fromisoformat(start);last=date.fromisoformat(end)
    daily=[];months={};n=0;valid_counts={key:0 for key in PARAMS}
    d=first
    while d<=last:
        key=d.strftime('%Y%m%d');row={'date':d.isoformat()}
        for k in PARAMS:
            val=clean_number(p[k].get(key))
            if k=='PRECTOTCORR' and val is not None and val<0:val=None
            if k in ('RH2M',) and val is not None and not 0<=val<=100:val=None
            if k=='ALLSKY_SFC_SW_DWN' and val is not None:val*=solar_factor
            row[k]=round(val,3) if val is not None else None
            if val is not None:valid_counts[k]+=1
        daily.append(row);n+=1
        m=months.setdefault(d.strftime('%Y-%m'),{'month':d.strftime('%Y-%m'),'days':0,'valid_days':{k:0 for k in PARAMS},'sum':{k:0. for k in PARAMS}})
        m['days']+=1
        for k in PARAMS:
            if row[k] is not None:m['sum'][k]+=row[k];m['valid_days'][k]+=1
        d+=timedelta(days=1)
    if not n or not valid_counts['T2M'] or not valid_counts['PRECTOTCORR']:
        raise ValueError('No usable temperature or precipitation records returned by NASA')
    monthly=[]
    for m in months.values():
        month={'month':m['month'],'expected_days':m['days']}
        for k in PARAMS:
            count=m['valid_days'][k]
            month[k]=round(m['sum'][k] if k=='PRECTOTCORR' else m['sum'][k]/count,2) if count else None
            month[k+'_valid_days']=count
        monthly.append(month)
    rain_ok=valid_counts['PRECTOTCORR']==n
    total_rain=round(sum(row['PRECTOTCORR'] for row in daily if row['PRECTOTCORR'] is not None),2) if rain_ok else None
    mean_temp=round(sum(row['T2M'] for row in daily if row['T2M'] is not None)/valid_counts['T2M'],2)
    return {'source':'NASA POWER','source_url':url,'retrieved_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'data_status':'live-real-api','snapshot':False,'coordinates':{'lat':lat,'lon':lon},'period':{'start':start,'end':end},
        'time_standard':'LST','units':{'T2M':'°C','T2M_MAX':'°C','T2M_MIN':'°C','RH2M':'%',
        'PRECTOTCORR':'mm/day','WS2M':'m/s','ALLSKY_SFC_SW_DWN':'kWh/m²/day'},
        'daily':daily,'monthly':monthly,'valid_days':valid_counts,'expected_days':n,
        'totals':{'rain_mm':total_rain,'temperature_mean_c':mean_temp},
        'limits':'Gridded near-surface weather estimates, not field sensors. Missing rainfall prevents a complete-period precipitation total. No NPK assay or irrigation prescription.'}


def cache_path(lat,lon,start,end):
    digest=sha256(f'{lat:.4f}|{lon:.4f}|{start}|{end}|v1'.encode()).hexdigest()[:32]
    return STORE/f'agro_weather_{digest}.json'


def read_saved(lat,lon,start,end):
    path=cache_path(lat,lon,start,end)
    try:
        entry=json.loads(path.read_text('utf-8'))
        if entry.get('verified_source') is not True:return None
        data=entry.get('data')
        if not isinstance(data,dict) or data.get('coordinates')!={'lat':lat,'lon':lon} or data.get('period')!={'start':start,'end':end}:
            return None
        if not isinstance(data.get('monthly'),list) or not data.get('source_url','').startswith(SOURCE):return None
        return {**data,'snapshot':True,'data_status':'verified-stored-snapshot','snapshot_retrieved_at':entry['retrieved_at']}
    except (OSError,ValueError,TypeError,KeyError):return None


def save_real(lat,lon,start,end,data):
    STORE.mkdir(exist_ok=True)
    payload={'verified_source':True,'retrieved_at':data['retrieved_at'],'data':data}
    path=cache_path(lat,lon,start,end)
    # Avoid leaving partially written files after a process crash.
    import tempfile
    fd,temp=tempfile.mkstemp(prefix='.agro_weather_',suffix='.tmp',dir=STORE)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False)
        os.replace(temp,path)
    finally:
        if os.path.exists(temp):os.remove(temp)


def get_weather(lat,lon,start,end,fetcher):
    key=(lat,lon,start,end)
    with LOCK:
        row=MEM.get(key)
        if row and time.monotonic()-row[0]<LIFETIME:return dict(row[1])
    url=request_url(*key)
    # A recent verified snapshot can serve requests without repeatedly downloading
    # the same gridded weather point (POWER asks clients to avoid duplicate polling).
    previous=read_saved(*key)
    if previous:
        try:
            fetched=datetime.fromisoformat(previous['retrieved_at'])
            if datetime.now(timezone.utc)-fetched<timedelta(hours=24):
                with LOCK:MEM[key]=(time.monotonic(),previous)
                return previous
        except (ValueError,TypeError):pass
    try:
        raw=fetcher(url,timeout=30)
        data=transform(raw,*key,url)
        save_real(*key,data)
        with LOCK:MEM[key]=(time.monotonic(),data)
        return dict(data)
    except (OSError,ValueError,KeyError,RuntimeError,TimeoutError) as ex:
        if previous:return previous
        raise
