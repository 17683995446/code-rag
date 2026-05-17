"""
Code RAG v18.0 - 性能监控优化模块
提供查询响应时间追踪、资源监控、性能基准测试和缓存机制
"""

import time
import functools
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from collections import OrderedDict
from threading import Lock
import hashlib
import json


@dataclass
class PerformanceMetric:
    """性能指标"""
    operation: str
    start_time: float
    end_time: float
    duration: float
    success: bool
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def timestamp(self) -> datetime:
        return datetime.fromtimestamp(self.start_time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'operation': self.operation,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration_ms': self.duration * 1000,
            'success': self.success,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class ResourceUsage:
    """资源使用情况"""
    timestamp: datetime
    memory_mb: Optional[float] = None
    cpu_percent: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'memory_mb': self.memory_mb,
            'cpu_percent': self.cpu_percent
        }


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics: List[PerformanceMetric] = []
        self.operation_stats: Dict[str, Dict[str, float]] = {}
        self._lock = Lock()
        self._request_counter = 0
        self._error_counter = 0
    
    def record_metric(self, operation: str, start_time: float, end_time: float,
                     success: bool = True, metadata: Dict[str, Any] = None):
        """记录性能指标"""
        metric = PerformanceMetric(
            operation=operation,
            start_time=start_time,
            end_time=end_time,
            duration=end_time - start_time,
            success=success,
            metadata=metadata or {}
        )
        
        with self._lock:
            self.metrics.append(metric)
            self._update_stats(metric)
            
            if not success:
                self._error_counter += 1
            self._request_counter += 1
    
    def _update_stats(self, metric: PerformanceMetric):
        """更新统计信息"""
        op = metric.operation
        if op not in self.operation_stats:
            self.operation_stats[op] = {
                'count': 0,
                'total_duration': 0,
                'min_duration': float('inf'),
                'max_duration': 0,
                'error_count': 0
            }
        
        stats = self.operation_stats[op]
        stats['count'] += 1
        stats['total_duration'] += metric.duration
        stats['min_duration'] = min(stats['min_duration'], metric.duration)
        stats['max_duration'] = max(stats['max_duration'], metric.duration)
        if not metric.success:
            stats['error_count'] += 1
    
    def get_operation_stats(self, operation: str) -> Optional[Dict[str, Any]]:
        """获取操作统计"""
        with self._lock:
            stats = self.operation_stats.get(operation)
            if not stats:
                return None
            
            count = stats['count']
            return {
                'operation': operation,
                'count': count,
                'total_duration_ms': stats['total_duration'] * 1000,
                'avg_duration_ms': (stats['total_duration'] / count) * 1000 if count > 0 else 0,
                'min_duration_ms': stats['min_duration'] * 1000,
                'max_duration_ms': stats['max_duration'] * 1000,
                'error_count': stats['error_count'],
                'error_rate': stats['error_count'] / count if count > 0 else 0
            }
    
    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有统计"""
        with self._lock:
            return {
                'total_requests': self._request_counter,
                'total_errors': self._error_counter,
                'error_rate': self._error_counter / self._request_counter if self._request_counter > 0 else 0,
                'operations': {
                    op: self.get_operation_stats(op)
                    for op in self.operation_stats.keys()
                }
            }
    
    def get_recent_metrics(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取最近的指标"""
        with self._lock:
            return [m.to_dict() for m in self.metrics[-limit:]]
    
    def clear_metrics(self):
        """清除指标"""
        with self._lock:
            self.metrics.clear()
            self.operation_stats.clear()
            self._request_counter = 0
            self._error_counter = 0


class ResourceMonitor:
    """资源监控器"""
    
    def __init__(self):
        self.usage_history: List[ResourceUsage] = []
        self._lock = Lock()
        self._psutil_available = False
        
        try:
            import psutil
            self._psutil = psutil
            self._psutil_available = True
        except ImportError:
            import warnings
            warnings.warn("psutil not available, resource monitoring limited")
    
    def record_usage(self) -> ResourceUsage:
        """记录资源使用"""
        usage = ResourceUsage(timestamp=datetime.now())
        
        if self._psutil_available:
            try:
                process = self._psutil.Process()
                memory_info = process.memory_info()
                usage.memory_mb = memory_info.rss / (1024 * 1024)
                try:
                    usage.cpu_percent = process.cpu_percent(interval=0)
                except Exception:
                    usage.cpu_percent = None
            except Exception:
                pass
        
        with self._lock:
            self.usage_history.append(usage)
            if len(self.usage_history) > 1000:
                self.usage_history = self.usage_history[-1000:]
        
        return usage
    
    def get_current_usage(self) -> Optional[ResourceUsage]:
        """获取当前使用情况"""
        if not self._psutil_available:
            return None
        
        return self.record_usage()
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """获取使用统计"""
        with self._lock:
            if not self.usage_history:
                return {'message': 'No usage data available'}
            
            memory_values = [u.memory_mb for u in self.usage_history if u.memory_mb]
            cpu_values = [u.cpu_percent for u in self.usage_history if u.cpu_percent]
            
            return {
                'samples': len(self.usage_history),
                'memory_mb': {
                    'current': memory_values[-1] if memory_values else None,
                    'avg': sum(memory_values) / len(memory_values) if memory_values else None,
                    'max': max(memory_values) if memory_values else None,
                    'min': min(memory_values) if memory_values else None
                },
                'cpu_percent': {
                    'current': cpu_values[-1] if cpu_values else None,
                    'avg': sum(cpu_values) / len(cpu_values) if cpu_values else None,
                    'max': max(cpu_values) if cpu_values else None,
                    'min': min(cpu_values) if cpu_values else None
                }
            }


