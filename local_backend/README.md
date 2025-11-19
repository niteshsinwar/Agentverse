# AgentVerse Backend

Local orchestration server for AI agents.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10--3.12-blue.svg)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-0.3+-purple.svg)](https://langchain.com)

## 🎯 What's Inside

Local HTTP server (`localhost:8000`) providing agent orchestration, multi-LLM integration, document processing, and real-time streaming.

**Tech Stack**: FastAPI • LangChain 0.3 • Official MCP SDK • ChromaDB • SQLite • Pydantic

## 🚀 Quick Start

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env
# Add LLM API keys to .env
python server.py
```

**Verify**: http://localhost:8000/docs

## 📁 Structure

```
backend/
├── src/
│   ├── api/v1/endpoints/    REST API routes
│   ├── services/            Business logic layer
│   └── core/
│       ├── agents/          LangChain framework
│       ├── llm/             Multi-provider integration
│       ├── memory/          SQLite + ChromaDB
│       ├── mcp/             Protocol client
│       ├── document_processing/  Multi-format support
│       └── telemetry/       Event logging
│
├── agent_store/             User-defined entities
├── config/                  System settings
├── data/                    SQLite databases
├── chroma_db/              Vector embeddings
└── documents/              Uploaded files
```

## 🏗️ Core Systems

**Agent Framework (LangChain 0.3+)**
- ReAct agent pattern with tool calling
- Multi-agent coordination
- @mention-based routing
- Custom Python tool support
- MCP server integration

**Document Intelligence (RAG)**
- 40+ format support (PDF, DOCX, images, code)
- Semantic chunking pipeline
- Embedding generation (Gemini/OpenAI/Anthropic)
- ChromaDB vector storage
- Time-decay retrieval weighting

**Conversation Memory**
- SQLite persistence
- Message history with metadata
- Automatic summarization
- Threshold-based compression

**Real-time Streaming**
- Server-Sent Events (SSE)
- Live agent responses
- Tool execution updates
- Event telemetry

**MCP Protocol**
- Official Anthropic SDK
- Subprocess lifecycle management
- Tool discovery and registration
- OAuth flow for remote servers

## 📝 API Structure

REST endpoints at `/api/v1/`:

- **CRUD Operations** - Entity management
- **Conversation Streaming** - SSE message flow
- **Document Upload** - Multi-format processing
- **Configuration** - System settings
- **Telemetry** - Event logs and analytics

Full documentation: http://localhost:8000/docs

## 🔧 Configuration

**`config/settings.json`** - System settings:
```json
{
  "llm_provider": "gemini",
  "llm_model": "gemini-2.5-flash",
  "llm_temperature": 0.2,
  "max_upload_size_mb": 9,
  "rag_top_k": 5,
  "conversation_summary_trigger_count": 20
}
```

**`.env`** - API credentials:
```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...
GITHUB_TOKEN=ghp-...
```

## 💬 Message Flow

1. HTTP request → API endpoint
2. Persist to SQLite
3. RAG retrieval from ChromaDB
4. Route to LangChain agent
5. Execute with tools/MCP
6. Stream via SSE
7. Store response
8. Trigger summarization

## 📄 Document Pipeline

1. Upload → `documents/uploads/`
2. Content extraction (format-specific)
3. Semantic chunking
4. Embedding generation
5. ChromaDB storage
6. Available for RAG

## 🗄️ Storage

**SQLite** (`data/app.db`):
- Conversations and messages
- Entity metadata
- Summaries and telemetry

**ChromaDB** (`chroma_db/`):
- Document embeddings
- Semantic search index

**Filesystem**:
- Agent definitions (`agent_store/`)
- Uploaded documents (`documents/`)
- Working files (`workspace/`)

## 🛠️ Development

```bash
python server.py         # Auto-reload enabled

# Code quality
black src/              # Format
flake8 src/             # Lint
mypy src/               # Type check
```

## 🚀 Production

```bash
# Gunicorn (Linux/macOS)
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker server:app

# Uvicorn (Windows)
pip install uvicorn[standard]
uvicorn server:app --workers 4
```

## 🛡️ Security

- ✅ Local-first architecture
- ✅ Environment-based credentials
- ✅ File validation and sanitization
- ✅ CORS restricted to localhost
- ✅ Pydantic request validation
- ✅ Parameterized SQL queries

## 🐛 Troubleshooting

**Port 8000 in use**
```bash
lsof -ti:8000 | xargs kill -9   # macOS/Linux
netstat -ano | findstr :8000    # Windows
```

**Database locked**
- Close connections
- Delete `data/app.db-wal` and `app.db-shm`

**Module errors**
- Activate venv: `source venv/bin/activate`
- Reinstall: `pip install -r requirements.txt`

**MCP failures**
- Check Node.js installed
- Test: `npx @modelcontextprotocol/server-filesystem --help`

## 📄 License

See main repository for license information.

---

**FastAPI + LangChain 0.3 + Official MCP SDK**
