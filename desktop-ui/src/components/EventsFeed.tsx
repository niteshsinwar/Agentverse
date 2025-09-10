import React, { useState, useEffect } from 'react';
import { EventMessage } from '../types';
import { Activity, Clock, AlertCircle } from 'lucide-react';

interface EventsFeedProps {
  groupId: string;
}

export const EventsFeed: React.FC<EventsFeedProps> = ({ groupId }) => {
  const [events, setEvents] = useState<EventMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // In a real implementation, you'd connect to your SSE endpoint here
    // For now, we'll simulate some events
    const simulateEvents = () => {
      const eventTypes = [
        'agent.started',
        'agent.finished', 
        'mcp.tool_call',
        'agent.error',
        'group.message_sent'
      ];
      
      const interval = setInterval(() => {
        if (Math.random() > 0.7) { // 30% chance of event
          const eventType = eventTypes[Math.floor(Math.random() * eventTypes.length)];
          const newEvent: EventMessage = {
            type: eventType,
            data: {
              agent_id: `agent_${Math.floor(Math.random() * 6) + 1}`,
              message: `Simulated ${eventType} event`,
              details: `Processing task for group ${groupId}`
            },
            timestamp: Date.now() / 1000
          };
          
          setEvents(prev => [newEvent, ...prev].slice(0, 50)); // Keep last 50 events
        }
      }, 3000);

      setIsConnected(true);
      
      return () => {
        clearInterval(interval);
        setIsConnected(false);
      };
    };

    const cleanup = simulateEvents();
    return cleanup;
  }, [groupId]);

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case 'agent.error':
        return <AlertCircle className="w-3 h-3 text-red-500" />;
      case 'agent.started':
        return <Activity className="w-3 h-3 text-green-500" />;
      case 'agent.finished':
        return <Activity className="w-3 h-3 text-blue-500" />;
      case 'mcp.tool_call':
        return <Activity className="w-3 h-3 text-purple-500" />;
      default:
        return <Activity className="w-3 h-3 text-gray-500" />;
    }
  };

  const getEventColor = (eventType: string) => {
    switch (eventType) {
      case 'agent.error':
        return 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800';
      case 'agent.started':
        return 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800';
      case 'agent.finished':
        return 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800';
      case 'mcp.tool_call':
        return 'bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800';
      default:
        return 'bg-gray-50 dark:bg-gray-700/50 border-gray-200 dark:border-gray-600';
    }
  };

  return (
    <div className="flex flex-col h-1/2">
      <div className="p-3 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <Activity className="w-4 h-4" />
            Live Events
          </h3>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2 scrollbar-thin">
        {events.length > 0 ? (
          events.map((event, index) => (
            <div
              key={index}
              className={`p-2 rounded-lg border ${getEventColor(event.type)}`}
            >
              <div className="flex items-start gap-2">
                {getEventIcon(event.type)}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <div className="font-medium text-xs text-gray-900 dark:text-white">
                      {event.type}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {formatTimestamp(event.timestamp)}
                    </div>
                  </div>
                  
                  {event.data.agent_id && (
                    <div className="text-xs text-gray-600 dark:text-gray-300 mt-1">
                      Agent: {event.data.agent_id}
                    </div>
                  )}
                  
                  {event.data.message && (
                    <div className="text-xs text-gray-600 dark:text-gray-300 mt-1">
                      {event.data.message}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No events yet</p>
            <p className="text-xs">Agent activities will appear here in real-time</p>
          </div>
        )}
      </div>
    </div>
  );
};