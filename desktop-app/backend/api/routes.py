from flask import Blueprint, request, jsonify, Response
from flask_socketio import emit
from data.models import get_pref, store_pref
from data.unified_schema import BurnoutTrackerDB, AppUsage, IdlePeriod, InputActivity, FocusSession, BreakLog, BreakType
from metrics.util import calculate_focus_score, detect_burnout_signals, format_duration
from cerebro_db import CerebroDB
from ai_insights import compute_insights
from config_manager import config
import json
import time
import csv
import io
from datetime import datetime, timedelta

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



@api.route('/insights', methods=['GET'])
def get_insights():
    """Compute and return AI insights based on recent activity."""
    try:
        results = compute_insights(unified_db)
        return jsonify(results)
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
            date = datetime.now().date() - timedelta(days=i)
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

@api.route('/export/pdf', methods=['GET'])
def export_pdf():
    """Export data from cerebro.db as PDF with date range filtering"""
    try:
        # Get query parameters
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        tables = request.args.get('tables', 'all')
        
        # Parse dates if provided
        start_timestamp = None
        end_timestamp = None
        
        if start_date:
            start_timestamp = int(datetime.fromisoformat(start_date.replace('Z', '+00:00')).timestamp())
        if end_date:
            end_timestamp = int(datetime.fromisoformat(end_date.replace('Z', '+00:00')).timestamp())
        
        # For now, we'll create a simple text-based PDF
        # In a production environment, you might want to use a proper PDF library like reportlab
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        import io
        
        # Create PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Center
        )
        story.append(Paragraph("CereBro Data Export Report", title_style))
        story.append(Spacer(1, 12))
        
        # Export info
        info_style = styles['Normal']
        story.append(Paragraph(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", info_style))
        if start_date and end_date:
            story.append(Paragraph(f"Date Range: {start_date} to {end_date}", info_style))
        story.append(Spacer(1, 20))
        
        # Add data tables
        if tables == 'all' or 'app_usage' in tables:
            story.append(Paragraph("Application Usage", styles['Heading2']))
            app_usage = cerebro_db.get_app_usage(limit=1000)
            if app_usage:
                data = [['App Name', 'Duration', 'Start Time', 'End Time']]
                for row in app_usage[:20]:  # Limit to first 20 rows for PDF
                    data.append([
                        row['app_name'],
                        f"{row['duration']}s",
                        datetime.fromtimestamp(row['start_time']).strftime('%Y-%m-%d %H:%M'),
                        datetime.fromtimestamp(row['end_time']).strftime('%Y-%m-%d %H:%M')
                    ])
                table = Table(data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(table)
                story.append(Spacer(1, 12))
        
        if tables == 'all' or 'focus_sessions' in tables:
            story.append(Paragraph("Focus Sessions", styles['Heading2']))
            focus_sessions = cerebro_db.get_focus_sessions(limit=1000)
            if focus_sessions:
                data = [['Start Time', 'End Time', 'Duration', 'Interrupted']]
                for row in focus_sessions[:20]:
                    data.append([
                        datetime.fromtimestamp(row['start_time']).strftime('%Y-%m-%d %H:%M'),
                        datetime.fromtimestamp(row['end_time']).strftime('%Y-%m-%d %H:%M'),
                        f"{row['duration']}s",
                        'Yes' if row['was_interrupted'] else 'No'
                    ])
                table = Table(data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(table)
                story.append(Spacer(1, 12))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return Response(
            buffer.getvalue(),
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment; filename=cerebro_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'}
        )
        
    except ImportError:
        # Fallback to CSV if reportlab is not available
        return export_csv()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/export/csv', methods=['GET'])
def export_csv():
    """Export data from cerebro.db as CSV with date range filtering"""
    try:
        # Get query parameters
        format_type = request.args.get('format', 'csv')
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        tables = request.args.get('tables', 'all')
        
        # Parse dates if provided
        start_timestamp = None
        end_timestamp = None
        
        if start_date:
            start_timestamp = int(datetime.fromisoformat(start_date.replace('Z', '+00:00')).timestamp())
        if end_date:
            end_timestamp = int(datetime.fromisoformat(end_date.replace('Z', '+00:00')).timestamp())
        
        # Create CSV data
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Add export metadata
        writer.writerow(['CereBro Data Export'])
        writer.writerow(['Export Date:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        if start_date and end_date:
            writer.writerow(['Date Range:', f'{start_date} to {end_date}'])
        writer.writerow([])
        
        if tables == 'all' or 'app_usage' in tables:
            writer.writerow(['Table: app_usage'])
            writer.writerow(['id', 'app_name', 'start_time', 'end_time', 'duration', 'created_at'])
            app_usage = cerebro_db.get_app_usage(limit=10000)
            for row in app_usage:
                writer.writerow([row['id'], row['app_name'], row['start_time'], row['end_time'], row['duration'], row['created_at']])
            writer.writerow([])
        
        if tables == 'all' or 'idle_periods' in tables:
            writer.writerow(['Table: idle_periods'])
            writer.writerow(['id', 'start_time', 'end_time', 'duration', 'created_at'])
            idle_periods = cerebro_db.get_idle_periods(limit=10000)
            for row in idle_periods:
                writer.writerow([row['id'], row['start_time'], row['end_time'], row['duration'], row['created_at']])
            writer.writerow([])
        
        if tables == 'all' or 'input_activity' in tables:
            writer.writerow(['Table: input_activity'])
            writer.writerow(['id', 'timestamp', 'keypress_count', 'mouse_click_count', 'created_at'])
            input_activity = cerebro_db.get_input_activity(limit=10000)
            for row in input_activity:
                writer.writerow([row['id'], row['timestamp'], row['keypress_count'], row['mouse_click_count'], row['created_at']])
            writer.writerow([])
        
        if tables == 'all' or 'focus_sessions' in tables:
            writer.writerow(['Table: focus_sessions'])
            writer.writerow(['id', 'start_time', 'end_time', 'was_interrupted', 'duration', 'created_at'])
            focus_sessions = cerebro_db.get_focus_sessions(limit=10000)
            for row in focus_sessions:
                writer.writerow([row['id'], row['start_time'], row['end_time'], row['was_interrupted'], row['duration'], row['created_at']])
            writer.writerow([])
        
        if tables == 'all' or 'breaks' in tables:
            writer.writerow(['Table: breaks'])
            writer.writerow(['id', 'start_time', 'end_time', 'type', 'created_at'])
            breaks = cerebro_db.get_breaks(limit=10000)
            for row in breaks:
                writer.writerow([row['id'], row['start_time'], row['end_time'], row['type'], row['created_at']])
            writer.writerow([])
        
        if tables == 'all' or 'browser_activity' in tables:
            writer.writerow(['Table: browser_activity'])
            writer.writerow(['id', 'domain', 'url', 'start_time', 'end_time', 'duration', 'created_at'])
            browser_activity = cerebro_db.get_browser_activity(limit=10000)
            for row in browser_activity:
                writer.writerow([row['id'], row['domain'], row['url'], row['start_time'], row['end_time'], row['duration'], row['created_at']])
            writer.writerow([])
        
        if tables == 'all' or 'system_metrics' in tables:
            writer.writerow(['Table: system_metrics'])
            writer.writerow(['id', 'timestamp', 'cpu_usage', 'ram_usage', 'created_at'])
            system_metrics = cerebro_db.get_system_metrics(limit=10000)
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
    """Export data from cerebro.db as JSON with date range filtering"""
    try:
        # Get query parameters
        format_type = request.args.get('format', 'json')
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        tables = request.args.get('tables', 'all')
        
        # Parse dates if provided
        start_timestamp = None
        end_timestamp = None
        
        if start_date:
            start_timestamp = int(datetime.fromisoformat(start_date.replace('Z', '+00:00')).timestamp())
        if end_date:
            end_timestamp = int(datetime.fromisoformat(end_date.replace('Z', '+00:00')).timestamp())
        
        # Prepare export data
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'database': 'cerebro.db',
            'date_range': {
                'start_date': start_date,
                'end_date': end_date
            } if start_date and end_date else None,
            'tables': {}
        }
        
        if tables == 'all' or 'app_usage' in tables:
            export_data['tables']['app_usage'] = cerebro_db.get_app_usage(limit=10000)
        
        if tables == 'all' or 'idle_periods' in tables:
            export_data['tables']['idle_periods'] = cerebro_db.get_idle_periods(limit=10000)
        
        if tables == 'all' or 'input_activity' in tables:
            export_data['tables']['input_activity'] = cerebro_db.get_input_activity(limit=10000)
        
        if tables == 'all' or 'focus_sessions' in tables:
            export_data['tables']['focus_sessions'] = cerebro_db.get_focus_sessions(limit=10000)
        
        if tables == 'all' or 'breaks' in tables:
            export_data['tables']['breaks'] = cerebro_db.get_breaks(limit=10000)
        
        if tables == 'all' or 'browser_activity' in tables:
            export_data['tables']['browser_activity'] = cerebro_db.get_browser_activity(limit=10000)
        
        if tables == 'all' or 'system_metrics' in tables:
            export_data['tables']['system_metrics'] = cerebro_db.get_system_metrics(limit=10000)
        
        # Create response
        json_data = json.dumps(export_data, indent=2, default=str)
        
        return Response(
            json_data,
            mimetype='application/json',
            headers={'Content-Disposition': f'attachment; filename=cerebro_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'}
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/export/summary', methods=['GET'])
def export_summary():
    """Get export summary data for preview"""
    try:
        # Get query parameters
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        tables = request.args.get('tables', 'all')
        
        # Parse dates if provided
        start_timestamp = None
        end_timestamp = None
        
        if start_date:
            start_timestamp = int(datetime.fromisoformat(start_date.replace('Z', '+00:00')).timestamp())
        if end_date:
            end_timestamp = int(datetime.fromisoformat(end_date.replace('Z', '+00:00')).timestamp())
        
        # Calculate summary data
        total_rows = 0
        table_counts = {}
        
        if tables == 'all' or 'app_usage' in tables:
            app_usage = cerebro_db.get_app_usage(limit=10000)
            table_counts['app_usage'] = len(app_usage)
            total_rows += len(app_usage)
        
        if tables == 'all' or 'idle_periods' in tables:
            idle_periods = cerebro_db.get_idle_periods(limit=10000)
            table_counts['idle_periods'] = len(idle_periods)
            total_rows += len(idle_periods)
        
        if tables == 'all' or 'input_activity' in tables:
            input_activity = cerebro_db.get_input_activity(limit=10000)
            table_counts['input_activity'] = len(input_activity)
            total_rows += len(input_activity)
        
        if tables == 'all' or 'focus_sessions' in tables:
            focus_sessions = cerebro_db.get_focus_sessions(limit=10000)
            table_counts['focus_sessions'] = len(focus_sessions)
            total_rows += len(focus_sessions)
        
        if tables == 'all' or 'breaks' in tables:
            breaks = cerebro_db.get_breaks(limit=10000)
            table_counts['breaks'] = len(breaks)
            total_rows += len(breaks)
        
        if tables == 'all' or 'browser_activity' in tables:
            browser_activity = cerebro_db.get_browser_activity(limit=10000)
            table_counts['browser_activity'] = len(browser_activity)
            total_rows += len(browser_activity)
        
        if tables == 'all' or 'system_metrics' in tables:
            system_metrics = cerebro_db.get_system_metrics(limit=10000)
            table_counts['system_metrics'] = len(system_metrics)
            total_rows += len(system_metrics)
        
        # Estimate file size (rough calculation)
        estimated_size_kb = total_rows * 0.5  # Rough estimate: 0.5KB per row
        
        # Format date range
        date_range = ""
        if start_date and end_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            date_range = f"{start_dt.strftime('%b %d, %Y')} - {end_dt.strftime('%b %d, %Y')}"
        
        return jsonify({
            "status": "success",
            "summary": {
                "rows": total_rows,
                "dateRange": date_range,
                "estimatedSize": f"{estimated_size_kb:.0f} KB",
                "tables": list(table_counts.keys())
            },
            "tableCounts": table_counts
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
