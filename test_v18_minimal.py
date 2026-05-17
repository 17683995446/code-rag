#!/usr/bin/env python3
"""最简版性能测试"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*80)
print("🎯 性能监控核心测试")
print("="*80)

from code_rag.observability.performance_monitor import (
    PerformanceMonitor, LRUCache
)

print("\n1. 性能监控器...")
monitor = PerformanceMonitor()
start = time.time()
monitor.record_metric("op1", start, time.time())
print("✓ 记录操作")

stats = monitor.get_operation_stats("op1")
print(f"✓ 统计: {stats}")

print("\n2. LRU缓存...")
cache = LRUCache(max_size=3)
cache.set("a", 1)
val = cache.get("a")
print(f"✓ 缓存: {val}, 大小: {cache.get_stats()['size']}")

print("\n" + "="*80)
print("✅ 完成!")
print("="*80)
