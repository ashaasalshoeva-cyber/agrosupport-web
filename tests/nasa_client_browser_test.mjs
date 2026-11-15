/** Test browser direct NASA adapter without networking or simulated provenance. */
import assert from 'node:assert/strict';
import {transformPower,monthlyPowerSummary,fetchPower} from '../tools/nasa-client.js';
const raw={properties:{parameter:{}},parameters:{ALLSKY_SFC_SW_DWN:{units:'MJ/m^2/day'}}};
const keys=['T2M','T2M_MAX','T2M_MIN','RH2M','PRECTOTCORR','WS2M','ALLSKY_SFC_SW_DWN'];
for(const k of keys){raw.properties.parameter[k]={};for(let d=1;d<=3;d++)raw.properties.parameter[k]['2025030'+d]=k==='ALLSKY_SFC_SW_DWN'?3.6:k==='PRECTOTCORR'?d:k==='T2M'?10+d:2;}
const req={lat:'38.5598',lon:'68.7870',start:'2025-03-01',end:'2025-03-03'};
const r=transformPower(raw,req,'https://power.larc.nasa.gov/api/temporal/daily/point?example=1');
assert.equal(r.totals.rain_mm,6);assert.equal(r.monthly[0].ALLSKY_SFC_SW_DWN,1);assert.equal(r.totals.temperature_mean_c,12);
assert.equal(monthlyPowerSummary(r).months[0].PRECTOTCORR,6);
raw.properties.parameter.PRECTOTCORR['20250303']=-999;
assert.equal(transformPower(raw,req,'https://power.larc.nasa.gov/').totals.rain_mm,null);
raw.properties.parameter.PRECTOTCORR['20250303']=3;
const fetchLog=[];globalThis.fetch=async url=>{fetchLog.push(url);return {ok:true,json:async()=>raw}};
const w=await fetchPower(req);assert.equal(w.totals.rain_mm,6);assert.match(fetchLog[0],/community=AG/);assert.match(fetchLog[0],/start=20250301/);
await fetchPower(req);assert.equal(fetchLog.length,1,'Repeated requests reuse client cache');
for(const bad of [{...req,lat:'-91'},{...req,end:'2027-03-01'},{...req,start:'2025-04-01'}]){
 assert.throws(()=>transformPower(raw,bad,'https://power.larc.nasa.gov/'));
}
console.log('NASA browser adapter: 8 checks passed');
