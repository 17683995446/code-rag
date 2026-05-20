#!/usr/bin/env python3
"""
快速验证版本 - 测试v7.1核心功能（跳过长时间测试）
"""
import sys
import os
import time
import random
import json
import threading
import uuid
import tracemalloc
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kg_memory_v7_optimized import MemorySystemV7Optimized, NodeType, EdgeType


def test_basic_performance():
    """测试基本性能"""
    print("=" * 80)
    print("测试1：基本性能测试")
    print("=" * 80)
    
    memory = MemorySystemV7Optimized()
    
    # 节点添加
    print("  添加10,000节点...")
    start = time.time()
    for i in range(10000):
        memory.remember(f"node_{i}", node_type=NodeType.ENTITY)
    node_time = time.time() - start
    print(f"    ✅ 10,000节点: {node_time:.2f}秒 ({10000/node_time:.0f} 节点/秒)")
    
    # 边添加
    print("  添加10,000边...")
    start = time.time()
    for i in range(10000):
        memory.connect(f"node_{i}", f"node_{(i+1)%10000}")
    edge_time = time.time() - start
    print(f"    ✅ 10,000边: {edge_time:.2f}秒 ({10000/edge_time:.0f} 边/秒)")
    
    # 查询
    print("  查询测试...")
    start = time.time()
    for i in range(10000):
        memory.recall(f"node_{i}")
    query_time = time.time() - start
    print(f"    ✅ 10,000查询: {query_time:.2f}秒 ({10000/query_time:.0f} 查询/秒)")
    
    stats = memory.get_statistics()
    print(f"    最终状态: 节点 {stats['nodes']:,}, 边 {stats['edges']:,}")
    
    return True


def test_medium_concurrency():
    """测试中等并发"""
    print("\n" + "=" * 80)
    print("测试2：中等并发测试（100线程）")
    print("=" * 80)
    
    memory = MemorySystemV7Optimized()
    
    # 准备基础数据
    print("  准备基础数据...")
    for i in range(5000):
        memory.remember(f"base_{i}", node_type=NodeType.ENTITY)
    
    num_threads = 100
    ops_per_thread = 500
    
    print(f"  启动 {num_threads} 线程，每线程 {ops_per_thread} 操作...")
    
    errors = [0]
    completed = [0]
    errors_lock = threading.Lock()
    completed_lock = threading.Lock()
    
    def worker(worker_id):
        for i in range(ops_per_thread):
            try:
                op = random.randint(0, 5)
                
                if op == 0:
                    memory.remember(f"worker_{worker_id}_{i}", node_type=NodeType.ENTITY)
                elif op == 1:
                    memory.connect(f"base_{random.randint(0, 4999)}", f"base_{random.randint(0, 4999)}")
                elif op == 2:
                    memory.recall(f"base_{random.randint(0, 4999)}")
                elif op == 3:
                    memory.semantic_search("base")
                elif op == 4:
                    memory.recommend_connections(f"base_{random.randint(0, 4999)}")
                elif op == 5:
                    memory.infer(f"base_{random.randint(0, 4999)}", max_depth=3)
                
                with completed_lock:
                    completed[0] += 1
                
            except Exception as e:
                with errors_lock:
                    errors[0] += 1
    
    start_time = time.time()
    threads = []
    
    for i in range(num_threads):
        t = threading.Thread(target=worker, args=(i,))
        t.daemon = True
        t.start()
        threads.append(t)
    
    # 监控进度
    last_check = 0
    while True:
        time.sleep(3)
        elapsed = time.time() - start_time
        with completed_lock:
            done = completed[0]
        
        total_ops = num_threads * ops_per_thread
        if done >= total_ops:
            break
        
        if elapsed - last_check >= 15:
            progress = (done / total_ops) * 100
            rate = done / elapsed if elapsed > 0 else 0
            print(f"    进度: {done:,}/{total_ops:,} ({progress:.1f}%) 速率: {rate:.0f} ops/s")
            last_check = elapsed
    
    for t in threads:
        t.join()
    
    total_time = time.time() - start_time
    stats = memory.get_statistics()
    
    print(f"    ✅ 完成！总操作: {completed[0]:,}, 耗时: {total_time:.2f}秒")
    print(f"    速率: {(completed[0]/total_time):.0f} ops/s")
    print(f"    错误数: {errors[0]}")
    print(f"    最终节点: {stats['nodes']:,}, 边: {stats['edges']:,}")
    
    return errors[0] == 0


