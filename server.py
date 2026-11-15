"""AAIAP v0.1.1-demo: Nebraska pilot + NASA evidence module.

No accounts or field ownership. Public image uploads are for local testing ONLY.
Never expose this development server directly to the Internet.
"""
from __future__ import annotations
import json
import mimetypes
import science
import agro_nasa
import agro_lab
import agro_ai
from agro_nasa import parse_request as parse_power_request, get_weather as get_agro_weather
from agro_lab import calculate_balance
import os
import hmac
import secrets
import threading
import time
from datetime import datetime, timezone
from agro_calc import summarize_daily, climate_twin
from assistant_template import summary as template_summary
from snapshots import read_snapshot, write_snapshot
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, parse_qs, urlencode, unquote
from urllib.request import Request, urlopen

from image_checks import MAX_IMAGE_BYTES, CROP_IDS
from gallery_store import gallery, append_photo, photo_path
from photo_store import (UPLOAD_DIR, has_admin, admin_revision, check_admin_password, photo_manifest, update_crop_photo, focus_crop_photo, reset_crop_photo)

ROOT=Path(__file__).resolve().parent
MODE = os.environ.get('AAIAP_MODE','local')
CLOUD = MODE == 'cloud-demo'
HOST=os.environ.get('HOST',os.environ.get('AAIAP_HOST','0.0.0.0' if CLOUD else '127.0.0.1'))
PORT=int(os.environ.get('PORT',os.environ.get('AAIAP_PORT','8000')))
VERSION='0.2.1'
SITE={
 'id':'USA-NE-SCAL','name':'South Central Agricultural Laboratory (UNL)',
 'region':'USA-NE-SC','state':'Nebraska','country':'USA',
 'lat':40.575256,'lon':-98.137824,'area_ha':None,
 'location_kind':'verified-research-site-reference-point',
 'precision_note':'Officially published coordinates identify the research laboratory, not an individual field or parcel boundary.',
 'verified_source':'https://scal.unl.edu/location/',
 'about_source':'https://scal.unl.edu/',
 'documented_crops':['corn','soybean'],
 'documented_practices':['center-pivot irrigation','lateral-move irrigation','subsurface drip irrigation'],
 'public':True
}
CACHE={};LOCK=threading.RLock()
POWER_PARAMS=('T2M','PRECTOTCORR','ALLSKY_SFC_SW_DWN','WS2M')
DAILY_PARAMS=('T2M','T2M_MAX','T2M_MIN','PRECTOTCORR')
# These are historical climate estimates, not forecasts or station measurements.
POWER_YEAR=datetime.now(timezone.utc).year-1

# Sessions live only in RAM. Password hashes and photos persist on the laptop.
UPLOAD_LOG = {}
UPLOAD_LOCK = threading.RLock()
MAX_UPLOADS_PER_HOUR = 12
SESSIONS = {}
LOGIN_FAILS = {}
SESSION_TTL = 8 * 60 * 60
MAX_JSON_BYTES = 10_000
API_RATE={}
API_RATE_LOCK=threading.Lock()
API_LIMIT=120

def allow_upload(ip: str) -> bool:
    now = time.monotonic()
    with UPLOAD_LOCK:
        recent = [t for t in UPLOAD_LOG.get(ip, []) if now-t < 3600]
        UPLOAD_LOG[ip] = recent
        return len(recent) < MAX_UPLOADS_PER_HOUR


def record_upload(ip: str) -> None:
    with UPLOAD_LOCK:
        UPLOAD_LOG.setdefault(ip, []).append(time.monotonic())


def _expire_sessions():
    now = time.monotonic()
    with LOCK:
        for key in list(SESSIONS):
            if SESSIONS[key]['until'] < now:
                del SESSIONS[key]

def _check_login_limit(client_ip):
    now = time.monotonic()
    with LOCK:
        attempts = [x for x in LOGIN_FAILS.get(client_ip, []) if now-x < 900]
        LOGIN_FAILS[client_ip] = attempts
        return len(attempts) < 6

def _record_bad_login(client_ip):
    with LOCK:
        LOGIN_FAILS.setdefault(client_ip, []).append(time.monotonic())


