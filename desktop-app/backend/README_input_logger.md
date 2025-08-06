# Input Activity Logger

A comprehensive Python background script for logging keyboard keypresses and mouse clicks per minute without recording specific keys. This module is integrated into the CereBro Mental Burnout Tracker to provide detailed input activity analytics.

## Features

- **Cross-platform Support**: Windows, macOS, and Linux
- **Real-time Monitoring**: Continuously tracks keyboard and mouse input
- **Privacy-focused**: Counts inputs without recording specific keys or content
- **Configurable Intervals**: Adjustable logging intervals (default: 60 seconds)
- **SQLite Storage**: Efficient database storage with indexed queries
- **CSV Export**: Export input data to CSV files
- **Thread-safe**: Safe for multi-threaded applications
- **Integration Ready**: Easy integration with existing applications

## Database Schema

The module creates a SQLite database with the following structure:

```sql
CREATE TABLE input_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP NOT NULL,
    keypress_count INTEGER DEFAULT 0,
    mouse_click_count INTEGER DEFAULT 0,
    mouse_scroll_count INTEGER DEFAULT 0,
    mouse_move_count INTEGER DEFAULT 0,
    total_inputs INTEGER DEFAULT 0,
    interval_seconds INTEGER DEFAULT 60,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Columns

- `id`: Unique identifier for each record
- `timestamp`: When the input activity was recorded
- `keypress_count`: Number of keyboard keypresses in the interval
- `mouse_click_count`: Number of mouse clicks in the interval
- `mouse_scroll_count`: Number of mouse scroll events in the interval
- `mouse_move_count`: Number of mouse movements in the interval
- `total_inputs`: Total input events (keypresses + clicks + scrolls)
- `interval_seconds`: Duration of the logging interval
- `created_at`: When the record was created

## Installation

### Dependencies

The module requires the `pynput` library for input monitoring:

```bash
pip install pynput
```

### All Platforms
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from input_logger import InputLogger

# Create logger instance
logger = InputLogger(
    db_path="input_activity.db",
    log_interval=60,  # Log every 60 seconds
    enable_keyboard=True,
    enable_mouse=True
)

# Start logging
logger.start()

# ... your application code ...

# Stop logging
logger.stop()
```

### Integration with CereBro

The input logger is automatically integrated into the CereBro backend:

```python
# In app_service.py
from input_logger import InputLogger

# Initialize input logger
input_logger = InputLogger(
    db_path="input_activity.db", 
    log_interval=60,  # Log every minute
    enable_keyboard=True,
    enable_mouse=True
)
input_logger.start()
```

### API Endpoints

The CereBro backend provides REST API endpoints for accessing input activity data:

#### Get Recent Input Activity
```http
GET /api/input_activity?hours=24
```

Response:
```json
{
    "input_activity": [
        {
            "timestamp": "2024-01-01T10:00:00",
            "keypress_count": 150,
            "mouse_click_count": 25,
            "mouse_scroll_count": 5,
            "mouse_move_count": 1200,
            "total_inputs": 180,
            "interval_seconds": 60
        }
    ],
    "total_entries": 1440
}
```

#### Get Input Summary
```http
GET /api/input_summary?hours=24
```

Response:
```json
{
    "total_records": 1440,
    "total_keypresses": 216000,
    "total_clicks": 36000,
    "total_scrolls": 7200,
    "total_moves": 1728000,
    "total_inputs": 259200,
    "avg_keypresses": 150.0,
    "avg_clicks": 25.0,
    "avg_total_inputs": 180.0,
    "max_inputs": 500,
    "min_inputs": 0,
    "hours_analyzed": 24
}
```

#### Export to CSV
```http
GET /api/export_input_csv?hours=24
```

Response:
```json
{
    "success": true,
    "file_path": "input_export_1704067200.csv",
    "message": "Exported 24 hours of input data to input_export_1704067200.csv"
}
```

## Configuration

### InputLogger Parameters

- `db_path`: Path to SQLite database file (default: "input_activity.db")
- `log_interval`: How often to log data in seconds (default: 60)
- `enable_keyboard`: Whether to monitor keyboard input (default: True)
- `enable_mouse`: Whether to monitor mouse input (default: True)

### Logging Configuration

The module uses Python's logging module with the following configuration:

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('input_logger.log'),
        logging.StreamHandler()
    ]
)
```

## Platform-Specific Implementation

### Cross-platform
- Uses `pynput` library for input monitoring
- Works on Windows, macOS, and Linux
- No elevated permissions required
- Privacy-focused (counts only, no content recording)

## Methods

### Core Methods

#### `start()`
Start input logging in a background thread.

#### `stop()`
Stop input logging and log the final activity.

#### `get_recent_activity(hours=24)`
Get recent input activity from the last N hours.

#### `get_input_summary(hours=24)`
Get a summary of input activity statistics.

#### `export_to_csv(csv_path, hours=24)`
Export input activity to a CSV file.

### Internal Methods

#### `_on_key_press(key)`
Handle keyboard key press events.

#### `_on_key_release(key)`
Handle keyboard key release events.

#### `_on_mouse_click(x, y, button, pressed)`
Handle mouse click events.

#### `_on_mouse_scroll(x, y, dx, dy)`
Handle mouse scroll events.

#### `_on_mouse_move(x, y)`
Handle mouse movement events.

#### `_log_input_activity()`
Log current input activity to the database.

#### `_logging_loop()`
Main logging loop that runs in a background thread.

## Testing

### Quick Test
```bash
python test_input_logger.py
```

### Manual Testing
```python
from input_logger import InputLogger

