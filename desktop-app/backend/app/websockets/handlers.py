from flask_socketio import SocketIO, emit
from typing import Dict, Any, Optional
import threading
import time
import logging

logger = logging.getLogger(__name__)

class EventManager:
    _instance = None
    
    def __new__(cls, socketio: Optional[SocketIO] = None):
        if cls._instance is None:
            cls._instance = super(EventManager, cls).__new__(cls)
            cls._instance.socketio = socketio
            cls._instance.clients = set()
            cls._instance.lock = threading.Lock()
        elif socketio is not None:
            cls._instance.socketio = socketio
        return cls._instance

    def register_client(self, sid):
        with self.lock:
            self.clients.add(sid)
            logger.info(f"Client connected: {sid}")

    def unregister_client(self, sid):
        with self.lock:
            if sid in self.clients:
                self.clients.remove(sid)
                logger.info(f"Client disconnected: {sid}")

    def emit_event(self, event_type: str, data: Dict[str, Any]):
        if self.socketio:
            try:
                self.socketio.emit('event', {
                    'type': event_type,
                    'timestamp': int(time.time()),
                    'data': data
                })
            except Exception as e:
                logger.error(f"Error emitting event {event_type}: {e}")

    # Helper methods for specific events
    def emit_app_usage_update(self, data: Dict[str, Any]):
        self.emit_event('app_usage_update', data)

    def emit_idle_status(self, data: Dict[str, Any]):
        self.emit_event('idle_status', data)

    def emit_input_activity(self, data: Dict[str, Any]):
        self.emit_event('input_activity', data)

    def emit_focus_session_update(self, data: Dict[str, Any]):
        self.emit_event('focus_session_update', data)

    def emit_break_update(self, data: Dict[str, Any]):
        self.emit_event('break_update', data)

def init_event_manager(socketio: SocketIO) -> EventManager:
    return EventManager(socketio)

def get_event_manager() -> Optional[EventManager]:
    return EventManager()

def setup_socketio_handlers(socketio: SocketIO):
    event_manager = init_event_manager(socketio)

    @socketio.on('connect')
    def handle_connect():
        from flask import request
        event_manager.register_client(request.sid)
        emit('status', {'status': 'connected'})

    @socketio.on('disconnect')
    def handle_disconnect():
        from flask import request
        event_manager.unregister_client(request.sid)

    @socketio.on('subscribe')
    def handle_subscribe(data):
        # Client subscribing to specific events
        # For now we broadcast everything to everyone, but this could be used for filtering
        pass

    @socketio.on('ping')
    def handle_ping():
        emit('pong', {'timestamp': int(time.time())})
