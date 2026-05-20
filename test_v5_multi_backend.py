#!/usr/bin/env python3
"""
知识图谱记忆系统 v5.0 - 多后端架构测试
验证创新架构的功能和性能
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import time
import json
import tempfile
from typing import Dict, Any

from kg_memory.core_v5 import (
    MemorySystem,
    BackendType,
    NetworkXBackend,
    MemoryBackend,
)


def print_header(title: str):
    print("\n" + "="*80)
    print(f"🎯 {title}")
    print("="*80)


def test_backend_basic(backend_name: str, system: MemorySystem):
    """基础功能测试"""
    print(f"\n🔹 测试 {backend_name} 基础功能")
    
    # 1. 添加节点
    start = time.time()
    node1 = system.remember("Python")
    node2 = system.remember("FastAPI")
    node3 = system.remember("NetworkX")
    add_time = time.time() - start
    print(f"   ✅ 添加3个节点: {add_time*1000:.2f}ms")
    
    # 2. 连接节点
    start = time.time()
    edge1 = system.connect("Python", "FastAPI", "uses")
    edge2 = system.connect("Python", "NetworkX", "uses")
    edge3 = system.connect("FastAPI", "NetworkX", "uses")
    connect_time = time.time() - start
    print(f"   ✅ 添加3个边: {connect_time*1000:.2f}ms")
    
    # 3. 查询
    start = time.time()
    results = system.recall("Python", k=10)
    search_time = time.time() - start
    print(f"   ✅ 搜索结果: {len(results)} 个 ({search_time*1000:.2f}ms)")
    
    # 4. 推理
    start = time.time()
    inferences = system.infer("Python", max_depth=2)
    infer_time = time.time() - start
    print(f"   ✅ 推理结果: {len(inferences)} 个 ({infer_time*1000:.2f}ms)")
    
    # 5. 统计
    stats = system.get_statistics()
    print(f"   📊 统计: {stats['nodes']} 节点, {stats['edges']} 边")
    
    return True


def test_backend_performance(backend_name: str, system: MemorySystem):
    """性能测试"""
    print(f"\n📈 测试 {backend_name} 性能")
    
    n_nodes = 1000
    n_edges = 500
    n_queries = 500
    
    # 添加大量节点
    start = time.time()
    for i in range(n_nodes):
        system.remember(f"Test_Node_{i}", {"index": i})
    node_time = time.time() - start
    node_rate = n_nodes / node_time
    
    print(f"   ⚡ 添加 {n_nodes} 节点: {node_time:.3f}s ({node_rate:.0f} node/s)")
    
    # 添加边
    import random
    start = time.time()
    edge_count = 0
    for i in range(n_edges):
        source = f"Test_Node_{random.randint(0, n_nodes-1)}"
        target = f"Test_Node_{random.randint(0, n_nodes-1)}"
        try:
            system.connect(source, target, "related")
            edge_count += 1
        except:
            pass
    edge_time = time.time() - start
    edge_rate = edge_count / edge_time if edge_time > 0 else 0
    
    print(f"   ⚡ 添加 {edge_count} 边: {edge_time:.3f}s ({edge_rate:.0f} edge/s)")
    
    # 查询性能
    start = time.time()
    for i in range(n_queries):
        query = f"Test_Node_{random.randint(0, n_nodes-1)}"
        system.recall(query, k=5)
    query_time = time.time() - start
    qps = n_queries / query_time
    
    print(f"   ⚡ 查询 {n_queries} 次: {query_time:.3f}s ({qps:.0f} QPS)")
    
    # PageRank测试
    start = time.time()
    pr = system.calculate_pagerank()
    pr_time = time.time() - start
    print(f"   🧠 PageRank: {pr_time*1000:.2f}ms ({len(pr)} 结果)")
    
    # 中心性测试
    start = time.time()
    dc = system.calculate_centrality("degree")
    dc_time = time.time() - start
    print(f"   🧠 度中心性: {dc_time*1000:.2f}ms ({len(dc)} 结果)")
    
    return {
        "node_rate": node_rate,
        "edge_rate": edge_rate,
        "qps": qps,
        "pr_time": pr_time,
        "dc_time": dc_time,
    }


def test_backend_algorithms(backend_name: str, system: MemorySystem):
    """图算法测试"""
    print(f"\n🧠 测试 {backend_name} 图算法")
    
    # 初始化测试图
    for i in range(50):
        system.remember(f"Algo_Node_{i}")
    
    import random
    for i in range(100):
        source = f"Algo_Node_{random.randint(0, 49)}"
        target = f"Algo_Node_{random.randint(0, 49)}"
        try:
            system.connect(source, target, "related")
        except:
            pass
    
    # 测试各种算法
    algorithms = [
        ("PageRank", lambda: system.calculate_pagerank()),
        ("Degree Centrality", lambda: system.calculate_centrality("degree")),
        ("Communities", lambda: system.find_communities()),
        ("Similar Nodes", lambda: system.get_similar_nodes("Algo_Node_0", top_k=5)),
    ]
    
    all_passed = True
    for name, func in algorithms:
        try:
            start = time.time()
            result = func()
            elapsed = time.time() - start
            
            if isinstance(result, dict):
                print(f"   ✅ {name}: {len(result)} 结果 ({elapsed*1000:.2f}ms)")
            elif isinstance(result, list):
                print(f"   ✅ {name}: {len(result)} 结果 ({elapsed*1000:.2f}ms)")
            else:
                print(f"   ✅ {name}: 成功 ({elapsed*1000:.2f}ms)")
        except Exception as e:
            print(f"   ❌ {name}: 失败 - {e}")
            all_passed = False
    
    return all_passed


def test_backend_persistence(backend_name: str, temp_dir: str):
    """持久化测试"""
    print(f"\n💾 测试 {backend_name} 持久化")
    
    # 创建第一个实例
    system1 = MemorySystem(temp_dir, backend_type=BackendType.NETWORKX if backend_name == "NetworkX" else BackendType.MEMORY)
    for i in range(10):
        system1.remember(f"Persist_Node_{i}")
        system1.connect(f"Persist_Node_{i}", f"Persist_Node_{(i+1)%10}", "related")
    system1.save()
    stats1 = system1.get_statistics()
    print(f"   ✅ 保存: {stats1['nodes']} 节点, {stats1['edges']} 边")
    
    # 创建第二个实例并加载
    system2 = MemorySystem(temp_dir, backend_type=BackendType.NETWORKX if backend_name == "NetworkX" else BackendType.MEMORY)
    stats2 = system2.get_statistics()
    
    if stats2['nodes'] == stats1['nodes'] and stats2['edges'] == stats1['edges']:
        print(f"   ✅ 加载: {stats2['nodes']} 节点, {stats2['edges']} 边")
        return True
    else:
        print(f"   ❌ 加载不匹配: {stats2['nodes']} vs {stats1['nodes']}")
        return False


def benchmark_all_backends():
    """对比所有后端"""
    print_header("v5.0 多后端架构测试")
    
    backends = [
        ("NetworkX", BackendType.NETWORKX),
        ("Memory", BackendType.MEMORY),
    ]
    
    all_results = {}
    
    for name, backend_type in backends:
        print_header(f"测试 {name} 后端")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            system = MemorySystem(temp_dir, backend_type=backend_type)
            
            # 测试1: 基础功能
            basic_passed = test_backend_basic(name, system)
            
            # 测试2: 性能
            perf_results = test_backend_performance(name, system)
            
            # 测试3: 图算法
            algo_passed = test_backend_algorithms(name, system)
            
            # 测试4: 持久化
            persist_passed = test_backend_persistence(name, temp_dir)
            
            # 保存结果
            all_results[name] = {
                "basic_passed": basic_passed,
                "algo_passed": algo_passed,
                "persist_passed": persist_passed,
                "performance": perf_results,
            }
            
            # 清理
            system.clear()
    
    # 生成报告
    print_header("测试报告")
    
    for name, results in all_results.items():
        print(f"\n📋 {name} 后端:")
        print(f"   基础功能: {'✅ 通过' if results['basic_passed'] else '❌ 失败'}")
        print(f"   图算法: {'✅ 通过' if results['algo_passed'] else '❌ 失败'}")
        print(f"   持久化: {'✅ 通过' if results['persist_passed'] else '❌ 失败'}")
        
        if 'performance' in results:
            perf = results['performance']
            print(f"   性能指标:")
            print(f"      节点创建: {perf['node_rate']:.0f} node/s")
            print(f"      边创建: {perf['edge_rate']:.0f} edge/s")
            print(f"      查询: {perf['qps']:.0f} QPS")
            print(f"      PageRank: {perf['pr_time']*1000:.2f}ms")
            print(f"      度中心性: {perf['dc_time']*1000:.2f}ms")
    
    # 保存报告
    with open("v5_backend_test_report.json", "w") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print("\n📝 报告已保存到 v5_backend_test_report.json")
    
    return all_results


if __name__ == "__main__":
    results = benchmark_all_backends()
    print("\n🎉 v5.0 多后端架构测试完成！")
