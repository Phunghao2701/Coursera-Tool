@echo off
chcp 65001 > nul
cd /d "c:\Users\LENOVO\Desktop\tool coursera"

set PYTHONUTF8=1

:: Tim lenh Python
set PY_CMD=
python --version >nul 2>&1 && set PY_CMD=python && goto :run
py --version >nul 2>&1 && set PY_CMD=py && goto :run
python3 --version >nul 2>&1 && set PY_CMD=python3 && goto :run

echo LOI: Khong tim thay Python! Chay setup.bat truoc.
pause
exit /b 1

:run
%PY_CMD% launcher.py
