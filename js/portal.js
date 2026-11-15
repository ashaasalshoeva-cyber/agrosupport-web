import {cropList,cropName,cropDesc,CATEGORIES,regionalDemos,guideSteps} from './catalog-data.js';
import {sources,supportSources} from './source-registry.js';
import {sites as staticSites} from './sites.js';
import {t,tt,fmt,sortLocale,getLang,pick,onLang} from './i18n.js';
import {icon} from './icons.js';
import './shell.js';
import {setBackground} from './backgrounds.js';
import {cropPhoto,cropDetailPhoto,cropPhotoPosition,refreshCropPhotos} from './photo-admin.js';
import {agroTab} from './agro-insights.js';
import {researchTab,metadataView,handleResearchAction,exportResearchCSV,refreshResearchStatic,switchResearchMetric} from './research-demo.js';

const $=id=>document.getElementById(id);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const MSG={
 title:['Nebraska research sites','Исследовательские площадки Небраски','Майдонҳои таҳқиқотии Небраска'],
 startText:['Public agricultural knowledge. No accounts or field claiming.','Открытая агрономическая информация. Без аккаунтов и закрепления полей.','Маълумоти кушоди кишоварзӣ. Бе ҳисоб ва тасарруфи майдон.'],
 country:['Country','Страна','Кишвар'],region:['Region','Регион','Минтақа'],site:['Research site','Исследовательская площадка','Майдони таҳқиқотӣ'],
 state:['Nebraska, USA','Небраска, США','Небраска, ИМА'],
 location:['South-central Nebraska','Южно-центральная Небраска','Небраскаи марказии ҷанубӣ'],
 open:['Explore crops','Перейти к растениям','Гузаштан ба зироатҳо'],
 public:['Open to everyone','Доступно всем','Барои ҳама дастрас'],
 access:['All sites are publicly viewable. Calculations run locally, without changing official source data.','Все площадки доступны для просмотра. Расчёты выполняются локально и не меняют научные данные.','Ҳамаи майдонҳо барои дидан дастрасанд. Ҳисобҳо маҳаллӣ мебошанд ва маълумоти илмиро тағйир намедиҳанд.'],
 context:['Verified site location, not a mapped field boundary','Подтверждена точка станции, не контур конкретного поля','Ҷойи марказ тасдиқ шудааст, на сарҳади майдон'],
 noArea:['Area of individual fields is not established','Площадь отдельных полей не установлена','Масоҳати майдонҳои алоҳида маълум нест'],
 documented:['Reported research crops','Подтверждённые исследуемые культуры','Зироатҳои таҳқиқшаванда'],
 documentedTag:['Documented at site','Подтверждено на станции','Дар марказ тасдиқ шудааст'],
 unranked:['No verified suitability ranking','Рейтинг пригодности пока не рассчитан','Рейтинги мувофиқат ҳоло ҳисоб нашудааст'],
 best:['Documented crops first (not suitability)','Сначала подтверждённые культуры (не пригодность)','Аввал зироатҳои тасдиқшуда (на мувофиқат)'],
 find:['Search crops','Поиск культур','Ҷустуҷӯи зироатҳо'],
 data:['Site data','Данные местности','Маълумоти маҳал'],
 about:['About plant','О растении','Дар бораи растанӣ'],
 land:['Land','Земля','Замин'],npk:['NPK calculator','Калькулятор NPK','Ҳисобкунаки NPK'],
 irrigation:['Irrigation calculator','Калькулятор орошения','Ҳисобкунаки обёрӣ'],
 weather:['Weather forecast','Прогноз погоды','Пешгӯии ҳаво'], ai:['AAIAP (later)','AAIAP (позже)','AAIAP (баъдтар)'],
 back:['Back to catalogue','Назад к каталогу','Бозгашт ба феҳрист'],
 how:['How to grow','Как выращивать','Чӣ тавр парвариш кардан'],
 local:['Local planning only; not an agronomic recommendation.','Локальный планировщик, не агрономическая рекомендация.','Банақшагирии маҳаллӣ, на тавсияи агрономӣ.'],
 unknown:['Unknown','Неизвестно','Номаълум'],
 fieldArea:['Assumed field area, ha','Планируемая площадь участка, га','Масоҳати тахминии майдон, га'],
 planted:['Already sown, ha','Уже посеяно, га','Аллакай кишт шудааст, га'],
 extra:['Additional sowing, ha','Дополнительный посев, га','Кишти иловагӣ, га'],
 N:['N per ha (kg)','N на гектар (кг)','N ба гектар (кг)'],
 P:['P₂O₅ per ha (kg)','P₂O₅ на гектар (кг)','P₂O₅ ба гектар (кг)'],
 K:['K₂O per ha (kg)','K₂O на гектар (кг)','K₂O ба гектар (кг)'],
 W:['Water per ha (m³)','Вода на гектар (м³)','Об ба гектар (м³)'],
 areaTotal:['Total sowing','Общий посев','Кишти умумӣ'],
 available:['Unallocated','Свободно','Озод'],
 total:['Total demand','Общая потребность','Талаботи умумӣ'],
 extraNeed:['For extension','Для расширения','Барои васеъкунӣ'],
 badArea:['Planned sowing exceeds the assumed land area.','Площадь посевов превышает планируемую площадь участка.','Масоҳати кишт аз масоҳати замин зиёд аст.'],
 notGiven:['Enter rates to calculate. Values are never invented by AAIAP.','Введите нормы самостоятельно. AAIAP не выдумывает значения.','Меъёрҳоро худ ворид кунед. AAIAP рақамҳоро намесозад.'],
 guideNote:['General steps only. Consult current Nebraska Extension guidance for rates and timing.','Только общие этапы. Точные нормы и сроки уточняйте по рекомендациям Nebraska Extension.','Танҳо қадамҳои умумӣ. Меъёр ва муҳлатҳоро аз дастури Nebraska Extension санҷед.'],
 source:['Official source','Официальный источник','Манбаи расмӣ'],
 linked:['Reference link · not connected','Источник · ещё не подключён','Манбаъ · ҳоло пайваст нест'],
 api:['Live request available','Можно запросить реальные данные','Дархости маълумоти воқеӣ дастрас'],
 editorial:['Documented research practice','Подтверждённые сведения станции','Маълумоти тасдиқшудаи марказ'],
 load:['Load official data','Загрузить данные из источника','Маълумотро бор кунед'],
 loading:['Requesting source…','Запрос к источнику…','Дархост ба манбаъ…'],
 error:['Source unavailable. No estimates substituted.','Источник недоступен. Подставлять условные значения не будем.','Манбаъ дастнорас аст. Қиматҳои тахминӣ истифода намешаванд.'],
 period:['Year of data','Год данных','Соли маълумот'],
 gps:['Official site coordinates','Официальные координаты станции','Координатаҳои расмии марказ'],
 unit:['Data type','Тип данных','Навъи маълумот'],
 avgTemp:['Mean temperature','Средняя температура','Ҳарорати миёна'],
 precip:['Monthly rainfall','Осадки по месяцам','Боришот дар моҳ'],
 solar:['Solar radiation','Солнечная радиация','Радиатсияи офтобӣ'],
 wind:['Wind speed','Скорость ветра','Суръати шамол'],
 mapUnit:['Soil map units at the point','Почвенные единицы в точке','Воҳидҳои харитаи хок'],
 noRows:['No map units returned for these coordinates.','Почвенные единицы для точки не найдены.','Воҳидҳои хок ёфт нашуданд.'],
 cropSource:['Research center reports corn and soybean; this is not a crop mask for a particular plot.','Исследовательская станция сообщает о выращивании кукурузы и сои; это не карта культуры конкретного поля.','Марказ ҷуворимакка ва сояро қайд мекунад; ин харитаи майдони муайян нест.'],
 extraSources:['Supporting data sources','Вспомогательные источники','Манбаъҳои иловагӣ'],
 readOnly:['Public read-only scientific catalogue','Общий научный каталог — без редактирования','Феҳристи илмии умумӣ — бе таҳрир'],
 planning:['Only you see these calculation inputs in this browser tab.','Эти расчётные вводные видны только вам в этой вкладке браузера.','Ин рақамҳо танҳо дар ҳамин равзанаи шумо дида мешаванд.'],
 close:['Close','Закрыть','Пӯшидан'],
 empty:['No data have been loaded.','Данные ещё не загружены.','Маълумот ҳоло бор нашудааст.'],
 farmerPhotos:['Farmers’ photos','Фотографии фермеров','Аксҳои деҳқонон'],
 farmerNotice:['Community photos are illustrative and have not been verified as images of this site. Do not upload people or private information.','Фотографии пользователей не проверены и не считаются снимками этой площадки. Не загружайте людей и личные сведения.','Аксҳои корбарон санҷида нашудаанд ва ба ин майдон ҳатман тааллуқ надоранд. Аксҳои одамон ё маълумоти шахсиро нафиристед.'],
 photoAdd:['Add a photo','Добавить фотографию','Илова кардани акс'],
 photoSave:['Upload to laptop server','Сохранить на сервере','Дар сервер нигоҳ доштан'],
 photoNone:['No farmer photos yet. Be the first to add one.','Фотографий фермеров пока нет. Можно добавить первую.','Ҳоло акси деҳқонон нест. Аввалин аксро илова кунед.'],
 photoLabel:['User-submitted · unverified','Загружено пользователем · не проверено','Аз корбар · санҷида нашудааст'],
 photoRule:['JPG, PNG or WebP, up to 5 MB. Stored on the site owner’s laptop.','JPG, PNG или WebP до 5 МБ. Хранится на ноутбуке владельца сайта.','JPG, PNG ё WebP то 5 МБ. Дар ноутбуки соҳиби сайт нигоҳ дошта мешавад.'],
 photoDone:['Photo saved. Everyone using this server can see it.','Фото сохранено. Оно доступно всем посетителям этого сервера.','Акс нигоҳ дошта шуд ва ба ҳама корбарони ин сервер дастрас аст.'],
 photoWait:['Uploading…','Загрузка…','Бор карда истодааст.']
};
const m=k=>MSG[k]?.[['en','ru','tg'].indexOf(getLang())]||MSG[k]?.[0]||k;
const state={view:'welcome',farm:null,sites:[],cropId:'corn',tab:'about',sub:'land',dataTab:'crops',sort:'priority',filter:'all',search:'',draft:{},data:{},busy:{},errors:{},gallery:{},galleryLoading:{}};
const country='USA', region='USA-NE-SC';
const preferred=regionalDemos[region]||[];
const moneyNumber=x=>x===''||x===null||x===undefined?null:(Number.isFinite(+x)&&+x>=0?+x:null);
const planKey=()=>`${state.farm?.id}:${state.cropId}`;
const defaultPlan=()=>({field_ha:null,planted_ha:null,extra_ha:null,n_kg_ha:null,p2o5_kg_ha:null,k2o_kg_ha:null,water_m3_ha:null});
const plans={};
const retrievePlan=()=>({...defaultPlan(),...(plans[planKey()]||{})});
const savePlan=()=>{plans[planKey()]={...state.draft}};
const activeCrop=()=>cropList.find(c=>c.id===state.cropId)||cropList[0];
const fieldName=()=>state.farm?.name||'South Central Agricultural Laboratory';
const iconText=(i,s)=>`${icon(i,18)}<span>${s}</span>`;
const orb=n=>`<span class="num" aria-hidden="true">${String(n).padStart(2,'0')}</span>`;

