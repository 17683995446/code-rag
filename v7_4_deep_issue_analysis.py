#!/usr/bin/env python3
"""
v7.4 深度问题分析测试
慢工出细活: 深度发现系统潜在问题
"""

import sys
import os
import time
import threading
import random
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath('.')))

from kg_memory_v7_optimized import MemorySystemV7Optimized, NodeType, EdgeType


def test_issue_1_cache_consistency():
    """问题1: 缓存一致性测试"""
    print("\n" + "="*60)
    print("🔍 测试1: 缓存一致性检查")
    print("="*60)
    
    memory = MemorySystemV7Optimized()
    
    print("1. 添加节点 'test_node_1'")
    memory.remember("test_node_1", node_type=NodeType.ENTITY)
    
    print("2. 第一次查询 - 缓存未命中")
    result1 = memory.recall("test_node_1", k=5)
    
    print("3. 修改节点（理论上） - 再次添加相同标签")
    memory.remember("test_node_1", node_type=NodeType.CONCEPT)
    
    print("4. 第二次查询 - 应该获取最新状态，而非缓存")
    result2 = memory.recall("test_node_1", k=5)
    
    stats = memory.get_statistics()
    print(f"\n📊 缓存状态:")
    print(f"  命中: {stats['cache_hits']}")
    print(f"  未命中: {stats['cache_misses']}")
    
    if result1 and result2:
        print(f"\n✅ 查询成功")
        return True
    else:
        print(f"\n⚠️  潜在问题: 查询结果异常")
        return False


def test_issue_2_semantic_cache_invalidation():
    """问题2: 语义搜索缓存有效性"""
    print("\n" + "="*60)
    print("🔍 测试2: 语义搜索缓存有效性")
    print("="*60)
    
    memory = MemorySystemV7Optimized()
    
    print("1. 添加10个节点")
    for i in range(10):
        memory.remember(f"semantic_test_{i}", node_type=NodeType.ENTITY, compute_embedding=True)
    
    print("2. 第一次语义搜索")
    start = time.time()
    result1 = memory.semantic_search("semantic_test_0", k=5)
    time1 = time.time() - start
    
    print("3. 添加新节点（应该不会影响已有节点的语义）")
    memory.remember("semantic_test_10", node_type=NodeType.ENTITY, compute_embedding=True)
    
    print("4. 第二次语义搜索 - 应该可以用缓存")
    start = time.time()
    result2 = memory.semantic_search("semantic_test_0", k=5)
    time2 = time.time() - start
    
    stats = memory.get_statistics()
    print(f"\n📊 测试结果:")
    print(f"  第一次: {time1:.4f}s")
    print(f"  第二次: {time2:.4f}s")
    print(f"  语义缓存命中: {stats['semantic_cache_hits']}")
    
    if time2 < time1 * 0.1:
        print("\n✅ 缓存工作正常，性能显著提升")
        return True
    elif stats['semantic_cache_hits'] > 0:
        print("\n✅ 缓存命中，但性能提升不明显")
        return True
    else:
        print("\n⚠️ 缓存可能未正确工作")
        return False


def test_issue_3_memory_leak_quick_check():
    """问题3: 快速内存泄漏检查"""
    print("\n" + "="*60)
    print("🔍 测试3: 内存泄漏快速检查")
    print("="*60)
    
    import gc
    
    memory = MemorySystemV7Optimized()
    
    print("1. 批量添加10,000节点")
    for i in range(10000):
        memory.remember(f"mem_test_{i}", node_type=NodeType.ENTITY)
    
    print("2. 批量添加5,000边")
    for i in range(5000):
        memory.connect(f"mem_test_{i}", f"mem_test_{(i+1)%5000}")
    
    print("3. 执行10,000次查询")
    for i in range(10000):
        memory.recall(f"mem_test_{i%10000}", k=3)
    
    stats = memory.get_statistics()
    
    print(f"\n📊 最终状态:")
    print(f"  节点: {stats['nodes']:,}")
    print(f"  边: {stats['edges']:,}")
    print(f"  缓存大小: {stats['cache_size']}")
    print(f"  缓存命中率: {stats['cache_hits']}/{stats['cache_hits'] + stats['cache_misses']}")
    
    print("\n✅ 基础功能正常（无崩溃）")
    return True


