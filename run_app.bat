@echo off
REM Activate virtual environment
call "%~dp0\venv\Scripts\activate.bat"

REM Run the Streamlit launcher
python "%~dp0run_app.py"

pause