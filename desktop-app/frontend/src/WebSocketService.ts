import { io, Socket } from 'socket.io-client';

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
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  private status: WebSocketStatus = {
    connected: false,
    connecting: false
  };

  constructor() {
    this.setupSocket();
  }

  private setupSocket() {
    try {
      this.socket = io('http://localhost:5005', {
        transports: ['websocket', 'polling'],
        timeout: 5000,
        reconnection: true,
        reconnectionAttempts: this.maxReconnectAttempts,
        reconnectionDelay: this.reconnectDelay,
        forceNew: true
      });

      this.socket.on('connect', () => {
        console.log('WebSocket connected successfully');
        this.reconnectAttempts = 0;
        this.updateStatus({ connected: true, connecting: false });
        
        // Resubscribe to all events after reconnection
        this.resubscribeToEvents();
      });

      this.socket.on('disconnect', (reason) => {
        console.log('WebSocket disconnected:', reason);
        this.updateStatus({ connected: false, connecting: false });
        
        if (reason === 'io server disconnect') {
          // Server disconnected us, try to reconnect
          this.socket?.connect();
        }
      });

      this.socket.on('connect_error', (error) => {
        console.error('WebSocket connection error:', error);
        this.reconnectAttempts++;
        this.updateStatus({ 
          connected: false, 
          connecting: false, 
          error: error.message 
        });
      });

      this.socket.on('event', (event: WebSocketEvent) => {
        console.log('Received WebSocket event:', event.type, event.data);
        this.handleEvent(event);
      });

      this.socket.on('connected', (data) => {
        console.log('WebSocket handshake completed:', data);
      });

      this.socket.on('subscribed', (data) => {
        console.log('Subscribed to events:', data);
      });

      this.socket.on('reconnect', (attemptNumber) => {
        console.log('WebSocket reconnected after', attemptNumber, 'attempts');
        this.reconnectAttempts = 0;
      });

      this.socket.on('reconnect_error', (error) => {
        console.error('WebSocket reconnection error:', error);
      });

    } catch (error) {
      console.error('Failed to setup WebSocket:', error);
      this.updateStatus({ 
        connected: false, 
        connecting: false, 
        error: error instanceof Error ? error.message : 'Unknown error' 
      });
    }
  }

  private updateStatus(status: WebSocketStatus) {
    this.status = status;
    this.statusListeners.forEach(listener => listener(status));
  }

  private handleEvent(event: WebSocketEvent) {
    const listeners = this.eventListeners.get(event.type);
    if (listeners) {
      listeners.forEach(listener => {
        try {
          listener(event);
        } catch (error) {
          console.error(`Error in event listener for ${event.type}:`, error);
        }
      });
    }
  }

  public connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.socket) {
        this.setupSocket();
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

    // Send subscription message to server
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
    // Immediately call with current status
    callback(this.status);

    // Return unsubscribe function
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
    } else {
      console.warn('WebSocket not connected, cannot emit event:', event);
    }
  }

  private resubscribeToEvents() {
    // Resubscribe to all events after reconnection
    this.eventListeners.forEach((listeners, eventType) => {
      if (listeners.length > 0) {
        this.socket?.emit('subscribe', { event_type: eventType });
      }
    });
  }
}

// Export singleton instance
export const webSocketService = new WebSocketService();
export default webSocketService;
