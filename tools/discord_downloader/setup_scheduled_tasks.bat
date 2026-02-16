@echo off
REM =================================================================
REM Auto-setup Windows Task Scheduler
REM Runs WeChat + Discord download tasks together on a schedule
REM =================================================================
REM Run this script as Administrator!
REM =================================================================

SET TASK_NAME=WeChatDiscordDownloader
SET SCRIPT_PATH=%~dp0run_all_tasks.bat

echo.
echo ============================================================
echo   Scheduled Task Setup / 定时任务设置
echo ============================================================
echo.
echo Task Name:  %TASK_NAME%
echo Script:     %SCRIPT_PATH%
echo.

:MENU
echo Choose schedule / 选择运行频率:
echo   1. Every 1 hour   / 每1小时
echo   2. Every 3 hours  / 每3小时
echo   3. Every 6 hours  / 每6小时 (recommended / 推荐)
echo   4. Every 12 hours / 每12小时
echo   5. Once a day     / 每天一次
echo   6. Cancel          / 取消
echo.
set /p CHOICE=Enter choice (1-6) / 输入选择: 

if "%CHOICE%"=="1" (
    set INTERVAL=1
    set SCHEDULE_TYPE=HOURLY
    set SCHEDULE_DESC=每1小时
) else if "%CHOICE%"=="2" (
    set INTERVAL=3
    set SCHEDULE_TYPE=HOURLY
    set SCHEDULE_DESC=每3小时
) else if "%CHOICE%"=="3" (
    set INTERVAL=6
    set SCHEDULE_TYPE=HOURLY
    set SCHEDULE_DESC=每6小时
) else if "%CHOICE%"=="4" (
    set INTERVAL=12
    set SCHEDULE_TYPE=HOURLY
    set SCHEDULE_DESC=每12小时
) else if "%CHOICE%"=="5" (
    set INTERVAL=1
    set SCHEDULE_TYPE=DAILY
    set SCHEDULE_DESC=每天一次
) else if "%CHOICE%"=="6" (
    echo Cancelled.
    goto :END
) else (
    echo Invalid choice. / 无效选择
    goto :MENU
)

echo.
echo Creating task: %SCHEDULE_DESC%...

schtasks /create /tn "%TASK_NAME%" /tr "\"%SCRIPT_PATH%\"" /sc %SCHEDULE_TYPE% /mo %INTERVAL% /f

if %ERRORLEVEL% == 0 (
    echo.
    echo ============================================================
    echo   Task created successfully! / 定时任务创建成功！
    echo ============================================================
    echo.
    echo   Schedule:  %SCHEDULE_DESC%
    echo   Task Name: %TASK_NAME%
    echo.
    echo   Useful commands / 常用命令:
    echo     View:   schtasks /query /tn "%TASK_NAME%"
    echo     Run:    schtasks /run /tn "%TASK_NAME%"
    echo     Delete: schtasks /delete /tn "%TASK_NAME%" /f
    echo.
) else (
    echo.
    echo FAILED! Please run this script as Administrator.
    echo 失败！请以管理员身份运行此脚本。
)

:END
pause
