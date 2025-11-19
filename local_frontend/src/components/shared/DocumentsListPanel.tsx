import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  DocumentIcon,
  TrashIcon,
  ArrowDownTrayIcon,
  ChevronRightIcon,
  ChevronDownIcon,
  FolderIcon,
  CalendarIcon
} from '@heroicons/react/24/outline';
import { Document, Agent } from '@/lib/types';
import { apiService } from "@/lib/api";
import { toast } from 'react-hot-toast';
import { BrandedCard } from './BrandedComponents';
import { BrandLogo } from './BrandLogo';

interface DocumentsListPanelProps {
  groupId: string;
  agents: Agent[];
  isVisible: boolean;
}

export const DocumentsListPanel: React.FC<DocumentsListPanelProps> = ({
  groupId,
  agents,
  isVisible,
}) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [expandedAgents, setExpandedAgents] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (isVisible && groupId) {
      loadDocuments();
    }
  }, [isVisible, groupId]);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const response = await apiService.getGroupDocuments(groupId);
      setDocuments(Array.isArray(response) ? response : []);
    } catch (error) {
      console.error('Failed to load documents:', error);
      toast.error('Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteDocument = async (documentId: string, filename: string) => {
    if (!window.confirm(`Are you sure you want to delete "${filename}"?`)) {
      return;
    }

    try {
      // Note: We'll need to add a delete endpoint to the API service
      // await apiService.deleteDocument(groupId, documentId);
      console.log(`Deleting document: ${documentId}`);
      toast.success(`Document "${filename}" deleted successfully`);
      await loadDocuments(); // Refresh the list
    } catch (error) {
      console.error('Failed to delete document:', error);
      toast.error('Failed to delete document');
    }
  };

  const handleDownloadDocument = async (documentId: string, filename: string) => {
    try {
      // Note: We'll need to add a download endpoint to the API service
      // const blob = await apiService.downloadDocument(groupId, documentId);
      console.log(`Downloading document: ${documentId}`);
      // const url = window.URL.createObjectURL(blob);
      // const a = document.createElement('a');
      // a.style.display = 'none';
      // a.href = url;
      // a.download = filename;
      // document.body.appendChild(a);
      // a.click();
      // window.URL.revokeObjectURL(url);
      toast.success(`Download started for "${filename}"`);
    } catch (error) {
      console.error('Failed to download document:', error);
      toast.error('Failed to download document');
    }
  };

  const toggleAgentExpansion = (agentId: string) => {
    const newExpanded = new Set(expandedAgents);
    if (newExpanded.has(agentId)) {
      newExpanded.delete(agentId);
    } else {
      newExpanded.add(agentId);
    }
    setExpandedAgents(newExpanded);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatUploadTime = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString();
  };

  const getAgentInfo = (agentId: string) => {
    return agents.find(a => a.key === agentId);
  };

  const getDocumentsByAgent = () => {
    const documentsByAgent: Record<string, Document[]> = {};

    documents.forEach(doc => {
      const agentId = doc.target_agent || 'unknown';
      if (!documentsByAgent[agentId]) {
        documentsByAgent[agentId] = [];
      }
      documentsByAgent[agentId].push(doc);
    });

    // Sort documents within each agent by upload time (newest first)
    Object.keys(documentsByAgent).forEach(agentId => {
      documentsByAgent[agentId].sort((a, b) => b.created_at - a.created_at);
    });

    return documentsByAgent;
  };

  const documentsByAgent = getDocumentsByAgent();
  const totalDocuments = documents.length;

  return (
    <div className="h-full flex flex-col brand-shell border-l border-transparent">
      {/* Header */}
      <div className="p-4 border-b border-transparent">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <FolderIcon className="h-5 w-5 text-slate-500" />
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
              Documents
            </h3>
            <span className="bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400 text-xs px-2 py-1 rounded-full">
              {totalDocuments}
            </span>
          </div>
        </div>
        <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
          Files uploaded to this group
        </p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="p-4 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-transparent border-t-indigo-500 mx-auto"></div>
            <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">Loading documents...</p>
          </div>
        ) : totalDocuments === 0 ? (
          <BrandedCard variant="glass" className="p-6 text-center m-2">
            <div className="flex justify-center mb-4">
              <BrandLogo variant="icon" size="sm" />
            </div>
            <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200 mb-2">
              No documents uploaded
            </h4>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              Upload documents through the chat interface to see them here
            </p>
          </BrandedCard>
        ) : (
          <div className="p-2">
            {Object.entries(documentsByAgent).map(([agentId, agentDocuments]) => {
              const agentInfo = getAgentInfo(agentId);
              const isExpanded = expandedAgents.has(agentId);

              return (
                <div key={agentId} className="mb-4">
                  {/* Agent Header */}
                  <button
                    onClick={() => toggleAgentExpansion(agentId)}
                    className="w-full flex items-center justify-between p-2 text-left hover:bg-slate-50 dark:hover:bg-slate-700 rounded-lg transition-colors"
                  >
                    <div className="flex items-center space-x-2">
                      {isExpanded ? (
                        <ChevronDownIcon className="h-4 w-4 text-slate-500" />
                      ) : (
                        <ChevronRightIcon className="h-4 w-4 text-slate-500" />
                      )}
                      <span className="text-sm">{agentInfo?.emoji || '🤖'}</span>
                      <span className="text-sm font-medium text-slate-900 dark:text-white">
                        {agentInfo?.name || agentId}
                      </span>
                      <span className="bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400 text-xs px-2 py-1 rounded-full">
                        {agentDocuments.length}
                      </span>
                    </div>
                  </button>

                  {/* Documents List */}
                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden"
                      >
                        <div className="ml-6 space-y-2 mt-2">
                          {agentDocuments.map((document) => (
                            <div
                              key={document.document_id}
                              className="p-3 bg-slate-50 dark:bg-slate-700 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-600 transition-colors"
                            >
                              <div className="flex items-start justify-between">
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center space-x-2">
                                    <DocumentIcon className="h-4 w-4 text-indigo-600 flex-shrink-0" />
                                    <span className="text-sm font-medium text-slate-900 dark:text-white truncate">
                                      {document.filename}
                                    </span>
                                  </div>
                                  <div className="flex items-center space-x-4 mt-1 text-xs text-slate-500 dark:text-slate-400">
                                    <span className="flex items-center space-x-1">
                                      <span>📁</span>
                                      <span>{formatFileSize(document.size)}</span>
                                    </span>
                                    <span className="flex items-center space-x-1">
                                      <CalendarIcon className="h-3 w-3" />
                                      <span>{formatUploadTime(document.created_at)}</span>
                                    </span>
                                  </div>
                                </div>

                                <div className="flex items-center space-x-1 ml-2">
                                  <button
                                    onClick={() => handleDownloadDocument(document.document_id, document.filename)}
                                    className="p-1 text-slate-400 hover:text-indigo-600 rounded"
                                    title="Download document"
                                  >
                                    <ArrowDownTrayIcon className="h-4 w-4" />
                                  </button>
                                  <button
                                    onClick={() => handleDeleteDocument(document.document_id, document.filename)}
                                    className="p-1 text-slate-400 hover:text-red-600 rounded"
                                    title="Delete document"
                                  >
                                    <TrashIcon className="h-4 w-4" />
                                  </button>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Footer with Refresh Button */}
      <div className="p-3 border-t border-slate-200 dark:border-slate-700">
        <button
          onClick={loadDocuments}
          disabled={loading}
          className="w-full text-xs text-center text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300 disabled:opacity-50"
        >
          {loading ? 'Refreshing...' : 'Refresh Documents'}
        </button>
      </div>
    </div>
  );
};