async function api(path){const response=await fetch('/api'+path,{cache:'no-store',headers:{Accept:'application/json'}});
 const data=await response.json();if(!response.ok)throw Error(data.error||'Source unavailable');return data}
function toast(message){const e=$('toast');e.textContent=message;e.hidden=false;clearTimeout(toast.timer);toast.timer=setTimeout(()=>e.hidden=true,4000)}

async function start(){
 try{const mode=await api('/health');if(mode.mode==='cloud-demo'){document.body.classList.add('cloud-demo')}}catch{}
 try{const info=await api('/sites');state.sites=info.sites||[];state.farm=state.sites[0]||null;}catch(e){state.sites=[{...staticSites.find(x=>x.id==='USA-NE-SCAL'),name:'South Central Agricultural Laboratory (UNL)',documented_crops:['corn','soybean']}];state.farm=state.sites[0];state.errors.sites='Static hosting: server APIs are unavailable';}try{await refreshCropPhotos();}catch(e){console.warn('Main photos unavailable',e);}readHash();render()}
function setView(view){state.view=view;render();$('portal')?.scrollTo({top:0,behavior:'instant'});}
function welcome(){const site=state.farm;
 return `<main class="welcome-layout"><section class="welcome-left"><div class="superlabel"><span class="pulse-dot"></span> ${t('w.label')}</div><div class="welcome-copy"><span class="welcome-count">01 / NEBRASKA PILOT</span><h1>${t('w.h1a')}<br><em>${t('w.h1b')}</em><br>${t('w.h1c')}</h1><p>${m('startText')}</p></div><div class="who-card"><h2>${t('w.who')}</h2><button class="role-active" type="button" aria-pressed="true"><span class="role-symbol">${icon('sprout',22)}</span><span class="role-text"><strong>${t('role.farmer')}</strong><small>${t('role.farmer.d')}</small></span><span class="tiny-check">${icon('check',18)}</span></button><button class="role-locked" disabled type="button"><span class="role-symbol">${icon('flask',22)}</span><span class="role-text"><strong>${t('role.expert')}</strong><small>${t('role.expert.d')}</small></span><span class="soon-tag">${t('soon')}</span></button></div><div class="welcome-bottom">${t('w.bottom')} <span>v0.2.1</span></div></section>
 <section class="welcome-right"><div class="setup-head"><span>${t('setup.label')}</span><strong>${m('title')}</strong><p>${m('access')}</p></div>
 <div class="step-selector">${orb(1)}<div><label>${m('country')}</label><div class="fixed-choice">🇺🇸 United States</div></div></div>
 <div class="step-selector">${orb(2)}<div><label>${m('region')}</label><div class="fixed-choice">${m('state')} · ${m('location')}</div></div></div>
 <div class="step-selector step-farm">${orb(3)}<div><label>${m('site')}</label><div class="farm-options">${site?`<button type="button" data-action="enter" class="farm-option picked"><span class="farm-text"><strong>${esc(site.name)}</strong><small>Clay County · ${m('context')}</small></span><span class="option-arrow">${icon('check',16)}</span></button>`:`<p class="empty-row">${m('error')}</p>`}</div></div></div>
 <div class="setup-footer"><button id="enterCatalog" class="hero-go" type="button" ${!site?'disabled':''}>${m('open')} ${icon('arrowRight',18)}</button><button type="button" data-action="openDemo" class="demo-quicklink">NASA DEMO / 🌽 Corn ↗</button><p>${m('public')} · ${m('readOnly')}</p></div></section></main>`;
}
function locbar(){return `<div class="locbar"><button class="loc-change" data-view="welcome"><span class="loc-back">${icon('arrowLeft',16)}</span>${t('loc.change')}</button><span class="loc-path"><span class="loc-chip"><span class="loc-code">US</span> USA</span><span class="loc-sep"></span><span class="loc-chip current">${icon('pin',16)} Nebraska · Clay Center</span></span></div>`}
function catalog(){return `<main class="content-shell">${locbar()}<section class="catalog-hero"><div class="catalog-headline"><span class="overline">${t('cat.over')}</span><h1>${t('cat.h1a')}<br><em>${t('cat.h1b')}</em></h1><p>${m('unranked')}</p></div><div class="farm-status"><span class="tag-small">UNL / RESEARCH</span><h2>${esc(fieldName())}</h2><p>Harvard, Nebraska · Clay County</p><div class="status-line"><span class="state-dot owned"></span><strong>${m('public')}</strong></div><p class="farm-area">${m('noArea')}</p><small>${m('context')}</small></div></section>
 <section class="catalog-tools"><div class="catalog-title"><div><span class="overline">${t('crops.over')}</span><h2>${t('crops.h')}</h2></div><span id="countLabel" class="count-chip"></span></div><div class="filters"><label class="searchbox">${icon('search',18)}<input id="cropSearch" type="search" placeholder="${esc(m('find'))}" value="${esc(state.search)}"></label><label class="filterbox"><span class="fb-label">${t('filter.cat')}</span><span class="select-wrap"><select id="categoryFilter"><option value="all">${t('filter.all')}</option>${CATEGORIES.map(c=>`<option value="${c}" ${state.filter===c?'selected':''}>${t('cat.'+c)}</option>`).join('')}</select>${icon('chevron',16)}</span></label><label class="filterbox"><span class="fb-label">${t('sort.label')}</span><span class="select-wrap"><select id="sortSelect"><option value="priority">${m('best')}</option><option value="alpha" ${state.sort==='alpha'?'selected':''}>${t('sort.alpha')}</option><option value="category" ${state.sort==='category'?'selected':''}>${t('sort.category')}</option></select>${icon('chevron',16)}</span></label></div><div class="informational-banner">${icon('info',18)} ${m('unranked')}</div><div id="cropGrid" class="crop-grid"></div></section></main>`}
