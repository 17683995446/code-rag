# Code RAG v18.0 - 性能监控模块文档

## 📋 概述

性能监控模块提供完整的系统性能追踪、资源监控、缓存管理和基准测试功能，帮助优化Code RAG的运行效率。

## 🏗️ 架构设计

```
性能监控系统
├── PerformanceMonitor         # 性能指标收集器
├── ResourceMonitor            # 系统资源监控
├── LRUCache                  # LRU缓存实现
├── PerformanceBenchmark       # 基准测试工具
├── PerformanceDashboard      # 性能仪表板
├── PerformanceOptimizer      # 性能优化建议
└── 装饰器和工具函数
    ├── @timed_operation      # 操作计时装饰器
    └── @cached_operation     # 缓存装饰器
```

## 🚀 快速开始

### 1. 基本性能监控

```python
from code_rag.observability.performance_monitor import PerformanceMonitor
import time

monitor = PerformanceMonitor()

start = time.time()
# 执行操作
result = your_operation()
end = time.time()

monitor.record_metric("operation_name", start, end, success=True)
```

### 2. 使用计时装饰器

```python
from code_rag.observability.performance_monitor import timed_operation

monitor = PerformanceMonitor()

@timed_operation(monitor, "my_operation")
def my_function():
    # 你的代码
    return result
```

### 3. LRU缓存

```python
from code_rag.observability.performance_monitor import LRUCache

cache = LRUCache(max_size=100, ttl_seconds=3600)

cache.set("key", "value")
value = cache.get("key")

stats = cache.get_stats()
print(f"命中率: {stats['hit_rate']:.2%}")
```

### 4. 性能仪表板

```python
from code_rag.observability.performance_monitor import (
    PerformanceMonitor, ResourceMonitor, LRUCache, PerformanceDashboard
)

monitor = PerformanceMonitor()
resource_monitor = ResourceMonitor()
cache = LRUCache(max_size=128)

dashboard = PerformanceDashboard(monitor, resource_monitor, cache)
dashboard.print_dashboard()
```

## 📊 核心组件

### PerformanceMonitor - 性能监控器

**功能**: 追踪和记录所有操作的性能指标

**主要方法**:

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `record_metric()` | 记录性能指标 | None |
| `get_operation_stats()` | 获取操作统计 | Dict |
| `get_all_stats()` | 获取所有统计 | Dict |
| `get_recent_metrics()` | 获取最近指标 | List[Dict] |

**统计指标**:

```python
{
    'operation': 'search',           # 操作名称
    'count': 100,                    # 调用次数
    'total_duration_ms': 1500.0,    # 总耗时(ms)
    'avg_duration_ms': 15.0,        # 平均耗时(ms)
    'min_duration_ms': 5.0,         # 最小耗时(ms)
    'max_duration_ms': 50.0,        # 最大耗时(ms)
    'error_count': 2,                # 错误次数
    'error_rate': 0.02              # 错误率
}
```

### ResourceMonitor - 资源监控器

**功能**: 监控CPU和内存使用情况

**主要方法**:

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `record_usage()` | 记录资源使用 | ResourceUsage |
| `get_current_usage()` | 获取当前使用 | ResourceUsage |
| `get_usage_stats()` | 获取统计 | Dict |

**资源指标**:

```python
{
    'samples': 100,
    'memory_mb': {
        'current': 256.5,
        'avg': 245.3,
        'max': 280.2,
        'min': 230.1
    },
    'cpu_percent': {
        'current': 15.2,
        'avg': 12.5,
        'max': 25.0,
        'min': 5.0
    }
}
```

**注意**: 需要安装 `psutil` 库以启用完整功能:
```bash
pip install psutil
```

### LRUCache - LRU缓存

**功能**: 实现最近最少使用缓存策略

**主要方法**:

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `get(key)` | 获取缓存值 | Any |
| `set(key, value)` | 设置缓存 | None |
| `clear()` | 清空缓存 | None |
| `get_stats()` | 获取统计 | Dict |

**缓存统计**:

```python
{
    'size': 50,               # 当前大小
    'max_size': 128,          # 最大容量
    'hits': 1000,             # 命中次数
    'misses': 200,           # 未命中次数
    'hit_rate': 0.833,       # 命中率
    'ttl_seconds': 3600       # TTL设置
}
```

### @timed_operation 装饰器

**功能**: 自动计时函数执行

**使用示例**:

```python
from code_rag.observability.performance_monitor import (
    timed_operation, PerformanceMonitor
)

monitor = PerformanceMonitor()

@timed_operation(monitor, "data_processing")
def process_data(data):
    # 处理数据
    return processed_data
```

### @cached_operation 装饰器

**功能**: 自动缓存函数结果

**使用示例**:

```python
from code_rag.observability.performance_monitor import cached_operation, LRUCache

cache = LRUCache(max_size=256)

@cached_operation(cache)
def expensive_computation(x, y):
    # 耗时计算
    return result
```

## 📈 性能基准测试

### PerformanceBenchmark

**功能**: 运行和记录基准测试

