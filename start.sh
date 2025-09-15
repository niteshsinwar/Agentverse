#!/bin/bash

# Agentverse - Start Script for macOS/Linux
# This script starts both backend and frontend services

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🤖 Starting Agentverse Platform${NC}"
echo "=================================================="

# Function to check if port is in use
check_port() {
    lsof -ti:$1 > /dev/null 2>&1
}

# Function to kill process on port
kill_port() {
    echo -e "${YELLOW}Port $1 is in use, attempting to free it...${NC}"
    lsof -ti:$1 | xargs kill -9 2>/dev/null || true
    sleep 2
}

# Check and free ports if needed
if check_port 8000; then
    kill_port 8000
fi

if check_port 1420; then
    kill_port 1420
fi

# Start backend in background
echo -e "${GREEN}🐍 Starting Backend Server...${NC}"
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please copy .env.example to .env and configure it."
    exit 1
fi

# Start backend
source venv/bin/activate
python3 server.py &
BACKEND_PID=$!

echo -e "${GREEN}✅ Backend started on http://localhost:8000${NC}"
echo "   - Health: http://localhost:8000/health"
echo "   - API Docs: http://localhost:8000/docs"

cd ..

# Wait a moment for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 5

# Start frontend
echo -e "${GREEN}⚛️  Starting Frontend...${NC}"
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "❌ Frontend dependencies not installed. Please run setup.sh first."
    kill $BACKEND_PID
    exit 1
fi

# Start frontend
npm run dev &
FRONTEND_PID=$!

echo -e "${GREEN}✅ Frontend started on http://localhost:1420${NC}"

cd ..

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down services...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true

    # Kill any remaining processes on our ports
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    lsof -ti:1420 | xargs kill -9 2>/dev/null || true

    echo -e "${GREEN}✅ Services stopped${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo ""
echo -e "${GREEN}🎉 Welcome to the Agentverse! Your agent universe is now running! 🚀${NC}"
echo ""
echo "📱 Frontend: http://localhost:1420"
echo "🔧 Backend:  http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for processes to finish
wait