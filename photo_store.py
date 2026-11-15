"""Local photo/administrator storage for the AAIAP research pilot.

No third-party dependencies. Only verified JPEG, PNG and WebP images are stored;
image metadata (such as GPS EXIF) is not stripped automatically.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import struct
import threading
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
# Optionally set AAIAP_STORAGE_DIR to a stable directory outside the code folder.
STORAGE = Path(os.environ.get('AAIAP_STORAGE_DIR', str(BASE))).expanduser().resolve()
DATA_DIR = STORAGE / 'data'
UPLOAD_DIR = STORAGE / 'uploads' / 'crops'
ADMIN_FILE = DATA_DIR / 'admin.json'
PHOTO_FILE = DATA_DIR / 'crop_photos.json'
PHOTO_LOCK = threading.RLock()
MAX_IMAGE_BYTES = 6 * 1024 * 1024
MAX_IMAGE_PIXELS = 28_000_000
CROP_IDS = frozenset((
    'wheat', 'cotton', 'corn', 'barley', 'tomato', 'potato', 'rice',
    'alfalfa', 'sunflower', 'soybean', 'apple', 'apricot', 'grape', 'chickpea'
))


def _json_read(path: Path) -> dict:
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError(f'Invalid JSON object: {path.name}')
    return data


def _atomic_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    candidate = path.with_name(path.name + '.' + secrets.token_hex(8) + '.tmp')
    try:
        with candidate.open('x', encoding='utf-8') as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        os.replace(candidate, path)
    finally:
        candidate.unlink(missing_ok=True)


def set_admin_password(password: str) -> None:
    if len(password) < 12 or len(password) > 200:
        raise ValueError('Administrator password must be between 12 and 200 characters')
    salt = secrets.token_bytes(32)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 400_000)
    with PHOTO_LOCK:
        _atomic_json(ADMIN_FILE, {
            'version': 1, 'method': 'pbkdf2-sha256', 'iterations': 400_000,
            'salt': salt.hex(), 'hash': hashed.hex()
        })


def has_admin() -> bool:
    return ADMIN_FILE.is_file()

def admin_revision() -> str:
    # Any reset of the administrator password invalidates existing login sessions.
    try:
        return hashlib.sha256(ADMIN_FILE.read_bytes()).hexdigest()
    except OSError:
        return ''


def check_admin_password(password: str) -> bool:
    if len(password) > 200 or not has_admin():
        return False
    try:
        doc = _json_read(ADMIN_FILE)
        if doc.get('method') != 'pbkdf2-sha256':
            return False
        iterations = int(doc['iterations'])
        if not 300_000 <= iterations <= 2_000_000:
            return False
        expected = bytes.fromhex(doc['hash'])
        actual = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(doc['salt']), iterations)
        return hmac.compare_digest(expected, actual)
    except (ValueError, KeyError, TypeError, OSError):
        return False


def photo_manifest() -> dict:
    """Sanitize stored metadata before returning it publicly."""
    with PHOTO_LOCK:
        raw = _json_read(PHOTO_FILE)
        clean = {}
        for crop, row in raw.items():
            if crop not in CROP_IDS or not isinstance(row, dict):
                continue
            url = row.get('url', '')
            if not isinstance(url, str) or not url.startswith(f'/uploads/crops/{crop}/'):
                continue
            filename = url.rsplit('/', 1)[-1]
            if filename in ('.', '..') or not filename or '/' in filename or '\\' in filename:
                continue
            clean[crop] = {
                'url': url,
                'focus_x': max(0, min(100, int(row.get('focus_x', 50)))),
                'focus_y': max(0, min(100, int(row.get('focus_y', 50)))),
                'updated_at': str(row.get('updated_at', '')),
            }
        return clean


def inspect_image(data: bytes) -> str:
    """Identify image bytes, not client-provided file extensions or MIME types."""
    if not data or len(data) > MAX_IMAGE_BYTES:
        raise ValueError('Image must be between 1 byte and 6 MB')
    if data.startswith(b'\x89PNG\r\n\x1a\n') and data[12:16] == b'IHDR' and len(data) > 25:
        width, height = struct.unpack('>II', data[16:24])
        fmt = 'png'
    elif data[:3] == b'\xff\xd8\xff':
        width, height = _jpeg_size(data)
        fmt = 'jpg'
    elif data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        width, height = _webp_size(data)
        fmt = 'webp'
    else:
        raise ValueError('Only genuine JPEG, PNG or WebP files are accepted')
    if min(width, height) < 50 or max(width, height) > 10_000 or width * height > MAX_IMAGE_PIXELS:
        raise ValueError('Invalid dimensions; use an image at least 50 px and at most 28 megapixels')
    return fmt


def _jpeg_size(data: bytes) -> tuple[int, int]:
    i = 2
    while i < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        while i < len(data) and data[i] == 0xFF:
            i += 1
        if i >= len(data):
            break
        marker = data[i]; i += 1
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            continue
        if i + 2 > len(data):
            break
        segment_len = int.from_bytes(data[i:i+2], 'big')
        if segment_len < 2 or i + segment_len > len(data):
            break
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            if segment_len < 7:
                break
            return (int.from_bytes(data[i+5:i+7], 'big'), int.from_bytes(data[i+3:i+5], 'big'))
        i += segment_len
    raise ValueError('Cannot read JPEG dimensions')


def _webp_size(data: bytes) -> tuple[int, int]:
    chunk = data[12:16]
    if chunk == b'VP8X' and len(data) >= 30:
        return int.from_bytes(data[24:27], 'little') + 1, int.from_bytes(data[27:30], 'little') + 1
    if chunk == b'VP8L' and len(data) >= 25 and data[20] == 0x2F:
        b0,b1,b2,b3 = data[21:25]
        return 1 + (b0 | ((b1 & 63) << 8)), 1 + ((b1 >> 6) | (b2 << 2) | ((b3 & 15) << 10))
    if chunk == b'VP8 ' and len(data) >= 30 and data[23:26] == b'\x9d\x01\x2a':
        return int.from_bytes(data[26:28], 'little') & 0x3FFF, int.from_bytes(data[28:30], 'little') & 0x3FFF
    raise ValueError('Cannot read WebP dimensions')


def update_crop_photo(crop: str, data: bytes) -> dict:
    if crop not in CROP_IDS:
        raise ValueError('Unknown crop')
    fmt = inspect_image(data)
    with PHOTO_LOCK:
        existing = photo_manifest().get(crop)
        folder = UPLOAD_DIR / crop
        folder.mkdir(parents=True, exist_ok=True)
        filename = secrets.token_hex(16) + '.' + fmt
        file_path = folder / filename
        with file_path.open('xb') as fh:
            fh.write(data)
        try:
            manifest = _json_read(PHOTO_FILE)
            entry = {'url': f'/uploads/crops/{crop}/{filename}',
                     'focus_x': 50, 'focus_y': 50,
                     'updated_at': datetime.now(timezone.utc).isoformat(timespec='seconds')}
            manifest[crop] = entry
            _atomic_json(PHOTO_FILE, manifest)
        except Exception:
            file_path.unlink(missing_ok=True)
            raise
        # Old uploads only; bundled reference images are never deleted.
        if existing:
            old_file = folder / Path(existing['url']).name
            if old_file != file_path:
                old_file.unlink(missing_ok=True)
        return entry


def focus_crop_photo(crop: str, x: int, y: int) -> dict:
    if crop not in CROP_IDS:
        raise ValueError('Unknown crop')
    if not (0 <= x <= 100 and 0 <= y <= 100):
        raise ValueError('Position must be between 0 and 100')
    with PHOTO_LOCK:
        rows = _json_read(PHOTO_FILE)
        if crop not in rows:
            raise ValueError('Upload a photo first')
        rows[crop]['focus_x'] = x
        rows[crop]['focus_y'] = y
        rows[crop]['updated_at'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
        _atomic_json(PHOTO_FILE, rows)
        return photo_manifest()[crop]


def reset_crop_photo(crop: str) -> None:
    if crop not in CROP_IDS:
        raise ValueError('Unknown crop')
    with PHOTO_LOCK:
        rows = _json_read(PHOTO_FILE)
        old = rows.pop(crop, None)
        _atomic_json(PHOTO_FILE, rows)
        if isinstance(old, dict):
            name = Path(str(old.get('url',''))).name
            if name and name != '.':
                (UPLOAD_DIR / crop / name).unlink(missing_ok=True)
