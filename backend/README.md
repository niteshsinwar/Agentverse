# 🔧 AgentVerse Backend

**Enterprise-Grade AI Agent Orchestration API**

Professional FastAPI-based Python backend service providing enterprise-ready AI agent management, real-time communication, and advanced orchestration capabilities.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.9--3.12-blue.svg)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-0.1+-purple.svg)](https://langchain.com)
[![Pydantic](https://img.shields.io/badge/Pydantic-2.5+-red.svg)](https://pydantic.dev)
[![Tests](https://img.shields.io/badge/Tests-179%20passed-brightgreen.svg)](tests/)
[![Coverage](https://img.shields.io/badge/Coverage-59%25-yellow.svg)](tests/)
[![Code Quality](https://img.shields.io/badge/Code%20Quality-Professional-blue.svg)](#-code-quality--testing)

---

## 🏗️ **Architecture Overview**

The backend follows **Clean Architecture** principles with clear separation of concerns:

```
backend/
├── 🚀 server.py                    # Application entry point & lifecycle management
├── 📁 src/                         # Source code (immutable business logic)
│   ├── 🌐 api/v1/                  # RESTful API layer
│   │   ├── endpoints/              # API endpoint implementations
│   │   │   ├── agents.py          # Agent CRUD operations with user action tracking
│   │   │   ├── groups.py          # Conversation group management
│   │   │   ├── chat.py            # Real-time messaging & SSE streaming
│   │   │   ├── logs.py            # Session & event log access with analytics
│   │   │   ├── tools.py           # Custom tool management & validation
│   │   │   ├── mcp.py             # MCP server configuration & validation
│   │   │   ├── settings.py        # System configuration endpoints
│   │   │   └── validation.py      # Pre-validation endpoints for all resources
│   │   └── dependencies.py        # Dependency injection setup
│   │
│   ├── 🧠 core/                    # Business logic & domain services
│   │   ├── agents/                # Agent orchestration system
│   │   │   ├── base_agent.py      # Multi-step planner loop with structured responses
│   │   │   ├── orchestrator.py    # Multi-agent coordination & state management
│   │   │   ├── router.py          # @mention-based agent routing
│   │   │   ├── registry.py        # Dynamic agent discovery & tool registration
│   │   │   └── response_models.py # Pydantic models for agent responses
│   │   ├── llm/                   # LLM provider integrations
│   │   │   ├── factory.py         # LLM provider factory with streaming support
│   │   │   ├── openai_provider.py # OpenAI GPT integration (streaming)
│   │   │   ├── claude_provider.py # Anthropic Claude integration (streaming)
│   │   │   ├── gemini_provider.py # Google Gemini integration (streaming)
│   │   │   └── base.py            # Abstract LLM provider interface
│   │   ├── memory/                # Knowledge & session management
│   │   │   ├── session_store.py   # SQLite conversation persistence & history
│   │   │   └── rag_store.py       # Vector storage for document RAG
│   │   ├── mcp/                   # Model Context Protocol
│   │   │   └── client.py          # MCP server lifecycle & tool discovery
│   │   ├── document_processing/   # AI document analysis
│   │   │   ├── storage.py         # Document metadata & chunk storage
│   │   │   └── processors/        # Format-specific processors
│   │   ├── telemetry/             # Analytics & monitoring
│   │   │   ├── session_logger.py  # Structured session event logging
│   │   │   ├── user_actions.py    # User action tracking & analytics
│   │   │   ├── logger.py          # LLM call & tool execution logging
│   │   │   └── context.py         # Logging context management
│   │   ├── validation/            # Input validation & security
│   │   │   ├── agent_validator.py # Complete agent config validation
│   │   │   ├── tool_validator.py  # Tool code execution validation
│   │   │   ├── mcp_validator.py   # MCP connectivity validation
│   │   │   └── validation_result.py # Validation result models
│   │   └── config/                # Configuration management
│   │       └── settings.py        # Pydantic settings with env vars
│   │
│   └── 📡 services/                # Application service layer
│       └── orchestrator_service.py # High-level service coordinating all operations
│
├── ⚙️  config/                     # Configuration files (JSON)
│   ├── tools.json                 # Pre-built tool definitions
│   ├── mcp.json                   # MCP server configurations
│   └── settings.json              # Application settings overrides
│
├── 💾 Runtime Data Directories
│   ├── agent_store/               # Dynamic agent instances
│   │   └── {agent_key}/           # Per-agent directories
│   │       ├── config.yaml        # Agent metadata & LLM config
│   │       ├── tools.py           # Custom agent tools
│   │       └── mcp_config.json    # Agent-specific MCP config
│   ├── documents/                 # Uploaded file storage
│   ├── data/                      # SQLite database files
│   │   ├── session_store.db       # Conversation history & messages
│   │   └── document_store.db      # Document chunks & metadata
│   └── logs/                      # Session & event logs
│       └── session_{id}.jsonl     # Structured event logs per session
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
- Application factory pattern with lifespan management
- CORS middleware configuration
- Dependency injection setup
- Professional FastAPI configuration with API versioning

### Agent System (`src/core/agents/`)

#### **BaseAgent** - Multi-Step Planner Loop
- **Structured Response Parsing**: Pydantic models ensure reliable JSON handling
- **Planning Loop**: Up to 8 iterations for complex multi-step tasks
- **Actions Supported**: `final`, `call_tool`, `call_mcp`
- **Conversation Memory**: Session store integration for context awareness
- **Tool Registration**: Decorator-based `@agent_tool` system
- **MCP Integration**: Dynamic tool discovery from MCP servers

#### **Orchestrator** - Multi-Agent Coordination
- **@mention Routing**: Natural agent collaboration via mentions
- **State Management**: Tracks active agents and conversation flow
- **Router Integration**: Intelligent agent selection and delegation
- **Error Handling**: Graceful degradation on agent failures

#### **Registry** - Dynamic Agent Discovery
- **Runtime Loading**: Discovers agents from `agent_store/` directory
- **Tool Registration**: Automatically loads `tools.py` from agent folders
- **MCP Configuration**: Per-agent MCP server management
- **Validation**: Pre-flight checks before agent instantiation

### LLM Integration (`src/core/llm/`)
- **Multi-Provider Support**: OpenAI, Anthropic Claude, Google Gemini
- **Streaming**: Real-time response streaming for all providers
- **Factory Pattern**: Dynamic provider selection based on config
- **Error Handling**: Automatic retry and fallback mechanisms
- **Token Management**: Configurable max tokens and temperature

### Memory System (`src/core/memory/`)

#### **Session Store** - Conversation Persistence
- **SQLite Storage**: Lightweight, file-based conversation history
- **Role-Based Messages**: Supports user, assistant, tool, mcp, system roles
- **Metadata Tracking**: Rich context for each message
- **History Management**: Configurable context window (20 messages default)
- **Multi-Group Support**: Isolated conversations per group

#### **RAG Store** - Document Knowledge
- **Document Processing**: PDF, DOCX, PPTX, Excel, images
- **Chunk Storage**: Intelligent text chunking for retrieval
- **Vector Search**: Semantic search capabilities (planned)
- **Metadata**: Document source tracking and provenance

### Validation System (`src/core/validation/`)
- **Agent Validator**: Complete agent config validation with runtime testing
- **Tool Validator**: Python code execution validation in isolation
- **MCP Validator**: Connectivity testing and tool discovery verification
- **Pre-Flight Checks**: Validate before saving to prevent runtime errors

### Telemetry & Analytics (`src/core/telemetry/`)
- **Session Logger**: Structured JSONL event logs per session
- **User Action Tracker**: Comprehensive user interaction analytics
- **LLM Logger**: Track all LLM calls with timing and token usage
- **Context Management**: Request-scoped logging context

### Services Layer (`src/services/`)
- **OrchestratorService**: High-level facade coordinating all operations
- **Lifecycle Management**: Agent registration, group management, health checks
- **Error Handling**: Centralized exception handling and logging
- **Clean Interface**: Simplified API for endpoint handlers

### API Endpoints (`src/api/v1/endpoints/`)
- **RESTful Design**: Resource-based endpoints with proper HTTP methods
- **Validation**: Pydantic request/response models for type safety
- **Error Handling**: Consistent error responses with proper status codes
- **User Action Tracking**: Automatic tracking of all user operations
- **Real-time Streaming**: SSE for live updates and notifications

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

### **Agent Management** (`/api/v1/agents`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | List all available agents with metadata |
| `GET` | `/{key}/details/` | Get detailed agent configuration |
| `POST` | `/create/` | Create new agent with validation |
| `PUT` | `/{key}/` | Update existing agent |
| `DELETE` | `/{key}/` | Delete agent and cleanup |
| `POST` | `/test-registration/` | Test agent registration without saving |

### **Group & Chat Management** (`/api/v1/groups`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | List all conversation groups |
| `POST` | `/create/` | Create new conversation group |
| `DELETE` | `/{group_id}/` | Delete group and history |
| `GET` | `/{group_id}/agents/` | Get agents in group |
| `POST` | `/{group_id}/agents/` | Add agent to group |
| `DELETE` | `/{group_id}/agents/{agent_key}/` | Remove agent from group |

### **Chat & Messaging** (`/api/v1/chat`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/groups/{group_id}/messages/` | Send message to group |
| `GET` | `/groups/{group_id}/messages/` | Get conversation history |
| `GET` | `/groups/{group_id}/events` | SSE stream for real-time events |
| `POST` | `/groups/{group_id}/documents/upload/` | Upload document for RAG |
| `POST` | `/groups/{group_id}/stop/` | Stop agent execution |

### **Tools Management** (`/api/v1/tools`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | List all configured tools |
| `POST` | `/` | Add new tool with code validation |
| `PUT` | `/{tool_id}` | Update existing tool |
| `DELETE` | `/{tool_id}` | Delete tool configuration |

### **MCP Server Management** (`/api/v1/mcp`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | List all MCP server configurations |
| `POST` | `/` | Add new MCP server with connectivity test |
| `PUT` | `/{mcp_id}` | Update MCP server configuration |
| `DELETE` | `/{mcp_id}` | Delete MCP server |

### **Validation Endpoints** (`/api/v1/validation`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/agent/` | Validate agent config before creation |
| `POST` | `/agent/folder/` | Validate existing agent folder |
| `POST` | `/tool/` | Validate tool configuration |
| `POST` | `/tool/code/` | Test tool code execution |
| `POST` | `/mcp/` | Validate MCP server config |
| `POST` | `/mcp/connectivity/` | Test MCP server connectivity |
| `GET` | `/templates/tools/` | Get tool code templates |
| `GET` | `/templates/mcp/` | Get MCP configuration templates |

### **Settings Management** (`/api/v1/settings`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Get current system settings |
| `POST` | `/` | Update system settings |
| `GET` | `/status/` | Get configuration status & diagnostics |

### **Logs & Analytics** (`/api/v1/logs`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/sessions/` | List all log sessions |
| `GET` | `/sessions/{session_id}/` | Get session details |
| `GET` | `/sessions/{session_id}/events/` | Get session events |
| `GET` | `/sessions/{session_id}/analytics/` | Get session analytics |
| `GET` | `/sessions/{session_id}/export/` | Export session logs |
| `GET` | `/user-actions/` | Get user action logs |
| `GET` | `/user-actions/summary/` | Get user action summary |

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

## ✅ **Code Quality & Testing**

### **Test Coverage: 59%**
- **179 tests passing** across comprehensive test suite
- **Critical paths covered**: Agent orchestration, document processing, API endpoints
- **Edge cases validated**: Error handling, encoding issues, async operations
- **Zero dead code**: 73 lines of unused code eliminated

### **Test Suite Breakdown**

#### **Document Processing** (64% coverage) ✅
- ✅ PDF extraction (PyMuPDF + fallback)
- ✅ DOCX extraction (paragraphs + tables)
- ✅ PPTX extraction (slides + content)
- ✅ CSV extraction (data + summary)
- ✅ Text extraction (encoding fallback)
- ✅ Image extraction (analysis)
- ✅ Error handling (corrupted files)

#### **Agent System** (48% coverage) ✅
- ✅ Multi-step planning workflows
- ✅ Context management & memory
- ✅ Tool selection & execution
- ✅ Error recovery mechanisms
- ✅ Sequential task handling

#### **API Endpoints** (100% coverage) ✅
- ✅ Agent CRUD operations
- ✅ Group management
- ✅ Message routing
- ✅ Document uploads
- ✅ Validation endpoints

### **Code Quality Verification**

#### **Linting (flake8)** ✅
```bash
flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics
# Result: 0 critical errors
```

#### **Type Safety (mypy)** ✅
```bash
mypy src/ --ignore-missing-imports
# Result: Type-safe with LLM SDK compatibility
```

#### **Code Cleanliness** ✅
- ✅ Zero syntax errors
- ✅ Zero undefined names
- ✅ Zero dead code
- ✅ Professional structure

### **Running Tests**

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=term-missing

# Run specific test suite
pytest tests/test_processor_comprehensive.py -v

# Run with detailed output
pytest -v --tb=short
```

### **Quality Metrics**
| Metric | Status | Details |
|--------|--------|---------|
| **Test Pass Rate** | ✅ 100% | 179/179 tests passing |
| **Coverage** | ✅ 59% | All critical paths covered |
| **Critical Errors** | ✅ 0 | flake8 verified |
| **Type Safety** | ✅ Yes | mypy verified |
| **Dead Code** | ✅ 0 lines | Eliminated 73 lines |
| **Edge Cases** | ✅ Tested | Error handling validated |

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