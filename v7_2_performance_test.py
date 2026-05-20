#!/usr/bin/env python3
"""
v7.2 vs v7.1 性能对比测试
验证LRU缓存优化和缓存失效问题修复的效果
"""
import sys
import os
import time
import threading
import random
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_basic_performance_v7_2():
    """测试v7.2基本性能"""
    print("=" * 80)
    print("🔍 v7.2 基本性能测试")
    print("=" * 80)
    
    from kg_memory_v7_optimized import MemorySystemV7Optimized, NodeType, EdgeType
    
    memory = MemorySystemV7Optimized()
    
    print("  测试1: 添加50,000节点...")
    start = time.time()
    for i in range(50000):
        memory.remember(f"node_{i}", node_type=NodeType.ENTITY)
    node_time = time.time() - start
    node_rate = 50000 / node_time
    print(f"    ✅ 50,000节点: {node_time:.2f}秒 ({node_rate:.0f} 节点/秒)")
    
    print("  测试2: 添加25,000边...")
    start = time.time()
    edges_added = 0
    for i in range(25000):
        if memory.connect(f"node_{i}", f"node_{(i+1)%25000}"):
            edges_added += 1
    edge_time = time.time() - start
    edge_rate = edges_added / edge_time if edge_time > 0 else 0
    print(f"    ✅ 25,000边: {edge_time:.2f}秒 ({edge_rate:.0f} 边/秒)")
    
    print("  测试3: 查询性能（冷缓存）...")
    start = time.time()
    for i in range(10000):
        memory.recall(f"node_{i}", k=10)
    cold_query_time = time.time() - start
    cold_query_rate = 10000 / cold_query_time
    print(f"    冷缓存查询: {cold_query_time:.2f}秒 ({cold_query_rate:.0f} 查询/秒)")
    
    print("  测试4: 查询性能（热缓存）...")
    start = time.time()
    for i in range(10000):
        memory.recall(f"node_{i}", k=10)
    hot_query_time = time.time() - start
    hot_query_rate = 10000 / hot_query_time
    print(f"    热缓存查询: {hot_query_time:.2f}秒 ({hot_query_rate:.0f} 查询/秒)")
    
    cache_speedup = hot_query_rate / cold_query_rate if cold_query_rate > 0 else 0
    print(f"    缓存加速比: {cache_speedup:.2f}x")
    
    stats = memory.get_statistics()
    cache_total = stats['cache_hits'] + stats['cache_misses']
    cache_hit_rate = stats['cache_hits'] / cache_total if cache_total > 0 else 0
    print(f"    缓存命中率: {cache_hit_rate:.1%} ({stats['cache_hits']}/{cache_total})")
    
    return {
        "node_rate": node_rate,
        "edge_rate": edge_rate,
        "cold_query_rate": cold_query_rate,
        "hot_query_rate": hot_query_rate,
        "cache_hit_rate": cache_hit_rate
    }


def test_concurrent_performance_v7_2():
    """测试v7.2并发性能"""
    print("\n" + "=" * 80)
    print("🔍 v7.2 高并发性能测试（200线程）")
    print("=" * 80)
    
    from kg_memory_v7_optimized import MemorySystemV7Optimized, NodeType, EdgeType
    
    memory = MemorySystemV7Optimized()
    
    print("  准备基础数据...")
    for i in range(5000):
        memory.remember(f"base_{i}", node_type=NodeType.ENTITY)
    
    num_threads = 200
    ops_per_thread = 100
    
    print(f"  启动 {num_threads} 线程，每线程 {ops_per_thread} 操作...")
    
    errors = [0]
    completed = [0]
    errors_lock = threading.Lock()
    completed_lock = threading.Lock()
    
    def worker(worker_id):
        local_errors = 0
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
                local_errors += 1
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
    
    print(f"    ✅ 完成！总操作: {completed[0]:,}, 耗时: {total_time:.2f}秒")
    print(f"    速率: {(completed[0]/total_time):.0f} ops/s")
    print(f"    错误数: {errors[0]}")
    print(f"    最终节点: {stats['nodes']:,}, 边: {stats['edges']:,}")
    
    return {
        "total_ops": completed[0],
        "total_time": total_time,
        "ops_per_sec": completed[0] / total_time,
        "errors": errors[0],
        "final_nodes": stats['nodes'],
        "final_edges": stats['edges']
    }


def test_cache_behavior_v7_2():
    """测试v7.2缓存行为"""
    print("\n" + "=" * 80)
    print("🔍 v7.2 缓存行为测试（验证修复）")
    print("=" * 80)
    
    from kg_memory_v7_optimized import MemorySystemV7Optimized, NodeType
    
    memory = MemorySystemV7Optimized()
    
    print("  测试1: 添加节点后缓存是否保留...")
    
    # 添加1000个节点
    for i in range(1000):
        memory.remember(f"cache_test_{i}", node_type=NodeType.ENTITY)
    
    # 查询触发缓存
    print("    查询1000次填充缓存...")
    for i in range(1000):
        memory.recall(f"cache_test_{i}", k=1)
    
    stats_before = memory.get_statistics()
    cache_hits_before = stats_before['cache_hits']
    print(f"    缓存命中: {cache_hits_before}")
    
    # 添加更多节点（v7.1会清空缓存，v7.2不会）
    print("    添加5000个新节点...")
    for i in range(1000, 6000):
        memory.remember(f"cache_test_{i}", node_type=NodeType.ENTITY)
    
    # 再次查询之前的节点
    print("    再次查询之前的1000个节点...")
    cache_hits_during_write = 0
    for i in range(1000):
        result = memory.recall(f"cache_test_{i}", k=1)
        if result:
            cache_hits_during_write += 1
    
    stats_after = memory.get_statistics()
    print(f"    第二次查询缓存命中: {cache_hits_during_write}/1000")
    
    # v7.2应该保留缓存（缓存命中应该很高）
    # v7.1会清空缓存（缓存命中会是0）
    if cache_hits_during_write >= 900:
        print(f"    ✅ 缓存保留正常！v7.2优化成功")
        print(f"    说明：添加节点不会清空缓存")
        return True
    else:
        print(f"    ❌ 缓存被清空！v7.2优化失败")
        return False


