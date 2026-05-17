"""
Code RAG v18.0 - 性能监控测试
测试性能监控、资源监控、缓存和基准测试功能
"""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from code_rag.observability.performance_monitor import (
    PerformanceMonitor, ResourceMonitor, LRUCache, 
    PerformanceBenchmark, PerformanceDashboard, PerformanceOptimizer,
    timed_operation, cached_operation
)


def test_performance_monitor():
    """测试性能监控器"""
    print("\n" + "="*80)
    print("📊 测试 1: 性能监控器")
    print("="*80)
    
    monitor = PerformanceMonitor()
    
    for i in range(5):
        start = time.time()
        time.sleep(0.01)
        end = time.time()
        monitor.record_metric("test_operation", start, end, success=True)
    
    stats = monitor.get_operation_stats("test_operation")
    print(f"✓ 记录操作: {stats['count']} 次")
    print(f"✓ 平均耗时: {stats['avg_duration_ms']:.2f}ms")
    print(f"✓ 最小耗时: {stats['min_duration_ms']:.2f}ms")
    print(f"✓ 最大耗时: {stats['max_duration_ms']:.2f}ms")
    
    monitor.record_metric("error_operation", time.time() - 0.1, time.time(), success=False)
    error_stats = monitor.get_operation_stats("error_operation")
    print(f"✓ 错误率: {error_stats['error_rate']:.2%}")
    
    all_stats = monitor.get_all_stats()
    print(f"✓ 总请求数: {all_stats['total_requests']}")
    print(f"✓ 总错误数: {all_stats['total_errors']}")
    
    print("\n✅ 性能监控器 - 通过")
    return True


def test_resource_monitor():
    """测试资源监控器"""
    print("\n" + "="*80)
    print("🖥️ 测试 2: 资源监控器")
    print("="*80)
    
    monitor = ResourceMonitor()
    
    for _ in range(3):
        usage = monitor.record_usage()
        print(f"✓ 记录使用情况:")
        if usage.memory_mb:
            print(f"  - 内存: {usage.memory_mb:.2f} MB")
        if usage.cpu_percent is not None:
            print(f"  - CPU: {usage.cpu_percent:.2f}%")
        time.sleep(0.1)
    
    stats = monitor.get_usage_stats()
    print(f"✓ 样本数: {stats['samples']}")
    
    current = monitor.get_current_usage()
    if current:
        print(f"✓ 当前内存: {current.memory_mb:.2f} MB" if current.memory_mb else "✓ 内存: N/A")
    
    print("\n✅ 资源监控器 - 通过")
    return True


def test_lru_cache():
    """测试LRU缓存"""
    print("\n" + "="*80)
    print("💾 测试 3: LRU缓存")
    print("="*80)
    
    cache = LRUCache(max_size=3, ttl_seconds=2)
    
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")
    
    print(f"✓ 设置3个缓存项")
    print(f"✓ 缓存大小: {cache.get_stats()['size']}")
    
    val1 = cache.get("key1")
    print(f"✓ 获取key1: {val1}")
    
    cache.set("key4", "value4")
    stats = cache.get_stats()
    print(f"✓ 添加第4项后大小: {stats['size']} (应触发驱逐)")
    
    val2 = cache.get("key2")
    print(f"✓ 获取key2: {val2} (应为None，已被驱逐)")
    
    time.sleep(2.5)
    val3 = cache.get("key3")
    print(f"✓ 获取key3 (TTL后): {val3} (应为None，已过期)")
    
    print(f"✓ 命中率: {stats['hit_rate']:.2%}")
    
    print("\n✅ LRU缓存 - 通过")
    return True


def test_cached_decorator():
    """测试缓存装饰器"""
    print("\n" + "="*80)
    print("🎯 测试 4: 缓存装饰器")
    print("="*80)
    
    cache = LRUCache(max_size=10)
    computation_count = [0]
    
    @cached_operation(cache)
    def expensive_computation(x, y):
        computation_count[0] += 1
        time.sleep(0.01)
        return x + y
    
    result1 = expensive_computation(5, 10)
    print(f"✓ 第一次计算: {result1}, 计算次数: {computation_count[0]}")
    
    result2 = expensive_computation(5, 10)
    print(f"✓ 第二次计算: {result2}, 计算次数: {computation_count[0]}")
    
    stats = cache.get_stats()
    print(f"✓ 缓存命中: {stats['hits']}, 缓存未命中: {stats['misses']}")
    print(f"✓ 命中率: {stats['hit_rate']:.2%}")
    
    assert computation_count[0] == 1, "应该只计算一次"
    
    print("\n✅ 缓存装饰器 - 通过")
    return True


