from flask import Blueprint, request, jsonify, Response
from flask_socketio import emit
from data.models import get_pref, store_pref
from data.unified_schema import BurnoutTrackerDB, AppUsage, IdlePeriod, InputActivity, FocusSession, BreakLog, BreakType
from metrics.util import calculate_focus_score, detect_burnout_signals, format_duration
from cerebro_db import CerebroDB
import json
import time
import csv
import io
from datetime import datetime

api = Blueprint('api', __name__)

# Initialize unified database instance
unified_db = BurnoutTrackerDB("data/burnout_tracker.db")
cerebro_db = CerebroDB()

@api.route('/track', methods=['POST'])
def track_extension_data():
    """Receive data from Chrome extension"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        current_time = int(time.time())
        
        # Log burnout signals from extension data
        if 'tabSwitches' in data and data['tabSwitches'] > 10:
            unified_db.insert_burnout_signal(
                signal_type="rapid_tab_switching",
                severity=min(data['tabSwitches'] / 20.0, 1.0),
                description=f"User switched tabs {data['tabSwitches']} times",
                metadata={"tab_switches": data['tabSwitches']}
            )
        
        if 'erraticClicks' in data and data['erraticClicks']:
            unified_db.insert_burnout_signal(
                signal_type="erratic_clicking",
                severity=0.6,
                description=f"Detected {len(data['erraticClicks'])} erratic clicks",
                metadata={"erratic_clicks": len(data['erraticClicks'])}
            )
        
        if 'ytLoops' in data and data['ytLoops']:
            unified_db.insert_burnout_signal(
                signal_type="youtube_binge",
                severity=0.8,
                description=f"Detected {len(data['ytLoops'])} YouTube loops",
                metadata={"yt_loops": len(data['ytLoops'])}
            )
        
        # Store browser activity as app usage
        if 'siteCategoryStats' in data:
            stats = data['siteCategoryStats']
            focus_time = stats.get('focus', 0)
            distraction_time = stats.get('distraction', 0)
            
            if focus_time > 0:
                app_usage = AppUsage(
                    app_name="Browser - Focus Sites",
                    start_time=current_time - focus_time,
                    end_time=current_time,
                    duration=focus_time,
                    category="productive"
                )
                unified_db.insert_app_usage(app_usage)
            
            if distraction_time > 0:
                app_usage = AppUsage(
                    app_name="Browser - Distraction Sites",
                    start_time=current_time - distraction_time,
                    end_time=current_time,
                    duration=distraction_time,
                    category="distraction"
                )
                unified_db.insert_app_usage(app_usage)
        
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/metrics', methods=['GET'])
def get_metrics():
    """Get all metrics for dashboard"""
    try:
        # Get today's data from unified database
        today = datetime.now().strftime("%Y-%m-%d")
        daily_summary = unified_db.get_daily_summary(today)
        recent_activity = unified_db.get_recent_activity(hours=24)
        
        # Get recent app usage, idle periods, and input activity
        recent_usage = recent_activity['app_usage'][:50]
        recent_idle = recent_activity['idle_periods'][:50]
        recent_input = recent_activity['input_activity'][:50]
        
        # Calculate focus score based on recent usage
        focus_score = calculate_focus_score(recent_usage) if recent_usage else 0.0
        
        # Get burnout signals from today
        burnout_signals = list(daily_summary['burnout_signals'].keys())
        
        # Prepare metrics summary
        metrics_data = {
            "app_switches": len([u for u in recent_usage if u[4] != "productive"]),  # Non-productive app switches
            "recent_usage": len(recent_usage),
            "idle_events": len(recent_idle),
            "focus_score": focus_score,
            "total_app_time": daily_summary['total_app_time'],
            "total_idle_time": daily_summary['total_idle_time'],
            "focus_sessions": daily_summary['focus_sessions']
        }
        
        return jsonify({
            "recent_usage": recent_usage,
            "recent_idle": recent_idle,
            "recent_input": recent_input,
            "focus_score": focus_score,
            "burnout_signals": burnout_signals,
            "metrics_summary": metrics_data,
            "daily_summary": daily_summary
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/analytics', methods=['GET'])
def get_analytics():
    """Get detailed analytics"""
    try:
        # Get date range from query parameters
        days = request.args.get('days', 7, type=int)
        
        # Get analytics for the specified number of days
        analytics_data = {}
        total_records = 0
        total_idle_records = 0
        
        for i in range(days):
            date = datetime.now().date() - datetime.timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            
            # Get daily summary
            daily_summary = unified_db.get_daily_summary(date_str)
            
            # Get app usage for the day
            app_usage = unified_db.get_app_usage_by_date(date_str, limit=1000)
            
            # Calculate app usage stats
            app_stats = {}
            for usage in app_usage:
                app_name, start_time, end_time, duration, window_title, category = usage
                if app_name not in app_stats:
                    app_stats[app_name] = {"total_time": 0, "sessions": 0, "category": category}
                app_stats[app_name]["total_time"] += duration
                app_stats[app_name]["sessions"] += 1
            
            analytics_data[date_str] = {
                "daily_summary": daily_summary,
                "app_stats": app_stats,
                "total_app_time": daily_summary['total_app_time'],
                "total_idle_time": daily_summary['total_idle_time'],
                "focus_sessions": daily_summary['focus_sessions'],
                "breaks": daily_summary['breaks'],
                "burnout_signals": daily_summary['burnout_signals']
            }
            
            total_records += len(app_usage)
            total_idle_records += len(unified_db.get_idle_periods_by_date(date_str, limit=1000))
        
        return jsonify({
            "analytics_data": analytics_data,
            "total_records": total_records,
            "total_idle_records": total_idle_records,
            "days_analyzed": days
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/preferences', methods=['GET', 'POST'])
def handle_preferences():
    """Get or update user preferences"""
    if request.method == 'POST':
        try:
            new_prefs = request.get_json()
            store_pref(new_prefs)
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify(get_pref())

@api.route('/config', methods=['GET', 'PUT'])
def handle_config():
    """Get or update application configuration"""
    if request.method == 'PUT':
        try:
            updates = request.get_json()
            if not updates:
                return jsonify({"error": "No configuration data provided"}), 400
            
            # Update the configuration
            config.update_config(updates)
            
            return jsonify({"status": "success", "message": "Configuration updated successfully"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        try:
            # Return current configuration
            return jsonify(config.config)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": int(time.time()),
        "version": "2.0.0"
    })

@api.route('/unified/summary', methods=['GET'])
def get_unified_summary():
    """Get unified database summary"""
    try:
        date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        summary = unified_db.get_daily_summary(date)
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/unified/recent', methods=['GET'])
def get_unified_recent():
    """Get recent activity from unified database"""
    try:
        hours = request.args.get('hours', 24, type=int)
        recent = unified_db.get_recent_activity(hours=hours)
        return jsonify(recent)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/unified/app-usage', methods=['GET'])
def get_app_usage():
    """Get app usage data"""
    try:
        date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        limit = request.args.get('limit', 100, type=int)
        app_usage = unified_db.get_app_usage_by_date(date, limit=limit)
        return jsonify({"app_usage": app_usage})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/unified/focus-sessions', methods=['GET'])
def get_focus_sessions():
    """Get focus sessions data"""
    try:
        date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        limit = request.args.get('limit', 50, type=int)
        focus_sessions = unified_db.get_focus_sessions_by_date(date, limit=limit)
        return jsonify({"focus_sessions": focus_sessions})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/unified/break-logs', methods=['GET'])
def get_break_logs():
    """Get break logs data"""
    try:
        date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        limit = request.args.get('limit', 50, type=int)
        break_logs = unified_db.get_break_logs_by_date(date, limit=limit)
        return jsonify({"break_logs": break_logs})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/unified/log-app-usage', methods=['POST'])
def log_app_usage():
    """Log app usage to unified database"""
    try:
        data = request.get_json()
        app_usage = AppUsage(
            app_name=data['app_name'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            duration=data['duration'],
            window_title=data.get('window_title'),
            category=data.get('category')
        )
        result = unified_db.insert_app_usage(app_usage)
        return jsonify({"status": "success", "id": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/unified/log-idle-period', methods=['POST'])
def log_idle_period():
    """Log idle period to unified database"""
    try:
        data = request.get_json()
        idle_period = IdlePeriod(
            start_time=data['start_time'],
            end_time=data['end_time'],
            duration=data['duration'],
            reason=data.get('reason', 'system_idle')
        )
        result = unified_db.insert_idle_period(idle_period)
        return jsonify({"status": "success", "id": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/unified/log-input-activity', methods=['POST'])
def log_input_activity():
    """Log input activity to unified database"""
    try:
        data = request.get_json()
        input_activity = InputActivity(
            timestamp=data['timestamp'],
            keypress_count=data.get('keypress_count', 0),
            mouse_click_count=data.get('mouse_click_count', 0),
            scroll_events=data.get('scroll_events', 0),
            mouse_movement=data.get('mouse_movement', 0)
        )
        result = unified_db.insert_input_activity(input_activity)
        return jsonify({"status": "success", "id": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/unified/log-focus-session', methods=['POST'])
def log_focus_session():
    """Log focus session to unified database"""
    try:
        data = request.get_json()
        focus_session = FocusSession(
            session_id=data['session_id'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            was_interrupted=data.get('was_interrupted', False),
            focus_score=data.get('focus_score'),
            notes=data.get('notes')
        )
        result = unified_db.insert_focus_session(focus_session)
        return jsonify({"status": "success", "id": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/unified/log-break', methods=['POST'])
def log_break():
    """Log break to unified database"""
    try:
        data = request.get_json()
        break_log = BreakLog(
            start_time=data['start_time'],
            end_time=data['end_time'],
            break_type=BreakType(data['break_type']),
            duration=data['duration'],
            was_productive=data.get('was_productive', True),
            notes=data.get('notes')
        )
        result = unified_db.insert_break_log(break_log)
        return jsonify({"status": "success", "id": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/unified/log-burnout-signal', methods=['POST'])
def log_burnout_signal():
    """Log burnout signal to unified database"""
    try:
        data = request.get_json()
        result = unified_db.insert_burnout_signal(
            signal_type=data['signal_type'],
            severity=data.get('severity', 1.0),
            description=data.get('description'),
            metadata=data.get('metadata')
        )
        return jsonify({"status": "success", "id": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/websocket/status', methods=['GET'])
def websocket_status():
    """Get WebSocket connection status"""
    try:
        from websocket_events import get_event_manager
        event_manager = get_event_manager()
        if event_manager:
            return jsonify({
                "status": "available",
                "connected_clients": len(event_manager.clients),
                "events": [
                    "app_usage_update",
                    "idle_status", 
                    "input_activity",
                    "focus_session_update",
                    "break_update"
                ]
            })
        else:
            return jsonify({"status": "unavailable"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/export/csv', methods=['GET'])
def export_csv():
    """Export all data from cerebro.db as CSV"""
    try:
        # Get query parameters
        table = request.args.get('table', 'all')
        limit = request.args.get('limit', 1000, type=int)
        
        # Create CSV data
        output = io.StringIO()
        writer = csv.writer(output)
        
        if table == 'all' or table == 'app_usage':
            writer.writerow(['Table: app_usage'])
            writer.writerow(['id', 'app_name', 'start_time', 'end_time', 'duration', 'created_at'])
            app_usage = cerebro_db.get_app_usage(limit=limit)
            for row in app_usage:
                writer.writerow([row['id'], row['app_name'], row['start_time'], row['end_time'], row['duration'], row['created_at']])
            writer.writerow([])
        
        if table == 'all' or table == 'idle_periods':
            writer.writerow(['Table: idle_periods'])
            writer.writerow(['id', 'start_time', 'end_time', 'duration', 'created_at'])
            idle_periods = cerebro_db.get_idle_periods(limit=limit)
            for row in idle_periods:
                writer.writerow([row['id'], row['start_time'], row['end_time'], row['duration'], row['created_at']])
            writer.writerow([])
        
        if table == 'all' or table == 'input_activity':
            writer.writerow(['Table: input_activity'])
            writer.writerow(['id', 'timestamp', 'keypress_count', 'mouse_click_count', 'created_at'])
            input_activity = cerebro_db.get_input_activity(limit=limit)
            for row in input_activity:
                writer.writerow([row['id'], row['timestamp'], row['keypress_count'], row['mouse_click_count'], row['created_at']])
            writer.writerow([])
        
        if table == 'all' or table == 'focus_sessions':
            writer.writerow(['Table: focus_sessions'])
            writer.writerow(['id', 'start_time', 'end_time', 'was_interrupted', 'duration', 'created_at'])
            focus_sessions = cerebro_db.get_focus_sessions(limit=limit)
            for row in focus_sessions:
                writer.writerow([row['id'], row['start_time'], row['end_time'], row['was_interrupted'], row['duration'], row['created_at']])
            writer.writerow([])
        
        if table == 'all' or table == 'breaks':
            writer.writerow(['Table: breaks'])
            writer.writerow(['id', 'start_time', 'end_time', 'type', 'created_at'])
            breaks = cerebro_db.get_breaks(limit=limit)
            for row in breaks:
                writer.writerow([row['id'], row['start_time'], row['end_time'], row['type'], row['created_at']])
            writer.writerow([])
        
        if table == 'all' or table == 'browser_activity':
            writer.writerow(['Table: browser_activity'])
            writer.writerow(['id', 'domain', 'url', 'start_time', 'end_time', 'duration', 'created_at'])
            browser_activity = cerebro_db.get_browser_activity(limit=limit)
            for row in browser_activity:
                writer.writerow([row['id'], row['domain'], row['url'], row['start_time'], row['end_time'], row['duration'], row['created_at']])
            writer.writerow([])
        
        if table == 'all' or table == 'system_metrics':
            writer.writerow(['Table: system_metrics'])
            writer.writerow(['id', 'timestamp', 'cpu_usage', 'ram_usage', 'created_at'])
            system_metrics = cerebro_db.get_system_metrics(limit=limit)
            for row in system_metrics:
                writer.writerow([row['id'], row['timestamp'], row['cpu_usage'], row['ram_usage'], row['created_at']])
            writer.writerow([])
        
        # Create response
        output.seek(0)
        csv_data = output.getvalue()
        
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=cerebro_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/export/json', methods=['GET'])
def export_json():
    """Export all data from cerebro.db as JSON"""
    try:
        # Get query parameters
        table = request.args.get('table', 'all')
        limit = request.args.get('limit', 1000, type=int)
        
        # Prepare export data
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'database': 'cerebro.db',
            'tables': {}
        }
        
        if table == 'all' or table == 'app_usage':
            export_data['tables']['app_usage'] = cerebro_db.get_app_usage(limit=limit)
        
        if table == 'all' or table == 'idle_periods':
            export_data['tables']['idle_periods'] = cerebro_db.get_idle_periods(limit=limit)
        
        if table == 'all' or table == 'input_activity':
            export_data['tables']['input_activity'] = cerebro_db.get_input_activity(limit=limit)
        
        if table == 'all' or table == 'focus_sessions':
            export_data['tables']['focus_sessions'] = cerebro_db.get_focus_sessions(limit=limit)
        
        if table == 'all' or table == 'breaks':
            export_data['tables']['breaks'] = cerebro_db.get_breaks(limit=limit)
        
        if table == 'all' or table == 'browser_activity':
            export_data['tables']['browser_activity'] = cerebro_db.get_browser_activity(limit=limit)
        
        if table == 'all' or table == 'system_metrics':
            export_data['tables']['system_metrics'] = cerebro_db.get_system_metrics(limit=limit)
        
        # Create response
        json_data = json.dumps(export_data, indent=2, default=str)
        
        return Response(
            json_data,
            mimetype='application/json',
            headers={'Content-Disposition': f'attachment; filename=cerebro_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'}
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
