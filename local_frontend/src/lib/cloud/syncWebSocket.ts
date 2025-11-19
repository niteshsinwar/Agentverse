/**
 * Cloud Sync WebSocket Client
 *
 * Receives real-time configuration updates from cloud backend.
 */

import { cloudConfig } from './config';
import { cloudAuth } from './auth';

export type SyncEventType =
  | 'agent_updated'
  | 'tool_updated'
  | 'mcp_updated'
  | 'group_updated';

export interface SyncEvent {
  type: SyncEventType;
  agent?: any;
  tool?: any;
  mcp_server?: any;
  group?: any;
}

type SyncEventHandler = (event: SyncEvent) => void;

class SyncWebSocketClient {
  private ws: WebSocket | null = null;
  private handlers: SyncEventHandler[] = [];
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 5000;

  /**
   * Connect to sync WebSocket
   */
  connect(): void {
    const token = cloudAuth.getAccessToken();
    if (!token) {
      console.error('Cannot connect to sync: No access token');
      return;
    }

    const config = cloudConfig();
    const wsUrl = `${config.wsUrl}/ws/sync/?token=${token}`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('✅ Connected to cloud sync channel');
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const data: SyncEvent = JSON.parse(event.data);
          console.log('🔄 Config update received:', data.type);
          this.notifyHandlers(data);
        } catch (error) {
          console.error('Error parsing sync message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('Sync WebSocket error:', error);
      };

      this.ws.onclose = () => {
        console.log('Sync WebSocket closed');
        this.handleReconnect();
      };
    } catch (error) {
      console.error('Error creating sync WebSocket:', error);
    }
  }

  /**
   * Handle reconnection
   */
  private handleReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * this.reconnectAttempts;

      console.log(`Reconnecting to sync in ${delay}ms...`);

      setTimeout(() => {
        this.connect();
      }, delay);
    } else {
      console.error('Max sync reconnect attempts reached');
    }
  }

  /**
   * Notify all registered handlers
   */
  private notifyHandlers(event: SyncEvent): void {
    this.handlers.forEach(handler => {
      try {
        handler(event);
      } catch (error) {
        console.error('Error in sync event handler:', error);
      }
    });
  }

  /**
   * Register sync event handler
   */
  onSync(handler: SyncEventHandler): () => void {
    this.handlers.push(handler);

    // Return unsubscribe function
    return () => {
      this.handlers = this.handlers.filter(h => h !== handler);
    };
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.handlers = [];
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

// Singleton instance
export const syncWebSocket = new SyncWebSocketClient();
