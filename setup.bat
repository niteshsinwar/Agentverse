@echo off
:: Agentverse - Setup Script for Windows
:: This script automates the setup process for the Agentverse platform

echo.
echo 🤖 Agentverse - Setup Script for Windows
echo ===============================================
echo.

:: Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo ℹ️  Please install Python 3.9-3.12 from https://python.org
    echo ⚠️  Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

:: Get Python version and validate
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set PYTHON_MAJOR=%%a
    set PYTHON_MINOR=%%b
)

if %PYTHON_MAJOR% NEQ 3 (
    echo ❌ Python 3.9-3.12 is required. Found: %PYTHON_VERSION%
    echo ℹ️  Please install Python 3.9-3.12 from https://python.org
    pause
    exit /b 1
)

if %PYTHON_MINOR% LSS 9 (
    echo ❌ Python 3.9-3.12 is required. Found: %PYTHON_VERSION%
    echo ℹ️  Please install Python 3.9-3.12 from https://python.org
    pause
    exit /b 1
)

if %PYTHON_MINOR% GTR 12 (
    echo ⚠️  Python %PYTHON_VERSION% - newer than tested versions
    echo ℹ️  Tested with Python 3.9-3.12. Should work but not guaranteed.
) else (
    echo ✅ Python %PYTHON_VERSION% found and compatible
)

:: Check Node.js version
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed or not in PATH
    echo ℹ️  Please install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)

:: Get Node.js version and validate
for /f "tokens=1 delims=v" %%i in ('node --version') do set NODE_VERSION=%%i
for /f "tokens=1 delims=." %%a in ("%NODE_VERSION%") do set NODE_MAJOR=%%a

if %NODE_MAJOR% LSS 18 (
    echo ❌ Node.js 18+ is required. Found: v%NODE_VERSION%
    echo ℹ️  Please install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
) else (
    echo ✅ Node.js v%NODE_VERSION% found and compatible
)

:: Check if npm is installed
npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ npm is not installed
    echo ℹ️  npm should be installed with Node.js
    pause
    exit /b 1
) else (
    echo ✅ npm found:
    npm --version
)

:: Check if Rust is installed (optional)
rustc --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Rust not found. Install from https://rustup.rs/ (required for Tauri builds)
) else (
    echo ✅ Rust found:
    rustc --version
)

echo.
echo ✅ All prerequisites satisfied!
echo.

:: Setup backend
echo 🐍 Setting up Backend...
cd backend

:: Create virtual environment if it doesn't exist
if not exist "venv" (
    echo ℹ️  Creating Python virtual environment...
    python -m venv venv
    echo ✅ Virtual environment created
) else (
    echo ℹ️  Virtual environment already exists
)

:: Activate virtual environment and install dependencies
echo ℹ️  Activating virtual environment and installing dependencies...
call venv\Scripts\activate.bat

:: Upgrade pip
python -m pip install --upgrade pip

:: Install requirements
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install backend dependencies
    pause
    exit /b 1
)
echo ✅ Backend dependencies installed

:: Create .env file if it doesn't exist
if not exist ".env" (
    echo ℹ️  Creating .env file from template...
    copy ..\.env.example .env
    echo ⚠️  Please edit backend\.env with your API keys before starting the application
) else (
    echo ℹ️  .env file already exists
)

cd ..

:: Setup frontend
echo ⚛️  Setting up Frontend...
cd frontend

:: Install frontend dependencies
echo ℹ️  Installing frontend dependencies...
npm install
if errorlevel 1 (
    echo ❌ Failed to install frontend dependencies
    pause
    exit /b 1
)
echo ✅ Frontend dependencies installed

cd ..

:: Final instructions
echo.
echo ✅ 🎉 Agentverse setup completed successfully! Welcome to your agent universe! 🚀
echo.
echo 📋 Next steps:
echo 1. Edit backend\.env with your API keys (OPENAI_API_KEY, GITHUB_TOKEN)
echo 2. Start the backend:
echo    - Open Command Prompt/PowerShell
echo    - cd backend
echo    - venv\Scripts\activate
echo    - python server.py
echo 3. Start the frontend:
echo    - Open another Command Prompt/PowerShell
echo    - cd frontend
echo    - npm run dev
echo 4. Visit http://localhost:1420 to access the application
echo.
echo 📚 For more information, see README.md
echo.
echo ℹ️  To start the application, run start.bat (if available) or follow the manual steps above
echo.
pause