import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  QuestionMarkCircleIcon,
  BookOpenIcon,
  RocketLaunchIcon,
  WrenchScrewdriverIcon,
  ServerIcon,
  ArrowRightIcon,
  ChevronRightIcon,
  ChevronDownIcon,
  LightBulbIcon,

  CpuChipIcon,
  DocumentTextIcon,
  PlayIcon,
  UserGroupIcon,
  PlusIcon
} from '@heroicons/react/24/outline';
import { BrandedCard, BrandedButton, BrandedBadge } from './BrandedComponents';
import { BrandLogo } from './BrandLogo';

interface HelpPanelProps {
  isVisible: boolean;
}

interface HelpSection {
  id: string;
  title: string;
  icon: React.ComponentType<any>;
  badge?: string;
  description: string;
  content: React.ReactNode;
}

export const HelpPanel: React.FC<HelpPanelProps> = ({ isVisible: _isVisible }) => {
  const [activeSection, setActiveSection] = useState<string>('overview');
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['overview']));

  const toggleSection = (sectionId: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }
    setExpandedSections(newExpanded);
  };

  const helpSections: HelpSection[] = [
    {
      id: 'overview',
      title: 'Platform Overview',
      icon: BookOpenIcon,
      badge: 'Start Here',
      description: 'Learn about AgentVerse and its core capabilities',
      content: (
        <div className="space-y-6">
          <div className="text-center mb-8">
            <BrandLogo variant="full" size="lg" />
            <h2 className="text-2xl font-bold text-slate-800 dark:text-slate-200 mt-4 mb-2">
              Welcome to AgentVerse
            </h2>
            <p className="text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
              A professional platform for creating, managing, and orchestrating AI agents with advanced multi-agent workflows, tool integration, and real-time collaboration.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <BrandedCard variant="glass" className="p-6">
              <CpuChipIcon className="h-8 w-8 text-indigo-600 mb-3" />
              <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-2">Multi-Agent Orchestration</h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Create sophisticated workflows with multiple AI agents working together using LangGraph and LangChain integration.
              </p>
            </BrandedCard>

            <BrandedCard variant="glass" className="p-6">
              <WrenchScrewdriverIcon className="h-8 w-8 text-purple-600 mb-3" />
              <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-2">Tool Integration</h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Integrate custom tools and external APIs to extend agent capabilities with Python-based tool definitions.
              </p>
            </BrandedCard>

            <BrandedCard variant="glass" className="p-6">
              <ServerIcon className="h-8 w-8 text-pink-600 mb-3" />
              <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-2">MCP Integration</h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Connect to Model Context Protocol (MCP) servers for enhanced capabilities and data sources.
              </p>
            </BrandedCard>

            <BrandedCard variant="glass" className="p-6">
              <DocumentTextIcon className="h-8 w-8 text-indigo-600 mb-3" />
              <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-2">Document Intelligence</h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Upload and analyze documents with AI-powered insights and multi-format support including PDFs, images, and more.
              </p>
            </BrandedCard>
          </div>

          <BrandedCard variant="glass" className="p-6">
            <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-4 flex items-center">
              <RocketLaunchIcon className="h-5 w-5 mr-2 text-indigo-600" />
              Quick Start Guide
            </h3>
            <ol className="space-y-3 text-sm text-slate-600 dark:text-slate-400">
              <li className="flex items-start">
                <span className="bg-indigo-100 dark:bg-indigo-900 text-indigo-600 dark:text-indigo-400 rounded-full w-6 h-6 flex items-center justify-center text-xs font-semibold mr-3 mt-0.5">1</span>
                <span>Create a conversation group by clicking "+" in the sidebar Groups section</span>
              </li>
              <li className="flex items-start">
                <span className="bg-indigo-100 dark:bg-indigo-900 text-indigo-600 dark:text-indigo-400 rounded-full w-6 h-6 flex items-center justify-center text-xs font-semibold mr-3 mt-0.5">2</span>
                <span>Switch to "Agent Management" view and create your first AI agent</span>
              </li>
              <li className="flex items-start">
                <span className="bg-indigo-100 dark:bg-indigo-900 text-indigo-600 dark:text-indigo-400 rounded-full w-6 h-6 flex items-center justify-center text-xs font-semibold mr-3 mt-0.5">3</span>
                <span>Return to "Chat" view, select your group, and add your agent</span>
              </li>
              <li className="flex items-start">
                <span className="bg-indigo-100 dark:bg-indigo-900 text-indigo-600 dark:text-indigo-400 rounded-full w-6 h-6 flex items-center justify-center text-xs font-semibold mr-3 mt-0.5">4</span>
                <span>Start messaging agents and drag & drop documents for analysis</span>
              </li>
            </ol>
          </BrandedCard>
        </div>
      )
    },
    {
      id: 'groups',
      title: 'Managing Groups',
      icon: UserGroupIcon,
      badge: 'Essential',
      description: 'Learn how to create and manage conversation groups',
      content: (
        <div className="space-y-6">
          <div className="mb-6">
            <h2 className="text-xl font-bold text-slate-800 dark:text-slate-200 mb-2">Conversation Groups Guide</h2>
            <p className="text-slate-600 dark:text-slate-400">
              Groups are the foundation of AgentVerse - they organize conversations between you and your AI agents.
            </p>
          </div>

          <BrandedCard variant="glass" className="p-6">
            <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-4 flex items-center">
              <PlusIcon className="h-5 w-5 mr-2 text-indigo-600" />
              Creating Your First Group
            </h3>
            <ol className="space-y-3 text-sm text-slate-600 dark:text-slate-400">
              <li className="flex items-start">
                <span className="bg-indigo-100 dark:bg-indigo-900 text-indigo-600 dark:text-indigo-400 rounded-full w-6 h-6 flex items-center justify-center text-xs font-semibold mr-3 mt-0.5">1</span>
                <span>Look for the "Groups" section in the left sidebar</span>
              </li>
              <li className="flex items-start">
                <span className="bg-indigo-100 dark:bg-indigo-900 text-indigo-600 dark:text-indigo-400 rounded-full w-6 h-6 flex items-center justify-center text-xs font-semibold mr-3 mt-0.5">2</span>
                <span>Click the "+" (plus) button next to "Groups"</span>
              </li>
              <li className="flex items-start">
                <span className="bg-indigo-100 dark:bg-indigo-900 text-indigo-600 dark:text-indigo-400 rounded-full w-6 h-6 flex items-center justify-center text-xs font-semibold mr-3 mt-0.5">3</span>
                <span>Enter a descriptive name (e.g., "Marketing Team", "Code Review")</span>
              </li>
              <li className="flex items-start">
                <span className="bg-indigo-100 dark:bg-indigo-900 text-indigo-600 dark:text-indigo-400 rounded-full w-6 h-6 flex items-center justify-center text-xs font-semibold mr-3 mt-0.5">4</span>
                <span>Press Enter or click Create - your group appears in the sidebar</span>
              </li>
            </ol>
          </BrandedCard>

          <BrandedCard variant="glass" className="p-6">
            <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-4">
              Adding Agents to Groups
            </h3>
            <div className="space-y-4">
              <div>
                <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-2">Prerequisites</h4>
                <ul className="text-sm text-slate-600 dark:text-slate-400 space-y-1 ml-4">
                  <li>• You must create agents first (see "Creating Agents" section)</li>
                  <li>• Make sure you're in "Chat" view (not "Agent Management")</li>
                  <li>• Select a group from the sidebar</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-2">Adding Process</h4>
                <ol className="text-sm text-slate-600 dark:text-slate-400 space-y-2">
                  <li>1. Select your group from the sidebar</li>
                  <li>2. Look for "Add Agent" option in the group interface</li>
                  <li>3. Choose from your created agents</li>
                  <li>4. Agent appears in the group's agent list</li>
                  <li>5. Start conversing with your agents!</li>
                </ol>
              </div>
            </div>
          </BrandedCard>

          <BrandedCard variant="glass" className="p-6">
            <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-4">
              Conversation Features
            </h3>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="p-4 bg-slate-50 dark:bg-slate-700 rounded-lg">
                <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-2">@user Mentions</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  When agents mention @user in responses, you'll receive browser notifications (if enabled).
                </p>
              </div>
              <div className="p-4 bg-slate-50 dark:bg-slate-700 rounded-lg">
                <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-2">Real-time Streaming</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Agent responses stream live as they're generated for immediate feedback.
                </p>
              </div>
              <div className="p-4 bg-slate-50 dark:bg-slate-700 rounded-lg">
                <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-2">Document Upload</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Drag & drop files into the chat to have agents analyze documents.
                </p>
              </div>
              <div className="p-4 bg-slate-50 dark:bg-slate-700 rounded-lg">
                <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-2">Stop Chain</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Use the "Stop Chain" button to halt ongoing agent conversations.
                </p>
              </div>
            </div>
          </BrandedCard>

          <BrandedCard variant="glass" className="p-6">
            <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-4 flex items-center">
              <LightBulbIcon className="h-5 w-5 mr-2 text-yellow-500" />
              Group Management Tips
            </h3>
            <ul className="space-y-2 text-sm text-slate-600 dark:text-slate-400">
              <li>• Use descriptive group names to organize different projects or topics</li>
              <li>• You can have multiple agents in one group for collaborative conversations</li>
              <li>• Groups maintain conversation history - messages persist between sessions</li>
              <li>• Delete groups you no longer need to keep your workspace organized</li>
              <li>• Switch between groups easily using the sidebar navigation</li>
            </ul>
          </BrandedCard>
        </div>
      )
    },
    {
      id: 'agents',
      title: 'Creating Agents',
      icon: CpuChipIcon,
      description: 'Step-by-step guide to creating and configuring AI agents',
      content: (
        <div className="space-y-6">
          <div className="mb-6">
            <h2 className="text-xl font-bold text-slate-800 dark:text-slate-200 mb-2">Agent Creation Guide</h2>
            <p className="text-slate-600 dark:text-slate-400">
              Learn how to create powerful AI agents with custom configurations, tools, and capabilities.
            </p>
          </div>

          <BrandedCard variant="glass" className="p-6">
            <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-4 flex items-center">
              <PlayIcon className="h-5 w-5 mr-2 text-indigo-600" />
              Step 1: Access Agent Management
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
              Switch to Agent Management view using the toggle at the top of the interface.
            </p>
            <div className="bg-slate-50 dark:bg-slate-700 p-4 rounded-lg">
              <code className="text-sm text-slate-700 dark:text-slate-300">
                Toggle "Agent Management" → Click "Create Agent"
              </code>
            </div>
          </BrandedCard>

          <BrandedCard variant="glass" className="p-6">
            <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-4">
              Step 2: Basic Configuration
            </h3>
            <div className="space-y-4">
              <div>
                <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-2">Agent Identity</h4>
                <ul className="text-sm text-slate-600 dark:text-slate-400 space-y-1 ml-4">
                  <li>• <strong>Name:</strong> Choose a descriptive name for your agent</li>
                  <li>• <strong>Emoji:</strong> Select an emoji to represent your agent visually</li>
                  <li>• <strong>Description:</strong> Provide a clear description of the agent's purpose</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-2">System Prompt</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Define the agent's personality, behavior, and core instructions. This is the foundational prompt that guides all agent responses.
                </p>
              </div>
            </div>
          </BrandedCard>

          <BrandedCard variant="glass" className="p-6">
            <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-4">
              Step 3: LLM Selection & Configuration
            </h3>
            <div className="space-y-4">
              <div>
                <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-2">Supported Models</h4>
                <div className="grid grid-cols-2 gap-3">
                  <BrandedBadge variant="secondary">OpenAI GPT-4</BrandedBadge>
                  <BrandedBadge variant="secondary">Anthropic Claude</BrandedBadge>
                  <BrandedBadge variant="secondary">Google Gemini</BrandedBadge>
                  <BrandedBadge variant="secondary">Local Models</BrandedBadge>
                </div>
              </div>
              <div>
                <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-2">Parameters</h4>
                <ul className="text-sm text-slate-600 dark:text-slate-400 space-y-1 ml-4">
                  <li>• <strong>Temperature:</strong> Controls creativity (0.0-1.0)</li>
                  <li>• <strong>Max Tokens:</strong> Maximum response length</li>
                  <li>• <strong>Top P:</strong> Nucleus sampling parameter</li>
                </ul>
              </div>
            </div>
          </BrandedCard>

          <BrandedCard variant="glass" className="p-6">
            <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-4">
              Step 4: Tool Integration
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
              Select from available tools to enhance your agent's capabilities:
            </p>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-700 rounded-lg">
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Web Search</span>
                <BrandedBadge variant="success">Available</BrandedBadge>
              </div>
              <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-700 rounded-lg">
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">File Operations</span>
                <BrandedBadge variant="success">Available</BrandedBadge>
              </div>
              <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-700 rounded-lg">
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Custom Tools</span>
                <BrandedBadge variant="primary">Configurable</BrandedBadge>
              </div>
            </div>
          </BrandedCard>

          <BrandedCard variant="glass" className="p-6">
            <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-4">
              Step 5: Testing & Deployment
            </h3>
            <ol className="space-y-3 text-sm text-slate-600 dark:text-slate-400">
              <li className="flex items-start">
                <span className="bg-indigo-100 dark:bg-indigo-900 text-indigo-600 dark:text-indigo-400 rounded-full w-6 h-6 flex items-center justify-center text-xs font-semibold mr-3 mt-0.5">1</span>
                <span>Test your agent configuration with sample prompts</span>
              </li>
              <li className="flex items-start">
                <span className="bg-indigo-100 dark:bg-indigo-900 text-indigo-600 dark:text-indigo-400 rounded-full w-6 h-6 flex items-center justify-center text-xs font-semibold mr-3 mt-0.5">2</span>
                <span>Verify tool integrations work as expected</span>
              </li>
              <li className="flex items-start">
                <span className="bg-indigo-100 dark:bg-indigo-900 text-indigo-600 dark:text-indigo-400 rounded-full w-6 h-6 flex items-center justify-center text-xs font-semibold mr-3 mt-0.5">3</span>
                <span>Save your agent configuration</span>
              </li>
              <li className="flex items-start">
                <span className="bg-indigo-100 dark:bg-indigo-900 text-indigo-600 dark:text-indigo-400 rounded-full w-6 h-6 flex items-center justify-center text-xs font-semibold mr-3 mt-0.5">4</span>
                <span>Deploy to a conversation group for use</span>
              </li>
            </ol>
          </BrandedCard>
        </div>
      )
    },
    {
      id: 'tools',
      title: 'Managing Tools',
      icon: WrenchScrewdriverIcon,
      description: 'Configure and create custom tools for your agents',
      content: (
        <div className="space-y-6">
          <div className="mb-6">
            <h2 className="text-xl font-bold text-slate-800 dark:text-slate-200 mb-2">Tool Management Guide</h2>
            <p className="text-slate-600 dark:text-slate-400">
              Extend your agents' capabilities with custom tools and integrations.
            </p>
          </div>

          <BrandedCard variant="glass" className="p-6">
            <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-4">
              Built-in Tools
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
              AgentVerse comes with several pre-built tools ready for use:
            </p>
            <div className="grid gap-3">
              <div className="p-4 bg-slate-50 dark:bg-slate-700 rounded-lg">
                <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-2">Web Search Tool</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Enables agents to search the web and retrieve real-time information.
                </p>
              </div>
              <div className="p-4 bg-slate-50 dark:bg-slate-700 rounded-lg">
                <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-2">File Operations</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Read, write, and manipulate files within the system.
                </p>
              </div>
              <div className="p-4 bg-slate-50 dark:bg-slate-700 rounded-lg">
                <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-2">Code Execution</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Execute Python code securely in a sandboxed environment.
                </p>
              </div>
            </div>
          </BrandedCard>

          <BrandedCard variant="glass" className="p-6">
            <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-4">
              Creating Custom Tools
            </h3>
            <div className="space-y-4">
              <div>
                <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-2">Method 1: Via Tools Management Panel</h4>
                <ol className="text-sm text-slate-600 dark:text-slate-400 space-y-2 mb-4">
                  <li>1. Open Settings → Tools Management</li>
                  <li>2. Click "Create New Tool"</li>
                  <li>3. Fill in tool details and Python code</li>
                  <li>4. Save and test your tool</li>
                </ol>
              </div>

              <div>
                <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-2">Editing Existing Tools</h4>
                <ol className="text-sm text-slate-600 dark:text-slate-400 space-y-2 mb-4">
                  <li>1. Select any tool from the tools list</li>
                  <li>2. Click the "Edit" button</li>
                  <li>3. Modify the tool's name, description, or functionality</li>
                  <li>4. Test your changes before saving</li>
                  <li>5. Update the tool for all agents using it</li>
                </ol>
              </div>

              <div>
                <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-2">Tool Management Features</h4>
                <ul className="text-sm text-slate-600 dark:text-slate-400 space-y-1 ml-4">
                  <li>• <strong>Categories:</strong> Organize tools by function (File, Web, Data, etc.)</li>
                  <li>• <strong>Search:</strong> Find tools quickly using the search bar</li>
                  <li>• <strong>Status:</strong> See which tools are active or inactive</li>
                  <li>• <strong>Usage:</strong> View which agents are using each tool</li>
                  <li>• <strong>Testing:</strong> Test tools before deploying to agents</li>
                </ul>
              </div>
            </div>
          </BrandedCard>

          <BrandedCard variant="glass" className="p-6">
            <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-4">
              Using Tools in Agents
            </h3>
            <div className="space-y-4">
              <div>
                <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-2">Assigning Tools to Agents</h4>
                <ol className="text-sm text-slate-600 dark:text-slate-400 space-y-2 mb-4">
                  <li>1. Go to Agent Management view</li>
                  <li>2. Create a new agent or edit existing one</li>
                  <li>3. In the "Tools" section, select which tools to enable</li>
                  <li>4. Choose tools that match your agent's purpose</li>
                  <li>5. Save the agent configuration</li>
                </ol>
              </div>
              <div>
                <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-2">Tool Categories Available</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg">
                    <h5 className="font-medium text-indigo-800 dark:text-indigo-200">File Operations</h5>
                    <p className="text-xs text-indigo-600 dark:text-indigo-300">Read, write, manage files</p>
                  </div>
                  <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                    <h5 className="font-medium text-purple-800 dark:text-purple-200">Web & API</h5>
                    <p className="text-xs text-purple-600 dark:text-purple-300">Search, scrape, API calls</p>
                  </div>
                  <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                    <h5 className="font-medium text-green-800 dark:text-green-200">Data Processing</h5>
                    <p className="text-xs text-green-600 dark:text-green-300">CSV, JSON, analysis</p>
                  </div>
                  <div className="p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
                    <h5 className="font-medium text-orange-800 dark:text-orange-200">Custom Tools</h5>
                    <p className="text-xs text-orange-600 dark:text-orange-300">Your created tools</p>
                  </div>
                </div>
              </div>
            </div>
          </BrandedCard>

          <BrandedCard variant="glass" className="p-6 border border-slate-200 dark:border-slate-600">
            <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-4 flex items-center">
              <LightBulbIcon className="h-5 w-5 mr-2 text-yellow-500" />
              Best Practices
            </h3>
            <ul className="space-y-2 text-sm text-slate-600 dark:text-slate-400">
              <li>• Test tools before assigning them to agents</li>
              <li>• Use descriptive names and clear descriptions for custom tools</li>
              <li>• Organize tools into appropriate categories for easy discovery</li>
              <li>• Only assign tools that agents actually need to avoid confusion</li>
              <li>• Regularly review and update tool configurations as needed</li>
            </ul>
          </BrandedCard>
        </div>
      )
    },
    {
      id: 'interface',
      title: 'Using the Interface',
      icon: CpuChipIcon,
      badge: 'Navigation',
      description: 'Master the AgentVerse user interface and shortcuts',
      content: (
        <div className="space-y-6">
          <div className="mb-6">
            <h2 className="text-xl font-bold text-slate-800 dark:text-slate-200 mb-2">Interface Guide</h2>
            <p className="text-slate-600 dark:text-slate-400">
              Learn how to navigate AgentVerse efficiently and use all available features.
            </p>
          </div>

          <BrandedCard variant="glass" className="p-6">
            <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-4">
              Main Navigation
            </h3>
            <div className="space-y-4">
              <div>
                <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-2">View Toggle</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                  Switch between the two main views using the toggle at the top:
                </p>
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg">
                    <h5 className="font-medium text-indigo-800 dark:text-indigo-200">Chat View</h5>
                    <p className="text-xs text-indigo-600 dark:text-indigo-300">Talk with agents in groups</p>
                  </div>
                  <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                    <h5 className="font-medium text-purple-800 dark:text-purple-200">Agent Management</h5>
                    <p className="text-xs text-purple-600 dark:text-purple-300">Create and configure agents</p>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-2">Sidebar</h4>
                <ul className="text-sm text-slate-600 dark:text-slate-400 space-y-1 ml-4">
                  <li>• <strong>Groups section:</strong> Create and select conversation groups</li>
                  <li>• <strong>Agents section:</strong> View agents in current group (Chat view only)</li>
                  <li>• <strong>Expand/Collapse:</strong> Click the chevron to resize sidebar</li>
                </ul>
              </div>
            </div>
          </BrandedCard>

          <BrandedCard variant="glass" className="p-6">
            <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-4">
              Keyboard Shortcuts & Features
            </h3>
            <div className="space-y-4">
              <div>
                <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-2">Command Palette</h4>
                <div className="bg-slate-50 dark:bg-slate-700 p-3 rounded-lg mb-3">
                  <code className="text-sm text-slate-700 dark:text-slate-300">
                    ⌘K (Mac) / Ctrl+K (Windows/Linux)
                  </code>
                </div>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Quick access to all application features and navigation.
                </p>
              </div>

              <div>
                <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-2">Settings & Management</h4>
                <div className="grid gap-3">
                  <div className="flex justify-between items-center p-3 bg-slate-50 dark:bg-slate-700 rounded-lg">
                    <span className="text-sm text-slate-600 dark:text-slate-400">Application Settings</span>
                    <BrandedBadge variant="secondary">⚙️ Settings</BrandedBadge>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-slate-50 dark:bg-slate-700 rounded-lg">
                    <span className="text-sm text-slate-600 dark:text-slate-400">Tools Management</span>
                    <BrandedBadge variant="secondary">🛠️ Tools</BrandedBadge>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-slate-50 dark:bg-slate-700 rounded-lg">
                    <span className="text-sm text-slate-600 dark:text-slate-400">MCP Management</span>
                    <BrandedBadge variant="secondary">🌐 MCP</BrandedBadge>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-slate-50 dark:bg-slate-700 rounded-lg">
                    <span className="text-sm text-slate-600 dark:text-slate-400">Session Logs</span>
                    <BrandedBadge variant="secondary">📊 Logs</BrandedBadge>
                  </div>
                </div>
              </div>
            </div>
          </BrandedCard>

          <BrandedCard variant="glass" className="p-6">
            <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-4">
              Settings Panel Overview
            </h3>
            <div className="space-y-4">
              <div>
                <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-2">Frontend Settings (Auto-Save)</h4>
                <ul className="text-sm text-slate-600 dark:text-slate-400 space-y-1 ml-4">
                  <li>• <strong>Theme:</strong> Light, Dark, or System preference</li>
                  <li>• <strong>Notifications:</strong> Enable/disable, sound selection, volume</li>
                  <li>• <strong>Sidebar:</strong> Expanded or collapsed by default</li>
                </ul>
                <div className="mt-2 p-2 bg-green-50 dark:bg-green-900/20 rounded text-xs text-green-700 dark:text-green-300">
                  ✓ These settings save automatically as you change them
                </div>
              </div>

              <div>
                <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-2">Backend Settings (Manual Save)</h4>
                <ul className="text-sm text-slate-600 dark:text-slate-400 space-y-1 ml-4">
                  <li>• <strong>API Keys:</strong> OpenAI, Anthropic, Gemini configuration</li>
                  <li>• <strong>LLM Settings:</strong> Default provider, model, temperature</li>
                  <li>• <strong>Security:</strong> Session timeout, file upload limits</li>
                </ul>
                <div className="mt-2 p-2 bg-yellow-50 dark:bg-yellow-900/20 rounded text-xs text-yellow-700 dark:text-yellow-300">
                  ⚠️ Click "Save Settings" button to apply these changes
                </div>
              </div>
            </div>
          </BrandedCard>

          <BrandedCard variant="glass" className="p-6">
            <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-4">
              Document Upload & Processing
            </h3>
            <div className="space-y-4">
              <div>
                <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-2">Supported Formats</h4>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <BrandedBadge variant="secondary">PDF</BrandedBadge>
                  <BrandedBadge variant="secondary">DOCX</BrandedBadge>
                  <BrandedBadge variant="secondary">TXT</BrandedBadge>
                  <BrandedBadge variant="secondary">CSV</BrandedBadge>
                  <BrandedBadge variant="secondary">JSON</BrandedBadge>
                  <BrandedBadge variant="secondary">MD</BrandedBadge>
                  <BrandedBadge variant="secondary">PNG</BrandedBadge>
                  <BrandedBadge variant="secondary">JPG</BrandedBadge>
                  <BrandedBadge variant="secondary">GIF</BrandedBadge>
                </div>
              </div>
              <div>
                <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-2">Upload Process</h4>
                <ol className="text-sm text-slate-600 dark:text-slate-400 space-y-2">
                  <li>1. Drag & drop files into the chat area</li>
                  <li>2. Select which agent should receive the document</li>
                  <li>3. Add optional message describing what you want analyzed</li>
                  <li>4. Document appears in chat and agent can reference it</li>
                  <li>5. View all group documents in the Documents panel</li>
                </ol>
              </div>
            </div>
          </BrandedCard>

          <BrandedCard variant="glass" className="p-6 border border-slate-200 dark:border-slate-600">
            <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-4 flex items-center">
              <LightBulbIcon className="h-5 w-5 mr-2 text-yellow-500" />
              Interface Tips
            </h3>
            <ul className="space-y-2 text-sm text-slate-600 dark:text-slate-400">
              <li>• Use the Command Palette (⌘K) for quick navigation to any feature</li>
              <li>• Real-time message streaming means you see agent responses as they type</li>
              <li>• @user mentions in agent messages trigger browser notifications</li>
              <li>• Theme changes apply immediately - no save required</li>
              <li>• Sidebar can be collapsed to maximize chat space</li>
              <li>• Check session logs for detailed analytics and troubleshooting</li>
            </ul>
          </BrandedCard>
        </div>
      )
    },
    {
      id: 'mcp',
      title: 'MCP Integration',
      icon: ServerIcon,
      description: 'Connect to Model Context Protocol servers',
      content: (
        <div className="space-y-6">
          <div className="mb-6">
            <h2 className="text-xl font-bold text-slate-800 dark:text-slate-200 mb-2">MCP Server Integration</h2>
            <p className="text-slate-600 dark:text-slate-400">
              Learn how to connect and configure Model Context Protocol (MCP) servers to extend agent capabilities.
            </p>
          </div>

          <BrandedCard variant="glass" className="p-6">
            <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-4">
              What is MCP?
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
              Model Context Protocol (MCP) is an open standard for connecting AI assistants to external data sources and tools.
              It enables secure, standardized connections between AI agents and various services.
            </p>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="p-4 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg">
                <h4 className="font-medium text-indigo-800 dark:text-indigo-200 mb-2">Key Benefits</h4>
                <ul className="text-sm text-indigo-700 dark:text-indigo-300 space-y-1">
                  <li>• Standardized data access</li>
                  <li>• Secure authentication</li>
                  <li>• Real-time updates</li>
                  <li>• Extensible architecture</li>
                </ul>
              </div>
              <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                <h4 className="font-medium text-purple-800 dark:text-purple-200 mb-2">Use Cases</h4>
                <ul className="text-sm text-purple-700 dark:text-purple-300 space-y-1">
                  <li>• Database connections</li>
                  <li>• API integrations</li>
                  <li>• File system access</li>
                  <li>• Cloud services</li>
                </ul>
              </div>
            </div>
          </BrandedCard>

          <BrandedCard variant="glass" className="p-6">
            <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-4">
              Setting Up MCP Servers
            </h3>
            <div className="space-y-4">
              <div>
                <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-2">1. Accessing MCP Management</h4>
                <ol className="text-sm text-slate-600 dark:text-slate-400 space-y-2 mb-4">
                  <li>1. Click the ⚙️ Settings icon</li>
                  <li>2. Navigate to "MCP Management" section</li>
                  <li>3. View all available MCP servers and their status</li>
                  <li>4. Enable/disable servers as needed for your agents</li>
                </ol>
              </div>

              <div>
                <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-2">2. Managing MCP Servers</h4>
                <ol className="text-sm text-slate-600 dark:text-slate-400 space-y-2 mb-4">
                  <li>1. Click "Create New Server" to add a server</li>
                  <li>2. Fill in server name and description</li>
                  <li>3. Configure server settings through the interface</li>
                  <li>4. Test the connection to ensure it works</li>
                  <li>5. Assign servers to specific agents during agent creation</li>
                </ol>
              </div>
            </div>
          </BrandedCard>

          <BrandedCard variant="glass" className="p-6">
            <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-4">
              Popular MCP Servers
            </h3>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="p-4 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg">
                <h4 className="font-medium text-indigo-800 dark:text-indigo-200 mb-2">File System Access</h4>
                <p className="text-sm text-indigo-700 dark:text-indigo-300">
                  Enables agents to read, write, and manage files securely within designated directories.
                </p>
              </div>

              <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                <h4 className="font-medium text-purple-800 dark:text-purple-200 mb-2">Database Connections</h4>
                <p className="text-sm text-purple-700 dark:text-purple-300">
                  Connect agents to databases for data queries, analysis, and operations.
                </p>
              </div>

              <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <h4 className="font-medium text-green-800 dark:text-green-200 mb-2">GitHub Integration</h4>
                <p className="text-sm text-green-700 dark:text-green-300">
                  Manage repositories, code reviews, and GitHub operations through agents.
                </p>
              </div>

              <div className="p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
                <h4 className="font-medium text-orange-800 dark:text-orange-200 mb-2">Web Services</h4>
                <p className="text-sm text-orange-700 dark:text-orange-300">
                  Connect to various web APIs and services for extended functionality.
                </p>
              </div>
            </div>
          </BrandedCard>

          <BrandedCard variant="glass" className="p-6">
            <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-4">
              Using MCP Servers with Agents
            </h3>
            <div className="space-y-4">
              <div>
                <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-2">Assigning MCP Servers to Agents</h4>
                <ol className="text-sm text-slate-600 dark:text-slate-400 space-y-2 mb-4">
                  <li>1. Go to Agent Management view</li>
                  <li>2. Create a new agent or edit an existing one</li>
                  <li>3. In the "MCP Servers" section, select available servers</li>
                  <li>4. Choose servers that match your agent's intended capabilities</li>
                  <li>5. Save the agent configuration to apply changes</li>
                </ol>
              </div>
              <div>
                <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-2">Monitoring MCP Server Status</h4>
                <ul className="text-sm text-slate-600 dark:text-slate-400 space-y-1 ml-4">
                  <li>• Check connection status in the MCP Management panel</li>
                  <li>• View server activity logs for troubleshooting</li>
                  <li>• Monitor which agents are using which servers</li>
                  <li>• Restart servers if they become unresponsive</li>
                </ul>
              </div>
            </div>
          </BrandedCard>

          <BrandedCard variant="glass" className="p-6 border border-slate-200 dark:border-slate-600">
            <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-4 flex items-center">
              <LightBulbIcon className="h-5 w-5 mr-2 text-yellow-500" />
              Best Practices
            </h3>
            <ul className="space-y-2 text-sm text-slate-600 dark:text-slate-400">
              <li>• Test MCP server connections before assigning to agents</li>
              <li>• Only enable MCP servers that agents actually need</li>
              <li>• Monitor server status regularly through the management panel</li>
              <li>• Use descriptive names for servers to track their purposes</li>
              <li>• Review agent access to servers periodically for security</li>
            </ul>
          </BrandedCard>
        </div>
      )
    }
  ];

  return (
    <div className="h-full flex flex-col bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center space-x-2 mb-2">
          <QuestionMarkCircleIcon className="h-5 w-5 text-indigo-600" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Help & Documentation
          </h3>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Comprehensive guides for mastering AgentVerse
        </p>
      </div>

      <div className="flex-1 flex min-h-0">
        {/* Sidebar Navigation */}
        <div className="w-64 border-r border-gray-200 dark:border-gray-700 flex flex-col min-h-0">
          <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-indigo-300 dark:scrollbar-thumb-indigo-600 scrollbar-track-transparent">
            <div className="p-4">
              <nav className="space-y-2">
                {helpSections.map((section) => {
                  const Icon = section.icon;
                  const isExpanded = expandedSections.has(section.id);

                  return (
                    <div key={section.id}>
                      <button
                        onClick={() => {
                          setActiveSection(section.id);
                          toggleSection(section.id);
                        }}
                        className={`w-full flex items-center justify-between p-3 text-left rounded-lg transition-colors ${
                          activeSection === section.id
                            ? 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300'
                            : 'hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300'
                        }`}
                      >
                        <div className="flex items-center space-x-3">
                          <Icon className="h-5 w-5" />
                          <div>
                            <div className="flex items-center space-x-2">
                              <span className="text-sm font-medium">{section.title}</span>
                              {section.badge && (
                                <BrandedBadge variant="primary" size="sm">
                                  {section.badge}
                                </BrandedBadge>
                              )}
                            </div>
                            <p className="text-xs text-gray-500 dark:text-gray-400 text-left">
                              {section.description}
                            </p>
                          </div>
                        </div>
                        {isExpanded ? (
                          <ChevronDownIcon className="h-4 w-4" />
                        ) : (
                          <ChevronRightIcon className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                  );
                })}
              </nav>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col min-h-0">
          <AnimatePresence mode="wait">
            {helpSections.map((section) => (
              activeSection === section.id && (
                <motion.div
                  key={section.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.2 }}
                  className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-indigo-300 dark:scrollbar-thumb-indigo-600 scrollbar-track-transparent p-6"
                >
                  {section.content}
                </motion.div>
              )
            ))}
          </AnimatePresence>
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
            <BrandLogo variant="icon" size="sm" />
            <span>AgentVerse Documentation</span>
          </div>
          <BrandedButton
            variant="ghost"
            size="sm"
            onClick={() => window.open('https://github.com/niteshsinwar/Agentverse', '_blank')}
          >
            View on GitHub
            <ArrowRightIcon className="h-4 w-4 ml-1" />
          </BrandedButton>
        </div>
      </div>
    </div>
  );
};