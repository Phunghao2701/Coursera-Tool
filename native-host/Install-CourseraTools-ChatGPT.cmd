@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" -Browser Edge
set "installExitCode=%ERRORLEVEL%"
if not "%installExitCode%"=="0" (
    echo.
    echo Setup did not finish. Review the message above and try again.
    pause
    exit /b %installExitCode%
)
echo.
echo Setup is complete. Reload Coursera Tools in Edge.
pause
exit /b 0
