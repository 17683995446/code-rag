"""
中间件层模块（Middleware Layer）
提供请求处理管道、拦截器、过滤器等功能
"""

from typing import Dict, Any, Optional, List, Callable, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
import time

try:
    from ..base_layer import get_logger
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)

logger = get_logger(__name__)


# ============================================================================
# 中间件接口
# ============================================================================

class Middleware(ABC):
    """中间件抽象接口"""

    @abstractmethod
    def process_request(self, request: Any) -> Any:
        """处理请求"""
        pass

    @abstractmethod
    def process_response(self, response: Any) -> Any:
        """处理响应"""
        pass

    @abstractmethod
    def process_error(self, error: Exception) -> Any:
        """处理错误"""
        pass


class Filter(Middleware):
    """过滤器接口"""

    @abstractmethod
    def filter(self, data: Any) -> bool:
        """过滤数据"""
        pass


class Interceptor(Middleware):
    """拦截器接口"""

    @abstractmethod
    def intercept(self, request: Any) -> Tuple[bool, Any]:
        """拦截请求"""
        pass


# ============================================================================
# 请求/响应对象
# ============================================================================

@dataclass
class Request:
    """请求对象"""
    id: str
    method: str
    path: str
    headers: Dict[str, str]
    body: Any
    params: Dict[str, str]
    timestamp: datetime
    context: Dict[str, Any] = None


@dataclass
class Response:
    """响应对象"""
    status_code: int
    headers: Dict[str, str]
    body: Any
    request_id: str
    timestamp: datetime
    latency: float = 0.0


# ============================================================================
# 实现类
# ============================================================================

class RequestLoggingMiddleware(Middleware):
    """请求日志中间件"""

    def __init__(self):
        self._logger = logger

    def process_request(self, request: Request) -> Request:
        """记录请求日志"""
        self._logger.info(f"Request: {request.method} {request.path}")
        self._logger.debug(f"Request params: {request.params}")
        return request

    def process_response(self, response: Response) -> Response:
        """记录响应日志"""
        self._logger.info(f"Response: {response.status_code} (latency: {response.latency:.2f}ms)")
        return response

    def process_error(self, error: Exception) -> Exception:
        """记录错误日志"""
        self._logger.error(f"Error: {error}", exc_info=True)
        return error


class TimingMiddleware(Middleware):
    """计时中间件"""

    def __init__(self):
        self._start_time = 0.0

    def process_request(self, request: Request) -> Request:
        """记录开始时间"""
        self._start_time = time.time()
        return request

    def process_response(self, response: Response) -> Response:
        """计算延迟"""
        response.latency = (time.time() - self._start_time) * 1000
        return response

    def process_error(self, error: Exception) -> Exception:
        """计算错误处理延迟"""
        latency = (time.time() - self._start_time) * 1000
        logger.info(f"Error processing time: {latency:.2f}ms")
        return error


class ValidationMiddleware(Middleware):
    """验证中间件"""

    def __init__(self, validators: Dict[str, Callable] = None):
        self._validators = validators or {}

    def register_validator(self, name: str, validator: Callable):
        """注册验证器"""
        self._validators[name] = validator

    def process_request(self, request: Request) -> Request:
        """验证请求"""
        for name, validator in self._validators.items():
            try:
                if not validator(request):
                    raise ValueError(f"Validation failed: {name}")
            except Exception as e:
                raise ValueError(f"Validation error: {e}")
        return request

    def process_response(self, response: Response) -> Response:
        """验证响应"""
        if response.status_code >= 400:
            logger.warning(f"Error response: {response.status_code}")
        return response

    def process_error(self, error: Exception) -> Exception:
        """处理验证错误"""
        logger.error(f"Validation error: {error}")
        return error


class RateLimitingMiddleware(Middleware):
    """限流中间件"""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._request_counts: Dict[str, List[float]] = {}

    def _get_client_key(self, request: Request) -> str:
        """获取客户端标识"""
        return request.headers.get('X-Client-Id', 'unknown')

    def process_request(self, request: Request) -> Request:
        """限流检查"""
        client_key = self._get_client_key(request)
        now = time.time()

        # 清理过期请求记录
        if client_key not in self._request_counts:
            self._request_counts[client_key] = []
        
        self._request_counts[client_key] = [
            t for t in self._request_counts[client_key]
            if now - t < self._window_seconds
        ]

        # 检查请求数
        if len(self._request_counts[client_key]) >= self._max_requests:
            raise ValueError("Rate limit exceeded")

        # 记录请求
        self._request_counts[client_key].append(now)
        return request

    def process_response(self, response: Response) -> Response:
        """处理响应"""
        return response

    def process_error(self, error: Exception) -> Exception:
        """处理错误"""
        return error


