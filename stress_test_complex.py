"""
超大规模复杂场景压力测试与问题发现
测试大规模知识图谱的构建、查询、推理能力
"""

import sys
import os
import time
import random
import threading
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.code_rag.knowledge_graph import (
    KnowledgeGraph, KnowledgeNode, KnowledgeEdge,
    KnowledgeType, RelationType
)
from src.code_rag.memory_system import MemorySystem


def generate_complex_test_data(num_nodes=1000, num_edges=5000):
    """生成复杂测试数据集"""
    print("=" * 70)
    print(f"生成复杂测试数据：{num_nodes} 节点，{num_edges} 边")
    print("=" * 70)
    
    categories = [
        "编程语言", "Web框架", "数据库", "DevOps", "ML框架", 
        "云服务", "开发工具", "架构模式", "设计模式", "算法"
    ]
    languages = ["Python", "JavaScript", "Java", "Go", "Rust", "C++", "TypeScript", "Ruby"]
    frameworks = ["Django", "Flask", "Spring", "Express", "React", "Vue"]
    databases = ["PostgreSQL", "MongoDB", "Redis", "MySQL", "Elasticsearch"]
    devops_tools = ["Docker", "Kubernetes", "Jenkins", "GitLab", "Terraform"]
    
    all_labels = languages + frameworks + databases + devops_tools
    
    ms = MemorySystem(data_dir="./stress_test_data")
    ms.store.clear_all()
    ms.start_session()
    
    # 生成节点
    start_nodes = time.time()
    node_ids = []
    for i in range(num_nodes):
        # 生成多样化标签
        if i < len(all_labels):
            label = all_labels[i]
        else:
            category = random.choice(categories)
            label = f"{category}-{i:04d}"
        
        kt = random.choice([KnowledgeType.ENTITY, KnowledgeType.CONCEPT, KnowledgeType.FACT])
        node = KnowledgeNode(label, type=kt, properties={
            "category": random.choice(categories),
            "created_at": datetime.now().isoformat(),
            "popularity": random.random()
        })
        node_id = ms.store.graph.add_node(node)
        node_ids.append(node_id)
        
        if (i + 1) % 100 == 0:
            print(f"  已生成 {i+1} 节点...")
    
    print(f"  节点生成耗时: {time.time() - start_nodes:.2f}s")
    
    # 生成边
    start_edges = time.time()
    relation_types = list(RelationType)
    
    for i in range(num_edges):
        source_idx = random.randint(0, num_nodes - 1)
        target_idx = random.randint(0, num_nodes - 1)
        
        while target_idx == source_idx:
            target_idx = random.randint(0, num_nodes - 1)
        
        rt = random.choice(relation_types)
        edge = KnowledgeEdge(
            node_ids[source_idx],
            node_ids[target_idx],
            type=rt,
            weight=random.uniform(0.5, 3.0)
        )
        
        try:
            ms.store.graph.add_edge(edge)
        except Exception as e:
            pass
        
        if (i + 1) % 500 == 0:
            print(f"  已生成 {i+1} 边...")
    
    print(f"  边生成耗时: {time.time() - start_edges:.2f}s")
    print(f"  总构建耗时: {time.time() - start_nodes:.2f}s")
    
    return ms


def test_query_performance(ms, num_queries=1000):
    """测试查询性能"""
    print("\n" + "=" * 70)
    print(f"查询性能测试：{num_queries} 次查询")
    print("=" * 70)
    
    all_labels = [n.label for n in ms.store.graph.nodes.values()]
    
    search_queries = [
        "Python", "Web", "数据", "数据库", "开发", "框架", "云", "容器",
        "学习", "测试", random.choice(all_labels) if all_labels else "Random"
    ] * 100
    search_queries = search_queries[:num_queries]
    
    start_time = time.time()
    total_results = 0
    
    for i, query in enumerate(search_queries):
        results = ms.recall(query, k=5)
        total_results += len(results)
        
        if (i + 1) % 100 == 0:
            print(f"  已执行 {i+1} 次查询...")
    
    elapsed = time.time() - start_time
    qps = num_queries / elapsed
    
    print(f"  查询总耗时: {elapsed:.2f}s")
    print(f"  QPS (查询/秒): {qps:.2f}")
    print(f"  平均每次结果数: {total_results / num_queries:.2f}")
    
    return qps


