# ⚛️ AgentVerse Frontend

<div align="center">

![AgentVerse Logo](../logo-horizontal.svg)

**Professional Desktop Application for AI Agent Management**

*React 18 + TypeScript + Tauri + Professional Architecture*

</div>

Modern cross-platform desktop application built with **Tauri + React + TypeScript**, providing a professional user interface for managing AI agents, real-time chat, and comprehensive analytics. **Recently refactored with enterprise-grade architecture.**

[![React](https://img.shields.io/badge/React-18.2+-cyan.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://typescriptlang.org)
[![Tauri](https://img.shields.io/badge/Tauri-1.5+-orange.svg)](https://tauri.app)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.3+-teal.svg)](https://tailwindcss.com)
[![Zustand](https://img.shields.io/badge/Zustand-5.0+-green.svg)](https://zustand-demo.pmnd.rs)

---

## 🏗️ **NEW Professional Architecture**

**✨ Recently migrated from legacy structure to enterprise-grade architecture with:**
- **Zustand State Management** instead of React useState
- **Domain-separated API layer** with professional HTTP client
- **Shared component library** with consistent branding
- **TypeScript path aliases** for clean imports
- **Complete legacy code removal** for maintainability

```
frontend/
├── 📄 Configuration Files
│   ├── package.json                    # Dependencies, scripts, and project metadata
│   ├── package-lock.json              # Exact dependency versions lock file
│   ├── tsconfig.json                  # TypeScript compiler configuration with path aliases
│   ├── tsconfig.node.json             # Node.js specific TypeScript configuration
│   ├── vite.config.ts                 # Vite build tool configuration and plugins
│   ├── tailwind.config.js             # TailwindCSS utility classes configuration
│   ├── postcss.config.js              # CSS post-processing configuration
│   ├── index.html                     # Main HTML entry point for the application
│   └── README.md                      # This comprehensive documentation file
│
├── 📁 public/                         # Static Assets
│   ├── favicon.ico                    # Browser tab icon
│   ├── favicon.svg                    # Scalable vector icon
│   └── (other static assets)          # Images, icons, fonts
│
└── 📁 src/                           # Source Code (PROFESSIONAL ARCHITECTURE)
    ├── 📄 main.tsx                   # React application entry point and providers setup
    ├── 📄 App.tsx                    # ✅ MAIN APP COMPONENT (Migrated to Zustand stores)
    ├── 📄 App.css                    # Global application styles and animations
    ├── 📄 index.css                  # Base styles, Tailwind imports, and CSS variables
    ├── 📄 vite-env.d.ts             # Vite environment type declarations
    │
    ├── 📁 components/                # UI Components (ALL UPDATED TO NEW ARCHITECTURE)
    │   ├── 📄 Sidebar.tsx            # ✅ Navigation sidebar with group/agent management
    │   ├── 📄 MainWorkspace.tsx      # ✅ Primary chat interface with real-time messaging
    │   ├── 📄 EnhancedAgentCreationPanel.tsx # ✅ Agent creation wizard with validation
    │   ├── 📄 SettingsPanel.tsx      # ✅ System configuration and preferences
    │   ├── 📄 CommandPalette.tsx     # ✅ Quick actions with ⌘K shortcut support
    │   ├── 📄 ComprehensiveLogPanel.tsx # ✅ Advanced logging and analytics viewer
    │   ├── 📄 UserActivityDashboard.tsx # ✅ User analytics and activity tracking
    │   ├── 📄 DocumentsListPanel.tsx # ✅ Document management and file browser
    │   ├── 📄 ToolsManagementPanel.tsx # ✅ Tool configuration and management
    │   ├── 📄 McpManagementPanel.tsx # ✅ MCP server discovery and management
    │   ├── 📄 LogViewer.tsx          # ✅ Real-time session log streaming
    │   ├── 📄 LoadingOverlay.tsx     # Loading states and skeleton screens
    │   ├── 📄 ProgressBar.tsx        # Progress indicators and upload tracking
    │   ├── 📄 ErrorBoundary.tsx      # ✅ Error handling and graceful recovery
    │   ├── 📄 AnimatedSplashScreen.tsx # Professional app startup screen
    │   ├── 📄 BrandedComponents.tsx  # AgentVerse branded UI components
    │   ├── 📄 BrandLogo.tsx          # Company logo with multiple variants
    │   ├── 📄 HelpPanel.tsx          # Comprehensive help and documentation
    │   └── 📄 UnifiedHeader.tsx      # Application header with navigation
    │
    ├── 📁 contexts/                  # React Context Providers
    │   └── 📄 ThemeContext.tsx       # Dark/light theme management and persistence
    │
    ├── 📁 types/                     # Legacy Type Definitions (Still Used)
    │   └── 📄 index.ts               # Core type definitions for entities and API
    │
    ├── 📁 utils/                     # Utility Functions
    │   └── 📄 userActionLogger.ts    # ✅ User interaction tracking and analytics
    │
    └── 📁 shared/                    # ✨ NEW PROFESSIONAL SHARED ARCHITECTURE
        ├── 📄 index.ts               # Main shared exports for easy importing
        │
        ├── 📁 api/                   # Professional API Layer
        │   ├── 📄 index.ts           # API exports with backward compatibility wrapper
        │   │
        │   ├── 📁 client/            # HTTP Client Infrastructure
        │   │   └── 📄 http-client.ts # Professional HTTP client with retry, logging, timeouts
        │   │
        │   ├── 📁 endpoints/         # Domain-Separated API Endpoints
        │   │   ├── 📄 agents.api.ts  # Agent CRUD operations and lifecycle management
        │   │   ├── 📄 groups.api.ts  # Group management and messaging operations
        │   │   ├── 📄 logs.api.ts    # Logging and analytics API endpoints
        │   │   ├── 📄 mcp.api.ts     # MCP server discovery and management
        │   │   ├── 📄 settings.api.ts # Application settings and configuration
        │   │   └── 📄 tools.api.ts   # Tool management and configuration
        │   │
        │   └── 📁 types/             # API Type Definitions
        │       ├── 📄 entities.ts    # Core entity types (Agent, Group, Message, etc.)
        │       └── 📄 logs.ts        # Logging and analytics type definitions
        │
        ├── 📁 store/                 # Zustand State Management
        │   ├── 📄 index.ts           # Store exports and utility functions
        │   ├── 📄 app.store.ts       # Global app state (UI, modals, loading, theme)
        │   ├── 📄 groups.store.ts    # Groups, messages, and SSE connection management
        │   └── 📄 agents.store.ts    # Agent state and form management
        │
        ├── 📁 components/            # Shared UI Component Library
        │   └── 📁 ui/                # Base UI Components with AgentVerse Branding
        │       ├── 📄 index.ts       # UI component exports
        │       ├── 📄 Button.tsx     # Professional button with variants and states
        │       ├── 📄 Input.tsx      # Form input with validation and styling
        │       ├── 📄 Modal.tsx      # Accessible modal with animations
        │       └── 📄 Loading.tsx    # Loading spinners and progress indicators
        │
        ├── 📁 hooks/                 # Shared React Hooks
        │   ├── 📄 index.ts           # Hook exports for easy importing
        │   ├── 📄 useDebounce.ts     # Debounced value hook for search/input
        │   └── 📄 useModal.ts        # Modal state management hook
        │
        ├── 📁 types/                 # Shared Type Definitions
        │   └── 📄 common.ts          # Common types, interfaces, and utilities
        │
        ├── 📁 config/                # Application Configuration
        │   └── 📄 env.ts             # Environment variables with validation
        │
        └── 📁 constants/             # Application Constants
            └── 📄 app.ts             # App-wide constants and configuration values
```

---

## 📁 **Detailed File Documentation**

### 🔧 **Configuration Files**

| File | Purpose | Key Responsibilities |
|------|---------|---------------------|
| `package.json` | **Project manifest** | Dependencies, build scripts, metadata, Tauri configuration |
| `tsconfig.json` | **TypeScript config** | Compiler options, path aliases (`@/*` → `./src/*`) |
| `vite.config.ts` | **Build configuration** | Development server, build optimization, plugin setup |
| `tailwind.config.js` | **CSS framework** | Design system colors, spacing, responsive breakpoints |
| `index.html` | **App entry point** | HTML template, meta tags, app mounting point |

### ⚛️ **Core Application Files**

| File | Purpose | Key Features | Migration Status |
|------|---------|--------------|------------------|
| `main.tsx` | **React entry** | App mounting, providers setup, error boundaries | ✅ Stable |
| `App.tsx` | **Main component** | Layout, routing, global state, SSE connections | ✅ **Migrated to Zustand** |
| `App.css` | **Global styles** | Layout styles, animations, utility classes | ✅ Stable |
| `vite-env.d.ts` | **Type definitions** | Vite environment variables, module declarations | ✅ Updated |

### 🎨 **UI Components** (All Updated to New Architecture)

#### **Core Interface Components**
| Component | Purpose | Key Features | API Integration |
|-----------|---------|--------------|-----------------|
| `Sidebar.tsx` | **Navigation panel** | Group list, agent management, quick actions | ✅ Uses new groups/agents stores |
| `MainWorkspace.tsx` | **Primary interface** | Chat UI, message streaming, file uploads | ✅ Uses new messaging API |
| `CommandPalette.tsx` | **Quick actions** | ⌘K shortcut, fuzzy search, command execution | ✅ Uses new API endpoints |

#### **Agent Management Components**
| Component | Purpose | Key Features | API Integration |
|-----------|---------|--------------|-----------------|
| `EnhancedAgentCreationPanel.tsx` | **Agent creation** | Wizard UI, validation, tool selection | ✅ Uses agents.api.ts |
| `SettingsPanel.tsx` | **System config** | LLM settings, API keys, preferences | ✅ Uses settings.api.ts |
| `ToolsManagementPanel.tsx` | **Tool management** | Tool discovery, configuration, testing | ✅ Uses tools.api.ts |
| `McpManagementPanel.tsx` | **MCP servers** | Server discovery, management, configuration | ✅ Uses mcp.api.ts |

#### **Analytics & Monitoring Components**
| Component | Purpose | Key Features | API Integration |
|-----------|---------|--------------|-----------------|
| `UserActivityDashboard.tsx` | **User analytics** | Activity tracking, usage patterns, charts | ✅ Uses logs.api.ts |
| `ComprehensiveLogPanel.tsx` | **Advanced logging** | Session analysis, error tracking, metrics | ✅ Uses logs.api.ts |
| `LogViewer.tsx` | **Simple logs** | Real-time log streaming, filtering, search | ✅ Uses logs.api.ts |
| `DocumentsListPanel.tsx` | **Document management** | File browser, upload, search, management | ✅ Uses groups.api.ts |

#### **Utility Components**
| Component | Purpose | Key Features | Status |
|-----------|---------|--------------|--------|
| `LoadingOverlay.tsx` | **Loading states** | Skeleton screens, progress indicators | ✅ Stable |
| `ProgressBar.tsx` | **Progress tracking** | Upload progress, task completion bars | ✅ Stable |
| `ErrorBoundary.tsx` | **Error handling** | Graceful error recovery, error reporting | ✅ Updated API |
| `BrandedComponents.tsx` | **Brand components** | AgentVerse styled UI elements | ✅ Stable |
| `BrandLogo.tsx` | **Company branding** | Logo with multiple size variants | ✅ Stable |

### 🌐 **Shared Architecture** (NEW Professional Structure)

#### **🔌 API Layer** (`src/shared/api/`)
| File | Purpose | Key Responsibilities |
|------|---------|---------------------|
| `index.ts` | **API exports** | Centralized exports, backward compatibility wrapper |
| `client/http-client.ts` | **HTTP infrastructure** | Professional HTTP client with retry, logging, timeout |
| `endpoints/agents.api.ts` | **Agent operations** | CRUD operations, validation, lifecycle management |
| `endpoints/groups.api.ts` | **Group management** | Group CRUD, messaging, SSE connections, file uploads |
| `endpoints/logs.api.ts` | **Logging system** | Session logs, analytics, user activity tracking |
| `endpoints/mcp.api.ts` | **MCP integration** | Server discovery, management, configuration |
| `endpoints/settings.api.ts` | **Configuration** | App settings, preferences, system configuration |
| `endpoints/tools.api.ts` | **Tool management** | Tool discovery, configuration, testing |

#### **🏪 State Management** (`src/shared/store/`)
| File | Purpose | State Managed | Key Features |
|------|---------|---------------|--------------|
| `index.ts` | **Store exports** | Store utilities, reset functions | Centralized store management |
| `app.store.ts` | **Global app state** | UI state, modals, theme, loading | Persistent UI preferences |
| `groups.store.ts` | **Groups & messaging** | Groups, messages, SSE, documents | Real-time message updates |
| `agents.store.ts` | **Agent management** | Agents, forms, validation | Agent lifecycle management |

#### **🎨 UI Components** (`src/shared/components/ui/`)
| File | Purpose | Component Type | Features |
|------|---------|----------------|----------|
| `Button.tsx` | **Interactive buttons** | Base component | Variants, states, accessibility |
| `Input.tsx` | **Form inputs** | Base component | Validation, styling, error states |
| `Modal.tsx` | **Overlay dialogs** | Base component | Animations, accessibility, focus trap |
| `Loading.tsx` | **Loading indicators** | Utility component | Spinners, progress bars, skeletons |

#### **🪝 Shared Hooks** (`src/shared/hooks/`)
| File | Purpose | Hook Type | Use Cases |
|------|---------|-----------|-----------|
| `useDebounce.ts` | **Debounced values** | Performance | Search inputs, API calls |
| `useModal.ts` | **Modal management** | UI state | Modal open/close, state management |

#### **⚙️ Configuration & Types**
| File | Purpose | Contains |
|------|---------|----------|
| `config/env.ts` | **Environment config** | API URLs, feature flags, validation |
| `types/common.ts` | **Shared types** | Common interfaces, utility types |
| `constants/app.ts` | **App constants** | API endpoints, UI constants, defaults |

---

## 🔄 **Migration Summary**

### ✅ **What Was Successfully Migrated**

| Component | Before (Legacy) | After (Professional) | Status |
|-----------|----------------|---------------------|--------|
| **State Management** | React useState | Zustand stores with persistence | ✅ Complete |
| **API Layer** | Monolithic `services/api.ts` | Domain-separated endpoints | ✅ Complete |
| **Component Imports** | `../services/api` | `@/shared/api` | ✅ Complete |
| **File Structure** | Flat component structure | Feature-based architecture | ✅ Complete |
| **Type Safety** | Basic TypeScript | Comprehensive type definitions | ✅ Complete |

### 🗑️ **Legacy Code Removed**

| Removed | Reason | Replacement |
|---------|--------|-------------|
| `src/services/` folder | Monolithic, hard to maintain | `src/shared/api/endpoints/` |
| `src/features/` folder | Incomplete implementation | Integrated into shared architecture |
| `App-new.tsx` backup | No longer needed | Integrated into main App.tsx |
| Manual useState management | Inefficient, hard to sync | Zustand stores with persistence |

---

## 🚀 **Development Workflow**

### **Development Commands**
```bash
# Start development server
npm run dev                 # Runs on http://localhost:1420

# Type checking
npm run build              # TypeScript compilation + Vite build
npx tsc --noEmit          # Type checking only

# Code quality
npm run lint              # ESLint checking
npm run lint -- --fix    # Auto-fix ESLint issues
```

### **Desktop App Development**
```bash
# Desktop development
npm run tauri dev         # Start desktop app in dev mode

# Desktop builds
npm run tauri build       # Build production desktop app
```

### **Architecture Guidelines**

#### **1. Import Patterns**
```typescript
// ✅ CORRECT: Use path aliases
import { apiService } from '@/shared/api';
import { useAppStore } from '@/shared/store';
import { Button } from '@/shared/components/ui';

// ❌ WRONG: Relative imports for shared code
import { apiService } from '../../../shared/api';
```

#### **2. State Management**
```typescript
// ✅ CORRECT: Use Zustand stores
const { groups, loadGroups } = useGroupsStore();
const { sidebarExpanded, setSidebarExpanded } = useAppStore();

// ❌ WRONG: Manual useState for global state
const [groups, setGroups] = useState([]);
```

#### **3. API Integration**
```typescript
// ✅ CORRECT: Use domain-specific APIs
import { groupsApi } from '@/shared/api/endpoints/groups.api';
await groupsApi.createGroup({ name: 'New Group' });

// ❌ WRONG: Direct fetch calls
fetch('/api/groups', { method: 'POST', ... });
```

---

## 🎯 **Key Features**

### **🎨 Professional UI/UX**
- **AgentVerse Branding**: Consistent violet/indigo/purple color scheme
- **Glass Morphism**: Modern glass effects and backdrop blur
- **Responsive Design**: Adaptive layouts for different screen sizes
- **Dark/Light Theme**: System-aware theme with smooth transitions
- **Accessibility**: ARIA labels, keyboard navigation, screen reader support

### **⚡ Real-time Capabilities**
- **Live Chat**: WebSocket-based real-time messaging with SSE
- **Streaming Responses**: Live AI response streaming with typing indicators
- **Auto-refresh**: Automatic data updates for dynamic content
- **Event Notifications**: Toast notifications for system events

### **🤖 Agent Management**
- **Visual Creation**: Step-by-step agent creation wizard
- **Tool Integration**: Comprehensive tool and MCP server management
- **Group Organization**: Create and manage conversation groups
- **Real-time Monitoring**: Live agent status and performance metrics

### **📊 Analytics & Monitoring**
- **Session Analytics**: Detailed conversation statistics and insights
- **Performance Metrics**: Response times, success rates, token usage
- **User Activity**: Action logging and usage pattern analysis
- **Error Tracking**: Comprehensive error monitoring and reporting

---

## 🛠️ **Technology Stack**

### **Core Framework**
- **React 18** - Modern React with concurrent features
- **TypeScript 5** - Type-safe JavaScript with strict configuration
- **Vite 4** - Lightning-fast build tool and development server
- **Tauri 1.5** - Rust-based desktop app framework

### **State Management**
- **Zustand 5** - Simple, scalable state management with persistence
- **React Context** - Theme management and global providers

### **UI & Styling**
- **TailwindCSS 3** - Utility-first CSS framework
- **Framer Motion 12** - Production-ready animation library
- **Headless UI 2** - Unstyled, accessible UI components
- **Heroicons 2** - Beautiful hand-crafted SVG icons

### **Development Tools**
- **ESLint 8** - JavaScript/TypeScript linting
- **TypeScript ESLint** - TypeScript-specific linting rules
- **PostCSS & Autoprefixer** - CSS post-processing

---

## 🔒 **Security & Best Practices**

### **Type Safety**
- **Strict TypeScript**: No implicit any, strict null checks
- **API Type Safety**: Comprehensive type definitions for all endpoints
- **Runtime Validation**: Input validation with proper error handling

### **Secure Communication**
- **CORS Configuration**: Proper cross-origin request handling
- **Request Validation**: Client-side input validation and sanitization
- **Error Boundaries**: Graceful error handling and user feedback

### **Performance Optimization**
- **Code Splitting**: Optimized bundle sizes with Vite
- **Lazy Loading**: Component and route-based lazy loading
- **Memoization**: React.memo and useMemo for expensive operations

---

## 📦 **Build & Deployment**

### **Development Build**
```bash
npm run dev                # Development server with hot reload
npm run build             # Production build with optimization
npm run preview           # Preview production build locally
```

### **Desktop Distribution**
```bash
npm run tauri build       # Build desktop app for current platform
```

**Output Formats:**
- **macOS**: `.dmg` installer
- **Windows**: `.msi` installer
- **Linux**: `.deb` package, `.AppImage`

---

## 🧪 **Testing & Quality Assurance**

### **Code Quality Tools**
- **ESLint**: Comprehensive linting rules
- **TypeScript**: Strict type checking
- **Prettier**: Code formatting consistency

### **Testing Strategy** (Planned)
- **Unit Tests**: Component and utility function testing
- **Integration Tests**: API integration and data flow testing
- **E2E Tests**: Full application workflow testing

---

## 🤝 **Contributing Guidelines**

### **Code Style**
- Use TypeScript path aliases (`@/shared/*`)
- Follow ESLint configuration
- Use Zustand stores for state management
- Implement proper error boundaries

### **Component Development**
- Create reusable components in `shared/components/ui/`
- Use AgentVerse branding guidelines
- Implement accessibility features
- Add proper TypeScript types

### **API Integration**
- Use domain-specific API endpoints
- Implement proper error handling
- Add loading states and user feedback
- Follow API response type definitions

---

**⚛️ AgentVerse Frontend - Professional Desktop Application**

*Built with React 18, TypeScript, Zustand, and Tauri for enterprise-grade AI agent management.*

---

**Architecture Status: ✅ MIGRATION COMPLETE**

*All legacy code removed, new professional architecture implemented, all components updated to use Zustand stores and domain-separated API layer.*