/**
 * Cloud WebSocket Client for Chat
 *
 * Real-time chat messages with typing indicators and user presence.
 */

import { cloudConfig } from './config';
import { cloudAuth } from './auth';

export interface ChatMessage {
  id: string;
  content: string;
  sender_id: string;
  sender_type: 'user' | 'agent';
  group_id: string;
  created_at: string;
}

export type ChatEventType =
  | 'message_created'
  | 'message_updated'
  | 'message_deleted'
  | 'typing_indicator'
  | 'user_presence';

export interface ChatEvent {
  type: ChatEventType;
  message?: ChatMessage;
  message_id?: string;
  user_id?: string;
  user_name?: string;
  is_typing?: boolean;
  action?: 'joined' | 'left';
}

type ChatEventHandler = (event: ChatEvent) => void;

class ChatWebSocketClient {
  private ws: WebSocket | null = null;
  private groupId: string | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 2000;
  private handlers: ChatEventHandler[] = [];

  /**
   * Connect to chat WebSocket for a specific group
   */
  connect(groupId: string): void {
    this.groupId = groupId;
    this.reconnectAttempts = 0;
    this.createConnection();
  }

  /**
   * Create WebSocket connection
   */
  private createConnection(): void {
    const token = cloudAuth.getAccessToken();
    if (!token) {
      console.error('Cannot connect to chat: No access token');
      return;
    }

    const config = cloudConfig();
    const wsUrl = `${config.wsUrl}/ws/messages/${this.groupId}/?token=${token}`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log(`✅ Connected to chat for group ${this.groupId}`);
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const data: ChatEvent = JSON.parse(event.data);
          this.notifyHandlers(data);
        } catch (error) {
          console.error('Error parsing chat message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('Chat WebSocket error:', error);
      };

      this.ws.onclose = () => {
        console.log('Chat WebSocket closed');
        this.handleReconnect();
      };
    } catch (error) {
      console.error('Error creating chat WebSocket:', error);
    }
  }

  /**
   * Handle reconnection with exponential backoff
   */
  private handleReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

      console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})...`);

      setTimeout(() => {
        if (this.groupId) {
          this.createConnection();
        }
      }, delay);
    } else {
      console.error('Max reconnect attempts reached');
    }
  }

  /**
   * Notify all registered handlers
   */
  private notifyHandlers(event: ChatEvent): void {
    this.handlers.forEach(handler => {
      try {
        handler(event);
      } catch (error) {
        console.error('Error in chat event handler:', error);
      }
    });
  }

  /**
   * Register event handler
   */
  onMessage(handler: ChatEventHandler): () => void {
    this.handlers.push(handler);

    // Return unsubscribe function
    return () => {
      this.handlers = this.handlers.filter(h => h !== handler);
    };
  }

  /**
   * Send typing indicator
   */
  sendTyping(isTyping: boolean): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'typing_indicator',
        is_typing: isTyping,
      }));
    }
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
    this.groupId = null;
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

// Singleton instance
export const chatWebSocket = new ChatWebSocketClient();
