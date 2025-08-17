# 🧠 Unified SQLite Schema for Mental Burnout Tracker

This document describes the comprehensive unified SQLite database schema designed for tracking mental burnout indicators and digital wellness metrics.

## 📋 Overview

The unified schema provides a complete solution for tracking:
- **App Usage**: Time spent in different applications
- **Idle Periods**: System inactivity and break times
- **Input Activity**: Keyboard, mouse, and scroll interactions
- **Focus Sessions**: Dedicated work periods with interruption tracking
- **Break Logs**: Structured break activities with productivity tracking
- **Burnout Signals**: Stress indicators and behavioral patterns

## 🗄️ Database Schema

### 1. App Usage Table (`app_usage`)

Tracks time spent in different applications with detailed metadata.

```sql
CREATE TABLE app_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_name TEXT NOT NULL,
    start_time INTEGER NOT NULL,
    end_time INTEGER NOT NULL,
    duration INTEGER NOT NULL,
    window_title TEXT,
    category TEXT,
    created_at INTEGER DEFAULT (strftime('%s', 'now')),
    updated_at INTEGER DEFAULT (strftime('%s', 'now')),
    UNIQUE(app_name, start_time)
);
```

**Fields:**
- `app_name`: Name of the application (e.g., "Visual Studio Code", "Chrome")
- `start_time`: Unix timestamp when app usage started
- `end_time`: Unix timestamp when app usage ended
- `duration`: Duration in seconds
- `window_title`: Active window title (optional)
- `category`: App category (e.g., "development", "research", "social")

### 2. Idle Periods Table (`idle_periods`)

Tracks system inactivity and break periods.

```sql
CREATE TABLE idle_periods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time INTEGER NOT NULL,
    end_time INTEGER NOT NULL,
    duration INTEGER NOT NULL,
    reason TEXT,
    created_at INTEGER DEFAULT (strftime('%s', 'now')),
    updated_at INTEGER DEFAULT (strftime('%s', 'now')),
    UNIQUE(start_time)
);
```

**Fields:**
- `start_time`: Unix timestamp when idle period started
- `end_time`: Unix timestamp when idle period ended
- `duration`: Duration in seconds
- `reason`: Reason for idle period (e.g., "coffee_break", "lunch", "system_idle")

### 3. Input Activity Table (`input_activity`)

Tracks user input patterns and interaction metrics.

```sql
CREATE TABLE input_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,
    keypress_count INTEGER DEFAULT 0,
    mouse_click_count INTEGER DEFAULT 0,
    scroll_events INTEGER DEFAULT 0,
    mouse_movement INTEGER DEFAULT 0,
    created_at INTEGER DEFAULT (strftime('%s', 'now')),
    UNIQUE(timestamp)
);
```

**Fields:**
- `timestamp`: Unix timestamp of the activity
- `keypress_count`: Number of keypresses in the period
- `mouse_click_count`: Number of mouse clicks
- `scroll_events`: Number of scroll events
- `mouse_movement`: Mouse movement distance/units

### 4. Focus Sessions Table (`focus_sessions`)

Tracks dedicated work sessions with focus metrics.

```sql
CREATE TABLE focus_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL UNIQUE,
    start_time INTEGER NOT NULL,
    end_time INTEGER NOT NULL,
    was_interrupted BOOLEAN DEFAULT FALSE,
    focus_score REAL,
    notes TEXT,
    created_at INTEGER DEFAULT (strftime('%s', 'now')),
    updated_at INTEGER DEFAULT (strftime('%s', 'now'))
);
```

**Fields:**
- `session_id`: Unique identifier for the focus session
- `start_time`: Unix timestamp when session started
- `end_time`: Unix timestamp when session ended
- `was_interrupted`: Whether the session was interrupted
- `focus_score`: Focus quality score (0.0-1.0)
- `notes`: Additional notes about the session

### 5. Break Logs Table (`break_logs`)

Tracks structured break activities with productivity assessment.

```sql
CREATE TABLE break_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time INTEGER NOT NULL,
    end_time INTEGER NOT NULL,
    break_type TEXT NOT NULL,
    duration INTEGER NOT NULL,
    was_productive BOOLEAN,
    notes TEXT,
    created_at INTEGER DEFAULT (strftime('%s', 'now')),
    updated_at INTEGER DEFAULT (strftime('%s', 'now')),
    UNIQUE(start_time)
);
```

