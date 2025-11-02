@echo off
REM CCTV Local Recording Client Installation Script for Windows
REM This script installs the CCTV local recording client on Windows

setlocal enabledelayedexpansion

echo ===================================
echo CCTV Local Recording Client Setup
echo ===================================
echo.

REM Check if running as Administrator (optional for Windows)
net session >nul 2>&1
if %errorLevel% == 0 (
    echo WARNING: Running as Administrator. This is optional for Windows.
    echo.
)

REM Check Python installation
echo Checking Python version...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found Python !PYTHON_VERSION!

REM Verify Python version
python -c "import sys; assert sys.version_info >= (3,8)" 2>nul
if %errorLevel% neq 0 (
    echo ERROR: Python 3.8 or higher is required
    pause
    exit /b 1
)

REM Installation directory (using user's AppData)
set INSTALL_DIR=%LOCALAPPDATA%\CCTV-Client
echo.
echo Installation directory: !INSTALL_DIR!
echo.

REM Create installation directory
if not exist "!INSTALL_DIR!" (
    echo Creating installation directory...
    mkdir "!INSTALL_DIR!"
)

REM Copy files (copy current directory contents)
echo.
echo Copying files...
xcopy /E /I /Y . "!INSTALL_DIR!\" >nul
cd /d "!INSTALL_DIR!"

REM Create virtual environment
echo.
echo Creating virtual environment...
python -m venv venv
if %errorLevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip --quiet
if %errorLevel% neq 0 (
    echo ERROR: Failed to upgrade pip
    pause
    exit /b 1
)

REM Install dependencies
echo.
echo Installing dependencies...
pip install -r requirements.txt --quiet
if %errorLevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

REM Create directories
echo.
echo Creating directories...
if not exist "recordings\recordings" mkdir recordings\recordings
if not exist "recordings\logs" mkdir recordings\logs
if not exist "recordings\cache" mkdir recordings\cache
if not exist "recordings\pending_uploads" mkdir recordings\pending_uploads

REM Setup configuration
echo.
if not exist ".env" (
    echo Creating .env file...
    if exist ".env.example" (
        copy /Y .env.example .env >nul
    ) else (
        REM Create basic .env file
        (
            echo # Backend API Configuration
            echo BACKEND_API_URL=http://localhost:8000
            echo.
            echo # Client Authentication ^(REQUIRED^)
            echo # Get CLIENT_TOKEN from Django Admin -^> Local Recording Clients
            echo CLIENT_TOKEN=
            echo CLIENT_ID=
            echo.
            echo # GCP Storage Configuration
            echo GCP_CREDENTIALS_PATH=
            echo GCP_BUCKET_NAME=cctv_feed
            echo GCP_PROJECT_ID=learningdevops-455404
            echo.
            echo # Recording Settings
            echo RECORDING_BASE_DIR=./recordings
            echo CLEANUP_AFTER_UPLOAD=true
            echo KEEP_LOCAL_DAYS=1
            echo MAX_CONCURRENT_RECORDINGS=4
            echo.
            echo # Sync Settings
            echo SYNC_INTERVAL_SECONDS=30
            echo HEARTBEAT_INTERVAL_SECONDS=60
            echo MAX_RETRY_ATTEMPTS=5
            echo.
            echo # System Settings
            echo LOG_LEVEL=INFO
            echo TIME_ZONE=Asia/Kolkata
        ) > .env
    )
    echo.
    echo ====================================
    echo Configuration Setup Required
    echo ====================================
    echo.
    echo Please edit the .env file with your configuration:
    echo Location: !INSTALL_DIR!\.env
    echo.
    echo Required Settings:
    echo   - BACKEND_API_URL: Backend API URL ^(default: http://localhost:8000^)
    echo   - CLIENT_TOKEN: Authentication token from Django admin ^(REQUIRED^)
    echo   - GCP_CREDENTIALS_PATH: Path to GCP service account JSON file
    echo   - GCP_BUCKET_NAME: GCP storage bucket ^(default: cctv_feed^)
    echo   - GCP_PROJECT_ID: GCP project ID ^(default: learningdevops-455404^)
    echo.
    echo To get CLIENT_TOKEN and CLIENT_ID:
    echo   1. Go to Django Admin -^> CCTV -^> Local Recording Clients
    echo   2. Create a new client or view existing client
    echo   3. Copy the client_token ^(REQUIRED^)
    echo   4. Copy the UUID id field as CLIENT_ID ^(optional^)
    echo.
    echo Optional Settings:
    echo   - RECORDING_BASE_DIR: Directory for recordings
    echo   - CLEANUP_AFTER_UPLOAD: Delete local files after upload
    echo   - SYNC_INTERVAL_SECONDS: Schedule sync interval
    echo   - LOG_LEVEL: Logging level ^(DEBUG, INFO, WARNING, ERROR^)
    echo.
)

echo.
echo ====================================
echo Installation Complete!
echo ====================================
echo.
echo Next steps:
echo 1. Edit configuration:
echo    notepad "!INSTALL_DIR!\.env"
echo.
echo 2. Test the client:
echo    cd "!INSTALL_DIR!"
echo    venv\Scripts\activate
echo    python main.py
echo.
echo 3. To run as a Windows Service:
echo    - Use NSSM ^(Non-Sucking Service Manager^) to install as a service
echo    - Or use Task Scheduler to run on startup
echo    - Or create a startup script in Startup folder
echo.
echo 4. For help, see: !INSTALL_DIR!\README.md
echo.
echo Installation directory: !INSTALL_DIR!
echo.
pause

