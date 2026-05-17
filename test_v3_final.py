"""
🚀 验证v3.0超级优化版！
"""

import sys
import os
import time
import threading
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.code_rag.kg_v3_optimized import OptimizedMemorySystem


def run_v3_performance_test():
    print("=" * 70)
    print("🚀 v3.0 超级优化版 - 性能验证测试")
    print("=" * 70)
    
    # 初始化
    ms = OptimizedMemorySystem(data_dir="./v3_test")
    ms.clear_all()
    ms.start_session()
    
    # 1. 大规模数据创建
    print("\n1️⃣  数据构建测试 (5000 nodes, 10000 edges)")
    start_time = time.time()
    
    node_ids = []
    node_labels = [f"Node-{i}" for i in range(5000)]
    
    for label in node_labels:
        node_ids.append(ms.remember(label))
    
    for i in range(10000):
        s = random.randint(0, 4999)
        t = random.randint(0, 4999)
        while s == t:
            t = random.randint(0, 4999)
        ms.connect_knowledge(node_labels[s], node_labels[t])
    
    build_time = time.time() - start_time
    print(f"   构建耗时: {build_time:.2f}s")
    
    stats = ms.stats()
    print(f"   统计: {stats}")
    
    # 2. 查询性能测试
    print("\n2️⃣  查询性能测试 (10000 queries)")
    start_time = time.time()
    
    for i in range(10000):
        q = random.choice(node_labels)
        ms.recall(q, k=5)
    
    query_time = time.time() - start_time
    qps = 10000 / query_time
    print(f"   查询耗时: {query_time:.2f}s")
    print(f"   QPS: {qps:.0f} QPS")
    
    # 3. 推理性能测试
    print("\n3️⃣  深度推理测试 (2000 inferences)")
    start_time = time.time()
    
    for i in range(2000):
        q = random.choice(node_labels)
        ms.infer(q, max_depth=3)
    
    infer_time = time.time() - start_time
    ips = 2000 / infer_time
    print(f"   推理耗时: {infer_time:.2f}s")
    print(f"   IPS: {ips:.0f} IPS")
    
    # 4. 批量操作测试
    print("\n4️⃣  批量删除测试 (500 nodes)")
    start_time = time.time()
    
    for i in range(500):
        ms.forget(node_ids[i])
    
    delete_time = time.time() - start_time
    print(f"   删除耗时: {delete_time:.3f}s")
    
    stats = ms.stats()
    print(f"   删除后统计: {stats}")
    
    # 5. 并发测试
    print("\n5️⃣  并发风暴测试 (30 threads x 1000 ops)")
    errors = []
    
    def worker(tid):
        try:
            for _ in range(1000):
                q = random.choice(node_labels)
                ms.recall(q, k=3)
                if random.random() < 0.1:
                    ms.remember(f"Random-{tid}-{time.time()}")
        except Exception as e:
            errors.append(str(e))
    
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(30)]
    start_time = time.time()
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    concurrent_time = time.time() - start_time
    
    print(f"   并发耗时: {concurrent_time:.2f}s")
    print(f"   错误数: {len(errors)}")
    if errors:
        print(f"   错误示例: {errors[:3]}")
    
    # 6. 最终报告
    print("\n" + "=" * 70)
    print("📊 v3.0 性能总结")
    print("=" * 70)
    print(f"数据规模: {5000} 节点, {10000} 边")
    print(f"构建速度: {build_time:.2f}s")
    print(f"查询性能: {qps:.0f} QPS")
    print(f"推理性能: {ips:.0f} IPS")
    print(f"删除性能: {500/delete_time:.0f} nodes/s")
    print(f"并发安全: {'✅' if len(errors) == 0 else '❌' }")
    print(f"关键词索引: {stats.get('keywords', 0)}")
    
    if qps > 50000 and ips > 10000 and len(errors) == 0:
        print("\n🎉 v3.0 性能卓越！成功通过所有测试！")
    else:
        print("\n✅ v3.0 性能良好！")
    print("=" * 70)


def compare_versions():
    """快速对比测试"""
    print("\n" + "=" * 70)
    print("📊 版本对比")
    print("=" * 70)
    
    # 创建v3数据
    ms = OptimizedMemorySystem(data_dir="./v3_benchmark")
    ms.clear_all()
    
    for i in range(1000):
        ms.remember(f"TestNode-{i}")
    
    for i in range(999):
        ms.connect_knowledge(f"TestNode-{i}", f"TestNode-{i+1}")
    
    # 测试
    start = time.time()
    for i in range(5000):
        ms.recall(f"TestNode-{i % 1000}", k=3)
    elapsed = time.time() - start
    
    print(f"v3 查询 5000 次: {elapsed:.2f}s")
    print(f"v3 QPS: {5000/elapsed:.0f}")


if __name__ == "__main__":
    run_v3_performance_test()
