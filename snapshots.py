"""Read-only offline fallback from real saved JSON responses, never synthetic data."""
import json
from pathlib import Path
from datetime import datetime, timezone
SNAP_DIR=Path(__file__).resolve().parent/'data_snapshots'
VALID={'power','forecast','soil','season','modis'}

def read_snapshot(name):
    if name not in VALID: return None
    p=SNAP_DIR/f'{name}.json'
    if not p.is_file(): return None
    try:
        row=json.loads(p.read_text('utf-8'))
        if (row.get('verified_source') is not True or not isinstance(row.get('data'),dict)
            or not row.get('retrieved_at') or not row.get('source_url')): return None
        return {**row['data'],'snapshot':True,'snapshot_retrieved_at':row['retrieved_at'],
                'data_status':'offline-real-snapshot','snapshot_source':row['source_url']}
    except (OSError,ValueError,TypeError): return None

def write_snapshot(name, data, source_url):
    if name not in VALID: raise ValueError('invalid snapshot type')
    SNAP_DIR.mkdir(exist_ok=True)
    row={'verified_source':True,'retrieved_at':datetime.now(timezone.utc).isoformat(),
         'source_url':source_url,'data':data}
    target=SNAP_DIR/f'{name}.json';temp=target.with_suffix('.tmp')
    temp.write_text(json.dumps(row,ensure_ascii=False,indent=2),encoding='utf-8');temp.replace(target)
