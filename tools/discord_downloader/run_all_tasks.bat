@echo off
REM =================================================================
REM Combined Task Runner - WeChat + Discord Download
REM =================================================================
REM
REM This batch file runs the unified task runner, which executes all
REM configured tasks (WeChat exe + Discord download) in sequence.
REM
REM Setup:
REM   1. Edit tasks_config.json to set your exe paths and channels
REM   2. Set up .env with DISCORD_BOT_TOKEN
REM   3. Run setup_scheduled_tasks.bat as Administrator to auto-schedule
REM      OR manually add this .bat to Windows Task Scheduler
REM
REM =================================================================

SET PYTHON_PATH=python
SET SCRIPT_DIR=%~dp0

cd /d "%SCRIPT_DIR%"

echo ============================================================
echo [%date% %time%] Starting all download tasks...
echo ============================================================

%PYTHON_PATH% task_runner.py

echo.
echo [%date% %time%] All tasks finished (exit code: %ERRORLEVEL%)
echo.