**使用方法**:

```python
from code_rag.observability.performance_monitor import (
    PerformanceBenchmark, PerformanceMonitor
)

monitor = PerformanceMonitor()
benchmark = PerformanceBenchmark(monitor)

def my_function():
    # 测试函数
    return result

result = benchmark.run_benchmark(
    name="my_benchmark",
    func=my_function,
    iterations=100,
    warmup=10
)

print(f"平均耗时: {result['avg_ms']:.2f}ms")
print(f"P95: {result['p95_ms']:.2f}ms")
print(f"P99: {result['p99_ms']:.2f}ms")
```

**基准测试结果**:

```python
{
    'name': 'my_benchmark',
    'iterations': 100,
    'min_ms': 5.2,
    'max_ms': 15.3,
    'avg_ms': 8.5,
    'median_ms': 8.2,
    'p95_ms': 12.1,
    'p99_ms': 14.8
}
```

## 📊 性能仪表板

### PerformanceDashboard

**功能**: 生成综合性能报告和可视化

**使用方法**:

```python
from code_rag.observability.performance_monitor import (
    PerformanceDashboard
)

dashboard = PerformanceDashboard(monitor, resource_monitor, cache)
dashboard.print_dashboard()

# 获取JSON报告
report = dashboard.generate_report()
```

**报告内容**:

```python
{
    'timestamp': '2026-05-16T10:30:00',
    'performance': {
        'total_requests': 1000,
        'total_errors': 5,
        'error_rate': 0.005,
        'operations': {...}
    },
    'resources': {
        'memory_mb': {...},
        'cpu_percent': {...}
    },
    'cache': {
        'size': 128,
        'hit_rate': 0.85
    },
    'summary': {
        'status': 'healthy',
        'issues': [],
        'recommendations': []
    }
}
```

## 🔧 性能优化建议

### PerformanceOptimizer

**功能**: 分析性能数据并提供优化建议

**使用方法**:

```python
from code_rag.observability.performance_monitor import PerformanceOptimizer

optimizer = PerformanceOptimizer(monitor, cache)

# 添加自定义优化规则
optimizer.add_rule(
    condition=lambda stats: stats['error_rate'] > 0.1,
    action=lambda stats: print("高错误率警告!")
)

suggestions = optimizer.analyze_and_optimize()
```

## ✅ 验收标准

### 性能目标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 查询响应时间 | < 200ms | P95 |
| 缓存命中率 | > 60% | 目标80% |
| 内存占用 | < 500MB | 正常运行 |
| 错误率 | < 5% | 目标<1% |

### 功能完整性

| 功能 | 状态 | 测试率 |
|------|------|--------|
| 性能指标收集 | ✅ 完成 | 100% |
| 资源监控 | ✅ 完成 | 100% |
| LRU缓存 | ✅ 完成 | 100% |
| 基准测试 | ✅ 完成 | 100% |
| 性能仪表板 | ✅ 完成 | 100% |
| 优化建议 | ✅ 完成 | 100% |

## 🎯 使用场景

### 1. API性能监控

```python
from code_rag.observability.performance_monitor import timed_operation

monitor = PerformanceMonitor()

@timed_operation(monitor, "api_search")
def search_api(query):
    # 搜索逻辑
    return results
```

### 2. 缓存热门查询

```python
from code_rag.observability.performance_monitor import cached_operation

cache = LRUCache(max_size=1000, ttl_seconds=1800)

@cached_operation(cache)
def search_code(query):
    # 搜索逻辑
    return results
```

### 3. 持续性能监控

```python
import schedule
from code_rag.observability.performance_monitor import PerformanceDashboard

def monitor_performance():
    dashboard = PerformanceDashboard(monitor, resource_monitor, cache)
    report = dashboard.generate_report()
    
    if report['summary']['status'] != 'healthy':
        alert_team(report)

schedule.every().hour.do(monitor_performance)
```

## 🔍 故障排查

### 问题: 性能监控数据为空

**原因**: 未正确调用 `record_metric()`

**解决**: 确保在操作完成后调用:
```python
monitor.record_metric("operation", start_time, end_time, success=True)
```

### 问题: 缓存命中率过低

**原因**: TTL设置过短或缓存key不唯一

**解决**: 
- 增加 `ttl_seconds`
- 使用更精确的缓存key

### 问题: 资源监控返回None

**原因**: psutil未安装

**解决**: 安装psutil:
```bash
pip install psutil
```

## 📚 相关文档

- [主项目README](../README.md)
- [技术路线图](./ROADMAP_v18.md)
- [测试文档](./V18_TESTING.md)
- [API文档](./API_DOCUMENTATION.md)

## 🔄 更新日志

### v18.0 (2026-05-16)

- ✨ 实现完整的性能监控系统
- ✨ 实现LRU缓存机制
- ✨ 实现基准测试工具
- ✨ 实现性能仪表板
- ✨ 提供优化建议功能

---

**版本**: v18.0  
**创建日期**: 2026-05-16  
**维护者**: Code RAG 团队
