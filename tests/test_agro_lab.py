"""Regression tests for NASA and nutrient balance, no external API needed."""
import contextlib
import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from datetime import date,timedelta
from http.server import ThreadingHTTPServer
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request,urlopen
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import agro_lab,agro_nasa,agro_ai,server

DEMO={'area_ha':5,'yield_t_ha':5,'straw_ratio':1.1,'straw_exported':False,
      'mineral_kg_ha':{'N':95,'P2O5':35,'K2O':25},'organic_kg_ha':{'N':10,'P2O5':5,'K2O':10},
      'estimated_loss_kg_ha':{'N':15,'P2O5':0,'K2O':0}}

def response(start='2025-03-01',days=3):
    values={p:{} for p in agro_nasa.PARAMS}
    for i in range(days):
        day=(date.fromisoformat(start)+timedelta(days=i)).strftime('%Y%m%d')
        for k,v in [('T2M',10+i),('T2M_MAX',14+i),('T2M_MIN',4+i),('RH2M',50),('PRECTOTCORR',1+i),('WS2M',2),('ALLSKY_SFC_SW_DWN',4)]:values[k][day]=v
    return {'properties':{'parameter':values}}

class NPKTests(unittest.TestCase):
    def test_straw_export_increases_removal(self):
        on=agro_lab.calculate_balance({**DEMO,'straw_exported':True})
        off=agro_lab.calculate_balance(DEMO)
        self.assertEqual(off['elements']['N']['balance_kg_ha'],-20)
        self.assertEqual(off['elements']['P2O5']['balance_kg_ha'],-5)
        self.assertEqual(off['elements']['K2O']['balance_kg_ha'],5)
        self.assertAlmostEqual(on['elements']['K2O']['balance_kg_ha'],5-5*1.1*15)
        self.assertEqual(on['elements']['K2O']['balance_total_kg'],round(on['elements']['K2O']['balance_kg_ha']*5,2))

    def test_invalid_values_cannot_pass(self):
        for bad in [None,True,float('nan'),float('inf'),-1,1000000]:
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                agro_lab.calculate_balance({**DEMO,'yield_t_ha':bad})
        with self.assertRaises(ValueError):agro_lab.calculate_balance({**DEMO,'straw_exported':'yes'})

    def test_advice_without_nasa_discloses_missing_data(self):
        text=agro_lab.basic_advice(agro_lab.calculate_balance(DEMO))
        self.assertIn('NASA не загружены',text)
        self.assertIn('N 20.0 кг/га',text)