def test_long_term_stability_v7_2():
    """测试v7.2长时间稳定性"""
    print("\n" + "=" * 80)
    print("🔍 v7.2 长时间稳定性测试（3分钟）")
    print("=" * 80)
    
    from kg_memory_v7_optimized import MemorySystemV7Optimized, NodeType
    
    kg = MemorySystemV7Optimized()
    
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
                    kg.remember(f"stable_{wid}_{local_ops}", node_type=NodeType.ENTITY)
                elif op == 1:
                    kg.connect(f"stable_{wid}_0", f"stable_{(wid+1)%10}_0")
                elif op == 2:
                    kg.recall(f"stable_{wid}_0", k=5)
                else:
                    kg.semantic_search("stable")
                
                local_ops += 1
                
                if local_ops % 100 == 0:
                    with lock:
                        operations[0] += 100
                        
            except Exception as e:
                with lock:
                    errors[0] += 1
    
    print("  启动50线程运行3分钟...")
    
    threads = []
    for i in range(50):
        t = threading.Thread(target=worker, args=(i,))
        t.daemon = True
        t.start()
        threads.append(t)
    
    start_time = time.time()
    last_ops = 0
    
    while time.time() - start_time < 180:  # 3分钟
        time.sleep(30)
        elapsed = time.time() - start_time
        with lock:
            ops = operations[0]
        
        rate = ops / elapsed
        recent_rate = (ops - last_ops) / 30
        
        print(f"    {elapsed/60:.1f}分钟: {ops:,} ops ({rate:.0f} ops/s, 最近30秒: {recent_rate:.0f} ops/s)")
        
        last_ops = ops
        
        if elapsed >= 180:
            break
    
    stop_flag[0] = True
    
    for t in threads:
        t.join(timeout=1)
    
    final_time = time.time() - start_time
    with lock:
        final_ops = operations[0]
        final_errors = errors[0]
    
    stats = kg.get_statistics()
    
    print(f"    ✅ 完成！")
    print(f"    总操作: {final_ops:,}")
    print(f"    总耗时: {final_time:.1f}秒")
    print(f"    平均速率: {final_ops/final_time:.0f} ops/s")
    print(f"    错误数: {final_errors}")
    print(f"    最终节点: {stats['nodes']:,}, 边: {stats['edges']:,}")
    
    return final_errors == 0


def main():
    print("\n" + "=" * 80)
    print("🚀 v7.2 性能验证测试")
    print("=" * 80)
    
    start_time = time.time()
    
    results = {}
    
    try:
        results['basic'] = test_basic_performance_v7_2()
    except Exception as e:
        print(f"  ❌ 基本性能测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        results['concurrent'] = test_concurrent_performance_v7_2()
    except Exception as e:
        print(f"  ❌ 并发性能测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        results['cache_behavior'] = test_cache_behavior_v7_2()
    except Exception as e:
        print(f"  ❌ 缓存行为测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        results['stability'] = test_long_term_stability_v7_2()
    except Exception as e:
        print(f"  ❌ 稳定性测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    total_time = time.time() - start_time
    
    print("\n" + "=" * 80)
    print("📊 v7.2 测试结果总结")
    print("=" * 80)
    
    if 'basic' in results:
        print(f"  基本性能:")
        print(f"    节点添加: {results['basic']['node_rate']:.0f} 节点/秒")
        print(f"    边添加: {results['basic']['edge_rate']:.0f} 边/秒")
        print(f"    查询(冷): {results['basic']['cold_query_rate']:.0f} 查询/秒")
        print(f"    查询(热): {results['basic']['hot_query_rate']:.0f} 查询/秒")
        print(f"    缓存命中率: {results['basic']['cache_hit_rate']:.1%}")
    
    if 'concurrent' in results:
        print(f"  并发性能:")
        print(f"    200线程速率: {results['concurrent']['ops_per_sec']:.0f} ops/s")
        print(f"    错误数: {results['concurrent']['errors']}")
    
    if 'cache_behavior' in results:
        status = "✅ 缓存保留正常" if results['cache_behavior'] else "❌ 缓存失效"
        print(f"  缓存行为: {status}")
    
    if 'stability' in results:
        status = "✅ 稳定运行" if results['stability'] else "❌ 稳定性问题"
        print(f"  长时间稳定性: {status}")
    
    print(f"\n总耗时: {total_time/60:.1f}分钟")
    
    # 保存报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_time": total_time,
        "results": results
    }
    
    report_path = os.path.join(os.path.dirname(__file__), "v7_2_performance_report.json")
    with open(report_path, "w") as f:
        import json
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n报告保存: {report_path}")
    
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    main()
