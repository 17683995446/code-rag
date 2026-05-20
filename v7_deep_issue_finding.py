#!/usr/bin/env python3
"""
v7.1 深度问题发现测试
第一性原理分析：发现真实运行时的竞态条件、内存泄漏和性能瓶颈
"""
import sys
import os
import time
import random
import json
import threading
import tracemalloc
from collections import defaultdict
from datetime import datetime
import gc

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kg_memory_v7_optimized import MemorySystemV7Optimized, NodeType, EdgeType


def test_race_condition_deep():
    """深度测试：发现竞态条件"""
    print("\n" + "=" * 80)
    print("🔍 测试1：深度竞态条件检测")
    print("=" * 80)
    
    errors = []
    race_detected = [False]
    lock = threading.Lock()
    
    def intensive_writer(thread_id):
        for i in range(1000):
            try:
                label = f"race_node_{thread_id}_{i}"
                node_id = kg.remember(label, node_type=NodeType.ENTITY)
                
                # 立即读取验证一致性
                recalled = kg.recall(label, k=1)
                if not recalled:
                    with lock:
                        errors.append(f"线程{thread_id}: 添加后无法召回 {label}")
                        race_detected[0] = True
                
                # 尝试连接
                target_label = f"race_node_{thread_id}_{(i+1)%1000}"
                kg.remember(target_label, node_type=NodeType.ENTITY)
                kg.connect(label, target_label)
                
            except Exception as e:
                with lock:
                    errors.append(f"线程{thread_id}: {e}")
    
    print("  启动200线程同时写入...")
    kg = MemorySystemV7Optimized()
    
    start = time.time()
    threads = []
    
    for i in range(200):
        t = threading.Thread(target=intensive_writer, args=(i,))
        t.daemon = True
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join()
    
    elapsed = time.time() - start
    stats = kg.get_statistics()
    
    print(f"    完成！耗时: {elapsed:.2f}秒")
    print(f"    节点数: {stats['nodes']:,}, 边数: {stats['edges']:,}")
    print(f"    错误数: {len(errors)}")
    
    if errors:
        print(f"    ⚠️  发现竞态条件！前5个错误:")
        for err in errors[:5]:
            print(f"      - {err}")
    
    return len(errors) == 0


def test_cache_thrashing():
    """测试缓存失效风暴"""
    print("\n" + "=" * 80)
    print("🔍 测试2：缓存失效风暴检测")
    print("=" * 80)
    
    kg = MemorySystemV7Optimized()
    
    print("  添加10,000节点...")
    for i in range(10000):
        kg.remember(f"cache_node_{i}", node_type=NodeType.ENTITY)
    
    cache_hits_before = [0]
    cache_misses = [0]
    
    def query_worker():
        for _ in range(100):
            result = kg.recall("cache_node_5000", k=5)
            if result:
                cache_hits_before[0] += 1
            else:
                cache_misses[0] += 1
    
    print("  测试缓存命中率...")
    threads = []
    for _ in range(10):
        t = threading.Thread(target=query_worker)
        t.daemon = True
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join()
    
    print(f"    缓存命中: {cache_hits_before[0]}, 缺失: {cache_misses[0]}")
    
    print("  添加更多节点触发缓存失效...")
    for i in range(10000, 20000):
        kg.remember(f"cache_node_{i}", node_type=NodeType.ENTITY)
    
    cache_hits_after = [0]
    cache_misses_after = [0]
    
    def query_worker_after():
        for _ in range(100):
            result = kg.recall("cache_node_5000", k=5)
            if result:
                cache_hits_after[0] += 1
            else:
                cache_misses_after[0] += 1
    
    threads = []
    for _ in range(10):
        t = threading.Thread(target=query_worker_after)
        t.daemon = True
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join()
    
    print(f"    缓存命中: {cache_hits_after[0]}, 缺失: {cache_misses_after[0]}")
    
    # 缓存应该被清空，命中率应该下降
    cache_invalidated = cache_hits_before[0] > 0 and cache_hits_after[0] < cache_hits_before[0]
    
    if cache_invalidated:
        print(f"    ⚠️  缓存被意外失效！每次添加节点都清空缓存")
        print(f"    建议：使用更智能的缓存失效策略")
        return False
    
    return True


