@echo off
echo Starting J.A.R.V.I.S V3.1...
cd /d C:\Users\badge\JarvisV3.1
start "Jarvis Server" python core/server.py
timeout /t 3 /nobreak >nul
cd client
npm start
