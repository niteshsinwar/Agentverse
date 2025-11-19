#!/bin/bash
# Setup and Test Script - AgentVerse Cloud Backend

set -e  # Exit on error

echo "🚀 AgentVerse Cloud Backend - Setup & Test"
echo "==========================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create virtual environment if needed
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}📥 Installing dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Use SQLite for quick testing
echo -e "${YELLOW}📝 Configuring SQLite database...${NC}"
export DATABASE_URL="sqlite:///./db.sqlite3"
export DJANGO_SECRET_KEY="test-secret-key-$(date +%s)"
export DEBUG="True"

# Create logs directory
mkdir -p logs

# Run migrations
echo -e "${YELLOW}🔄 Running migrations...${NC}"
python manage.py makemigrations core users agents tools mcp groups messages documents analytics 2>/dev/null || true
python manage.py makemigrations
python manage.py migrate

# Create superuser (non-interactive)
echo -e "${YELLOW}👤 Creating superuser...${NC}"
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(email='admin@example.com').exists() or User.objects.create_superuser('admin@example.com', password='password123', name='Admin User')" | python manage.py shell

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "📊 Database status:"
python manage.py showmigrations | head -20

echo ""
echo -e "${GREEN}🎉 Cloud backend is ready!${NC}"
echo ""
echo "To start the server:"
echo "  cd cloud_backend"
echo "  source venv/bin/activate"
echo "  export DATABASE_URL='sqlite:///./db.sqlite3'"
echo "  python manage.py runserver 9000"
echo ""
echo "Login credentials:"
echo "  Email: admin@example.com"
echo "  Password: password123"
