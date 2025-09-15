import React, { useState, useRef } from 'react';
import { Agent, Document } from '../types';
import { FileText, Upload, Trash2, Eye } from 'lucide-react';

interface DocumentManagerProps {
  groupId: string;
  agents: Agent[];
}

export const DocumentManager: React.FC<DocumentManagerProps> = ({
  groupId,
  agents,
}) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string>('');
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0 && selectedAgent) {
      uploadFiles(Array.from(files));
    }
  };

  const uploadFiles = async (files: File[]) => {
    if (!selectedAgent) {
      alert('Please select an agent first');
      return;
    }

    setUploading(true);
    try {
      // In a real implementation, you'd call your API here
      // For now, we'll just simulate the upload
      const newDocs: Document[] = files.map(file => ({
        id: Math.random().toString(36),
        filename: file.name,
        size: file.size,
        upload_time: Date.now() / 1000,
        agent_id: selectedAgent,
        group_id: groupId,
      }));
      
      setDocuments([...documents, ...newDocs]);
    } catch (error) {
      console.error('Failed to upload files:', error);
      alert('Failed to upload files');
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getAgentName = (agentKey: string) => {
    const agent = agents.find(a => a.key === agentKey);
    return agent ? `${agent.emoji} ${agent.name}` : agentKey;
  };

  return (
    <div className="flex flex-col h-1/2 border-b border-gray-200 dark:border-gray-700">
      <div className="p-3 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          <FileText className="w-4 h-4" />
          Documents ({documents.length})
        </h3>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {/* Upload Section */}
        <div className="space-y-2">
          {agents.length > 0 ? (
            <>
              <select
                value={selectedAgent}
                onChange={(e) => setSelectedAgent(e.target.value)}
                className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select agent for upload...</option>
                {agents.map((agent) => (
                  <option key={agent.key} value={agent.key}>
                    {agent.emoji} {agent.name}
                  </option>
                ))}
              </select>
              
              <div className="relative">
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  onChange={handleFileSelect}
                  className="hidden"
                  accept=".txt,.py,.js,.md,.json,.yaml,.yml,.pdf,.docx,.csv"
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={!selectedAgent || uploading}
                  className="w-full px-3 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  <Upload className="w-4 h-4" />
                  {uploading ? 'Uploading...' : 'Upload Files'}
                </button>
              </div>
            </>
          ) : (
            <div className="text-center py-4 text-gray-500 dark:text-gray-400">
              <FileText className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">Add agents to upload documents</p>
            </div>
          )}
        </div>

        {/* Documents List */}
        {documents.length > 0 ? (
          <div className="space-y-2">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="p-2 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm text-gray-900 dark:text-white truncate">
                      {doc.filename}
                    </div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">
                      {formatFileSize(doc.size)} • {getAgentName(doc.agent_id)}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {new Date(doc.upload_time * 1000).toLocaleString()}
                    </div>
                  </div>
                  
                  <div className="flex gap-1 ml-2">
                    <button
                      onClick={() => {
                        // View document logic
                        console.log('View document:', doc);
                      }}
                      className="p-1 text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                      title="View document"
                    >
                      <Eye className="w-3 h-3" />
                    </button>
                    <button
                      onClick={() => {
                        if (confirm(`Delete "${doc.filename}"?`)) {
                          setDocuments(documents.filter(d => d.id !== doc.id));
                        }
                      }}
                      className="p-1 text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
                      title="Delete document"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <FileText className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No documents uploaded</p>
            <p className="text-xs">Upload files to provide context to your agents</p>
          </div>
        )}
      </div>
    </div>
  );
};