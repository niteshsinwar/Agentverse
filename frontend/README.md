# AgentVerse Frontend

A modern React + TypeScript desktop application for multi-agent orchestration and management.

## 📋 Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Code Quality Metrics](#code-quality-metrics)
- [Project Structure](#project-structure)
- [Technology Stack](#technology-stack)
- [Getting Started](#getting-started)
- [Development](#development)
- [Testing](#testing)
- [Build](#build)
- [Code Analysis](#code-analysis)

## 🎯 Overview

AgentVerse Frontend is a desktop application built with Tauri that provides a beautiful, performant interface for managing AI agents, groups, tools, and MCP servers. It features real-time updates via Server-Sent Events (SSE), in-stream self-reflection indicators, comprehensive logging, and a polished UI with dark mode support.

## 🏗️ Architecture

### **Design Patterns**
- **State Management**: Zustand for lightweight, performant global state
- **API Layer**: Centralized HTTP client with interceptors and logging
- **Component Architecture**: Atomic design with branded components
- **Type Safety**: Full TypeScript coverage with strict mode
- **Real-time Updates**: SSE (Server-Sent Events) for live message streaming, tool telemetry, and reflective planning states

### **Key Architectural Decisions**

1. **Zustand over Redux**
   - Simpler API, less boilerplate
   - Better TypeScript support
   - Smaller bundle size (~3KB vs ~15KB)
   - Built-in persistence middleware

2. **Tauri over Electron**
   - Smaller binary size (~600KB vs ~120MB)
   - Better performance (Rust backend)
   - Lower memory footprint
   - Native OS integration

3. **Vite over Webpack**
   - Faster development server (instant HMR)
   - Better build times (~2s vs ~30s)
   - Modern ES modules support

## 📊 Code Quality Metrics

### **Build Status**
✅ **Production Build**: Successful
✅ **TypeScript**: Zero compilation errors
✅ **Bundle Size**: 718.27 KB (gzip: 196.04 KB)
✅ **CSS Size**: 81.84 KB (gzip: 12.72 KB)

### **Code Analysis Results**
- **Total Lines of Code**: ~13,559 lines
- **TypeScript Files**: 65 files
- **Components**: 17 components
- **API Endpoints**: 6 endpoint modules
- **Stores**: 3 Zustand stores
- **Dead Code Removed**: 6 functions + 4 components + 2 files

### **Dead Code Elimination**
- **Unused Components Removed**: 4 (BrandedAlert, BrandedSpinner, LoadingOverlay, UnifiedHeader)
- **Unused Functions Removed**: 4 (trackAgentCreation, trackToolCreation, trackMcpCreation, trackFormValidationError)
- **Files Deleted**: 2 (LoadingOverlay.tsx, UnifiedHeader.tsx)
- **Lines Removed**: ~350 lines
- **CSS Reduction**: 4.45 KB (86.29 KB → 81.84 KB)

### **Testing Infrastructure**
- **Framework**: Vitest + React Testing Library
- **Coverage Provider**: v8
- **Coverage Targets**: 70% per file (lines, functions, branches, statements)
- **Test Setup**: Configured with mocks for window.matchMedia, IntersectionObserver, ResizeObserver
- **Scripts**: test, test:ui, test:coverage, test:watch

## 🛠️ Technology Stack

### **Core**
- **React 18.2**: UI library with hooks and concurrent features
- **TypeScript 5.0**: Type-safe JavaScript with strict mode
- **Tauri 1.5**: Rust-based desktop framework
- **Vite 4.4**: Next-generation frontend tooling

### **State & Data**
- **Zustand 5.0**: Lightweight state management
- **Server-Sent Events**: Real-time message streaming

### **UI & Styling**
- **Tailwind CSS 3.3**: Utility-first CSS framework
- **Framer Motion 12.23**: Animation library
- **Headless UI 2.2**: Unstyled, accessible components
- **Heroicons 2.2**: Beautiful hand-crafted SVG icons
- **Lucide React 0.263**: Icon library

### **Development**
- **Vitest 3.2**: Fast unit test framework
- **React Testing Library 16.3**: Component testing
- **ts-prune 0.10**: Dead code detection
- **ESLint**: Code linting

## 🚀 Getting Started

### **Prerequisites**
- Node.js 18+ and npm
- Rust 1.70+ (for Tauri)

### **Installation**
```bash
npm install
```

### **Development Server**
```bash
npm run dev
```

## 🧪 Testing

```bash
# Run tests in watch mode
npm run test

# Run tests with coverage
npm run test:coverage

# Interactive UI
npm run test:ui
```

## 🏗️ Build

```bash
# Production build
npm run build

# Build stats
dist/index.html               0.77 kB │ gzip:   0.43 kB
dist/assets/index.css        81.84 kB │ gzip:  12.72 kB
dist/assets/index.js        718.27 kB │ gzip: 196.04 kB
```

## 🔍 Code Analysis

### **Dead Code Detection**
```bash
npx ts-prune --project tsconfig.json
```

Results documented in [DEAD_CODE_ANALYSIS.md](./DEAD_CODE_ANALYSIS.md)

## 📄 License

See the main repository for license information.