def fetch_json(url,*,method='GET',payload=None,timeout=16):
    headers={'Accept':'application/json','User-Agent':'AAIAP-ResearchPilot/0.1.1-demo (+https://agrosupport.earth)'}
    data=None
    if payload is not None:
        data=json.dumps(payload).encode('utf-8');headers['Content-Type']='application/json'
    with urlopen(Request(url,data=data,headers=headers,method=method),timeout=timeout) as r:
        raw=r.read(3_000_001)
        if len(raw)>3_000_000:raise RuntimeError('Source returned an unexpectedly large response')
        return json.loads(raw.decode('utf-8'))


def cached(key,ttl,fn):
    with LOCK:
        row=CACHE.get(key)
        if row and time.monotonic()-row[0]<ttl:return row[1]
    # Persist only successfully retrieved real responses; keep original provenance.
    # A failed refresh never overwrites the last successful NASA snapshot.
    result=fn()
    if key in ('power','season','modis') and isinstance(result,dict) and result.get('source_url'):
        try:
            write_snapshot(key,result,result['source_url'])
        except OSError as exc:
            print(f'NASA snapshot persistence failed ({key}): {exc}',flush=True)
    with LOCK:CACHE[key]=(time.monotonic(),result)
    return result


def valid_value(v):
    return isinstance(v,(float,int)) and not isinstance(v,bool) and -990 < v < 1e12


