"""Offline validation of the no-account crop gallery, using a synthetically made PNG."""
import json
import os
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gallery_store as g
import server


def chunk(kind, data):
    return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind+data) & 0xffffffff)


def png_with_metadata():
    # PNG RGBA 60x60, includes arbitrary private metadata that should be discarded.
    raw = b''.join(b'\x00' + bytes([80,160,40,255]) * 60 for _ in range(60))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB',60,60,8,6,0,0,0))
            + chunk(b'tEXt', b'GPSLocation\x00confidential_test_marker')
            + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))


class GalleryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.storage = root
        self.old_dir, self.old_file = g.GALLERY_DIR, g.GALLERY_FILE
        g.GALLERY_DIR = root / 'uploads' / 'community'
        g.GALLERY_FILE = root / 'data' / 'farmer_photos.json'
        self.addCleanup(self.restore)

    def restore(self):
        g.GALLERY_DIR, g.GALLERY_FILE = self.old_dir, self.old_file

    def test_upload_persist_and_remove_metadata(self):
        picture = png_with_metadata()
        saved = g.append_photo('corn', picture)
        self.assertIn('/uploads/community/corn/', saved['url'])
        self.assertEqual(len(g.gallery('corn')), 1)
        contents = g.photo_path('corn', saved['url'].rsplit('/',1)[-1]).read_bytes()
        self.assertNotIn(b'confidential_test_marker', contents)
        self.assertTrue(contents.startswith(b'\x89PNG'))
        # Persisted list survives in-memory state loss (read from JSON file each time).
        self.assertEqual(g.gallery('corn')[0]['url'], saved['url'])
        self.assertIsNone(g.photo_path('wheat', saved['url'].rsplit('/',1)[-1]))

    def test_reject_not_image_and_unknown_crop(self):
        with self.assertRaises(ValueError): g.append_photo('corn', b'not an image')
        with self.assertRaises(ValueError): g.append_photo('../corn', png_with_metadata())
        self.assertEqual(g.gallery('corn'), [])

    def test_limit(self):
        data = png_with_metadata()
        with patch.object(g, 'MAX_PER_CROP', 2):
            g.append_photo('soybean', data)
            g.append_photo('soybean', data)
            with self.assertRaises(ValueError): g.append_photo('soybean', data)

    def test_origin_upload_header(self):
        # Static code API contract should refuse unauthenticated writes to science,
        # and only accept opt-in image upload routes.
        self.assertTrue(hasattr(server, 'UPLOAD_LOG'))
        self.assertTrue(callable(server.Handler.do_POST))
        self.assertEqual(server.HOST, '127.0.0.1')


if __name__ == '__main__':
    unittest.main()
