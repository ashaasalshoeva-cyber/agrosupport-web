"""v0.2.1 regression tests - no network dependency."""
import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server,science

class V021Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        cls.base='http://127.0.0.1:'+str(cls.http.server_port)
        cls.thread=threading.Thread(target=cls.http.serve_forever,daemon=True);cls.thread.start()
    @classmethod
    def tearDownClass(cls):cls.http.shutdown();cls.http.server_close()
    def read(self,path):
        with urlopen(self.base+path,timeout=5) as r:return r, r.read()
    def test_science_routes_and_legacy_data(self):
        for path in ['/api/science/sites','/api/science/evidence?site=TJK-SUG-001&crop=corn',
                     '/api/science/twin?site=TJK-SUG-001','/api/science/modis?site=USA-NE-SCAL',
                     '/api/data/power','/api/health']:
            with self.subTest(path=path):
                _,data=self.read(path);self.assertTrue(json.loads(data))
    def test_tools_and_security(self):
        for name in ['agro-lab.html','wheat-water.html','npk-original.html']:
            r,data=self.read('/tools/'+name+'?embed=1')
            self.assertIn(b'embedded',data);self.assertEqual(r.headers['X-Frame-Options'],'SAMEORIGIN')
            self.assertIn("frame-ancestors 'self'",r.headers['Content-Security-Policy'])
            self.assertIn('https://power.larc.nasa.gov',r.headers['Content-Security-Policy'])
    def test_snapshot_and_months(self):
        with patch.object(science,'request_json',side_effect=OSError('offline')):
            result=science.bundle('TJK-SUG-001','corn')
        self.assertEqual(result['status'],'available')
        self.assertEqual(result['provenance']['delivery'],'snapshot')
        self.assertEqual(len(result['monthly']['last_complete_year']),12)
        self.assertEqual(len(result['monthly']['baseline_10_years']),12)
    def test_solar_unit_conversion(self):
        # Verify both source unit variants are treated distinctly.
        sample={'properties':{'parameter':{k:{'20250101':10} for k in server.POWER_PARAMS}},
                'parameters':{'ALLSKY_SFC_SW_DWN':{'units':'MJ/m²/day'}}}
        with patch.object(server,'fetch_json',return_value=sample):
            a=server.power_summary()['months'][0]['ALLSKY_SFC_SW_DWN']
        sample['parameters']['ALLSKY_SFC_SW_DWN']['units']='kWh/m²/day'
        with patch.object(server,'fetch_json',return_value=sample):
            b=server.power_summary()['months'][0]['ALLSKY_SFC_SW_DWN']
        self.assertAlmostEqual(a,10/3.6,places=2);self.assertEqual(b,10.0)
    def test_readable_validation(self):
        r,data=self.read('/assets/validation.json');v=json.loads(data)
        self.assertIn('PRECTOTCORR_monthly',v['metrics'])
        r,data=self.read('/docs/validation_report.md');self.assertGreater(len(data),100)

if __name__=='__main__':unittest.main()
