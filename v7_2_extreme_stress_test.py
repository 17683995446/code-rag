#!/usr/bin/env python3
"""
v7.2 超大规模压力测试 - 发现极端场景问题
测试目标：在超大规模数据和极端并发下发现问题
"""
import sys
import os
import time
import threading
import random
import tracemalloc
import gc
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kg_memory_v7_optimized import MemorySystemV7Optimized, NodeType, EdgeType


def test_million_scale():
    """百万级规模测试"""
    print("\n" + "=" * 80)
    print("🔍 测试1：百万级规模测试")
    print("=" * 80)
    
    memory = MemorySystemV7Optimized()
    
    print("  添加100,000节点...")
    start = time.time()
    for i in range(100000):
        memory.remember(f"mega_node_{i}", node_type=NodeType.ENTITY)
        if i % 10000 == 0 and i > 0:
            elapsed = time.time() - start
            rate = i / elapsed
            print(f"    {i}: {rate:.0f} 节点/秒")
    node_time = time.time() - start
    print(f"    ✅ 100,000节点完成: {node_time:.2f}秒 ({100000/node_time:.0f} 节点/秒)")
    
    print("  添加50,000边...")
    start = time.time()
    edges_added = 0
    for i in range(50000):
        if memory.connect(f"mega_node_{i}", f"mega_node_{(i+1)%50000}"):
            edges_added += 1
    edge_time = time.time() - start
    print(f"    ✅ {edges_added}边完成: {edge_time:.2f}秒 ({edges_added/edge_time:.0f} 边/秒)")
    
    stats = memory.get_statistics()
    print(f"    最终节点: {stats['nodes']:,}, 边: {stats['edges']:,}")
    
    return stats['nodes'] >= 100000


def test_extreme_concurrency():
    """极端并发测试"""
    print("\n" + "=" * 80)
    print("🔍 测试2：极端并发测试（500线程）")
    print("=" * 80)
    
    memory = MemorySystemV7Optimized()
    
    print("  准备基础数据...")
    for i in range(10000):
        memory.remember(f"extreme_base_{i}", node_type=NodeType.ENTITY)
    
    num_threads = 500
    ops_per_thread = 200
    
    print(f"  启动 {num_threads} 线程，每线程 {ops_per_thread} 操作...")
    print(f"  总操作数: {num_threads * ops_per_thread:,}")
    
    errors = [0]
    completed = [0]
    errors_lock = threading.Lock()
    completed_lock = threading.Lock()
    
    def worker(worker_id):
        for i in range(ops_per_thread):
            try:
                op = random.randint(0, 5)
                
                if op == 0:
                    memory.remember(f"extreme_{worker_id}_{i}", node_type=NodeType.ENTITY)
                elif op == 1:
                    memory.connect(f"extreme_base_{random.randint(0, 9999)}", 
                                 f"extreme_base_{random.randint(0, 9999)}")
                elif op == 2:
                    memory.recall(f"extreme_base_{random.randint(0, 9999)}")
                elif op == 3:
                    memory.semantic_search("extreme_base")
                elif op == 4:
                    memory.recommend_connections(f"extreme_base_{random.randint(0, 9999)}")
                elif op == 5:
                    memory.infer(f"extreme_base_{random.randint(0, 9999)}", max_depth=3)
                
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
    
    last_check = 0
    while True:
        time.sleep(5)
        elapsed = time.time() - start_time
        with completed_lock:
            done = completed[0]
        
        total_ops = num_threads * ops_per_thread
        if done >= total_ops:
            break
        
        if elapsed - last_check >= 20:
            progress = (done / total_ops) * 100
            rate = done / elapsed if elapsed > 0 else 0
            print(f"    进度: {done:,}/{total_ops:,} ({progress:.1f}%) 速率: {rate:.0f} ops/s")
            last_check = elapsed
    
    for t in threads:
        t.join()
    
    total_time = time.time() - start_time
    stats = memory.get_statistics()
    
    print(f"    ✅ 完成！")
    print(f"    总操作: {completed[0]:,}, 耗时: {total_time:.2f}秒")
    print(f"    速率: {(completed[0]/total_time):.0f} ops/s")
    print(f"    错误数: {errors[0]}")
    print(f"    最终节点: {stats['nodes']:,}, 边: {stats['edges']:,}")
    
    return errors[0] == 0


