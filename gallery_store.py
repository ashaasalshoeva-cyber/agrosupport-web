"""Local, append-only gallery for farmer photos. No user accounts.

Upload bodies are verified against image signatures and dimensions, and common
image metadata is removed before writing. Only crop IDs allowlisted by the app
are accepted. This is a LAN/local prototype and is not a public upload service.
"""
from __future__ import annotations

import json
import os
import secrets
import struct
import threading
import zlib
from datetime import datetime, timezone
from pathlib import Path

from image_checks import CROP_IDS, MAX_IMAGE_BYTES, inspect_image

ROOT = Path(__file__).resolve().parent
STORAGE = Path(os.environ.get('AAIAP_STORAGE_DIR', str(ROOT))).expanduser().resolve()
GALLERY_FILE = STORAGE / 'data' / 'farmer_photos.json'
GALLERY_DIR = STORAGE / 'uploads' / 'community'
MAX_PER_CROP = 12
LOCK = threading.RLock()


def _read() -> dict:
    if not GALLERY_FILE.exists():
        return {}
    data = json.loads(GALLERY_FILE.read_text(encoding='utf8'))
    if not isinstance(data, dict):
        raise ValueError('Invalid gallery index')
    return data


def _write(data: dict) -> None:
    GALLERY_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = GALLERY_FILE.with_name(GALLERY_FILE.name + '.' + secrets.token_hex(6) + '.tmp')
    try:
        with tmp.open('x', encoding='utf8') as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        os.replace(tmp, GALLERY_FILE)
    finally:
        tmp.unlink(missing_ok=True)


def gallery(crop: str) -> list[dict]:
    if crop not in CROP_IDS:
        raise ValueError('Unknown crop')
    with LOCK:
        rows = _read().get(crop, [])
        if not isinstance(rows, list):
            return []
        clean = []
        for entry in rows:
            if not isinstance(entry, dict):
                continue
            url = entry.get('url', '')
            if (not isinstance(url, str) or not url.startswith(f'/uploads/community/{crop}/')
                    or '/' in url.split('/')[-1] or '\\' in url):
                continue
            clean.append({'id': str(entry.get('id', ''))[:40], 'url': url,
                          'uploaded_at': str(entry.get('uploaded_at', ''))[:35]})
        return clean[-MAX_PER_CROP:]


def _strip_jpeg_metadata(data: bytes) -> bytes:
    # Preserve compressed image scan; drop EXIF, IPTC, XMP, comments and other APP blocks.
    if not data.endswith(b'\xff\xd9'):
        raise ValueError('Truncated JPEG image')
    i = 2
    out = bytearray(data[:2])
    while i + 3 <= len(data):
        if data[i] != 0xff:
            raise ValueError('Invalid JPEG marker sequence')
        marker_start = i
        while i < len(data) and data[i] == 0xff:
            i += 1
        if i >= len(data):
            break
        marker = data[i]; i += 1
        if marker == 0xda:   # Start of Scan: copy remaining encoded image unchanged
            if i + 2 > len(data):
                raise ValueError('Invalid JPEG scan')
            length = int.from_bytes(data[i:i+2], 'big')
            if length < 2 or i + length > len(data):
                raise ValueError('Invalid JPEG scan')
            out.extend(data[marker_start:])
            return bytes(out)
        if marker in (0xd8, 0xd9, 0x01) or 0xd0 <= marker <= 0xd7:
            out.extend(data[marker_start:i]); continue
        if i + 2 > len(data):
            break
        length = int.from_bytes(data[i:i+2], 'big')
        if length < 2 or i + length > len(data):
            break
        if not (0xe0 <= marker <= 0xef or marker == 0xfe):
            out.extend(data[marker_start:i+length])
        # Keep the standard JFIF APP0 marker for normal decoding.
        elif marker == 0xe0 and data[i+2:i+7] == b'JFIF\x00':
            out.extend(data[marker_start:i+length])
        # Adobe APP14 marker helps correct decoding for some CMYK images.
        elif marker == 0xee and data[i+2:i+7] == b'Adobe':
            out.extend(data[marker_start:i+length])
        i += length
    raise ValueError('Malformed JPEG image')


