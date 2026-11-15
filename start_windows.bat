@echo off
cd /d "%~dp0"
echo AAIAP 0.1.1-demo -- local research pilot
echo Open http://127.0.0.1:8000 after the server starts.
py -3 server.py
pause
