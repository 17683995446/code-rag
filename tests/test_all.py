"""
完整的测试套件！
包含单元测试、集成测试、系统测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import time
import threading
from pathlib import Path
import tempfile

import pytest


# 单元测试

def test_node_creation():
    """单元测试1: 节点创建
    """
    from kg_memory.core import Node, NodeType
    node = Node(label="Python")
    assert node.label == "Python"
    assert node.type == NodeType.ENTITY
    assert len(node.id) > 0
    print("✅ 节点创建正常")


def test_edge_creation():
    """单元测试2: 边创建
    """
    from kg_memory.core import Node, Edge, EdgeType
    node1 = Node(label="Python")
    node2 = Node(label="Django")
    edge = Edge(source_id=node1.id, target_id=node2.id, type=EdgeType.USES)
    assert edge.source_id == node1.id
    assert edge.target_id == node2.id
    print("✅ 边创建正常")


def test_memory_system_basic():
    """单元测试3: 记忆系统基础功能
    """
    from kg_memory.core import MemorySystem
    ms = MemorySystem(tempfile.mkdtemp())
    ms.clear()
    
    nid = ms.remember("Python")
    assert len(nid) > 0
    
    results = ms.recall("Python")
    assert len(results) == 1
    
    print("✅ 记忆系统基础功能正常")


def test_memory_system_connect():
    """集成测试1: 连接和推理
    """
    from kg_memory.core import MemorySystem
    ms = MemorySystem(tempfile.mkdtemp())
    ms.clear()
    
    ms.remember("Python")
    ms.remember("Django")
    ms.connect("Django", "Python", "uses")
    
    infer_results = ms.infer("Django", max_depth=2)
    assert len(infer_results) > 0
    
    print("✅ 连接和推理正常")


def test_networkx_shortest_path():
    """集成测试2: NetworkX最短路径
    """
    from kg_memory.core import MemorySystem
    ms = MemorySystem(tempfile.mkdtemp())
    ms.clear()
    
    ms.remember("A")
    ms.remember("B")
    ms.remember("C")
    
    ms.connect("A", "B")
    ms.connect("B", "C")
    ms.connect("A", "C")
    
    path = ms.shortest_path("A", "C")
    assert len(path) >= 2
    
    print("✅ NetworkX功能正常")


def test_concurrent_access():
    """系统测试1: 并发访问
    """
    from kg_memory.core import MemorySystem
    ms = MemorySystem(tempfile.mkdtemp())
    ms.clear()
    
    errors = []
    
    def worker(id):
        nonlocal errors
        try:
            for i in range(50):
                ms.remember(f"Test-{id}-{i}")
                ms.recall("Test")
        except Exception as e:
            errors.append(str(e))
    
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    
    start = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.time() - start
    
    assert len(errors) == 0
    
    print(f"✅ 并发测试通过: 耗时 {elapsed:.2f}s")


def test_performance():
    """系统测试2: 性能基准
    """
    from kg_memory.core import MemorySystem
    ms = MemorySystem(tempfile.mkdtemp())
    ms.clear()
    
    # 批量添加
    start = time.time()
    for i in range(500):
        ms.remember(f"Node-{i}")
    add_time = time.time() - start
    
    # 连接
    start = time.time()
    for i in range(499):
        ms.connect(f"Node-{i}", f"Node-{i+1}")
    connect_time = time.time() - start
    
    # 查询
    start = time.time()
    for i in range(1000):
        ms.recall("Node-0")
    query_time = time.time() - start
    
    print(f"✅ 性能测试通过")
    print(f"   添加 500 节点: {add_time:.2f}s")
    print(f"   连接 499 边: {connect_time:.2f}s")
    print(f"   查询 1000 次: {query_time:.2f}s")
    print(f"   QPS: {1000/query_time:.0f}")


def test_persistence():
    """系统测试3: 持久化
    """
    from kg_memory.core import MemorySystem
    dir1 = tempfile.mkdtemp()
    
    ms1 = MemorySystem(dir1)
    ms1.clear()
    ms1.remember("Python")
    ms1.save()
    
    ms2 = MemorySystem(dir1)
    results = ms2.recall("Python")
    
    assert len(results) == 1
    
    print("✅ 持久化正常")


def test_lru_cache():
    """单元测试4: LRU缓存
    """
    from kg_memory.core import LRUCache
    cache = LRUCache(capacity=5)
    
    cache.put("a", 1)
    cache.put("b", 2)
    assert cache.get("a") == 1
    
    for i in range(5):
        cache.put(str(i), i)
    
    print("✅ LRU缓存正常")


def run_all_tests():
    """运行完整测试套件
    """
    print("=" * 70)
    print("🧪 知识图谱记忆系统 - 完整测试套件")
    print("=" * 70)
    print()
    
    all_passed = True
    
    tests = [
        ("单元测试1: 节点创建", test_node_creation),
        ("单元测试2: 边创建", test_edge_creation),
        ("单元测试3: 记忆系统基础功能", test_memory_system_basic),
        ("单元测试4: LRU缓存", test_lru_cache),
        ("集成测试1: 连接和推理", test_memory_system_connect),
        ("集成测试2: NetworkX最短路径", test_networkx_shortest_path),
        ("系统测试1: 并发访问", test_concurrent_access),
        ("系统测试2: 性能基准", test_performance),
        ("系统测试3: 持久化", test_persistence),
    ]
    
    for name, test_func in tests:
        print(f"执行: {name}")
        try:
            test_func()
        except Exception as e:
            print(f"❌ {name} 失败: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
        print()
    
    print("=" * 70)
    if all_passed:
        print("🎉 所有测试通过！")
    else:
        print("⚠️ 部分测试失败")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
