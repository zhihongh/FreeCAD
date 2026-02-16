@echo off
REM =================================================================
REM Discord Message Downloader - Windows Scheduled Task Runner
REM =================================================================
REM
REM This batch file is designed to be used with Windows Task Scheduler
REM to periodically download Discord messages.
REM
REM Setup Steps:
REM   1. Edit the PYTHON_PATH and SCRIPT_DIR variables below
REM   2. Open Task Scheduler (taskschd.msc)
REM   3. Create Basic Task -> set trigger (e.g., every 6 hours)
REM   4. Action: Start a Program -> Browse to this .bat file
REM   5. Check "Run whether user is logged on or not"
REM
REM =================================================================

REM --- Configuration ---
REM Set this to your Python executable path (or just "python" if it's in PATH)
SET PYTHON_PATH=python

REM Set this to the directory containing discord_downloader.py
SET SCRIPT_DIR=%~dp0

REM --- Run the downloader ---
cd /d "%SCRIPT_DIR%"

echo [%date% %time%] Starting Discord download... >> download_log.txt
%PYTHON_PATH% discord_downloader.py --last-run >> download_log.txt 2>&1
echo [%date% %time%] Download finished (exit code: %ERRORLEVEL%) >> download_log.txt
echo. >> download_log.txt
