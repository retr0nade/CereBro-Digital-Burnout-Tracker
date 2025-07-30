import sqlite3, os, json
DB_PATH = "data/metrics.db"

def init_db(path=DB_PATH):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = sqlite3.connect(path)
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS app_usage (id INTEGER PRIMARY KEY, app TEXT, win_title TEXT, ts INTEGER)")
    cur.execute("CREATE TABLE IF NOT EXISTS idle_events (id INTEGER PRIMARY KEY, seconds INTEGER, ts INTEGER)")
    cur.execute("CREATE TABLE IF NOT EXISTS metrics (id INTEGER PRIMARY KEY, kind TEXT, value TEXT, ts INTEGER)")
    con.commit()
    con.close()

def store_app_event(app, win_title, ts):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("INSERT INTO app_usage (app, win_title, ts) VALUES (?, ?, ?)", (app, win_title, ts))
    con.commit(); con.close()

def store_idle_event(seconds, ts):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("INSERT INTO idle_events (seconds, ts) VALUES (?, ?)", (seconds, ts))
    con.commit(); con.close()

def store_metric(kind, value, ts):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("INSERT INTO metrics (kind, value, ts) VALUES (?, ?, ?)", (kind, str(value), ts))
    con.commit(); con.close()

def list_usage(limit=50):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT app, win_title, ts FROM app_usage ORDER BY ts DESC LIMIT ?", (limit,))
    r = cur.fetchall(); con.close(); return r

def list_idle(limit=50):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT seconds, ts FROM idle_events ORDER BY ts DESC LIMIT ?", (limit,))
    r = cur.fetchall(); con.close(); return r

def list_switches(limit=200):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT value, ts FROM metrics WHERE kind='app_switch' ORDER BY ts DESC LIMIT ?", (limit,))
    r = cur.fetchall(); con.close(); return r

def store_pref(obj, path="settings.json"):
    with open(path, "w") as f:
        json.dump(obj, f)
def get_pref(path="settings.json"):
    if not os.path.exists(path): return {}
    with open(path, "r") as f: return json.load(f)
