# 🔧 AgentVerse Backend

**Enterprise-Grade AI Agent Orchestration API**

Professional FastAPI-based Python backend service providing enterprise-ready AI agent management, real-time communication, and advanced orchestration capabilities.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.9--3.12-blue.svg)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-0.1+-purple.svg)](https://langchain.com)
[![Pydantic](https://img.shields.io/badge/Pydantic-2.5+-red.svg)](https://pydantic.dev)

---

## 🏗️ **Architecture Overview**

The backend follows **Clean Architecture** principles with clear separation of concerns:

```
backend/
├── 🚀 server.py                    # Application entry point & lifecycle management
├── 📁 src/                         # Source code (immutable business logic)
│   ├── 🌐 api/v1/                  # RESTful API layer
│   │   ├── endpoints/              # API endpoint implementations
│   │   │   ├── agents.py          # Agent CRUD operations
│   │   │   ├── groups.py          # Conversation group management
│   │   │   ├── chat.py            # Real-time messaging & streaming
│   │   │   ├── analytics.py       # Performance metrics & insights
│   │   │   ├── config.py          # System configuration endpoints
│   │   │   └── logs.py            # Session & event log access
│   │   ├── models/                # Pydantic request/response models
│   │   └── dependencies.py        # Dependency injection setup
│   │
│   ├── 🧠 core/                    # Business logic & domain services
│   │   ├── agents/                # Agent orchestration system
│   │   │   ├── base_agent.py      # Base agent class & tool framework
│   │   │   ├── orchestrator.py    # Multi-agent coordination
│   │   │   ├── router.py          # Agent communication routing
│   │   │   └── registry.py        # Agent discovery & lifecycle
│   │   ├── llm/                   # LLM provider integrations
│   │   │   ├── factory.py         # LLM provider factory
│   │   │   ├── openai_provider.py # OpenAI GPT integration
│   │   │   ├── claude_provider.py # Anthropic Claude integration
│   │   │   ├── gemini_provider.py # Google Gemini integration
│   │   │   └── base.py            # Abstract LLM provider interface
│   │   ├── memory/                # Knowledge & session management
│   │   │   ├── session_store.py   # Conversation persistence
│   │   │   └── rag_store.py       # Vector storage for RAG
│   │   ├── mcp/                   # Model Context Protocol
│   │   │   └── client.py          # MCP server communication
│   │   ├── document_processing/   # AI document analysis
│   │   ├── telemetry/             # Analytics & monitoring
│   │   ├── validation/            # Input validation & security
│   │   └── config/                # Configuration management
│   │       └── settings.py        # Pydantic settings with env vars
│   │
│   └── 📡 services/                # Application service layer
│       └── orchestrator_service.py # Main business logic coordinator
│
├── ⚙️  config/                     # Configuration files (JSON)
│   ├── tools.json                 # Pre-built tool definitions
│   ├── mcp.json                   # MCP server configurations
│   └── settings.json              # Application settings
│
├── 💾 Runtime Data Directories
│   ├── agent_store/               # Dynamic agent instances
│   ├── documents/                 # Uploaded file storage
│   ├── data/                      # SQLite database files
│   └── logs/                      # Session & event logs
│
└── 📋 Requirements & Setup
    ├── requirements.txt           # Python dependencies
    ├── .env                       # Environment variables
    └── venv/                      # Python virtual environment
```

## Design Principles

### 1. **Layered Architecture**
- **API Layer**: FastAPI routes, request/response handling
- **Service Layer**: Business operations and orchestration
- **Core Layer**: Domain-specific business logic
- **Repository Layer**: Data access and persistence

### 2. **Clean Code Practices**
- **Single Responsibility**: Each module has one clear purpose
- **Dependency Injection**: Services are injected, not instantiated
- **Type Safety**: Full Pydantic integration for data validation
- **Error Handling**: Proper exception handling at each layer

### 3. **Scalability Features**
- **API Versioning**: `/api/v1/` prefix for future compatibility
- **Configuration Management**: Environment-based settings
- **Service Isolation**: Easy to extract services as microservices
- **Professional Structure**: Easy for new developers to understand

### 4. **Data Separation Architecture**
- **Immutable Code**: All logic in `src/` directory
- **Mutable Data**: Agent instances in `agent_store/`
- **Persistent Storage**: Database in `data/`, uploads in `documents/`
- **Clean Isolation**: Easy backup, deployment, and scaling

## Key Components

### Server Entry Point (`server.py`)
- Application factory pattern
- Lifespan management
- Dependency injection setup
- Professional FastAPI configuration

### Configuration (`src/core/config/settings.py`)
- Pydantic Settings for type-safe configuration
- Environment variable support
- Validation and defaults
- Clear documentation

### Services (`src/services/`)
- **OrchestratorService**: High-level agent management
- Business logic abstraction
- Error handling and validation
- Clean API interface

### API Endpoints (`src/api/v1/endpoints/`)
- **groups.py**: Group management endpoints
- **agents.py**: Agent system endpoints
- **chat.py**: Message and chat endpoints
- RESTful design principles
- Comprehensive error handling

## Development Workflow

### 1. **Running the Server**
```bash
cd backend
python server.py
```

### 2. **API Documentation**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 3. **Adding New Features**
1. Add business logic to `src/services/`
2. Create API models in `src/api/v1/models/`
3. Add endpoints in `src/api/v1/endpoints/`
4. Update configuration if needed

### 4. **Environment Setup**
Create a `.env` file in project root:
```env
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
GITHUB_TOKEN=your_token_here
```

## Why This Structure?

### **For Experienced Developers:**
- Follows FastAPI and Python web development best practices
- Clear separation enables easy testing and maintenance
- Scalable architecture supports future microservices migration
- Professional patterns familiar from enterprise applications

### **For Beginners:**
- Each folder has a single, clear purpose
- File names indicate their function
- Dependencies flow in one direction (API → Services → Core)
- Examples and documentation guide development

### **For Team Collaboration:**
- Multiple developers can work on different layers simultaneously
- Clear interfaces prevent conflicts
- Easy to code review and understand changes
- Standard patterns reduce learning curve

---

## 🚀 **Core Features**

### **🤖 Agent Orchestration**
- **Multi-Agent Coordination**: LangGraph-powered agent workflows
- **Dynamic Agent Loading**: Runtime agent discovery and instantiation
- **Tool Integration**: 15+ pre-built tools with custom tool support
- **MCP Server Support**: Extensible Model Context Protocol integration
- **Memory Management**: Session persistence and knowledge retention

### **🌐 Enterprise API**
- **RESTful Endpoints**: 20+ documented API endpoints
- **Real-time Messaging**: WebSocket streaming for live agent responses
- **Type Safety**: Full Pydantic validation for all requests/responses
- **Auto Documentation**: Interactive Swagger UI and ReDoc
- **Error Handling**: Comprehensive error responses with proper HTTP codes

### **📊 Analytics & Monitoring**
- **Session Tracking**: Detailed conversation logging and analytics
- **Performance Metrics**: Response times, success rates, agent performance
- **User Activity**: Action tracking and usage analytics
- **Event Logging**: Structured logging with multiple severity levels
- **Health Monitoring**: Application health checks and system status

### **🔧 LLM Integration**
- **Multi-Provider Support**: OpenAI, Anthropic Claude, Google Gemini
- **Dynamic Model Selection**: Runtime LLM provider switching
- **Streaming Responses**: Real-time response streaming for better UX
- **Token Management**: Intelligent token usage and optimization
- **Error Handling**: Robust fallback mechanisms for LLM failures

---

## 📋 **Dependencies & Technology Stack**

### **Core Framework**
```python
# Web Framework & API
fastapi>=0.104.0           # Modern async web framework
uvicorn[standard]>=0.24.0  # ASGI server with auto-reload
pydantic>=2.5.0            # Type validation & serialization
pydantic-settings>=2.1.0   # Environment-based configuration
```

### **AI & Agent Framework**
```python
# LLM Providers
openai>=1.0.0              # OpenAI GPT models
anthropic>=0.7.0           # Anthropic Claude models
google-generativeai>=0.3.0 # Google Gemini models

# Agent Orchestration
langgraph>=0.0.60          # Multi-agent workflow orchestration
langchain>=0.1.0           # LLM application framework
langchain-openai>=0.0.8    # LangChain OpenAI integration
```

### **Document Processing**
```python
# Document Formats
pypdf>=3.15.0              # PDF processing
python-docx>=1.1.0         # Word document processing
python-pptx>=0.6.21        # PowerPoint processing
openpyxl>=3.1.0            # Excel processing
Pillow>=9.0.0              # Image processing
PyMuPDF>=1.23.0            # Advanced PDF processing
```

### **Data & Utilities**
```python
# Data Handling
pandas>=1.5.0              # Data analysis and manipulation
numpy>=1.21.0              # Numerical computing
PyYAML>=6.0.0              # YAML configuration support
beautifulsoup4>=4.12.0     # HTML/XML parsing

# HTTP & File Operations
httpx>=0.25.0              # Async HTTP client
aiofiles>=23.0.0           # Async file operations
requests>=2.28.0           # Synchronous HTTP client
```

---

## ⚙️ **Configuration Management**

### **Environment Variables (.env)**
```bash
# Required API Keys
OPENAI_API_KEY=sk-your-openai-key-here
GITHUB_TOKEN=ghp_your-github-token-here

# Optional API Keys
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
GEMINI_API_KEY=your-gemini-key-here

# Application Settings
ENVIRONMENT=development
SECRET_KEY=your-secret-key
HOST=0.0.0.0
PORT=8000

# LLM Configuration
LLM_PROVIDER=openai
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=4096

# File Processing
MAX_UPLOAD_SIZE_MB=15
SUPPORTED_FILE_FORMATS=txt,csv,json,pdf,docx,md
```

---

## 🛠️ **Development Setup**

### **1. Environment Setup**
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### **2. Configuration**
```bash
# Create environment file
cp ../.env.example .env

# Edit with your API keys
nano .env  # or your preferred editor
```

### **3. Start Development Server**
```bash
# Start with auto-reload
python server.py

# Alternative: Use uvicorn directly
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

### **4. Verify Installation**
- **Health Check**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

---

## 📊 **API Endpoints**

### **Agent Management**
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/agents/` | List all available agents |
| `POST` | `/api/v1/agents/create/` | Create new agent |
| `PUT` | `/api/v1/agents/{key}/` | Update existing agent |
| `DELETE` | `/api/v1/agents/{key}/` | Delete agent |
| `GET` | `/api/v1/agents/{key}/details/` | Get agent details |

### **Group & Chat Management**
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/groups/` | List conversation groups |
| `POST` | `/api/v1/groups/create/` | Create new group |
| `POST` | `/api/v1/groups/{id}/messages/` | Send message to agent |
| `GET` | `/api/v1/groups/{id}/messages/` | Get conversation history |

### **Configuration**
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/config/tools/` | Get available tools |
| `GET` | `/api/v1/config/mcp/` | Get MCP server configs |
| `POST` | `/api/v1/config/tools/` | Update tool configuration |

### **Analytics & Monitoring**
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/analytics/sessions/` | Get session analytics |
| `GET` | `/api/v1/analytics/performance/` | Get performance metrics |
| `GET` | `/api/v1/logs/sessions/` | List log sessions |
| `GET` | `/api/v1/logs/events/` | Get session events |

---

## 🔒 **Security Features**

### **Input Validation**
- **Pydantic Models**: Type-safe request/response validation
- **File Upload Security**: Size limits, format validation, virus scanning
- **SQL Injection Prevention**: Parameterized queries and ORM usage
- **XSS Protection**: Input sanitization and output encoding

### **API Security**
- **CORS Configuration**: Configurable allowed origins
- **Rate Limiting**: Request throttling (planned)
- **API Key Management**: Secure environment variable storage
- **Session Management**: Configurable timeout and cleanup

---

## 🚀 **Production Deployment**

### **Using Gunicorn (Recommended)**
```bash
# Install production server
pip install gunicorn

# Start with multiple workers
gunicorn -w 4 -k uvicorn.workers.UvicornWorker server:app --bind 0.0.0.0:8000
```

### **Docker Deployment** (Planned)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "server:app", "--bind", "0.0.0.0:8000"]
```

---

This structure ensures the backend can grow from a simple API to a comprehensive system while maintaining code quality and developer productivity.

**🔧 Backend Service - Part of the AgentVerse Enterprise Platform**

*Built with FastAPI, LangChain, and modern Python best practices for enterprise-grade AI agent orchestration.*