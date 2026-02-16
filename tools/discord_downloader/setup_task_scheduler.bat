@echo off
REM =================================================================
REM Auto-setup Windows Task Scheduler for Discord Downloader
REM =================================================================
REM Run this script as Administrator to create a scheduled task
REM that runs the Discord downloader every 6 hours.
REM =================================================================

SET TASK_NAME=DiscordMessageDownloader
SET SCRIPT_PATH=%~dp0run_download.bat

echo Creating scheduled task: %TASK_NAME%
echo Script: %SCRIPT_PATH%
echo Schedule: Every 6 hours
echo.

schtasks /create /tn "%TASK_NAME%" /tr "\"%SCRIPT_PATH%\"" /sc HOURLY /mo 6 /f

if %ERRORLEVEL% == 0 (
    echo.
    echo Task created successfully!
    echo.
    echo To verify: schtasks /query /tn "%TASK_NAME%"
    echo To delete:  schtasks /delete /tn "%TASK_NAME%" /f
    echo To run now: schtasks /run /tn "%TASK_NAME%"
) else (
    echo.
    echo Failed to create task. Try running this script as Administrator.
)

pause