function renderCatalogGrid(){const host=$('cropGrid');if(!host)return;const q=state.search.toLocaleLowerCase(sortLocale());const items=cropList.filter(c=>(state.filter==='all'||c.cat===state.filter)&&(`${Object.values(c.names).join(' ')} ${c.latin}`).toLocaleLowerCase(sortLocale()).includes(q));
 const nm=c=>cropName(c);
 if(state.sort==='priority')items.sort((a,b)=>(preferred.includes(a.id)?preferred.indexOf(a.id):99)-(preferred.includes(b.id)?preferred.indexOf(b.id):99)||nm(a).localeCompare(nm(b)));
 else if(state.sort==='alpha')items.sort((a,b)=>nm(a).localeCompare(nm(b)));
 else items.sort((a,b)=>t('cat.'+a.cat).localeCompare(t('cat.'+b.cat)));
 $('countLabel').innerHTML=`${orb(items.length)}<span>${t('crops.count')}</span>`;
 host.innerHTML=items.map(c=>`<article class="crop-card"><button data-crop="${c.id}" type="button"><span class="crop-orb"><img src="${esc(cropPhoto(c))}" style="object-position:${cropPhotoPosition(c)}" loading="lazy" alt=""><span class="num orb-num">${String(cropList.indexOf(c)+1).padStart(2,'0')}</span></span><span class="crop-category">${t('cat.'+c.cat)}</span><h3>${esc(nm(c))}</h3><p class="latin">${esc(c.latin)}</p><span class="crop-flag ${preferred.includes(c.id)?'on':''}">${preferred.includes(c.id)?m('documentedTag'):m('unranked')}</span><span class="crop-bottom">${t('card.open')} ${icon('arrowUpRight',16)}</span></button></article>`).join('')
}
const cropTabs=['about','calc','nasa'];
const subTabs={calc:['npk','wheat','rates'],nasa:['land','irrigation','forecast']};
const tabTitle=id=>t(({about:'tab.aboutNew',calc:'tab.calculators',nasa:'tab.nasaNew'})[id]);
const subTitle=id=>t('sub.'+id);
const defaultSub=tab=>tab==='calc'?'npk':'land';
const hashPath=()=>`#/crop/${encodeURIComponent(state.cropId)}/${state.tab}${state.tab==='about'?'':'/'+state.sub}`;
function updateHash(){const target=hashPath();if(location.hash!==target)history.pushState(null,'',target)}
function readHash(){const match=location.hash.match(/^#\/crop\/([a-z0-9-]+)\/([a-z]+)(?:\/([a-z]+))?$/);if(!match)return false;
 if(!cropList.some(c=>c.id===match[1]))return false;
 state.cropId=match[1];state.tab=cropTabs.includes(match[2])?match[2]:'about';
 state.sub=subTabs[state.tab]?.includes(match[3])?match[3]:defaultSub(state.tab);
 state.view='crop';return true;}
function subNavigation(){const tabs=subTabs[state.tab];if(!tabs)return '';
 return `<nav class="source-tabs crop-subtabs" role="tablist" aria-label="${esc(tabTitle(state.tab))}">${tabs.map(key=>`<button type="button" role="tab" data-sub="${key}" id="sub-${key}" aria-controls="crop-panel" aria-selected="${key===state.sub}" tabindex="${key===state.sub?'0':'-1'}" class="source-chip ${key===state.sub?'active':''}">${esc(subTitle(key))}</button>`).join('')}</nav>`;}
function collapsible(label,content){return `<details class="crop-details"><summary>${esc(label)}</summary>${content}</details>`}
function toolFrame(){const file={npk:'agro-lab.html#npk',wheat:'wheat-water.html',rates:'npk-original.html'}[state.sub];
 const url='/tools/'+file.replace('#npk','')+'?embed=1'+(state.sub==='npk'?'#npk':'');
 return `<div class="embedded-tool"><iframe class="crop-iframe" src="${url}" title="${esc(subTitle(state.sub))}" loading="lazy" scrolling="no"></iframe></div>`;}
function scienceBlock(kind){const name=kind==='modis'?'NASA MODIS':kind==='twin'?'Climate Twin':'NASA POWER';return `<section class="science-card"><h3>${name}</h3><p>${t('science.limit')}</p><button data-science="${kind}" class="hero-go" type="button">${t('science.load')}</button><div id="science-${kind}" class="science-data" aria-live="polite">${scienceCached(kind)}</div></section>`;}
const scienceCache={};
function scienceCached(kind){const d=scienceCache[kind];if(!d)return `<p>${t('science.pending')}</p>`;
 if(d.error||d.status==='unavailable')return `<p>${t('science.pending')}</p>`;
 const source=Array.isArray(d.provenance)?(d.provenance[0]||{}):(d.provenance||d);
 const status=source.delivery||d.delivery||'unavailable';const meta=`${esc(source.source||'NASA')} · ${esc(status)} · ${esc(source.retrieved_at||'—')} · ${esc(source.resolution||'—')}`;
 if(kind==='modis')return `<small>${meta}</small><p>${t('science.modis')}</p>${modisChart(d.rows||[])}<button data-science-csv="modis" type="button">CSV ↓</button><div class="climate-table-wrap"><table class="climate-table"><thead><tr><th>Date</th><th>NDVI</th><th>Valid pixels</th></tr></thead><tbody>${(d.rows||[]).map(r=>`<tr><td>${esc(r.date)}</td><td>${r.ndvi==null?'—':esc(r.ndvi)}</td><td>${esc(r.valid_pixels??'—')}</td></tr>`).join('')}</tbody></table></div><p>${esc(d.status||'partial')}</p>`;
 if(kind==='twin')return `<small>${meta}</small><pre class="science-json">${esc(JSON.stringify(d,null,2))}</pre>`;
 const metrics=d.metrics||{};const metricUnits={rain_mm:'mm',gdd:'°C·day',frost_free_days:'days',mean_c:'°C',radiation:'kWh/m²/day',root_wetness:'0–1 (model)',hot_days_30c:'days',valid_days:'days',expected_days:'days'};
 const monthly=d.monthly||{};const yearRows=monthly.last_complete_year||[];const baseline=monthly.baseline_10_years||[];
 const monthlyTable=yearRows.length?`<h4>NASA POWER · ${esc(d.metrics?.year||'—')} / 10-year baseline</h4><div class="climate-table-wrap"><table class="climate-table"><thead><tr><th>Month</th><th>Rain (mm)</th><th>10y rain (mm)</th><th>Temperature (°C)</th><th>Solar (kWh/m²/day)</th><th>Wind (m/s)</th><th>Root wetness (0–1)</th></tr></thead><tbody>${yearRows.map((r,i)=>`<tr><td>${esc(r.month)}</td>${[['PRECTOTCORR',r],['PRECTOTCORR',baseline[i]||{}],['T2M',r],['ALLSKY_SFC_SW_DWN',r],['WS2M',r],['GWETROOT',r]].map(([k,v])=>`<td>${v[k]==null?'—':esc(v[k])}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`:'';
 return `<small>${meta}</small><p>${t('science.frost')}</p><div class="science-metrics">${Object.entries(metrics).filter(([k,v])=>typeof v==='number'||v===null).map(([k,v])=>`<div><strong>${esc(k)} (${esc(metricUnits[k]||'source units')})</strong><span>${v==null?'—':esc(v)}</span></div>`).join('')}</div>${monthlyTable}<details><summary>Historical weeks</summary><div class="climate-table-wrap"><table class="climate-table"><thead><tr><th>Week</th><th>Frost probability</th><th>n</th></tr></thead><tbody>${(d.weeks||[]).map(r=>`<tr><td>${esc(r.week)}</td><td>${r.frost_probability==null?'—':esc(r.frost_probability)}</td><td>${esc(r.n)}</td></tr>`).join('')}</tbody></table></div></details>`;
}
function modisChart(rows){const valid=rows.map((r,i)=>({...r,i})).filter(r=>typeof r.ndvi==='number'&&r.ndvi>=-1&&r.ndvi<=1);
 if(valid.length<2)return '<p>NDVI: insufficient verified data for a chart.</p>';
 const length=Math.max(1,rows.length-1);const points=valid.map(r=>`${(r.i/length*600+25).toFixed(1)},${(185-(r.ndvi+1)*80).toFixed(1)}`).join(' ');
 return `<div style="overflow-x:auto"><svg role="img" aria-label="MODIS NDVI series, qualified pixels only" viewBox="0 0 660 215" style="width:100%;min-width:320px"><line x1="25" y1="105" x2="635" y2="105" stroke="currentColor" opacity=".4"/><polyline points="${points}" fill="none" stroke="currentColor" stroke-width="2.5"/></svg></div>`;
}
function scienceCsv(){const d=scienceCache.modis;if(!d?.rows)return;
 const lines=['date,ndvi,valid_pixels,total_pixels',...d.rows.map(r=>[r.date,r.ndvi,r.valid_pixels,r.total_pixels].map(x=>String(x??'')).join(','))];
 const blob=new Blob([lines.join('\n')],{type:'text/csv;charset=utf-8'});const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='nasa-modis-ndvi.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
async function fetchScience(kind){const host=$('science-'+kind);if(!host)return;host.textContent='Loading verified source…';
 const path=kind==='modis'?'modis':kind==='twin'?'twin':'evidence';const site=state.farm?.id||'USA-NE-SCAL';
 try{const response=await fetch(`/api/science/${path}?site=${encodeURIComponent(site)}&crop=${encodeURIComponent(state.cropId)}`);const data=await response.json();if(!response.ok)throw Error(data.error||'unavailable');scienceCache[kind]=data;}catch(e){scienceCache[kind]={error:true};}
 if(host.isConnected)host.innerHTML=scienceCached(kind);
}
async function fetchValidation(){const slot=$('validation-metrics');if(!slot)return;try{
 const response=await fetch('/assets/validation.json');if(!response.ok)throw Error('missing');const data=await response.json();
 const rain=data.metrics?.PRECTOTCORR||{},monthly=data.metrics?.PRECTOTCORR_monthly||{};
 slot.innerHTML=`<p>NOAA station ${esc(data.station_id)} · ${esc(data.year)} · ${esc(data.status)} · ${esc(data.retrieved_at)} (snapshot)</p><div class="science-metrics"><div>Daily rain correlation <strong>${esc(rain.correlation??'—')}</strong></div><div>Monthly rain correlation <strong>${esc(monthly.correlation??'—')}</strong></div><div>Monthly rain bias (mm) <strong>${esc(monthly.bias??'—')}</strong></div></div>`;
 }catch(e){slot.textContent=t('science.pending')}
}
function nasaPanel(){let body='';
 if(state.sub==='land')body=calculator('land')+scienceBlock('modis')+scienceBlock('twin')+collapsible('Soil / vegetation',agroTab('soilInsights',activeCrop(),state.farm)+agroTab('vegetation',activeCrop(),state.farm));
 if(state.sub==='irrigation')body=calculator('irrigation')+scienceBlock('evidence')+collapsible('Water insights',agroTab('waterInsights',activeCrop(),state.farm));
 if(state.sub==='forecast')body=`<div class="tab-topline"><h2>${m('weather')}</h2><p>NOAA / NWS · USA only</p></div><button data-load="forecast" class="hero-go">${m('load')}</button><div id="liveData">${liveView('forecast')}</div>`+scienceBlock('evidence');
 return body+collapsible(t('more.sources'),dataExplorer()+agroTab('researchExtra',activeCrop(),state.farm)+`<div class="science-card"><h3>NASA POWER · ground validation (Nebraska)</h3><button data-validation="1">${t('science.load')}</button><div id="validation-metrics"></div><p>No ground-station validation for Tajikistan.</p><a href="/docs/validation_report.md" target="_blank" rel="noopener">Validation report</a></div>`)+collapsible(t('more.ai'),researchTab('aaiap'));
}
function cropDetail(){const crop=activeCrop();const site=state.farm;
 return `<main class="content-shell crop-detail">${locbar()}<div class="crop-breadcrumb"><button data-view="catalog" type="button">${icon('arrowLeft',16)} ${m('back')}</button><span class="crumb-now">${esc(cropName(crop))}</span></div><section class="crop-header"><div class="crop-hero-picture"><img src="${esc(cropDetailPhoto(crop))}" style="object-position:${cropPhotoPosition(crop)}" alt="${esc(cropName(crop))}" loading="eager"></div><div class="crop-header-copy"><span class="overline">NEBRASKA / ${esc(t('cat.'+crop.cat)).toUpperCase()}</span><h1>${esc(cropName(crop))}</h1><p class="latin">${esc(crop.latin)}</p><p class="crop-desc">${esc(cropDesc(crop))}</p><span class="img-credit">${t('img.credit')}</span><div class="crop-meta"><span>${icon('pin',15)} Nebraska</span><span>${icon('field',15)} SCAL · Clay Center</span><span class="viewer-pill">${icon('eye',15)} ${m('public')}</span></div></div></section>
 <section class="tool-layout"><div class="tool-primary"><nav class="crop-tabs" role="tablist" aria-label="Crop sections">${cropTabs.map(k=>`<button data-tab="${k}" type="button" role="tab" aria-selected="${state.tab===k}" class="${state.tab===k?'active':''}">${esc(tabTitle(k))}</button>`).join('')}</nav>${subNavigation()}<div id="tabArea" class="tab-area" role="tabpanel">${tabContent()}</div></div><aside class="tool-aside"><div class="aside-label">UNL · NEBRASKA</div><h3>${esc(fieldName())}</h3><p>40.575256° N · 98.137824° W</p><div class="aside-line"><span>${m('site')}</span><strong>${m('public')}</strong></div><div class="aside-line"><span>${t('area')}</span><strong>${m('unknown')}</strong></div><div class="aside-note">${m('context')}</div><a class="map-link" href="https://scal.unl.edu/location/" target="_blank" rel="noopener noreferrer">${icon('arrowUpRight',16)} UNL ${m('source')}</a><button data-nav="map" class="map-link">${icon('globe',16)} ${t('nav.map')}</button></aside></section></main>`;
}
function input(label,key,unit){const n=state.draft[key];return `<label class="field-input"><span>${label}</span><div class="input-unit"><input data-plan="${key}" type="number" min="0" step="any" inputmode="decimal" value="${n===null||n===undefined?'':esc(n)}" placeholder="—"><span>${unit}</span></div></label>`}
function compute(){const p=state.draft,a=moneyNumber(p.field_ha),x=moneyNumber(p.planted_ha),y=moneyNumber(p.extra_ha),total=(x===null||y===null)?null:x+y;
 const product=rate=>total!==null&&moneyNumber(rate)!==null?total*moneyNumber(rate):null;
 const extension=rate=>y!==null&&moneyNumber(rate)!==null?y*moneyNumber(rate):null;
 return {area:a,old:x,extra:y,total,free:(a!==null&&total!==null)?a-total:null,
  n:product(p.n_kg_ha),nExtra:extension(p.n_kg_ha),ph:product(p.p2o5_kg_ha),phExtra:extension(p.p2o5_kg_ha),k:product(p.k2o_kg_ha),kExtra:extension(p.k2o_kg_ha),water:product(p.water_m3_ha),waterExtra:extension(p.water_m3_ha)};
}
function orbStat(label,n,unit,secondary=''){return `<div class="orb-stat"><div class="orb s2"><strong>${fmt(n)}</strong>${n===null?'':`<small>${unit}</small>`}</div><span class="orb-label">${label}</span>${secondary?`<span class="orb-extra">${secondary}</span>`:''}</div>`}
function summary(mode='all'){const c=compute();const sets=[['N',c.n,c.nExtra,'kg'],['P₂O₅',c.ph,c.phExtra,'kg'],['K₂O',c.k,c.kExtra,'kg'],[m('W'),c.water,c.waterExtra,'m³']];
 const chosen=mode==='npk'?sets.slice(0,3):mode==='irrigation'?sets.slice(3):sets;
 const warning=c.area!==null&&c.total!==null&&c.total>c.area?`<p class="notice neutral">${icon('info',18)} ${m('badArea')}</p>`:'';
 return chosen.map(([name,n,more,unit])=>orbStat(name,n,unit,`${m('extraNeed')}: ${fmt(more)} ${unit}`)).join('')+warning;
}
function calculator(mode){const labels=mode==='land'?[m('fieldArea'),m('planted'),m('extra'),m('N'),m('P'),m('K'),m('W')]:mode==='npk'?[m('N'),m('P'),m('K')]:[m('W')];
 const keys=mode==='land'?['field_ha','planted_ha','extra_ha','n_kg_ha','p2o5_kg_ha','k2o_kg_ha','water_m3_ha']:mode==='npk'?['n_kg_ha','p2o5_kg_ha','k2o_kg_ha']:['water_m3_ha'];
 return `<div class="tab-topline"><span class="overline">${m('planning')}</span><h2>${m(mode)}</h2><p>${m('local')}</p></div><p class="notice neutral">${icon('info',18)} ${m('notGiven')}</p>
 <div class="input-card"><h3>${mode==='land'?m('land'):m('total')}</h3><div class="form-grid ${mode==='npk'?'three':''}">${keys.map((k,i)=>input(labels[i],k,k==='field_ha'||k==='planted_ha'||k==='extra_ha'?'ha':k==='water_m3_ha'?'m³/ha':'kg/ha')).join('')}</div>${mode!=='land'?`<p class="input-hint">${m('planning')} · ${m('land')}: ${fmt(state.draft.planted_ha)} + ${fmt(state.draft.extra_ha)} ha</p>`:''}</div>
 ${mode==='land'?`<div class="land-overview" id="liveLand">${orbStat(m('fieldArea'),compute().area,'ha')}${orbStat(m('areaTotal'),compute().total,'ha')}${orbStat(m('available'),compute().free,'ha')}</div>`:''}
 <h3>${m('total')}</h3><div class="calc-summary" id="liveSummary">${summary(mode)}</div><p class="calculation-caption">${m('planning')}</p>`;
}
function dataExplorer(){const s=sources.find(x=>x.id===state.dataTab)||sources[0],k=['en','ru','tg'].indexOf(getLang());
 const status=s.status==='linked'?m('linked'):s.status==='editorial'?m('editorial'):m('api');
 return `<div class="tab-topline"><span class="overline">NEBRASKA / RESEARCH DATA</span><h2>${m('data')}</h2><p>${m('readOnly')} · ${m('gps')}: ${state.farm.lat}, ${state.farm.lon}</p></div>
 <nav class="source-tabs" aria-label="Research source sections">${sources.map(x=>`<button type="button" data-source="${x.id}" class="source-chip ${x.id===s.id?'active':''}">${esc(x.name[k])}</button>`).join('')}</nav>
 <section class="source-card"><div class="source-card-head"><div><span class="overline">${s.tier==='essential'?'01 / ESSENTIAL':'02 / SECONDARY'}</span><h3>${esc(s.agency)}</h3></div><span class="data-state">${status}</span></div><p>${esc(s.detail[k])}</p><a class="source-link" href="${esc(s.url)}" target="_blank" rel="noopener noreferrer">${icon('arrowUpRight',16)} ${m('source')}</a>${sourceBody(s)}
 </section><section class="support-list"><h3>${m('extraSources')}</h3><div class="support-grid">${supportSources.map(item=>`<a href="${esc(item.url)}" target="_blank" rel="noopener noreferrer"><strong>${esc(item.name)}</strong><small>${esc(item.use[k])}</small>${icon('arrowUpRight',16)}</a>`).join('')}</div></section>`;
}
function sourceBody(s){if(s.id==='crops')return `<div class="source-results"><h3>${m('documented')}</h3><div class="quick-chips"><span>🌽 ${esc(cropName(cropList.find(x=>x.id==='corn')))}</span><span>🌱 ${esc(cropName(cropList.find(x=>x.id==='soybean')))}</span></div><p>${m('cropSource')} <a class="source-link" href="https://scal.unl.edu/" target="_blank" rel="noopener noreferrer">UNL SCAL</a></p></div>`;
 if(s.id==='practices')return `<div class="source-results"><h3>${m('editorial')}</h3><div class="quick-chips"><span>Center pivot</span><span>Lateral move</span><span>Subsurface drip</span></div><a class="source-link" href="https://scal.unl.edu/" target="_blank" rel="noopener noreferrer">UNL SCAL · ${m('source')}</a></div>`;
 if(['soil','climate','forecast'].includes(s.id))return `<div class="live-box"><button class="hero-go live-load" type="button" data-load="${s.id}" ${state.busy[s.id]?'disabled':''}>${state.busy[s.id]?m('loading'):m('load')} ${icon('arrowRight',16)}</button><div id="liveData">${liveView(s.id)}</div></div>`;
 return `<div class="source-results">${m('linked')}</div>`;
}
function liveView(id){const data=state.data[id],err=state.errors[id];if(err)return `<p class="source-error">${icon('info',18)} ${m('error')}<small>${esc(err)}</small></p>`;
 if(!data)return `<p class="source-idle">${m('empty')}</p>`;
 if(id==='soil')return `<div class="source-results"><small>USDA NRCS · ${esc(data.retrieved_at||'')}</small><h3>${m('mapUnit')}</h3>${data.map_units.length?data.map_units.map(x=>`<div class="source-record"><strong>${esc(x.name)}</strong><span>${esc(x.symbol)} · ${esc(x.mukey)}</span></div>`).join(''):`<p>${m('noRows')}</p>`}<p class="source-note">${esc(data.resolution_note)}</p></div>`;
 if(id==='climate')return `<div class="source-results"><small>NASA POWER · ${m('period')}: ${data.reference_year}</small><p class="source-note">${esc(data.resolution_note)}</p><div class="climate-table-wrap"><table class="climate-table"><thead><tr><th>Month</th><th>${m('avgTemp')} (°C)</th><th>${m('precip')} (mm)</th><th>${m('solar')} (kWh/m²/day)</th><th>${m('wind')} (m/s)</th></tr></thead><tbody>${data.months.map(x=>`<tr><td>${String(x.month).padStart(2,'0')}</td><td>${fmt(x.T2M)}</td><td>${fmt(x.PRECTOTCORR)}</td><td>${fmt(x.ALLSKY_SFC_SW_DWN)}</td><td>${fmt(x.WS2M)}</td></tr>`).join('')}</tbody></table></div></div>`;
 if(id==='forecast')return `<div class="source-results"><small>NOAA / NWS · ${esc(data.issued_at||data.retrieved_at||'')}</small><p class="source-note">${esc(data.resolution_note)}</p><div class="forecast-grid">${data.periods.map(x=>`<article><strong>${esc(x.name)}</strong><div class="forecast-temp">${fmt(x.temperature,0)} °${esc(x.temperatureUnit||'F')}</div><p>${esc(x.shortForecast)}</p><small>${esc(x.windSpeed||'')} ${esc(x.windDirection||'')}</small></article>`).join('')}</div></div>`;
 return '';
}

function galleryPhotosHtml(cropId){
 const photos=state.gallery[cropId];
 if(!photos)return `<p class="community-empty">${m('loading')}</p>`;
 if(!photos.length)return `<p class="community-empty">${m('photoNone')}</p>`;
 return photos.map(row=>`<figure class="community-photo"><img loading="lazy" src="${esc(row.url)}" alt="${esc(m('photoLabel'))}"><figcaption>${esc(m('photoLabel'))} · ${esc(row.uploaded_at?.slice(0,10)||'')}</figcaption></figure>`).join('');
}
function renderCommunityGallery(){
 if(document.body.classList.contains('cloud-demo'))return '';
 return `<section class="community-gallery" aria-labelledby="communityGalleryHeading"><header class="community-gallery-head"><div><span class="overline">AAIAP · COMMUNITY</span><h3 id="communityGalleryHeading">${m('farmerPhotos')}</h3><p>${m('farmerNotice')}</p></div></header>
 <div class="community-photos" id="communityPhotos">${galleryPhotosHtml(state.cropId)}</div>
 <div class="community-upload"><label for="communityPhotoFile">${m('photoAdd')}</label><input id="communityPhotoFile" type="file" accept="image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp"><small class="community-upload-note">${m('photoRule')}</small>
 <button type="button" data-community-upload="1">${m('photoSave')}</button><p id="communityPhotoError" class="community-error" hidden></p></div></section>`;
}
async function loadCommunityPhotos(crop){
 if(state.galleryLoading[crop])return;
 state.galleryLoading[crop]=true;
 try{const response=await fetch(`/api/community/photos?crop=${encodeURIComponent(crop)}`,{cache:'no-store'});
   const result=await response.json();if(!response.ok)throw new Error(result.error||'Could not load images');
   state.gallery[crop]=result.photos||[];
   if(state.view==='crop'&&state.cropId===crop){const area=$('communityPhotos');if(area)area.innerHTML=galleryPhotosHtml(crop)}
 }catch(err){console.warn('Community photo gallery unavailable',err);if(!state.gallery[crop])state.gallery[crop]=[];}
 finally{state.galleryLoading[crop]=false}
}
async function submitCommunityPhoto(button){
 const input=$('communityPhotoFile'),file=input?.files?.[0],crop=state.cropId,err=$('communityPhotoError');
 if(!file){if(err){err.hidden=false;err.textContent=m('photoAdd')+': JPG, PNG, WebP'}return;}
 if(file.size===0||file.size>5*1024*1024||!['image/jpeg','image/png','image/webp'].includes(file.type)){
   if(err){err.hidden=false;err.textContent=m('photoRule')}return;
 }
 button.disabled=true;button.textContent=m('photoWait');if(err)err.hidden=true;
 try{
   const response=await fetch(`/api/community/photos/${encodeURIComponent(crop)}`,{method:'POST',headers:{'Content-Type':file.type,'X-AAIAP-Photo-Upload':'1'},body:file,cache:'no-store'});
   const data=await response.json();if(!response.ok)throw new Error(data.error||`HTTP ${response.status}`);
   input.value='';await loadCommunityPhotos(crop);toast(m('photoDone'));
 }catch(e){if(err){err.hidden=false;err.textContent=e.message||String(e)}}
 finally{button.disabled=false;button.textContent=m('photoSave')}
}
function tabContent(){const c=activeCrop();if(state.tab==='about')return `<div class="tab-topline"><span class="overline">${m('about')}</span><h2>${esc(cropName(c))}</h2><p>${esc(cropDesc(c))}</p></div><div class="facts-grid"><div><small>${t('fact.latin')}</small><strong class="latin">${esc(c.latin)}</strong></div><div><small>${t('fact.group')}</small><strong>${t('cat.'+c.cat)}</strong></div><div><small>${t('fact.water')}</small><strong>${t('wat.'+c.water)}</strong></div><div><small>${t('fact.season')}</small><strong>${t('sea.'+c.season)}</strong></div></div><h3>${m('how')}</h3><div class="guide-grid">${guideSteps.map((g,i)=>`<article>${orb(i+1)}<strong>${t(g[0])}</strong><p>${t(g[1])}</p></article>`).join('')}</div><p class="notice">${m('guideNote')}</p>${renderCommunityGallery()}${collapsible(tabTitle("about")+" · Agrotechnology",agroTab("agrotech",c,state.farm))}`;
 if(state.tab==='calc')return toolFrame();
 if(state.tab==='nasa')return nasaPanel();
 return `<div class="pending-card"><h2>AAIAP</h2></div>`;
}
function render(){const host=$('portalContent');if(!host)return;
 host.innerHTML=state.view==='welcome'?welcome():state.view==='catalog'?catalog():state.view==='methodology'?metadataView():cropDetail();
 setBackground(state.view,state.cropId);
 refreshResearchStatic();
 if(state.view==='catalog')renderCatalogGrid();
 document.querySelectorAll('.crop-iframe').forEach(frame=>{frame.addEventListener('load',()=>{
  try{const doc=frame.contentDocument;const adjust=()=>{frame.style.height=Math.min(15000,Math.max(450,doc.documentElement.scrollHeight+32))+'px'};
   adjust();new ResizeObserver(adjust).observe(doc.documentElement);
  }catch(e){frame.style.height='1000px'}
 })});
 document.querySelector('.crop-subtabs [aria-selected="true"]')?.scrollIntoView({inline:'nearest',block:'nearest'});
 document.querySelectorAll('[data-nav]').forEach(b=>b.classList.toggle('current',b.dataset.nav===state.view||(b.dataset.nav==='catalog'&&state.view==='crop')));
}
async function loadSource(id){if(state.busy[id])return;state.busy[id]=true;state.errors[id]=null;render();
 try{state.data[id]=await api('/data/'+(id==='climate'?'power':id==='soil'?'soil':'forecast'));}
 catch(e){state.errors[id]=e.message;}
 finally{state.busy[id]=false;render();}
}
function showMap(){$('portal').hidden=true;document.body.classList.add('map-visible');window.dispatchEvent(new Event('resize'));window.dispatchEvent(new Event('aaiap-map-shown'));}
function showPortal(){$('portal').hidden=false;document.body.classList.remove('map-visible');render();}
$('backToPortal')?.addEventListener('click',showPortal);
$('homeBrand')?.addEventListener('click',()=>setView('welcome'));
document.addEventListener('click',async e=>{const b=e.target.closest('button');if(!b)return;
 if(b.dataset.researchMetric){switchResearchMetric(b.dataset.researchMetric);return}
 if(b.dataset.research){await handleResearchAction(b,state.farm?.id,state.cropId);return}
 if(b.dataset.researchExport){exportResearchCSV(b.dataset.researchExport);return}
 if(b.dataset.action==='openDemo'){state.cropId='corn';state.tab='nasa';state.sub='land';state.draft=retrievePlan();setView('crop');updateHash();return}
 if(b.dataset.nav){if(b.dataset.nav==='map')showMap();else setView(b.dataset.nav==='catalog'&&!state.farm?'welcome':b.dataset.nav);return;}
 if(b.dataset.view){setView(b.dataset.view);return}
 if(b.dataset.action==='enter'||b.id==='enterCatalog'){if(state.farm)setView('catalog');return}
 if(b.dataset.crop){state.cropId=b.dataset.crop;state.tab='about';state.sub='land';state.draft=retrievePlan();setView('crop');updateHash();loadCommunityPhotos(state.cropId);return}
 if(b.dataset.tab){state.tab=b.dataset.tab;state.sub=defaultSub(state.tab);render();updateHash();if(state.tab==='about'&&!state.gallery[state.cropId])loadCommunityPhotos(state.cropId);return}
 if(b.dataset.sub){state.sub=b.dataset.sub;render();updateHash();return}
 if(b.dataset.science){await fetchScience(b.dataset.science);return}
 if(b.dataset.scienceCsv){scienceCsv();return}
 if(b.dataset.validation){await fetchValidation();return}
 if(b.dataset.communityUpload){await submitCommunityPhoto(b);return}
 if(b.dataset.source){state.dataTab=b.dataset.source;render();return}
 if(b.dataset.load){await loadSource(b.dataset.load);return}
});
document.addEventListener('input',e=>{
 if(e.target.id==='cropSearch'){state.search=e.target.value;renderCatalogGrid();return;}
 if(e.target.matches('[data-plan]')){state.draft[e.target.dataset.plan]=moneyNumber(e.target.value);savePlan();const sum=$('liveSummary');if(sum)sum.innerHTML=summary(state.tab==='nasa'?state.sub:state.tab);const land=$('liveLand');if(land){const c=compute();land.innerHTML=orbStat(m('fieldArea'),c.area,'ha')+orbStat(m('areaTotal'),c.total,'ha')+orbStat(m('available'),c.free,'ha')}}
});
document.addEventListener('change',e=>{if(e.target.id==='categoryFilter'){state.filter=e.target.value;renderCatalogGrid()}if(e.target.id==='sortSelect'){state.sort=e.target.value;renderCatalogGrid()}});
function navigationFromHash(){if(readHash()){render()}else if(location.hash.startsWith('#/crop/')){state.tab='about';state.sub='land';render()}}
window.addEventListener('hashchange',navigationFromHash);
window.addEventListener('popstate',navigationFromHash);
document.addEventListener('keydown',e=>{
 const b=e.target.closest('[data-sub], [data-tab]');if(!b||!['ArrowLeft','ArrowRight'].includes(e.key))return;
 e.preventDefault();const step=e.key==='ArrowRight'?1:-1;
 if(b.dataset.sub){const keys=subTabs[state.tab];state.sub=keys[(keys.indexOf(state.sub)+step+keys.length)%keys.length];render();updateHash();document.querySelector(`[data-sub="${state.sub}"]`)?.focus();}
 else {state.tab=cropTabs[(cropTabs.indexOf(state.tab)+step+cropTabs.length)%cropTabs.length];state.sub=defaultSub(state.tab);render();updateHash();document.querySelector(`[data-tab="${state.tab}"]`)?.focus()}
});
onLang(()=>render());

document.addEventListener('aaiap-photos-updated',()=>render());
// External image URLs are illustrative. For unavailable images, use the local asset.
document.addEventListener('error',e=>{const image=e.target;if(image?.tagName==='IMG'&&!image.closest('.leaflet-container')&&!image.dataset.fallbackShown){image.dataset.fallbackShown='true';image.src='./assets/farm-fallback.svg';}},true);
start();
