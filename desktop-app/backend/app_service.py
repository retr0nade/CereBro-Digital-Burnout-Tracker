import threading, time, sqlite3, json, os, platform
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from metrics.apps import get_foreground_app
from metrics.idle import get_idle_seconds
from data.models import store_pref, get_pref
from cerebro_db import CerebroDB
from api.routes import api
from window_tracker import WindowTracker
from idle_monitor import IdleMonitor
from input_logger import InputLogger
from screen_time_tracker import ScreenTimeTracker
from focus_timer import FocusTimer
from break_monitor import BreakMonitor
from config_manager import config
from service_manager import ServiceManager
from websocket_events import init_event_manager, setup_socketio_handlers, get_event_manager

SETTINGS_PATH = "settings.json"

def load_settings():
    if not os.path.exists(SETTINGS_PATH):
        store_pref({
            "track_apps": True,
            "track_idle": True,
            "idle_threshold": 180,
            "track_screenshots": False,
            "track_audio": False,
            "track_windows": True,  # New setting for window tracking
            "track_idle_detailed": True,  # New setting for detailed idle monitoring
            "track_input": True,  # New setting for input monitoring
            "track_screen_time": True,  # New setting for screen time tracking
            "track_focus_sessions": True,  # New setting for focus session tracking
            "track_breaks": True  # New setting for break monitoring
        })
    return get_pref()

def update_pref(new_settings):
    store_pref(new_settings)

