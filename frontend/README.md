# Agentic SF Desktop - React + Tauri Frontend

This is the desktop application frontend for the Agentic Salesforce Developer Assistant, built with React, Vite, and Tauri.

## 🏗️ Architecture

```
┌─────────────────────────┐  ┌──────────────────────────────┐
│   React + Vite + Tauri  │  │      Python Backend          │
│   (Desktop Frontend)    │  │  ┌─────────────────────────┐  │
│                         │  │  │    FastAPI Wrapper      │  │
│  ├─ Components          │◄─┤  │  (api_server.py)        │  │
│  ├─ State Management    │  │  └─────────────────────────┘  │
│  ├─ Real-time Events    │  │  ┌─────────────────────────┐  │
│  └─ Tauri Commands      │  │  │   Existing App/         │  │
│                         │  │  │   (Untouched)           │  │
└─────────────────────────┘  │  │  ├─ agents/             │  │
                             │  │  ├─ llm/                │  │
                             │  │  ├─ memory/             │  │
                             │  │  └─ orchestrator/       │  │
                             │  └─────────────────────────┘  │
                             └──────────────────────────────┘
```

## 🚀 Development

### Prerequisites

- Node.js 18+
- Rust (for Tauri)
- Python 3.9+ (for backend)

### Quick Start

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start development (from project root):**
   ```bash
   python start_dual_frontend.py
   ```

   This starts:
   - 🎯 Gradio UI: `http://localhost:7860`
   - 🚀 FastAPI: `http://localhost:8000` 
   - ⚛️ React Dev: `http://localhost:1420`

3. **Manual development:**
   ```bash
   # Terminal 1: Start Python backend
   python api_server.py
   
   # Terminal 2: Start React dev server
   cd desktop-ui
   npm run dev
   ```

### Desktop App

1. **Install Tauri CLI:**
   ```bash
   cargo install tauri-cli
   ```

2. **Run desktop app:**
   ```bash
   npm run tauri dev
   ```

3. **Build for production:**
   ```bash
   npm run tauri build
   ```

   This generates:
   - **macOS**: `.dmg` file in `src-tauri/target/release/bundle/dmg/`
   - **Windows**: `.exe` file in `src-tauri/target/release/bundle/msi/`

## 📁 Project Structure

```
desktop-ui/
├── src/
│   ├── components/          # React components
│   │   ├── GroupManager.tsx
│   │   ├── AgentManager.tsx
│   │   ├── ChatInterface.tsx
│   │   ├── DocumentManager.tsx
│   │   └── EventsFeed.tsx
│   ├── services/
│   │   └── api.ts          # FastAPI client
│   ├── types/
│   │   └── index.ts        # TypeScript types
│   └── App.tsx             # Main app component
├── src-tauri/              # Tauri Rust backend
│   ├── src/main.rs         # Tauri main
│   ├── Cargo.toml          # Rust dependencies
│   └── tauri.conf.json     # Tauri config
├── package.json
└── vite.config.ts
```

## 🎨 UI Components

The React UI replicates the Gradio interface with:

- **GroupManager**: Create/select/delete agent groups
- **AgentManager**: Add/remove agents from groups  
- **ChatInterface**: Chat with agents in selected group
- **DocumentManager**: Upload files for agent context
- **EventsFeed**: Real-time agent activity stream

## 🔗 API Integration

The React app communicates with the Python backend via REST API:

- `GET /api/groups` - List groups
- `POST /api/groups` - Create group
- `GET /api/agents/available` - List all agents
- `POST /api/groups/{id}/messages` - Send message to agent
- `GET /api/groups/{id}/events` - Stream real-time events

## 📱 Desktop Features

- **Native window management**
- **System tray integration** 
- **Auto-updater support**
- **Cross-platform**: macOS, Windows, Linux
- **Small bundle size** (~15MB vs 100MB+ Electron)

## 🔧 Configuration

### Tauri Config

Edit `src-tauri/tauri.conf.json`:
- Window size/position
- Bundle settings
- Security permissions
- Auto-updater settings

### Vite Config

Edit `vite.config.ts`:
- Dev server port (default: 1420)
- Build optimizations
- Plugin configuration

## 📦 Packaging

### macOS (.dmg)
```bash
npm run tauri build
# Output: src-tauri/target/release/bundle/dmg/
```

### Windows (.msi)
```bash
npm run tauri build
# Output: src-tauri/target/release/bundle/msi/
```

### Linux (.deb/.appimage)
```bash
npm run tauri build
# Output: src-tauri/target/release/bundle/deb/ or appimage/
```

## 🐛 Troubleshooting

### Port Conflicts
- Gradio: 7860
- FastAPI: 8000  
- React Dev: 1420

### Tauri Build Issues
- Ensure Rust is installed: `rustc --version`
- Update Tauri: `cargo install tauri-cli --force`
- Clear cache: `cargo clean`

### API Connection Issues
- Check FastAPI is running on port 8000
- Check CORS settings in `api_server.py`
- Verify API endpoints with `/docs`

## 🚀 Production Deployment

1. **Build React:**
   ```bash
   npm run build
   ```

2. **Package desktop app:**
   ```bash
   npm run tauri build
   ```

3. **Distribute:**
   - Upload `.dmg` to Mac App Store or distribute directly
   - Upload `.msi` to Microsoft Store or distribute directly
   - Package `.deb` for Linux package managers

## 🔄 Dual Frontend Benefits

- ✅ **Development**: Use familiar Gradio UI
- ✅ **Production**: Ship polished desktop app  
- ✅ **Same Backend**: No code duplication
- ✅ **Gradual Migration**: Switch at your own pace
- ✅ **Testing**: Compare UIs side-by-side