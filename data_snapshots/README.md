# NASA/NOAA/USDA snapshots

This directory ships **without fabricated measurements**. Run
`python scripts/refresh_snapshots.py` with Internet access to save genuine API
responses. Files are generated only after successful upstream parsing. A missing
snapshot is shown as **unavailable**, never replaced by arbitrary numbers.

On a deployment platform, commit only reviewed, clearly dated data snapshots.