settings = load_settings()
app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000", "http://localhost:3001", "http://localhost:5005"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Initialize SocketIO with CORS support
socketio = SocketIO(app, cors_allowed_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5005"])
event_manager = init_event_manager(socketio)
setup_socketio_handlers(socketio)  # No need to pass event_manager as it's managed globally

# Register API routes
app.register_blueprint(api, url_prefix='/api')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
init_event_manager(socketio)
setup_socketio_handlers(socketio)

# Initialize unified database
unified_db = CerebroDB(config.get_database_path())
print("Unified database initialized successfully")

# Initialize service manager for status tracking (will be created when needed)
service_manager = None

# Initialize window tracker
window_tracker = None
if settings.get("track_windows", True):
    try:
        service_config = config.get_service_config('window_tracker')
        window_tracker = WindowTracker(
            log_interval=service_config.get('log_interval', 1.0),
            cerebro_db=unified_db
        )
        window_tracker.start()
        print("Window tracker started successfully")
    except Exception as e:
        print(f"Failed to start window tracker: {e}")

# Initialize idle monitor
idle_monitor = None
if settings.get("track_idle_detailed", True):
    try:
        service_config = config.get_service_config('idle_monitor')
        idle_monitor = IdleMonitor(
            timeout_seconds=service_config.get('timeout_seconds', 300),
            check_interval=service_config.get('check_interval', 1.0),
            cerebro_db=unified_db
        )
        idle_monitor.start()
        print("Idle monitor started successfully")
    except Exception as e:
        print(f"Failed to start idle monitor: {e}")

# Initialize input logger
input_logger = None
if settings.get("track_input", True):
    try:
        service_config = config.get_service_config('input_logger')
        input_logger = InputLogger(
            log_interval=service_config.get('log_interval', 60),
            enable_keyboard=service_config.get('enable_keyboard', True),
            enable_mouse=service_config.get('enable_mouse', True),
            cerebro_db=unified_db
        )
        input_logger.start()
        print("Input logger started successfully")
    except Exception as e:
        print(f"Failed to start input logger: {e}")

# Initialize screen time tracker
screen_time_tracker = None
if settings.get("track_screen_time", True):
    try:
        service_config = config.get_service_config('screen_time_tracker')
        screen_time_tracker = ScreenTimeTracker(
            idle_threshold=service_config.get('idle_threshold', 60),
            check_interval=service_config.get('check_interval', 1.0),
            daily_reset_hour=service_config.get('daily_reset_hour', 0)
        )
        screen_time_tracker.start()
        print("Screen time tracker started successfully")
    except Exception as e:
        print(f"Failed to start screen time tracker: {e}")

# Initialize focus timer
focus_timer = None
if settings.get("track_focus_sessions", True):
    try:
        service_config = config.get_service_config('focus_timer')
        focus_timer = FocusTimer(
            idle_threshold=service_config.get('idle_threshold', 60),
            cerebro_db=unified_db
        )
        print("Focus timer initialized successfully")
    except Exception as e:
        print(f"Failed to initialize focus timer: {e}")

# Initialize break monitor
break_monitor = None
if settings.get("track_breaks", True):
    try:
        service_config = config.get_service_config('break_monitor')
        break_monitor = BreakMonitor(
            min_break_duration=service_config.get('min_break_duration', 120),
            max_break_duration=service_config.get('max_break_duration', 900),
            check_interval=service_config.get('check_interval', 1.0),
            detect_lock_events=service_config.get('detect_lock_events', True)
        )
        break_monitor.start()
        print("Break monitor started successfully")
    except Exception as e:
        print(f"Failed to start break monitor: {e}")

def collect_app_usage():
    last_app = None
    last_app_start = None
    while True:
        settings = load_settings()
        if not settings.get("track_apps"):
            time.sleep(2)
            continue
        try:
            app_name, win_title = get_foreground_app()
            ts = int(time.time())
            # store_app_event(app_name, win_title, ts)  # Commented out - function doesn't exist
            
            # Emit WebSocket event for app usage update
            try:
                event_manager = get_event_manager()
                if event_manager and last_app is not None and last_app != app_name:
                    # Calculate duration for the previous app
                    duration = ts - last_app_start if last_app_start else 1
                    event_manager.emit_app_usage_update({
                        "app_name": last_app,
                        "window_title": win_title,
                        "start_time": last_app_start or ts,
                        "end_time": ts,
                        "duration": duration,
                        "pid": 0  # We don't have PID in this context
                    })
                    # store_metric("app_switch", app_name, ts)  # Commented out - function doesn't exist
            except Exception as e:
                print(f"Failed to emit app usage WebSocket event: {e}")
            
            if last_app != app_name:
                last_app_start = ts
            last_app = app_name
        except Exception as e:
            print(f"Error in collect_app_usage: {e}")
        time.sleep(1)

def collect_idle():
    last_idle_status = False
    while True:
        settings = load_settings()
        if not settings.get("track_idle"):
            time.sleep(5)
            continue
        try:
            idle_sec = get_idle_seconds()
            current_idle_status = idle_sec > settings["idle_threshold"]
            
            if current_idle_status:
                # store_idle_event(idle_sec, int(time.time()))  # Commented out - function doesn't exist
                pass
            
            # Emit WebSocket event when idle status changes
            if current_idle_status != last_idle_status:
                try:
                    event_manager = get_event_manager()
                    if event_manager:
                        event_manager.emit_idle_status({
                            "is_idle": current_idle_status,
                            "idle_seconds": idle_sec,
                            "threshold": settings["idle_threshold"],
                            "timestamp": int(time.time())
                        })
                except Exception as e:
                    print(f"Failed to emit idle status WebSocket event: {e}")
            
            last_idle_status = current_idle_status
        except Exception as e:
            print(f"Error in collect_idle: {e}")
        time.sleep(15)

@app.route('/api/metrics', methods=["GET"])
def api_metrics():
    # Return all metrics for dashboard
    try:
        # Pull from CerebroDB and normalize to the array-based shape the frontend expects
        raw_usage = unified_db.get_app_usage(limit=200) or []
        raw_idle = unified_db.get_idle_periods(limit=200) or []

        # Convert dict rows to tuples: [app_name, start_time, end_time, duration, category]
        recent_usage = [
            [
                row.get('app_name'),
                row.get('start_time'),
                row.get('end_time'),
                row.get('duration', 0),
                None  # category placeholder (not stored in CerebroDB)
            ]
            for row in raw_usage
        ]

        # Convert idle dict rows to tuples: [start_time, end_time, duration, reason]
        recent_idle = [
            [
                row.get('start_time'),
                row.get('end_time'),
                row.get('duration', 0),
                None  # reason placeholder
            ]
            for row in raw_idle
        ]

        total_app_time = sum([row.get('duration', 0) for row in raw_usage])
        total_idle_time = sum([row.get('duration', 0) for row in raw_idle])

        return jsonify({
            "recent_usage": recent_usage,
            "recent_idle": recent_idle,
            "app_switches": [],
            "focus_score": 85,
            "burnout_signals": [],
            "metrics_summary": {
                "app_switches": len(recent_usage),
                "recent_usage": len(recent_usage),
                "idle_events": len(recent_idle),
                "focus_score": 85,
                "total_app_time": total_app_time,
                "total_idle_time": total_idle_time
            }
        })
    except Exception as e:
        print(f"Error in api_metrics: {e}")
        return jsonify({
            "recent_usage": [],
            "recent_idle": [],
            "app_switches": [],
            "focus_score": 85,
            "burnout_signals": [],
            "metrics_summary": {
                "app_switches": 0,
                "recent_usage": 0,
                "idle_events": 0,
                "focus_score": 85,
                "total_app_time": 0,
                "total_idle_time": 0
            }
        })

@app.route('/api/insights', methods=["GET"])
def api_insights():
    """Get AI insights and suggestions"""
    try:
        # For now, return some sample insights
        insights = {
            "suggestions": [
                {
                    "id": "1",
                    "type": "productivity_tip",
                    "severity": "info",
                    "message": "You've been working for 2 hours. Consider taking a 5-minute break.",
                    "rule": "long_work_session",
                    "timestamp": int(time.time())
                },
                {
                    "id": "2", 
                    "type": "focus_reminder",
                    "severity": "warning",
                    "message": "You've switched between apps frequently. Try to focus on one task at a time.",
                    "rule": "frequent_app_switching",
                    "timestamp": int(time.time())
                }
            ],
            "meta": {
                "total_suggestions": 2,
                "generated_at": int(time.time())
            },
            "generated_at": int(time.time())
        }
        return jsonify(insights)
    except Exception as e:
        print(f"Error in api_insights: {e}")
        return jsonify({
            "suggestions": [],
            "meta": {},
            "generated_at": int(time.time())
        })

@app.route('/api/preferences', methods=["GET", "POST"])
def api_preferences():
    if request.method == "POST":
        update_pref(request.json)
        return {"ok": True}
    return jsonify(get_pref())

@app.route('/api/extension_data', methods=["POST"])
def api_extension():
    # Browser extension posts data here
    try:
        data = request.get_json()
        # store_metric("browser_ext", json.dumps(data), int(time.time()))  # Commented out - function doesn't exist
        return {"ok": True}
    except Exception as e:
        print(f"Error in api_extension: {e}")
        return {"ok": False, "error": str(e)}

@app.route('/api/window_activity', methods=["GET"])
def api_window_activity():
    """Get window activity data"""
    try:
        if window_tracker is None:
            return jsonify({"error": "Window tracker not available"}), 500
        
        hours = request.args.get('hours', 24, type=int)
        activity = window_tracker.get_recent_activity(hours=hours)
        
        return jsonify({
            "activity": activity,
            "total_entries": len(activity)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/window_summary', methods=["GET"])
def api_window_summary():
    """Get window activity summary"""
    try:
        if window_tracker is None:
            return jsonify({"error": "Window tracker not available"}), 500
        
        hours = request.args.get('hours', 24, type=int)
        summary = window_tracker.get_app_summary(hours=hours)
        
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/idle_activity', methods=["GET"])
def api_idle_activity():
    """Get idle activity data"""
    try:
        if idle_monitor is None:
            return jsonify({"error": "Idle monitor not available"}), 500
        
        hours = request.args.get('hours', 24, type=int)
        idle_periods = idle_monitor.get_recent_idle_periods(hours=hours)
        
        return jsonify({
            "idle_periods": idle_periods,
            "total_entries": len(idle_periods)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/idle_summary', methods=["GET"])
def api_idle_summary():
    """Get idle activity summary"""
    try:
        if idle_monitor is None:
            return jsonify({"error": "Idle monitor not available"}), 500
        
        hours = request.args.get('hours', 24, type=int)
        summary = idle_monitor.get_idle_summary(hours=hours)
        
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/export_idle_csv', methods=["GET"])
def api_export_idle_csv():
    """Export idle data to CSV"""
    try:
        if idle_monitor is None:
            return jsonify({"error": "Idle monitor not available"}), 500
        
        hours = request.args.get('hours', 24, type=int)
        csv_path = f"idle_export_{int(time.time())}.csv"
        
        idle_monitor.export_to_csv(csv_path, hours=hours)
        
        return jsonify({
            "success": True,
            "file_path": csv_path,
            "message": f"Exported {hours} hours of idle data to {csv_path}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/input_activity', methods=["GET"])
def api_input_activity():
    """Get input activity data"""
    try:
        if input_logger is None:
            return jsonify({"error": "Input logger not available"}), 500
        
        hours = request.args.get('hours', 24, type=int)
        input_activity = input_logger.get_recent_activity(hours=hours)
        
        return jsonify({
            "input_activity": input_activity,
            "total_entries": len(input_activity)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/input_summary', methods=["GET"])
def api_input_summary():
    """Get input activity summary"""
    try:
        if input_logger is None:
            return jsonify({"error": "Input logger not available"}), 500
        
        hours = request.args.get('hours', 24, type=int)
        summary = input_logger.get_input_summary(hours=hours)
        
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/export_input_csv', methods=["GET"])
def api_export_input_csv():
    """Export input data to CSV"""
    try:
        if input_logger is None:
            return jsonify({"error": "Input logger not available"}), 500
        
        hours = request.args.get('hours', 24, type=int)
        csv_path = f"input_export_{int(time.time())}.csv"
        
        input_logger.export_to_csv(csv_path, hours=hours)
        
        return jsonify({
            "success": True,
            "file_path": csv_path,
            "message": f"Exported {hours} hours of input data to {csv_path}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/screen_time_summary', methods=["GET"])
def api_screen_time_summary():
    """Get screen time summary"""
    try:
        if screen_time_tracker is None:
            return jsonify({"error": "Screen time tracker not available"}), 500
        
        summary = screen_time_tracker.get_today_summary()
        
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/screen_time_weekly', methods=["GET"])
def api_screen_time_weekly():
    """Get weekly screen time summary"""
    try:
        if screen_time_tracker is None:
            return jsonify({"error": "Screen time tracker not available"}), 500
        
        summary = screen_time_tracker.get_weekly_summary()
        
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/screen_time_sessions', methods=["GET"])
def api_screen_time_sessions():
    """Get recent screen time sessions"""
    try:
        if screen_time_tracker is None:
            return jsonify({"error": "Screen time tracker not available"}), 500
        
        hours = request.args.get('hours', 24, type=int)
        sessions = screen_time_tracker.get_recent_sessions(hours=hours)
        
        return jsonify({
            "sessions": sessions,
            "total_entries": len(sessions)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/export_screen_time_csv', methods=["GET"])
def api_export_screen_time_csv():
    """Export screen time data to CSV"""
    try:
        if screen_time_tracker is None:
            return jsonify({"error": "Screen time tracker not available"}), 500
        
        days = request.args.get('days', 7, type=int)
        csv_path = f"screen_time_export_{int(time.time())}.csv"
        
        screen_time_tracker.export_to_csv(csv_path, days=days)
        
        return jsonify({
            "success": True,
            "file_path": csv_path,
            "message": f"Exported {days} days of screen time data to {csv_path}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/focus_session_start', methods=["POST"])
def api_focus_session_start():
    """Start a new focus session"""
    try:
        if focus_timer is None:
            return jsonify({"error": "Focus timer not available"}), 500
        
        data = request.get_json() or {}
        duration_minutes = data.get('duration_minutes', 25)
        notes = data.get('notes', '')
        
        session_id = focus_timer.start_session(duration_minutes, notes)
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "duration_minutes": duration_minutes,
            "message": f"Started {duration_minutes}-minute focus session"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/focus_session_stop', methods=["POST"])
def api_focus_session_stop():
    """Stop the current focus session"""
    try:
        if focus_timer is None:
            return jsonify({"error": "Focus timer not available"}), 500
        
        data = request.get_json() or {}
        notes = data.get('notes', '')
        
        result = focus_timer.stop_session(notes)
        
        return jsonify({
            "success": True,
            "result": result,
            "message": "Focus session stopped"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/focus_session_status', methods=["GET"])
def api_focus_session_status():
    """Get current focus session status"""
    try:
        if focus_timer is None:
            return jsonify({"error": "Focus timer not available"}), 500
        
        status = focus_timer.get_session_status()
        
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/focus_session_history', methods=["GET"])
def api_focus_session_history():
    """Get focus session history"""
    try:
        if focus_timer is None:
            return jsonify({"error": "Focus timer not available"}), 500
        
        days = request.args.get('days', 7, type=int)
        sessions = focus_timer.get_session_history(days=days)
        
        return jsonify({
            "sessions": sessions,
            "total_entries": len(sessions)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/focus_session_stats', methods=["GET"])
def api_focus_session_stats():
    """Get focus session statistics"""
    try:
        if focus_timer is None:
            return jsonify({"error": "Focus timer not available"}), 500
        
        days = request.args.get('days', 7, type=int)
        stats = focus_timer.get_session_statistics(days=days)
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/export_focus_csv', methods=["GET"])
def api_export_focus_csv():
    """Export focus session data to CSV"""
    try:
        if focus_timer is None:
            return jsonify({"error": "Focus timer not available"}), 500
        
        days = request.args.get('days', 7, type=int)
        csv_path = f"focus_sessions_export_{int(time.time())}.csv"
        
        focus_timer.export_to_csv(csv_path, days=days)
        
        return jsonify({
            "success": True,
            "file_path": csv_path,
            "message": f"Exported {days} days of focus session data to {csv_path}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/break_status', methods=["GET"])
def api_break_status():
    """Get current break monitoring status"""
    try:
        if break_monitor is None:
            return jsonify({"error": "Break monitor not available"}), 500
        
        status = break_monitor.get_current_status()
        
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/break_history', methods=["GET"])
def api_break_history():
    """Get break history"""
    try:
        if break_monitor is None:
            return jsonify({"error": "Break monitor not available"}), 500
        
        hours = request.args.get('hours', 24, type=int)
        breaks = break_monitor.get_recent_breaks(hours=hours)
        
        return jsonify({
            "breaks": breaks,
            "total_entries": len(breaks)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/break_stats', methods=["GET"])
def api_break_stats():
    """Get break statistics"""
    try:
        if break_monitor is None:
            return jsonify({"error": "Break monitor not available"}), 500
        
        hours = request.args.get('hours', 24, type=int)
        stats = break_monitor.get_break_statistics(hours=hours)
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/lock_events', methods=["GET"])
def api_lock_events():
    """Get lock event history"""
    try:
        if break_monitor is None:
            return jsonify({"error": "Break monitor not available"}), 500
        
        hours = request.args.get('hours', 24, type=int)
        events = break_monitor.get_recent_lock_events(hours=hours)
        
        return jsonify({
            "events": events,
            "total_entries": len(events)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/export_break_csv', methods=["GET"])
def api_export_break_csv():
    """Export break data to CSV"""
    try:
        if break_monitor is None:
            return jsonify({"error": "Break monitor not available"}), 500
        
        hours = request.args.get('hours', 24, type=int)
        csv_path = f"break_activity_export_{int(time.time())}.csv"
        
        break_monitor.export_to_csv(csv_path, hours=hours)
        
        return jsonify({
            "success": True,
            "file_path": csv_path,
            "message": f"Exported {hours} hours of break data to {csv_path}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# New unified API endpoints for cerebro.db data
@app.route('/api/status', methods=["GET"])
def api_status():
    """Get status of all trackers"""
    try:
        # Create a simple status response without using ServiceManager
        status = {
            "window_tracker": {
                "name": "Window Tracker",
                "status": "running" if window_tracker and window_tracker.is_running else "stopped",
                "start_time": None,
                "last_error": None,
                "restart_count": 0,
                "max_restarts": 3,
                "uptime": None
            },
            "idle_monitor": {
                "name": "Idle Monitor", 
                "status": "running" if idle_monitor and idle_monitor.is_running else "stopped",
                "start_time": None,
                "last_error": None,
                "restart_count": 0,
                "max_restarts": 3,
                "uptime": None
            },
            "input_logger": {
                "name": "Input Logger",
                "status": "running" if input_logger and input_logger.is_running else "stopped", 
                "start_time": None,
                "last_error": None,
                "restart_count": 0,
                "max_restarts": 3,
                "uptime": None
            },
            "screen_time_tracker": {
                "name": "Screen Time Tracker",
                "status": "running" if screen_time_tracker and screen_time_tracker.is_running else "stopped",
                "start_time": None,
                "last_error": None,
                "restart_count": 0,
                "max_restarts": 3,
                "uptime": None
            },
            "focus_timer": {
                "name": "Focus Timer",
                "status": "initialized" if focus_timer else "not_initialized",
                "start_time": None,
                "last_error": None,
                "restart_count": 0,
                "max_restarts": 3,
                "uptime": None
            },
            "break_monitor": {
                "name": "Break Monitor",
                "status": "running" if break_monitor and break_monitor.is_running else "stopped",
                "start_time": None,
                "last_error": None,
                "restart_count": 0,
                "max_restarts": 3,
                "uptime": None
            }
        }
        
        return jsonify({
            "status": "success",
            "services": status,
            "timestamp": int(time.time())
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/logs/app_usage', methods=["GET"])
def api_logs_app_usage():
    """Get app usage logs from cerebro.db"""
    try:
        limit = request.args.get('limit', 100, type=int)
        
        # Use get_app_usage method from CerebroDB
        app_usage_data = unified_db.get_app_usage(limit=limit)
        
        return jsonify({
            "status": "success",
            "data": app_usage_data,
            "total_entries": len(app_usage_data),
            "timestamp": int(time.time())
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/logs/idle', methods=["GET"])
def api_logs_idle():
    """Get idle logs from cerebro.db"""
    try:
        limit = request.args.get('limit', 100, type=int)
        
        # Use get_idle_periods method from CerebroDB
        idle_data = unified_db.get_idle_periods(limit=limit)
        
        return jsonify({
            "status": "success",
            "data": idle_data,
            "total_entries": len(idle_data),
            "timestamp": int(time.time())
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/logs/input', methods=["GET"])
def api_logs_input():
    """Get input logs from cerebro.db"""
    try:
        limit = request.args.get('limit', 100, type=int)
        
        # Use get_input_activity method from CerebroDB
        input_data = unified_db.get_input_activity(limit=limit)
        
        return jsonify({
            "status": "success",
            "data": input_data,
            "total_entries": len(input_data),
            "timestamp": int(time.time())
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/logs/focus', methods=["GET"])
def api_logs_focus():
    """Get focus logs from cerebro.db"""
    try:
        limit = request.args.get('limit', 100, type=int)
        
        # Use get_focus_sessions method from CerebroDB
        focus_data = unified_db.get_focus_sessions(limit=limit)
        
        return jsonify({
            "status": "success",
            "data": focus_data,
            "total_entries": len(focus_data),
            "timestamp": int(time.time())
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/logs/breaks', methods=["GET"])
def api_logs_breaks():
    """Get break logs from cerebro.db"""
    try:
        limit = request.args.get('limit', 100, type=int)
        
        # Use get_breaks method from CerebroDB
        breaks_data = unified_db.get_breaks(limit=limit)
        
        return jsonify({
            "status": "success",
            "data": breaks_data,
            "total_entries": len(breaks_data),
            "timestamp": int(time.time())
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/logs/browser', methods=["GET"])
def api_logs_browser():
    """Get browser logs from cerebro.db"""
    try:
        limit = request.args.get('limit', 100, type=int)
        
        # Use get_browser_activity method from CerebroDB
        browser_data = unified_db.get_browser_activity(limit=limit)
        
        return jsonify({
            "status": "success",
            "data": browser_data,
            "total_entries": len(browser_data),
            "timestamp": int(time.time())
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Service control endpoints
@app.route('/api/service/<service_name>/start', methods=["POST"])
def api_start_service(service_name):
    """Start a specific service"""
    try:
        global window_tracker, idle_monitor, input_logger, screen_time_tracker, focus_timer, break_monitor
        
        if service_name == "window_tracker" and window_tracker is None:
            service_config = config.get_service_config('window_tracker')
            window_tracker = WindowTracker(
                log_interval=service_config.get('log_interval', 1.0),
                cerebro_db=unified_db
            )
            window_tracker.start()
            return jsonify({
                "success": True,
                "message": "Window tracker started successfully",
                "service_name": service_name
            })
        
        elif service_name == "idle_monitor" and idle_monitor is None:
            service_config = config.get_service_config('idle_monitor')
            idle_monitor = IdleMonitor(
                timeout_seconds=service_config.get('timeout_seconds', 300),
                check_interval=service_config.get('check_interval', 1.0),
                cerebro_db=unified_db
            )
            idle_monitor.start()
            return jsonify({
                "success": True,
                "message": "Idle monitor started successfully",
                "service_name": service_name
            })
        
        elif service_name == "input_logger" and input_logger is None:
            service_config = config.get_service_config('input_logger')
            input_logger = InputLogger(
                log_interval=service_config.get('log_interval', 60),
                enable_keyboard=service_config.get('enable_keyboard', True),
                enable_mouse=service_config.get('enable_mouse', True),
                cerebro_db=unified_db
            )
            input_logger.start()
            return jsonify({
                "success": True,
                "message": "Input logger started successfully",
                "service_name": service_name
            })
        
        elif service_name == "screen_time_tracker" and screen_time_tracker is None:
            service_config = config.get_service_config('screen_time_tracker')
            screen_time_tracker = ScreenTimeTracker(
                idle_threshold=service_config.get('idle_threshold', 60),
                check_interval=service_config.get('check_interval', 1.0),
                daily_reset_hour=service_config.get('daily_reset_hour', 0),
                cerebro_db=unified_db
            )
            screen_time_tracker.start()
            return jsonify({
                "success": True,
                "message": "Screen time tracker started successfully",
                "service_name": service_name
            })
        
        elif service_name == "focus_timer" and focus_timer is None:
            service_config = config.get_service_config('focus_timer')
            focus_timer = FocusTimer(
                idle_threshold=service_config.get('idle_threshold', 60),
                cerebro_db=unified_db
            )
            return jsonify({
                "success": True,
                "message": "Focus timer initialized successfully",
                "service_name": service_name
            })
        
        elif service_name == "break_monitor" and break_monitor is None:
            service_config = config.get_service_config('break_monitor')
            break_monitor = BreakMonitor(
                min_break_duration=service_config.get('min_break_duration', 120),
                max_break_duration=service_config.get('max_break_duration', 900),
                check_interval=service_config.get('check_interval', 1.0),
                detect_lock_events=service_config.get('detect_lock_events', True),
                cerebro_db=unified_db
            )
            break_monitor.start()
            return jsonify({
                "success": True,
                "message": "Break monitor started successfully",
                "service_name": service_name
            })
        
        else:
            return jsonify({
                "success": False,
                "message": f"Service {service_name} is already running or not found",
                "service_name": service_name
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to start {service_name}: {str(e)}",
            "service_name": service_name
        }), 500

@app.route('/api/service/<service_name>/stop', methods=["POST"])
def api_stop_service(service_name):
    """Stop a specific service"""
    try:
        global window_tracker, idle_monitor, input_logger, screen_time_tracker, focus_timer, break_monitor
        
        if service_name == "window_tracker" and window_tracker is not None:
            window_tracker.stop()
            window_tracker = None
            return jsonify({
                "success": True,
                "message": "Window tracker stopped successfully",
                "service_name": service_name
            })
        
        elif service_name == "idle_monitor" and idle_monitor is not None:
            idle_monitor.stop()
            idle_monitor = None
            return jsonify({
                "success": True,
                "message": "Idle monitor stopped successfully",
                "service_name": service_name
            })
        
        elif service_name == "input_logger" and input_logger is not None:
            input_logger.stop()
            input_logger = None
            return jsonify({
                "success": True,
                "message": "Input logger stopped successfully",
                "service_name": service_name
            })
        
        elif service_name == "screen_time_tracker" and screen_time_tracker is not None:
            screen_time_tracker.stop()
            screen_time_tracker = None
            return jsonify({
                "success": True,
                "message": "Screen time tracker stopped successfully",
                "service_name": service_name
            })
        
        elif service_name == "focus_timer" and focus_timer is not None:
            # Focus timer doesn't have a stop method, just set to None
            focus_timer = None
            return jsonify({
                "success": True,
                "message": "Focus timer stopped successfully",
                "service_name": service_name
            })
        
        elif service_name == "break_monitor" and break_monitor is not None:
            break_monitor.stop()
            break_monitor = None
            return jsonify({
                "success": True,
                "message": "Break monitor stopped successfully",
                "service_name": service_name
            })
        
        else:
            return jsonify({
                "success": False,
                "message": f"Service {service_name} is not running or not found",
                "service_name": service_name
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to stop {service_name}: {str(e)}",
            "service_name": service_name
        }), 500

if __name__ == "__main__":
    threading.Thread(target=collect_app_usage, daemon=True).start()
    threading.Thread(target=collect_idle, daemon=True).start()
    # Additional metric collectors go here as threads (audio, screenshot...)
    
    # Get API configuration
    api_config = config.get_api_config()
    
    # Set up server configuration
    host = api_config.get('host', 'localhost')
    port = api_config.get('port', 5000)
    debug = api_config.get('debug', False)
    
    print(f"Starting server on {host}:{port}...")
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)
