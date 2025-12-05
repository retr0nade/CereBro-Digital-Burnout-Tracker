from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class SiteCategoryStats(BaseModel):
    focus: int = 0
    distraction: int = 0
    neutral: int = 0

class TrackExtensionData(BaseModel):
    tabSwitches: Optional[int] = 0
    erraticClicks: Optional[List[Any]] = []
    ytLoops: Optional[List[Any]] = []
    siteCategoryStats: Optional[SiteCategoryStats] = None

class Preferences(BaseModel):
    track_apps: bool = True
    track_idle: bool = True
    idle_threshold: int = 180
    track_screenshots: bool = False
    track_audio: bool = False
    track_windows: bool = True
    track_idle_detailed: bool = True
    track_input: bool = True
    track_screen_time: bool = True
    track_focus_sessions: bool = True
    track_breaks: bool = True

class FocusSessionStart(BaseModel):
    duration_minutes: int = 25
    notes: Optional[str] = ""

class FocusSessionStop(BaseModel):
    notes: Optional[str] = ""
