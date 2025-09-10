import React, { useState, useEffect } from 'react';
import { Bot, Plus, Edit3, Trash2, Code2, Settings, Save, X, Wrench, CheckCircle, AlertCircle, Info, Zap } from 'lucide-react';
import { apiService } from '../services/api';

interface Agent {
  key: string;
  name: string;
  description: string;
  emoji: string;
  tools: string[];
  mcpConfig: any;
  toolsCode?: string;
}

interface PrebuiltTool {
  id: string;
  name: string;
  description: string;
  code: string;
  dependencies?: string[];
}

const PREBUILT_TOOLS: PrebuiltTool[] = [
  {
    id: 'serper',
    name: 'Serper Search',
    description: 'Google search using Serper API - Get web search results programmatically (requires API key)',
    code: `@agent_tool
def search_web(query: str, num_results: int = 10) -> Dict[str, Any]:
    """Search the web using Serper API"""
    import requests
    import json
    
    url = "https://google.serper.dev/search"
    payload = json.dumps({
        "q": query,
        "num": num_results
    })
    headers = {
        'X-API-KEY': 'YOUR_SERPER_API_KEY',  # Replace with actual key
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}`,
    dependencies: ['requests']
  },
  {
    id: 'web_scraping',
    name: 'Web Scraping',
    description: 'Extract content from web pages - Parse HTML and extract text, links, and data',
    code: `@agent_tool
def scrape_webpage(url: str) -> Dict[str, Any]:
    """Scrape content from a webpage"""
    import requests
    from bs4 import BeautifulSoup
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract text content
        text = soup.get_text(strip=True)
        
        # Extract links
        links = [a.get('href') for a in soup.find_all('a', href=True)]
        
        return {
            "success": True,
            "title": soup.title.string if soup.title else "",
            "text": text[:1000] + "..." if len(text) > 1000 else text,
            "links": links[:20],  # Limit to first 20 links
            "url": url
        }
    except Exception as e:
        return {"success": False, "error": str(e), "url": url}`,
    dependencies: ['requests', 'beautifulsoup4']
  },
  {
    id: 'file_operations',
    name: 'File Operations',
    description: 'File and folder management - Create, read, write, list, and manage files and directories',
    code: `@agent_tool
def create_file(path: str, content: str = "") -> Dict[str, Any]:
    """Create a new file with optional content"""
    import os
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return {"success": True, "message": f"File created: {path}", "size": len(content)}
    except Exception as e:
        return {"success": False, "error": str(e)}

@agent_tool
def read_file(path: str) -> Dict[str, Any]:
    """Read content from a file"""
    import os
    
    try:
        if not os.path.exists(path):
            return {"success": False, "error": "File not found"}
            
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"success": True, "content": content, "path": path, "size": len(content)}
    except Exception as e:
        return {"success": False, "error": str(e)}

@agent_tool
def list_directory(path: str = ".") -> Dict[str, Any]:
    """List contents of a directory"""
    import os
    
    try:
        if not os.path.exists(path):
            return {"success": False, "error": "Directory not found"}
            
        items = []
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            items.append({
                "name": item,
                "type": "directory" if os.path.isdir(item_path) else "file",
                "size": os.path.getsize(item_path) if os.path.isfile(item_path) else 0
            })
        return {"success": True, "items": items, "path": path, "count": len(items)}
    except Exception as e:
        return {"success": False, "error": str(e)}`
  }
];

const DEFAULT_MCP_CONFIG = {
  mcpServers: {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/files"]
    }
  }
};

