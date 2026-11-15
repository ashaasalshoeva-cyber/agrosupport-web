#!/usr/bin/env python3
"""Install independently chosen crop images into Git-tracked public assets.

Usage: python scripts/add_crop_images.py corn --card photo.webp --detail closeup.jpg --background field.jpg
Only local files; does not upload to GitHub or operate a public upload endpoint.
"""
import argparse
import re
import shutil
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from photo_store import CROP_IDS, inspect_image  # matches the actual site's image signature/dimension checks

parser=argparse.ArgumentParser(description='Copy public crop images and update JS manifest for GitHub')
parser.add_argument('crop',choices=sorted(CROP_IDS))
for x in ('card','detail','background'):
    parser.add_argument('--'+x,type=Path,help='JPEG, PNG or WebP file to publish for '+x)
args=parser.parse_args()
if not any(getattr(args,s) for s in ('card','detail','background')):
    parser.error('Provide at least one of --card, --detail or --background')
manifest_path=ROOT/'js'/'crop-images.js'
manifest=manifest_path.read_text(encoding='utf-8')
pattern=r'(?m)^(\s*'+re.escape(args.crop)+r'\s*:\s*\{)([^}]*)(\},?)$'
m=re.search(pattern,manifest)
if not m:
    raise SystemExit('Cannot find crop in manifest')
properties={k:v for k,v in re.findall(r"(card|detail|background):'([^']*)'",m.group(2))}
for slot in ('card','detail','background'):
    file=getattr(args,slot)
    if file is None:
        continue
    raw=file.read_bytes()
    extension=inspect_image(raw)
    folder=ROOT/'assets'/'crops'/args.crop
    folder.mkdir(parents=True,exist_ok=True)
    output=folder/(slot+'.'+extension)
    output.write_bytes(raw)
    properties[slot]='./assets/crops/'+args.crop+'/'+output.name
    print('Added',output.relative_to(ROOT))
body=", ".join(f"{slot}:'{properties.get(slot,'')}'" for slot in ('card','detail','background'))
manifest=manifest[:m.start()]+m.group(1)+body+m.group(3)+manifest[m.end():]
manifest_path.write_text(manifest,encoding='utf-8')
print('Updated js/crop-images.js — commit changed files to GitHub to publish.')