def test_extreme_edge_cases():
    """测试极端边缘情况"""
    print("\n" + "=" * 80)
    print("测试3：极端边缘情况测试")
    print("=" * 80)
    
    memory = MemorySystemV7Optimized()
    
    tests = [
        ("空字符串标签", lambda: memory.remember("")),
        ("None查询", lambda: memory.recall(None)),
        ("超长标签(10000字符)", lambda: memory.remember("x" * 10000)),
        ("特殊字符", lambda: memory.remember("emoji_🚀")),
        ("中文标签", lambda: memory.remember("中文测试")),
        ("重复连接", lambda: (
            memory.remember("node_a"),
            memory.remember("node_b"),
            [memory.connect("node_a", "node_b") for _ in range(100)]
        )),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            print(f"  ✅ {test_name}: 通过")
            passed += 1
        except Exception as e:
            print(f"  ⚠️  {test_name}: 失败 - {e}")
            failed += 1
    
    print(f"  结果: {passed} 通过, {failed} 失败")
    return failed == 0


def test_memory_leak():
    """测试内存泄漏"""
    print("\n" + "=" * 80)
    print("测试4：内存泄漏测试")
    print("=" * 80)
    
    tracemalloc.start()
    
    memory = MemorySystemV7Optimized()
    
    initial_size = sum(stat.size for stat in tracemalloc.take_snapshot().statistics('lineno'))
    print(f"  初始内存: {initial_size / 1024 / 1024:.2f} MB")
    
    # 添加大量节点
    print("  添加50,000节点...")
    for i in range(50000):
        memory.remember(f"mem_test_{i}", node_type=NodeType.ENTITY)
        if i % 10000 == 0 and i > 0:
            current_mb = sum(stat.size for stat in tracemalloc.take_snapshot().statistics('lineno')) / 1024 / 1024
            print(f"    进度: {i}/50000 ({current_mb:.2f} MB)")
    
    import gc
    gc.collect()
    
    final_size = sum(stat.size for stat in tracemalloc.take_snapshot().statistics('lineno'))
    final_mb = final_size / 1024 / 1024
    memory_growth = (final_size - initial_size) / 1024 / 1024
    growth_per_op = memory_growth / 50000 * 1024
    
    print(f"  最终内存: {final_mb:.2f} MB")
    print(f"  内存增长: {memory_growth:.2f} MB")
    print(f"  每千操作增长: {growth_per_op:.4f} KB")
    
    has_leak = growth_per_op > 1.0
    
    if has_leak:
        print(f"  ⚠️  可能存在内存泄漏")
    else:
        print(f"  ✅ 内存增长正常，无泄漏")
    
    tracemalloc.stop()
    
    return not has_leak


def test_persistence():
    """测试持久化"""
    print("\n" + "=" * 80)
    print("测试5：持久化测试")
    print("=" * 80)
    
    import tempfile
    
    memory = MemorySystemV7Optimized()
    
    # 添加数据
    print("  添加测试数据...")
    for i in range(1000):
        memory.remember(f"persist_{i}", node_type=NodeType.ENTITY)
    
    for i in range(500):
        memory.connect(f"persist_{i}", f"persist_{(i+1)%1000}")
    
    initial_stats = memory.get_statistics()
    print(f"    初始状态: 节点 {initial_stats['nodes']}, 边 {initial_stats['edges']}")
    
    # 保存
    print("  保存...")
    temp_path = os.path.join(tempfile.mkdtemp(), "test_persist.json")
    memory.save(temp_path)
    
    # 重新加载
    print("  重新加载...")
    new_memory = MemorySystemV7Optimized()
    new_memory.load(temp_path)
    
    loaded_stats = new_memory.get_statistics()
    print(f"    加载后: 节点 {loaded_stats['nodes']}, 边 {loaded_stats['edges']}")
    
    nodes_match = initial_stats['nodes'] == loaded_stats['nodes']
    edges_match = initial_stats['edges'] == loaded_stats['edges']
    
    if nodes_match and edges_match:
        print(f"  ✅ 持久化一致性完美！")
        return True
    else:
        print(f"  ⚠️  持久化不一致")
        return False


def main():
    print("\n" + "=" * 80)
    print("🚀 知识图谱记忆系统 v7.1 - 快速验证测试")
    print("=" * 80)
    
    start_time = time.time()
    
    tests = [
        ("基本性能测试", test_basic_performance),
        ("中等并发测试", test_medium_concurrency),
        ("极端边缘情况", test_extreme_edge_cases),
        ("内存泄漏测试", test_memory_leak),
        ("持久化测试", test_persistence),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n  ❌ {test_name} 异常: {e}")
            results.append((test_name, False))
    
    total_time = time.time() - start_time
    
    print("\n" + "=" * 80)
    print("📊 测试结果总结")
    print("=" * 80)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    print(f"\n 通过率: {passed}/{total} ({100*passed/total:.0f}%)")
    print(f" 总耗时: {total_time:.1f}秒")
    
    # 保存报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_time": total_time,
        "passed": passed,
        "total": total,
        "results": [{"name": name, "passed": success} for name, success in results]
    }
    
    report_path = os.path.join(os.path.dirname(__file__), "v7_quick_verification_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n报告保存: {report_path}")
    
    print("=" * 80)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
