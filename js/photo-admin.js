// AAIAP crop photo editor: public read-only photos + password-protected uploads.
// The server is authoritative; local previews do not change public photos until saved.
import {cropList, cropName} from './catalog-data.js';
import {mediaFor} from './crop-images.js';

const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c]));
const fallback = './assets/farm-fallback.svg';
let photos = {};
let auth = {authenticated:false, configured:false, csrf:''};
let currentCropId = 'corn';
let pendingFile = null;
let pendingObjectUrl = '';
let busy = false;

export function cropPhoto(crop) {
  return photos[crop.id]?.url || mediaFor(crop.id,'card') || crop.photo;
}
export function cropDetailPhoto(crop) { return mediaFor(crop.id,'detail') || cropPhoto(crop); }
export function cropPhotoPosition(crop) {
  const entry = photos[crop.id];
  return `${entry?.focus_x ?? 50}% ${entry?.focus_y ?? 50}%`;
}
export async function refreshCropPhotos() {
  const res = await fetch('/api/photos', {cache:'no-store'});
  if (!res.ok) { photos={}; document.dispatchEvent(new Event('aaiap-photos-updated')); return; }
  const data = await res.json();
  photos = data.photos || {};
  document.dispatchEvent(new Event('aaiap-photos-updated'));
}

async function request(url, options = {}) {
  const res = await fetch(url, {credentials:'same-origin', cache:'no-store', ...options});
  let result = {};
  try { result = await res.json(); } catch (_) { /* network/proxy error */ }
  if (!res.ok) throw new Error(result.error || `Ошибка сервера (${res.status})`);
  return result;
}
function notice(message, error=false) {
  const n = $('photoEditorNotice');
  if (!n) return;
  n.hidden = false;
  n.textContent = message;
  n.classList.toggle('is-error', error);
}
function clearNotice() {
  const n = $('photoEditorNotice');
  if (n) { n.hidden = true; n.textContent = ''; }
}
function releasePreview() {
  if (pendingObjectUrl) URL.revokeObjectURL(pendingObjectUrl);
  pendingObjectUrl = '';
  pendingFile = null;
}
function selectedCrop() { return cropList.find(c => c.id === currentCropId) || cropList[0]; }
function currentFocus() {
  return [photos[currentCropId]?.focus_x ?? 50, photos[currentCropId]?.focus_y ?? 50];
}
function updatePreview() {
  const image = $('photoEditorPreview');
  if (!image) return;
  image.src = pendingObjectUrl || cropPhoto(selectedCrop());
  image.style.objectPosition = `${$('photoFocusX')?.value ?? 50}% ${$('photoFocusY')?.value ?? 50}%`;
  const label = $('photoEditorCurrent');
  if (label) label.textContent = pendingFile ? `Новое изображение: ${pendingFile.name}` :
    (photos[currentCropId] ? 'Фотография сохранена на сервере' : 'Исходная иллюстрация сайта');
}
function chooseCrop(id) {
  currentCropId = cropList.some(c => c.id === id) ? id : 'corn';
  releasePreview();
  const input = $('photoFileInput');
  if (input) input.value = '';
  const [x,y] = currentFocus();
  if ($('photoFocusX')) $('photoFocusX').value = x;
  if ($('photoFocusY')) $('photoFocusY').value = y;
  updatePreview();
}

