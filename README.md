# 🤖 AgentVerse

<div align="center">

![AgentVerse Logo](logo.svg)

**Enterprise-Grade AI Agent Orchestration Platform**

*Multiverse of Agents*

</div>

A professional, production-ready platform for creating, managing, and deploying intelligent AI agents with advanced tooling, real-time collaboration, and MCP (Model Context Protocol) integration. Welcome to the AgentVerse - where AI agents collaborate, evolve, and thrive in a unified ecosystem! 🌌

[![Python](https://img.shields.io/badge/Python-3.9--3.12-blue.svg)](https://python.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://typescriptlang.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.2+-cyan.svg)](https://react.dev)
[![Tauri](https://img.shields.io/badge/Tauri-1.5+-orange.svg)](https://tauri.app)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎯 Platform Overview

AgentVerse is a comprehensive B2B SaaS platform designed for enterprises seeking to integrate AI agents into their workflows. Built with production-grade architecture and modern technologies, it provides:

### 🏢 **Enterprise Features**
- **Professional Backend**: FastAPI-based Python backend with clean architecture and enterprise patterns
- **Desktop Application**: Cross-platform Tauri + React/TypeScript app with native performance
- **Agent Orchestration**: Advanced multi-agent collaboration using LangGraph and LangChain
- **Real-time Communication**: WebSocket-based messaging with live streaming responses
- **Document Intelligence**: AI-powered document processing and analysis
- **MCP Integration**: Cutting-edge Model Context Protocol support for extensibility
- **Analytics & Monitoring**: Comprehensive session logging, performance metrics, and user analytics
- **Multi-LLM Support**: OpenAI, Anthropic Claude, Google Gemini integration

### 🚀 **Core Capabilities**
- **Agent Lifecycle Management**: Create, configure, deploy, and monitor AI agents
- **Tool Ecosystem**: 15+ pre-built tools (file ops, web scraping, data processing, API calls)
- **Workflow Automation**: Chain multiple agents for complex business processes
- **Document Processing**: Support for 20+ file formats with AI analysis
- **Custom Integrations**: Extensible architecture for custom tools and MCP servers
- **Enterprise Security**: Secure API key management, session control, and audit logging

## 🏗️ Architecture & Technology Stack

### **System Architecture**
```
AgentVerse/ (Enterprise-Grade Platform)
├── 🖥️  Frontend (Tauri Desktop App)           # Cross-platform native performance
│   ├── React 18 + TypeScript 5.0             # Modern reactive UI framework
│   ├── TailwindCSS + Framer Motion           # Professional styling & animations
│   ├── Real-time WebSocket client            # Live messaging & updates
│   └── 14 specialized components             # Modular, reusable UI components
│
├── 🔧 Backend (FastAPI Python)               # Production-ready API server
│   ├── src/api/v1/                          # RESTful API endpoints (6 modules)
│   │   ├── agents/     # Agent CRUD operations
│   │   ├── groups/     # Conversation management
│   │   ├── chat/       # Real-time messaging
│   │   ├── analytics/  # Performance metrics
│   │   ├── config/     # System configuration
│   │   └── logs/       # Session & event logging
│   │
│   ├── src/core/                           # Business logic & services
│   │   ├── agents/     # Agent orchestration (LangGraph)
│   │   ├── llm/        # Multi-provider LLM integration
│   │   ├── memory/     # Session & knowledge management
│   │   ├── mcp/        # Model Context Protocol client
│   │   ├── document_processing/ # AI document analysis
│   │   ├── telemetry/  # Analytics & monitoring
│   │   └── validation/ # Input validation & security
│   │
│   └── src/services/                       # Application services
│       └── orchestrator_service.py        # Main business logic layer
│
├── 📁 Configuration & Data
│   ├── config/         # JSON configuration files
│   │   ├── tools.json  # Pre-built tool definitions
│   │   ├── mcp.json    # MCP server configurations
│   │   └── settings.json # Application settings
│   ├── agent_store/    # Runtime agent instances
│   ├── documents/      # Uploaded file storage
│   ├── data/          # SQLite databases
│   └── logs/          # Session & event logs
│
└── 🛠️  DevOps & Setup
    ├── setup.sh/bat    # Automated platform setup
    ├── start.sh/bat    # Development server launcher
    └── .env.example    # Environment configuration template
```

### **Technology Stack**

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Tauri + React 18 + TypeScript | Cross-platform desktop app with web technologies |
| **Backend** | FastAPI + Python 3.9-3.12 | High-performance async API server |
| **Agent Framework** | LangChain + LangGraph | Multi-agent orchestration & workflows |
| **LLM Providers** | OpenAI, Anthropic, Gemini | Multi-model AI capabilities |
| **UI Framework** | TailwindCSS + Framer Motion | Professional design system |
| **Real-time** | WebSocket + Server-Sent Events | Live messaging & updates |
| **Data Storage** | SQLite + JSON configs | Lightweight data persistence |
| **Documentation** | Pydantic + FastAPI auto-docs | Type-safe API documentation |

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

**Windows:**
```cmd
# Run setup script
setup.bat

# Verify installation
python verify-setup.py

# Start the application
start.bat
```

**macOS/Linux:**
```bash
# Run setup script
./setup.sh

# Verify installation
python3 verify-setup.py

# Start the application
./start.sh
```

### Option 2: Manual Setup

### Prerequisites

**Windows:**
- **Python 3.9-3.12** (Download from [python.org](https://python.org) - ensure "Add to PATH" is checked)
- **Node.js 18+** (Download from [nodejs.org](https://nodejs.org))
- **Rust** (Download from [rustup.rs](https://rustup.rs/) - run `rustup-init.exe`)
- **Visual Studio Build Tools** (for Tauri): Download from [Microsoft](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

**macOS:**
- **Python 3.9-3.12** (Install via Homebrew: `brew install python` or download from [python.org](https://python.org))
- **Node.js 18+** (Install via Homebrew: `brew install node` or download from [nodejs.org](https://nodejs.org))
- **Rust** (Install via Homebrew: `brew install rust` or from [rustup.rs](https://rustup.rs/))
- **Xcode Command Line Tools**: `xcode-select --install`

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd agentverse
   ```

2. **Set up Backend**

   **Windows (Command Prompt/PowerShell):**
   ```cmd
   cd backend

   :: Create virtual environment (recommended)
   python -m venv venv
   venv\Scripts\activate

   :: Install Python dependencies
   pip install -r requirements.txt

   :: Create environment file
   copy ..\.env.example .env

   :: Edit .env with your API keys using notepad or your preferred editor
   notepad .env
   ```

   **Windows (Git Bash):**
   ```bash
   cd backend

   # Create virtual environment (recommended)
   python -m venv venv
   source venv/Scripts/activate

   # Install Python dependencies
   pip install -r requirements.txt

   # Create environment file
   cp ../.env.example .env

   # Edit .env with your API keys
   nano .env
   ```

   **macOS/Linux:**
   ```bash
   cd backend

   # Create virtual environment (recommended)
   python3 -m venv venv
   source venv/bin/activate

   # Install Python dependencies
   pip install -r requirements.txt

   # Create environment file
   cp ../.env.example .env

   # Edit .env with your API keys
   nano .env
   ```
idv
   **Required API Keys in .env:**
   ```env
   OPENAI_API_KEY=sk-your-openai-key-here
   GITHUB_TOKEN=ghp_your-github-token-here
   # Optional:
   ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
   GEMINI_API_KEY=your-gemini-key-here
   ```

3. **Set up Frontend**

   **Windows:**
   ```cmd
   cd frontend

   :: Install dependencies
   npm install
   ```

   **macOS/Linux:**
   ```bash
   cd frontend

   # Install dependencies
   npm install
   ```

4. **Start the Applications**

   **Terminal 1 - Backend:**

   **Windows:**
   ```cmd
   cd backend
   venv\Scripts\activate
   python server.py
   ```

   **macOS/Linux:**
   ```bash
   cd backend
   source venv/bin/activate
   python3 server.py
   ```
   Backend will start on `http://localhost:8000`

   **Terminal 2 - Frontend:**

   **Windows/macOS/Linux:**
   ```bash
   cd frontend
   npm run dev
   ```
   Frontend will start on `http://localhost:1420`

## ✅ Verification

After starting both services, verify everything is working:

1. **Backend Health Check**: Visit `http://localhost:8000/health`
   - Should return: `{"status": "healthy", "service": "Agentverse Backend"}`

2. **API Documentation**: Visit `http://localhost:8000/docs`
   - Should show the Swagger UI with all API endpoints

3. **Frontend**: Visit `http://localhost:1420`
   - Should show the agent collaboration interface

4. **Agent Creation**: Try creating a test agent through the UI
   - Click "Agent Management" → "Create Agent"

## 🔧 Configuration

### Backend Configuration

The backend uses a professional Pydantic-based settings system. Configuration files are now located in `backend/config/`:

- `backend/config/tools.json` - Pre-built tools configuration
- `backend/config/mcp.json` - MCP servers configuration
- `backend/config/settings.json` - Application settings

Key configurations:

```python
# Core Settings
app_name = "Agentverse Backend"
environment = "development"  # development, staging, production
host = "0.0.0.0"
port = 8000

# LLM Configuration
llm_provider = "openai"  # openai, anthropic, gemini
llm_temperature = 0.2
llm_max_tokens = 4096

# Security
secret_key = "your-secret-key"
session_timeout_hours = 24

# File Processing
max_upload_size_mb = 10
supported_file_formats = ["txt", "csv", "json", "pdf", "docx", "md"]
```

### Frontend Configuration

The frontend stores UI-specific settings in localStorage and syncs with backend settings via the Settings panel (⚙️ icon).

## 🤖 Agent Management

### Creating Agents

1. **Via UI**: Click "Agent Management" → "Create Agent"
2. **Choose Pre-built Tools**: Select from file operations, web scraping, data processing, etc.
3. **Configure MCP**: Add Model Context Protocol servers
4. **Custom Code**: Write custom Python tools and MCP configurations

### Pre-built Tools Available

- **File Operations**: Read, write, list, search files
- **Web Scraping**: Extract content from web pages
- **Data Processing**: CSV, JSON, pandas operations
- **Database Operations**: SQLite, PostgreSQL connections
- **Email Automation**: Send emails with attachments
- **Image Processing**: Resize, crop, convert images

### Pre-built MCP Servers

- **Filesystem**: File system operations with security controls
- **Brave Search**: Web search capabilities
- **GitHub**: Repository access and management
- **PostgreSQL/SQLite**: Database operations
- **Puppeteer**: Browser automation
- **Memory**: Persistent knowledge management

## 🔨 Adding New Tools/MCPs

To add new tools or MCP servers, edit the JSON configuration files in `backend/config/`:

### Adding Tools
Edit `backend/config/tools.json`:

```json
{
  "my_new_tool": {
    "name": "My New Tool",
    "description": "Description of what this tool does",
    "category": "category_name",
    "code": "def my_function():\n    # Your Python code here\n    pass",
    "functions": ["my_function"]
  }
}
```

### Adding MCP Servers
Edit `backend/config/mcp.json`:

```json
{
  "my_mcp_server": {
    "name": "My MCP Server",
    "description": "Description of MCP server capabilities",
    "category": "category_name",
    "config": {
      "command": "npx",
      "args": ["my-mcp-server"],
      "env": {
        "API_KEY": "${MY_API_KEY}"
      },
      "capabilities": ["capability1", "capability2"]
    }
  }
}
```

## 📝 API Documentation

The backend provides comprehensive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

- `GET /api/v1/agents/` - List all agents
- `POST /api/v1/agents/create/` - Create new agent
- `PUT /api/v1/agents/{key}/` - Update agent
- `DELETE /api/v1/agents/{key}/` - Delete agent
- `GET /api/v1/groups/` - List conversation groups
- `POST /api/v1/groups/{id}/messages/` - Send message to agent
- `GET /api/v1/config/tools/` - Get tools configuration
- `GET /api/v1/config/mcp/` - Get MCP configuration

## 🛡️ Security Features

- **API Key Management**: Secure storage and rotation
- **File Upload Validation**: Size limits and format restrictions
- **Session Management**: Configurable timeouts
- **CORS Protection**: Configurable allowed origins
- **Input Validation**: Pydantic-based request validation

## 🎨 UI Features

- **Professional Design**: Modern Tailwind CSS styling
- **Dark/Light Mode**: System-aware theme switching
- **Responsive Layout**: Adaptive to different screen sizes
- **Animations**: Smooth Framer Motion transitions
- **Keyboard Shortcuts**: Command palette (⌘K / Ctrl+K)
- **Real-time Updates**: Live message streaming
- **File Drag & Drop**: Easy document uploads

## 📊 Development

### Backend Development

**Windows:**
```cmd
cd backend
venv\Scripts\activate

:: Run with auto-reload
python server.py

:: Format code (if installed)
black src\
flake8 src\
```

**macOS/Linux:**
```bash
cd backend
source venv/bin/activate

# Run with auto-reload
python3 server.py

# Format code (if installed)
black src/
flake8 src/
```

### Frontend Development

**Windows/macOS/Linux:**
```bash
cd frontend

# Development server
npm run dev

# Build for production
npm run build

# Lint code
npm run lint

# Build Tauri app
npm run tauri build
```

## 🐳 Deployment

### Backend Deployment

1. **Production Settings**:
   **Windows:**
   ```cmd
   set ENVIRONMENT=production
   set SECRET_KEY=your-production-secret-key
   ```

   **macOS/Linux:**
   ```bash
   export ENVIRONMENT=production
   export SECRET_KEY=your-production-secret-key
   ```

2. **Using Gunicorn** (macOS/Linux):
   ```bash
   pip install gunicorn
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker server:app
   ```

   **Windows alternative** (using uvicorn directly):
   ```cmd
   pip install uvicorn[standard]
   uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4
   ```

### Frontend Deployment

The frontend is a Tauri desktop application that can be built for multiple platforms:

```bash
cd frontend
npm run tauri build
```

## 🛠️ Troubleshooting

### Common Issues

**Windows:**
- **Python not found**: Ensure Python is added to PATH during installation
- **npm not found**: Restart terminal after Node.js installation
- **Rust compiler errors**: Install Visual Studio Build Tools
- **Permission errors**: Run terminal as Administrator if needed

**macOS:**
- **Command not found**: Install Xcode Command Line Tools: `xcode-select --install`
- **Permission errors**: Use `sudo` for global npm packages if needed
- **Python version issues**: Use `python3` instead of `python`

**Both Platforms:**
- **Port already in use**: Kill processes using ports 8000 or 1420
- **Module not found**: Ensure virtual environment is activated for backend
- **API key errors**: Double-check .env file formatting and key validity

### Port Conflicts

**Windows:**
```cmd
:: Find process using port 8000
netstat -ano | findstr :8000

:: Kill process by PID
taskkill /PID <PID> /F
```

**macOS/Linux:**
```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Find and kill process using port 1420
lsof -ti:1420 | xargs kill -9
```

## 📚 Documentation

- **API Reference**: http://localhost:8000/docs
- **Frontend Components**: Documented with TypeScript interfaces
- **Configuration**: All config files in `backend/config/`

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

1. Check the troubleshooting section above
2. Review API documentation at http://localhost:8000/docs
3. Open an issue on GitHub

## 🎯 Product Roadmap

### **Current Status: Production Ready (v1.0)**
✅ **Completed Features**
- [x] Enterprise-grade backend with FastAPI
- [x] Professional desktop app with Tauri + React
- [x] Multi-agent orchestration system
- [x] Real-time chat with streaming responses
- [x] Document processing (20+ formats)
- [x] Multi-LLM provider support
- [x] MCP integration framework
- [x] Advanced analytics & logging
- [x] Pre-built tool ecosystem (15+ tools)
- [x] Professional UI/UX design

### **Phase 2: Enterprise Features (v1.1-1.2)**
- [ ] **Authentication & Authorization** - User management, roles, permissions
- [ ] **Team Collaboration** - Multi-user workspaces, shared agents
- [ ] **Cloud Deployment** - Docker containers, Kubernetes manifests
- [ ] **API Rate Limiting** - Enterprise-grade API controls
- [ ] **Advanced Security** - Encryption, audit logs, compliance features

### **Phase 3: Marketplace & Integrations (v1.3-1.4)**
- [ ] **Agent Marketplace** - Community-driven agent sharing platform
- [ ] **Plugin Ecosystem** - Third-party tool integration framework
- [ ] **Enterprise Connectors** - Slack, Teams, Salesforce, Jira integrations
- [ ] **Workflow Builder** - Visual drag-and-drop agent workflows
- [ ] **Advanced Analytics** - Business intelligence dashboard

### **Phase 4: Scale & Innovation (v2.0+)**
- [ ] **Mobile Companion App** - iOS/Android companion for monitoring
- [ ] **Cloud-Native SaaS** - Multi-tenant cloud platform
- [ ] **Enterprise SSO** - SAML, OAuth, Active Directory integration
- [ ] **AI Training Pipeline** - Custom model fine-tuning
- [ ] **Advanced Orchestration** - Complex multi-step workflows

### **Market Position**
**Target Competitors**: CrewAI, AutoGen, LangFlow, n8n, Zapier
**Differentiators**: Desktop performance, MCP integration, enterprise architecture, multi-LLM support

---

**Built with ❤️ using FastAPI, React, TypeScript, and Tauri**

*Welcome to the Agentverse - a multiverse where AI agents collaborate, evolve, and thrive! 🌌🤖✨*