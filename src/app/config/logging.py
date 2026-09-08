"""
# Ontology: app.config.logging

Centralized logging configuration for the Ontology application.
"""
# Standard Libraries
import logging.config
import re
from datetime import datetime
from pathlib import Path

# Application Libraries
import app.config.settings as settings

def _get_session_log_filename(log_dir: Path = settings.LOG_DIR) -> str:
    """
    Calculates the next session index for the current date and returns the filename.
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    file_pattern = re.compile(rf"^ontology_{date_str}_(\d+)\.log$")
    
    max_index = 0
    if log_dir.exists():
        for file_path in log_dir.glob(f"ontology_{date_str}_*.log"):
            match = file_pattern.match(file_path.name)
            if match:
                index = int(match.group(1))
                max_index = max(max_index, index)
                
    next_index = max_index + 1
    return f"ontology_{date_str}-{next_index}.log"

def configure_logging(
    log_level: str = settings.LOG_LEVEL, 
    log_dir: Path = settings.LOG_DIR
) -> None:
    """
    Configures the application to write logs to both stdout and a rotating file.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Calculate the dynamic session filename
    log_name = _get_session_log_filename(log_dir)
    filename = str(log_dir / log_name)

    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "console": {
                "format": "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
            },
            "detailed": {
                "format": "%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s",
            },
        },
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "console",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "detailed",
                "filename": filename,
                "maxBytes": 10 * 1024 * 1024,
                "backupCount": 5,
                "encoding": "utf-8",
            },
        },
        "root": {
            "level": log_level, 
            "handlers": ["stdout", "file"],
        },
        "loggers": {
            "jinja2": {
                "level": "WARNING",
                "handlers": ["stdout", "file"],
                "propagate": False
            }
        }
    })