def test_inference_performance(ms, num_inferences=200):
    """测试推理性能"""
    print("\n" + "=" * 70)
    print(f"推理性能测试：{num_inferences} 次推理")
    print("=" * 70)
    
    labels = [n.label for n in ms.store.graph.nodes.values()]
    if len(labels) > 0:
        test_labels = labels[:min(50, len(labels))]
        test_labels = (test_labels * (num_inferences // len(test_labels) + 1))[:num_inferences]
        
        start_time = time.time()
        total_infer_result = 0
        
        for i, label in enumerate(test_labels):
            results = ms.infer(label)
            total_infer_result += len(results)
            
            if (i + 1) % 50 == 0:
                print(f"  已执行 {i+1} 次推理...")
        
        elapsed = time.time() - start_time
        ips = num_inferences / elapsed
        
        print(f"  推理总耗时: {elapsed:.2f}s")
        print(f"  IPS (推理/秒): {ips:.2f}")
        print(f"  平均结果数: {total_infer_result / num_inferences:.2f}")
        
        return ips
    else:
        print("  没有数据可推理")
        return 0


def test_concurrent_access(ms, num_threads=10, operations_per_thread=100):
    """测试并发访问（可能发现问题！）"""
    print("\n" + "=" * 70)
    print(f"并发访问测试：{num_threads} 线程，每线程 {operations_per_thread} 次")
    print("=" * 70)
    
    errors = []
    
    def worker(thread_id):
        try:
            labels = list(ms.store.graph.nodes.values())[:50]
            for i in range(operations_per_thread):
                if labels:
                    query = random.choice(labels).label
                    ms.recall(query, k=3)
                
                if i % 10 == 0:
                    ms.get_context()
        
        except Exception as e:
            errors.append(f"线程 {thread_id} 错误: {str(e)}")
    
    start_time = time.time()
    threads = []
    
    for i in range(num_threads):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    elapsed = time.time() - start_time
    
    print(f"  并发总耗时: {elapsed:.2f}s")
    print(f"  发生错误数: {len(errors)}")
    
    if errors:
        print(f"  错误示例: {errors[:3]}")
    
    return len(errors)


def test_serialization_performance(ms):
    """测试序列化/反序列化性能"""
    print("\n" + "=" * 70)
    print("序列化/反序列化性能测试")
    print("=" * 70)
    
    # 序列化测试
    start = time.time()
    json_data = ms.store.graph.to_json()
    ser_time = time.time() - start
    
    print(f"  序列化到 JSON: {ser_time:.4f}s, 大小: {len(json_data)/1024:.2f}KB")
    
    # 反序列化测试
    start = time.time()
    new_graph = KnowledgeGraph.from_json(json_data)
    deser_time = time.time() - start
    
    print(f"  JSON 反序列化: {deser_time:.4f}s")
    
    # 验证一致性
    assert len(new_graph.nodes) == len(ms.store.graph.nodes), "节点数不匹配"
    assert len(new_graph.edges) == len(ms.store.graph.edges), "边数不匹配"
    print(f"  验证一致性：✅ 通过")
    
    return ser_time + deser_time


def test_memory_cleanup_and_delete(ms):
    """测试删除与清理功能"""
    print("\n" + "=" * 70)
    print("删除与清理功能测试")
    print("=" * 70)
    
    nodes = list(ms.store.graph.nodes.values())
    num_to_delete = min(50, len(nodes))
    deleted_ids = [n.id for n in nodes[:num_to_delete]]
    
    start = time.time()
    for node_id in deleted_ids:
        try:
            ms.forget(node_id)
        except Exception as e:
            pass
    
    delete_time = time.time() - start
    print(f"  删除 {num_to_delete} 节点: {delete_time:.2f}s")
    
    # 验证删除
    remaining = len(ms.store.graph.nodes)
    print(f"  剩余节点: {remaining}")


def run_complete_stress_test():
    """运行完整压力测试"""
    print("\n" + "=" * 70)
    print("🧪 开始超大规模复杂场景压力测试！")
    print("=" * 70)
    
    # 1. 生成复杂数据
    ms = generate_complex_test_data(num_nodes=1000, num_edges=3000)
    
    stats = ms.get_stats()
    print(f"\n初始统计: {stats}")
    
    # 2. 测试查询
    qps = test_query_performance(ms, num_queries=1000)
    
    # 3. 测试推理
    ips = test_inference_performance(ms, num_inferences=200)
    
    # 4. 测试并发
    errors = test_concurrent_access(ms, num_threads=10, operations_per_thread=100)
    
    # 5. 测试序列化
    total_ser_time = test_serialization_performance(ms)
    
    # 6. 测试删除
    test_memory_cleanup_and_delete(ms)
    
    # 总结报告
    print("\n" + "=" * 70)
    print("📊 压力测试报告")
    print("=" * 70)
    print(f"  查询 QPS:          {qps:.2f}")
    print(f"  推理 IPS:          {ips:.2f}")
    print(f"  并发错误数:        {errors}")
    print(f"  总序列化耗时:      {total_ser_time:.4f}s")
    
    # 保存测试数据用于后续分析
    ms.store.save()
    print(f"\n  测试数据已保存到 ./stress_test_data/")
    
    print("\n" + "=" * 70)
    print("🧠 现在开始问题发现与分析...")
    print("=" * 70)
    
    return ms


if __name__ == "__main__":
    run_complete_stress_test()