class NASATests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.store=patch.object(agro_nasa,'STORE',Path(self.tmp.name));self.store.start()
        agro_nasa.MEM.clear()
    def tearDown(self):
        self.store.stop();self.tmp.cleanup();agro_nasa.MEM.clear()

    def test_request_validation(self):
        self.assertEqual(agro_nasa.parse_request({'lat':'38.5598','lon':'68.7870','start':'2025-03-01','end':'2025-03-03'})[0],38.5598)
        for invalid in [
           {'lat':'90.01','lon':'68.7','start':'2025-03-01','end':'2025-03-03'},
           {'lat':'38','lon':'181','start':'2025-03-01','end':'2025-03-03'},
           {'lat':'38','lon':'68','start':'2025-03-03','end':'2025-03-01'},
           {'lat':'38','lon':'68','start':'2024-01-01','end':'2025-03-03'},
           {'lat':'38','lon':'68','start':'2027-01-01','end':'2027-02-01'}]:
            with self.subTest(invalid=invalid),self.assertRaises(ValueError):agro_nasa.parse_request(invalid)

    def test_live_real_saved_then_reused_without_request(self):
        fetches=[]
        def fetch(url,**kw):fetches.append(url);return response()
        args=(38.56,68.79,'2025-03-01','2025-03-03')
        data=agro_nasa.get_weather(*args,fetch)
        self.assertFalse(data['snapshot']);self.assertEqual(data['totals']['rain_mm'],6)
        self.assertEqual(data['totals']['temperature_mean_c'],11)
        self.assertEqual(len(fetches),1)
        self.assertTrue(agro_nasa.cache_path(*args).exists())
        agro_nasa.MEM.clear()
        reused=agro_nasa.get_weather(*args,lambda *a,**kw:(_ for _ in ()).throw(RuntimeError('network down')))
        self.assertTrue(reused['snapshot']);self.assertEqual(reused['data_status'],'verified-stored-snapshot')

    def test_ag_solar_units_are_converted_to_kwh(self):
        raw=response()
        raw['parameters']={'ALLSKY_SFC_SW_DWN': {'units':'MJ/m^2/day'}}
        result=agro_nasa.transform(raw,38,68,'2025-03-01','2025-03-03',agro_nasa.SOURCE+'?test=1')
        self.assertAlmostEqual(result['monthly'][0]['ALLSKY_SFC_SW_DWN'],1.11,places=2)
        raw['parameters']['ALLSKY_SFC_SW_DWN']['units']='kW-hr/m^2/day'
        result=agro_nasa.transform(raw,38,68,'2025-03-01','2025-03-03',agro_nasa.SOURCE+'?test=1')
        self.assertEqual(result['monthly'][0]['ALLSKY_SFC_SW_DWN'],4)

    def test_missing_not_invented(self):
        x=response()
        x['properties']['parameter']['PRECTOTCORR']['20250302']=-999
        d=agro_nasa.transform(x,38,68,'2025-03-01','2025-03-03','https://power.larc.nasa.gov/api/temporal/daily/point?test=1')
        self.assertIsNone(d['totals']['rain_mm'])
        self.assertIsNone(d['daily'][1]['PRECTOTCORR'])
        self.assertEqual(d['valid_days']['PRECTOTCORR'],2)

    def test_broken_remote_not_saved(self):
        with self.assertRaises(ValueError):agro_nasa.get_weather(38,68,'2025-03-01','2025-03-03',lambda *a,**kw:{})
        self.assertEqual(list(Path(self.tmp.name).glob('agro_weather*')),[])

class APITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        cls.thread=threading.Thread(target=cls.httpd.serve_forever,daemon=True)
        cls.thread.start();cls.base='http://127.0.0.1:'+str(cls.httpd.server_address[1])
    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown();cls.httpd.server_close();cls.thread.join(2)
    def request(self,path,payload):
        req=Request(self.base+path,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
        with urlopen(req,timeout=10) as r:return json.load(r)

    def test_balance_and_offline_advice(self):
        result=self.request('/api/agro/balance',{'balance':DEMO})
        self.assertEqual(result['elements']['N']['balance_kg_ha'],-20)
        with patch.dict(os.environ,{'OPENAI_API_KEY':''}):
            advice=self.request('/api/agro/advice',{'balance':DEMO})
        self.assertFalse(advice['ai_used']);self.assertEqual(advice['mode'],'template')
        self.assertFalse(advice['weather_used'])
    def test_nasa_endpoint_uses_validated_series(self):
        test_response=agro_nasa.transform(response(),38.5598,68.787,'2025-03-01','2025-03-03',agro_nasa.SOURCE+'?parameters=ok')
        with patch.object(server,'get_agro_weather',return_value=test_response):
            with urlopen(self.base+'/api/agro/weather?lat=38.5598&lon=68.7870&start=2025-03-01&end=2025-03-03',timeout=10) as r:row=json.load(r)
        self.assertEqual(row['totals']['rain_mm'],6)
        with self.assertRaises(HTTPError) as ctx:urlopen(self.base+'/api/agro/weather?lat=3800&lon=68.7870&start=2025-03-01&end=2025-03-03')
        self.assertEqual(ctx.exception.code,400)
    def test_static_tools_accessible_and_server_private(self):
        for path in ['/tools/agro-lab.html','/tools/agro-lab.js','/tools/agro-lab.css','/tools/wheat-water.html']:
            with urlopen(self.base+path) as r:self.assertEqual(r.status,200)
        with self.assertRaises(HTTPError) as ctx:urlopen(self.base+'/agro_ai.py')
        self.assertEqual(ctx.exception.code,404)

if __name__=='__main__':unittest.main()
