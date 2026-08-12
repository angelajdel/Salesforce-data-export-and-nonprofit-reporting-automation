@echo off
REM Double-click this file to pull fresh Salesforce data and open Impact Hub
REM -- no GitHub, no command line typing required beyond double-clicking this.
cd /d "%~dp0"
python run_local.py
echo.
pause