def test_memory_growth():
    """内存增长测试"""
    print("\n" + "=" * 80)
    print("🔍 测试3：内存增长测试")
    print("=" * 80)
    
    tracemalloc.start()
    
    gc.collect()
    initial = tracemalloc.take_snapshot()
    initial_size = sum(stat.size for stat in initial.statistics('lineno'))
    print(f"  初始内存: {initial_size / 1024 / 1024:.2f} MB")
    
    memory = MemorySystemV7Optimized()
    
    print("  添加200,000节点...")
    for i in range(200000):
        memory.remember(f"mem_{i}", node_type=NodeType.ENTITY)
        if i % 50000 == 0 and i > 0:
            gc.collect()
            snap = tracemalloc.take_snapshot()
            size = sum(stat.size for stat in snap.statistics('lineno'))
            growth = (size - initial_size) / 1024 / 1024
            print(f"    {i}: {growth:.2f} MB")
    
    gc.collect()
    final = tracemalloc.take_snapshot()
    final_size = sum(stat.size for stat in final.statistics('lineno'))
    total_growth = (final_size - initial_size) / 1024 / 1024
    
    print(f"  最终内存: {final_size / 1024 / 1024:.2f} MB")
    print(f"  总增长: {total_growth:.2f} MB")
    print(f"  每10K节点增长: {total_growth / 20:.2f} MB")
    
    growth_per_node = total_growth * 1024 / 200000
    print(f"  每节点增长: {growth_per_node:.4f} KB")
    
    has_leak = growth_per_node > 1.0
    
    if has_leak:
        print(f"    ⚠️  可能存在内存泄漏")
    else:
        print(f"    ✅ 内存增长正常")
    
    tracemalloc.stop()
    
    return not has_leak


def test_burst_writes():
    """突发写入测试"""
    print("\n" + "=" * 80)
    print("🔍 测试4：突发写入测试")
    print("=" * 80)
    
    memory = MemorySystemV7Optimized()
    
    print("  阶段1：稳定写入（10,000节点）...")
    start = time.time()
    for i in range(10000):
        memory.remember(f"burst_{i}", node_type=NodeType.ENTITY)
    stable_time = time.time() - start
    stable_rate = 10000 / stable_time
    print(f"    稳定写入: {stable_rate:.0f} 节点/秒")
    
    print("  阶段2：突发写入（10线程同时写入100,000节点）...")
    start = time.time()
    
    def burst_worker(start_idx, count):
        for i in range(start_idx, start_idx + count):
            memory.remember(f"burst_{i}", node_type=NodeType.ENTITY)
    
    threads = []
    for i in range(10):
        t = threading.Thread(target=burst_worker, args=(10000 + i * 10000, 10000))
        t.daemon = True
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join()
    
    burst_time = time.time() - start
    burst_rate = 100000 / burst_time
    print(f"    突发写入: {burst_rate:.0f} 节点/秒")
    
    print("  阶段3：再次稳定写入（验证系统未崩溃）...")
    start = time.time()
    for i in range(10000, 20000):
        memory.remember(f"burst_{i}", node_type=NodeType.ENTITY)
    final_time = time.time() - start
    final_rate = 10000 / final_time
    print(f"    再次稳定: {final_rate:.0f} 节点/秒")
    
    stats = memory.get_statistics()
    print(f"    最终节点: {stats['nodes']:,}")
    
    burst_vs_stable = burst_rate / stable_rate
    print(f"    突发/稳定比率: {burst_vs_stable:.2f}x")
    
    return stats['nodes'] >= 120000


