import sqlite3
import json
import time
from typing import Any, Dict, List, Optional

from data.unified_schema import BurnoutTrackerDB


def _safe_count(cursor: sqlite3.Cursor, query: str, params: tuple) -> int:
    try:
        cursor.execute(query, params)
        row = cursor.fetchone()
        return int(row[0]) if row and row[0] is not None else 0
    except sqlite3.OperationalError:
        return 0


def compute_insights(db: Optional[BurnoutTrackerDB] = None) -> Dict[str, Any]:
    """
    Compute AI insights based on recent activity.

    Rules implemented:
    - If continuous screen time > 4 hours → Suggest break
    - If frequent tab switching (>10 in 10 min) → Suggest focus reset
    - If no breaks > 2 hours → Suggest pause
    - If input activity drops sharply → Suggest fatigue warning
    """

    unified_db = db or BurnoutTrackerDB("data/burnout_tracker.db")
    now_ts = int(time.time())

    suggestions: List[Dict[str, Any]] = []
    meta: Dict[str, Any] = {}

    with sqlite3.connect(unified_db.db_path) as conn:
        cursor = conn.cursor()

        # 1) Continuous screen time > 4 hours → Suggest break
        four_hours_ago = now_ts - 4 * 3600

        idle_events_4h = _safe_count(
            cursor,
            "SELECT COUNT(*) FROM idle_periods WHERE start_time >= ?",
            (four_hours_ago,),
        )

        breaks_4h = _safe_count(
            cursor,
            "SELECT COUNT(*) FROM break_logs WHERE start_time >= ?",
            (four_hours_ago,),
        )

        cursor.execute(
            "SELECT COALESCE(SUM(duration), 0) FROM app_usage WHERE start_time >= ?",
            (four_hours_ago,),
        )
        active_seconds_4h = int(cursor.fetchone()[0] or 0)

        meta["continuous_screen_time"] = {
            "active_seconds_last_4h": active_seconds_4h,
            "idle_events_last_4h": idle_events_4h,
            "breaks_last_4h": breaks_4h,
        }

        if active_seconds_4h >= 4 * 3600 and idle_events_4h == 0 and breaks_4h == 0:
            suggestions.append(
                {
                    "id": "suggest_break",
                    "type": "break",
                    "severity": "warning",
                    "message": "You've been on screen continuously for over 4 hours. Take a short break.",
                    "rule": "continuous_screen_time_gt_4h",
                    "timestamp": now_ts,
                }
            )

        # 2) Frequent tab switching (>10 in 10 min) → Suggest focus reset
        ten_min_ago = now_ts - 600
        rapid_switch_detected = False
        rapid_switch_samples = 0
        try:
            cursor.execute(
                """
                SELECT timestamp, severity, metadata
                FROM burnout_signals
                WHERE signal_type = ? AND timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT 50
                """,
                ("rapid_tab_switching", ten_min_ago),
            )
            rows = cursor.fetchall()
            rapid_switch_samples = len(rows)
            for ts, severity, metadata in rows:
                md = {}
                try:
                    md = json.loads(metadata) if metadata else {}
                except Exception:
                    md = {}
                tab_switches = int(md.get("tab_switches", 0))
                if tab_switches > 10:
                    rapid_switch_detected = True
                    break
                # Fallback: infer from severity (server sets severity ~ tabSwitches/20)
                if severity is not None and float(severity) >= 0.5:
                    rapid_switch_detected = True
                    break
        except sqlite3.OperationalError:
            rows = []

        meta["rapid_tab_switch_signals_last_10m"] = rapid_switch_samples
        if rapid_switch_detected:
            suggestions.append(
                {
                    "id": "suggest_focus_reset",
                    "type": "focus_reset",
                    "severity": "info",
                    "message": "High tab switching detected. Consider a quick focus reset.",
                    "rule": "tab_switches_gt_10_in_10m",
                    "timestamp": now_ts,
                }
            )

        # 3) No breaks > 2 hours → Suggest pause
        two_hours_ago = now_ts - 2 * 3600
        breaks_2h = _safe_count(
            cursor,
            "SELECT COUNT(*) FROM break_logs WHERE start_time >= ?",
            (two_hours_ago,),
        )
        # Treat idle periods >= 5 minutes as meaningful breaks
        idle_breaks_2h = _safe_count(
            cursor,
            "SELECT COUNT(*) FROM idle_periods WHERE start_time >= ? AND duration >= ?",
            (two_hours_ago, 300),
        )
        meta["breaks_last_2h"] = {
            "break_logs": breaks_2h,
            "idle_periods_ge5m": idle_breaks_2h,
        }
        if breaks_2h == 0 and idle_breaks_2h == 0:
            suggestions.append(
                {
                    "id": "suggest_pause",
                    "type": "pause",
                    "severity": "warning",
                    "message": "No meaningful breaks in the last 2 hours. Pause to recharge.",
                    "rule": "no_breaks_gt_2h",
                    "timestamp": now_ts,
                }
            )

        # 4) Input activity drops sharply → Suggest fatigue warning
        # Compare last 10 minutes vs previous 10 minutes
        try:
            cursor.execute(
                """
                SELECT timestamp, COALESCE(keypress_count,0), COALESCE(mouse_click_count,0), COALESCE(scroll_events,0)
                FROM input_activity
                WHERE timestamp >= ?
                ORDER BY timestamp ASC
                """,
                (now_ts - 1200,),
            )
            input_rows = cursor.fetchall()
        except sqlite3.OperationalError:
            input_rows = []

        def _sum_inputs(rows: List[tuple], start_ts: int, end_ts: int) -> int:
            total = 0
            for ts, kc, mc, sc in rows:
                if start_ts <= int(ts) < end_ts:
                    total += int(kc or 0) + int(mc or 0) + int(sc or 0)
            return total

        prev_10m_total = _sum_inputs(input_rows, now_ts - 1200, now_ts - 600)
        last_10m_total = _sum_inputs(input_rows, now_ts - 600, now_ts)
        meta["input_activity"] = {
            "prev_10m": prev_10m_total,
            "last_10m": last_10m_total,
        }

        if prev_10m_total >= 50 and last_10m_total <= int(0.3 * prev_10m_total):
            suggestions.append(
                {
                    "id": "fatigue_warning",
                    "type": "fatigue_warning",
                    "severity": "warning",
                    "message": "Input activity dropped sharply. You might be fatigued.",
                    "rule": "input_activity_drop",
                    "timestamp": now_ts,
                }
            )

    return {
        "suggestions": suggestions,
        "meta": meta,
        "generated_at": now_ts,
    }