**Break Types:**
- `short`: Short breaks (5-15 minutes)
- `long`: Long breaks (15-60 minutes)
- `micro`: Micro breaks (1-5 minutes)
- `lunch`: Lunch breaks
- `coffee`: Coffee breaks

### 6. App Categories Table (`app_categories`)

Organizes applications into categories for better analytics.

```sql
CREATE TABLE app_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    is_productive BOOLEAN DEFAULT FALSE,
    created_at INTEGER DEFAULT (strftime('%s', 'now')),
    updated_at INTEGER DEFAULT (strftime('%s', 'now'))
);
```

### 7. Burnout Signals Table (`burnout_signals`)

Tracks stress indicators and behavioral patterns.

```sql
CREATE TABLE burnout_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_type TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    severity REAL DEFAULT 1.0,
    description TEXT,
    metadata TEXT,  -- JSON string for additional data
    created_at INTEGER DEFAULT (strftime('%s', 'now'))
);
```

**Common Signal Types:**
- `rapid_tab_switching`: Frequent tab switching
- `extended_focus_session`: Long work without breaks
- `rapid_context_switching`: Frequent task switching
- `high_input_frequency`: Excessive typing/mouse activity
- `low_idle_time`: Insufficient break time

## 🐍 Python API

### BurnoutTrackerDB Class

The main class for interacting with the database.

```python
from data.unified_schema import BurnoutTrackerDB, AppUsage, IdlePeriod, InputActivity, FocusSession, BreakLog, BreakType

# Initialize database
db = BurnoutTrackerDB("data/burnout_tracker.db")

# Insert app usage
app_usage = AppUsage(
    app_name="Visual Studio Code",
    start_time=1640995200,
    end_time=1640998800,
    duration=3600,
    window_title="project/src/main.py",
    category="development"
)
db.insert_app_usage(app_usage)

# Insert idle period
idle_period = IdlePeriod(
    start_time=1640998800,
    end_time=1640999100,
    duration=300,
    reason="coffee_break"
)
db.insert_idle_period(idle_period)

# Insert input activity
input_activity = InputActivity(
    timestamp=1640995200,
    keypress_count=150,
    mouse_click_count=25,
    scroll_events=10,
    mouse_movement=500
)
db.insert_input_activity(input_activity)

# Insert focus session
focus_session = FocusSession(
    session_id="focus_1234567890",
    start_time=1640995200,
    end_time=1640998800,
    was_interrupted=False,
    focus_score=0.85,
    notes="Productive coding session"
)
db.insert_focus_session(focus_session)

# Insert break log
break_log = BreakLog(
    start_time=1640998800,
    end_time=1640999100,
    break_type=BreakType.SHORT,
    duration=300,
    was_productive=True,
    notes="Quick stretch and coffee"
)
db.insert_break_log(break_log)

# Insert burnout signal
db.insert_burnout_signal(
    signal_type="rapid_tab_switching",
    severity=0.7,
    description="User switched tabs 15 times in 5 minutes",
    metadata={"tab_switches": 15, "time_window": 300}
)
```

### Key Methods

#### Data Insertion
- `insert_app_usage(app_usage: AppUsage) -> int`
- `insert_idle_period(idle_period: IdlePeriod) -> int`
- `insert_input_activity(input_activity: InputActivity) -> int`
- `insert_focus_session(focus_session: FocusSession) -> int`
- `insert_break_log(break_log: BreakLog) -> int`
- `insert_burnout_signal(signal_type: str, severity: float, description: str, metadata: dict) -> int`

#### Data Retrieval
- `get_app_usage_by_date(date: str, limit: int = 100) -> List[Tuple]`
- `get_idle_periods_by_date(date: str, limit: int = 100) -> List[Tuple]`
- `get_focus_sessions_by_date(date: str, limit: int = 50) -> List[Tuple]`
- `get_break_logs_by_date(date: str, limit: int = 50) -> List[Tuple]`
- `get_daily_summary(date: str) -> Dict[str, Any]`
- `get_recent_activity(hours: int = 24, limit: int = 100) -> Dict[str, List]`

#### Maintenance
- `cleanup_old_data(days_to_keep: int = 30)`

## 🔄 Integration with Existing App

### UnifiedBurnoutTracker Class

A high-level integration class that combines the database with existing app components.

