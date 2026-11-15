import {t,tt,fmt,onLang} from './i18n.js';
import {icon} from './icons.js';
import {sitePhotos,photoFallback} from './sites.js';
import {siteName,siteRegion,siteCrop,siteSoil,siteArea,siteCountry} from './site-format.js';
const $=id=>document.getElementById(id);
const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const stages=[1,2,3,4,5].map(i=>[`st${i}.t`,`st${i}.d`]);
const pad=n=>String(n).padStart(2,'0');
export function createExperience({map,sites,closePanels,getProvenance}){
 let timer=null,preview=null,current=null,previousHash='';
 const page=$('fieldPage');
 // Specialist mode is intentionally unavailable in v0.5; the old role gate stays hidden.
 $('roleGate').hidden=true;
 const photoOf=s=>(sitePhotos[s.crop]||[photoFallback]);
 function previewMarkup(s){return `<div class="section-title">${t('preview.h')}</div><div class="metric"><span>${t('m.region')}</span><strong>${escape(siteRegion(s))}</strong></div><div class="metric"><span>${t('m.cropEx')}</span><strong>${escape(siteCrop(s))}</strong></div><div class="metric"><span>${t('m.area')}</span><strong>${escape(siteArea(s))}</strong></div><div class="metric"><span>${t('m.contour')}</span><strong>${escape(getProvenance(s.id))}</strong></div><div class="demo-alert">${t('preview.demo')}</div><button class="primary-btn preview-open" id="previewOpen">${t('preview.more')} ${icon('arrowRight',16)}</button>`}
 function renderPreview(s){if(!page.hidden)return;preview=s;closePanels();$('fieldTitle').textContent=siteName(s);$('fieldSubtitle').textContent=siteRegion(s);$('fieldContent').innerHTML=previewMarkup(s);$('photoPreviewContent').innerHTML=`<img class="preview-photo" src="${photoOf(s)[0]}" alt="${escape(tt('photo.alt'))}"><p><strong>${t('preview.photoP')}</strong></p><p>${t('preview.photoN')}</p><button class="primary-btn" id="photoOpen">${t('preview.card')} ${icon('arrowRight',16)}</button>`;['leftPanel','rightPanel'].forEach(id=>{$(id).classList.add('open');$(id).setAttribute('aria-hidden','false')});$('previewOpen').onclick=()=>openDetail(s);$('photoOpen').onclick=()=>openDetail(s)}
 function schedulePreview(s){clearTimeout(timer);if(!page.hidden)return;timer=setTimeout(()=>renderPreview(s),650)}
 function cancelPreview(){clearTimeout(timer);timer=null}
 const fieldTabs=['overview','plants','guide','tech','science'];
 let activeTab='overview';
 const metric=(a,b)=>`<div class="metric"><span>${a}</span><strong>${b}</strong></div>`;
 function tabContent(s){switch(activeTab){case 'plants':return `<h2>${t('fd.plantsH')}</h2><p>${t('fd.plants1',{crop:siteCrop(s)})}</p><p>${t('fd.plants2')}</p>`;
 case 'guide':return `<h2>${t('fd.guideH',{crop:siteCrop(s)})}</h2><p class="notice">${icon('info',18)}<span>${t('fd.guideN')}</span></p><div class="steps">${stages.map((a,i)=>`<article class="step"><span class="num" aria-hidden="true">${pad(i+1)}</span><div><strong>${t(a[0])}</strong><p>${t(a[1])}</p></div></article>`).join('')}</div>`;
 case 'tech':return `<h2>${t('fd.techH')}</h2><div class="topic-grid">${[1,2,3].map(i=>`<article><h3>${t('tc'+i+'.t')}</h3><p>${t('tc'+i+'.d')}</p></article>`).join('')}</div><p class="notice">${icon('info',18)}<span>${t('fd.techN')}</span></p>`;
 case 'science':return `<h2>${t('fd.sciH')}</h2>${metric(t('m.geom'),escape(getProvenance(s.id)))}${metric(t('fd.soilLab'),t('m.none'))}${metric(t('fd.ndvi'),t('fd.noVerified'))}${metric(t('fd.nasa'),t('fd.notConn'))}${metric(t('fd.coords'),`${fmt(s.lat,3,3)}, ${fmt(s.lon,3,3)}`)}<p class="notice">${icon('info',18)}<span>${t('fd.sciN')}</span></p>`;
 default:return `<h2>${t('fd.aboutH')}</h2><p>${t('fd.about1',{region:siteRegion(s)})}</p><div class="topic-grid"><article><span>${t('m.crop')}</span><h3>${escape(siteCrop(s))}</h3></article><article><span>${t('m.area')}</span><h3>${escape(siteArea(s))}</h3><small>${t('fd.areaNote')}</small></article><article><span>${t('fd.data')}</span><h3>${t('fd.demoData')}</h3></article></div><p>${t('fd.about2')}</p>`}}
 function renderDetail(s){current=s;const imgs=photoOf(s);page.innerHTML=`<div class="detail-shell"><div class="detail-top"><button id="backToMap" class="back-btn" type="button">${icon('arrowLeft',16)} ${t('fd.back')}</button><span class="detail-brand">AgroSupport <em>${t('role.farmer').toUpperCase()}</em></span></div><div class="detail-hero"><img src="${imgs[0]}" alt="${escape(tt('fd.photoAlt'))}"><div class="hero-overlay"><span>${t('fd.hero')}</span><h1>${escape(siteName(s))}</h1><p>${escape(siteRegion(s))}</p></div></div><p class="photo-credit">${t('fd.credit')}</p><div class="detail-layout"><div class="detail-main"><nav class="field-tabs" aria-label="${escape(tt('fd.tabs'))}">${fieldTabs.map(id=>`<button data-tab="${id}" type="button" class="${activeTab===id?'active':''}">${t('ft.'+id)}</button>`).join('')}</nav><section class="detail-section">${tabContent(s)}</section></div><aside class="detail-aside"><h3>${t('fd.passport')}</h3>${metric('ID',escape(s.id))}${metric(t('m.country'),escape(siteCountry(s)))}${metric(t('m.crop'),escape(siteCrop(s)))}${metric(t('m.soil'),escape(siteSoil(s)))}${metric(t('m.status'),t('fd.demoV'))}</aside></div></div>`;page.querySelector('#backToMap').onclick=()=>{history.pushState({},'',previousHash||location.pathname+location.search);hideDetail()};page.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>{activeTab=b.dataset.tab;renderDetail(s)});}
 function openDetail(s){cancelPreview();closePanels();previousHash=location.pathname+location.search+location.hash;activeTab='overview';page.hidden=false;map.getContainer().setAttribute('aria-hidden','true');renderDetail(s);history.pushState({site:s.id},'',`#field=${encodeURIComponent(s.id)}`);page.scrollTop=0}
 function hideDetail(){page.hidden=true;current=null;map.getContainer().removeAttribute('aria-hidden');map.invalidateSize()}
 window.addEventListener('popstate',()=>{const id=decodeURIComponent(location.hash.match(/^#field=(.*)$/)?.[1]||'');const s=sites.find(x=>x.id===id);if(s){page.hidden=false;current=s;renderDetail(s)}else hideDetail()});
 const startId=decodeURIComponent(location.hash.match(/^#field=(.*)$/)?.[1]||'');const startSite=sites.find(x=>x.id===startId);if(startSite){page.hidden=false;renderDetail(startSite)}
 onLang(()=>{if(current&&!page.hidden)renderDetail(current)});
 return {schedulePreview,cancelPreview,openDetail};
}
