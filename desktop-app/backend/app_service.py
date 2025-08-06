import threading, time, sqlite3, json, os, platform
from flask import Flask, request, jsonify
from metrics.apps import get_foreground_app
from metrics.idle import get_idle_seconds
from data.models import init_db, store_app_event, store_idle_event, store_metric, list_usage, list_idle, list_switches, store_pref, get_pref
from api.routes import api

SETTINGS_PATH = "settings.json"

def load_settings():
    if not os.path.exists(SETTINGS_PATH):
        store_pref({
            "track_apps": True,
            "track_idle": True,
            "idle_threshold": 180,
            "track_screenshots": False,
            "track_audio": False
        })
    return get_pref()

def update_pref(new_settings):
    store_pref(new_settings)

settings = load_settings()
app = Flask(__name__)
app.register_blueprint(api, url_prefix='/api')
init_db()

def collect_app_usage():
    last_app = None
    while True:
        settings = load_settings()
        if not settings.get("track_apps"):
            time.sleep(2)
            continue
        app_name, win_title = get_foreground_app()
        ts = int(time.time())
        store_app_event(app_name, win_title, ts)
        if last_app is not None and last_app != app_name:
            store_metric("app_switch", app_name, ts)
        last_app = app_name
        time.sleep(1)

def collect_idle():
    while True:
        settings = load_settings()
        if not settings.get("track_idle"):
            time.sleep(5)
            continue
        idle_sec = get_idle_seconds()
        if idle_sec > settings["idle_threshold"]:
            store_idle_event(idle_sec, int(time.time()))
        time.sleep(15)

@app.route('/api/metrics', methods=["GET"])
def api_metrics():
    # Return all metrics for dashboard
    last_usage = list_usage(limit=50)
    last_idle = list_idle(limit=50)
    switches = list_switches(limit=200)
    return jsonify({
        "recent_usage": last_usage,
        "recent_idle": last_idle,
        "app_switches": switches
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
    data = request.get_json()
    store_metric("browser_ext", json.dumps(data), int(time.time()))
    return {"ok": True}

if __name__ == "__main__":
    threading.Thread(target=collect_app_usage, daemon=True).start()
    threading.Thread(target=collect_idle, daemon=True).start()
    # Additional metric collectors go here as threads (audio, screenshot...)
    app.run(port=5005)
