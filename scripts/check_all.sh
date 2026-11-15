#!/usr/bin/env sh
set -eu
python -m compileall -q server.py agro_calc.py assistant_template.py snapshots.py
python -m unittest discover -s tests -v
if command -v node >/dev/null 2>&1; then
 for f in js/*.js; do node --check "$f"; done
fi
printf 'All checks completed\n'
