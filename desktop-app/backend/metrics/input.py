import platform
import time
from datetime import datetime, timedelta

class InputMonitor:
    def __init__(self):
        self.key_events = []
        self.mouse_events = []
        self.last_activity = time.time()
        self.is_monitoring = False
        
    def start_monitoring(self):
        """Start monitoring keyboard and mouse input"""
        self.is_monitoring = True
        # Note: Full implementation would require platform-specific libraries
        # For Windows: pynput or keyboard libraries
        # For cross-platform: pynput
        print("Input monitoring started (placeholder)")
        
    def stop_monitoring(self):
        """Stop monitoring input"""
        self.is_monitoring = False
        print("Input monitoring stopped")
        
    def get_typing_speed(self):
        """Calculate typing speed (characters per minute)"""
        if not self.key_events:
            return 0
            
        # Calculate based on recent key events
        recent_events = [e for e in self.key_events if time.time() - e['timestamp'] < 60]
        if len(recent_events) < 2:
            return 0
            
        time_span = recent_events[-1]['timestamp'] - recent_events[0]['timestamp']
        if time_span == 0:
            return 0
            
        return len(recent_events) / (time_span / 60)
        
    def get_mouse_activity(self):
        """Get mouse activity level"""
        if not self.mouse_events:
            return 0
            
        # Count recent mouse events
        recent_events = [e for e in self.mouse_events if time.time() - e['timestamp'] < 60]
        return len(recent_events)
        
    def is_idle(self, threshold_seconds=300):
        """Check if user is idle based on input activity"""
        return time.time() - self.last_activity > threshold_seconds
        
    def get_activity_summary(self):
        """Get summary of recent input activity"""
        return {
            "typing_speed": self.get_typing_speed(),
            "mouse_activity": self.get_mouse_activity(),
            "is_idle": self.is_idle(),
            "last_activity": self.last_activity
        }

# Global instance
input_monitor = InputMonitor()

def get_input_metrics():
    """Get current input metrics"""
    return input_monitor.get_activity_summary()

def start_input_monitoring():
    """Start input monitoring"""
    input_monitor.start_monitoring()

def stop_input_monitoring():
    """Stop input monitoring"""
    input_monitor.stop_monitoring()