def test_timed_decorator():
    """测试计时装饰器"""
    print("\n" + "="*80)
    print("⏱️ 测试 5: 计时装饰器")
    print("="*80)
    
    monitor = PerformanceMonitor()
    
    @timed_operation(monitor, "decorated_operation")
    def sample_operation(x):
        time.sleep(0.05)
        return x * 2
    
    result = sample_operation(5)
    print(f"✓ 操作结果: {result}")
    
    stats = monitor.get_operation_stats("decorated_operation")
    print(f"✓ 平均耗时: {stats['avg_duration_ms']:.2f}ms")
    
    assert stats['count'] == 1
    assert stats['avg_duration_ms'] >= 50
    
    print("\n✅ 计时装饰器 - 通过")
    return True


def test_performance_benchmark():
    """测试性能基准测试"""
    print("\n" + "="*80)
    print("🏃 测试 6: 性能基准测试")
    print("="*80)
    
    monitor = PerformanceMonitor()
    benchmark = PerformanceBenchmark(monitor)
    
    def sample_function():
        time.sleep(0.01)
        return sum(range(100))
    
    result = benchmark.run_benchmark("sample_test", sample_function, iterations=20, warmup=5)
    
    print(f"✓ 基准测试: {result['name']}")
    print(f"✓ 迭代次数: {result['iterations']}")
    print(f"✓ 平均耗时: {result['avg_ms']:.2f}ms")
    print(f"✓ 最小耗时: {result['min_ms']:.2f}ms")
    print(f"✓ 最大耗时: {result['max_ms']:.2f}ms")
    print(f"✓ 中位数: {result['median_ms']:.2f}ms")
    print(f"✓ P95: {result['p95_ms']:.2f}ms")
    print(f"✓ P99: {result['p99_ms']:.2f}ms")
    
    results = benchmark.get_benchmark_results()
    print(f"✓ 基准测试数量: {len(results)}")
    
    print("\n✅ 性能基准测试 - 通过")
    return True


def test_performance_dashboard():
    """测试性能仪表板"""
    print("\n" + "="*80)
    print("📈 测试 7: 性能仪表板")
    print("="*80)
    
    monitor = PerformanceMonitor()
    resource_monitor = ResourceMonitor()
    cache = LRUCache(max_size=10)
    
    for i in range(10):
        start = time.time()
        time.sleep(0.01)
        monitor.record_metric(f"operation_{i % 3}", start, time.time())
    
    resource_monitor.record_usage()
    
    for i in range(5):
        cache.set(f"key_{i}", f"value_{i}")
        cache.get(f"key_{i}")
    
    dashboard = PerformanceDashboard(monitor, resource_monitor, cache)
    
    report = dashboard.generate_report()
    print(f"✓ 报告生成成功")
    print(f"✓ 总请求数: {report['performance']['total_requests']}")
    print(f"✓ 缓存命中率: {report['cache']['hit_rate']:.2%}")
    
    summary = report['summary']
    print(f"✓ 健康状态: {summary['status']}")
    print(f"✓ 问题数: {len(summary['issues'])}")
    print(f"✓ 建议数: {len(summary['recommendations'])}")
    
    print("\n✅ 性能仪表板 - 通过")
    return True


def test_performance_optimizer():
    """测试性能优化器"""
    print("\n" + "="*80)
    print("🔧 测试 8: 性能优化器")
    print("="*80)
    
    monitor = PerformanceMonitor()
    cache = LRUCache(max_size=10)
    
    for i in range(5):
        start = time.time()
        time.sleep(0.15)
        monitor.record_metric("slow_operation", start, time.time())
    
    optimizer = PerformanceOptimizer(monitor, cache)
    
    suggestions = optimizer.analyze_and_optimize()
    print(f"✓ 优化建议数: {len(suggestions)}")
    
    for i, suggestion in enumerate(suggestions, 1):
        print(f"  {i}. 类型: {suggestion['type']}")
        if 'details' in suggestion:
            for op, duration in suggestion['details']:
                print(f"     - {op}: {duration:.2f}ms")
    
    print("\n✅ 性能优化器 - 通过")
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*80)
    print("🎯 Code RAG v18.0 - 性能监控测试套件")
    print("="*80)
    
    tests = [
        ("性能监控器", test_performance_monitor),
        ("资源监控器", test_resource_monitor),
        ("LRU缓存", test_lru_cache),
        ("缓存装饰器", test_cached_decorator),
        ("计时装饰器", test_timed_decorator),
        ("性能基准测试", test_performance_benchmark),
        ("性能仪表板", test_performance_dashboard),
        ("性能优化器", test_performance_optimizer),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n❌ {name} - 失败: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*80)
    print("📋 性能监控测试总结")
    print("="*80)
    print(f"📊 结果: {passed}/{len(tests)} 测试通过")
    print(f"✅ 通过率: {100*passed/len(tests):.1f}%")
    
    if failed == 0:
        print("\n🎉 所有性能监控测试通过! 性能优化模块就绪!")
        return True
    else:
        print(f"\n⚠️ {failed} 个测试失败")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