```python
from integration_example import UnifiedBurnoutTracker

tracker = UnifiedBurnoutTracker()

# Start tracking an app
tracker.start_app_tracking("Visual Studio Code", "project/src/main.py", "development")

# Start a focus session
tracker.start_focus_session("Morning coding session")

# Log input activity
tracker.log_input_activity(
    keypress_count=50,
    mouse_click_count=10,
    scroll_events=5,
    mouse_movement=200
)

# End focus session
tracker.end_focus_session(focus_score=0.85, notes="Productive session")

# End app tracking
tracker.end_app_tracking()

# Log a break
tracker.log_break(
    BreakType.SHORT,
    start_time=1640998800,
    end_time=1640999100,
    was_productive=True,
    notes="Coffee break"
)

# Log burnout signal
tracker.log_burnout_signal(
    "rapid_context_switching",
    severity=0.7,
    description="Switched between 5 tasks in 30 minutes"
)

# Get analytics
summary = tracker.get_today_summary()
recent = tracker.get_recent_activity(hours=24)
```

## 📊 Analytics and Insights

### Daily Summary

The `get_daily_summary()` method provides comprehensive daily analytics:

```python
summary = db.get_daily_summary("2024-01-01")
print(f"Total App Time: {summary['total_app_time']} seconds")
print(f"Total Idle Time: {summary['total_idle_time']} seconds")
print(f"Focus Sessions: {summary['focus_sessions']['total']}")
print(f"Completed Sessions: {summary['focus_sessions']['completed']}")
print(f"Break Types: {list(summary['breaks'].keys())}")
print(f"Burnout Signals: {list(summary['burnout_signals'].keys())}")
```

### Recent Activity

The `get_recent_activity()` method provides recent activity across all tables:

```python
recent = db.get_recent_activity(hours=24)
print(f"App Usage Records: {len(recent['app_usage'])}")
print(f"Idle Periods: {len(recent['idle_periods'])}")
print(f"Input Activity Records: {len(recent['input_activity'])}")
```

## 🚀 Usage Examples

### Basic Usage

```python
# Initialize database
db = BurnoutTrackerDB()

# Log a work session
app_usage = AppUsage(
    app_name="Chrome",
    start_time=int(time.time()) - 3600,
    end_time=int(time.time()),
    duration=3600,
    category="research"
)
db.insert_app_usage(app_usage)

# Get today's summary
today = datetime.now().strftime("%Y-%m-%d")
summary = db.get_daily_summary(today)
print(f"Today's app time: {summary['total_app_time']/3600:.1f} hours")
```

### Advanced Integration

```python
# Use the integration class for real-time tracking
tracker = UnifiedBurnoutTracker()

# Simulate a workday
tracker.start_app_tracking("VS Code", "project/main.py", "development")
tracker.start_focus_session("Morning coding")

# Simulate work activity
for i in range(3):
    time.sleep(1)
    tracker.log_input_activity(
        keypress_count=50 + i*10,
        mouse_click_count=10 + i*2
    )

tracker.end_focus_session(focus_score=0.85)
tracker.end_app_tracking()

# Get summary
summary = tracker.get_today_summary()
print(f"Focus sessions: {summary['focus_sessions']['total']}")
```

## 🔧 Database Maintenance

### Cleanup Old Data

```python
# Keep only last 30 days of data
db.cleanup_old_data(days_to_keep=30)
```

### Database Location

By default, the database is created at `data/burnout_tracker.db`. You can specify a custom path:

```python
db = BurnoutTrackerDB("custom/path/to/database.db")
```

## 📈 Performance Considerations

- **Indexes**: The schema includes indexes on timestamp fields for efficient queries
- **Unique Constraints**: Prevents duplicate entries for the same time periods
- **Batch Operations**: Use transactions for bulk insertions
- **Cleanup**: Regular cleanup prevents database bloat

## 🔒 Data Privacy

- All data is stored locally in SQLite
- No external dependencies or cloud services
- Data can be exported or backed up as needed
- Optional encryption can be added for sensitive data

## 🧪 Testing

Run the example scripts to test the functionality:

```bash
# Basic functionality test
python example_usage.py

# Integration test
python integration_example.py
```

## 📝 Migration from Existing Schema

If you have an existing database, you can migrate data using the existing `models.py` functions and then use the new unified schema for future data.

The new schema is designed to be backward compatible and can coexist with existing data structures.
