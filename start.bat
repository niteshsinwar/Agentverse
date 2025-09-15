@echo off
:: Agentverse - Start Script for Windows
:: This script starts both backend and frontend services

echo.
echo 🤖 Starting Agentverse Platform
echo ==================================================
echo.

:: Check if backend virtual environment exists
if not exist "backend\venv" (
    echo ❌ Backend virtual environment not found
    echo ℹ️  Please run setup.bat first
    pause
    exit /b 1
)

:: Check if .env exists
if not exist "backend\.env" (
    echo ❌ .env file not found in backend directory
    echo ℹ️  Please copy .env.example to backend\.env and configure it
    pause
    exit /b 1
)

:: Check if frontend dependencies are installed
if not exist "frontend\node_modules" (
    echo ❌ Frontend dependencies not installed
    echo ℹ️  Please run setup.bat first
    pause
    exit /b 1
)

:: Function to check if port is in use and kill process
echo ℹ️  Checking and freeing ports...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
    echo ⚠️  Killing process on port 8000...
    taskkill /PID %%a /F >nul 2>&1
)

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :1420') do (
    echo ⚠️  Killing process on port 1420...
    taskkill /PID %%a /F >nul 2>&1
)

:: Start backend
echo 🐍 Starting Backend Server...
cd backend
start "Agentverse Backend" cmd /k "venv\Scripts\activate && python server.py"
echo ✅ Backend starting on http://localhost:8000
echo    - Health: http://localhost:8000/health
echo    - API Docs: http://localhost:8000/docs
cd ..

:: Wait for backend to start
echo ⏳ Waiting for backend to initialize...
timeout /t 8 /nobreak >nul

:: Start frontend
echo ⚛️  Starting Frontend...
cd frontend
start "Agentverse Frontend" cmd /k "npm run dev"
echo ✅ Frontend starting on http://localhost:1420
cd ..

echo.
echo 🎉 Welcome to the Agentverse! Your agent universe is starting! 🚀
echo.
echo 📱 Frontend: http://localhost:1420
echo 🔧 Backend:  http://localhost:8000
echo 📚 API Docs: http://localhost:8000/docs
echo.
echo ℹ️  Two new command windows have been opened:
echo    - Backend Server (Python)
echo    - Frontend Dev Server (Node.js)
echo.
echo ℹ️  Close those windows to stop the services
echo    Or use Ctrl+C in each window
echo.
echo 📋 If you encounter any issues:
echo 1. Check that all prerequisites are installed
echo 2. Ensure API keys are configured in backend\.env
echo 3. Try running setup.bat again
echo.
pause