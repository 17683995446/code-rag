#!/usr/bin/env python3
"""简单性能测试"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*80)
print("🎯 简单性能监控测试")
print("="*80)

from code_rag.observability.performance_monitor import (
    PerformanceMonitor, LRUCache, timed_operation
)

print("\n1. 测试性能监控器...")
monitor = PerformanceMonitor()

for i in range(3):
    start = time.time()
    time.sleep(0.01)
    end = time.time()
    monitor.record_metric("test", start, end, True)
    print(f"  ✓ 记录 {i+1}/3")

stats = monitor.get_operation_stats("test")
print(f"  ✓ 平均耗时: {stats['avg_duration_ms']:.2f}ms")

print("\n2. 测试LRU缓存...")
cache = LRUCache(max_size=5)

cache.set("a", 1)
cache.set("b", 2)
print(f"  ✓ 缓存大小: {cache.get_stats()['size']}")

val = cache.get("a")
print(f"  ✓ 获取值: {val}")

print("\n3. 测试计时装饰器...")
@timed_operation(monitor, "decorated")
def sample():
    time.sleep(0.05)
    return 42

result = sample()
print(f"  ✓ 结果: {result}")

stats2 = monitor.get_operation_stats("decorated")
print(f"  ✓ 耗时: {stats2['avg_duration_ms']:.2f}ms")

print("\n" + "="*80)
print("✅ 简单测试完成!")
print("="*80)
