@echo off
echo Starting Church Registry System...
echo.

cd /d "%~dp0"

call venv\Scripts\activate.bat

echo Running migrations...
python manage.py migrate --run-syncdb

echo.
echo Starting server...
echo Open your browser and go to: http://127.0.0.1:8000
echo Press CTRL+C to stop the server.
echo.

python manage.py runserver

pause
