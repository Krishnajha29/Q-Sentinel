@echo off
title Q-sentinel // Tactical Situational Awareness & RF Command Workstation
color 0B
echo =======================================================================
echo   Q-Sentinel: ADAPTIVE ELECTRONIC SUPPORT & SITUATIONAL AWARENESS
echo    Unified Multi-Sensor Defence Command & Control Workstation 
echo =======================================================================
echo.

cd /d "%~dp0"

IF NOT EXIST "node_modules" (
    echo [INFO] First time setup: Installing server dependencies...
    call npm.cmd install
)

echo [INFO] Starting Q-Sentinel Workstation Server on http://localhost:8080 ...
start "" "http://localhost:8080"
node server.js

pause
