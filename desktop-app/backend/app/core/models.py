from sqlalchemy import Column, Integer, String, Boolean, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from .config import settings

Base = declarative_base()

class AppUsage(Base):
    __tablename__ = 'app_usage'
    id = Column(Integer, primary_key=True, autoincrement=True)
    app_name = Column(String, nullable=False, index=True)
    start_time = Column(Integer, nullable=False, index=True)
    end_time = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=False)
    created_at = Column(Integer, nullable=True) # Default handled by DB

class IdlePeriod(Base):
    __tablename__ = 'idle_periods'
    id = Column(Integer, primary_key=True, autoincrement=True)
    start_time = Column(Integer, nullable=False, index=True)
    end_time = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=False)
    created_at = Column(Integer, nullable=True)

class InputActivity(Base):
    __tablename__ = 'input_activity'
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(Integer, nullable=False, index=True)
    keypress_count = Column(Integer, default=0)
    mouse_click_count = Column(Integer, default=0)
    created_at = Column(Integer, nullable=True)

class FocusSession(Base):
    __tablename__ = 'focus_sessions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    start_time = Column(Integer, nullable=False, index=True)
    end_time = Column(Integer, nullable=False)
    was_interrupted = Column(Boolean, default=False)
    duration = Column(Integer, nullable=False)
    created_at = Column(Integer, nullable=True)

class Break(Base):
    __tablename__ = 'breaks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    start_time = Column(Integer, nullable=False, index=True)
    end_time = Column(Integer, nullable=False)
    type = Column(String, nullable=False)
    created_at = Column(Integer, nullable=True)

class BrowserActivity(Base):
    __tablename__ = 'browser_activity'
    id = Column(Integer, primary_key=True, autoincrement=True)
    domain = Column(String, nullable=False, index=True)
    url = Column(String, nullable=False)
    start_time = Column(Integer, nullable=False, index=True)
    end_time = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=False)
    created_at = Column(Integer, nullable=True)

class SystemMetrics(Base):
    __tablename__ = 'system_metrics'
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(Integer, nullable=False)
    cpu_usage = Column(Float, nullable=False)
    ram_usage = Column(Float, nullable=False)
    created_at = Column(Integer, nullable=True)