logger = InputLogger(log_interval=10)  # 10 second interval for testing
logger.start()

# Type and move mouse for 30 seconds
import time
time.sleep(30)

logger.stop()

# View results
activity = logger.get_recent_activity(hours=1)
for (timestamp, keypresses, clicks, scrolls, moves, total, interval) in activity:
    print(f"{timestamp}: {keypresses} keys, {clicks} clicks, {total} total")
```

### Command Line Usage

```bash
# Basic usage with 60-second interval
python input_logger.py --interval 60 --duration 300

# Export to CSV after completion
python input_logger.py --interval 60 --duration 300 --export-csv input_data.csv

# Keyboard-only monitoring
python input_logger.py --no-mouse --interval 30 --duration 120

# Mouse-only monitoring
python input_logger.py --no-keyboard --interval 30 --duration 120
```

## Performance Considerations

- **CPU Usage**: Minimal CPU usage, primarily for event handling
- **Memory Usage**: Minimal memory footprint, primarily for counters
- **Database Size**: The database can grow large over time. Consider implementing a cleanup strategy
- **Privacy**: Only counts inputs, never records specific keys or content

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `pynput` is installed
2. **Permission Errors**: Some systems may require accessibility permissions
3. **Database Errors**: Check file permissions for the database directory
4. **No Input Detection**: Check if input monitoring is enabled in system settings

### Debug Mode

Enable debug logging by modifying the logging level:

```python
import logging
logging.getLogger('input_logger').setLevel(logging.DEBUG)
```

### Platform-Specific Issues

#### Windows
- May require running as administrator for some applications
- Check Windows security settings
- Verify accessibility permissions

#### macOS
- May require accessibility permissions in System Preferences
- Check if the application has input monitoring permissions
- May require running with elevated permissions

#### Linux
- May require X11 or Wayland permissions
- Check display server permissions
- Verify input device access

## Integration Examples

### With Flask Application
```python
from flask import Flask
from input_logger import InputLogger

app = Flask(__name__)
logger = InputLogger()

@app.before_first_request
def start_logger():
    logger.start()

@app.teardown_appcontext
def stop_logger():
    logger.stop()
```

### With Background Service
```python
import signal
from input_logger import InputLogger

logger = InputLogger()

def signal_handler(signum, frame):
    logger.stop()
    exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

logger.start()

# Keep the service running
while True:
    signal.pause()
```

### With Configuration Management
```python
import json
from input_logger import InputLogger

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)

logger = InputLogger(
    db_path=config.get('input_db_path', 'input_activity.db'),
    log_interval=config.get('input_log_interval', 60),
    enable_keyboard=config.get('enable_keyboard', True),
    enable_mouse=config.get('enable_mouse', True)
)

logger.start()
```

## Data Analysis

### Sample Queries

Get total inputs per hour:
```sql
SELECT 
    strftime('%H', timestamp) as hour,
    SUM(total_inputs) as total_inputs,
    AVG(total_inputs) as avg_inputs
FROM input_activity 
GROUP BY strftime('%H', timestamp)
ORDER BY hour;
```

Get keyboard vs mouse usage:
```sql
SELECT 
    DATE(timestamp) as date,
    SUM(keypress_count) as total_keypresses,
    SUM(mouse_click_count) as total_clicks,
    SUM(mouse_scroll_count) as total_scrolls
FROM input_activity 
GROUP BY DATE(timestamp)
ORDER BY date;
```

Get peak activity periods:
```sql
SELECT 
    timestamp,
    total_inputs,
    keypress_count,
    mouse_click_count
FROM input_activity 
ORDER BY total_inputs DESC
LIMIT 10;
```

## Privacy and Security

### Privacy Features

- **No Content Recording**: Only counts input events, never records specific keys or text
- **No Screenshots**: Does not capture screen content
- **No Network Transmission**: All data stored locally
- **Configurable Monitoring**: Can disable keyboard or mouse monitoring independently

### Security Considerations

- **Local Storage**: All data stored in local SQLite database
- **No Remote Access**: No automatic data transmission
- **User Control**: Users can enable/disable monitoring through preferences
- **Transparent Operation**: Clear logging of all activities

## License

This module is part of the CereBro Mental Burnout Tracker project and follows the same license terms.

## Contributing

When contributing to the input logger:

1. Test on multiple platforms
2. Follow the existing code style
3. Add appropriate error handling
4. Update documentation for new features
5. Add tests for new functionality
6. Consider privacy implications
7. Ensure no sensitive data is recorded 