/**
 * Client WebSocket pour synchronisation temps réel
 * Gère la connexion, reconnexion automatique, et callbacks
 */

export interface WebSocketMessage {
  type: 'connected' | 'schedule_updated' | 'slot_booked' | 'appointment_cancelled' | 'pong';
  doctor_id?: number;
  slot_id?: string;
  patient_id?: number;
  appointment_id?: number;
  timestamp?: string;
}

export type MessageCallback = (message: WebSocketMessage) => void;

export class DoctorScheduleSocket {
  private ws: WebSocket | null = null;
  private doctorId: number;
  private token: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // 1 seconde
  private maxReconnectDelay = 30000; // 30 secondes
  private pingInterval: number | null = null;
  private callbacks: Map<string, MessageCallback[]> = new Map();
  private isIntentionalClose = false;

  constructor(doctorId: number, token: string) {
    this.doctorId = doctorId;
    this.token = token;
  }

  /**
   * Établir la connexion WebSocket
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const wsUrl = `${protocol}//${host}/api/v1/ws/doctor/${this.doctorId}?token=${encodeURIComponent(this.token)}`;
      
      console.log(`🔌 Connexion WebSocket à: ${wsUrl}`);
      
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('✅ WebSocket connecté');
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;
        
        // Démarrer le ping keepalive
        this.startPing();
        
        resolve();
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          console.log('📨 Message WebSocket reçu:', message);
          
          // Déclencher les callbacks pour ce type de message
          this.triggerCallbacks(message.type, message);
          
          // Callback générique pour tous les messages
          this.triggerCallbacks('*', message);
          
        } catch (error) {
          console.error('❌ Erreur parsing message WebSocket:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('❌ Erreur WebSocket:', error);
        reject(error);
      };

      this.ws.onclose = (event) => {
        console.log(`🔌 WebSocket fermé (code: ${event.code}, reason: ${event.reason})`);
        
        // Arrêter le ping
        this.stopPing();
        
        // Reconnexion automatique sauf si fermé intentionnellement
        if (!this.isIntentionalClose) {
          this.attemptReconnect();
        }
      };
    });
  }

  /**
   * Fermer la connexion WebSocket
   */
  disconnect(): void {
    this.isIntentionalClose = true;
    this.stopPing();
    
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
    
    console.log('🔌 WebSocket déconnecté');
  }

  /**
   * Enregistrer un callback pour un type de message
   */
  on(messageType: string, callback: MessageCallback): void {
    if (!this.callbacks.has(messageType)) {
      this.callbacks.set(messageType, []);
    }
    this.callbacks.get(messageType)!.push(callback);
  }

  /**
   * Supprimer un callback
   */
  off(messageType: string, callback: MessageCallback): void {
    const callbacks = this.callbacks.get(messageType);
    if (callbacks) {
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  /**
   * Déclencher tous les callbacks pour un type de message
   */
  private triggerCallbacks(messageType: string, message: WebSocketMessage): void {
    const callbacks = this.callbacks.get(messageType);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(message);
        } catch (error) {
          console.error(`❌ Erreur dans callback ${messageType}:`, error);
        }
      });
    }
  }

  /**
   * Tentative de reconnexion avec backoff exponentiel
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error(`❌ Impossible de se reconnecter après ${this.maxReconnectAttempts} tentatives`);
      return;
    }

    this.reconnectAttempts++;
    
    // Backoff exponentiel
    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
      this.maxReconnectDelay
    );
    
    console.log(`🔄 Tentative de reconnexion ${this.reconnectAttempts}/${this.maxReconnectAttempts} dans ${delay}ms...`);
    
    setTimeout(() => {
      this.connect().catch(error => {
        console.error('❌ Échec de reconnexion:', error);
      });
    }, delay);
  }

  /**
   * Démarrer le ping keepalive (toutes les 30 secondes)
   */
  private startPing(): void {
    this.pingInterval = window.setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send('ping');
      }
    }, 30000);
  }

  /**
   * Arrêter le ping keepalive
   */
  private stopPing(): void {
    if (this.pingInterval !== null) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  /**
   * Vérifier si la connexion est ouverte
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * Obtenir l'état de la connexion
   */
  getState(): string {
    if (!this.ws) return 'CLOSED';
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING: return 'CONNECTING';
      case WebSocket.OPEN: return 'OPEN';
      case WebSocket.CLOSING: return 'CLOSING';
      case WebSocket.CLOSED: return 'CLOSED';
      default: return 'UNKNOWN';
    }
  }
}
