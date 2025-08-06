import time
import json
from datetime import datetime, timedelta

def format_duration(seconds):
    """Format seconds into human readable duration."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m {seconds % 60}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

def get_time_ranges():
    """Get common time ranges for analytics."""
    now = datetime.now()
    return {
        "today": (now.replace(hour=0, minute=0, second=0, microsecond=0), now),
        "yesterday": (
            (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0),
            now.replace(hour=0, minute=0, second=0, microsecond=0)
        ),
        "this_week": (
            (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0),
            now
        )
    }

def calculate_focus_score(usage_data):
    """Calculate a focus score based on usage patterns."""
    if not usage_data:
        return 0
    
    # Simple scoring: more time in focus apps = higher score
    # usage_data is a list of tuples (app, win_title, timestamp)
    # For now, calculate based on number of different apps used
    unique_apps = len(set(entry[0] for entry in usage_data))
    total_entries = len(usage_data)
    
    if total_entries == 0:
        return 0
    
    # Higher score for fewer app switches (more focus)
    focus_score = max(0, 100 - (unique_apps * 10))
    return min(100, focus_score)

def detect_burnout_signals(metrics):
    """Detect potential burnout signals from metrics."""
    signals = []
    
    # High tab switching frequency
    if metrics.get('tab_switches', 0) > 50:  # Threshold
        signals.append("High tab switching frequency")
    
    # Erratic clicking patterns
    if len(metrics.get('erratic_clicks', [])) > 10:
        signals.append("Erratic clicking detected")
    
    # YouTube loops
    if len(metrics.get('yt_loops', [])) > 5:
        signals.append("Video loop behavior detected")
    
    # Rapid navigation
    if metrics.get('rapid_nav_count', 0) > 3:
        signals.append("Rapid navigation patterns")
    
    return signals
