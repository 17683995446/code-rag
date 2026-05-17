"""
Base Layer - Foundation and Infrastructure Modules
Provides core logging, configuration, security, and monitoring
"""

# Use try-except imports for graceful degradation
try:
    from .logging_and_diagnostics import (
        get_logger,
        get_root_logger,
        log_context,
        DiagnosticLogger,
        LoggingConfiguration
    )
    
    # Create fallbacks for missing functions
    def setup_logging(*args, **kwargs):
        print("Warning: setup_logging not fully implemented")
        return True
        
    def create_operation_logger(*args, **kwargs):
        return get_logger(*args, **kwargs) if 'get_logger' in globals() else None
        
    def log_performance_metrics(*args, **kwargs):
        if 'get_logger' in globals():
            get_logger().info("Performance metrics (fallback)")
        
    def log_system_health(*args, **kwargs):
        if 'get_logger' in globals():
            get_logger().info("System health (fallback)")
            
except Exception as e:
    print(f"Warning: Logging module not fully available: {e}")
    
    # Fallback implementations
    import logging
    
    def get_logger(name="code_rag"):
        return logging.getLogger(name)
    
    def get_root_logger():
        return logging.getLogger()
    
    def log_context(name):
        class DummyContext:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        return DummyContext()
    
    class DiagnosticLogger:
        def __init__(self, name="code_rag"):
            self.logger = logging.getLogger(name)
        def info(self, msg):
            self.logger.info(msg)
        def error(self, msg):
            self.logger.error(msg)
        def warning(self, msg):
            self.logger.warning(msg)
    
    class LoggingConfiguration:
        def __init__(self):
            pass
    
    def setup_logging(*args, **kwargs):
        return True
        
    def create_operation_logger(*args, **kwargs):
        return None
        
    def log_performance_metrics(*args, **kwargs):
        pass
        
    def log_system_health(*args, **kwargs):
        pass

try:
    from .configuration_and_settings import (
        CodeRAGSettings,
        get_settings,
        ConfigLoader,
        ConfigManager,
        get_config_manager
    )
    
    # Create compatibility aliases
    RAGSettings = CodeRAGSettings
    
    def set_settings(settings):
        pass
        
    def init_config(*args, **kwargs):
        return get_settings()
        
    def get_config():
        return get_settings().to_dict()
        
    def set_config(config_dict):
        pass
        
    # Settings class aliases
    class EmbeddingSettings:
        pass
    class VectorDBSettings:
        pass
    class LLMSettings:
        pass
    class StorageSettings:
        pass
    class LoggingSettings:
        pass
    class APISettings:
        pass
        
except Exception as e:
    print(f"Warning: Configuration module not fully available: {e}")
    
    # Fallback implementations
    class CodeRAGSettings:
        def to_dict(self):
            return {}
        def get(self, key, default=None):
            return default
        def set(self, key, value):
            pass
    
    def get_settings():
        return CodeRAGSettings()
    
    def ConfigLoader():
        class DummyLoader:
            def get_config(self):
                return get_settings()
        return DummyLoader()
    
    def ConfigManager():
        class DummyManager:
            pass
        return DummyManager()
    
    def get_config_manager():
        return None
        
    RAGSettings = CodeRAGSettings
    def set_settings(settings):
        pass
    def init_config(*args, **kwargs):
        return get_settings()
    def get_config():
        return {}
    def set_config(config_dict):
        pass
    class EmbeddingSettings:
        pass
    class VectorDBSettings:
        pass
    class LLMSettings:
        pass
    class StorageSettings:
        pass
    class LoggingSettings:
        pass
    class APISettings:
        pass

try:
    from .security_and_access_control import (
        RateLimiter,
        InputValidator,
        SecurityManager,
        get_security_manager
    )
    
    def rate_limit(*args, **kwargs):
        return True
        
    def security_context(*args, **kwargs):
        class DummyContext:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        return DummyContext()
        
except Exception as e:
    print(f"Warning: Security module not fully available: {e}")
    
    # Fallback implementations
    class RateLimiter:
        def __init__(self, max_requests=100, window_seconds=60):
            self.max_requests = max_requests
            self.window_seconds = window_seconds
        def is_allowed(self, key):
            return True
    
    class InputValidator:
        def validate_query(self, text):
            return text and len(text.strip()) > 0
        def sanitize(self, text):
            return text or ""
    
    class SecurityManager:
        pass
    
    def get_security_manager():
        return SecurityManager()
        
    def rate_limit(*args, **kwargs):
        return True
        
    def security_context(*args, **kwargs):
        class DummyContext:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        return DummyContext()

try:
    from .performance_monitoring import (
        MetricsCollector,
        PerformanceMonitor,
        get_monitor
    )
    
    def monitor(*args, **kwargs):
        class DummyContext:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        return DummyContext()
        
except Exception as e:
    print(f"Warning: Monitoring module not fully available: {e}")
    
    # Fallback implementations
    class MetricsCollector:
        def __init__(self):
            self.metrics = {}
        def record(self, key, value):
            pass
    
    class PerformanceMonitor:
        pass
    
    def get_monitor():
        return PerformanceMonitor()
        
    def monitor(*args, **kwargs):
        class DummyContext:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        return DummyContext()

__all__ = [
    "get_logger",
    "get_root_logger",
    "setup_logging",
    "log_context",
    "DiagnosticLogger",
    "LoggingConfiguration",
    "create_operation_logger",
    "log_performance_metrics",
    "log_system_health",
    "RAGSettings",
    "get_settings",
    "set_settings",
    "EmbeddingSettings",
    "VectorDBSettings",
    "LLMSettings",
    "StorageSettings",
    "LoggingSettings",
    "APISettings",
    "ConfigLoader",
    "ConfigManager",
    "get_config_manager",
    "init_config",
    "get_config",
    "set_config",
    "RateLimiter",
    "InputValidator",
    "SecurityManager",
    "get_security_manager",
    "rate_limit",
    "security_context",
    "MetricsCollector",
    "PerformanceMonitor",
    "get_monitor",
    "monitor"
]
