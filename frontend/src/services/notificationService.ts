/**
 * Notification Service
 * Handles browser notifications for agent mentions and other events
 */

interface NotificationOptions {
  title: string;
  body: string;
  icon?: string;
  tag?: string;
  requireInteraction?: boolean;
}

type NotificationSound = 'bell' | 'chime' | 'beep' | 'ding' | 'none';

interface NotificationSettings {
  enabled: boolean;
  sound: NotificationSound;
  volume: number; // 0-1
}

class NotificationService {
  private static instance: NotificationService;
  private permission: NotificationPermission = 'default';
  private settings: NotificationSettings = {
    enabled: true,
    sound: 'bell',
    volume: 0.5
  };
  private audio: HTMLAudioElement | null = null;

  private constructor() {
    this.init();
    this.setupAudio();
  }

  static getInstance(): NotificationService {
    if (!NotificationService.instance) {
      NotificationService.instance = new NotificationService();
    }
    return NotificationService.instance;
  }

  private async init() {
    // Check if notifications are supported
    if (!('Notification' in window)) {
      console.warn('Browser does not support notifications');
      return;
    }

    this.permission = Notification.permission;
    this.loadSettings();
  }

  private loadSettings() {
    try {
      const frontendSettings = localStorage.getItem('frontend_settings');
      if (frontendSettings) {
        const settings = JSON.parse(frontendSettings);
        this.settings = {
          enabled: settings.notifications_enabled ?? true,
          sound: settings.notification_sound ?? 'bell',
          volume: settings.notification_volume ?? 0.5
        };
      }
    } catch (error) {
      console.error('Failed to load notification settings:', error);
    }
  }

  private setupAudio() {
    try {
      // Create a simple notification sound using Web Audio API
      this.audio = new Audio();

      // Set up a simple notification sound using a data URL
      this.audio.src = 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmsfCjiR2u/NeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmsfCjiR2u/NeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmsfCjiR2u/NeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmsfCjiR2u/NeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmsfCjiR2u/NeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmsfCjiR2u/NeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmsfCjiR2u/NeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmsfCjiR2u/NeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmsfCjiR2u/NeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmsfCjiR2u/NeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmsfCjiR2u/NeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmsfCjiR2u/NeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmsfCjiR2u/NeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmsfCjiR2u/NeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmsfCg==';
    } catch (error) {
      console.warn('Failed to setup notification audio:', error);
      // Fallback: create audio element without Web Audio API
      this.audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmsfCjiR2u/NeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmsfCjiR2u/NeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmsfCjiR2u/NeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmsfCjiR2u/NeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmsfCjiR2u/NeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmsfCjiR2u/NeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmsfCjiR2u/NeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmsfCjiR2u/NeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmsfCjiR2u/NeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmsfCjiR2u/NeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmsfCjiR2u/NeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmsfCjiR2u/NeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmsfCjiR2u/NeSsFJHfH8N2QQAoUXrTp66hVFApGn+DyvmsfCg==');
    }
  }

  playNotificationSound() {
    try {
      if (this.settings.enabled && this.settings.sound !== 'none') {
        const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);

        // Different sound types
        switch (this.settings.sound) {
          case 'bell':
            oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
            oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.1);
            gainNode.gain.setValueAtTime(this.settings.volume * 0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.3);
            break;

          case 'chime':
            oscillator.frequency.setValueAtTime(523, audioContext.currentTime);     // C5
            oscillator.frequency.setValueAtTime(659, audioContext.currentTime + 0.1); // E5
            oscillator.frequency.setValueAtTime(784, audioContext.currentTime + 0.2); // G5
            gainNode.gain.setValueAtTime(this.settings.volume * 0.2, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.4);
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.4);
            break;

          case 'beep':
            oscillator.frequency.setValueAtTime(1000, audioContext.currentTime);
            gainNode.gain.setValueAtTime(this.settings.volume * 0.4, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.15);
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.15);
            break;

          case 'ding':
            oscillator.frequency.setValueAtTime(1200, audioContext.currentTime);
            oscillator.frequency.setValueAtTime(900, audioContext.currentTime + 0.05);
            gainNode.gain.setValueAtTime(this.settings.volume * 0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.2);
            break;
        }
      }
    } catch (error) {
      console.warn('Error playing notification sound:', error);
    }
  }

  async requestPermission(): Promise<boolean> {
    if (!('Notification' in window)) {
      return false;
    }

    if (this.permission === 'granted') {
      return true;
    }

    this.permission = await Notification.requestPermission();
    return this.permission === 'granted';
  }

  setEnabled(enabled: boolean) {
    this.settings.enabled = enabled;
    this.saveSettings();
  }

  setSound(sound: NotificationSound) {
    this.settings.sound = sound;
    this.saveSettings();
  }

  setVolume(volume: number) {
    this.settings.volume = Math.max(0, Math.min(1, volume));
    this.saveSettings();
  }

  getSettings(): NotificationSettings {
    return { ...this.settings };
  }

  private saveSettings() {
    try {
      const frontendSettings = localStorage.getItem('frontend_settings') || '{}';
      const settings = JSON.parse(frontendSettings);
      settings.notifications_enabled = this.settings.enabled;
      settings.notification_sound = this.settings.sound;
      settings.notification_volume = this.settings.volume;
      localStorage.setItem('frontend_settings', JSON.stringify(settings));
    } catch (error) {
      console.error('Failed to save notification settings:', error);
    }
  }

  isNotificationEnabled(): boolean {
    return this.settings.enabled && this.permission === 'granted';
  }

  async showNotification(options: NotificationOptions): Promise<boolean> {
    if (!this.isNotificationEnabled()) {
      return false;
    }

    try {
      // Play notification sound FIRST
      this.playNotificationSound();

      const notification = new Notification(options.title, {
        body: options.body,
        icon: options.icon || '/favicon.svg',
        tag: options.tag,
        requireInteraction: options.requireInteraction || false,
        badge: '/favicon.svg',
        silent: false // Ensure notification is not silent
      });

      // Auto-close after 5 seconds unless requireInteraction is true
      if (!options.requireInteraction) {
        setTimeout(() => {
          notification.close();
        }, 5000);
      }

      return true;
    } catch (error) {
      console.error('Failed to show notification:', error);
      return false;
    }
  }

  // Specific notification types
  async notifyAgentMention(agentName: string, message: string, groupName?: string): Promise<boolean> {
    const title = `${agentName} mentioned you`;
    const body = groupName
      ? `In ${groupName}: ${message.substring(0, 100)}${message.length > 100 ? '...' : ''}`
      : message.substring(0, 100) + (message.length > 100 ? '...' : '');

    return this.showNotification({
      title,
      body,
      tag: `agent-mention-${agentName}`,
      requireInteraction: false
    });
  }

  async notifyAgentResponse(agentName: string, groupName?: string): Promise<boolean> {
    const title = `New response from ${agentName}`;
    const body = groupName ? `In conversation: ${groupName}` : 'New agent response';

    return this.showNotification({
      title,
      body,
      tag: `agent-response-${agentName}`,
      requireInteraction: false
    });
  }

  async notifyError(title: string, message: string): Promise<boolean> {
    return this.showNotification({
      title: `❌ ${title}`,
      body: message,
      tag: 'error',
      requireInteraction: true
    });
  }

  async notifySuccess(title: string, message: string): Promise<boolean> {
    return this.showNotification({
      title: `✅ ${title}`,
      body: message,
      tag: 'success',
      requireInteraction: false
    });
  }
}

// Export singleton instance
export const notificationService = NotificationService.getInstance();
export default notificationService;