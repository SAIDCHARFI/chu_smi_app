@echo off
SETLOCAL

REM -------------------------------
REM Define paths
REM -------------------------------
SET VENV_DIR=venv
SET REQUIREMENTS=requirements.txt
SET APP_FILE=main.py
SET USERS_FILE=users.yaml

REM -------------------------------
REM Check Python installation
REM -------------------------------
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed. Please install Python 3.11+.
    pause
    exit /b
)

REM -------------------------------
REM Create users.yaml if it does not exist
REM -------------------------------
IF NOT EXIST "%USERS_FILE%" (
    echo Creating default users.yaml...
    echo usernames: > %USERS_FILE%
    echo "  admin:" >> %USERS_FILE%
    echo "    name: Admin" >> %USERS_FILE%
    echo "    password: admin123" >> %USERS_FILE%
    echo "    role: admin" >> %USERS_FILE%
    echo cookie: >> %USERS_FILE%
    echo "  name: streamlit_auth" >> %USERS_FILE%
    echo "  key: some_secret_key_123" >> %USERS_FILE%
    echo "  expiry_days: 1" >> %USERS_FILE%
)

REM -------------------------------
REM Create virtual environment if it does not exist
REM -------------------------------
IF NOT EXIST "%VENV_DIR%\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv %VENV_DIR%
)

REM -------------------------------
REM Activate virtual environment
REM -------------------------------
CALL "%VENV_DIR%\Scripts\activate.bat"

REM -------------------------------
REM Upgrade pip and install requirements
REM -------------------------------
echo Installing dependencies...
pip install --upgrade pip
pip install -r %REQUIREMENTS%

REM -------------------------------
REM Run Streamlit app
REM -------------------------------
echo Running Streamlit app...
streamlit run %APP_FILE%

ENDLOCAL
pause
