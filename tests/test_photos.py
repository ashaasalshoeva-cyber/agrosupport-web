"""Integration tests using an ephemeral local HTTP server; no network service needed."""
import http.cookiejar
import json
import struct
import sys
import tempfile
import threading
import unittest
import zlib
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, build_opener, HTTPCookieProcessor

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import photo_store
import server


def chunk(marker, data):
    return struct.pack('>I', len(data)) + marker + data + struct.pack('>I', zlib.crc32(marker + data) & 0xFFFFFFFF)


def sample_png():
    width, height = 100, 80
    rgba = b''.join(b'\0' + bytes([35, 130, 55, 255]) * width for _ in range(height))
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(rgba)) + chunk(b'IEND', b'')

class PhotoAdminTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        for obj, attr, value in (
            (photo_store,'DATA_DIR',base/'data'),
            (photo_store,'ADMIN_FILE',base/'data'/'admin.json'),
            (photo_store,'PHOTO_FILE',base/'data'/'crop_photos.json'),
            (photo_store,'UPLOAD_DIR',base/'uploads'/'crops'),
            (server,'UPLOAD_DIR',base/'uploads'/'crops'),
            (server,'ROOT',base),
        ):
            p = patch.object(obj, attr, value); p.start(); self.addCleanup(p.stop)
        photo_store.set_admin_password('very_secure_test_password')
        self.http = ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        self.addCleanup(self.http.server_close)
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.http.shutdown)
        self.baseurl = f'http://127.0.0.1:{self.http.server_port}'
        self.opener = build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))
        with server.LOCK:
            server.SESSIONS.clear();server.LOGIN_FAILS.clear()

    def req(self, path, method='GET', data=None, headers=None, expected=200):
        req = Request(self.baseurl + path, data=data, headers=headers or {}, method=method)
        try:
            response = self.opener.open(req, timeout=4)
        except HTTPError as exc:
            response = exc
        with response:
            raw = response.read()
            self.assertEqual(response.status, expected, (response.status, raw))
            return json.loads(raw) if response.headers.get_content_type() == 'application/json' else raw

    def login(self):
        auth = self.req('/api/admin/login','POST',json.dumps({'password':'very_secure_test_password'}).encode(),{'Content-Type':'application/json'})
        return auth['csrf']

    def test_images_are_private_to_admin_for_write_but_public_for_read(self):
        self.assertEqual(self.req('/api/photos')['photos'], {})
        image = sample_png()
        route = '/api/admin/photos/corn'
        self.req(route, 'PUT', image, {'Content-Type':'image/png'}, 401)
        self.req('/api/admin/login', 'POST', b'{"password":"incorrect"}', {'Content-Type':'application/json'}, 401)
        csrf = self.login()
        self.req(route,'PUT', image,{'Content-Type':'image/png','X-AAIAP-CSRF':'wrong'},403)
        self.req(route,'PUT', b'<svg onload="alert(1)"/>',{'Content-Type':'image/png','X-AAIAP-CSRF':csrf},400)
        response = self.req(route,'PUT',image,{'Content-Type':'image/png','X-AAIAP-CSRF':csrf})
        url=response['photo']['url']
        self.assertTrue(url.startswith('/uploads/crops/corn/'))
        self.assertEqual(self.req('/api/photos')['photos']['corn']['url'], url)
        self.assertEqual(self.req(url), image)
        self.req(route,'PATCH',json.dumps({'focus_x':10,'focus_y':75}).encode(),{'Content-Type':'application/json','X-AAIAP-CSRF':csrf})
        self.assertEqual(self.req('/api/photos')['photos']['corn']['focus_x'],10)
        self.assertEqual(self.req('/api/photos')['photos']['corn']['focus_y'],75)
        self.req('/api/admin/logout','POST',b'',{'X-AAIAP-CSRF':csrf})
        self.req(route,'DELETE',None,{'X-AAIAP-CSRF':csrf},401)
        csrf = self.login()
        self.req(route,'DELETE',None,{'X-AAIAP-CSRF':csrf})
        self.assertNotIn('corn',self.req('/api/photos')['photos'])
        self.req(url,expected=404)

    def test_persistent_metadata_secret_never_public(self):
        csrf=self.login()
        self.req('/api/admin/photos/soybean','PUT',sample_png(),{'Content-Type':'image/png','X-AAIAP-CSRF':csrf})
        self.assertIn('soybean',photo_store.photo_manifest())
        self.req('/data/admin.json', expected=404)
        self.req('/assets/../data/admin.json', expected=404)
        self.req('/data/crop_photos.json', expected=404)
        self.req('/api/admin/photos/corn','PUT',sample_png(),{'Content-Type':'image/png','X-AAIAP-CSRF':csrf,'Origin':'https://evil.example'},403)

    def test_password_reset_invalidates_prior_session(self):
        csrf = self.login()
        self.assertTrue(self.req('/api/admin/status')['authenticated'])
        photo_store.set_admin_password('new_secure_test_password')
        self.assertFalse(self.req('/api/admin/status')['authenticated'])
        self.req('/api/admin/photos/corn', 'PUT', sample_png(),
                 {'Content-Type':'image/png','X-AAIAP-CSRF':csrf}, 401)

    def test_unknown_crop_and_invalid_image(self):
        csrf=self.login()
        self.req('/api/admin/photos/unknown','PUT',sample_png(),{'Content-Type':'image/png','X-AAIAP-CSRF':csrf},404)
        self.req('/api/admin/photos/corn','PUT',b'not-an-image',{'Content-Type':'image/jpeg','X-AAIAP-CSRF':csrf},400)

if __name__ == '__main__':
    unittest.main()
