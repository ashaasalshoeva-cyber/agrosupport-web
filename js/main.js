import {sites} from './sites.js';
import {initMapFallback} from './map-fallback.js';
import {createExperience} from './experience.js';
import {loadWorld,loadTajikRegions} from './geography.js';
import {createFieldLayer} from './fields.js';
import {t,tt,onLang} from './i18n.js';
import {siteName,siteRegion,siteCrop,siteSoil,siteArea,siteMoist,siteNdvi,sitePh,siteTemp} from './site-format.js';
import './shell.js';
const $=id=>document.getElementById(id);
if(typeof L==='undefined'){initMapFallback()}else{initMap()}
function initMap(){
const map=L.map('map',{zoomControl:false,worldCopyJump:true,minZoom:2,maxZoom:15}).setView([24,20],2);
L.control.zoom({position:'topright'}).addTo(map);
const base=L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap contributors'}).addTo(map);
let osmErrors=0;
base.on('tileerror',()=>{if(++osmErrors===4){const h=$('mapHint');if(h)h.textContent='Basemap tiles unavailable / Нет картографических тайлов / Қабатҳои харита дастнорасанд. Use map markers and catalog.'}});
window.addEventListener('aaiap-map-shown',()=>setTimeout(()=>map.invalidateSize({pan:false}),120));
// Satellite layer is optional. Esri imagery is a third-party service and may be unavailable.
const satellite=L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{maxZoom:18,attribution:'Imagery © Esri and providers'});
let satelliteOn=false,worldLayer=null,regionLayer=null,activeSite=null;
const tajikBounds=L.latLngBounds([36.5,67.2],[41.2,75.2]);
// Texts that must follow the language are stored as {key,params} and re-rendered on change.
const msg={hint:{key:'map.hint0'},boundary:{key:'lg.loading'},contour:{key:'lg.note'}};
const paintMsg=()=>{$('mapHint').textContent=tt(msg.hint.key,msg.hint.params);$('boundaryStatus').textContent=tt(msg.boundary.key,msg.boundary.params);$('contourStatus').textContent=tt(msg.contour.key,msg.contour.params)};
const hint=(key,params)=>{msg.hint={key,params};$('mapHint').textContent=tt(key,params)};
const status=(key,params)=>{msg.boundary={key,params};$('boundaryStatus').textContent=tt(key,params)};
let experience=null;
function closePanels(){for(const id of ['leftPanel','rightPanel']){$(id).classList.remove('open');$(id).setAttribute('aria-hidden','true')}activeSite=null}
function tajikView(){closePanels();map.flyToBounds(tajikBounds,{padding:[65,65],duration:1.3});hint('map.hintTj')}
function worldView(){closePanels();map.flyTo([24,20],2,{duration:1.2});hint('map.hintWorld')}
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function metric(label,value){return `<div class="metric"><span>${label}</span><strong>${esc(value)}</strong></div>`}
function fillSite(s){$('fieldTitle').textContent=siteName(s);$('fieldSubtitle').textContent=`${s.id} · ${siteRegion(s)}`;$('fieldContent').innerHTML=`<div class="section-title">${t('pn.site')}</div>${metric(t('m.id'),s.id)}${metric(t('m.area'),siteArea(s))}${metric(t('m.crop'),siteCrop(s))}${metric(t('m.soil'),siteSoil(s))}<div class="section-title">${t('s.water')}</div>${metric(t('m.moist'),siteMoist(s))}${metric(t('m.temp'),siteTemp(s))}<div class="section-title">${t('s.fert')}</div>${metric(t('m.ph'),sitePh(s))}${metric(t('m.npk'),tt('m.none'))}${metric(t('m.ecc'),tt('m.none'))}<div class="section-title">${t('s.veg')}</div>${metric('NDVI',siteNdvi(s))}${metric('EVI',tt('m.none'))}<div class="section-title">${t('s.prov')}</div>${metric(t('m.src'),tt('m.srcV'))}${metric(t('m.geom'),fieldLayer.getProvenance(s.id))}${metric(t('m.date'),tt('m.dateV'))}${metric(t('m.rel'),tt('m.relV'))}`}
function selectSite(s){if(experience){experience.openDetail(s);return;}activeSite=s;fillSite(s);for(const id of ['leftPanel','rightPanel']){$(id).classList.add('open');$(id).setAttribute('aria-hidden','false')}hint('map.hintSite',{id:s.id});if(window.innerWidth>700)map.panTo([s.lat,s.lon],{animate:true})}
const soilIcon=()=>L.divIcon({className:'',html:`<div class="soil-pin"><div class="soil-top"></div><div class="soil-front"></div><div class="soil-side"></div><div class="soil-label">${esc(tt('tip.field').toUpperCase())}</div></div>`,iconSize:[56,62],iconAnchor:[28,47]});
const markers=L.layerGroup().addTo(map);
const fieldLayer=createFieldLayer(map,sites,selectSite,s=>experience?.schedulePreview(s),()=>experience?.cancelPreview());
experience=createExperience({map,sites,closePanels,getProvenance:(id)=>fieldLayer.getProvenance(id)});
let contoursEnabled=true;
function buildMarkers(){markers.clearLayers();for(const s of sites){L.marker([s.lat,s.lon],{icon:soilIcon(),title:siteName(s)}).addTo(markers).bindTooltip(tt('tip.demo',{name:siteName(s)})).on('click',()=>selectSite(s)).on('mouseover',()=>experience?.schedulePreview(s)).on('mouseout',()=>experience?.cancelPreview())}}
buildMarkers();
// Sites are only visible at country / regional zoom, not on initial world view.
function updateSiteVisibility(){const visible=map.getZoom()>=6; if(visible){if(!map.hasLayer(markers))map.addLayer(markers)}else if(map.hasLayer(markers))map.removeLayer(markers);if(visible&&contoursEnabled){if(!map.hasLayer(fieldLayer.layer))map.addLayer(fieldLayer.layer);fieldLayer.layer.bringToBack()}else if(map.hasLayer(fieldLayer.layer))map.removeLayer(fieldLayer.layer)}
map.on('zoomend',updateSiteVisibility);updateSiteVisibility();
const paintContoursBtn=()=>{const el=$('contoursLabel');el.dataset.i18n=contoursEnabled?'map.cOn':'map.cOff';el.innerHTML=t(el.dataset.i18n);$('contoursBtn').setAttribute('aria-pressed',String(contoursEnabled))};
$('contoursBtn').addEventListener('click',()=>{contoursEnabled=!contoursEnabled;paintContoursBtn();updateSiteVisibility()});
$('geojsonInput').addEventListener('change',async event=>{const file=event.target.files?.[0];if(!file)return;try{if(file.size>5_000_000)throw new Error(tt('imp.big'));const json=JSON.parse(await file.text());const n=fieldLayer.importGeoJSON(json);msg.contour={key:'imp.ok',params:{n}};updateSiteVisibility();if(activeSite)fillSite(activeSite)}catch(error){msg.contour={key:'imp.err',params:{m:error.message}};console.warn(error)}finally{paintMsg();event.target.value=''}});
$('worldBtn').addEventListener('click',worldView);$('nebraskaBtn').addEventListener('click',()=>{closePanels();map.flyTo([40.575256,-98.137824],11,{duration:1.2})});$('tajikBtn').addEventListener('click',tajikView);
// NASA GIBS MODIS Terra true-color: external NASA WMTS; not a numerical NDVI observation.
// Source and date are explicitly exposed; availability checked via tile events.
let gibsLayer=null;
$('gibsBtn')?.addEventListener('click',()=>{
 const btn=$('gibsBtn'); if(gibsLayer){map.removeLayer(gibsLayer);gibsLayer=null;btn.setAttribute('aria-pressed','false');hint('map.hintWorld');return}
 const date='2025-07-15'; // historical date; check NASA GIBS GetCapabilities online before relying on it.
 const url=`https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/${date}/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg`;
 gibsLayer=L.tileLayer(url,{maxNativeZoom:9,maxZoom:16,opacity:0.82,
    attribution:'NASA GIBS / MODIS Terra · 2025-07-15 · satellite true-color (not field NDVI)'});
 let errors=0;
 gibsLayer.on('tileerror',()=>{if(++errors===3){btn.title='NASA tiles unavailable; turn off GIBS';btn.classList.add('source-error');}});
 gibsLayer.addTo(map);btn.setAttribute('aria-pressed','true');btn.title='NASA GIBS MODIS Terra · 2025-07-15 · true color (not NDVI)';
 if(worldLayer)worldLayer.bringToFront();if(map.hasLayer(markers))markers.bringToFront?.();
});
$('layersBtn').addEventListener('click',()=>{if(satelliteOn){map.removeLayer(satellite);base.addTo(map)}else{map.removeLayer(base);satellite.addTo(map)}satelliteOn=!satelliteOn;$('map').classList.toggle('is-satellite',satelliteOn);if(worldLayer)worldLayer.bringToFront();if(regionLayer)regionLayer.bringToFront();if(map.hasLayer(markers))markers.bringToFront?.()});
document.querySelectorAll('[data-close]').forEach(btn=>btn.addEventListener('click',closePanels));
loadWorld(map,(feature,layer)=>{const p=feature.properties||{};const name=p.name||p.ADMIN||'';if(/tajikistan/i.test(name)){tajikView()}else{closePanels();map.flyToBounds(layer.getBounds(),{padding:[45,45],maxZoom:6,duration:1.2});hint('map.hintCountry',{name})}}).then(layer=>{worldLayer=layer;status('lg.ok1')}).catch(err=>{status('lg.fail1');console.warn('World boundaries:',err)});
loadTajikRegions(map,(name,layer)=>{closePanels();map.flyToBounds(layer.getBounds(),{padding:[55,55],maxZoom:9,duration:1.2});hint('map.hintRegion',{name})}).then(layer=>{regionLayer=layer;status('lg.ok2')}).catch(err=>{status('lg.fail2');console.warn('Tajik regions:',err)});
// Re-render everything that was written in JS when the language changes.
onLang(()=>{paintMsg();paintContoursBtn();buildMarkers();fieldLayer.refresh();updateSiteVisibility();if(activeSite)fillSite(activeSite)});

}
