/** NASA POWER direct browser client for static/GitHub Pages. No credentials, no fake data. */
const ENDPOINT='https://power.larc.nasa.gov/api/temporal/daily/point';
const KEYS=['T2M','T2M_MAX','T2M_MIN','RH2M','PRECTOTCORR','WS2M','ALLSKY_SFC_SW_DWN'];
const DAY=86400000;
const memo=new Map();
const round=(x,d=2)=>Number(x.toFixed(d));
const fmtDate=(ms)=>new Date(ms).toISOString().slice(0,10);
function validate(query){
 const lat=Number(query.lat),lon=Number(query.lon),start=query.start,end=query.end;
 if(query.lat===''||query.lon===''||!Number.isFinite(lat)||!Number.isFinite(lon)||lat < -90||lat>90||lon < -180||lon>180)throw Error('Координаты вне диапазона: широта −90…90, долгота −180…180.');
 if(!/^\d{4}-\d\d-\d\d$/.test(start)||!/^\d{4}-\d\d-\d\d$/.test(end))throw Error('Выберите даты начала и конца периода.');
 const t0=Date.parse(start+'T00:00:00Z'),t1=Date.parse(end+'T00:00:00Z');
 if(!Number.isFinite(t0)||!Number.isFinite(t1)||fmtDate(t0)!==start||fmtDate(t1)!==end)throw Error('Некорректные даты.');
 const latest=Date.now()-7*DAY;
 if(t0<Date.UTC(1981,0,1)||t1<t0||t1-t0>365*DAY||t1>latest)throw Error('NASA POWER: завершённый период с 1981 года, до 366 дней, без последних 7 суток.');
 return {lat:round(lat,4),lon:round(lon,4),start,end,t0,t1};
}
function makeURL(q){const p=new URLSearchParams({parameters:KEYS.join(','),community:'AG',latitude:String(q.lat),longitude:String(q.lon),start:q.start.replaceAll('-',''),end:q.end.replaceAll('-',''),format:'JSON','time-standard':'LST'});return ENDPOINT+'?'+p;}
function clean(v,k){if(typeof v!=='number'||!Number.isFinite(v)||v<=-990)return null;if(k==='RH2M'&&(v<0||v>100))return null;if(k==='PRECTOTCORR'&&v<0)return null;return v;}
function solarFactor(raw){const u=String(raw?.parameters?.ALLSKY_SFC_SW_DWN?.units||'MJ/m^2/day').toLowerCase().replaceAll(' ','');
 if(u.includes('kw-hr')||u.includes('kwh'))return 1;
 if(u.includes('mj'))return 1/3.6;
 throw Error('NASA POWER вернул неизвестные единицы солнечной радиации: '+u);
}
export function transformPower(raw,query,url){
 const q=validate(query),params=raw?.properties?.parameter;
 if(!params||KEYS.some(k=>!params[k]||typeof params[k]!=='object'||Array.isArray(params[k])))throw Error('NASA POWER: отсутствуют необходимые показатели в ответе.');
 const factor=solarFactor(raw),counts=Object.fromEntries(KEYS.map(k=>[k,0])),monthly=new Map(),daily=[];
 for(let t=q.t0;t<=q.t1;t+=DAY){const d=fmtDate(t),key=d.replaceAll('-',''),month=d.slice(0,7);
  const r={date:d};for(const k of KEYS){let value=clean(params[k][key],k);if(value!=null&&k==='ALLSKY_SFC_SW_DWN')value*=factor;r[k]=value==null?null:round(value,3);if(value!=null)counts[k]++;}
  daily.push(r);if(!monthly.has(month))monthly.set(month,{month,expected_days:0,totals:Object.fromEntries(KEYS.map(k=>[k,0])),counts:Object.fromEntries(KEYS.map(k=>[k,0]))});
  const m=monthly.get(month);m.expected_days++;for(const k of KEYS)if(r[k]!=null){m.totals[k]+=r[k];m.counts[k]++;}}
 if(!counts.T2M||!counts.PRECTOTCORR)throw Error('NASA POWER не вернул достаточно данных о температуре и осадках за указанный период.');
 const rows=[...monthly.values()].map(m=>{const out={month:m.month,expected_days:m.expected_days};for(const k of KEYS){out[k]=m.counts[k]?round(k==='PRECTOTCORR'?m.totals[k]:m.totals[k]/m.counts[k]):null;out[k+'_valid_days']=m.counts[k];}return out;});
 const completeRain=counts.PRECTOTCORR===daily.length;
 return {source:'NASA POWER',source_url:url,retrieved_at:new Date().toISOString(),snapshot:false,data_status:'direct-browser-nasa-power',coordinates:{lat:q.lat,lon:q.lon},period:{start:q.start,end:q.end},time_standard:'LST',units:{T2M:'°C',T2M_MAX:'°C',T2M_MIN:'°C',RH2M:'%',PRECTOTCORR:'mm/day',WS2M:'m/s',ALLSKY_SFC_SW_DWN:'kWh/m²/day'},daily,monthly:rows,valid_days:counts,expected_days:daily.length,totals:{rain_mm:completeRain?round(daily.reduce((acc,row)=>acc+row.PRECTOTCORR,0)):null,temperature_mean_c:round(daily.reduce((acc,row)=>acc+(row.T2M??0),0)/counts.T2M)},limits:'Глобальная сетка NASA POWER, не измерение на поле; последние дни могут быть неполными.'};
}
export async function fetchPower(query){
 const q=validate(query),url=makeURL(q),key=url;
 if(memo.has(key))return memo.get(key);
 const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),60000);
 try{let response;try{response=await fetch(url,{method:'GET',headers:{Accept:'application/json'},signal:controller.signal});}
 catch(e){throw Error(e.name==='AbortError'?'NASA POWER не ответил за 60 секунд. Повторите позже.':'Прямое подключение NASA POWER заблокировано сетью или CORS. Для GitHub Pages нужен доступный серверный API.');}
 if(!response.ok){let message='';try{const err=await response.json();message=err?.messages?.join('; ')||err?.detail||err?.message||'';}catch{}
  throw Error('NASA POWER: HTTP '+response.status+(message?' — '+String(message).slice(0,160):'')+'.');}
 let raw;try{raw=await response.json();}catch{throw Error('NASA POWER вернул ответ не в формате JSON.');}
 const data=transformPower(raw,q,url);if(memo.size>=12)memo.clear();memo.set(key,data);return data;
 }finally{clearTimeout(timeout);}
}
export function monthlyPowerSummary(weather){
 return {source:'NASA POWER',source_url:weather.source_url,retrieved_at:weather.retrieved_at,reference_year:Number(weather.period.start.slice(0,4)),resolution_note:'NASA POWER: сеточные оценки; прямой запрос из браузера по координатам пилотной точки.',units:{T2M:'°C',PRECTOTCORR:'mm',ALLSKY_SFC_SW_DWN:'kWh/m²/day',WS2M:'m/s'},months:weather.monthly.map(m=>{const year=Number(m.month.slice(0,4)),month=Number(m.month.slice(5));return {year,month,T2M:m.T2M,T2M_days:m.T2M_valid_days,PRECTOTCORR:m.PRECTOTCORR,PRECTOTCORR_days:m.PRECTOTCORR_valid_days,ALLSKY_SFC_SW_DWN:m.ALLSKY_SFC_SW_DWN,ALLSKY_SFC_SW_DWN_days:m.ALLSKY_SFC_SW_DWN_valid_days,WS2M:m.WS2M,WS2M_days:m.WS2M_valid_days}})};
}