class LRUCache:
    """LRU缓存实现"""
    
    def __init__(self, max_size: int = 128, ttl_seconds: int = 3600):
        self._cache: OrderedDict = OrderedDict()
        self._timestamps: Dict[str, float] = {}
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds
        self._lock = Lock()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            if self._is_expired(key):
                self._remove(key)
                self._misses += 1
                return None
            
            self._cache.move_to_end(key)
            self._hits += 1
            return self._cache[key]
    
    def set(self, key: str, value: Any):
        """设置缓存值"""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self._max_size:
                    self._evict_oldest()
                
                self._cache[key] = value
            
            self._timestamps[key] = time.time()
    
    def _is_expired(self, key: str) -> bool:
        """检查是否过期"""
        if key not in self._timestamps:
            return True
        return (time.time() - self._timestamps[key]) > self._ttl_seconds
    
    def _remove(self, key: str):
        """移除缓存项"""
        if key in self._cache:
            del self._cache[key]
        if key in self._timestamps:
            del self._timestamps[key]
    
    def _evict_oldest(self):
        """驱逐最老的项"""
        if self._cache:
            oldest_key = next(iter(self._cache))
            self._remove(oldest_key)
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
            self._hits = 0
            self._misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self._lock:
            total = self._hits + self._misses
            return {
                'size': len(self._cache),
                'max_size': self._max_size,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': self._hits / total if total > 0 else 0,
                'ttl_seconds': self._ttl_seconds
            }


