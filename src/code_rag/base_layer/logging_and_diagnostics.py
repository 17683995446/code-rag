"""
Logging and Diagnostics - Product-level implementation
Provides structured logging, diagnostics, and performance monitoring
"""
import os
import sys
import logging
import traceback
import time
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum


class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: str
    level: str
    message: str
    logger_name: str
    module: str
    line: int
    extra: Dict[str, Any] = None


class DiagnosticLogger:
    """
    Production-level diagnostic logger
    Provides structured logging, error tracking, and context management
    """
    
    _instances: Dict[str, 'DiagnosticLogger'] = {}
    _root_logger_configured: bool = False
    
    def __new__(cls, name: str = "code_rag", log_dir: Optional[Path] = None):
        """Singleton pattern per logger name"""
        if name not in cls._instances:
            instance = super().__new__(cls)
            instance._initialized = False
            cls._instances[name] = instance
        return cls._instances[name]
    
    def __init__(self, name: str = "code_rag", log_dir: Optional[Path] = None):
        if self._initialized:
            return
        
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.log_dir = log_dir
        self._structured_logs: List[Dict] = []
        
        # Configure logging
        self._configure_logging()
        
        # Prevent duplicate log messages
        if not self.logger.handlers:
            self._add_handlers()
        
        self._initialized = True
    
    def _configure_logging(self):
        """Configure logging format and handlers"""
        # Console handler
        if not DiagnosticLogger._root_logger_configured:
            root_logger = logging.getLogger()
            root_logger.setLevel(logging.INFO)
            
            console_handler = logging.StreamHandler(sys.stdout)
            console_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(console_format)
            root_logger.addHandler(console_handler)
            DiagnosticLogger._root_logger_configured = True
    
    def _add_handlers(self):
        """Add file handlers if log_dir is specified"""
        if self.log_dir:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = self.log_dir / f"{self.name}.log"
            file_handler = logging.FileHandler(str(log_file))
            file_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str, **kwargs):
        """Debug level logging"""
        self.logger.debug(message, extra=kwargs)
        self._record_log("DEBUG", message, kwargs)
    
    def info(self, message: str, **kwargs):
        """Info level logging"""
        self.logger.info(message, extra=kwargs)
        self._record_log("INFO", message, kwargs)
    
    def warning(self, message: str, **kwargs):
        """Warning level logging"""
        self.logger.warning(message, extra=kwargs)
        self._record_log("WARNING", message, kwargs)
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Error level logging with optional exception traceback"""
        if exception:
            tb_str = traceback.format_exc()
            kwargs['exception_type'] = type(exception).__name__
            kwargs['traceback'] = tb_str
            message = f"{message}: {exception}"
        
        self.logger.error(message, extra=kwargs)
        self._record_log("ERROR", message, kwargs)
    
    def critical(self, message: str, **kwargs):
        """Critical level logging"""
        self.logger.critical(message, extra=kwargs)
        self._record_log("CRITICAL", message, kwargs)
    
    def log_exception(self, exception: Exception, context: str = ""):
        """Log an exception with full traceback"""
        if context:
            self.error(f"{context}: {exception}", exception=exception)
        else:
            self.error(str(exception), exception=exception)
    
    def _record_log(self, level: str, message: str, extra: Dict):
        """Record structured log for diagnostics"""
        frame = sys._getframe(2)
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level=level,
            message=message,
            logger_name=self.name,
            module=frame.f_code.co_filename,
            line=frame.f_lineno,
            extra=extra or {}
        )
        self._structured_logs.append(asdict(entry))
        
        # Keep last 1000 logs in memory
        if len(self._structured_logs) > 1000:
            self._structured_logs = self._structured_logs[-1000:]
    
    def get_recent_logs(self, limit: int = 100, level: Optional[str] = None) -> List[Dict]:
        """Get recent structured logs"""
        logs = self._structured_logs[-limit:]
        if level:
            logs = [log for log in logs if log['level'] == level.upper()]
        return logs
    
    def export_logs(self, filepath: Path, format: str = "json"):
        """Export logs to file"""
        if format == "json":
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self._structured_logs, f, indent=2, ensure_ascii=False)
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                for log in self._structured_logs:
                    f.write(f"{log['timestamp']} - {log['level']} - {log['message']}\n")


class LoggingConfiguration:
    """
    Centralized logging configuration
    Manages global logging settings
    """
    
    def __init__(self):
        self.log_level: LogLevel = LogLevel.INFO
        self.log_dir: Optional[Path] = None
        self.max_file_size_mb: int = 10
        self.backup_count: int = 5
        self.structured_logging: bool = True
    
    def set_log_level(self, level: Union[str, LogLevel]):
        """Set global log level"""
        if isinstance(level, str):
            level = LogLevel[level.upper()]
        
        self.log_level = level
        root_logger = logging.getLogger()
        root_logger.setLevel(level.value)
        
        # Set level on all existing loggers
        for logger_name in logging.root.manager.loggerDict:
            logging.getLogger(logger_name).setLevel(level.value)
    
    def set_log_directory(self, dir_path: Union[str, Path]):
        """Set log directory"""
        self.log_dir = Path(dir_path) if dir_path else None
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def get_config(self) -> Dict:
        """Get current configuration"""
        return {
            'log_level': self.log_level.name,
            'log_dir': str(self.log_dir) if self.log_dir else None,
            'max_file_size_mb': self.max_file_size_mb,
            'backup_count': self.backup_count,
            'structured_logging': self.structured_logging
        }


def get_logger(name: str = "code_rag") -> DiagnosticLogger:
    """Get a diagnostic logger instance"""
    return DiagnosticLogger(name)


def get_root_logger() -> DiagnosticLogger:
    """Get the root logger"""
    return DiagnosticLogger("code_rag")


def log_context(context_name: str):
    """Context manager for logging operations"""
    class LogContext:
        def __init__(self, context: str):
            self.context = context
            self.start_time = time.time()
            self.logger = get_logger()
        
        def __enter__(self):
            self.logger.info(f"START: {self.context}")
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            elapsed = time.time() - self.start_time
            if exc_type:
                self.logger.error(f"FAILED: {self.context} (duration: {elapsed:.3f}s)",
                                  exception=exc_val)
            else:
                self.logger.info(f"COMPLETED: {self.context} (duration: {elapsed:.3f}s)")
    
    return LogContext(context_name)


# Simple settings class for graceful degradation
class MockSettings:
    def __init__(self):
        self.log_level = "INFO"
        self.log_dir = None


def get_settings():
    """Get configuration settings with graceful degradation"""
    try:
        from .configuration_and_settings import get_settings as _get_settings
        return _get_settings()
    except Exception:
        return MockSettings()


# Initialize default logger
_default_logger = DiagnosticLogger()

if __name__ == "__main__":
    logger = get_logger()
    logger.info("Test logging")
    logger.debug("Debug message")
    logger.warning("Warning message")
    
    try:
        raise ValueError("Test exception")
    except Exception as e:
        logger.error("An error occurred", exception=e)
    
    print("Recent logs:", len(logger.get_recent_logs()))
