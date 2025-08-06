from flask import Blueprint, request, jsonify
from data.models import store_metric, list_usage, list_idle, list_switches, get_pref, store_pref
from metrics.util import calculate_focus_score, detect_burnout_signals, format_duration
import json
import time

api = Blueprint('api', __name__)

@api.route('/track', methods=['POST'])
def track_extension_data():
    """Receive data from Chrome extension"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Store the raw extension data
        store_metric("browser_ext", json.dumps(data), int(time.time()))
        
        # Extract and store specific metrics
        if 'tabSwitches' in data:
            store_metric("tab_switches", str(data['tabSwitches']), int(time.time()))
        
        if 'erraticClicks' in data and data['erraticClicks']:
            store_metric("erratic_clicks", str(len(data['erraticClicks'])), int(time.time()))
        
        if 'ytLoops' in data and data['ytLoops']:
            store_metric("yt_loops", str(len(data['ytLoops'])), int(time.time()))
        
        if 'siteCategoryStats' in data:
            stats = data['siteCategoryStats']
            store_metric("focus_time", str(stats.get('focus', 0)), int(time.time()))
            store_metric("distraction_time", str(stats.get('distraction', 0)), int(time.time()))
        
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/metrics', methods=['GET'])
def get_metrics():
    """Get all metrics for dashboard"""
    try:
        # Get recent data
        recent_usage = list_usage(limit=50)
        recent_idle = list_idle(limit=50)
        app_switches = list_switches(limit=200)
        
        # Calculate focus score
        focus_score = calculate_focus_score(recent_usage)
        
        # Detect burnout signals
        metrics_data = {
            "app_switches": len(app_switches),
            "recent_usage": len(recent_usage),
            "idle_events": len(recent_idle),
            "focus_score": focus_score
        }
        
        burnout_signals = detect_burnout_signals(metrics_data)
        
        return jsonify({
            "recent_usage": recent_usage,
            "recent_idle": recent_idle,
            "app_switches": app_switches,
            "focus_score": focus_score,
            "burnout_signals": burnout_signals,
            "metrics_summary": metrics_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/analytics', methods=['GET'])
def get_analytics():
    """Get detailed analytics"""
    try:
        # Get time-based data
        usage_data = list_usage(limit=1000)
        idle_data = list_idle(limit=1000)
        
        # Calculate daily stats
        daily_stats = {}
        for usage in usage_data:
            date = time.strftime('%Y-%m-%d', time.localtime(usage[2]))
            if date not in daily_stats:
                daily_stats[date] = {"apps": {}, "total_time": 0}
            
            app = usage[0]
            if app not in daily_stats[date]["apps"]:
                daily_stats[date]["apps"][app] = 0
            daily_stats[date]["apps"][app] += 1
            daily_stats[date]["total_time"] += 1
        
        return jsonify({
            "daily_stats": daily_stats,
            "total_records": len(usage_data),
            "idle_records": len(idle_data)
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

@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": int(time.time()),
        "version": "2.0.0"
    })
