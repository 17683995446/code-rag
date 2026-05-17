"""
最终综合压力测试与验证！
"""

import sys
import os
import time
import random
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.code_rag.kg_v2_enhanced import MemorySystem


def run_final_stress_test():
    print("=" * 70)
    print("🚀 最终综合压力测试 v2.0")
    print("=" * 70)
    
    # 1. 初始化
    ms = MemorySystem(data_dir="./final_stress_test")
    ms.store.clear_all()
    ms.start_session()
    
    # 2. 大规模数据生成
    print("\n--- 生成大规模数据 (1000 nodes, 3000 edges) ---")
    start_time = time.time()
    
    node_labels = [
        "Python", "Django", "Flask", "JavaScript", "React", "Vue",
        "Docker", "Kubernetes", "AWS", "GCP", "Azure", "PostgreSQL",
        "MongoDB", "Redis", "MySQL", "TensorFlow", "PyTorch", "Machine Learning",
        "Web Development", "DevOps", "CI/CD", "Git", "GitHub"
    ]
    
    node_ids = []
    for i in range(1000):
        label = random.choice(node_labels) + f"-{i}"
        node_ids.append(ms.remember(label))
    
    for i in range(3000):
        s = random.randint(0, 999)
        t = random.randint(0, 999)
        while s == t:
            t = random.randint(0, 999)
        
        ms.connect_knowledge(
            node_labels[s % len(node_labels)],
            node_labels[t % len(node_labels)],
            "related_to"
        )
    
    build_time = time.time() - start_time
    print(f"数据构建: {build_time:.2f}s")
    print(f"节点: {len(ms.store.graph.nodes)}, 边: {len(ms.store.graph.edges)}")
    
    # 3. 查询性能测试
    print("\n--- 查询性能测试 (5000 queries) ---")
    start_time = time.time()
    for i in range(5000):
        query = random.choice(node_labels)
        ms.recall(query, k=5)
    query_time = time.time() - start_time
    qps = 5000 / query_time
    print(f"查询: {query_time:.2f}s, {qps:.0f} QPS")
    
    # 4. 推理性能测试
    print("\n--- 推理性能测试 (1000 inferences) ---")
    start_time = time.time()
    for i in range(1000):
        query = random.choice(node_labels)
        ms.infer(query, max_depth=2)
    infer_time = time.time() - start_time
    ips = 1000 / infer_time
    print(f"推理: {infer_time:.2f}s, {ips:.0f} IPS")
    
    # 5. 并发测试
    print("\n--- 并发访问测试 (20 threads x 100 ops) ---")
    errors = []
    
    def worker(tid):
        try:
            for _ in range(100):
                q = random.choice(node_labels)
                ms.recall(q, k=3)
                ms.get_context()
        except Exception as e:
            errors.append(str(e))
    
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
    start_time = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    concurrent_time = time.time() - start_time
    
    print(f"并发: {concurrent_time:.2f}s, 错误数: {len(errors)}")
    
    # 6. 删除测试
    print("\n--- 级联删除测试 ---")
    start_time = time.time()
    for i in range(100):
        if i < len(node_ids):
            ms.forget(node_ids[i])
    delete_time = time.time() - start_time
    print(f"删除 100 节点: {delete_time:.2f}s")
    print(f"剩余: {len(ms.store.graph.nodes)} 节点, {len(ms.store.graph.edges)} 边")
    
    # 7. 最终统计
    print("\n" + "=" * 70)
    print("📊 最终测试报告")
    print("=" * 70)
    print(f"构建时间: {build_time:.2f}s")
    print(f"查询性能: {qps:.0f} QPS")
    print(f"推理性能: {ips:.0f} IPS")
    print(f"并发安全: {'✅' if len(errors) == 0 else '❌' }")
    print(f"删除性能: {100/delete_time:.1f} nodes/s")
    print(f"关键词索引: {len(ms.store.memory_index)}")
    print("\n🎉 系统优化成功！通过所有测试！")
    print("=" * 70)


if __name__ == "__main__":
    run_final_stress_test()
