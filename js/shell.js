// Shared chrome for both the portal and the GIS map: theme, language, static icons.
import {applyStatic,initTheme,getTheme,setTheme,setLang,onLang,tt} from './i18n.js';
import {icon} from './icons.js';

export function hydrateIcons(root=document){
 root.querySelectorAll('[data-icon]').forEach(el=>{if(el.dataset.done)return;el.innerHTML=icon(el.dataset.icon,Number(el.dataset.size)||18);el.dataset.done='1';el.classList.add('ico')});
}
function paintTheme(){
 const dark=getTheme()==='dark';
 document.querySelectorAll('.js-theme .theme-icon').forEach(el=>{el.innerHTML=icon(dark?'sun':'moon',18)});
 document.querySelectorAll('.js-theme').forEach(b=>b.setAttribute('aria-pressed',String(!dark)));
}
initTheme();hydrateIcons();paintTheme();applyStatic();
window.addEventListener('themechange',paintTheme);
document.addEventListener('click',e=>{
 const lb=e.target.closest('[data-lang-btn]');if(lb){setLang(lb.dataset.langBtn);return}
 if(e.target.closest('.js-theme')){setTheme(getTheme()==='dark'?'light':'dark')}
});
onLang(()=>{hydrateIcons();paintTheme()});
export {tt};