def test_memory_leak_deep():
    """深度内存泄漏检测"""
    print("\n" + "=" * 80)
    print("🔍 测试3：深度内存泄漏检测")
    print("=" * 80)
    
    tracemalloc.start()
    
    snapshots = []
    kg = MemorySystemV7Optimized()
    
    print("  初始内存...")
    gc.collect()
    initial = tracemalloc.take_snapshot()
    initial_size = sum(stat.size for stat in initial.statistics('lineno'))
    print(f"    初始: {initial_size / 1024 / 1024:.2f} MB")
    
    # 阶段1：添加节点
    print("  阶段1：添加50,000节点...")
    for i in range(50000):
        kg.remember(f"leak_node_{i}", node_type=NodeType.ENTITY)
        if i % 10000 == 0 and i > 0:
            gc.collect()
            snap = tracemalloc.take_snapshot()
            size = sum(stat.size for stat in snap.statistics('lineno'))
            snapshots.append((i, size))
            print(f"    {i}: {size / 1024 / 1024:.2f} MB")
    
    gc.collect()
    after_nodes = tracemalloc.take_snapshot()
    nodes_size = sum(stat.size for stat in after_nodes.statistics('lineno'))
    nodes_growth = (nodes_size - initial_size) / 1024 / 1024
    
    print(f"    节点阶段增长: {nodes_growth:.2f} MB")
    
    # 阶段2：添加边
    print("  阶段2：添加25,000边...")
    edges_added = 0
    for i in range(25000):
        if kg.connect(f"leak_node_{i}", f"leak_node_{(i+1)%50000}"):
            edges_added += 1
        if i % 5000 == 0 and i > 0:
            gc.collect()
            snap = tracemalloc.take_snapshot()
            size = sum(stat.size for stat in snap.statistics('lineno'))
            snapshots.append((50000 + i, size))
            print(f"    {50000 + i}: {size / 1024 / 1024:.2f} MB")
    
    gc.collect()
    after_edges = tracemalloc.take_snapshot()
    edges_size = sum(stat.size for stat in after_edges.statistics('lineno'))
    edges_growth = (edges_size - nodes_size) / 1024 / 1024
    
    print(f"    边阶段增长: {edges_growth:.2f} MB")
    
    # 阶段3：大量查询
    print("  阶段3：执行100,000次查询...")
    for i in range(100000):
        kg.recall(f"leak_node_{i % 50000}", k=5)
        if i % 20000 == 0 and i > 0:
            gc.collect()
            snap = tracemalloc.take_snapshot()
            size = sum(stat.size for stat in snap.statistics('lineno'))
            snapshots.append((50000 + 25000 + i, size))
            print(f"    {50000 + 25000 + i}: {size / 1024 / 1024:.2f} MB")
    
    gc.collect()
    final = tracemalloc.take_snapshot()
    final_size = sum(stat.size for stat in final.statistics('lineno'))
    total_growth = (final_size - initial_size) / 1024 / 1024
    
    print(f"    最终内存: {final_size / 1024 / 1024:.2f} MB")
    print(f"    总增长: {total_growth:.2f} MB")
    
    # 分析泄漏
    growth_per_node = total_growth * 1024 / 75000
    print(f"    每节点增长: {growth_per_node:.4f} KB")
    
    has_leak = growth_per_node > 0.5
    
    if has_leak:
        print(f"    ⚠️  可能存在内存泄漏")
        
        # 找出增长最大的对象
        top_stats = final.compare_to(initial, 'lineno')
        print(f"    增长最多的位置:")
        for stat in top_stats[:5]:
            print(f"      {stat}")
    else:
        print(f"    ✅ 内存增长正常")
    
    tracemalloc.stop()
    
    return not has_leak


def test_vector_index_bottleneck():
    """测试向量索引瓶颈"""
    print("\n" + "=" * 80)
    print("🔍 测试4：向量索引瓶颈检测")
    print("=" * 80)
    
    kg = MemorySystemV7Optimized()
    
    print("  添加10,000节点...")
    for i in range(10000):
        kg.remember(f"vec_node_{i}", node_type=NodeType.ENTITY)
    
    print("  测试语义搜索性能...")
    
    start = time.time()
    for _ in range(100):
        kg.semantic_search("vec_node_5000", k=10)
    elapsed = time.time() - start
    
    search_rate = 100 / elapsed
    print(f"    100次搜索耗时: {elapsed:.2f}秒 ({search_rate:.1f} 搜索/秒)")
    
    # 向量索引应该被使用
    vector_size = len(kg.vector_index.vectors)
    print(f"    向量索引大小: {vector_size:,}")
    
    is_bottleneck = search_rate < 10
    
    if is_bottleneck:
        print(f"    ⚠️  语义搜索性能较差，可能是瓶颈")
        return False
    
    return True


def test_concurrent_read_write():
    """测试并发读写一致性"""
    print("\n" + "=" * 80)
    print("🔍 测试5：并发读写一致性检测")
    print("=" * 80)
    
    kg = MemorySystemV7Optimized()
    
    inconsistencies = []
    lock = threading.Lock()
    
    def writer(wid):
        for i in range(500):
            label = f"concurrent_{wid}_{i}"
            kg.remember(label, node_type=NodeType.ENTITY)
    
    def reader(rid):
        for _ in range(500):
            # 随机选择一个写入的标签
            wid = random.randint(0, 9)
            label = f"concurrent_{wid}_0"
            
            # 验证存在
            result = kg.recall(label, k=1)
            
            # 在写入过程中可能读不到，这是正常的
            # 但如果节点应该存在而读不到，就是问题
            if not result:
                # 尝试直接检查
                if label.lower() in kg._label_to_node:
                    with lock:
                        inconsistencies.append(f"Reader{rid}: {label} 在索引中但无法召回")
    
    print("  启动10个写入线程 + 20个读取线程...")
    
    threads = []
    
    for i in range(10):
        t = threading.Thread(target=writer, args=(i,))
        t.daemon = True
        t.start()
        threads.append(t)
    
    time.sleep(0.1)
    
    for i in range(20):
        t = threading.Thread(target=reader, args=(i,))
        t.daemon = True
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join()
    
    stats = kg.get_statistics()
    print(f"    节点数: {stats['nodes']:,}")
    print(f"    不一致数: {len(inconsistencies)}")
    
    if inconsistencies:
        print(f"    ⚠️  发现读写不一致:")
        for inc in inconsistencies[:5]:
            print(f"      {inc}")
        return False
    
    return True


