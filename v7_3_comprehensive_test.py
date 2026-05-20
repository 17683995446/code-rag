#!/usr/bin/env python3
"""
v7.3 综合压力测试 - 10分钟长时间测试
测试目标：验证v7.3的7大优化是否有效
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


def test_basic_performance():
    """基本性能测试"""
    print("=" * 80)
    print("测试1：基本性能测试")
    print("=" * 80)
    
    memory = MemorySystemV7Optimized()
    
    print("  添加100,000节点...")
    start = time.time()
    for i in range(100000):
        memory.remember(f"node_{i}", node_type=NodeType.ENTITY)
        if i % 20000 == 0 and i > 0:
            elapsed = time.time() - start
            rate = i / elapsed
            print(f"    {i}: {rate:.0f} 节点/秒")
    node_time = time.time() - start
    node_rate = 100000 / node_time
    print(f"    ✅ 100,000节点: {node_time:.2f}秒 ({node_rate:.0f} 节点/秒)")
    
    print("  添加50,000边...")
    start = time.time()
    for i in range(50000):
        memory.connect(f"node_{i}", f"node_{(i+1)%50000}")
    edge_time = time.time() - start
    edge_rate = 50000 / edge_time
    print(f"    ✅ 50,000边: {edge_time:.2f}秒 ({edge_rate:.0f} 边/秒)")
    
    print("  查询测试...")
    start = time.time()
    for i in range(10000):
        memory.recall(f"node_{i}", k=10)
    query_time = time.time() - start
    query_rate = 10000 / query_time
    print(f"    ✅ 10,000查询: {query_time:.2f}秒 ({query_rate:.0f} 查询/秒)")
    
    stats = memory.get_statistics()
    print(f"    最终状态: 节点 {stats['nodes']:,}, 边 {stats['edges']:,}")
    print(f"    缓存命中率: {stats['cache_hits']}/{stats['cache_hits']+stats['cache_misses']}")
    
    return {
        "node_rate": node_rate,
        "edge_rate": edge_rate,
        "query_rate": query_rate
    }


def test_concurrent_performance():
    """并发性能测试"""
    print("\n" + "=" * 80)
    print("测试2：高并发性能测试（300线程）")
    print("=" * 80)
    
    memory = MemorySystemV7Optimized()
    
    print("  准备基础数据...")
    for i in range(10000):
        memory.remember(f"base_{i}", node_type=NodeType.ENTITY)
    
    num_threads = 300
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
                    memory.remember(f"worker_{worker_id}_{i}", node_type=NodeType.ENTITY)
                elif op == 1:
                    memory.connect(f"base_{random.randint(0, 9999)}", f"base_{random.randint(0, 9999)}")
                elif op == 2:
                    memory.recall(f"base_{random.randint(0, 9999)}")
                elif op == 3:
                    memory.semantic_search("base")
                elif op == 4:
                    memory.recommend_connections(f"base_{random.randint(0, 9999)}")
                elif op == 5:
                    memory.infer(f"base_{random.randint(0, 9999)}", max_depth=3)
                
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
        
        if elapsed - last_check >= 15:
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
    
    return {
        "total_ops": completed[0],
        "total_time": total_time,
        "ops_per_sec": completed[0] / total_time,
        "errors": errors[0]
    }


def test_long_duration():
    """长时间稳定性测试（10分钟）"""
    print("\n" + "=" * 80)
    print("测试3：长时间稳定性测试（10分钟）")
    print("=" * 80)
    
    memory = MemorySystemV7Optimized()
    
    print("  准备基础数据...")
    for i in range(5000):
        memory.remember(f"stable_{i}", node_type=NodeType.ENTITY)
    
    operations = [0]
    errors = [0]
    lock = threading.Lock()
    stop_flag = [False]
    
    def worker(wid):
        local_ops = 0
        
        while not stop_flag[0]:
            try:
                op = random.randint(0, 3)
                
                if op == 0:
                    memory.remember(f"stable_w_{wid}_{local_ops}", node_type=NodeType.ENTITY)
                elif op == 1:
                    memory.connect(f"stable_{random.randint(0, 4999)}", f"stable_{random.randint(0, 4999)}")
                elif op == 2:
                    memory.recall(f"stable_{random.randint(0, 4999)}", k=5)
                else:
                    memory.semantic_search("stable")
                
                local_ops += 1
                
                if local_ops % 100 == 0:
                    with lock:
                        operations[0] += 100
                        
            except Exception as e:
                with lock:
                    errors[0] += 1
    
    print("  启动100线程运行10分钟...")
    
    threads = []
    for i in range(100):
        t = threading.Thread(target=worker, args=(i,))
        t.daemon = True
        t.start()
        threads.append(t)
    
    start_time = time.time()
    last_ops = 0
    
    while time.time() - start_time < 600:  # 10分钟
        time.sleep(60)
        elapsed = time.time() - start_time
        with lock:
            ops = operations[0]
        
        rate = ops / elapsed
        recent_rate = (ops - last_ops) / 60
        
        print(f"    {elapsed/60:.1f}分钟: {ops:,} ops ({rate:.0f} ops/s, 最近1分钟: {recent_rate:.0f} ops/s)")
        
        last_ops = ops
        
        if elapsed >= 600:
            break
    
    stop_flag[0] = True
    
    for t in threads:
        t.join(timeout=2)
    
    final_time = time.time() - start_time
    with lock:
        final_ops = operations[0]
        final_errors = errors[0]
    
    stats = memory.get_statistics()
    
    print(f"    ✅ 完成！")
    print(f"    总操作: {final_ops:,}")
    print(f"    总耗时: {final_time:.1f}秒 ({final_time/60:.1f}分钟)")
    print(f"    平均速率: {final_ops/final_time:.0f} ops/s")
    print(f"    错误数: {final_errors}")
    print(f"    最终节点: {stats['nodes']:,}, 边: {stats['edges']:,}")
    
    return {
        "total_ops": final_ops,
        "total_time": final_time,
        "ops_per_sec": final_ops / final_time,
        "errors": final_errors,
        "final_nodes": stats['nodes'],
        "final_edges": stats['edges']
    }


def test_memory_leak():
    """内存泄漏测试"""
    print("\n" + "=" * 80)
    print("测试4：内存泄漏测试")
    print("=" * 80)
    
    tracemalloc.start()
    
    gc.collect()
    initial = tracemalloc.take_snapshot()
    initial_size = sum(stat.size for stat in initial.statistics('lineno'))
    print(f"  初始内存: {initial_size / 1024 / 1024:.2f} MB")
    
    memory = MemorySystemV7Optimized()
    
    print("  添加500,000节点...")
    for i in range(500000):
        memory.remember(f"mem_{i}", node_type=NodeType.ENTITY)
        if i % 100000 == 0 and i > 0:
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
    
    growth_per_node = total_growth * 1024 / 500000
    print(f"  每节点增长: {growth_per_node:.4f} KB")
    
    has_leak = growth_per_node > 1.0
    
    if has_leak:
        print(f"    ⚠️  可能存在内存泄漏")
    else:
        print(f"    ✅ 内存增长正常")
    
    tracemalloc.stop()
    
    return not has_leak


def main():
    print("\n" + "=" * 80)
    print("🚀 v7.3 综合压力测试 - 验证7大优化")
    print("=" * 80)
    
    start_time = time.time()
    
    tests = [
        ("基本性能测试", test_basic_performance),
        ("高并发性能测试（300线程）", test_concurrent_performance),
        ("长时间稳定性测试（10分钟）", test_long_duration),
        ("内存泄漏测试", test_memory_leak),
    ]
    
    results = {}
    issues = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
            
            if isinstance(result, dict) and 'errors' in result:
                if result['errors'] > 0:
                    issues.append(test_name)
            elif isinstance(result, bool) and not result:
                issues.append(test_name)
                
        except Exception as e:
            print(f"\n  ❌ {test_name} 异常: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = {"error": str(e)}
            issues.append(test_name)
    
    total_time = time.time() - start_time
    
    print("\n" + "=" * 80)
    print("📊 v7.3 测试结果总结")
    print("=" * 80)
    
    if '基本性能测试' in results and isinstance(results['基本性能测试'], dict):
        r = results['基本性能测试']
        print(f"  基本性能:")
        print(f"    节点添加: {r.get('node_rate', 0):.0f} 节点/秒")
        print(f"    边添加: {r.get('edge_rate', 0):.0f} 边/秒")
        print(f"    查询速度: {r.get('query_rate', 0):.0f} 查询/秒")
    
    if '高并发性能测试（300线程）' in results and isinstance(results['高并发性能测试（300线程）'], dict):
        r = results['高并发性能测试（300线程）']
        print(f"  高并发性能:")
        print(f"    300线程速率: {r.get('ops_per_sec', 0):.0f} ops/s")
        print(f"    错误数: {r.get('errors', 0)}")
    
    if '长时间稳定性测试（10分钟）' in results and isinstance(results['长时间稳定性测试（10分钟）'], dict):
        r = results['长时间稳定性测试（10分钟）']
        print(f"  长时间稳定性:")
        print(f"    10分钟总操作: {r.get('total_ops', 0):,}")
        print(f"    平均速率: {r.get('ops_per_sec', 0):.0f} ops/s")
        print(f"    错误数: {r.get('errors', 0)}")
        print(f"    最终节点: {r.get('final_nodes', 0):,}")
    
    if '内存泄漏测试' in results:
        r = results['内存泄漏测试']
        if isinstance(r, bool):
            status = "✅ 正常" if r else "❌ 泄漏"
            print(f"  内存管理: {status}")
    
    print(f"\n总耗时: {total_time/60:.1f}分钟")
    
    if issues:
        print(f"\n⚠️  发现 {len(issues)} 个问题:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print(f"\n🎉 所有测试通过！v7.3优化成功！")
    
    print("=" * 80)
    
    return len(issues) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
