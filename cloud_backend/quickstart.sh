#!/bin/bash
# Quick Start Script for Django Cloud Backend

echo "🚀 AgentVerse Cloud Backend - Quick Start"
echo "=========================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please update .env with your configuration!"
fi

# For quick testing, use SQLite instead of PostgreSQL
echo "📝 Setting up SQLite for quick testing..."
export DATABASE_URL="sqlite:///./db.sqlite3"

# Create logs directory
mkdir -p logs

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env with your configuration"
echo "2. Run migrations: python manage.py makemigrations && python manage.py migrate"
echo "3. Create superuser: python manage.py createsuperuser"
echo "4. Run server: python manage.py runserver 9000"
echo ""
echo "For production with PostgreSQL:"
echo "- Install PostgreSQL"
echo "- Create database: createdb agentverse_cloud"
echo "- Update DATABASE_URL in .env"
echo "- Run migrations with: python manage.py migrate_schemas"
