
## ⚡ Quickstart

```bash
# 1. Setup Python environment
python3.12 -m venv .venv && source .venv/bin/activate   # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt

# 2. Configure secrets
cp .env.example .env
# Fill in OPENAI_API_KEY, GITHUB_TOKEN, etc.

# 3. Install Node.js dependencies for React frontend
cd desktop-ui
npm install
cd ..

# 4. Run the unified backend and frontend
python app.py
```

Open:
- FastAPI API: [http://localhost:8000](http://localhost:8000)
- React Dev UI: [http://localhost:1420](http://localhost:1420)
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---






## 🛠️ Development Guide

### Project Layout

```
app/
  agents/         # Planner, SchemaAgent, ApexAgent, LWC, UI Tests, VCS, Deploy
  api/            # FastAPI endpoints
  llm/            # LLM base + providers
  mcp/            # Salesforce, GitHub, Playwright stubs
  memory/         # Session store + RAG
  telemetry/      # Event bus + logging
  tools/          # CSV loader, JSON writer, filesystem utils
desktop-ui/       # React + Tauri frontend
workspace/        # Per-session outputs
logs/             # Detailed run logs
.env.example      # Secrets template
app.py            # Unified entry point
```


### Configuration

* **`.env`** — secrets & keys (OPENAI_API_KEY, GITHUB_TOKEN, etc.)
* **`config.yaml`** — LLM, GitHub repo, Salesforce org, coverage gates

### Extending

* **New LLM** → implement `LLMProvider` in `app/llm/` and register in `factory.py`.
* **New Agent** → create under `app/agents/`

---

## 🐞 Debugging & Logs

* **Session logs** → `workspace/sessions/<sid>/logs.md`
* **Run logs** → `logs/sessions/<sid>/run.log`
