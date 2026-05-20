#!/usr/bin/env python3
"""
v7.4 极端压力测试 - 真实场景bug发现
慢工出细活：深度测试系统的稳定性和性能边界
"""
import sys
import os
import time
import threading
import random
import tracemalloc
import gc
import json
import uuid
from datetime import datetime
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kg_memory_v7_optimized import MemorySystemV7Optimized, NodeType, EdgeType


class StressTestLogger:
    def __init__(self, log_file: str):
        self.log_file = log_file
        self.lock = threading.Lock()
        
    def log(self, msg: str):
        with self.lock:
            timestamp = datetime.now().isoformat()
            line = f"[{timestamp}] {msg}\n"
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(line)
            print(line, end="")


def test_cache_efficiency():
    """测试缓存效率 - 发现缓存失效问题"""
    print("\n" + "=" * 80)
    print("🔍 测试1: 缓存效率深度测试")
    print("=" * 80)
    
    memory = MemorySystemV7Optimized()
    logger = StressTestLogger("v7_4_cache_test.log")
    
    logger.log("准备测试数据...")
    
    for i in range(20000):
        memory.remember(f"cache_test_{i}", node_type=NodeType.ENTITY)
    
    logger.log("开始热缓存测试...")
    
    test_queries = [f"cache_test_{i}" for i in range(100)]
    
    hot_cache_misses = 0
    hot_cache_hits = 0
    
    for round in range(10):
        logger.log(f"缓存预热轮次 {round + 1}")
        for query in test_queries:
            memory.recall(query, k=5)
    
    logger.log("开始正式测试 - 相同查询重复调用...")
    
    for round in range(50):
        for query in test_queries:
            result = memory.recall(query, k=5)
            if result:
                hot_cache_hits += 1
            else:
                hot_cache_misses += 1
    
    stats = memory.get_statistics()
    logger.log(f"热缓存测试完成 - 命中: {hot_cache_hits}, 未命中: {hot_cache_misses}")
    logger.log(f"官方统计: hits={stats['cache_hits']}, misses={stats['cache_misses']}")
    
    hit_rate = hot_cache_hits / (hot_cache_hits + hot_cache_misses) if (hot_cache_hits + hot_cache_misses) > 0 else 0
    logger.log(f"热缓存命中率: {hit_rate:.2%}")
    
    if hit_rate < 0.9:
        logger.log("⚠️ 问题发现: 缓存命中率低于预期")
        return False
    
    return True


