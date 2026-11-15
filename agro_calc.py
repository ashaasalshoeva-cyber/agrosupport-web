"""Deterministic educational calculations; missing values never become zero."""
import math
import statistics
from datetime import date, timedelta


def finite(x):
    return isinstance(x, (float, int)) and not isinstance(x, bool) and math.isfinite(x) and x > -990


def gdd(tmin, tmax, base=10, cap=30):
    """Modified corn GDD (°C day): max(0,(min(Tmax,cap)+max(Tmin,base))/2-base).
    NOAA CPC modified degree-day method. No cultivar maturity claim.
    """
    if not finite(tmin) or not finite(tmax) or tmin > tmax:
        return None
    return max(0, (min(tmax, cap) + max(tmin, base))/2 - base)


def frost_window(daily, year):
    """Calendar NH spring (< July) / autumn (>= July); missing days invalidate window.
    Days between last spring and first autumn Tmin <= 0. Boundaries may be censored.
    """
    start, end = date(year, 1, 1), date(year, 12, 31)
    dates = [start+timedelta(days=i) for i in range((end-start).days+1)]
    if any(not finite(daily.get(d.strftime('%Y%m%d'))) for d in dates):
        return {'days': None, 'last_spring': None, 'first_autumn': None, 'complete': False}
    cold = [d for d in dates if daily[d.strftime('%Y%m%d')] <= 0]
    spring = [d for d in cold if d.month < 7]
    autumn = [d for d in cold if d.month >= 7]
    a = max(spring) if spring else start-timedelta(days=1)
    b = min(autumn) if autumn else end+timedelta(days=1)
    return {'days': max(0, (b-a).days-1), 'last_spring': str(a) if spring else None,
            'first_autumn': str(b) if autumn else None, 'complete': True,
            'censored': not spring or not autumn}


def precipitation_anomaly(total, baseline):
    values = [v for v in baseline if finite(v)]
    if not finite(total) or len(values) < 2:
        return {'mm': None, 'percent': None, 'z': None, 'normal': None}
    mean = statistics.mean(values); sd = statistics.stdev(values)
    return {'mm': total-mean, 'percent': 100*(total-mean)/mean if mean else None,
            'z': (total-mean)/sd if sd else None, 'normal': mean}


def climate_similarity(a, b, scales, weights=None):
    """100 exp(-weighted RMS distance). Scales/weights are explicit design assumptions,
    NOT calibrated agronomic probabilities. Identical vectors = 100.
    """
    weights = weights or [1]*len(a)
    if not len(a) == len(b) == len(scales) == len(weights) or not a:
        raise ValueError('Dimensions differ')
    if any(not finite(v) for v in a+b) or any(s <= 0 for s in scales) or any(w < 0 for w in weights) or sum(weights) <= 0:
        raise ValueError('Invalid feature vector')
    terms = [w*((x-y)/s)**2 for x,y,s,w in zip(a,b,scales,weights)]
    distance = math.sqrt(sum(terms)/sum(weights))
    return {'similarity': 100*math.exp(-distance), 'distance': distance,
            'contributions': terms, 'scales': scales, 'weights': weights}


def validation_metrics(model, observed):
    pairs = [(a,b) for a,b in zip(model, observed) if finite(a) and finite(b)]
    if not pairs: return {'n': 0, 'bias': None, 'mae': None, 'rmse': None, 'correlation': None}
    a,b=zip(*pairs); errors=[x-y for x,y in pairs]
    corr = statistics.correlation(a,b) if len(pairs)>1 and len(set(a))>1 and len(set(b))>1 else None
    return {'n':len(pairs), 'bias':statistics.mean(errors),'mae':statistics.mean(map(abs,errors)),
            'rmse':math.sqrt(statistics.mean(e*e for e in errors)), 'correlation':corr}


# Compatibility: deterministic B-model functions, kept separate from A methods.
"""Transparent agronomic indicators from **observed or modelled** daily weather.

All results depend on the input data provenance. Calculations are NOT field
measurements, fertiliser prescriptions, or planting-date recommendations.
"""

from datetime import date
from math import sqrt


def is_valid(value):
    """Reject NASA fill values, booleans, NaN, and unreal climate values."""
    try:
        v = float(value)
        return value is not None and not isinstance(value, bool) and -900 < v < 100000 and v == v
    except (TypeError, ValueError, OverflowError):
        return False


