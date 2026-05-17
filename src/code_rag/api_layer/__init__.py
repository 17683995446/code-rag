"""
API Layer - REST and CLI Interfaces
Provides REST API endpoints, CLI tools, and service interfaces
"""

# 尝试导入API模块，优雅降级
try:
    from .rest_api_endpoints import (
        QueryRequest,
        QueryResponse,
        DocumentAddRequest,
        DocumentAddResponse,
        HealthResponse,
        StatsResponse,
        create_rest_api_app,
        run_rest_api
    )
    REST_API_AVAILABLE = True
except Exception as e:
    print(f"Warning: REST API endpoints not available: {e}")
    REST_API_AVAILABLE = False
    # 提供备用定义
    QueryRequest = None
    QueryResponse = None
    DocumentAddRequest = None
    DocumentAddResponse = None
    HealthResponse = None
    StatsResponse = None
    def create_rest_api_app(): return None
    def run_rest_api(): pass

try:
    from .error_handlers import (
        APIError,
        ValidationError,
        NotFoundError,
        UnauthorizedError,
        RateLimitError,
        InternalServerError,
        SearchRequestValidator,
        DocumentAddRequestValidator,
        QueryRequestValidator,
        sanitize_input,
        validate_file_path
    )
    ERROR_HANDLERS_AVAILABLE = True
except Exception as e:
    print(f"Warning: Error handlers not available: {e}")
    ERROR_HANDLERS_AVAILABLE = False
    # 提供备用定义
    class APIError(Exception): pass
    class ValidationError(APIError): pass
    class NotFoundError(APIError): pass
    class UnauthorizedError(APIError): pass
    class RateLimitError(APIError): pass
    class InternalServerError(APIError): pass
    def SearchRequestValidator(): return None
    def DocumentAddRequestValidator(): return None
    def QueryRequestValidator(): return None
    def sanitize_input(x): return x
    def validate_file_path(x): return True

__all__ = [
    # REST API
    "QueryRequest",
    "QueryResponse",
    "DocumentAddRequest",
    "DocumentAddResponse",
    "HealthResponse",
    "StatsResponse",
    "create_rest_api_app",
    "run_rest_api",

    # Error Handling
    "APIError",
    "ValidationError",
    "NotFoundError",
    "UnauthorizedError",
    "RateLimitError",
    "InternalServerError",

    # Validators
    "SearchRequestValidator",
    "DocumentAddRequestValidator",
    "QueryRequestValidator",

    # Utilities
    "sanitize_input",
    "validate_file_path"
]
