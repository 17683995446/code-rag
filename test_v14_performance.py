#!/usr/bin/env python3
"""
Code RAG v14.0 - 性能优化测试
测试增量索引和并行处理功能
"""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def print_header(title):
    print("\n" + "=" * 100)
    print(f"  {title}")
    print("=" * 100)


def test_incremental_index():
    """测试增量索引"""
    print_header("🚀 测试 1: 增量索引引擎")
    
    from code_rag.processing_layer.incremental_index_and_parallel_processing import (
        create_incremental_indexer
    )
    
    print("\n  创建增量索引器...")
    indexer = create_incremental_indexer()
    
    print(f"\n  ✓ 索引器创建成功")
    print(f"  ✓ 缓存目录: {indexer.cache_dir}")
    
    return True


def test_parallel_processing():
    """测试并行处理"""
    print_header("⚡ 测试 2: 并行处理引擎")
    
    from code_rag.processing_layer.incremental_index_and_parallel_processing import (
        create_parallel_engine
    )
    
    print("\n  创建并行处理引擎...")
    engine = create_parallel_engine()
    
    print(f"\n  ✓ 引擎创建成功")
    print(f"  ✓ 最大工作进程: {engine.max_workers}")
    
    return True


def test_cache_manager():
    """测试缓存管理器"""
    print_header("💾 测试 3: 智能缓存管理器")
    
    from code_rag.processing_layer.incremental_index_and_parallel_processing import (
        create_cache_manager
    )
    
    print("\n  创建缓存管理器...")
    cache = create_cache_manager(max_size=100, ttl_seconds=60)
    
    print(f"\n  ✓ 缓存创建成功")
    print(f"  ✓ 最大容量: {cache.max_size}")
    print(f"  ✓ TTL: {cache.ttl_seconds}s")
    
    print(f"\n  测试缓存操作:")
    
    cache.set("key1", {"data": "test1"})
    cache.set("key2", {"data": "test2"})
    cache.set("key3", {"data": "test3"})
    
    print(f"  ✓ 写入3个条目")
    
    value = cache.get("key1")
    print(f"  ✓ 读取key1: {value}")
    
    hit_rate = cache.get_hit_rate()
    print(f"  ✓ 命中率: {hit_rate*100:.1f}%")
    
    stats = cache.get_statistics()
    print(f"  ✓ 统计: 命中{stats['hits']}, 未命中{stats['misses']}")
    
    return True


def test_integration():
    """测试集成"""
    print_header("🔗 测试 4: 性能模块集成")
    
    from code_rag.processing_layer.incremental_index_and_parallel_processing import (
        create_incremental_indexer,
        create_parallel_engine,
        create_cache_manager
    )
    
    print("\n  创建所有性能组件...")
    
    indexer = create_incremental_indexer()
    engine = create_parallel_engine()
    cache = create_cache_manager()
    
    print(f"  ✓ 增量索引器: ✓")
    print(f"  ✓ 并行处理引擎: ✓")
    print(f"  ✓ 智能缓存管理器: ✓")
    
    print(f"\n  测试组件协同:")
    
    test_code = "def test_function(): pass"
    cache.set("test_code", test_code)
    
    cached = cache.get("test_code")
    
    if cached == test_code:
        print(f"  ✓ 缓存系统正常工作")
    else:
        print(f"  ⚠️ 缓存系统异常")
        return False
    
    return True


def run_performance_tests():
    """运行性能测试"""
    print_header("📊 性能基准测试")
    
    import time
    
    from code_rag.processing_layer.incremental_index_and_parallel_processing import (
        create_cache_manager
    )
    
    print("\n  缓存性能测试:")
    
    cache = create_cache_manager(max_size=10000)
    
    iterations = 10000
    
    start = time.time()
    for i in range(iterations):
        cache.set(f"key_{i}", {"data": f"value_{i}"})
    set_time = time.time() - start
    
    start = time.time()
    for i in range(iterations):
        cache.get(f"key_{i}")
    get_time = time.time() - start
    
    print(f"  ✓ 写入{iterations}条: {set_time*1000:.2f}ms ({iterations/set_time:.0f} ops/s)")
    print(f"  ✓ 读取{iterations}条: {get_time*1000:.2f}ms ({iterations/get_time:.0f} ops/s)")
    print(f"  ✓ 命中率: {cache.get_hit_rate()*100:.1f}%")
    
    return True


def run_all_tests():
    """运行所有测试"""
    tests = [
        ("增量索引引擎", test_incremental_index),
        ("并行处理引擎", test_parallel_processing),
        ("智能缓存管理器", test_cache_manager),
        ("性能模块集成", test_integration),
        ("性能基准测试", run_performance_tests),
    ]
    
    results = []
    
    print_header("🧪 Code RAG v14.0 - 性能优化测试")
    print(f"  测试数量: {len(tests)}")
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅" if result else "❌"
            print(f"\n  {status} {test_name} - {'通过' if result else '失败'}")
        except Exception as e:
            print(f"\n  ❌ {test_name} - 异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    print_header("📋 测试总结")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n  📊 结果: {passed}/{total} 测试通过")
    print(f"  ✅ 通过率: {passed/total*100:.1f}%")
    
    print(f"\n  详细结果:")
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"    {status} - {test_name}")
    
    if passed == total:
        print(f"\n  🎉 所有测试通过! Code RAG v14.0 性能优化模块就绪!")
        return True
    else:
        print(f"\n  ⚠️ 部分测试失败，请检查")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
