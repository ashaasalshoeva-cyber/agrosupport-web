// Translated, formatted views of the demo research sites (sites.js stores raw values only).
import {t,fmt} from './i18n.js';
import {regionName,cropList,cropName} from './catalog-data.js';
export const siteName=s=>t('f.'+s.id);
export const siteRegion=s=>s.region.startsWith('USA')?`${regionName(s.region)}, ${t('c.USA')}`:regionName(s.region);
export const siteCrop=s=>s.crop==='veg'?t('crop.veg'):cropName(cropList.find(c=>c.id===s.crop));
export const siteSoil=s=>s.soil?t('soil.'+s.soil):t('m.tbd');
export const siteArea=s=>s.area===null?t('m.unconf'):`${fmt(s.area,1,1)} ${t('u.ha')}`;
export const siteMoist=s=>s.moisture===null?t('m.none'):`${fmt(s.moisture,0)} %`;
export const siteNdvi=s=>s.ndvi===null?t('m.none'):fmt(s.ndvi,2,2);
export const sitePh=s=>s.ph===null?t('m.none'):fmt(s.ph,1,1);
export const siteTemp=s=>s.temp===null?t('m.none'):`${fmt(s.temp,0)} °C`;
export const siteCountry=s=>s.id.startsWith('USA')?t('c.USA'):t('c.TJK');
