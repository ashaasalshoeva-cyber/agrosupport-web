import {mediaFor} from './crop-images.js';
// ============================================================
//  ФОТО НА ВЕСЬ ЭКРАН — здесь меняются и добавляются картинки.
//  Положите свой файл в папку assets/bg/ и впишите его имя ниже.
//  Лучше всего: JPG/WebP, 1920×1200 или больше, до ~300 КБ.
// ============================================================

// 1) Какое фото стоит на каком экране (отдельно для тёмной и светлой темы).
export const BACKGROUNDS = {
  welcome: { dark: './assets/bg/bg-1.jpg', light: './assets/bg/bg-2.jpg' }, // старт: выбор региона
  catalog: { dark: './assets/bg/bg-3.jpg', light: './assets/bg/bg-2.jpg' }, // каталог культур
  crop:    { dark: './assets/bg/bg-1.jpg', light: './assets/bg/bg-2.jpg' }, // страница культуры
};

// 2) Своё фото для отдельной культуры (необязательно).
//    Ключ — id культуры, например wheat, cotton, potato.
//    Пример:  wheat: './assets/bg/wheat.jpg',
export const CROP_BACKGROUNDS = {
};

const host = () => document.getElementById('bgPhoto');

export function setBackground(view, cropId) {
  const el = host(); if (!el) return;
  const gitCropBackground = view === 'crop' ? mediaFor(cropId,'background') : '';
  const set = gitCropBackground ? {dark:gitCropBackground,light:gitCropBackground} : (CROP_BACKGROUNDS[cropId] && view === 'crop')
    ? { dark: CROP_BACKGROUNDS[cropId], light: CROP_BACKGROUNDS[cropId] }
    : (BACKGROUNDS[view] || BACKGROUNDS.welcome);
  el.style.setProperty('--photo-dark', `url("${set.dark}")`);
  el.style.setProperty('--photo-light', `url("${set.light || set.dark}")`);
}