def gdd_day(tmax, tmin, base=10.0, ceiling=30.0):
    """GDD=max(0, (clamp(Tmax,base,ceiling)+clamp(Tmin,base,ceiling))/2-base).

    Corn example: 10/30 C (50/86 F), not a generic threshold for other crops.
    Returns None when either day value is invalid.
    """
    if not (is_valid(tmax) and is_valid(tmin)): return None
    if ceiling <= base: raise ValueError('ceiling must exceed base')
    hi = min(ceiling, max(base, float(tmax)))
    lo = min(ceiling, max(base, float(tmin)))
    return max(0.0, (hi + lo) / 2.0 - base)


def summarize_daily(parameters, year, *, base=10.0, ceiling=30.0, heat_threshold=30.0):
    """Summarize real NASA POWER daily series; unknown values stay unknown."""
    names = ('T2M_MAX','T2M_MIN','PRECTOTCORR','T2M')
    if not all(isinstance(parameters.get(k), dict) for k in names):
        raise ValueError('Missing required POWER daily parameters')
    records = []
    for ds, mx in sorted(parameters['T2M_MAX'].items()):
        if not (ds.isdigit() and len(ds) == 8 and ds.startswith(str(year))): continue
        try: when = date.fromisoformat(f'{ds[:4]}-{ds[4:6]}-{ds[6:8]}')
        except ValueError: continue
        mn=parameters['T2M_MIN'].get(ds)
        rain=parameters['PRECTOTCORR'].get(ds)
        avg=parameters['T2M'].get(ds)
        rec={'date':when.isoformat(), 'doy':when.timetuple().tm_yday,
             'tmax':float(mx) if is_valid(mx) else None,
             'tmin':float(mn) if is_valid(mn) else None,
             'temp':float(avg) if is_valid(avg) else None,
             'rain':float(rain) if is_valid(rain) and float(rain)>=0 else None}
        rec['gdd']=gdd_day(rec['tmax'],rec['tmin'],base,ceiling)
        records.append(rec)
    if not records: raise ValueError('No valid daily records in response')
    growing=[r for r in records if 4 <= int(r['date'][5:7]) <= 9]
    gd=[r['gdd'] for r in growing if r['gdd'] is not None]
    p=[r['rain'] for r in growing if r['rain'] is not None]
    heat=[r for r in growing if r['tmax'] is not None]
    sp=[r['date'] for r in records if r['doy'] <= 182 and r['tmin'] is not None and r['tmin'] <= 0]
    fa=[r['date'] for r in records if r['doy'] > 182 and r['tmin'] is not None and r['tmin'] <= 0]
    means=[r['temp'] for r in growing if r['temp'] is not None]
    result={
      'year':year, 'growing_months':'April–September',
      'gdd_corn_c':round(sum(gd),1) if gd else None,
      'gdd_days':len(gd),
      'rain_mm':round(sum(p),1) if p else None,
      'rain_days':len(p),
      'tmean_c':round(sum(means)/len(means),2) if means else None,
      'temp_days':len(means),
      'days_over_30c':sum(r['tmax']>heat_threshold for r in heat) if heat else None,
      'heat_valid_days':len(heat),
      'last_spring_frost':max(sp) if sp else None,
      'first_autumn_frost':min(fa) if fa else None,
      'frost_note':'Missing event does not prove absence of frost; check valid day coverage.',
      'valid_days':len(records),
      'coverage_fraction':round(len(records)/(366 if year%4==0 and (year%100!=0 or year%400==0) else 365),3),
      'method':'Corn GDD: daily clamped max/min 10–30°C; frost: daily minimum ≤0°C; seasonal April–September; >30°C heat days.',
      'record_type':'calculation-from-NASA-POWER-reanalysis',
    }
    return result


def climate_twin(a,b):
    """Heuristic, fully disclosed feature-distance score, NOT crop suitability.

    Features: mean temperature (15°C scale), growing-season rainfall (400mm),
    corn GDD (1200 degree-days), days above 30°C (60 days). Four features needed.
    Similarity score = 100/(1 + euclidean weighted-normalized-distance).
    Equal weighting is a demo methodological choice, not a calibrated model.
    """
    fs=[('tmean_c',15.0),('rain_mm',400.0),('gdd_corn_c',1200.0),('days_over_30c',60.0)]
    if any(not(is_valid(a.get(k)) and is_valid(b.get(k))) for k,_ in fs):
        return {'status':'insufficient-data','score':None}
    parts=[{'metric':k,'a':a[k],'b':b[k],'scale':s,'normalized_delta':round((a[k]-b[k])/s,4)} for k,s in fs]
    distance=sqrt(sum(x['normalized_delta']**2 for x in parts))
    return {'status':'computed','score':round(100/(1+distance),1),'distance':round(distance,3),
            'features':parts,'method':'Uncalibrated 100/(1+Euclidean distance); arbitrary display similarity, not agricultural transferability.',
            'limits':'NASA gridded estimates; weather alone cannot establish agronomic equivalence.'}