class AuthenticationMiddleware(Middleware):
    """认证中间件"""

    def __init__(self, valid_tokens: List[str] = None):
        self._valid_tokens = valid_tokens or []

    def process_request(self, request: Request) -> Request:
        """认证检查"""
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if token and token in self._valid_tokens:
            request.context = request.context or {}
            request.context['authenticated'] = True
            return request
        
        if not self._valid_tokens:
            # 如果没有配置令牌，允许访问
            request.context = request.context or {}
            request.context['authenticated'] = False
            return request
        
        raise ValueError("Unauthorized")

    def process_response(self, response: Response) -> Response:
        """处理响应"""
        return response

    def process_error(self, error: Exception) -> Exception:
        """处理认证错误"""
        logger.warning(f"Authentication failed: {error}")
        return error


class CompressionMiddleware(Middleware):
    """压缩中间件"""

    def __init__(self):
        try:
            import gzip
            self._gzip_available = True
        except ImportError:
            self._gzip_available = False
            logger.warning("gzip not available")

    def process_request(self, request: Request) -> Request:
        """检查压缩支持"""
        accept_encoding = request.headers.get('Accept-Encoding', '')
        request.context = request.context or {}
        request.context['accepts_gzip'] = 'gzip' in accept_encoding
        return request

    def process_response(self, response: Response) -> Response:
        """压缩响应"""
        if self._gzip_available and response.body:
            import gzip
            import io
            body_str = str(response.body) if not isinstance(response.body, str) else response.body
            compressed = gzip.compress(body_str.encode('utf-8'))
            response.body = compressed
            response.headers['Content-Encoding'] = 'gzip'
        return response

    def process_error(self, error: Exception) -> Exception:
        """处理错误"""
        return error


class CORSMiddleware(Middleware):
    """CORS中间件"""

    def __init__(self, allowed_origins: List[str] = None, allowed_methods: List[str] = None):
        self._allowed_origins = allowed_origins or ['*']
        self._allowed_methods = allowed_methods or ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']

    def process_request(self, request: Request) -> Request:
        """处理预检请求"""
        if request.method == 'OPTIONS':
            logger.debug("Handling CORS preflight request")
        return request

    def process_response(self, response: Response) -> Response:
        """添加CORS头"""
        response.headers['Access-Control-Allow-Origin'] = ','.join(self._allowed_origins)
        response.headers['Access-Control-Allow-Methods'] = ','.join(self._allowed_methods)
        response.headers['Access-Control-Allow-Headers'] = '*'
        return response

    def process_error(self, error: Exception) -> Exception:
        """处理错误"""
        return error


# ============================================================================
# 中间件管道
# ============================================================================

class MiddlewarePipeline:
    """中间件管道"""

    def __init__(self):
        self._middlewares: List[Middleware] = []

    def add(self, middleware: Middleware):
        """添加中间件"""
        self._middlewares.append(middleware)

    def process_request(self, request: Request) -> Request:
        """处理请求"""
        for middleware in self._middlewares:
            request = middleware.process_request(request)
        return request

    def process_response(self, response: Response) -> Response:
        """处理响应（逆序）"""
        for middleware in reversed(self._middlewares):
            response = middleware.process_response(response)
        return response

    def process_error(self, error: Exception) -> Exception:
        """处理错误"""
        for middleware in reversed(self._middlewares):
            error = middleware.process_error(error)
        return error

    def execute(self, request: Request, handler: Callable[[Request], Response]) -> Response:
        """执行请求处理"""
        try:
            request = self.process_request(request)
            response = handler(request)
            response = self.process_response(response)
            return response
        except Exception as e:
            self.process_error(e)
            return Response(
                status_code=500,
                headers={},
                body=str(e),
                request_id=request.id,
                timestamp=datetime.now(),
                latency=0.0
            )


# ============================================================================
# 工厂函数
# ============================================================================

def create_default_middleware_pipeline() -> MiddlewarePipeline:
    """创建默认中间件管道"""
    pipeline = MiddlewarePipeline()
    pipeline.add(RequestLoggingMiddleware())
    pipeline.add(TimingMiddleware())
    pipeline.add(ValidationMiddleware())
    pipeline.add(RateLimitingMiddleware())
    pipeline.add(AuthenticationMiddleware())
    pipeline.add(CORSMiddleware())
    pipeline.add(CompressionMiddleware())
    return pipeline


def get_logging_middleware() -> Middleware:
    """获取日志中间件"""
    return RequestLoggingMiddleware()


def get_timing_middleware() -> Middleware:
    """获取计时中间件"""
    return TimingMiddleware()


def get_validation_middleware() -> Middleware:
    """获取验证中间件"""
    return ValidationMiddleware()


def get_rate_limiting_middleware() -> Middleware:
    """获取限流中间件"""
    return RateLimitingMiddleware()


def get_authentication_middleware() -> Middleware:
    """获取认证中间件"""
    return AuthenticationMiddleware()


def get_cors_middleware() -> Middleware:
    """获取CORS中间件"""
    return CORSMiddleware()
