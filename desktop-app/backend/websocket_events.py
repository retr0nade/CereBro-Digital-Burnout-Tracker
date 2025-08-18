import time
from datetime import datetime
from flask_socketio import SocketIO, emit
from flask import request
from threading import Thread, Lock
import json

class WebSocketEventManager:
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.clients = set()
        self.lock = Lock()
        
    def register_client(self, sid):
        """Register a new client connection"""
        with self.lock:
            self.clients.add(sid)
            print(f"Client {sid} connected. Total clients: {len(self.clients)}")
    
    def unregister_client(self, sid):
        """Unregister a client connection"""
        with self.lock:
            self.clients.discard(sid)
            print(f"Client {sid} disconnected. Total clients: {len(self.clients)}")
    
    def broadcast_event(self, event_type: str, data: dict):
        """Broadcast an event to all connected clients"""
        if not self.clients:
            print(f"No clients connected to receive {event_type} event")
            return
            
        event_data = {
            "type": event_type,
            "timestamp": int(time.time()),
            "data": data
        }
        
        print(f"Broadcasting {event_type} event to {len(self.clients)} clients")
        
        with self.lock:
            disconnected_clients = []
            for client_sid in self.clients.copy():
                try:
                    self.socketio.emit('event', event_data, room=client_sid)
                except Exception as e:
                    print(f"Failed to send event to client {client_sid}: {e}")
                    disconnected_clients.append(client_sid)
            
            # Remove disconnected clients
            for client_sid in disconnected_clients:
                self.clients.discard(client_sid)
    
    def emit_app_usage_update(self, app_usage_data: dict):
        """Emit app usage update event"""
        self.broadcast_event('app_usage_update', app_usage_data)
    
    def emit_idle_status(self, idle_data: dict):
        """Emit idle status update event"""
        self.broadcast_event('idle_status', idle_data)
    
    def emit_input_activity(self, input_data: dict):
        """Emit input activity update event"""
        self.broadcast_event('input_activity', input_data)
    
    def emit_focus_session_update(self, focus_data: dict):
        """Emit focus session update event"""
        self.broadcast_event('focus_session_update', focus_data)
    
    def emit_break_update(self, break_data: dict):
        """Emit break update event"""
        self.broadcast_event('break_update', break_data)

# Global event manager instance
event_manager = None

def init_event_manager(socketio: SocketIO):
    """Initialize the global event manager"""
    global event_manager
    event_manager = WebSocketEventManager(socketio)
    return event_manager

def get_event_manager() -> WebSocketEventManager:
    """Get the global event manager instance"""
    return event_manager

def setup_socketio_handlers(socketio: SocketIO):
    """Setup SocketIO event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        if event_manager:
            event_manager.register_client(request.sid)
            emit('connected', {'status': 'connected', 'sid': request.sid})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        if event_manager:
            event_manager.unregister_client(request.sid)
    
    @socketio.on('subscribe')
    def handle_subscribe(data):
        """Handle client subscription to specific events"""
        event_type = data.get('event_type', 'all')
        emit('subscribed', {'event_type': event_type, 'status': 'subscribed'})
    
    @socketio.on('unsubscribe')
    def handle_unsubscribe(data):
        """Handle client unsubscription from specific events"""
        event_type = data.get('event_type', 'all')
        emit('unsubscribed', {'event_type': event_type, 'status': 'unsubscribed'})
