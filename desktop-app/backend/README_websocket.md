# WebSocket Real-time Updates

This document describes the WebSocket implementation for real-time updates in the CereBro Mental Burnout Tracker.

## Overview

The application now supports real-time updates via WebSocket connections, allowing the frontend to receive live updates when various events occur in the backend monitoring services.

## Backend Implementation

### Dependencies

- `flask-socketio==5.3.6` - WebSocket support for Flask

### Architecture

1. **WebSocket Event Manager** (`websocket_events.py`)
   - Manages WebSocket connections and event broadcasting
   - Handles client registration and event emission
   - Provides methods for each event type

2. **Event Types**
   - `app_usage_update` - When app usage is logged
   - `idle_status` - When user becomes idle/active
   - `input_activity` - When input activity is logged
   - `focus_session_update` - When focus sessions start/end
   - `break_update` - When breaks are detected

3. **Integration Points**
   - Window tracker emits app usage events
   - Idle monitor emits idle status events
   - Input logger emits input activity events
   - Focus timer emits focus session events
   - Break monitor emits break events

### Setup

The WebSocket functionality is automatically initialized when the Flask app starts:

```python
# In app_service.py
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
init_event_manager(socketio)
setup_socketio_handlers(socketio)
```

### Running the Server

The server now runs with SocketIO instead of the regular Flask development server:

```python
socketio.run(app, host='localhost', port=5005, debug=False)
```

## Frontend Implementation

### Dependencies

- `socket.io-client==4.7.4` - WebSocket client for React

### Components

1. **WebSocket Service** (`WebSocketService.ts`)
   - Manages WebSocket connection
   - Handles event subscription and unsubscription
   - Provides status monitoring
   - Automatic reconnection on disconnection

2. **Real-time Dashboard** (`RealTimeDashboard.tsx`)
   - Subscribes to all WebSocket events
   - Updates charts and metrics in real-time
   - Shows connection status
   - Displays live activity feed

### Usage

```typescript
import webSocketService from './WebSocketService';

// Subscribe to events
webSocketService.subscribe('app_usage_update', (event) => {
  console.log('App usage updated:', event.data);
});

// Monitor connection status
webSocketService.onStatusChange((status) => {
  console.log('WebSocket status:', status);
});
```

## Event Structure

All events follow this structure:

```typescript
interface WebSocketEvent {
  type: string;        // Event type (e.g., 'app_usage_update')
  timestamp: number;   // Unix timestamp
  data: any;          // Event-specific data
}
```

### Event Data Examples

**App Usage Update:**
```json
{
  "type": "app_usage_update",
  "timestamp": 1703123456,
  "data": {
    "app_name": "Chrome",
    "window_title": "Google - Chrome",
    "start_time": 1703123396,
    "end_time": 1703123456,
    "duration": 60,
    "pid": 12345
  }
}
```

**Idle Status:**
```json
{
  "type": "idle_status",
  "timestamp": 1703123456,
  "data": {
    "is_idle": true,
    "idle_start": 1703123456,
    "reason": "user_inactivity"
  }
}
```

**Input Activity:**
```json
{
  "type": "input_activity",
  "timestamp": 1703123456,
  "data": {
    "timestamp": 1703123456,
    "keypress_count": 10,
    "mouse_click_count": 5,
    "mouse_scroll_count": 2,
    "mouse_move_count": 100,
    "total_inputs": 17
  }
}
```

## Testing

Use the test script to verify WebSocket functionality:

```bash
cd desktop-app/backend
python test_websocket.py
```

This will emit test events for all event types. Check the frontend to see if events are received in real-time.

## API Endpoints

### WebSocket Status
- `GET /api/websocket/status` - Get WebSocket connection status and available events

## Troubleshooting

### Common Issues

1. **WebSocket not connecting**
   - Ensure the backend is running with SocketIO
   - Check that port 5005 is not blocked
   - Verify CORS settings

2. **Events not received**
   - Check browser console for connection errors
   - Verify event subscription in frontend
   - Check backend logs for event emission errors

3. **Performance issues**
   - Events are throttled to prevent overwhelming the frontend
   - Consider implementing event batching for high-frequency events

### Debug Mode

Enable debug mode to see detailed WebSocket logs:

```python
socketio.run(app, host='localhost', port=5005, debug=True)
```

## Security Considerations

- WebSocket connections are restricted to localhost
- CORS is configured to allow only necessary origins
- Event data is validated before emission
- Connection limits can be implemented if needed

## Future Enhancements

- Event filtering and subscription management
- Event persistence for offline clients
- Compression for high-frequency events
- Authentication for WebSocket connections
- Event batching for better performance
