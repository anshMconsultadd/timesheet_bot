import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path


def setup_logging():
    """
    Configure comprehensive logging for the Slack Timesheet Bot.
    Creates separate log files for different components with rotation.
    """
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Define log format
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Console handler (for Docker logs)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)
    root_logger.addHandler(console_handler)
    
    # Main application log file (with rotation)
    main_file_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "app.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    main_file_handler.setLevel(logging.INFO)
    main_file_handler.setFormatter(log_format)
    root_logger.addHandler(main_file_handler)
    
    # Scheduler-specific log file
    scheduler_logger = logging.getLogger('app.utils.scheduler')
    scheduler_file_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "scheduler.log",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    scheduler_file_handler.setLevel(logging.DEBUG)
    scheduler_file_handler.setFormatter(log_format)
    scheduler_logger.addHandler(scheduler_file_handler)
    scheduler_logger.setLevel(logging.DEBUG)
    
    # Slack service log file
    slack_logger = logging.getLogger('app.services.slack_service')
    slack_file_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "slack_service.log",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    slack_file_handler.setLevel(logging.DEBUG)
    slack_file_handler.setFormatter(log_format)
    slack_logger.addHandler(slack_file_handler)
    slack_logger.setLevel(logging.DEBUG)
    
    # Timesheet service log file
    timesheet_logger = logging.getLogger('app.services.timesheet_service')
    timesheet_file_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "timesheet_service.log",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    timesheet_file_handler.setLevel(logging.DEBUG)
    timesheet_file_handler.setFormatter(log_format)
    timesheet_logger.addHandler(timesheet_file_handler)
    timesheet_logger.setLevel(logging.DEBUG)
    
    # Interaction handler log file
    interaction_logger = logging.getLogger('app.handlers.interaction_handler')
    interaction_file_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "interactions.log",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    interaction_file_handler.setLevel(logging.DEBUG)
    interaction_file_handler.setFormatter(log_format)
    interaction_logger.addHandler(interaction_file_handler)
    interaction_logger.setLevel(logging.DEBUG)
    
    # Error-only log file for critical issues
    error_file_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "errors.log",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=5,
        encoding='utf-8'
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(log_format)
    root_logger.addHandler(error_file_handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    
    # Log the setup completion
    logger = logging.getLogger(__name__)
    logger.info("Logging configuration completed")
    logger.info(f"Log files will be saved to: {logs_dir.absolute()}")
    
    return logs_dir


def get_log_files_info():
    """
    Get information about current log files for debugging.
    """
    logs_dir = Path("logs")
    if not logs_dir.exists():
        return {"status": "No logs directory found"}
    
    log_files = {}
    for log_file in logs_dir.glob("*.log"):
        try:
            stat = log_file.stat()
            log_files[log_file.name] = {
                "size_mb": round(stat.st_size / (1024*1024), 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            log_files[log_file.name] = {"error": str(e)}
    
    return log_files


def cleanup_old_logs(days_to_keep=30):
    """
    Clean up log files older than specified days.
    """
    logs_dir = Path("logs")
    if not logs_dir.exists():
        return
    
    import time
    cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
    
    cleaned_files = []
    for log_file in logs_dir.glob("*.log*"):
        try:
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()
                cleaned_files.append(log_file.name)
        except Exception as e:
            logging.getLogger(__name__).warning(f"Failed to clean up {log_file}: {e}")
    
    if cleaned_files:
        logging.getLogger(__name__).info(f"Cleaned up old log files: {cleaned_files}")