from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from .core.config import settings
from .core.database import db
from .api.routes import api
from .websockets.handlers import setup_socketio_handlers
from .core.logging import setup_logging

# Setup logging before anything else
setup_logging()

def create_app():
    app = Flask(__name__)
    
    # Configure CORS
    CORS(app, resources={
        r"/*": {
            "origins": ["http://localhost:3000", "http://localhost:3001", "http://localhost:5005"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # Initialize SocketIO
    socketio = SocketIO(
        app, 
        cors_allowed_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5005"], 
        async_mode='threading'
    )

    # Register Blueprints
    app.register_blueprint(api, url_prefix='/api')

    # Setup SocketIO handlers
    setup_socketio_handlers(socketio)

    return app, socketio

app, socketio = create_app()

import socket
import json
import os

def find_free_port(start_port=5005, max_port=5050):
    for port in range(start_port, max_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(('127.0.0.1', port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free ports available")

def write_port_file(port):
    try:
        with open("backend_port.json", "w") as f:
            json.dump({"port": port}, f)
    except Exception as e:
        print(f"Failed to write port file: {e}")

if __name__ == "__main__":
    # This block is for running main.py directly for testing
    print("Starting CereBro Backend (v2.1)...")
    port = find_free_port()
    write_port_file(port)
    print(f"Selected port: {port}")
    socketio.run(app, host='127.0.0.1', port=port, allow_unsafe_werkzeug=True)
