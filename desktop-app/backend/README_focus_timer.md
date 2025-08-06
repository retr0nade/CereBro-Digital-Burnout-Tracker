# Focus Session Timer

A Python timer for managing focus sessions (Pomodoro-style) that tracks session start, end, interruptions, and stores detailed logs. This module is integrated into the CereBro Mental Burnout Tracker to provide comprehensive focus session analytics.

## Features

- **Pomodoro-style Sessions**: Configurable session durations (default: 25 minutes)
- **Interruption Detection**: Automatically detects when user becomes inactive
- **Session Tracking**: Detailed logging of session start, end, and interruptions
- **Cross-platform Support**: Works on Windows, macOS, and Linux
- **SQLite Storage**: Efficient local database storage with indexed queries
- **CSV Export**: Export focus session data to CSV files
- **Thread-safe**: Safe for multi-threaded applications
- **CLI Interface**: Command-line interface for easy usage
- **API Integration**: REST API endpoints for web integration

## Database Schema

The module creates a SQLite database with the following structure:

```sql
CREATE TABLE focus_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    target_duration INTEGER DEFAULT 1500,
    actual_duration REAL,
    interrupted BOOLEAN DEFAULT 0,
    interruption_duration REAL DEFAULT 0.0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Columns

- `id`: Unique identifier for each record
- `session_id`: Unique session identifier
- `start_time`: When the session started
- `end_time`: When the session ended
- `target_duration`: Target duration in seconds (default: 1500 = 25 minutes)
- `actual_duration`: Actual duration in seconds
- `interrupted`: Whether the session was interrupted
- `interruption_duration`: Total interruption time in seconds
- `notes`: User notes about the session
- `created_at`: When the record was created

## Installation

### Dependencies

The module uses platform-specific libraries for idle detection:

#### Windows
```bash
pip install pywin32
```

#### macOS
```bash
pip install pyobjc-framework-Quartz
```

#### Linux
```bash
pip install python-xlib
```

### All Platforms
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from focus_timer import FocusTimer

# Create timer instance
timer = FocusTimer(
    db_path="focus_sessions.db",
    idle_threshold=60  # 60 seconds of inactivity
)

# Start a 25-minute session
session_id = timer.start_session(25, "Work session")

# Check session status
status = timer.get_session_status()
print(f"Time remaining: {status['remaining_time']/60:.1f} minutes")

# Stop session
result = timer.stop_session("Session completed")
print(f"Duration: {result['actual_duration']/60:.1f} minutes")
```

### Command Line Usage

```bash
# Start a 25-minute focus session
python focus_timer.py --duration 25

# Start a 45-minute session with custom idle threshold
python focus_timer.py --duration 45 --idle-threshold 120

# Show session statistics
python focus_timer.py --show-stats

# Export to CSV
python focus_timer.py --export-csv focus_sessions.csv
```

### Integration with CereBro

The focus timer is automatically integrated into the CereBro backend:

```python
# In app_service.py
from focus_timer import FocusTimer

# Initialize focus timer
focus_timer = FocusTimer(
    db_path="focus_sessions.db",
    idle_threshold=60  # 60 seconds of inactivity
)
```

## API Endpoints

The CereBro backend provides REST API endpoints for focus session management:

### Start Focus Session
```http
POST /api/focus_session_start
Content-Type: application/json

{
    "duration_minutes": 25,
    "notes": "Work session"
}
```

Response:
```json
{
    "success": true,
    "session_id": "session_1704067200",
    "duration_minutes": 25,
    "message": "Started 25-minute focus session"
}
```

### Stop Focus Session
```http
POST /api/focus_session_stop
Content-Type: application/json

{
    "notes": "Session completed"
}
```

Response:
```json
{
    "success": true,
    "result": {
        "session_id": "session_1704067200",
        "start_time": "2024-01-01T10:00:00",
        "end_time": "2024-01-01T10:25:00",
        "target_duration": 1500,
        "actual_duration": 1500,
        "interrupted": false,
        "interruption_duration": 0.0,
        "completion_percentage": 100.0
    },
    "message": "Focus session stopped"
}
```

### Get Session Status
```http
GET /api/focus_session_status
```

Response:
```json
{
    "running": true,
    "session_id": "session_1704067200",
    "elapsed_time": 900.0,
    "target_duration": 1500,
    "remaining_time": 600.0,
    "completion_percentage": 60.0,
    "interrupted": false,
    "interruption_duration": 0.0
}
```

### Get Session History
```http
GET /api/focus_session_history?days=7
```

Response:
```json
{
    "sessions": [
        {
            "session_id": "session_1704067200",
            "start_time": "2024-01-01T10:00:00",
            "end_time": "2024-01-01T10:25:00",
            "target_duration": 1500,
            "actual_duration": 1500,
            "interrupted": false,
            "interruption_duration": 0.0,
            "notes": "Work session",
            "completion_percentage": 100.0
        }
    ],
    "total_entries": 1
}
```

### Get Session Statistics
```http
GET /api/focus_session_stats?days=7
```

Response:
```json
{
    "total_sessions": 10,
    "total_duration": 25000,
    "avg_duration": 2500,
    "completion_rate": 80.0,
    "interruption_rate": 20.0
}
```

### Export to CSV
```http
GET /api/export_focus_csv?days=7
```

Response:
```json
{
    "success": true,
    "file_path": "focus_sessions_export_1704067200.csv",
    "message": "Exported 7 days of focus session data to focus_sessions_export_1704067200.csv"
}
```

## Configuration

### FocusTimer Parameters

- `db_path`: Path to SQLite database file (default: "focus_sessions.db")
- `idle_threshold`: Seconds of inactivity before considering interrupted (default: 60)

