"""
缓存模块 - 产品级
支持LRU缓存和TTL缓存
"""

import time
import hashlib
from typing import Any, Optional, Callable, Dict, List
from collections import OrderedDict
from dataclasses import dataclass
from functools import wraps

try:
    from ..base_layer import get_logger, get_settings
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)
    class SimpleSettings:
        pass
    def get_settings():
        return SimpleSettings()

logger = get_logger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""
    value: Any
    timestamp: float
    ttl: Optional[float] = None  # None表示永久


class LRUCache:
    """
    产品级LRU缓存
    最近最少使用策略
    """

    def __init__(self, max_size: int = 1000, default_ttl: Optional[float] = None):
        self.settings = get_settings()
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key not in self.cache:
            self.misses += 1
            return None

        entry = self.cache[key]

        # 检查是否过期
        if entry.ttl is not None:
            if time.time() - entry.timestamp > entry.ttl:
                del self.cache[key]
                self.misses += 1
                logger.debug(f"缓存过期: {key}")
                return None

        # 移到末尾表示最近使用
        self.cache.move_to_end(key)
        self.hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """设置缓存"""
        # 如果已存在，先删除
        if key in self.cache:
            del self.cache[key]

        # 如果已满，删除最旧的
        if len(self.cache) >= self.max_size:
            removed_key, _ = self.cache.popitem(last=False)
            logger.debug(f"缓存溢出，删除: {removed_key}")

        # 添加新条目
        ttl = ttl if ttl is not None else self.default_ttl
        self.cache[key] = CacheEntry(
            value=value,
            timestamp=time.time(),
            ttl=ttl
        )

    def delete(self, key: str) -> bool:
        """删除缓存"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False

    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def cleanup_expired(self) -> int:
        """清理过期条目"""
        expired_keys = []
        current_time = time.time()

        for key, entry in self.cache.items():
            if entry.ttl is not None:
                if current_time - entry.timestamp > entry.ttl:
                    expired_keys.append(key)

        for key in expired_keys:
            del self.cache[key]

        return len(expired_keys)

    def stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0

        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate
        }

    def __contains__(self, key: str) -> bool:
        return self.get(key) is not None

    def __len__(self) -> int:
        return len(self.cache)


class TTLCache:
    """
    产品级TTL缓存
    基于过期时间的缓存
    """

    def __init__(self, default_ttl: float = 3600):
        self.settings = get_settings()
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key not in self.cache:
            self.misses += 1
            return None

        entry = self.cache[key]

        # 检查是否过期
        if entry.ttl is not None:
            if time.time() - entry.timestamp > entry.ttl:
                del self.cache[key]
                self.misses += 1
                logger.debug(f"缓存过期: {key}")
                return None

        self.hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """设置缓存"""
        ttl = ttl if ttl is not None else self.default_ttl
        self.cache[key] = CacheEntry(
            value=value,
            timestamp=time.time(),
            ttl=ttl
        )

    def delete(self, key: str) -> bool:
        """删除缓存"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False

    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def cleanup_expired(self) -> int:
        """清理过期条目"""
        expired_keys = []
        current_time = time.time()

        for key, entry in self.cache.items():
            if entry.ttl is not None:
                if current_time - entry.timestamp > entry.ttl:
                    expired_keys.append(key)

        for key in expired_keys:
            del self.cache[key]

        return len(expired_keys)

    def stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0

        return {
            'size': len(self.cache),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate
        }

    def __contains__(self, key: str) -> bool:
        return self.get(key) is not None

    def __len__(self) -> int:
        return len(self.cache)


# 全局缓存实例
_lru_cache: Optional[LRUCache] = None
_ttl_cache: Optional[TTLCache] = None


def get_lru_cache(max_size: int = 1000, default_ttl: Optional[float] = None) -> LRUCache:
    """获取LRU缓存单例"""
    global _lru_cache
    if _lru_cache is None:
        _lru_cache = LRUCache(max_size, default_ttl)
    return _lru_cache


def get_ttl_cache(default_ttl: float = 3600) -> TTLCache:
    """获取TTL缓存单例"""
    global _ttl_cache
    if _ttl_cache is None:
        _ttl_cache = TTLCache(default_ttl)
    return _ttl_cache


def lru_cache_decorator(max_size: int = 1000, 
                       ttl: Optional[float] = None,
                       key_func: Optional[Callable] = None):
    """
    LRU缓存装饰器
    """
    cache = LRUCache(max_size, ttl)

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key_parts = [func.__module__, func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                key = hashlib.md5("|".join(key_parts).encode()).hexdigest()

            # 尝试获取缓存
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value

            # 执行函数
            result = func(*args, **kwargs)

            # 缓存结果
            cache.set(key, result)
            return result

        return wrapper

    return decorator


def ttl_cache_decorator(ttl: float = 3600,
                       key_func: Optional[Callable] = None):
    """
    TTL缓存装饰器
    """
    cache = TTLCache(ttl)

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key_parts = [func.__module__, func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                key = hashlib.md5("|".join(key_parts).encode()).hexdigest()

            # 尝试获取缓存
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value

            # 执行函数
            result = func(*args, **kwargs)

            # 缓存结果
            cache.set(key, result)
            return result

        return wrapper

    return decorator
