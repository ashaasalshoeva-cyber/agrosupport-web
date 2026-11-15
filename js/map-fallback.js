import {sites} from './sites.js';
import {getLang} from './i18n.js';
const labels={en:['Map engine unavailable','The interactive map could not load. You can still explore the research sites.', 'Open Nebraska crops','Tajikistan — regional reference only','Explore NASA data from the crop catalogue'],ru:['Карта временно недоступна','Картографический движок не загрузился. Можно открыть площадки без карты.', 'Открыть растения Небраски','Таджикистан — только региональные точки','Данные NASA доступны в каталоге культур'],tg:['Харита муваққатан дастнорас аст','Муҳаррики харита бор нашуд. Майдонҳоро бе харита низ дидан мумкин аст.','Зироатҳои Небраскаро кушоед','Тоҷикистон — танҳо нуқтаҳои минтақавӣ','Маълумоти NASA дар феҳрист дастрас аст']};
export function initMapFallback(){
 const map=document.getElementById('map'); if(!map)return;
 const lang=getLang(); const words=labels[lang]||labels.en;
 map.classList.add('fallback-map');
 map.innerHTML=`<div class="map-fallback-pane" role="region" aria-label="Fallback research sites">
 <div class="fallback-globe" aria-hidden="true">◉</div><div class="map-fallback-copy">
 <p class="eyebrow">AAIAP GIS · OFFLINE FALLBACK</p><h2>${words[0]}</h2><p>${words[1]}</p>
 <button type="button" id="fallbackNebraska">🇺🇸 ${words[2]}</button>
 <p>🇹🇯 ${words[3]}</p><small>${words[4]}</small>
 <div class="fallback-site-list">${sites.filter(s=>s.id==='USA-NE-SCAL').map(s=>`<span>${s.id} · ${s.lat}, ${s.lon}</span>`).join('')}</div></div></div>`;
 document.getElementById('fallbackNebraska')?.addEventListener('click',()=>{
  document.querySelector('#backToPortal')?.click();
  document.querySelector('[data-nav="catalog"]')?.click();
 });
 document.querySelectorAll('.map-actions button, .map-actions label').forEach(e=>e.disabled=true);
 document.getElementById('boundaryStatus')?.replaceChildren(document.createTextNode(words[0]));
 console.warn('AAIAP GIS: Leaflet unavailable, showing functional catalogue fallback');
}
