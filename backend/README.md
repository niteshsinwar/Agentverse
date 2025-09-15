# Agentic SF Developer Backend

Professional Python backend for the Agentic Salesforce Developer Assistant.

## Architecture Overview

This backend follows industry-standard Python web application patterns with clean separation of concerns:

```
backend/
├── server.py                    # Application entry point
├── requirements.txt             # Python dependencies
├── agent_store/                 # Agent instances (mutable data)
│   ├── agent_1/                 # Individual agent configurations
│   ├── agent_2/
│   ├── TEMPLATE/               # Agent template
│   └── ...
├── data/                        # Database files
├── documents/                   # Document uploads
├── logs/                        # Session logs
└── src/                         # Source code (immutable)
    ├── api/                     # API layer (FastAPI routes)
    │   └── v1/                  # API version 1
    │       ├── endpoints/       # Route handlers
    │       ├── models/          # Request/response schemas
    │       └── dependencies.py  # Dependency injection
    ├── core/                    # Business logic layer
    │   ├── agents/              # Agent system logic
    │   ├── llm/                 # LLM providers
    │   ├── memory/              # Session management
    │   ├── config/              # Configuration
    │   ├── validation/          # Startup validation
    │   └── ...
    └── services/                # Service layer
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

This structure ensures the backend can grow from a simple API to a comprehensive system while maintaining code quality and developer productivity.