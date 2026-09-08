"""
# Ontology: app.config.logging

Centralized logging configuration for the Ontology application.
"""
# Standard Libraries
import logging.config
from pathlib import Path

# Application Libraries
import app.config.settings as settings

def configure_logging(
    log_level: str = settings.LOG_LEVEL, 
    log_dir: Path = settings.LOG_DIR,
    log_name: str = settings.LOG_FILE
) -> None:
    """
    Configures the application to write logs to both stdout and a rotating file.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
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
                "level": "DEBUG", # Capture deeper diagnostics on disk
                "formatter": "detailed",
                "filename": filename,
                "maxBytes": 10 * 1024 * 1024, # 10 MB per file
                "backupCount": 5,             # Keep 5 rotated backup files
                "encoding": "utf-8",
            },
        },
        "root": {
            "level": "DEBUG", # Root must be lowest level so handlers can filter
            "handlers": ["stdout", "file"],
        },
        "loggers": {
            # Silence noisy third-party libraries here if necessary
            "jinja2": {
                "level": "WARNING",
                "handlers": ["stdout", "file"],
                "propagate": False
            }
        }
    })