### Logging Configuration

The module uses Python's logging module with the following configuration:

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('focus_timer.log'),
        logging.StreamHandler()
    ]
)
```

## Platform-Specific Implementation

### Windows
- Uses `GetLastInputInfo` API for accurate idle detection
- Uses `ctypes` to interface with Windows API
- Provides most accurate results on Windows

### macOS
- Uses Core Graphics framework for idle detection
- Requires `pyobjc-framework-Quartz` dependency
- Provides good accuracy on macOS

### Linux
- Uses X11 for idle detection
- Requires `python-xlib` dependency
- Works well on X11-based Linux systems

## Methods

### Core Methods

#### `start_session(duration_minutes=25, notes="")`
Start a new focus session with specified duration and notes.

#### `stop_session(notes="")`
Stop the current focus session and log the results.

#### `get_session_status()`
Get current session status including time remaining and progress.

#### `get_session_history(days=7)`
Get session history from the last N days.

#### `get_session_statistics(days=7)`
Get session statistics from the last N days.

#### `export_to_csv(csv_path, days=7)`
Export session data to a CSV file.

### Internal Methods

#### `_get_last_input_time()`
Get the last input time from the system.

#### `_check_activity()`
Check if the user is currently active.

#### `_monitor_activity()`
Monitor user activity for interruptions.

#### `_timer_loop()`
Main timer loop that runs in a background thread.

## Testing

### Quick Test
```bash
python test_focus_timer.py
```

### Manual Testing
```python
from focus_timer import FocusTimer

timer = FocusTimer(idle_threshold=30)  # 30 second idle threshold for testing
session_id = timer.start_session(2)  # 2 minute session

# Monitor session
import time
time.sleep(60)

result = timer.stop_session("Test completed")
print(f"Duration: {result['actual_duration']/60:.1f} minutes")
print(f"Interrupted: {'Yes' if result['interrupted'] else 'No'}")
```

## Performance Considerations

- **CPU Usage**: Minimal CPU usage, primarily for activity checking
- **Memory Usage**: Minimal memory footprint, primarily for session tracking
- **Database Size**: The database can grow large over time. Consider implementing a cleanup strategy
- **Accuracy**: Windows provides the most accurate idle detection. macOS and Linux implementations may vary

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure platform-specific dependencies are installed
2. **Permission Errors**: Some systems require elevated permissions for input monitoring
3. **Database Errors**: Check file permissions for the database directory
4. **No Activity Detection**: Try adjusting the idle threshold or check system settings

### Debug Mode

Enable debug logging by modifying the logging level:

```python
import logging
logging.getLogger('focus_timer').setLevel(logging.DEBUG)
```

### Platform-Specific Issues

#### Windows
- Ensure `pywin32` is properly installed
- Check Windows security settings
- Verify user has appropriate permissions

#### macOS
- Install `pyobjc-framework-Quartz`
- Check accessibility permissions in System Preferences
- May require running with elevated permissions

#### Linux
- Install `python-xlib`
- Ensure X11 is running
- Check display permissions

## Data Analysis

### Sample Queries

Get daily focus session trends:
```sql
SELECT 
    DATE(start_time) as date,
    COUNT(*) as session_count,
    AVG(actual_duration / 60.0) as avg_duration_minutes,
    AVG(completion_percentage) as avg_completion_rate
FROM focus_sessions 
GROUP BY DATE(start_time)
ORDER BY date DESC;
```

Get interrupted sessions:
```sql
SELECT 
    session_id,
    start_time,
    actual_duration / 60.0 as duration_minutes,
    interruption_duration / 60.0 as interruption_minutes
FROM focus_sessions 
WHERE interrupted = 1
ORDER BY start_time DESC;
```

Get completion rate by duration:
```sql
SELECT 
    target_duration / 60 as target_minutes,
    COUNT(*) as session_count,
    AVG(completion_percentage) as avg_completion_rate
FROM focus_sessions 
GROUP BY target_duration
ORDER BY target_duration;
```

## Privacy and Security

### Privacy Features

- **Local Storage**: All data stored in local SQLite database
- **No Content Recording**: Only tracks session timing, never records content
- **No Network Transmission**: No automatic data transmission
- **User Control**: Users can enable/disable tracking through preferences

### Security Considerations

- **Local Storage**: All data stored in local SQLite database
- **No Remote Access**: No automatic data transmission
- **User Control**: Users can enable/disable tracking through preferences
- **Transparent Operation**: Clear logging of all activities

## Integration Examples

### With Flask Application
```python
from flask import Flask
from focus_timer import FocusTimer

app = Flask(__name__)
timer = FocusTimer()

@app.route('/start_session', methods=['POST'])
def start_session():
    data = request.get_json()
    session_id = timer.start_session(
        data.get('duration_minutes', 25),
        data.get('notes', '')
    )
    return jsonify({'session_id': session_id})

@app.route('/stop_session', methods=['POST'])
def stop_session():
    data = request.get_json()
    result = timer.stop_session(data.get('notes', ''))
    return jsonify(result)
```

### With Background Service
```python
import signal
from focus_timer import FocusTimer

timer = FocusTimer()

def signal_handler(signum, frame):
    if timer.is_running:
        timer.stop_session("Service stopped")
    exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Start a session
timer.start_session(25, "Background session")

# Keep the service running
while True:
    signal.pause()
```

## License

This module is part of the CereBro Mental Burnout Tracker project and follows the same license terms.

## Contributing

When contributing to the focus timer:

1. Test on multiple platforms
2. Follow the existing code style
3. Add appropriate error handling
4. Update documentation for new features
5. Add tests for new functionality
6. Consider performance implications
7. Ensure proper cleanup on shutdown 