def test_mixed_concurrency():
    """混合并发测试 - 发现并发竞态条件"""
    print("\n" + "=" * 80)
    print("🔍 测试2: 混合并发深度测试")
    print("=" * 80)
    
    memory = MemorySystemV7Optimized()
    logger = StressTestLogger("v7_4_mixed_concurrency.log")
    
    logger.log("准备基础数据...")
    for i in range(5000):
        memory.remember(f"mix_base_{i}", node_type=NodeType.ENTITY)
    
    total_ops = [0]
    errors = [0]
    stop_flag = [False]
    lock = threading.Lock()
    
    def worker_read(wid: int):
        while not stop_flag[0]:
            try:
                query_idx = random.randint(0, 4999)
                memory.recall(f"mix_base_{query_idx}", k=3)
                
                with lock:
                    total_ops[0] += 1
            except Exception as e:
                with lock:
                    errors[0] += 1
                logger.log(f"Reader {wid} error: {e}")
    
    def worker_write(wid: int):
        while not stop_flag[0]:
            try:
                memory.remember(f"mix_write_{wid}_{uuid.uuid4().hex[:8]}", node_type=NodeType.ENTITY)
                
                if random.random() < 0.3:
                    src = random.randint(0, 4999)
                    dst = random.randint(0, 4999)
                    memory.connect(f"mix_base_{src}", f"mix_base_{dst}")
                
                with lock:
                    total_ops[0] += 1
            except Exception as e:
                with lock:
                    errors[0] += 1
                logger.log(f"Writer {wid} error: {e}")
    
    def worker_infer(wid: int):
        while not stop_flag[0]:
            try:
                infer_idx = random.randint(0, 4999)
                memory.infer(f"mix_base_{infer_idx}", max_depth=2)
                
                with lock:
                    total_ops[0] += 1
            except Exception as e:
                with lock:
                    errors[0] += 1
                logger.log(f"Infer {wid} error: {e}")
    
    def worker_semantic(wid: int):
        while not stop_flag[0]:
            try:
                memory.semantic_search(f"mix_base_{random.randint(0, 4999)}", k=5)
                
                with lock:
                    total_ops[0] += 1
            except Exception as e:
                with lock:
                    errors[0] += 1
                logger.log(f"Semantic {wid} error: {e}")
    
    logger.log("启动200个混合工作线程...")
    threads = []
    
    for i in range(80):
        t = threading.Thread(target=worker_read, args=(i,))
        t.daemon = True
        t.start()
        threads.append(t)
    
    for i in range(60):
        t = threading.Thread(target=worker_write, args=(i,))
        t.daemon = True
        t.start()
        threads.append(t)
    
    for i in range(30):
        t = threading.Thread(target=worker_infer, args=(i,))
        t.daemon = True
        t.start()
        threads.append(t)
    
    for i in range(30):
        t = threading.Thread(target=worker_semantic, args=(i,))
        t.daemon = True
        t.start()
        threads.append(t)
    
    logger.log("开始30分钟的混合并发测试...")
    start_time = time.time()
    last_check = start_time
    last_ops = 0
    
    while time.time() - start_time < 1800:  # 30 minutes
        time.sleep(30)
        
        elapsed = time.time() - start_time
        with lock:
            current_ops = total_ops[0]
        
        recent_ops = current_ops - last_ops
        recent_rate = recent_ops / 30 if 30 > 0 else 0
        
        logger.log(f"[进度] 运行 {elapsed/60:.1f}分钟, 总操作: {current_ops:,}, 最近30秒: {recent_ops:,}, 速率: {recent_rate:.0f} ops/s")
        
        last_ops = current_ops
        last_check = time.time()
    
    stop_flag[0] = True
    
    logger.log("等待工作线程结束...")
    for t in threads:
        t.join(timeout=2)
    
    total_time = time.time() - start_time
    
    stats = memory.get_statistics()
    logger.log("=" * 80)
    logger.log("📊 混合并发测试总结")
    logger.log("=" * 80)
    logger.log(f"总操作: {total_ops[0]:,}")
    logger.log(f"总耗时: {total_time:.2f}秒")
    logger.log(f"平均速率: {(total_ops[0]/total_time):.0f} ops/s")
    logger.log(f"错误数: {errors[0]}")
    logger.log(f"最终节点: {stats['nodes']:,}, 最终边: {stats['edges']:,}")
    
    if errors[0] > 0:
        logger.log("⚠️ 问题发现: 测试过程中有错误发生")
        return False
    
    return True


def test_memory_leak_long_term():
    """长期内存泄漏测试"""
    print("\n" + "=" * 80)
    print("🔍 测试3: 长期内存泄漏监控")
    print("=" * 80)
    
    logger = StressTestLogger("v7_4_memory_leak.log")
    tracemalloc.start()
    
    memory = MemorySystemV7Optimized()
    
    logger.log("开始长期内存泄漏测试...")
    
    snapshots = []
    gc.collect()
    snapshot0 = tracemalloc.take_snapshot()
    initial_size = sum(stat.size for stat in snapshot0.statistics('lineno'))
    snapshots.append((0, initial_size))
    logger.log(f"初始内存: {initial_size / 1024 / 1024:.2f} MB")
    
    start_time = time.time()
    test_duration = 1800  # 30 minutes
    
    for round in range(180):
        for i in range(1000):
            memory.remember(f"leak_test_{round}_{i}", node_type=NodeType.ENTITY)
        
        if round % 10 == 0:
            gc.collect()
            snapshot = tracemalloc.take_snapshot()
            size = sum(stat.size for stat in snapshot.statistics('lineno'))
            snapshots.append((round, size))
            
            elapsed = time.time() - start_time
            growth = (size - initial_size) / 1024 / 1024
            logger.log(f"[进度] {elapsed/60:.1f}分钟, 轮次: {round}, 内存: {size/1024/1024:.2f} MB, 增长: {growth:.2f} MB")
        
        time.sleep(10)  # 每轮10秒
    
    gc.collect()
    final_snapshot = tracemalloc.take_snapshot()
    final_size = sum(stat.size for stat in final_snapshot.statistics('lineno'))
    total_growth = (final_size - initial_size) / 1024 / 1024
    
    logger.log("=" * 80)
    logger.log("📊 内存测试总结")
    logger.log("=" * 80)
    logger.log(f"测试时间: {(time.time() - start_time)/60:.1f}分钟")
    logger.log(f"初始内存: {initial_size/1024/1024:.2f} MB")
    logger.log(f"最终内存: {final_size/1024/1024:.2f} MB")
    logger.log(f"总增长: {total_growth:.2f} MB")
    
    tracemalloc.stop()
    
    if total_growth > 500:  # 超过500MB增长
        logger.log("⚠️ 问题发现: 内存增长异常")
        return False
    
    return True


