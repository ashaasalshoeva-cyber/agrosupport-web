"""Reproducible NOAA GHCN vs NASA POWER evaluation from archived, real source responses.

No observation is synthesized; station-derived (TMAX+TMIN)/2 is explicitly
labelled a proxy rather than measured TAVG. The station is not colocated with
South Central Agricultural Laboratory. Report time basis differs (POWER LST).
"""
from __future__ import annotations
import json, math, sys, calendar
from pathlib import Path
from datetime import date, timedelta
from statistics import mean
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from agro_calc import finite, validation_metrics
STA='USC00251684'; YEAR=2025
LAT1,LON1=40.575256,-98.137824
LAT2,LON2=40.5208,-98.0536

def haversine_km(a,b,c,d):
    R=6371.0;da=math.radians(c-a);db=math.radians(d-b)
    u=math.sin(da/2)**2+math.cos(math.radians(a))*math.cos(math.radians(c))*math.sin(db/2)**2
    return 2*R*math.asin(math.sqrt(u))

def flagged(row,key):
    parts=str(row.get(key+'_ATTRIBUTES','')).split(',')
    return len(parts)>1 and bool(parts[1].strip())

def obs(row,key):
    if row is None or flagged(row,key):return None
    try: v=float(row[key])
    except (KeyError,ValueError,TypeError):return None
    return v if finite(v) else None

def report(base=ROOT):
    weather=json.loads((base/f'data_snapshots/power_USA-NE-SCAL_{YEAR}.json').read_text())
    station=json.loads((base/f'data_snapshots/noaa_station_{STA}_{YEAR}.json').read_text())
    model=weather['raw']['properties']['parameter']
    rows={row.get('DATE'):row for row in station['raw'] if row.get('DATE')}
    comparisons=[('T2M_MAX','TMAX','temperature_max_°C'),('T2M_MIN','TMIN','temperature_min_°C'),('PRECTOTCORR','PRCP','precipitation_mm')]
    paired={}; metrics={}; monthly={}
    for metric,key,label in comparisons:
        aligned=[]
        for i in range((date(YEAR+1,1,1)-date(YEAR,1,1)).days):
            d=date(YEAR,1,1)+timedelta(days=i);stamp=d.strftime('%Y%m%d')
            a=model.get(metric,{}).get(stamp);b=obs(rows.get(d.isoformat()),key)
            if finite(a) and b is not None and (metric!='PRECTOTCORR' or a>=0):aligned.append((d,float(a),b))
        paired[metric]=aligned
        metrics[metric]=validation_metrics([x[1] for x in aligned],[x[2] for x in aligned])
        summary=[]
        for month in range(1,13):
            subset=[x for x in aligned if x[0].month==month]
            if len(subset)!=calendar.monthrange(YEAR,month)[1]:continue
            f=sum if metric=='PRECTOTCORR' else mean
            summary.append({'month':month,'model':round(f(x[1] for x in subset),3),'observed':round(f(x[2] for x in subset),3),'n':len(subset)})
        monthly[metric]=summary
        metrics[metric+'_monthly']=validation_metrics([x['model'] for x in summary],[x['observed'] for x in summary])
    proxy=[]
    for i in range((date(YEAR+1,1,1)-date(YEAR,1,1)).days):
        d=date(YEAR,1,1)+timedelta(days=i);stamp=d.strftime('%Y%m%d')
        row=rows.get(d.isoformat());hi=obs(row,'TMAX');lo=obs(row,'TMIN');v=model.get('T2M',{}).get(stamp)
        if hi is not None and lo is not None and finite(v):proxy.append((d,float(v),(hi+lo)/2))
    metrics['T2M_vs_station_max_min_proxy']=validation_metrics([x[1] for x in proxy],[x[2] for x in proxy])
    result={'year':YEAR,'station_id':STA,'source_url':station['source_url'],
       'retrieved_at':station['retrieved_at'],'power_retrieved_at':weather['retrieved_at'],
       'source_power':weather['source_url'],'station_coordinates':[LAT2,LON2],
       'power_coordinates':[LAT1,LON1],'station_distance_km':round(haversine_km(LAT1,LON1,LAT2,LON2),2),
       'status':'partial' if any(x['n']<365 for x in metrics.values() if isinstance(x,dict)) else 'complete',
       'metrics':metrics,'monthly':monthly,
       'validity_note':'Nearby station, not collocated with SCAL. NASA POWER uses LST; NOAA station reporting times differ. Daily precipitation agreement can be weaker than monthly. No Tajik ground validation.',
       'temperature_proxy_note':'T2M compared with (TMAX+TMIN)/2 is an approximation from station extremes, not official TAVG. Direct temperature comparisons are T2M_MAX ↔ TMAX and T2M_MIN ↔ TMIN.',
       'data_type':'real NASA model vs NOAA ground observations; statistics computed by AgroSupport'}
    (base/'assets/validation.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
    m=metrics
    lines=['# Валидация NASA POWER ↔ NOAA GHCN (2025)','',
        f'Станция: {STA}. Расстояние от пилота SCAL: {result["station_distance_km"]} км (точки не совпадают).',
        'Сохранённые реальные источники: '+str(station['source_url'])+'; '+str(weather['source_url']),
        '', '| Переменная | n (дни) | Bias | MAE | RMSE | r |','|---|---:|---:|---:|---:|---:|']
    for key,v in metrics.items():
        def fmt(x):return '—' if x is None else f'{x:.3f}'
        lines.append('| '+key+' | '+str(v['n'])+' | '+fmt(v['bias'])+' | '+fmt(v['mae'])+' | '+fmt(v['rmse'])+' | '+fmt(v['correlation'])+' |')
    lines+=['','**Ограничения.** '+result['validity_note'],result['temperature_proxy_note'],
           'Расхождения осадков на суточном масштабе не скрываются. Выводы касаются этих двух соседних точек и одного года.',
           'Новых измерений не создавалось. Для Таджикистана наземная валидация не проводилась.']
    (base/'docs/validation_report.md').write_text('\n'.join(lines)+'\n')
    return result
if __name__=='__main__':
    r=report();print('Validation:',r['status'],{k:v['n'] for k,v in r['metrics'].items()})
