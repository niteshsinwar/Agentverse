#!/bin/bash

# Agentverse - Setup Script for macOS/Linux
# This script automates the setup process for the Agentverse platform

set -e  # Exit on any error

echo "🤖 Agentverse - Setup Script"
echo "==============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        return 1
    fi
    return 0
}

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check Python - try python3.11 first, then python3
PYTHON_CMD="python3"
if check_command python3.11; then
    PYTHON_CMD="python3.11"
elif check_command python3.10; then
    PYTHON_CMD="python3.10"
elif check_command python3.12; then
    PYTHON_CMD="python3.12"
fi

if check_command $PYTHON_CMD; then
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+')
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

    if [[ "$PYTHON_MAJOR" -eq 3 ]] && [[ "$PYTHON_MINOR" -ge 10 ]] && [[ "$PYTHON_MINOR" -le 12 ]]; then
        print_success "Python $PYTHON_VERSION found: $($PYTHON_CMD --version)"
    elif [[ "$PYTHON_MAJOR" -eq 3 ]] && [[ "$PYTHON_MINOR" -ge 10 ]]; then
        print_warning "Python $PYTHON_VERSION - newer than tested versions"
        print_info "Tested with Python 3.10-3.12. Should work but not guaranteed."
    else
        print_error "Python 3.10-3.12 is required. Found: $(python3 --version)"
        exit 1
    fi
else
    print_error "Python 3.10-3.12 is required but not found."
    print_info "Install Python from: https://python.org"
    exit 1
fi

# Check Node.js
if check_command node; then
    NODE_VERSION=$(node --version | grep -o '[0-9]\+' | head -1)
    if [[ "$NODE_VERSION" -ge 18 ]]; then
        print_success "Node.js 18+ found: $(node --version)"
    else
        print_error "Node.js 18+ is required. Found: $(node --version)"
        exit 1
    fi
else
    print_error "Node.js 18+ is required but not found."
    print_info "Install Node.js from: https://nodejs.org"
    exit 1
fi

# Check npm
if check_command npm; then
    print_success "npm found: $(npm --version)"
else
    print_error "npm is required but not found."
    exit 1
fi

# Check Rust (optional for Tauri)
if check_command rustc; then
    print_success "Rust found: $(rustc --version)"
else
    print_warning "Rust not found. Install from: https://rustup.rs/ (required for Tauri builds)"
fi

echo ""
print_success "All prerequisites satisfied!"
echo ""

# Setup backend
echo "🐍 Setting up Backend..."
cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    print_info "Creating Python virtual environment..."
    $PYTHON_CMD -m venv venv
    print_success "Virtual environment created"
else
    print_info "Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
print_info "Activating virtual environment and installing dependencies..."
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
if pip install -r requirements.txt; then
    print_success "Backend dependencies installed"
else
    print_error "Failed to install backend dependencies"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_info "Creating .env file from template..."
    cp ../.env.example .env
    print_warning "Please edit backend/.env with your API keys before starting the application"
else
    print_info ".env file already exists"
fi

cd ..

# Setup frontend
echo "⚛️  Setting up Frontend..."
cd frontend

# Install frontend dependencies
print_info "Installing frontend dependencies..."
if npm install; then
    print_success "Frontend dependencies installed"
else
    print_error "Failed to install frontend dependencies"
    exit 1
fi

cd ..

# Final instructions
echo ""
print_success "🎉 Agentverse setup completed successfully! Welcome to your agent universe! 🚀"
echo ""
echo "📋 Next steps:"
echo "1. Edit backend/.env with your API keys (OPENAI_API_KEY, GITHUB_TOKEN)"
echo "2. Start the backend: cd backend && source venv/bin/activate && python3 server.py"
echo "3. Start the frontend: cd frontend && npm run dev"
echo "4. Visit http://localhost:1420 to access the application"
echo ""
echo "📚 For more information, see README.md"
echo ""
print_info "To start the application, run: ./start.sh (if available) or follow the manual steps above"