function draw() {
  const root = $('photoEditorBody');
  if (!root) return;
  clearNotice();
  if (!auth.configured) {
    root.innerHTML = `<p>Сначала создай пароль администратора в терминале на ноутбуке:</p>
    <pre>py -3 setup_admin.py</pre><p>Затем вернись сюда и нажми кнопку ниже.</p>
    <button id="photoRefreshAuth" type="button" class="photo-primary">Проверить настройку</button>`;
    $('photoRefreshAuth')?.addEventListener('click', refreshStatus);
    return;
  }
  if (!auth.authenticated) {
    root.innerHTML = `<p>Посетители видят фотографии, но менять их может только администратор.</p>
    <form id="photoLoginForm"><label for="photoPassword">Пароль администратора</label>
    <input type="password" id="photoPassword" autocomplete="current-password" required maxlength="200" />
    <button class="photo-primary" type="submit">Войти в редактор</button></form>`;
    $('photoLoginForm').addEventListener('submit', async e => {
      e.preventDefault();
      if (busy) return;
      busy = true;
      try {
        const data = await request('/api/admin/login', {
          method:'POST', headers:{'Content-Type':'application/json'},
          body:JSON.stringify({password:$('photoPassword').value})
        });
        auth.authenticated = true;
        auth.csrf = data.csrf;
        draw();
        notice('Вход выполнен. Теперь можно заменить фотографию любой культуры.');
      } catch(err) { notice(err.message, true); }
      finally { busy = false; }
    });
    return;
  }
  root.innerHTML = `<div class="photo-admin-session"><span>● Доступ администратора</span><button id="photoLogout" class="photo-secondary" type="button">Выйти</button></div>
    <label for="photoCropSelect">Выберите культуру</label>
    <select id="photoCropSelect">${cropList.map(c => `<option value="${esc(c.id)}">${esc(cropName(c))} · ${esc(c.latin)}</option>`).join('')}</select>
    <div class="photo-preview-frame"><img id="photoEditorPreview" src="${fallback}" alt="Предпросмотр культуры" /></div>
    <p id="photoEditorCurrent" class="photo-editor-help"></p>
    <label for="photoFileInput">Новая фотография (JPG, PNG, WebP; до 6 МБ)</label>
    <input id="photoFileInput" type="file" accept="image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp" />
    <p class="photo-editor-help">Файлы сохраняются на ноутбуке в папке <code>uploads/crops/</code>. Изображение станет видно всем после сохранения. Не загружай фотографии с личными GPS-данными: метаданные не удаляются автоматически.</p>
    <div class="photo-focus-controls"><label>Положение изображения по горизонтали <input id="photoFocusX" type="range" min="0" max="100" value="50" /></label>
    <label>По вертикали <input id="photoFocusY" type="range" min="0" max="100" value="50" /></label></div>
    <div class="photo-buttons"><button id="photoUpload" class="photo-primary" type="button">Сохранить фото</button>
    <button id="photoFocusSave" class="photo-secondary" type="button">Сохранить положение</button>
    <button id="photoReset" class="photo-danger" type="button">Вернуть исходное</button></div>`;

  $('photoCropSelect').value = currentCropId;
  $('photoCropSelect').addEventListener('change', e => { chooseCrop(e.target.value); clearNotice(); });
  $('photoFileInput').addEventListener('change', e => {
    releasePreview();
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 6 * 1024 * 1024 || !['image/jpeg','image/png','image/webp'].includes(file.type)) {
        e.target.value=''; notice('Выберите JPG, PNG или WebP размером до 6 МБ.', true);
      } else {
        pendingFile = file;
        pendingObjectUrl = URL.createObjectURL(file);
        clearNotice();
      }
    }
    updatePreview();
  });
  ['photoFocusX','photoFocusY'].forEach(id => $(id).addEventListener('input', updatePreview));
  $('photoUpload').addEventListener('click', async () => {
    if (!pendingFile) return notice('Сначала выберите новую фотографию.', true);
    await runEdit(async () => {
      await request(`/api/admin/photos/${currentCropId}`, {
        method:'PUT', headers:{'Content-Type':pendingFile.type,'X-AAIAP-CSRF':auth.csrf}, body:pendingFile
      });
      await saveFocus();
      await refreshCropPhotos();
      releasePreview();
      $('photoFileInput').value = '';
      updatePreview();
      notice('Фотография сохранена на сервере. Её видят все посетители.');
    });
  });
  $('photoFocusSave').addEventListener('click', () => runEdit(async () => {
    if (!photos[currentCropId]) throw new Error('Сначала загрузите фотографию на сервер.');
    await saveFocus();
    await refreshCropPhotos();
    updatePreview();
    notice('Положение фотографии сохранено.');
  }));
  $('photoReset').addEventListener('click', () => runEdit(async () => {
    if (!photos[currentCropId]) throw new Error('Для этой культуры ещё нет загруженного фото.');
    if (!confirm(`Вернуть исходную фотографию для «${cropName(selectedCrop())}»?`)) return;
    await request(`/api/admin/photos/${currentCropId}`, {method:'DELETE',headers:{'X-AAIAP-CSRF':auth.csrf}});
    await refreshCropPhotos();
    chooseCrop(currentCropId);
    notice('Исходное изображение восстановлено.');
  }));
  $('photoLogout').addEventListener('click', () => runEdit(async () => {
    await request('/api/admin/logout', {method:'POST',headers:{'X-AAIAP-CSRF':auth.csrf}});
    auth = {configured:true, authenticated:false, csrf:''};
    releasePreview();
    draw();
  }));
  chooseCrop(currentCropId);
}
async function saveFocus() {
  await request(`/api/admin/photos/${currentCropId}`, {
    method:'PATCH',headers:{'Content-Type':'application/json','X-AAIAP-CSRF':auth.csrf},
    body:JSON.stringify({focus_x:Number($('photoFocusX').value),focus_y:Number($('photoFocusY').value)})
  });
}
async function runEdit(fn) {
  if (busy) return;
  busy = true;
  const controls = $('photoEditorBody')?.querySelectorAll('button');
  controls?.forEach(b => b.disabled = true);
  try { await fn(); }
  catch(e) { notice(e.message, true); }
  finally { busy=false; controls?.forEach(b => b.disabled = false); }
}
async function refreshStatus() {
  try {
    auth = await request('/api/admin/status');
    draw();
  } catch(e) { notice(`Не удалось связаться с сервером: ${e.message}`, true); }
}
async function openEditor() {
  const layer = $('photoEditorBackdrop');
  if (!layer) return;
  layer.hidden = false;
  await refreshStatus();
  $('photoEditorClose')?.focus();
}
function closeEditor() {
  const layer = $('photoEditorBackdrop');
  if (layer) layer.hidden = true;
  releasePreview();
  $('photoAdminOpen')?.focus();
}
document.querySelectorAll('#photoAdminOpen').forEach(button => button.addEventListener('click', openEditor));
$('photoEditorClose')?.addEventListener('click', closeEditor);
$('photoEditorBackdrop')?.addEventListener('click', e => { if (e.target.id === 'photoEditorBackdrop') closeEditor(); });
document.addEventListener('keydown', e => { if(e.key === 'Escape' && !$('photoEditorBackdrop')?.hidden) closeEditor(); });
// Update catalogue/hero when a different user edits a photo and we refresh the page.
