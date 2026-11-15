import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import server
import snapshots

class NasaPersistenceTests(unittest.TestCase):
    def test_successful_power_ingestion_is_persisted_and_recoverable(self):
        sample={'source':'NASA POWER','source_url':'https://power.larc.nasa.gov/', 'retrieved_at':'2026-11-15T00:00:00+00:00', 'reference_year':2025,'months':[{'month':1,'T2M':3.2}]}
        with tempfile.TemporaryDirectory() as folder, patch.object(snapshots,'SNAP_DIR',Path(folder)),patch.object(server,'write_snapshot',snapshots.write_snapshot),patch.object(server,'CACHE',{}):
            response=server.cached('power',3600,lambda:sample)
            self.assertEqual(response,sample)
            saved=snapshots.read_snapshot('power')
            self.assertTrue(saved['snapshot'])
            self.assertEqual(saved['months'][0]['T2M'],3.2)
            with self.assertRaises(OSError):server.cached('power_failed',3600,lambda: (_ for _ in ()).throw(OSError('network')))
            self.assertEqual(snapshots.read_snapshot('power')['months'][0]['T2M'],3.2)

if __name__=='__main__':unittest.main()
