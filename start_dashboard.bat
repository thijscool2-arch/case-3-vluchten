@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Installeer eerst Python 3.12 vanaf python.org en probeer opnieuw.
  pause
  exit /b 1
)
if not exist .venv py -3.12 -m venv .venv
if not exist .venv\Scripts\python.exe (
  echo Python 3.12 is nodig. Installeer die versie en probeer opnieuw.
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m streamlit run app.py
pause
