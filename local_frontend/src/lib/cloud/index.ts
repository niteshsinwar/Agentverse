/**
 * Cloud Integration Module
 *
 * Exports all cloud-related functionality for easy import.
 */

// Configuration
export { cloudConfig, CLOUD_ENDPOINTS } from './config';
export type { CloudConfig } from './config';

// Authentication
export { cloudAuth } from './auth';
export type { AuthTokens, LoginCredentials, UserProfile } from './auth';

// HTTP Client
export { cloudHttpClient } from './httpClient';
export type { RequestOptions } from './httpClient';

// WebSocket Clients
export { chatWebSocket } from './chatWebSocket';
export type { ChatMessage, ChatEvent, ChatEventType } from './chatWebSocket';

export { syncWebSocket } from './syncWebSocket';
export type { SyncEvent, SyncEventType } from './syncWebSocket';
