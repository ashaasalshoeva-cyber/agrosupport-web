import {demoFieldPolygon} from './sites.js';
import {tt} from './i18n.js';
import {siteName} from './site-format.js';
// Palette-only styling: demo contours are teal/lime dashed, imported contours are solid clay.
const shapeStyle = feature => {const imp=feature.properties?.source_type==='imported';return {className:imp?'geo-field-imp':'geo-field',color:imp?'#7B5B43':'#E0FFC2',weight:2.2,fillColor:imp?'#7B5B43':'#0e4749',fillOpacity:imp?.34:.42,dashArray:imp?null:'6 5'}};
const escapeHTML = s => String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function createFieldLayer(map,sites,onSelect,onHover=()=>{},onLeave=()=>{}){
 const layer=L.geoJSON(null,{style:shapeStyle,onEachFeature(feature,shape){const id=feature.properties?.site_id;const site=sites.find(s=>s.id===id);shape.bindTooltip(`${escapeHTML(site?siteName(site):(id||tt('tip.field')))} · ${feature.properties?.source_type==='imported'?tt('tip.import'):tt('tip.contour')}`,{sticky:true});shape.on('click',()=>{if(site)onSelect(site);else shape.openPopup()});shape.on('mouseover',()=>{if(site)onHover(site)});shape.on('mouseout',()=>onLeave());if(!site)shape.bindPopup(tt('tip.orphan'));}}).addTo(map);
 const demo=sites.filter(s=>!s.referenceOnly).map(demoFieldPolygon);
 const imported=new Map();
 function refresh(){layer.clearLayers();for(const feature of demo){const id=feature.properties.site_id;layer.addData(imported.get(id)||feature)}for(const [id,feature] of imported){if(!sites.some(s=>s.id===id))layer.addData(feature)}}
 refresh();
 function importGeoJSON(raw){
  if(!raw||!['Feature','FeatureCollection'].includes(raw.type))throw new Error(tt('imp.type'));
  const features=raw.type==='Feature'?[raw]:raw.features;
  if(!Array.isArray(features)||features.length>300)throw new Error(tt('imp.count'));
  const accepted=[];
  for(const f of features){
   if(!f||f.type!=='Feature'||!['Polygon','MultiPolygon'].includes(f.geometry?.type))continue;
   const id=String(f.properties?.site_id||f.properties?.id||'').trim();
   if(!id||id.length>100)continue;
   const coords=[];const collect=a=>{if(typeof a?.[0]==='number'){coords.push(a);return}if(Array.isArray(a))a.forEach(collect)};collect(f.geometry.coordinates);
   if(!coords.length||coords.length>10000||coords.some(p=>p.length<2||!Number.isFinite(p[0])||!Number.isFinite(p[1])||Math.abs(p[0])>180||Math.abs(p[1])>90))continue;
   const feature={type:'Feature',geometry:f.geometry,properties:{site_id:id,source_type:'imported',verified:false}};
   // Imported geometry is user-provided, not automatically authenticated.
   accepted.push([id,feature]);
  }
  if(!accepted.length)throw new Error(tt('imp.none'));
  for(const [id,feature] of accepted)imported.set(id,feature);
  refresh();return accepted.length;
 }
 return {layer,refresh,importGeoJSON,getProvenance:id=>imported.has(id)?tt('prov.imp'):sites.find(s=>s.id===id)?.referenceOnly?tt('prov.reference'):tt('prov.demo'),getCount:()=>imported.size};
}