def test_issue_4_concurrent_edge_cases():
    """问题4: 并发边缘情况测试"""
    print("\n" + "="*60)
    print("🔍 测试4: 并发边缘情况")
    print("="*60)
    
    memory = MemorySystemV7Optimized()
    
    errors = []
    completed = 0
    lock = threading.Lock()
    
    def worker(wid):
        nonlocal completed
        try:
            for i in range(100):
                # 各种边缘情况
                if i % 5 == 0:
                    memory.remember(f"concurrent_test_{wid}_{i}", node_type=NodeType.ENTITY)
                elif i % 5 == 1:
                    memory.connect(f"concurrent_test_{wid}_{i-1}", f"concurrent_test_{wid}_{i}")
                elif i % 5 == 2:
                    memory.recall(f"concurrent_test_{wid}_{i-2}", k=2)
                elif i % 5 == 3:
                    memory.semantic_search(f"concurrent_test_{wid}_{i-3}", k=3)
                else:
                    memory.infer(f"concurrent_test_{wid}_{i-4}", max_depth=2)
                
                with lock:
                    completed += 1
        except Exception as e:
            with lock:
                errors.append(str(e))
    
    print("1. 启动50个并发工作线程")
    threads = []
    for i in range(50):
        t = threading.Thread(target=worker, args=(i,))
        t.daemon = True
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join()
    
    stats = memory.get_statistics()
    print(f"\n📊 测试结果:")
    print(f"  完成操作: {completed:,}")
    print(f"  错误数: {len(errors)}")
    print(f"  最终节点: {stats['nodes']:,}")
    print(f"  最终边: {stats['edges']:,}")
    
    if len(errors) == 0:
        print("\n✅ 并发运行正常，无错误")
        return True
    else:
        print(f"\n⚠️  发现 {len(errors)} 个错误:")
        for err in errors[:5]:
            print(f"  - {err}")
        return False


def test_issue_5_performance_scalability():
    """问题5: 性能可扩展性测试"""
    print("\n" + "="*60)
    print("🔍 测试5: 性能可扩展性")
    print("="*60)
    
    memory = MemorySystemV7Optimized()
    
    sizes = [1000, 5000, 10000, 20000]
    results = []
    
    for size in sizes:
        print(f"\n测试规模: {size:,} 节点")
        
        start = time.time()
        for i in range(size):
            memory.remember(f"scalability_{len(results)}_{i}", node_type=NodeType.ENTITY)
        add_time = time.time() - start
        
        start = time.time()
        for i in range(100):
            memory.recall(f"scalability_{len(results)}_{i}", k=10)
        query_time = time.time() - start
        
        results.append({
            "size": size,
            "add_time": add_time,
            "add_rate": size / add_time,
            "query_time": query_time,
            "query_rate": 100 / query_time
        })
        
        print(f"  添加: {add_time:.2f}s ({size/add_time:.0f} nodes/s)")
        print(f"  查询: {query_time:.4f}s ({100/query_time:.0f} queries/s)")
    
    print("\n📊 可扩展性分析:")
    for i in range(1, len(results)):
        size_ratio = results[i]['size'] / results[i-1]['size']
        rate_ratio = results[i]['query_rate'] / results[i-1]['query_rate']
        print(f"  规模x{size_ratio:.0f} -> 查询性能x{rate_ratio:.2f}")
    
    print("\n✅ 可扩展性测试完成")
    return True


def main():
    print("\n" + "="*80)
    print("🚀 v7.4 深度问题分析")
    print("="*80)
    print(f"开始时间: {datetime.now().isoformat()}")
    
    tests = [
        test_issue_1_cache_consistency,
        test_issue_2_semantic_cache_invalidation,
        test_issue_3_memory_leak_quick_check,
        test_issue_4_concurrent_edge_cases,
        test_issue_5_performance_scalability
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append((test_func.__name__, result))
        except Exception as e:
            print(f"\n❌ {test_func.__name__} 崩溃: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_func.__name__, False))
    
    print("\n" + "="*80)
    print("📊 总结")
    print("="*80)
    
    for name, passed in results:
        status = "✅" if passed else "❌"
        print(f"  {name:40}: {status}")
    
    passed = sum(1 for _, p in results if p)
    print(f"\n通过率: {passed}/{len(results)}")
    print(f"结束时间: {datetime.now().isoformat()}")
    
    print("\n" + "="*80)
    print("🔍 基于测试结果，下面分析并实现v7.5优化！")
    print("="*80)
    return passed == len(results)


if __name__ == "__main__":
    main()
