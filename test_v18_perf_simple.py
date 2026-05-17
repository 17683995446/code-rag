#!/usr/bin/env python3
"""精简版性能监控测试"""

import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*80)
print("🎯 Code RAG v18.0 - 性能监控测试")
print("="*80)

from code_rag.observability.performance_monitor import (
    PerformanceMonitor, LRUCache, timed_operation, 
    ResourceMonitor, PerformanceDashboard
)

print("\n📊 测试1: 性能监控器")
monitor = PerformanceMonitor()
for i in range(3):
    start = time.time()
    time.sleep(0.02)
    monitor.record_metric("test_op", start, time.time(), True)
stats = monitor.get_operation_stats("test_op")
print(f"✓ 操作统计: {stats['count']}次, 平均{stats['avg_duration_ms']:.2f}ms")

print("\n💾 测试2: LRU缓存")
cache = LRUCache(max_size=5, ttl_seconds=2)
for i in range(3):
    cache.set(f"key{i}", f"value{i}")
val = cache.get("key0")
print(f"✓ 缓存操作: {cache.get_stats()['size']}项, 命中率: {cache.get_stats()['hit_rate']:.2%}")

print("\n⏱️ 测试3: 计时装饰器")
@timed_operation(monitor, "decorated")
def sample():
    return 42
result = sample()
stats2 = monitor.get_operation_stats("decorated")
print(f"✓ 装饰器: 结果={result}, 耗时={stats2['avg_duration_ms']:.2f}ms")

print("\n🖥️ 测试4: 资源监控")
res_mon = ResourceMonitor()
usage = res_mon.record_usage()
print(f"✓ 资源: 内存={usage.memory_mb:.2f}MB" if usage.memory_mb else "✓ 资源: N/A")

print("\n📈 测试5: 性能仪表板")
dashboard = PerformanceDashboard(monitor, res_mon, cache)
report = dashboard.generate_report()
print(f"✓ 报告: 请求={report['performance']['total_requests']}, 缓存命中={report['cache']['hit_rate']:.2%}")

print("\n" + "="*80)
print("✅ 所有测试完成!")
print("="*80)
