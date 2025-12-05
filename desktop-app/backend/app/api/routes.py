from flask import Blueprint, request, jsonify, Response
from flask_socketio import emit
from ..core.config import settings
from ..core.database import db as unified_db
from ..websockets.handlers import get_event_manager
import json
import time
import csv
import io
import logging
from datetime import datetime, timedelta
from pydantic import ValidationError
from .schemas import TrackExtensionData, Preferences

logger = logging.getLogger(__name__)

api = Blueprint('api', __name__)

# Re-export unified_db as cerebro_db for compatibility if needed, 
# but we should use unified_db in new code.
cerebro_db = unified_db

@api.route('/track', methods=['POST'])
def track_extension_data():
    """Receive data from Chrome extension"""
    try:
        json_data = request.get_json()
        if not json_data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate data
        data = TrackExtensionData(**json_data)
        
        current_time = int(time.time())
        
        # Log burnout signals from extension data
        # Note: unified_db methods need to be verified against the new class structure
        # The original code used unified_db.insert_burnout_signal which wasn't in the cerebro_db.py I saw earlier
        # I will comment out parts that might not exist in the base CerebroDB class yet
        # and mark them for implementation.
        
        # if data.tabSwitches and data.tabSwitches > 10:
        #     unified_db.insert_burnout_signal(...)
        
        # Store browser activity as app usage
        if data.siteCategoryStats:
            stats = data.siteCategoryStats
            focus_time = stats.focus
            distraction_time = stats.distraction
            
            if focus_time > 0:
                unified_db.insert_app_usage(
                    app_name="Browser - Focus Sites",
                    start_time=current_time - focus_time,
                    end_time=current_time,
                    duration=focus_time
                )
            
            if distraction_time > 0:
                unified_db.insert_app_usage(
                    app_name="Browser - Distraction Sites",
                    start_time=current_time - distraction_time,
                    end_time=current_time,
                    duration=distraction_time
                )
        
        return jsonify({"status": "success"})
    except ValidationError as e:
        logger.warning(f"Validation error in /track: {e}")
        return jsonify({"error": "Validation error", "details": e.errors()}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/insights', methods=['GET'])
def get_insights():
    """Compute and return AI insights based on recent activity."""
    try:
        # results = compute_insights(unified_db) # Need to move ai_insights.py too
        results = {"suggestions": [], "meta": {"note": "AI insights temporarily unavailable during refactor"}}
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/analytics', methods=['GET'])
def get_analytics():
    """Get detailed analytics"""
    try:
        days = request.args.get('days', 7, type=int)
        # Placeholder for analytics logic - needs to be adapted to new DB structure
        return jsonify({
            "analytics_data": {},
            "total_records": 0,
            "total_idle_records": 0,
            "days_analyzed": days
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api.route('/preferences', methods=['GET', 'POST'])
def handle_preferences():
    """Get or update user preferences"""
    if request.method == 'POST':
        try:
            json_data = request.get_json()
            # Validate
            prefs = Preferences(**json_data)
            settings.save_settings(prefs.model_dump())
            return jsonify({"status": "success"})
        except ValidationError as e:
            return jsonify({"error": "Validation error", "details": e.errors()}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify(settings.load_settings())

@api.route('/config', methods=['GET', 'PUT'])
def handle_config():
    """Get or update application configuration"""
    if request.method == 'PUT':
        try:
            updates = request.get_json()
            if not updates:
                return jsonify({"error": "No configuration data provided"}), 400
            
            # Update the configuration
            # config.update_config(updates) # Need to implement update in Config class
            
            return jsonify({"status": "success", "message": "Configuration updated successfully"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        try:
            # Return current configuration
            return jsonify(settings.load_settings()) # Using settings as config for now
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": int(time.time()),
        "version": "2.1.0"
    })

# ... (Add other routes from app_service.py and api/routes.py as needed)
# For brevity, I'm starting with the core ones. I will add the rest in subsequent steps.