def timed_operation(monitor: PerformanceMonitor, operation_name: str):
    """装饰器：计时操作"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            result = None
            error = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error = str(e)
                raise
            finally:
                end_time = time.time()
                metadata = {'error': error} if error else {}
                monitor.record_metric(operation_name, start_time, end_time, success, metadata)
        
        return wrapper
    return decorator


class PerformanceBenchmark:
    """性能基准测试"""
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
        self.benchmarks: Dict[str, List[float]] = {}
    
    def run_benchmark(self, name: str, func: Callable, iterations: int = 100,
                     warmup: int = 10) -> Dict[str, Any]:
        """运行基准测试"""
        if warmup > 0:
            for _ in range(warmup):
                func()
        
        durations = []
        for _ in range(iterations):
            start = time.time()
            func()
            end = time.time()
            durations.append((end - start) * 1000)
        
        self.benchmarks[name] = durations
        
        sorted_durations = sorted(durations)
        return {
            'name': name,
            'iterations': iterations,
            'min_ms': min(durations),
            'max_ms': max(durations),
            'avg_ms': sum(durations) / len(durations),
            'median_ms': sorted_durations[len(sorted_durations) // 2],
            'p95_ms': sorted_durations[int(len(sorted_durations) * 0.95)],
            'p99_ms': sorted_durations[int(len(sorted_durations) * 0.99)],
        }
    
    def get_benchmark_results(self) -> Dict[str, Dict[str, float]]:
        """获取所有基准测试结果"""
        results = {}
        for name, durations in self.benchmarks.items():
            sorted_durations = sorted(durations)
            results[name] = {
                'min_ms': min(durations),
                'max_ms': max(durations),
                'avg_ms': sum(durations) / len(durations),
                'median_ms': sorted_durations[len(sorted_durations) // 2],
                'p95_ms': sorted_durations[int(len(durations) * 0.95)],
                'p99_ms': sorted_durations[int(len(durations) * 0.99)],
                'samples': len(durations)
            }
        return results


class PerformanceDashboard:
    """性能仪表板"""
    
    def __init__(self, monitor: PerformanceMonitor, resource_monitor: ResourceMonitor,
                 cache: LRUCache):
        self.monitor = monitor
        self.resource_monitor = resource_monitor
        self.cache = cache
    
    def generate_report(self) -> Dict[str, Any]:
        """生成性能报告"""
        return {
            'timestamp': datetime.now().isoformat(),
            'performance': self.monitor.get_all_stats(),
            'resources': self.resource_monitor.get_usage_stats(),
            'cache': self.cache.get_stats(),
            'summary': self._generate_summary()
        }
    
    def _generate_summary(self) -> Dict[str, Any]:
        """生成摘要"""
        perf_stats = self.monitor.get_all_stats()
        cache_stats = self.cache.get_stats()
        
        issues = []
        recommendations = []
        
        if cache_stats['hit_rate'] < 0.5:
            issues.append('缓存命中率较低')
            recommendations.append('考虑增大缓存大小或调整TTL')
        
        error_rate = perf_stats.get('error_rate', 0)
        if error_rate > 0.05:
            issues.append(f'错误率较高: {error_rate:.2%}')
            recommendations.append('检查系统稳定性')
        
        for op, stats in perf_stats.get('operations', {}).items():
            if stats and stats['avg_duration_ms'] > 200:
                issues.append(f'{op}平均响应时间过长: {stats["avg_duration_ms"]:.2f}ms')
                recommendations.append(f'优化{op}性能')
        
        return {
            'status': 'healthy' if len(issues) == 0 else 'warning',
            'issues': issues,
            'recommendations': recommendations
        }
    
    def print_dashboard(self):
        """打印仪表板"""
        report = self.generate_report()
        
        print("\n" + "="*80)
        print("📊 Code RAG v18.0 - 性能监控仪表板")
        print("="*80)
        print(f"⏰ 时间: {report['timestamp']}")
        
        print("\n🔍 性能统计:")
        perf = report['performance']
        print(f"  - 总请求数: {perf.get('total_requests', 0)}")
        print(f"  - 总错误数: {perf.get('total_errors', 0)}")
        print(f"  - 错误率: {perf.get('error_rate', 0):.2%}")
        
        if perf.get('operations'):
            print("\n📈 操作统计:")
            for op, stats in perf['operations'].items():
                if stats:
                    print(f"  {op}:")
                    print(f"    - 次数: {stats['count']}")
                    print(f"    - 平均: {stats['avg_duration_ms']:.2f}ms")
                    print(f"    - 最小: {stats['min_duration_ms']:.2f}ms")
                    print(f"    - 最大: {stats['max_duration_ms']:.2f}ms")
        
        print("\n💾 缓存统计:")
        cache = report['cache']
        print(f"  - 大小: {cache['size']}/{cache['max_size']}")
        print(f"  - 命中率: {cache['hit_rate']:.2%}")
        print(f"  - 命中: {cache['hits']}")
        print(f"  - 未命中: {cache['misses']}")
        
        print("\n🖥️ 资源使用:")
        resources = report['resources']
        if 'memory_mb' in resources:
            mem = resources['memory_mb']
            print(f"  - 当前内存: {mem.get('current', 0):.2f} MB")
            print(f"  - 平均内存: {mem.get('avg', 0):.2f} MB")
            print(f"  - 最大内存: {mem.get('max', 0):.2f} MB")
        
        print("\n📋 健康状态:")
        summary = report['summary']
        status_icon = "✅" if summary['status'] == 'healthy' else "⚠️"
        print(f"  {status_icon} 状态: {summary['status']}")
        
        if summary['issues']:
            print("\n❌ 问题:")
            for issue in summary['issues']:
                print(f"  - {issue}")
        
        if summary['recommendations']:
            print("\n💡 建议:")
            for rec in summary['recommendations']:
                print(f"  - {rec}")
        
        print("="*80 + "\n")


class PerformanceOptimizer:
    """性能优化器"""
    
    def __init__(self, monitor: PerformanceMonitor, cache: LRUCache):
        self.monitor = monitor
        self.cache = cache
        self.optimization_rules = []
    
    def add_rule(self, condition: Callable, action: Callable):
        """添加优化规则"""
        self.optimization_rules.append((condition, action))
    
    def analyze_and_optimize(self):
        """分析并优化"""
        report = self.monitor.get_all_stats()
        suggestions = []
        
        slow_operations = []
        for op, stats in report.get('operations', {}).items():
            if stats and stats['avg_duration_ms'] > 100:
                slow_operations.append((op, stats['avg_duration_ms']))
        
        if slow_operations:
            suggestions.append({
                'type': 'slow_operation',
                'details': slow_operations,
                'action': 'Consider adding caching or optimizing the algorithm'
            })
        
        cache_stats = self.cache.get_stats()
        if cache_stats['hit_rate'] < 0.6:
            suggestions.append({
                'type': 'cache_inefficient',
                'current_hit_rate': cache_stats['hit_rate'],
                'action': 'Increase cache size or adjust TTL'
            })
        
        for condition, action in self.optimization_rules:
            if condition(report):
                action(report)
                suggestions.append({
                    'type': 'custom_rule',
                    'action': action.__name__
                })
        
        return suggestions


def cached_operation(cache: LRUCache, key_func: Callable = None):
    """缓存操作装饰器"""
    def decorator(func: Callable) -> Callable:
        if key_func:
            cache_key_func = key_func
        else:
            def default_key_func(*args, **kwargs):
                key_str = f"{func.__name__}:{str(args)}:{str(kwargs)}"
                return hashlib.md5(key_str.encode()).hexdigest()
            cache_key_func = default_key_func
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = cache_key_func(*args, **kwargs)
            
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            return result
        
        return wrapper
    return decorator
