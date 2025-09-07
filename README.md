# Agentic SF Dev — Gradio MVP

An **autonomous Salesforce Developer assistant** that combines:

- 🔗 **MCP integrations**: Salesforce, GitHub, Playwright (UI testing)
- 🤖 **LLM-agnostic orchestration**: OpenAI, Gemini, Azure OpenAI, or vLLM
- 🧠 **Per-session memory + RAG** for contextual reasoning
- 🛠️ **Agent pipeline** for schema, Apex/LWC updates, static scans, UI tests, PR creation, and deploys
- ✅ **Automated test lifecycle**: CSV → JSON → Playwright → re-run from UI
- 🖥️ **Gradio UI** with chat panel, session sidebar, test manager, and live event feed

---

## 📌 Audience

- **Project Managers** → Track requests and defects across auditable sessions.  
- **Salesforce Developers** → Generate, update, and test Apex, LWC, objects, and fields.  
- **Python Developers** → Extend or debug by adding new agents, MCP clients, or LLM providers.  

---

## ⚡ Quickstart

```bash
# 1. Setup environment
python -m venv .venv && source .venv/bin/activate   # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt

# 2. Configure secrets
cp .env.example .env
# Fill in OPENAI_API_KEY, GITHUB_TOKEN, etc.

# 3. Run the app
python run_gradio.py
````

Open: [http://localhost:7860](http://localhost:7860)

---

## 🖥️ UI Overview

### **Sessions Sidebar**

* Sessions are **auto-created** when you type.
* Sidebar shows all sessions (newest first).
* Click to switch between sessions.

### **Chat / Workflow**

* Ask in plain English:

  > *“Add Discount\_\_c to Opportunity and expose in Cart LWC, then deploy to Sandbox.”*
* Agents execute pipeline → JSON summary (branch, PR link, deploy status).

### **Tests**

* Upload or generate a **CSV test file**.
* Each row = one test case → LLM converts to **Playwright JSON**.
* First-run executes new tests with Playwright.
* Saved JSON test scripts can be re-run **without LLM**.

Artifacts saved under:

```
workspace/sessions/<sid>/
  logs.md
  status.json
  TestCases/uploaded-file.csv
  json_scripts/*.json
```

### **Live Events**

* Real-time feed showing:

  * Current **agent**
  * **MCP tool** in use
  * Parameters passed (sanitized)

---

## 🔄 End-to-End Workflow

```mermaid
flowchart TD
    A[User Prompt] -->|Natural language| B[Planner Agent]
    B --> C[Spec Gate]
    C --> D[Schema Agent]
    D --> E[Apex Agent]
    E --> F[LWC Agent]
    F --> G[Static Scan]
    G --> H[UI Test Agent]
    H --> I[VCS Agent (PR)]
    I --> J[Deploy Agent]

    subgraph MCP Integrations
        D -.-> SF[Salesforce MCP]
        E -.-> SF
        F -.-> SF
        H -.-> PW[Playwright MCP]
        I -.-> GH[GitHub MCP]
    end

    K[CSV Test Cases] --> L[TestPlan Agent]
    L --> M[Playwright JSON Scripts]
    M --> H
```

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
  ui/             # Gradio app
workspace/        # Per-session outputs
logs/             # Detailed run logs
config.yaml       # Model & MCP config
.env.example      # Secrets template
run_gradio.py     # Entry point
```

### Configuration

* **`.env`** — secrets & keys (OPENAI\_API\_KEY, GITHUB\_TOKEN, etc.)
* **`config.yaml`** — LLM, GitHub repo, Salesforce org, coverage gates

### Extending

* **New LLM** → implement `LLMProvider` in `app/llm/` and register in `factory.py`.
* **New Agent** → create under `app/agents/`, wire into `graph.py`.
* **Real MCP** → update `app/mcp/client.py` to call your stdio/WebSocket servers.

---

## 🐞 Debugging & Logs

* **Session logs** → `workspace/sessions/<sid>/logs.md`
* **Run logs** → `logs/sessions/<sid>/run.log`
* **Artifacts** → JSON scripts, CSV files, status JSON

**Live Debugging** → Use **Live Events tab** for agent & MCP tool timeline.

### Common Issues

* **Empty SID?** → Ensure `ensure_sid()` wraps all actions.
* **Dataset warning?** → Always return `gr.Dataset(samples=[...])`.
* **IndentationError in agents?** → Align `bus.emit("agent.finished")` with other steps.

---

## 📦 Packaging as Desktop App

Since this runs as a **Gradio single-process app**, you can ship it:

```bash
pip install pyinstaller
pyinstaller --onefile --name "AgenticSFDev" run_gradio.py
```

Creates a `dist/AgenticSFDev` binary (wrap in `.app` on macOS).

---

## 🔮 Roadmap

* [ ] Pre-load prompt packs for Salesforce flows (login, record edit, save + toast assert).
* [ ] Replace MCP stubs with live Salesforce/GitHub/Playwright integrations.
* [ ] CI/CD integration for regression test plans.
* [ ] Richer embeddings-based RAG per session.
* [ ] Export session artifacts as shareable bundles.

---

## 🤝 Contributing

* **Salesforce Devs** → add more schema, Apex, LWC agents
* **Python Devs** → improve MCP clients, add new LLM providers
* **Project Managers** → track work via session logs & artifacts

---

## 📜 License

MIT (prototype/demo use)


