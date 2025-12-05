import logging
import logging.handlers
import os
import sys
from pathlib import Path

def setup_logging(log_dir: str = "logs", log_level: str = "INFO"):
    """
    Setup application logging with rotating file handler and console handler.
    """
    # Create logs directory if it doesn't exist
    base_dir = Path(__file__).resolve().parent.parent.parent
    log_path = base_dir / log_dir
    log_path.mkdir(exist_ok=True)
    
    # Define log format
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers = []
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    root_logger.addHandler(console_handler)
    
    # File Handler (Rotating)
    file_handler = logging.handlers.RotatingFileHandler(
        log_path / "cerebro.log",
        maxBytes=10*1024*1024, # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(log_format)
    root_logger.addHandler(file_handler)
    
    # Set levels for some noisy libraries
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("socketio").setLevel(logging.WARNING)
    logging.getLogger("engineio").setLevel(logging.WARNING)
    
    logging.info(f"Logging initialized. Log file: {log_path / 'cerebro.log'}")

def get_logger(name: str):
    return logging.getLogger(name)
