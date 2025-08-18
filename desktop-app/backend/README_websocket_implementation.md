# WebSocket Implementation for Real-Time Updates

This document describes the WebSocket implementation that provides real-time updates to the frontend for various system metrics and activities.

## Overview

The WebSocket system uses Flask-SocketIO to provide real-time communication between the backend services and the React frontend. It enables live updates for:

- **App Usage Updates**: When users switch between applications
- **Idle Status**: When the system becomes idle or active
- **Input Activity**: Keyboard and mouse activity metrics
- **Focus Session Updates**: Focus timer sessions and interruptions
- **Break Updates**: Break detection and duration tracking

## Architecture

### Backend Components

1. **websocket_events.py**: Core WebSocket event manager
2. **app_service.py**: Main Flask application with WebSocket integration
3. **Service Files**: Individual services that emit events (window_tracker.py, idle_monitor.py, etc.)

### Frontend Components

1. **WebSocketService.ts**: WebSocket client service
2. **RealTimeDashboard.tsx**: Dashboard that subscribes to real-time events
3. **Event Handlers**: Callback functions that update UI when events are received

## Event Types

### 1. app_usage_update
Emitted when a user switches between applications.

```json
{
  "type": "app_usage_update",
  "timestamp": 1640995200,
  "data": {
    "app_name": "Visual Studio Code",
    "window_title": "main.py - project",
    "start_time": 1640995140,
    "end_time": 1640995200,
    "duration": 60,
    "pid": 12345
  }
}
```

### 2. idle_status
Emitted when the system idle status changes.

```json
{
  "type": "idle_status",
  "timestamp": 1640995200,
  "data": {
    "is_idle": true,
    "idle_seconds": 300,
    "threshold": 180,
    "timestamp": 1640995200
  }
}
```

### 3. input_activity
Emitted periodically with input activity metrics.

```json
{
  "type": "input_activity",
  "timestamp": 1640995200,
  "data": {
    "timestamp": 1640995200,
    "keypress_count": 15,
    "mouse_click_count": 8,
    "mouse_scroll_count": 3,
    "mouse_move_count": 150,
    "total_inputs": 26
  }
}
```

### 4. focus_session_update
Emitted when focus sessions start, end, or are interrupted.

```json
{
  "type": "focus_session_update",
  "timestamp": 1640995200,
  "data": {
    "session_id": "focus_123",
    "start_time": 1640993700,
    "end_time": 1640995200,
    "was_interrupted": false,
    "duration": 1500,
    "notes": "Coding session",
    "status": "completed"
  }
}
```

### 5. break_update
Emitted when breaks are detected or completed.

```json
{
  "type": "break_update",
  "timestamp": 1640995200,
  "data": {
    "start_time": 1640994900,
    "end_time": 1640995200,
    "duration": 300,
    "break_type": "inactivity",
    "notes": "Coffee break",
    "status": "completed"
  }
}
```

## Setup and Usage

### Backend Setup

1. Install dependencies:
```bash
pip install flask-socketio==5.3.6
```

2. The WebSocket system is automatically initialized in `app_service.py`:
```python
from websocket_events import init_event_manager, setup_socketio_handlers, get_event_manager

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
init_event_manager(socketio)
setup_socketio_handlers(socketio)
```

3. Services emit events using the event manager:
```python
from websocket_events import get_event_manager

event_manager = get_event_manager()
if event_manager:
    event_manager.emit_app_usage_update({
        "app_name": app_name,
        "duration": duration,
        # ... other data
    })
```

### Frontend Setup

1. The WebSocket service is automatically initialized in `WebSocketService.ts`

2. Subscribe to events in components:
```typescript
import webSocketService from './WebSocketService';

useEffect(() => {
  webSocketService.subscribe('app_usage_update', handleAppUsageUpdate);
  webSocketService.subscribe('idle_status', handleIdleStatus);
  
  return () => {
    webSocketService.unsubscribe('app_usage_update', handleAppUsageUpdate);
    webSocketService.unsubscribe('idle_status', handleIdleStatus);
  };
}, []);
```

## Testing

### Test Server
Run the test server to verify WebSocket functionality:
```bash
python test_websocket_server.py
```

This will start a server that emits test events every 5 seconds.

### Manual Testing
1. Start the backend: `python app_service.py`
2. Start the frontend: `npm start`
3. Open the browser console to see WebSocket events
4. Navigate to the Real-Time Dashboard to see live updates

## Error Handling

### Backend
- WebSocket events are wrapped in try-catch blocks
- Failed event emissions are logged but don't crash the service
- Disconnected clients are automatically removed

### Frontend
- Automatic reconnection with exponential backoff
- Event listeners are protected from errors
- Connection status is tracked and displayed

## Performance Considerations

1. **Event Frequency**: Events are throttled to prevent overwhelming the frontend
2. **Data Size**: Event payloads are kept minimal
3. **Client Management**: Disconnected clients are cleaned up automatically
4. **Memory Management**: Event history is limited (e.g., last 50 app usage events)

## Troubleshooting

### Common Issues

1. **WebSocket not connecting**:
   - Check if the backend is running on port 5005
   - Verify CORS settings allow the frontend origin
   - Check browser console for connection errors

2. **Events not received**:
   - Verify the event manager is initialized
   - Check if services are emitting events
   - Look for errors in the backend console

3. **Frontend not updating**:
   - Check if event handlers are properly subscribed
   - Verify the WebSocket connection status
   - Look for JavaScript errors in the browser console

### Debug Mode
Enable debug logging by setting the WebSocket service to log all events:
```typescript
// In WebSocketService.ts
console.log('Received WebSocket event:', event.type, event.data);
```

## Future Enhancements

1. **Event Filtering**: Allow clients to subscribe to specific event types
2. **Event History**: Provide recent event history on connection
3. **Compression**: Compress event payloads for better performance
4. **Authentication**: Add authentication for WebSocket connections
5. **Rate Limiting**: Implement rate limiting for event emissions