export const AgentCreationPanel: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [editingAgent, setEditingAgent] = useState<Agent | null>(null);
  const [showCodeEditor, setShowCodeEditor] = useState(false);
  const [systemInfo, setSystemInfo] = useState<any>(null);
  const [validationResult, setValidationResult] = useState<any>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [showSystemInfo, setShowSystemInfo] = useState(false);
  
  // Form state
  const [formData, setFormData] = useState({
    name: '',
    key: '',
    description: '',
    emoji: '🤖',
    selectedTools: [] as string[],
    mcpConfig: JSON.stringify(DEFAULT_MCP_CONFIG, null, 2),
    customCode: ''
  });

  // Load existing agents and system info on component mount
  useEffect(() => {
    loadAgents();
    loadSystemInfo();
  }, []);

  const loadAgents = async () => {
    try {
      const agentsData = await apiService.getAvailableAgents();
      setAgents(agentsData);
    } catch (error) {
      console.error('Failed to load agents:', error);
    }
  };

  const loadSystemInfo = async () => {
    try {
      const data = await apiService.getSystemInfo();
      setSystemInfo(data);
    } catch (error) {
      console.error('Failed to load system info:', error);
    }
  };

  const validateAgent = async () => {
    if (!formData.name || !formData.key) {
      alert('Please fill in agent name and key first');
      return;
    }

    setIsValidating(true);
    try {
      // Safely parse MCP config, fallback to empty object if invalid
      let mcpConfig = {};
      if (formData.mcpConfig.trim()) {
        try {
          mcpConfig = JSON.parse(formData.mcpConfig);
        } catch (jsonError) {
          console.warn('Invalid MCP config JSON, using empty object:', jsonError);
          mcpConfig = {};
        }
      }

      const agentData = {
        key: formData.key,
        name: formData.name,
        description: formData.description,
        emoji: formData.emoji,
        tools: formData.selectedTools || [],
        mcpConfig,
        toolsCode: generateToolsCode()
      };

      console.log('Sending validation request:', agentData);
      const result = await apiService.validateAgent(agentData);
      console.log('Validation result:', result);
      setValidationResult(result);
    } catch (error) {
      console.error('Error validating agent:', error);
      setValidationResult({
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      });
    } finally {
      setIsValidating(false);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      key: '',
      description: '',
      emoji: '🤖',
      selectedTools: [],
      mcpConfig: JSON.stringify(DEFAULT_MCP_CONFIG, null, 2),
      customCode: ''
    });
  };

  const handleCreateAgent = async () => {
    try {
      // Generate tools code from selected prebuilt tools and custom code
      const toolsCode = generateToolsCode();
      
      // Safely parse MCP config, fallback to empty object if invalid
      let mcpConfig = {};
      if (formData.mcpConfig.trim()) {
        try {
          mcpConfig = JSON.parse(formData.mcpConfig);
        } catch (jsonError) {
          console.warn('Invalid MCP config JSON, using empty object:', jsonError);
          mcpConfig = {};
        }
      }

      const agentData = {
        key: formData.key,
        name: formData.name,
        description: formData.description,
        emoji: formData.emoji,
        tools: formData.selectedTools || [],
        mcpConfig,
        toolsCode
      };

      const newAgent = await apiService.createAgent(agentData);
      setAgents([...agents, newAgent]);
      setIsCreating(false);
      resetForm();
    } catch (error) {
      console.error('Error creating agent:', error);
    }
  };

  const handleUpdateAgent = async (agent: Agent) => {
    try {
      const updatedAgent = await apiService.updateAgent(agent.key, agent);
      setAgents(agents.map(a => a.key === agent.key ? updatedAgent : a));
      setEditingAgent(null);
    } catch (error) {
      console.error('Error updating agent:', error);
    }
  };

  const handleDeleteAgent = async (agentKey: string) => {
    if (!confirm('Are you sure you want to delete this agent?')) return;
    
    try {
      await apiService.deleteAgent(agentKey);
      setAgents(agents.filter(a => a.key !== agentKey));
    } catch (error) {
      console.error('Error deleting agent:', error);
    }
  };

  const generateToolsCode = () => {
    let code = '"""\nAgent Tools - Auto-generated\n"""\n\n';
    
    // Add selected prebuilt tools
    formData.selectedTools.forEach(toolId => {
      const tool = PREBUILT_TOOLS.find(t => t.id === toolId);
      if (tool) {
        code += `# ${tool.name} - ${tool.description}\n`;
        code += tool.code + '\n\n';
      }
    });
    
    // Add custom code
    if (formData.customCode.trim()) {
      code += '# Custom Tools\n';
      code += formData.customCode;
    }
    
    return code;
  };

  const handleToolToggle = (toolId: string) => {
    setFormData(prev => ({
      ...prev,
      selectedTools: prev.selectedTools.includes(toolId)
        ? prev.selectedTools.filter(id => id !== toolId)
        : [...prev.selectedTools, toolId]
    }));
  };

  const generateAgentKey = (name: string) => {
    return name.toLowerCase().replace(/[^a-z0-9]/g, '_').replace(/_+/g, '_').slice(0, 20);
  };

  const handleNameChange = (name: string) => {
    setFormData(prev => ({
      ...prev,
      name,
      key: generateAgentKey(name)
    }));
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Bot className="w-8 h-8 text-blue-600" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Agent Management</h1>
            <p className="text-gray-600 dark:text-gray-400">Create and manage your AI agents</p>
          </div>
        </div>
        
        <div className="flex gap-3">
          <button
            onClick={() => setShowSystemInfo(true)}
            className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
          >
            <Info className="w-4 h-4" />
            System Info
          </button>
          <button
            onClick={() => setIsCreating(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Create Agent
          </button>
        </div>
      </div>

      {/* Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {agents && agents.map((agent) => (
          <div key={agent.key} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 hover:shadow-lg transition-shadow">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <span className="text-3xl">{agent.emoji}</span>
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-white">{agent.name}</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">@{agent.key}</p>
                </div>
              </div>
              
              <div className="flex gap-2">
                <button
                  onClick={() => setEditingAgent(agent)}
                  className="p-2 text-gray-600 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400"
                  title="Edit agent"
                >
                  <Edit3 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleDeleteAgent(agent.key)}
                  className="p-2 text-gray-600 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400"
                  title="Delete agent"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
            
            <p className="text-gray-700 dark:text-gray-300 text-sm mb-4">{agent.description}</p>
            
            <div className="flex flex-wrap gap-2">
              {agent.tools && agent.tools.map((tool) => (
                <span key={tool} className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 text-xs rounded-full">
                  {tool}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Create/Edit Agent Modal */}
      {(isCreating || editingAgent) && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg w-full max-w-4xl max-h-[90vh] overflow-hidden">
            <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                {editingAgent ? 'Edit Agent' : 'Create New Agent'}
              </h2>
              <button
                onClick={() => {
                  setIsCreating(false);
                  setEditingAgent(null);
                  resetForm();
                }}
                className="p-2 text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-180px)]">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Basic Information */}
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                      <Bot className="w-5 h-5" />
                      Basic Information
                    </h3>
                    
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Agent Name
                        </label>
                        <input
                          type="text"
                          value={formData.name}
                          onChange={(e) => handleNameChange(e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          placeholder="Enter agent name"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Agent Key (Auto-generated)
                        </label>
                        <input
                          type="text"
                          value={formData.key}
                          onChange={(e) => setFormData(prev => ({ ...prev, key: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          placeholder="agent_key"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Description
                        </label>
                        <textarea
                          value={formData.description}
                          onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          rows={3}
                          placeholder="Describe what this agent does"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Emoji
                        </label>
                        <input
                          type="text"
                          value={formData.emoji}
                          onChange={(e) => setFormData(prev => ({ ...prev, emoji: e.target.value }))}
                          className="w-20 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-center"
                          placeholder="🤖"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Tool Selection */}
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                      <Wrench className="w-5 h-5" />
                      Pre-built Tools
                    </h3>
                    
                    <div className="space-y-3">
                      {PREBUILT_TOOLS.map((tool) => (
                        <div key={tool.id} className="flex items-start gap-3 p-3 border border-gray-200 dark:border-gray-600 rounded-lg">
                          <input
                            type="checkbox"
                            checked={formData.selectedTools.includes(tool.id)}
                            onChange={() => handleToolToggle(tool.id)}
                            className="mt-1"
                          />
                          <div className="flex-1">
                            <h4 className="font-medium text-gray-900 dark:text-white">{tool.name}</h4>
                            <p className="text-sm text-gray-600 dark:text-gray-400">{tool.description}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Configuration */}
                <div className="space-y-6">
                  {/* MCP Configuration */}
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                      <Settings className="w-5 h-5" />
                      MCP Configuration
                    </h3>
                    
                    <textarea
                      value={formData.mcpConfig}
                      onChange={(e) => setFormData(prev => ({ ...prev, mcpConfig: e.target.value }))}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-mono text-sm"
                      rows={10}
                      placeholder={`{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-filesystem", "./workspace"],
      "env": {
        "NODE_ENV": "production"
      }
    },
    "web-search": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-web-search"],
      "env": {
        "SEARCH_API_KEY": "your-api-key"
      }
    },
    "database": {
      "command": "python",
      "args": ["-m", "mcp_server_sqlite", "database.db"],
      "env": {
        "DB_PATH": "./data/database.db"
      }
    }
  }
}

Common MCP Servers:
- filesystem: File operations
- web-search: Web search capabilities  
- sqlite: Database operations
- git: Git repository management
- brave-search: Brave search API
- google-maps: Google Maps integration`}
                    />
                  </div>

                  {/* Custom Code */}
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white flex items-center gap-2">
                        <Code2 className="w-5 h-5" />
                        Custom Tools Code
                      </h3>
                      <button
                        onClick={() => setShowCodeEditor(!showCodeEditor)}
                        className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
                      >
                        {showCodeEditor ? 'Hide Editor' : 'Show Editor'}
                      </button>
                    </div>
                    
                    {showCodeEditor && (
                      <textarea
                        value={formData.customCode}
                        onChange={(e) => setFormData(prev => ({ ...prev, customCode: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-mono text-sm"
                        rows={15}
                        placeholder={`# Write your custom Python tools here...
# Example 1: Simple data processing tool
@agent_tool
def process_data(data: str, format: str = "json") -> Dict[str, Any]:
    """Process data in different formats"""
    import json
    
    if format == "json":
        return {"processed": data, "format": format}
    elif format == "csv":
        return {"rows": data.split("\\n"), "format": format}
    else:
        return {"error": "Unsupported format"}

# Example 2: API integration tool
@agent_tool
def fetch_weather(city: str) -> Dict[str, Any]:
    """Fetch weather data for a city"""
    import requests
    
    try:
        # Replace with actual API key
        api_key = "YOUR_API_KEY"
        url = f"http://api.openweathermap.org/data/2.5/weather"
        params = {"q": city, "appid": api_key, "units": "metric"}
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        return {
            "success": True,
            "data": response.json(),
            "city": city
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# Example 3: File operations tool
@agent_tool
def save_to_file(content: str, filename: str) -> Dict[str, Any]:
    """Save content to a file"""
    import os
    
    try:
        os.makedirs("workspace", exist_ok=True)
        filepath = os.path.join("workspace", filename)
        
        with open(filepath, "w") as f:
            f.write(content)
            
        return {
            "success": True,
            "message": f"Saved to {filepath}",
            "size": len(content)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# Tips:
# 1. Always use @agent_tool decorator
# 2. Add type hints for parameters and return values
# 3. Include descriptive docstrings
# 4. Handle errors gracefully
# 5. Return structured data (Dict/List/str)
# 6. Import modules inside functions when possible`}
                      />
                    )}
                  </div>
                </div>
              </div>
            </div>
            
            <div className="flex items-center justify-between gap-4 p-6 border-t border-gray-200 dark:border-gray-700">
              <button
                onClick={validateAgent}
                disabled={isValidating}
                className="flex items-center gap-2 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors disabled:opacity-50"
              >
                <Zap className="w-4 h-4" />
                {isValidating ? 'Validating...' : 'Test & Validate'}
              </button>
              
              <div className="flex gap-4">
                <button
                  onClick={() => {
                    setIsCreating(false);
                    setEditingAgent(null);
                    resetForm();
                    setValidationResult(null);
                  }}
                  className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
                >
                  Cancel
                </button>
                <button
                  onClick={editingAgent ? () => handleUpdateAgent(editingAgent) : handleCreateAgent}
                  disabled={validationResult && !validationResult.test_results?.ready_to_create}
                  className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Save className="w-4 h-4" />
                  {editingAgent ? 'Update Agent' : 'Deploy Agent'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Validation Results Panel */}
      {validationResult && (isCreating || editingAgent) && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg w-full max-w-2xl max-h-[80vh] overflow-hidden">
            <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Agent Validation Results
              </h3>
              <button
                onClick={() => setValidationResult(null)}
                className="p-2 text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto max-h-[60vh]">
              {/* Overall Status */}
              <div className={`p-4 rounded-lg mb-6 ${validationResult.test_results?.ready_to_create ? 'bg-green-100 dark:bg-green-900/20' : 'bg-red-100 dark:bg-red-900/20'}`}>
                <div className="flex items-center gap-3">
                  {validationResult.test_results?.ready_to_create ? (
                    <CheckCircle className="w-6 h-6 text-green-600" />
                  ) : (
                    <AlertCircle className="w-6 h-6 text-red-600" />
                  )}
                  <div>
                    <h4 className="font-semibold text-gray-900 dark:text-white">
                      {validationResult.test_results?.ready_to_create ? 'Ready to Deploy' : 'Issues Found'}
                    </h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {validationResult.test_results?.code_validation?.summary}
                    </p>
                  </div>
                </div>
              </div>

              {/* Agent Preview */}
              <div className="mb-6">
                <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Agent Preview</h4>
                <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-2xl">{validationResult.agent_preview?.emoji}</span>
                    <div>
                      <h5 className="font-medium text-gray-900 dark:text-white">{validationResult.agent_preview?.name}</h5>
                      <p className="text-sm text-gray-600 dark:text-gray-400">@{validationResult.agent_preview?.key}</p>
                    </div>
                  </div>
                  <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">{validationResult.agent_preview?.description}</p>
                  <div className="flex gap-4 text-xs text-gray-600 dark:text-gray-400">
                    <span>🛠️ {validationResult.agent_preview?.tools_count} tools</span>
                    <span>📦 {validationResult.agent_preview?.dependencies_count} dependencies</span>
                  </div>
                </div>
              </div>

              {/* Code Validation */}
              <div className="mb-6">
                <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Code Analysis</h4>
                <div className="space-y-3">
                  {validationResult.test_results?.code_validation?.agent_tool_functions?.length > 0 && (
                    <div className="bg-green-50 dark:bg-green-900/20 p-3 rounded-lg">
                      <h5 className="font-medium text-green-800 dark:text-green-300 mb-2">✅ Agent Tools Found</h5>
                      <div className="flex flex-wrap gap-2">
                        {validationResult.test_results.code_validation.agent_tool_functions.map((func: string, index: number) => (
                          <span key={`func-${index}-${func}`} className="px-2 py-1 bg-green-200 dark:bg-green-800 text-green-800 dark:text-green-200 text-xs rounded">
                            {func}()
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {validationResult.test_results?.code_validation?.missing_dependencies?.length > 0 && (
                    <div className="bg-red-50 dark:bg-red-900/20 p-3 rounded-lg">
                      <h5 className="font-medium text-red-800 dark:text-red-300 mb-2">❌ Missing Dependencies</h5>
                      <div className="space-y-1">
                        {validationResult.test_results.code_validation.missing_dependencies.map((dep: string, index: number) => (
                          <span key={`dep-${index}-${dep}`} className="block px-2 py-1 bg-red-200 dark:bg-red-800 text-red-800 dark:text-red-200 text-xs rounded">
                            pip install {dep}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {validationResult.test_results?.code_validation?.warnings?.length > 0 && (
                    <div className="bg-yellow-50 dark:bg-yellow-900/20 p-3 rounded-lg">
                      <h5 className="font-medium text-yellow-800 dark:text-yellow-300 mb-2">⚠️ Warnings</h5>
                      <ul className="space-y-1">
                        {validationResult.test_results.code_validation.warnings.map((warning: string, index: number) => (
                          <li key={`warning-${index}`} className="text-sm text-yellow-700 dark:text-yellow-300">• {warning}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>

              {/* MCP Validation */}
              {validationResult.test_results?.mcp_errors?.length > 0 && (
                <div className="mb-6">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-3">MCP Configuration</h4>
                  <div className="bg-red-50 dark:bg-red-900/20 p-3 rounded-lg">
                    <h5 className="font-medium text-red-800 dark:text-red-300 mb-2">❌ Configuration Issues</h5>
                    <ul className="space-y-1">
                      {validationResult.test_results.mcp_errors.map((error: string, index: number) => (
                        <li key={`mcp-error-${index}`} className="text-sm text-red-700 dark:text-red-300">• {error}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* System Info Modal */}
      {showSystemInfo && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg w-full max-w-4xl max-h-[80vh] overflow-hidden">
            <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                System Information & Available Modules
              </h3>
              <button
                onClick={() => setShowSystemInfo(false)}
                className="p-2 text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto max-h-[60vh]">
              {systemInfo ? (
                <div className="space-y-6">
                  {/* Python Info */}
                  <div>
                    <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Python Environment</h4>
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                      <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
                        <strong>Version:</strong> {systemInfo.python_info?.version?.split(' ')[0]}
                      </p>
                      <p className="text-sm text-gray-700 dark:text-gray-300">
                        <strong>Executable:</strong> {systemInfo.python_info?.executable}
                      </p>
                    </div>
                  </div>

                  {/* Available Modules */}
                  <div>
                    <h4 className="font-semibold text-gray-900 dark:text-white mb-3">
                      Available Modules ({systemInfo.modules?.filter((m: any) => m.status === 'available').length} / {systemInfo.total_checked})
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {systemInfo.modules?.map((module: any, index: number) => (
                        <div key={`module-${index}-${module.name}`} className={`p-3 rounded-lg border ${
                          module.status === 'available' 
                            ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800' 
                            : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
                        }`}>
                          <div className="flex items-center justify-between">
                            <span className="font-medium text-sm text-gray-900 dark:text-white">{module.name}</span>
                            {module.status === 'available' ? (
                              <CheckCircle className="w-4 h-4 text-green-600" />
                            ) : (
                              <X className="w-4 h-4 text-red-600" />
                            )}
                          </div>
                          <span className={`text-xs ${
                            module.status === 'available' 
                              ? 'text-green-600 dark:text-green-400' 
                              : 'text-red-600 dark:text-red-400'
                          }`}>
                            {module.status === 'available' ? 'Available' : 'Not Installed'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Installation Instructions */}
                  <div>
                    <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Missing Modules Installation</h4>
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                      <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">To install missing modules, run:</p>
                      <code className="block bg-gray-800 text-green-400 p-2 rounded text-sm">
                        pip install {systemInfo.modules?.filter((m: any) => m.status === 'not_installed').map((m: any) => m.name).join(' ')}
                      </code>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-center text-gray-500 dark:text-gray-400">Loading system information...</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};