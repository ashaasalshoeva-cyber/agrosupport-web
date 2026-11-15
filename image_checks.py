"""Small dependency-free image signature and dimension validators."""
from __future__ import annotations
import struct
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_IMAGE_PIXELS = 24_000_000
CROP_IDS = frozenset(('wheat','cotton','corn','barley','tomato','potato','rice','alfalfa','sunflower','soybean','apple','apricot','grape','chickpea'))
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