def test_mixed_operations():
    """混合操作测试"""
    print("\n" + "=" * 80)
    print("🔍 测试5：混合读写操作测试")
    print("=" * 80)
    
    memory = MemorySystemV7Optimized()
    
    print("  准备数据...")
    for i in range(50000):
        memory.remember(f"mixed_{i}", node_type=NodeType.ENTITY)
    
    print("  混合操作测试（写入:读取 = 1:4）...")
    operations = {
        "node_add": 0,
        "edge_add": 0,
        "recall": 0,
        "semantic": 0,
        "infer": 0,
        "errors": 0
    }
    lock = threading.Lock()
    
    def mixed_worker(wid):
        for i in range(1000):
            try:
                op = random.randint(0, 4)
                
                if op == 0:
                    memory.remember(f"mixed_w_{wid}_{i}", node_type=NodeType.ENTITY)
                    with lock:
                        operations["node_add"] += 1
                elif op == 1:
                    memory.connect(f"mixed_{random.randint(0, 49999)}", 
                                 f"mixed_{random.randint(0, 49999)}")
                    with lock:
                        operations["edge_add"] += 1
                elif op == 2:
                    memory.recall(f"mixed_{random.randint(0, 49999)}")
                    with lock:
                        operations["recall"] += 1
                elif op == 3:
                    memory.semantic_search("mixed")
                    with lock:
                        operations["semantic"] += 1
                elif op == 4:
                    memory.infer(f"mixed_{random.randint(0, 49999)}", max_depth=3)
                    with lock:
                        operations["infer"] += 1
                        
            except Exception as e:
                with lock:
                    operations["errors"] += 1
    
    print("  启动100线程...")
    start = time.time()
    threads = []
    
    for i in range(100):
        t = threading.Thread(target=mixed_worker, args=(i,))
        t.daemon = True
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join()
    
    elapsed = time.time() - start
    total_ops = sum(operations.values()) - operations["errors"]
    rate = total_ops / elapsed
    
    print(f"    ✅ 完成！")
    print(f"    总操作: {total_ops:,}, 耗时: {elapsed:.2f}秒")
    print(f"    速率: {rate:.0f} ops/s")
    print(f"    操作分布:")
    print(f"      节点添加: {operations['node_add']:,}")
    print(f"      边添加: {operations['edge_add']:,}")
    print(f"      查询: {operations['recall']:,}")
    print(f"      语义搜索: {operations['semantic']:,}")
    print(f"      图推理: {operations['infer']:,}")
    print(f"      错误: {operations['errors']}")
    
    stats = memory.get_statistics()
    print(f"    最终节点: {stats['nodes']:,}, 边: {stats['edges']:,}")
    
    return operations["errors"] == 0


def main():
    print("\n" + "=" * 80)
    print("🚀 v7.2 超大规模压力测试 - 发现极端场景问题")
    print("=" * 80)
    
    start_time = time.time()
    
    tests = [
        ("百万级规模测试", test_million_scale),
        ("极端并发测试（500线程）", test_extreme_concurrency),
        ("内存增长测试", test_memory_growth),
        ("突发写入测试", test_burst_writes),
        ("混合读写操作测试", test_mixed_operations),
    ]
    
    results = []
    issues = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
            
            if not success:
                issues.append(test_name)
                
        except Exception as e:
            print(f"\n  ❌ {test_name} 异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
            issues.append(test_name)
    
    total_time = time.time() - start_time
    
    print("\n" + "=" * 80)
    print("📊 超大规模压力测试结果")
    print("=" * 80)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    print(f"\n通过率: {passed}/{total} ({100*passed/total:.0f}%)")
    print(f"总耗时: {total_time/60:.1f}分钟")
    
    if issues:
        print(f"\n⚠️  发现 {len(issues)} 个问题:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print(f"\n🎉 所有测试通过！系统表现优秀！")
    
    print("=" * 80)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
