import unittest
from unittest.mock import patch
from agro_calc import gdd_day, summarize_daily, climate_twin
from assistant_template import summary
from snapshots import read_snapshot
import server

class AgroScienceTests(unittest.TestCase):
 def test_gdd_clamps_corn_limits(self):
  self.assertEqual(gdd_day(35,5),10)
  self.assertEqual(gdd_day(20,10),5)
  self.assertEqual(gdd_day(-999,10),None)
  self.assertEqual(gdd_day(4,-5),0)

 def test_daily_measures_never_impute_nasa_fill(self):
  data={'T2M_MAX':{'20250501':35,'20250502':-999},'T2M_MIN':{'20250501':5,'20250502':8},
        'T2M':{'20250501':20,'20250502':-999},'PRECTOTCORR':{'20250501':7,'20250502':-999}}
  x=summarize_daily(data,2025)
  self.assertEqual(x['gdd_corn_c'],10)
  self.assertEqual(x['gdd_days'],1)
  self.assertEqual(x['rain_mm'],7)
  self.assertEqual(x['rain_days'],1)
  self.assertLess(x['coverage_fraction'],.01)

 def test_similarity_only_if_complete(self):
  a={'tmean_c':22,'rain_mm':400,'gdd_corn_c':1200,'days_over_30c':60}
  self.assertEqual(climate_twin(a,a)['score'],100)
  self.assertIsNone(climate_twin(a,{}).get('score'))

 def test_template_is_honest_and_no_recommendation_doses(self):
  v=summary({'site_id':'USA-NE-SCAL','season':{'valid_days':365}},'ru')
  self.assertEqual(v['mode'],'template');self.assertIn('NASA POWER',v['summary'])
  self.assertNotIn('кг/га',v['summary'])

 def test_no_shipped_fabricated_snapshot(self):
  self.assertIsNone(read_snapshot('unknown-key'))
  self.assertIsNone(read_snapshot('season'))

 def test_real_source_parsing_from_mocked_api(self):
  params={'T2M_MAX':{'20250401':20},'T2M_MIN':{'20250401':10},
          'T2M':{'20250401':15},'PRECTOTCORR':{'20250401':2}}
  with patch.object(server,'_power_daily_at',return_value=params):
   x=server.season_summary()
  self.assertEqual(x['indicators']['gdd_corn_c'],5)
  self.assertEqual(x['source'],'NASA POWER')

 def test_cloud_mode_has_no_upload_or_admin(self):
  self.assertFalse(server.CLOUD) # ordinary local tests load local mode
  self.assertIn('cloud-demo',open('server.py',encoding='utf-8').read())

if __name__=='__main__':unittest.main()
