# AgentVerse Frontend

Native desktop UI for AI agent collaboration.

## 🎯 What's Inside

Cross-platform desktop application (Tauri) providing real-time interface for agent orchestration, conversations, and document management.

**Tech Stack**: React 18 • TypeScript 5 • Tauri 1.5 • Zustand • TailwindCSS • Framer Motion

## 🚀 Quick Start

```bash
cd frontend
npm install
npm run dev  # Opens at http://localhost:1420
```

### Build Desktop App
```bash
npm run tauri build
```

## 📁 Structure

```
src/
├── components/
│   ├── core/           Layout infrastructure (Header, Footer, Panels)
│   ├── modals/         Management interfaces (Settings, Logs)
│   ├── views/          Main screens (Chat, Studio, Admin)
│   └── shared/         Reusable UI components
│
├── lib/
│   ├── api/            HTTP client + backend endpoints
│   ├── stores/         Zustand state management
│   ├── hooks/          React hooks
│   └── types.ts        TypeScript definitions
│
└── App.tsx             Root component
```

## ✨ Core Features

**Real-time Communication**
- SSE streaming from backend
- Live agent response rendering
- Tool execution updates
- Event telemetry display

**UI Components**
- Native desktop chrome (Tauri)
- Dark mode support
- Sliding panels and modals
- Command palette (⌘K)
- Drag & drop file uploads

**State Management**
- Zustand for global state
- Persistent storage
- Optimistic UI updates
- SSE connection handling

## 🎨 Component Architecture

### Core Infrastructure
- **AppHeader** - Top navigation bar
- **AppFooter** - Status and notifications
- **SlidingPanel** - Reusable side panels

### Views
- **ConversationView** - Multi-agent chat interface
- **AgentStudio** - Creation workspace
- **AdminView** - System dashboard

### Shared Components
- Branded UI kit (buttons, inputs, cards)
- Document viewer
- Log display
- Error boundaries

## 📡 API Integration

HTTP client connects to `localhost:8000`:

**Endpoints**:
- `/api/v1/agents/` - Entity CRUD
- `/api/v1/groups/` - Conversation management
- `/api/v1/groups/{id}/messages/` - SSE streaming
- `/api/v1/settings/` - Configuration
- `/api/v1/logs/` - Event retrieval

**Real-time**: Server-Sent Events for live updates

## 🔐 State Stores

- **app** - Theme, UI state, panel visibility
- **auth** - MCP OAuth flow
- **groups** - Conversations and messages
- **agents** - Entity registry

## 🧪 Testing

```bash
npm run test              # Vitest
npm run test:coverage     # Coverage report
npm run test:ui           # Interactive UI
```

## 🛠️ Development

```bash
npm run dev       # Dev server with HMR
npm run build     # Production build
npm run lint      # ESLint
npm run preview   # Preview build
```

## 📦 Build Metrics

- Bundle: ~792 KB (gzip: ~212 KB)
- CSS: ~92 KB (gzip: ~14 KB)
- Zero TypeScript errors
- Full type coverage

## 📄 License

See main repository for license information.