def test_long_term_stability():
    """长时间稳定性测试（简化版）"""
    print("\n" + "=" * 80)
    print("🔍 测试6：长时间稳定性检测（5分钟）")
    print("=" * 80)
    
    kg = MemorySystemV7Optimized()
    
    operations = [0]
    errors = [0]
    lock = threading.Lock()
    
    stop_flag = [False]
    
    def worker(wid):
        local_ops = 0
        local_errors = 0
        
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
                local_errors += 1
                with lock:
                    errors[0] += 1
    
    print("  启动50线程运行5分钟...")
    
    threads = []
    for i in range(50):
        t = threading.Thread(target=worker, args=(i,))
        t.daemon = True
        t.start()
        threads.append(t)
    
    start_time = time.time()
    last_ops = 0
    
    while time.time() - start_time < 300:  # 5分钟
        time.sleep(30)
        elapsed = time.time() - start_time
        with lock:
            ops = operations[0]
        
        rate = ops / elapsed
        recent_rate = (ops - last_ops) / 30
        
        print(f"    {elapsed/60:.1f}分钟: {ops:,} ops ({rate:.0f} ops/s, 最近30秒: {recent_rate:.0f} ops/s)")
        
        last_ops = ops
        
        if elapsed >= 300:
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


def test_batch_operation_performance():
    """测试批量操作性能"""
    print("\n" + "=" * 80)
    print("🔍 测试7：批量操作性能检测")
    print("=" * 80)
    
    kg = MemorySystemV7Optimized()
    
    print("  单个添加100,000节点...")
    start = time.time()
    for i in range(100000):
        kg.remember(f"batch_{i}", node_type=NodeType.ENTITY)
    single_time = time.time() - start
    single_rate = 100000 / single_time
    print(f"    单个添加: {single_time:.2f}秒 ({single_rate:.0f} 节点/秒)")
    
    # 清理
    kg2 = MemorySystemV7Optimized()
    
    print("  批量添加100,000节点（模拟）...")
    start = time.time()
    
    # 批量操作接口不存在，但我们测试并发性能
    def batch_worker(start_idx, count):
        for i in range(start_idx, start_idx + count):
            kg2.remember(f"batch2_{i}", node_type=NodeType.ENTITY)
    
    threads = []
    batch_size = 10000
    for i in range(10):
        t = threading.Thread(target=batch_worker, args=(i * batch_size, batch_size))
        t.daemon = True
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join()
    
    batch_time = time.time() - start
    batch_rate = 100000 / batch_time
    print(f"    10线程批量: {batch_time:.2f}秒 ({batch_rate:.0f} 节点/秒)")
    
    improvement = batch_rate / single_rate
    print(f"    并发加速比: {improvement:.2f}x")
    
    # 如果加速比太低，说明锁成为瓶颈
    if improvement < 2.0:
        print(f"    ⚠️  并发加速比较低，锁竞争严重")
        return False
    
    return True


def main():
    print("\n" + "=" * 80)
    print("🚀 v7.1 深度问题发现测试 - 基于第一性原理")
    print("=" * 80)
    
    start_time = time.time()
    
    tests = [
        ("深度竞态条件检测", test_race_condition_deep),
        ("缓存失效风暴检测", test_cache_thrashing),
        ("深度内存泄漏检测", test_memory_leak_deep),
        ("向量索引瓶颈检测", test_vector_index_bottleneck),
        ("并发读写一致性检测", test_concurrent_read_write),
        ("长时间稳定性检测", test_long_term_stability),
        ("批量操作性能检测", test_batch_operation_performance),
    ]
    
    results = []
    issues_found = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
            
            if not success:
                issues_found.append(test_name)
                
        except Exception as e:
            print(f"\n  ❌ {test_name} 异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
            issues_found.append(test_name)
    
    total_time = time.time() - start_time
    
    print("\n" + "=" * 80)
    print("📊 测试结果总结")
    print("=" * 80)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "⚠️  发现问题"
        print(f"  {test_name}: {status}")
    
    print(f"\n通过率: {passed}/{total} ({100*passed/total:.0f}%)")
    print(f"总耗时: {total_time/60:.1f}分钟")
    
    if issues_found:
        print(f"\n⚠️  发现 {len(issues_found)} 个问题:")
        for issue in issues_found:
            print(f"  - {issue}")
    
    # 保存报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_time": total_time,
        "passed": passed,
        "total": total,
        "issues_found": issues_found,
        "results": [{"name": name, "passed": success} for name, success in results]
    }
    
    report_path = os.path.join(os.path.dirname(__file__), "v7_deep_issue_finding_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n报告保存: {report_path}")
    
    print("=" * 80)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