def test_vector_search_scalability():
    """向量搜索可扩展性测试"""
    print("\n" + "=" * 80)
    print("🔍 测试4: 向量搜索可扩展性测试")
    print("=" * 80)
    
    memory = MemorySystemV7Optimized()
    logger = StressTestLogger("v7_4_vector_scalability.log")
    
    sizes = [1000, 5000, 10000, 20000, 50000]
    results = []
    
    for size in sizes:
        logger.log(f"准备数据: 准备 {size:,} 节点...")
        
        for i in range(size):
            memory.remember(f"vec_test_{i}", node_type=NodeType.ENTITY, compute_embedding=True)
        
        logger.log(f"开始测试 {size:,} 向量搜索...")
        
        search_times = []
        for test_round in range(20):
            start = time.time()
            memory.semantic_search(f"vec_test_{random.randint(0, size-1)}", k=10)
            search_times.append(time.time() - start)
        
        avg_search = sum(search_times) / len(search_times)
        logger.log(f"大小 {size:,}: 平均搜索 {avg_search:.3f}秒, 最快 {min(search_times):.3f}秒, 最慢 {max(search_times):.3f}秒")
        
        results.append((size, avg_search))
    
    logger.log("=" * 80)
    logger.log("📊 可扩展性测试总结")
    logger.log("=" * 80)
    
    for size, avg in results:
        logger.log(f"{size:,} 向量: {avg:.3f}秒/搜索")
    
    if len(results) >= 2 and results[-1][1] > results[0][1] * 10:
        logger.log("⚠️ 问题发现: 向量搜索可扩展性差")
        return False
    
    return True


def test_data_consistency():
    """数据一致性测试"""
    print("\n" + "=" * 80)
    print("🔍 测试5: 数据一致性验证")
    print("=" * 80)
    
    memory = MemorySystemV7Optimized()
    logger = StressTestLogger("v7_4_consistency.log")
    
    logger.log("测试1: 节点添加和检索一致性")
    
    added_nodes = []
    for i in range(1000):
        label = f"consist_{i}"
        node_id = memory.remember(label, node_type=NodeType.ENTITY)
        added_nodes.append((label, node_id))
    
    inconsistencies = 0
    for label, expected_id in added_nodes:
        result = memory.recall(label, k=1)
        if not result:
            inconsistencies += 1
            logger.log(f"一致性错误: 节点 {label} 无法找回")
    
    logger.log(f"节点一致性检查完成, 不一致: {inconsistencies}")
    
    logger.log("测试2: 边添加和检索一致性")
    edge_count = 0
    for i in range(500):
        edge = memory.connect(f"consist_{i}", f"consist_{(i+1)%1000}")
        if edge:
            edge_count += 1
    
    logger.log(f"边添加完成, 成功: {edge_count}")
    
    stats = memory.get_statistics()
    logger.log(f"最终状态: 节点 {stats['nodes']}, 边 {stats['edges']}")
    
    if inconsistencies > 0:
        logger.log("⚠️ 问题发现: 数据存在不一致")
        return False
    
    return True


def main():
    print("\n" + "=" * 80)
    print("🚀 v7.4 极端压力测试 - 真实场景bug发现")
    print("=" * 80)
    
    results = {}
    issues_found = []
    
    tests = [
        ("缓存效率", test_cache_efficiency),
        ("混合并发", test_mixed_concurrency),
        ("长期内存泄漏", test_memory_leak_long_term),
        ("向量搜索可扩展性", test_vector_search_scalability),
        ("数据一致性", test_data_consistency),
    ]
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results[test_name] = success
            if not success:
                issues_found.append(test_name)
        except Exception as e:
            print(f"❌ {test_name} 崩溃: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = False
            issues_found.append(test_name)
    
    print("\n" + "=" * 80)
    print("📊 极端压力测试总结")
    print("=" * 80)
    
    for test_name, success in results.items():
        status = "✅ 通过" if success else "❌ 问题发现"
        print(f"  {test_name}: {status}")
    
    passed = sum(1 for s in results.values() if s)
    total = len(results)
    print(f"\n通过率: {passed}/{total} ({100*passed/total:.0f}%)")
    
    if issues_found:
        print(f"\n⚠️ 发现问题的测试:")
        for issue in issues_found:
            print(f"  - {issue}")
    
    print("=" * 80)
    
    return passed == total


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
