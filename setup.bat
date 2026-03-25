@echo off
echo ============================================
echo  Church Registry System - First Time Setup
echo ============================================
echo.

cd /d "%~dp0"

echo [1/4] Creating virtual environment...
python -m venv venv

echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/4] Installing required packages...
pip install -r requirements.txt

echo [4/4] Running database migrations...
python manage.py migrate --run-syncdb

echo.
echo ============================================
echo  Setup complete!
echo  Now create your admin login:
echo ============================================
python manage.py createsuperuser

echo.
echo Done! Run start.bat to launch the system.
pause