def _strip_png_metadata(data: bytes) -> bytes:
    out = bytearray(b'\x89PNG\r\n\x1a\n')
    pos, count = 8, 0
    seen_header = seen_data = seen_end = False
    while pos + 12 <= len(data):
        count += 1
        if count > 1500:
            raise ValueError('Excessive PNG chunks')
        size = struct.unpack('>I', data[pos:pos+4])[0]
        end = pos + 12 + size
        if size > MAX_IMAGE_BYTES or end > len(data):
            raise ValueError('Invalid PNG chunk')
        kind = data[pos+4:pos+8]
        payload = data[pos+8:pos+8+size]
        checksum = struct.unpack('>I', data[end-4:end])[0]
        if zlib.crc32(kind+payload) & 0xffffffff != checksum:
            raise ValueError('Invalid PNG CRC')
        if kind == b'IHDR':
            if seen_header or pos != 8:
                raise ValueError('Invalid PNG header')
            seen_header = True
        if kind == b'IDAT':
            seen_data = True
        if kind == b'IEND':
            seen_end = True
        # Only keep chunks required to render; EXIF/text/XMP/ICC etc are discarded.
        if kind in (b'IHDR', b'PLTE', b'IDAT', b'IEND', b'tRNS'):
            out.extend(data[pos:end])
        pos = end
        if kind == b'IEND':
            break
    if not (seen_header and seen_data and seen_end):
        raise ValueError('Incomplete PNG image')
    return bytes(out)


def _strip_webp_metadata(data: bytes) -> bytes:
    if len(data) < 20 or data[:4] != b'RIFF' or data[8:12] != b'WEBP':
        raise ValueError('Invalid WebP image')
    if struct.unpack('<I', data[4:8])[0] + 8 > len(data):
        raise ValueError('Truncated WebP')
    pos = 12
    chunks = bytearray()
    seen_image = False
    while pos + 8 <= len(data):
        kind = data[pos:pos+4]
        size = struct.unpack('<I', data[pos+4:pos+8])[0]
        end = pos + 8 + size + (size % 2)
        if end > len(data):
            raise ValueError('Invalid WebP chunk')
        if kind not in (b'EXIF', b'XMP ', b'ICCP'):
            chunk = bytearray(data[pos:end])
            if kind == b'VP8X' and size >= 10:
                chunk[8] &= ~(0x08 | 0x04 | 0x20)  # EXIF / XMP / ICC flags
            chunks.extend(chunk)
            if kind in (b'VP8 ', b'VP8L', b'ANIM', b'ANMF'):
                seen_image = True
        pos = end
    if not seen_image:
        raise ValueError('Missing WebP image data')
    return b'RIFF'+struct.pack('<I', len(chunks)+4)+b'WEBP'+bytes(chunks)


def clean_image(data: bytes) -> tuple[bytes, str]:
    fmt = inspect_image(data)
    if fmt == 'jpg':
        cleaned = _strip_jpeg_metadata(data)
    elif fmt == 'png':
        cleaned = _strip_png_metadata(data)
    else:
        cleaned = _strip_webp_metadata(data)
    return cleaned, fmt


def append_photo(crop: str, data: bytes) -> dict:
    if crop not in CROP_IDS:
        raise ValueError('Unknown crop')
    if not data or len(data) > MAX_IMAGE_BYTES:
        raise ValueError('JPG, PNG, WebP only, maximum 5 MB')
    cleaned, extension = clean_image(data)
    with LOCK:
        all_rows = _read()
        records = all_rows.get(crop, [])
        if not isinstance(records, list):
            raise ValueError('Invalid crop gallery')
        if len(records) >= MAX_PER_CROP:
            raise ValueError('Gallery is full (12 photos); ask the site owner to review old uploads')
        folder = GALLERY_DIR / crop
        folder.mkdir(parents=True, exist_ok=True)
        photo_id = secrets.token_hex(12)
        path = folder / f'{photo_id}.{extension}'
        with path.open('xb') as f:
            f.write(cleaned)
        row = {'id': photo_id, 'url': f'/uploads/community/{crop}/{path.name}',
               'uploaded_at': datetime.now(timezone.utc).isoformat(timespec='seconds')}
        try:
            all_rows[crop] = records + [row]
            _write(all_rows)
        except Exception:
            path.unlink(missing_ok=True)
            raise
        return row


def photo_path(crop: str, filename: str) -> Path | None:
    if crop not in CROP_IDS or not filename or not filename.isascii():
        return None
    url = f'/uploads/community/{crop}/{filename}'
    if not any(row['url'] == url for row in gallery(crop)):
        return None
    target = (GALLERY_DIR / crop / filename).resolve()
    if not target.is_relative_to(GALLERY_DIR) or not target.is_file():
        return None
    return target
