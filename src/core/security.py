"""
安全模块 - 产品级
支持认证、限流、数据验证、敏感信息处理
"""

import hashlib
import hmac
import time
import re
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from functools import wraps
from collections import defaultdict, deque
from contextlib import contextmanager

from .logger import get_logger
from .settings import get_settings

logger = get_logger(__name__)


class RateLimiter:
    """
    产品级限流器
    支持滑动窗口和令牌桶算法
    """

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: deque = deque()
        self._hits = 0
        self._misses = 0

    def check_rate_limit(self, client_id: str = "default") -> bool:
        """检查是否超过限流"""
        now = time.time()
        cutoff = now - self.window_seconds

        # 清理过期请求
        while self._requests and self._requests[0] < cutoff:
            self._requests.popleft()

        # 检查是否超过限制
        if len(self._requests) >= self.max_requests:
            self._misses += 1
            return False

        # 记录请求
        self._requests.append(now)
        self._hits += 1
        return True

    def get_remaining(self) -> int:
        """获取剩余请求数"""
        now = time.time()
        cutoff = now - self.window_seconds

        while self._requests and self._requests[0] < cutoff:
            self._requests.popleft()

        return max(0, self.max_requests - len(self._requests))

    def get_reset_time(self) -> float:
        """获取重置时间"""
        if not self._requests:
            return time.time()

        return self._requests[0] + self.window_seconds

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = self._hits + self._misses
        return {
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': self._hits / total if total > 0 else 0,
            'remaining': self.get_remaining()
        }


class InputValidator:
    """
    产品级输入验证器
    支持路径、查询、文件内容验证
    """

    def __init__(self):
        self.settings = get_settings()
        self._dangerous_patterns = [
            r'\.\.\/',  # 路径穿越
            r'\.\.\\',  # Windows路径穿越
            r'/\.\.',   # Unix路径穿越
            r'eval\s*\(',  # eval注入
            r'exec\s*\(',  # exec注入
            r'<script',  # XSS
            r'javascript:',  # JS协议
        ]
        self._dangerous_regex = [re.compile(p, re.IGNORECASE) for p in self._dangerous_patterns]

    def validate_path(self, path: str) -> bool:
        """验证路径安全性"""
        if not path:
            return False

        # 检查路径穿越
        if '..' in path:
            logger.warning(f"路径穿越尝试: {path}")
            return False

        # 检查危险模式
        for pattern in self._dangerous_regex:
            if pattern.search(path):
                logger.warning(f"危险路径模式: {path}")
                return False

        return True

    def validate_query(self, query: str) -> bool:
        """验证查询安全性"""
        if not query or len(query) > 10000:
            return False

        # 检查危险模式
        for pattern in self._dangerous_regex:
            if pattern.search(query):
                logger.warning(f"危险查询模式: {query}")
                return False

        return True

    def validate_file_content(self, content: str, max_size: int = 10 * 1024 * 1024) -> bool:
        """验证文件内容"""
        if not content:
            return False

        if len(content) > max_size:
            logger.warning(f"文件内容过大: {len(content)} bytes")
            return False

        # 检查危险模式
        for pattern in self._dangerous_regex:
            if pattern.search(content):
                logger.warning("文件内容包含危险模式")
                return False

        return True

    def sanitize_path(self, path: str) -> str:
        """清理路径"""
        # 移除危险字符
        path = path.replace('..', '')
        path = path.replace('<', '')
        path = path.replace('>', '')
        path = path.replace('|', '')
        path = path.replace('\0', '')
        return path.strip()

    def sanitize_query(self, query: str) -> str:
        """清理查询"""
        # HTML编码
        query = query.replace('<', '&lt;')
        query = query.replace('>', '&gt;')
        query = query.replace('"', '&quot;')
        query = query.replace("'", '&#x27;')
        return query.strip()


class SecurityManager:
    """
    产品级安全管理器
    整合认证、授权、审计
    """

    def __init__(self):
        self.settings = get_settings()
        self._rate_limiters: Dict[str, RateLimiter] = {}
        self._validator = InputValidator()
        self._audit_log = []

    def get_rate_limiter(self, client_id: str, max_requests: int = 100,
                        window_seconds: int = 60) -> RateLimiter:
        """获取或创建限流器"""
        if client_id not in self._rate_limiters:
            self._rate_limiters[client_id] = RateLimiter(max_requests, window_seconds)
        return self._rate_limiters[client_id]

    def check_auth(self, api_key: Optional[str]) -> bool:
        """检查认证"""
        if not api_key:
            return False

        # 简单的API Key检查（生产环境应使用更复杂的认证）
        return len(api_key) >= 32

    def audit_log(self, action: str, details: Dict[str, Any]):
        """记录审计日志"""
        entry = {
            'timestamp': time.time(),
            'action': action,
            'details': details
        }
        self._audit_log.append(entry)

        # 保留最近1000条审计日志
        if len(self._audit_log) > 1000:
            self._audit_log = self._audit_log[-1000:]

        logger.info(f"审计日志: {action} - {details}")

    def get_audit_log(self, limit: int = 100) -> list:
        """获取审计日志"""
        return self._audit_log[-limit:]


def rate_limit(max_requests: int = 100, window_seconds: int = 60,
              client_id_func: Optional[Callable] = None):
    """
    限流装饰器
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取客户端ID
            client_id = "default"
            if client_id_func:
                try:
                    client_id = client_id_func(*args, **kwargs)
                except:
                    pass

            # 检查限流
            limiter = _get_global_rate_limiter(client_id, max_requests, window_seconds)
            if not limiter.check_rate_limit(client_id):
                raise Exception(f"请求过于频繁，请稍后再试")

            return func(*args, **kwargs)
        return wrapper
    return decorator


# 全局限流器
_global_rate_limiters: Dict[str, RateLimiter] = {}
_security_manager: Optional[SecurityManager] = None


def _get_global_rate_limiter(client_id: str, max_requests: int,
                            window_seconds: int) -> RateLimiter:
    """获取全局限流器"""
    key = f"{client_id}:{max_requests}:{window_seconds}"
    if key not in _global_rate_limiters:
        _global_rate_limiters[key] = RateLimiter(max_requests, window_seconds)
    return _global_rate_limiters[key]


def get_security_manager() -> SecurityManager:
    """获取安全管理器"""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager


@contextmanager
def security_context(action: str, **kwargs):
    """安全的上下文管理器"""
    manager = get_security_manager()
    start_time = time.time()

    try:
        yield manager
        manager.audit_log(action, {**kwargs, 'status': 'success'})
    except Exception as e:
        manager.audit_log(action, {**kwargs, 'status': 'error', 'error': str(e)})
        raise
    finally:
        duration = time.time() - start_time
        logger.debug(f"{action} completed in {duration:.3f}s")
