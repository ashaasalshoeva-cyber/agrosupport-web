"""Offline tests for public read-only pilot and external-source parsing."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server

class TestScientificSafety(unittest.TestCase):
    def test_verified_site_and_no_fake_field_area(self):
        self.assertEqual(server.SITE['lat'],40.575256)
        self.assertEqual(server.SITE['lon'],-98.137824)
        self.assertIsNone(server.SITE['area_ha'])
        self.assertIn('not an individual field',server.SITE['precision_note'])

    def test_power_monthly_aggregation_and_missing_values(self):
        series={
          'T2M':{'20250101':2,'20250102':4,'20250201':-999,'20250202':5},
          'PRECTOTCORR':{'20250101':1.1,'20250102':2.3,'20250201':-999},
          'ALLSKY_SFC_SW_DWN':{'20250101':1.0,'20250102':3.0},
          'WS2M':{'20250101':5,'20250102':7}
        }
        with patch.object(server,'fetch_json',return_value={'properties':{'parameter':series}}):
            result=server.power_summary()
        jan=result['months'][0]
        self.assertEqual(jan['T2M'],3.0)
        self.assertEqual(jan['PRECTOTCORR'],3.4)
        self.assertEqual(jan['WS2M'],6.0)
        self.assertEqual(result['months'][1]['PRECTOTCORR'],None)
        self.assertEqual(result['months'][1]['T2M'],5.0)

    def test_forecast_only_allows_official_gridpoint_host(self):
        with patch.object(server,'fetch_json',return_value={'properties':{'forecast':'https://example.com/malicious'}}):
            with self.assertRaises(ValueError):server.forecast_summary()

    def test_forecast_real_response_parsing(self):
        responses=[{'properties':{'forecast':'https://api.weather.gov/gridpoints/GID/22,29/forecast'}},
                   {'properties':{'updateTime':'2026-11-14T04:00:00-06:00','periods':[{'name':'Tonight','temperature':30,'temperatureUnit':'F','shortForecast':'Mostly clear','windSpeed':'5 mph','windDirection':'N'}]}}]
        with patch.object(server,'fetch_json',side_effect=responses):
            data=server.forecast_summary()
        self.assertEqual(len(data['periods']),1)
        self.assertEqual(data['periods'][0]['temperature'],30)

    def test_soil_not_lab_npk(self):
        with patch.object(server,'fetch_json',return_value={'Table':[['1','A','Unit One']]}) as fn:
            result=server.soil_summary()
        self.assertEqual(result['map_units'][0]['name'],'Unit One')
        self.assertIn('not soil lab results',result['resolution_note'])
        self.assertIn('POINT(-98.137824 40.575256)',fn.call_args.kwargs['payload']['query'])

    def test_no_old_ownership_endpoints(self):
        self.assertFalse(hasattr(server.Handler, 'handle_claim'))
        self.assertNotIn('claim', server.Handler.do_POST.__code__.co_consts)
        self.assertIn('public-readonly-science', 'public-readonly-science/admin-photos')

if __name__=='__main__':unittest.main()