def power_summary():
    args={'latitude':SITE['lat'],'longitude':SITE['lon'],
          'start':f'{POWER_YEAR}0101','end':f'{POWER_YEAR}1231','community':'AG',
          'parameters':','.join(POWER_PARAMS),'format':'JSON','time-standard':'LST'}
    url='https://power.larc.nasa.gov/api/temporal/daily/point?'+urlencode(args)
    raw=fetch_json(url)
    records={key:dict(val) for key,val in raw.get('properties',{}).get('parameter',{}).items()}
    if not all(p in records for p in POWER_PARAMS):raise ValueError('Incomplete NASA POWER response')
    units=raw.get('parameters',{})
    solar_unit=str(units.get('ALLSKY_SFC_SW_DWN',{}).get('units','MJ/m²/day')).lower()
    if 'mj' in solar_unit:
        records['ALLSKY_SFC_SW_DWN']={k:(v/3.6 if valid_value(v) else v) for k,v in records['ALLSKY_SFC_SW_DWN'].items()}
    elif 'kwh' not in solar_unit:
        raise ValueError('Unknown solar radiation units')
    result=[]
    for month in range(1,13):
        prefix=f'{POWER_YEAR}{month:02d}'
        row={'month':month,'year':POWER_YEAR}
        for p in POWER_PARAMS:
            values=[v for d,v in records[p].items() if d.startswith(prefix) and valid_value(v)]
            row[p]=round(sum(values) if p=='PRECTOTCORR' else sum(values)/len(values),2) if values else None
            row[p+'_days']=len(values)
        result.append(row)
    return {'source':'NASA POWER','source_url':'https://power.larc.nasa.gov/',
            'service':'Daily Point API','reference_year':POWER_YEAR,'coordinates':{'lat':SITE['lat'],'lon':SITE['lon']},
            'units':{'T2M':'°C (daily means → monthly mean)', 'PRECTOTCORR':'mm (daily totals → monthly sum)',
                     'ALLSKY_SFC_SW_DWN':'kWh/m²/day (daily values → monthly mean)',
                     'WS2M':'m/s (daily values → monthly mean)'},
            'resolution_note':'Grid/model estimate for the location, not a measurement at the research plot.',
            'retrieved_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'months':result}


def forecast_summary():
    point_url=f"https://api.weather.gov/points/{SITE['lat']},{SITE['lon']}"
    p=fetch_json(point_url)
    forecast_url=p.get('properties',{}).get('forecast')
    if not isinstance(forecast_url,str) or not forecast_url.startswith('https://api.weather.gov/gridpoints/'):
        raise ValueError('Unexpected NOAA forecast URL')
    data=fetch_json(forecast_url)
    props=data.get('properties',{})
    periods=[]
    for period in props.get('periods',[])[:10]:
        periods.append({k:period.get(k) for k in ('name','startTime','endTime','isDaytime',
                        'temperature','temperatureUnit','probabilityOfPrecipitation',
                        'windSpeed','windDirection','shortForecast','detailedForecast') if k in period})
    if not periods:raise ValueError('Forecast has no periods')
    return {'source':'NOAA National Weather Service','source_url':'https://www.weather.gov/',
            'issued_at':props.get('updateTime') or props.get('generatedAt'),
            'retrieved_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'coordinates':{'lat':SITE['lat'],'lon':SITE['lon']},
            'resolution_note':'Forecast grid, not an on-farm weather station measurement.',
            'periods':periods}


def soil_summary():
    # SDA returns soil *map units*, not lab soil chemistry. Fixed coordinates, no arbitrary query input.
    wkt=f"POINT({SITE['lon']} {SITE['lat']})"
    sql=("SELECT TOP 6 mu.mukey, mu.musym, mu.muname "
         "FROM mapunit mu WHERE mu.mukey IN ("
         f"SELECT mukey FROM SDA_Get_Mukey_from_intersection_with_WktWgs84('{wkt}'))")
    raw=fetch_json('https://SDMDataAccess.sc.egov.usda.gov/Tabular/post.rest',method='POST',
                   payload={'query':sql,'format':'JSON'},timeout=18)
    if not isinstance(raw.get('Table'),list):raise ValueError('Unexpected NRCS soil service format')
    rows=[]
    for item in raw['Table'][:6]:
        if isinstance(item,list) and len(item)>=3:rows.append({'mukey':str(item[0]),'symbol':str(item[1]),'name':str(item[2])})
    return {'source':'USDA NRCS Soil Data Access / SSURGO','source_url':'https://sdmdataaccess.nrcs.usda.gov/',
            'retrieved_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'resolution_note':'Soil map units intersecting a point, not soil lab results or N/P/K measurements.',
            'map_units':rows,'coordinates':{'lat':SITE['lat'],'lon':SITE['lon']}}


def _power_daily_at(lat,lon,start,end):
    args={'latitude':lat,'longitude':lon,'start':start,'end':end,
          'community':'AG','parameters':','.join(DAILY_PARAMS),
          'format':'JSON','time-standard':'LST'}
    obj=fetch_json('https://power.larc.nasa.gov/api/temporal/daily/point?'+urlencode(args), timeout=25)
    data=obj.get('properties',{}).get('parameter',{})
    if not all(isinstance(data.get(k),dict) for k in DAILY_PARAMS):
        raise ValueError('Incomplete NASA POWER response; no figures substituted')
    return data


def season_summary():
    data=_power_daily_at(SITE['lat'],SITE['lon'],f'{POWER_YEAR}0101',f'{POWER_YEAR}1231')
    indicators=summarize_daily(data,POWER_YEAR)
    return {'source':'NASA POWER','source_url':'https://power.larc.nasa.gov/',
            'retrieved_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'year':POWER_YEAR,'indicators':indicators,
            'site_id':SITE['id'],'coordinates':{'lat':SITE['lat'],'lon':SITE['lon']},
            'spatial_resolution':'NASA POWER daily gridded estimate (~0.5-degree meteorological grid; varies by parameter)',
            'provenance_type':'NASA reanalysis/model derived; AAIAP deterministic calculation',
            'limits':'No ground validation performed. Corn GDD only; thresholds for other crops are not established.'}


def modis_summary():
    # ORNL TESViS documented MOD13Q1 Subset API. Actual availability/quality
    # must be verified on a connected device; output is not a plot measurement.
    lat,lon=SITE['lat'],SITE['lon']
    start=f'A{POWER_YEAR}001';end=f'A{POWER_YEAR}365'
    url='https://modis.ornl.gov/rst/api/v1/MOD13Q1/subset?'+urlencode({
        'latitude':lat,'longitude':lon,'startDate':start,'endDate':end,
        'kmAboveBelow':0,'kmLeftRight':0})
    raw=fetch_json(url,timeout=25)
    rows=[]
    for part in raw.get('subset',[]):
        if not isinstance(part,dict) or not part.get('band','').endswith('_NDVI'):continue
        arr=part.get('data',[])
        if not isinstance(arr,list):continue
        valid=[v for v in arr if isinstance(v,(int,float)) and -2000<=v<=10000]
        if not valid:continue
        rows.append({'modis_date':part.get('modis_date'),
                     'ndvi':round(sum(valid)/len(valid)*0.0001,4),
                     'pixels':len(valid)})
    if not rows:raise ValueError('No valid MODIS NDVI pixels returned')
    return {'source':'NASA ORNL DAAC TESViS · MOD13Q1 NDVI',
            'source_url':'https://modis.ornl.gov/data/modis_webservice.html',
            'retrieved_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'year':POWER_YEAR,'rows':rows,
            'resolution_note':'MOD13Q1 ~250m pixels; mixed land cover and QA flags are not yet filtered. Exploratory only; NOT measured NDVI of a field.',
            'status':'experimental-verify-online'}


def twin_summary():
    # Clearly labeled regional reference in Tajikistan, never a field parcel.
    regions=[{'id':'TJ-REGION-REFERENCE','name':'Dushanbe regional reference point (not a field)',
              'lat':38.56,'lon':68.77},
             {'id':'USA-NE-SCAL','name':SITE['name'],'lat':SITE['lat'],'lon':SITE['lon']}]
    results=[]
    # 5 completed growing seasons: enough for an illustrative comparison but not
    # a definitive 30-year climate normal.
    start_year=POWER_YEAR-4
    for r in regions:
        params=_power_daily_at(r['lat'],r['lon'],f'{start_year}0101',f'{POWER_YEAR}1231')
        years=[summarize_daily(params,year) for year in range(start_year,POWER_YEAR+1)]
        cols=('tmean_c','rain_mm','gdd_corn_c','days_over_30c')
        features={k:round(sum(x[k] for x in years if x[k] is not None)/len([x for x in years if x[k] is not None]),2)
                  if any(x[k] is not None for x in years) else None for k in cols}
        results.append({**r,'features':features,'period':f'{start_year}–{POWER_YEAR}',
                        'seasons_with_records':sum(x['coverage_fraction']>.95 for x in years)})
    compare=climate_twin(results[0]['features'],results[1]['features'])
    return {'source':'NASA POWER','source_url':'https://power.larc.nasa.gov/',
            'retrieved_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'regions':results,'similarity':compare,'type':'derived-reanalysis-heuristic',
            'warning':'Regional reference points; no claim of field or farm equivalence. The score is NOT crop suitability.'}


def api_allow(ip):
    now=time.monotonic()
    with API_RATE_LOCK:
        recent=[x for x in API_RATE.get(ip,[]) if now-x<60]
        if len(recent)>=API_LIMIT:API_RATE[ip]=recent;return False
        recent.append(now);API_RATE[ip]=recent
        if len(API_RATE)>500:
            for k in list(API_RATE)[:200]:
                if k!=ip:API_RATE.pop(k,None)
        return True


class Handler(BaseHTTPRequestHandler):
    server_version = 'AAIAP/0.1.1-demo'

    def _json(self, status, payload, *, cookie=None):
        content = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(content)))
        self.send_header('Cache-Control', 'no-store')
        self._security_headers()
        if cookie is not None:
            self.send_header('Set-Cookie', cookie)
        self.end_headers()
        self.wfile.write(content)

    def _security_headers(self):
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','strict-origin-when-cross-origin')
        self.send_header('X-Frame-Options','SAMEORIGIN')
        self.send_header('Permissions-Policy','camera=(), microphone=(), geolocation=()')
        self.send_header('Content-Security-Policy',
          "default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'self'; frame-src 'self'; "
          "script-src 'self' 'unsafe-inline' https://unpkg.com https://cdn.jsdelivr.net; "
          "style-src 'self' 'unsafe-inline' https://unpkg.com https://fonts.googleapis.com; "
          "img-src 'self' data: https://*.tile.openstreetmap.org https://server.arcgisonline.com "
          "https://images.unsplash.com https://gibs.earthdata.nasa.gov; "
          "font-src 'self' https://fonts.gstatic.com; "
          "connect-src 'self' https://power.larc.nasa.gov https://raw.githubusercontent.com https://www.geoboundaries.org "
          "https://gibs.earthdata.nasa.gov; form-action 'self'")

    def _session(self):
        _expire_sessions()
        try:
            jar = SimpleCookie()
            jar.load(self.headers.get('Cookie', ''))
            token = jar['aaiap_admin'].value if 'aaiap_admin' in jar else ''
        except Exception:
            return None, None
        with LOCK:
            session = SESSIONS.get(token)
        if not session or session['until'] < time.monotonic() or session['admin_revision'] != admin_revision():
            return None, None
        return token, session

    def _session_cookie(self, token, expire=False):
        parts = [f'aaiap_admin={token}', 'HttpOnly', 'SameSite=Strict', 'Path=/']
        if expire:
            parts += ['Max-Age=0']
        else:
            parts += [f'Max-Age={SESSION_TTL}']
        # Only enable this when HTTPS is truly used by the public-facing proxy.
        if os.environ.get('AAIAP_COOKIE_SECURE') == '1':
            parts.append('Secure')
        return '; '.join(parts)

    def _require_admin(self):
        if CLOUD:
            self._json(403, {'error_code':'CLOUD_READ_ONLY','error':'Administrative edits are disabled in the cloud demo'})
            return False
        _, session = self._session()
        if not session:
            self._json(401, {'error': 'Войдите как администратор'})
            return False
        sent = self.headers.get('X-AAIAP-CSRF', '')
        if not hmac.compare_digest(sent, session['csrf']):
            self._json(403, {'error': 'Недействительный защитный токен'})
            return False
        # Defense in depth against cross-site requests. CSRF token is mandatory regardless.
        origin = self.headers.get('Origin')
        if origin:
            origin_host = urlparse(origin).netloc.lower()
            request_host = self.headers.get('Host', '').lower()
            if origin_host != request_host or urlparse(origin).scheme not in ('http', 'https'):
                self._json(403, {'error': 'Недопустимый источник запроса'})
                return False
        return True

    def _read_body(self, max_size):
        try:
            n = int(self.headers.get('Content-Length', '-1'))
        except ValueError:
            n = -1
        if n < 0 or n > max_size:
            self._json(413, {'error': f'Размер запроса не должен превышать {max_size // 1024} КБ'})
            return None
        return self.rfile.read(n)

    def _read_json(self):
        if self.headers.get('Content-Type', '').split(';', 1)[0].strip().lower() != 'application/json':
            self._json(415, {'error': 'Ожидается application/json'})
            return None
        body = self._read_body(MAX_JSON_BYTES)
        if body is None:
            return None
        try:
            parsed = json.loads(body)
            if not isinstance(parsed, dict):
                raise ValueError('Expected JSON object')
            return parsed
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
            self._json(400, {'error': 'Некорректный JSON'})
            return None

    def _photo_crop(self):
        path = urlparse(self.path).path
        prefix = '/api/admin/photos/'
        crop = path[len(prefix):]
        if not path.startswith(prefix) or crop not in CROP_IDS:
            self._json(404, {'error': 'Культура не найдена'})
            return None
        return crop

    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        if path.startswith('/api/'):
            if not api_allow(self.client_address[0]):
                return self._json(429, {'error_code':'RATE_LIMIT','error':'Too many API requests'})
            if path == '/api/photos':
                return self._json(200, {'photos': {} if CLOUD else photo_manifest()})
            if path == '/api/admin/status':
                _, session = self._session() if not CLOUD else (None,None)
                result = {'configured': has_admin() if not CLOUD else False, 'authenticated': bool(session), 'disabled':CLOUD}
                if session:
                    result['csrf'] = session['csrf']
                return self._json(200, result)
            if path == '/api/community/photos':
                if CLOUD:return self._json(200, {'crop':'', 'photos':[], 'read_only':True})
                crop = parse_qs(urlparse(self.path).query).get('crop', [''])[0]
                try:
                    return self._json(200, {'crop': crop, 'photos': gallery(crop)})
                except ValueError as e:
                    return self._json(400, {'error': str(e)})
            if path.startswith('/api/science/'):
                q=parse_qs(urlparse(self.path).query)
                site=q.get('site',['USA-NE-SCAL'])[0];crop=q.get('crop',['corn'])[0]
                if path=='/api/science/sites':return self._json(200,science.SITES)
                if site not in science.SITES or crop not in CROP_IDS:return self._json(400,{'error':'invalid_selection'})
                try:
                    if path=='/api/science/evidence':result=science.bundle(site,crop)
                    elif path=='/api/science/twin':result=science.twin(site)
                    elif path=='/api/science/modis':
                        result=science.get_modis(site).copy();result.pop('raw',None)
                    else:return self._json(404,{'error':'not_found'})
                    return self._json(200,result)
                except (OSError,ValueError,KeyError,TypeError) as ex:
                    return self._json(503,{'status':'unavailable','error':'source_unavailable'})
            if path=='/api/agro/weather':
                try:
                    args=parse_qs(urlparse(self.path).query,keep_blank_values=True)
                    lat,lon,start,end=parse_power_request(args)
                    return self._json(200,get_agro_weather(lat,lon,start,end,fetch_json))
                except ValueError as ex:return self._json(400,{'error':str(ex)[:220]})
                except (HTTPError,URLError,TimeoutError,RuntimeError,OSError,KeyError,TypeError):
                    return self._json(503,{'status':'unavailable','error':'NASA POWER unavailable'})
            routes = {
                '/api/health': lambda: {'ok': True, 'version': VERSION, 'mode': MODE, 'cache_entries':len(CACHE), 'snapshot_available':[n for n in ('power','forecast','soil','season','modis') if read_snapshot(n)]},
                '/api/sites': lambda: {'sites': [SITE]},
                '/api/data/power': lambda: cached('power', 24*3600, power_summary),
                '/api/data/forecast': lambda: cached('forecast', 20*60, forecast_summary),
                '/api/data/soil': lambda: cached('soil', 7*24*3600, soil_summary),
                '/api/data/season': lambda: cached('season', 24*3600, season_summary),
                '/api/data/modis': lambda: cached('modis', 48*3600, modis_summary),
                '/api/data/twin': lambda: cached('twin', 14*24*3600, twin_summary)
            }
            if path not in routes:
                return self._json(404, {'error': 'Not found'})
            try:
                return self._json(200, routes[path]())
            except (HTTPError, URLError, TimeoutError, RuntimeError, ValueError, KeyError, TypeError) as e:
                if path=='/api/data/power':
                    historic=science.bundle('USA-NE-SCAL','corn')
                    if historic.get('status')=='available':
                        months=[]
                        for x in historic['monthly']['last_complete_year']:
                            months.append({**x,**{key+'_days':None for key in POWER_PARAMS}})
                        prov=historic['provenance']
                        return self._json(200,{'source':'NASA POWER','source_url':historic['sources'][0],
                            'reference_year':historic['metrics']['year'],'retrieved_at':prov['retrieved_at'],
                            'delivery':prov['delivery'],'snapshot':prov['delivery']=='snapshot','months':months,
                            'resolution_note':prov['resolution']+'; grid estimate, not field measurement',
                            'units':{'T2M':'°C','PRECTOTCORR':'mm/month','ALLSKY_SFC_SW_DWN':'kWh/m²/day','WS2M':'m/s'}})
                snap=read_snapshot(path.rsplit('/',1)[-1])
                if snap:return self._json(200,snap)
                return self._json(503, {'error': 'Data source is temporarily unavailable',
                                        'source': path.rsplit('/', 1)[-1], 'detail': str(e)[:180]})
        if CLOUD and path.startswith('/uploads/'):
            return self.send_error(404,'Uploads are disabled in cloud demo')
        if path.startswith('/uploads/crops/'):
            parts = path.split('/')
            if len(parts) != 5 or parts[3] not in CROP_IDS:
                return self.send_error(404, 'Not found')
            entry = photo_manifest().get(parts[3])
            if not entry or entry['url'] != path:
                return self.send_error(404, 'Not found')
            dest = (UPLOAD_DIR / parts[3] / parts[4]).resolve()
            if not dest.is_relative_to(UPLOAD_DIR) or not dest.is_file():
                return self.send_error(404, 'Not found')
            return self._static_response(dest, cache='public, max-age=86400, immutable')
        if path.startswith('/uploads/community/'):
            parts = path.split('/')
            if len(parts) != 5:
                return self.send_error(404, 'Not found')
            target = photo_path(parts[3], parts[4])
            if target is None:
                return self.send_error(404, 'Not found')
            return self._static_response(target, cache='private, max-age=86400, immutable')
        if path in ('', '/'):
            path = '/index.html'
        # Never expose admin hashes, upload metadata, Python code or private test files.
        allowed_root = {'index.html', 'styles.css', 'map.css', 'favicon.ico'}
        pieces = Path(path.lstrip('/')).parts
        if not (len(pieces) == 1 and pieces[0] in allowed_root or
                len(pieces) >= 2 and pieces[0] in ('assets', 'js', 'tools', 'docs')):
            return self.send_error(404, 'Not found')
        dest = (ROOT / path.lstrip('/')).resolve()
        if (not dest.is_relative_to(ROOT) or
                (len(pieces) >= 2 and not dest.is_relative_to(ROOT / pieces[0])) or
                dest.suffix.lower() not in
                {'.html', '.css', '.js', '.png', '.jpg', '.jpeg', '.svg', '.webp', '.ico', '.json', '.md'} or
                not dest.is_file()):
            return self.send_error(404, 'Not found')
        return self._static_response(dest)

    def _static_response(self, path, cache=None):
        data = path.read_bytes()
        ct = mimetypes.guess_type(str(path))[0] or 'application/octet-stream'
        self.send_response(200)
        if ct == 'image/svg+xml':
            self.send_header('Content-Security-Policy', "default-src 'none'; style-src 'unsafe-inline'; sandbox")
        self.send_header('Content-Type', ct + ('; charset=utf-8' if ct.startswith('text/') or ct in ('application/javascript', 'application/json') else ''))
        self.send_header('Content-Length', str(len(data)))
        self._security_headers()
        if cache:
            self.send_header('Cache-Control', cache)
        self.end_headers()
        self.wfile.write(data)

    def do_HEAD(self):
        path=urlparse(self.path).path
        if path in ('/','/index.html','/api/health'):
            self.send_response(200)
            self.send_header('Content-Type','application/json' if path=='/api/health' else 'text/html; charset=utf-8')
            self._security_headers()
            self.end_headers()
        else:
            self.send_error(404,'Not found')

    def do_POST(self):
        path = urlparse(self.path).path
        if CLOUD and (path.startswith('/api/admin/') or path.startswith('/api/community/')):
            return self._json(403, {'error_code':'CLOUD_READ_ONLY','error':'Uploads and admin disabled in cloud demo'})
        if path in ('/api/agro/balance','/api/agro/advice'):
            if not api_allow(self.client_address[0]):return self._json(429,{'error':'RATE_LIMIT'})
            origin=self.headers.get('Origin','')
            if origin and (urlparse(origin).netloc.lower()!=self.headers.get('Host','').lower() or urlparse(origin).scheme not in ('http','https')):
                return self._json(403,{'error':'INVALID_ORIGIN'})
            data=self._read_json()
            if data is None:return
            try:
                balance=calculate_balance(data.get('balance'))
                if path=='/api/agro/balance':return self._json(200,balance)
                return self._json(200,{'balance':balance,'weather_used':False,**agro_ai.explain(balance,None)})
            except (ValueError,TypeError,OverflowError) as ex:
                return self._json(400,{'error':str(ex)[:220]})
        if path == '/api/assistant/summary':
            if not api_allow(self.client_address[0]):return self._json(429,{'error_code':'RATE_LIMIT'})
            data=self._read_json()
            if data is None:return
            if data.get('site_id') != SITE['id'] or data.get('crop') not in CROP_IDS:
                return self._json(400,{'error_code':'INVALID_SITE_OR_CROP'})
            evidence={'site_id':SITE['id'],'crop':data['crop'],'season':None,'source_status':'not-loaded'}
            try:
                with LOCK:
                    row=CACHE.get('season')
                clim=row[1] if row and time.monotonic()-row[0]<24*3600 else read_snapshot('season')
                if clim:
                    evidence['season']=clim.get('indicators');evidence['source_status']='offline-snapshot' if clim.get('snapshot') else 'cached-live';evidence['source_url']=clim.get('source_url')
            except Exception:
                pass
            result=template_summary(evidence,data.get('lang','en'))
            result['ai_used']=False
            return self._json(200,result)
        if path == '/api/admin/login':
            if not CLOUD and not has_admin():
                return self._json(409, {'error': 'Сначала выполните: py -3 setup_admin.py'})
            if not _check_login_limit(self.client_address[0]):
                return self._json(429, {'error': 'Слишком много попыток. Повторите через 15 минут.'})
            data = self._read_json()
            if data is None:
                return
            password = data.get('password')
            if not isinstance(password, str) or not check_admin_password(password):
                _record_bad_login(self.client_address[0])
                return self._json(401, {'error': 'Неверный пароль'})
            token = secrets.token_urlsafe(32)
            csrf = secrets.token_urlsafe(32)
            with LOCK:
                LOGIN_FAILS.pop(self.client_address[0], None)
                SESSIONS[token] = {'until': time.monotonic() + SESSION_TTL, 'csrf': csrf,
                                   'admin_revision': admin_revision()}
            return self._json(200, {'authenticated': True, 'csrf': csrf},
                              cookie=self._session_cookie(token))
        if path == '/api/admin/logout':
            if not self._require_admin():
                return
            token, _ = self._session()
            with LOCK:
                SESSIONS.pop(token, None)
            return self._json(200, {'ok': True}, cookie=self._session_cookie('', expire=True))
        prefix = '/api/community/photos/'
        if not path.startswith(prefix):
            return self._json(405, {'error': 'Scientific datasets are read-only'})
        crop = path[len(prefix):]
        if crop not in CROP_IDS:
            return self._json(404, {'error': 'Unknown crop'})
        # Browser preflight cannot send uploads from unrelated origins.
        origin = self.headers.get('Origin')
        if origin and (urlparse(origin).netloc.lower() != self.headers.get('Host','').lower()
                       or urlparse(origin).scheme not in ('http', 'https')):
            return self._json(403, {'error': 'Cross-origin uploads are blocked'})
        if self.headers.get('Sec-Fetch-Site', '').lower() == 'cross-site':
            return self._json(403, {'error': 'Cross-site uploads are blocked'})
        if self.headers.get('X-AAIAP-Photo-Upload') != '1':
            return self._json(403, {'error': 'Missing upload acknowledgement'})
        mime = self.headers.get('Content-Type', '').split(';')[0].strip().lower()
        if mime not in ('image/jpeg', 'image/png', 'image/webp'):
            return self._json(415, {'error': 'JPG, PNG or WebP only'})
        if not allow_upload(self.client_address[0]):
            return self._json(429, {'error': 'Too many uploads; try again later'})
        body = self._read_body(MAX_IMAGE_BYTES)
        if body is None:
            return
        try:
            photo = append_photo(crop, body)
            record_upload(self.client_address[0])
            return self._json(201, {'ok': True, 'photo': photo})
        except ValueError as e:
            return self._json(400, {'error': str(e)})
        except OSError:
            return self._json(500, {'error': 'Could not save image to laptop storage'})

    def do_PUT(self):
        if CLOUD:return self._json(403,{'error_code':'CLOUD_READ_ONLY'})
        crop = self._photo_crop()
        if crop is None or not self._require_admin():
            return
        media_type = self.headers.get('Content-Type', '').split(';', 1)[0].strip().lower()
        if media_type not in ('image/jpeg', 'image/png', 'image/webp'):
            return self._json(415, {'error': 'Можно загрузить только JPG, PNG или WebP'})
        body = self._read_body(MAX_IMAGE_BYTES)
        if body is None:
            return
        try:
            result = update_crop_photo(crop, body)
            return self._json(200, {'ok': True, 'crop': crop, 'photo': result})
        except ValueError as e:
            return self._json(400, {'error': str(e)})
        except OSError:
            return self._json(500, {'error': 'Не удалось сохранить фотографию на сервере'})

    def do_PATCH(self):
        if CLOUD:return self._json(403,{'error_code':'CLOUD_READ_ONLY'})
        crop = self._photo_crop()
        if crop is None or not self._require_admin():
            return
        data = self._read_json()
        if data is None:
            return
        try:
            x, y = data.get('focus_x'), data.get('focus_y')
            if type(x) is not int or type(y) is not int:
                raise ValueError('Положение изображения должно быть целым числом')
            result = focus_crop_photo(crop, x, y)
            return self._json(200, {'ok': True, 'photo': result})
        except ValueError as e:
            return self._json(400, {'error': str(e)})

    def do_DELETE(self):
        if CLOUD:return self._json(403,{'error_code':'CLOUD_READ_ONLY'})
        crop = self._photo_crop()
        if crop is None or not self._require_admin():
            return
        try:
            reset_crop_photo(crop)
            return self._json(200, {'ok': True})
        except OSError:
            return self._json(500, {'error': 'Не удалось удалить изображение'})

    def do_OPTIONS(self):
        return self._json(405, {'error': 'Cross-origin requests are not permitted'})

if __name__ == '__main__':
    print(f'AAIAP {VERSION} · mode {MODE} · http://{HOST}:{PORT}')
    print('Cloud-demo: photo uploads/admin disabled' if CLOUD else 'Local mode: crop community uploads available')
    if not CLOUD and not has_admin():
        print('Редактор главных фотографий не настроен: py -3 setup_admin.py (не обязательно для фермеров)')
    print('Development only; never expose this Python HTTP server directly to the Internet.')
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
