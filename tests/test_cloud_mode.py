import contextlib,threading,unittest,json
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request,urlopen
from unittest.mock import patch
import server

class CloudDemoHttpTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.httpd=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
  cls.port=cls.httpd.server_address[1]
  cls.thread=threading.Thread(target=cls.httpd.serve_forever,daemon=True);cls.thread.start()
 @classmethod
 def tearDownClass(cls):
  cls.httpd.shutdown();cls.httpd.server_close();cls.thread.join(timeout=2)
 def url(self,path):return f'http://127.0.0.1:{self.port}{path}'
 def test_health_and_head_are_ready(self):
  with patch.object(server,'CLOUD',True),patch.object(server,'MODE','cloud-demo'):
   with urlopen(self.url('/api/health')) as r:
    data=json.load(r);self.assertEqual(data['mode'],'cloud-demo')
    self.assertEqual(data['version'],server.VERSION)
   with urlopen(Request(self.url('/'),method='HEAD')) as r:self.assertEqual(r.status,200)
 def test_cloud_admin_and_community_upload_are_blocked(self):
  with patch.object(server,'CLOUD',True):
   for path in ['/api/admin/login','/api/community/photos/corn']:
    request=Request(self.url(path),data=b'{}',method='POST',headers={'Content-Type':'application/json'})
    with self.assertRaises(HTTPError) as ctx:urlopen(request)
    self.assertEqual(ctx.exception.code,403)
   with urlopen(self.url('/api/community/photos?crop=corn')) as r:
    self.assertEqual(json.load(r)['photos'],[])
 def test_template_summary_work_without_external_requests(self):
  with patch.object(server,'CLOUD',True),patch.object(server,'CACHE',{}):
   data=json.dumps({'site_id':'USA-NE-SCAL','crop':'corn','lang':'en'}).encode()
   with urlopen(Request(self.url('/api/assistant/summary'),data=data,
          method='POST',headers={'Content-Type':'application/json'})) as r:
    response=json.load(r)
    self.assertEqual(response['mode'],'template')
    self.assertFalse(response['ai_used'])

if __name__=='__main__':unittest.main()
