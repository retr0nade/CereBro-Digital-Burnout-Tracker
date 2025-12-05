import sys
import os

# Add the current directory to sys.path so we can import 'app'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app, socketio
from app.core.config import settings
from app.core.database import db

# Import monitors (we still need to initialize them)
# TODO: Move monitor initialization to app/services/monitor_manager.py
# For now, we will initialize them here to keep the app working during refactor

from window_tracker import WindowTracker
from idle_monitor import IdleMonitor
from input_logger import InputLogger
from screen_time_tracker import ScreenTimeTracker
from focus_timer import FocusTimer
from break_monitor import BreakMonitor

def init_services():
    print("Initializing services...")
    
    # Initialize window tracker
    if settings.load_settings().get("track_windows", True):
        try:
            service_config = settings.get_service_config('window_tracker')
            # Note: WindowTracker expects the old CerebroDB instance, but our new one is compatible-ish
            # We might need to adjust WindowTracker to accept the new db instance or keep using the old import for now
            # To avoid breaking changes immediately, let's instantiate the monitors with the new db
            # This assumes the monitors accept a 'cerebro_db' argument which matches the interface
            
            window_tracker = WindowTracker(
                log_interval=service_config.get('log_interval', 1.0),
                cerebro_db=db
            )
            window_tracker.start()
            print("Window tracker started successfully")
        except Exception as e:
            print(f"Failed to start window tracker: {e}")

    # Initialize idle monitor
    if settings.load_settings().get("track_idle_detailed", True):
        try:
            service_config = settings.get_service_config('idle_monitor')
            idle_monitor = IdleMonitor(
                timeout_seconds=service_config.get('timeout_seconds', 300),
                check_interval=service_config.get('check_interval', 1.0),
                cerebro_db=db
            )
            idle_monitor.start()
            print("Idle monitor started successfully")
        except Exception as e:
            print(f"Failed to start idle monitor: {e}")

    # Initialize input logger
    if settings.load_settings().get("track_input", True):
        try:
            service_config = settings.get_service_config('input_logger')
            input_logger = InputLogger(
                log_interval=service_config.get('log_interval', 60),
                enable_keyboard=service_config.get('enable_keyboard', True),
                enable_mouse=service_config.get('enable_mouse', True),
                cerebro_db=db
            )
            input_logger.start()
            print("Input logger started successfully")
        except Exception as e:
            print(f"Failed to start input logger: {e}")

    # Initialize screen time tracker
    if settings.load_settings().get("track_screen_time", True):
        try:
            service_config = settings.get_service_config('screen_time_tracker')
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
    if settings.load_settings().get("track_focus_sessions", True):
        try:
            service_config = settings.get_service_config('focus_timer')
            focus_timer = FocusTimer(
                idle_threshold=service_config.get('idle_threshold', 60),
                cerebro_db=db
            )
            print("Focus timer initialized successfully")
        except Exception as e:
            print(f"Failed to initialize focus timer: {e}")

    # Initialize break monitor
    if settings.load_settings().get("track_breaks", True):
        try:
            service_config = settings.get_service_config('break_monitor')
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

from app.main import app, socketio, find_free_port, write_port_file
from app.core.config import settings
from app.core.database import db

# ... (imports)

if __name__ == "__main__":
    print("Starting CereBro Backend (Legacy Shim)...")
    init_services()
    port = find_free_port()
    write_port_file(port)
    print(f"Selected port: {port}")
    socketio.run(app, host='127.0.0.1', port=port, allow_unsafe_werkzeug=True)
