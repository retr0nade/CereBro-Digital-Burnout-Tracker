import { io, Socket } from 'socket.io-client';
import { SOCKET_URL } from './config';

export interface WebSocketEvent {
  type: string;
  timestamp: number;
  data: any;
}

export interface WebSocketStatus {
  connected: boolean;
  connecting: boolean;
  error?: string;
}

class WebSocketService {
  private socket: Socket | null = null;
  private eventListeners: Map<string, ((event: WebSocketEvent) => void)[]> = new Map();
  private statusListeners: ((status: WebSocketStatus) => void)[] = [];
  private status: WebSocketStatus = { connected: false, connecting: false };
  private reconnectAttempts = 0;

  private currentUrl: string = SOCKET_URL;

  private setupSocket(url: string) {
    this.currentUrl = url;
    try {
      this.socket = io(url, {
        transports: ['websocket'],
        autoConnect: true,
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
        forceNew: true
      });

      this.socket.on('connect', () => {
        this.reconnectAttempts = 0;
        this.updateStatus({ connected: true, connecting: false });
        this.resubscribeToEvents();
      });

      this.socket.on('disconnect', (reason) => {
        this.updateStatus({ connected: false, connecting: false });
        if (reason === 'io server disconnect') {
          this.socket?.connect();
        }
      });

      this.socket.on('connect_error', (error) => {
        this.reconnectAttempts++;
        this.updateStatus({
          connected: false,
          connecting: false,
          error: error.message
        });
      });

      this.socket.on('event', (event: WebSocketEvent) => {
        this.handleEvent(event);
      });

    } catch (error) {
      this.updateStatus({
        connected: false,
        connecting: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  }

  public connect(url?: string): Promise<void> {
    return new Promise((resolve, reject) => {
      if (url && url !== this.currentUrl) {
        if (this.socket) {
          this.socket.disconnect();
          this.socket = null;
        }
      }

      if (!this.socket) {
        this.setupSocket(url || this.currentUrl);
      }

      if (this.socket?.connected) {
        resolve();
        return;
      }

      this.updateStatus({ connected: false, connecting: true });

      const timeout = setTimeout(() => {
        reject(new Error('Connection timeout'));
      }, 10000);

      this.socket?.once('connect', () => {
        clearTimeout(timeout);
        resolve();
      });

      this.socket?.once('connect_error', (error) => {
        clearTimeout(timeout);
        reject(error);
      });
    });
  }

  public disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.updateStatus({ connected: false, connecting: false });
  }

  public subscribe(eventType: string, callback: (event: WebSocketEvent) => void) {
    if (!this.eventListeners.has(eventType)) {
      this.eventListeners.set(eventType, []);
    }
    this.eventListeners.get(eventType)!.push(callback);

    if (this.socket?.connected) {
      this.socket.emit('subscribe', { event_type: eventType });
    }
  }

  public unsubscribe(eventType: string, callback: (event: WebSocketEvent) => void) {
    const listeners = this.eventListeners.get(eventType);
    if (listeners) {
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }

  public onStatusChange(callback: (status: WebSocketStatus) => void): () => void {
    this.statusListeners.push(callback);
    callback(this.status);
    return () => {
      const index = this.statusListeners.indexOf(callback);
      if (index !== -1) {
        this.statusListeners.splice(index, 1);
      }
    };
  }

  public getStatus(): WebSocketStatus {
    return { ...this.status };
  }

  public isConnected(): boolean {
    return this.socket?.connected || false;
  }

  public emit(event: string, data?: any) {
    if (this.socket?.connected) {
      this.socket.emit(event, data);
    }
  }

  private updateStatus(newStatus: WebSocketStatus) {
    this.status = newStatus;
    this.statusListeners.forEach(listener => listener(this.status));
  }

  private handleEvent(event: WebSocketEvent) {
    const listeners = this.eventListeners.get(event.type);
    if (listeners) {
      listeners.forEach(callback => callback(event));
    }
  }

  private resubscribeToEvents() {
    this.eventListeners.forEach((listeners, eventType) => {
      if (listeners.length > 0) {
        this.socket?.emit('subscribe', { event_type: eventType });
      }
    });
  }
}

export const webSocketService = new WebSocketService();
export default webSocketService;
