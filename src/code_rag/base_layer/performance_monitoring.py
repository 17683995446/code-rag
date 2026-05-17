"""
监控和指标模块 - 产品级
支持性能监控、统计信息收集
站在巨人的肩膀上 - 使用psutil
"""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque
from datetime import datetime, timedelta
from contextlib import contextmanager

from .logging_and_diagnostics import get_logger

logger = get_logger(__name__)

# 尝试导入psutil，如果失败则使用fallback
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available, using fallback monitoring")


@dataclass
class MetricPoint:
    """指标点"""
    timestamp: float
    value: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class OperationStats:
    """操作统计"""
    operation: str
    count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    errors: int = 0
    
    @property
    def avg_time(self) -> float:
        return self.total_time / self.count if self.count > 0 else 0.0


class MetricsCollector:
    """
    产品级指标收集器
    收集和聚合系统指标
    """
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._operation_stats: Dict[str, OperationStats] = defaultdict(
            lambda: OperationStats(operation="")
        )
        
    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """记录指标"""
        point = MetricPoint(
            timestamp=time.time(),
            value=value,
            tags=tags or {}
        )
        self._metrics[name].append(point)
        
    def increment_counter(self, name: str, value: int = 1):
        """增加计数器"""
        self._counters[name] += value
        
    def set_gauge(self, name: str, value: float):
        """设置仪表值"""
        self._gauges[name] = value
        
    def record_operation(self, operation: str, duration: float, error: bool = False):
        """记录操作统计"""
        stats = self._operation_stats[operation]
        stats.operation = operation
        stats.count += 1
        stats.total_time += duration
        stats.min_time = min(stats.min_time, duration)
        stats.max_time = max(stats.max_time, duration)
        if error:
            stats.errors += 1
            
    def get_metric_stats(self, name: str, window_seconds: Optional[float] = None) -> Dict[str, Any]:
        """获取指标统计"""
        if name not in self._metrics:
            return {}
            
        points = self._metrics[name]
        if not points:
            return {}
            
        # 过滤时间窗口
        if window_seconds:
            cutoff = time.time() - window_seconds
            points = [p for p in points if p.timestamp >= cutoff]
            
        if not points:
            return {}
            
        values = [p.value for p in points]
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'latest': values[-1]
        }
        
    def get_counter(self, name: str) -> int:
        """获取计数器值"""
        return self._counters.get(name, 0)
        
    def get_gauge(self, name: str) -> float:
        """获取仪表值"""
        return self._gauges.get(name, 0.0)
        
    def get_operation_stats(self, operation: str) -> Optional[OperationStats]:
        """获取操作统计"""
        return self._operation_stats.get(operation)
        
    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有统计信息"""
        return {
            'counters': dict(self._counters),
            'gauges': dict(self._gauges),
            'operations': {
                name: {
                    'count': stats.count,
                    'total_time': stats.total_time,
                    'avg_time': stats.avg_time,
                    'min_time': stats.min_time if stats.min_time != float('inf') else 0,
                    'max_time': stats.max_time,
                    'errors': stats.errors,
                    'error_rate': stats.errors / stats.count if stats.count > 0 else 0
                }
                for name, stats in self._operation_stats.items()
            }
        }
        
    def reset(self):
        """重置所有指标"""
        self._metrics.clear()
        self._counters.clear()
        self._gauges.clear()
        self._operation_stats.clear()


class PerformanceMonitor:
    """
    产品级性能监控器
    监控CPU、内存、磁盘等系统资源
    支持psutil不可用时的fallback
    """
    
    def __init__(self, metrics_collector: Optional[MetricsCollector] = None):
        self.metrics = metrics_collector or MetricsCollector()
        self._process = None
        if PSUTIL_AVAILABLE:
            try:
                self._process = psutil.Process()
            except Exception as e:
                logger.warning(f"初始化psutil Process失败: {e}")
        
    def record_system_metrics(self):
        """记录系统指标"""
        if not PSUTIL_AVAILABLE:
            # Fallback - 记录一些基本指标
            self.metrics.set_gauge('system.cpu.percent', 0.0)
            self.metrics.set_gauge('system.memory.percent', 0.0)
            self.metrics.set_gauge('process.cpu.user', 0.0)
            self.metrics.set_gauge('process.cpu.system', 0.0)
            self.metrics.set_gauge('process.memory.rss_mb', 0.0)
            self.metrics.set_gauge('process.memory.vms_mb', 0.0)
            self.metrics.set_gauge('process.threads', 1)
            return
        
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.metrics.record_metric('system.cpu.percent', cpu_percent)
            self.metrics.set_gauge('system.cpu.percent', cpu_percent)
            
            # 内存使用
            mem = psutil.virtual_memory()
            self.metrics.record_metric('system.memory.percent', mem.percent)
            self.metrics.record_metric('system.memory.available_mb', mem.available / 1024 / 1024)
            self.metrics.set_gauge('system.memory.percent', mem.percent)
            
            # 进程资源
            if self._process:
                cpu_times = self._process.cpu_times()
                self.metrics.set_gauge('process.cpu.user', cpu_times.user)
                self.metrics.set_gauge('process.cpu.system', cpu_times.system)
                
                mem_info = self._process.memory_info()
                self.metrics.set_gauge('process.memory.rss_mb', mem_info.rss / 1024 / 1024)
                self.metrics.set_gauge('process.memory.vms_mb', mem_info.vms / 1024 / 1024)
                
                # 线程数
                self.metrics.set_gauge('process.threads', self._process.num_threads())
            
        except Exception as e:
            logger.warning(f"获取系统指标失败: {e}")
            # 即使失败也要设置一些基本指标
            self.metrics.set_gauge('system.cpu.percent', 0.0)
            self.metrics.set_gauge('system.memory.percent', 0.0)
            
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        if not PSUTIL_AVAILABLE:
            # Fallback - 返回基本信息
            return {
                'cpu': {
                    'count': 1,
                    'percent': 0.0
                },
                'memory': {
                    'percent': 0.0,
                    'available': 0
                },
                'disk': {
                    'percent': 0.0,
                    'free': 0
                },
                'process': {
                    'pid': 0,
                    'threads': 1
                }
            }
        
        try:
            result = {
                'cpu': {
                    'count': psutil.cpu_count(),
                    'percent': psutil.cpu_percent(interval=0.1)
                },
                'memory': psutil.virtual_memory()._asdict(),
                'disk': psutil.disk_usage('/')._asdict(),
                'process': {}
            }
            
            if self._process:
                result['process'] = {
                    'pid': self._process.pid,
                    'threads': self._process.num_threads(),
                    'memory_info': self._process.memory_info()._asdict()
                }
            
            return result
        except Exception as e:
            logger.error(f"获取系统信息失败: {e}")
            return {}
            
    @contextmanager
    def monitor_operation(self, operation: str):
        """监控操作上下文管理器"""
        start_time = time.time()
        error = False
        try:
            yield
        except Exception as e:
            error = True
            logger.error(f"操作 {operation} 失败: {e}")
            raise
        finally:
            duration = time.time() - start_time
            self.metrics.record_operation(operation, duration, error)
            self.metrics.increment_counter(f"operations.{operation}.total")
            if error:
                self.metrics.increment_counter(f"operations.{operation}.errors")
                
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        self.record_system_metrics()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'system': {
                'cpu_percent': self.metrics.get_gauge('system.cpu.percent'),
                'memory_percent': self.metrics.get_gauge('system.memory.percent'),
                'memory_available_mb': self.metrics.get_metric_stats(
                    'system.memory.available_mb', window_seconds=60
                ).get('latest', 0)
            },
            'process': {
                'cpu_user': self.metrics.get_gauge('process.cpu.user'),
                'cpu_system': self.metrics.get_gauge('process.cpu.system'),
                'memory_rss_mb': self.metrics.get_gauge('process.memory.rss_mb'),
                'threads': self.metrics.get_gauge('process.threads')
            },
            'operations': self.metrics.get_all_stats()['operations']
        }


# 全局监控器实例
_monitor: Optional[PerformanceMonitor] = None


def get_monitor() -> PerformanceMonitor:
    """获取全局监控器"""
    global _monitor
    if _monitor is None:
        _monitor = PerformanceMonitor()
    return _monitor


@contextmanager
def monitor(operation: str):
    """便捷的监控上下文管理器"""
    monitor = get_monitor()
    with monitor.monitor_operation(operation):
        yield
