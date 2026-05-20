#!/usr/bin/env python3
"""
知识图谱记忆系统 v7.7 - 超极端压力测试
最混乱、最大规模、最长时间的真实场景测试
"""
import sys
import os
import random
import time
import threading
from typing import List, Dict, Any
from datetime import datetime

# 添加上级目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kg_memory_v7_optimized import MemorySystemV7Optimized, NodeType, EdgeType

class ExtremeChaosTest:
    """超极端混乱测试 - 极限版"""
    
    def __init__(self):
        self.kg = MemorySystemV7Optimized()
        self.errors = []
        self.error_lock = threading.Lock()
        self.node_count = 0
        self.edge_count = 0
        self.query_count = 0
        self.semantic_search_count = 0
        self.recommend_count = 0
        self.infer_count = 0
        
    def record_error(self, operation: str, error: Exception, context: str = ""):
        with self.error_lock:
            self.errors.append({
                "operation": operation,
                "error": str(error),
                "type": type(error).__name__,
                "context": context,
                "time": datetime.now().isoformat()
            })
            print(f"❌ ERROR [{operation}]: {type(error).__name__}: {error}")
            if context:
                print(f"   Context: {context}")
    
    def extreme_node_test(self, iterations: int = 50000):
        """极端节点添加测试 - 大规模"""
        print(f"\n🧪 超极端节点添加: {iterations}次")
        start_time = time.time()
        
        labels = [
            None, "", " ", "\t", "\n", "😀", "测试节点", "Test Node",
            "A"*1000, "B"*2000, "C"*5000,
            "1234567890"*100,
            "Node with spaces",
            "Node_with_underscores",
            "Node-with-dashes",
            "Node.with.dots",
            "Node@with@ats",
            "Node#with#hashes",
            "Node$with$dollars",
            "Node%with%percents",
            "Node^with^carets",
            "Node&with&amps",
            "Node*with*stars",
            "Node(with(parens",
            "Node)with)parens",
            "Node{with{braces",
            "Node}with}braces",
            "Node[with[brackets",
            "Node]with]brackets",
            "Node\\with\\slashes",
            "Node|with|pipes",
            "Node;with;semicolons",
            "Node:with:colons",
            'Node"with"quotes',
            "Node'with'apostrophes",
            "Node<with<less",
            "Node>with>greater",
            "Node?with?questions",
            "Node/with/slashes",
            "Node`with`backticks",
            "Node~with~tildes",
            "Node=with=equals",
            "Node+with+pluses",
            "Node=with=equals",
            "你好世界",
            "こんにちは世界",
            "안녕하세요세계",
            "مرحبا بالعالم",
            "Привет мир",
        ]
        
        for i in range(iterations):
            try:
                label = random.choice(labels)
                properties = {
                    "index": i,
                    "random": random.random(),
                    "timestamp": time.time(),
                    "large_data": "x" * random.randint(0, 10000)
                }
                node_type = random.choice([
                    NodeType.ENTITY, NodeType.CONCEPT, NodeType.EVENT
                ])
                
                self.kg.remember(
                    label, 
                    properties=properties, 
                    node_type=node_type,
                    compute_embedding=random.choice([True, False])
                )
                self.node_count += 1
                
                if i % 5000 == 0:
                    elapsed = time.time() - start_time
                    print(f"   ⏱️  进度: {i}/{iterations} ({elapsed:.1f}s)")
                    
            except Exception as e:
                self.record_error("add_node", e, f"iteration={i}")
        
        elapsed = time.time() - start_time
        print(f"✅ 超极端节点测试: {iterations}次, {elapsed:.2f}s")
    
    def extreme_connect_test(self, iterations: int = 30000):
        """极端连接测试 - 大规模"""
        print(f"\n🧪 超极端连接测试: {iterations}次")
        start_time = time.time()
        
        # 先获取一些节点
        with self.kg._node_lock:
            nodes = list(self.kg._label_to_node.keys())
        
        if not nodes:
            print("⚠️  没有节点可连接")
            return
        
        edge_types = [
            EdgeType.RELATED_TO, EdgeType.PART_OF, EdgeType.CAUSES,
            EdgeType.SIMILAR_TO, None, "", "CUSTOM_RELATION"
        ]
        
        for i in range(iterations):
            try:
                source = random.choice(nodes) if random.random() > 0.1 else None
                target = random.choice(nodes) if random.random() > 0.1 else None
                
                relation = random.choice(edge_types)
                weight = random.random() * 10
                
                self.kg.connect(
                    source, target,
                    relation=relation,
                    weight=weight
                )
                self.edge_count += 1
                
                if i % 3000 == 0:
                    elapsed = time.time() - start_time
                    print(f"   ⏱️  进度: {i}/{iterations} ({elapsed:.1f}s)")
                    
            except Exception as e:
                self.record_error("connect", e, f"iteration={i}")
        
        elapsed = time.time() - start_time
        print(f"✅ 超极端连接测试: {iterations}次, {elapsed:.2f}s")
    
    def extreme_query_test(self, iterations: int = 20000):
        """极端查询测试 - 大规模"""
        print(f"\n🧪 超极端查询测试: {iterations}次")
        start_time = time.time()
        
        queries = [
            None, "", " ", "\t", "\n",
            "测试", "Test", "Node", "不存在的节点",
            "A"*100, "你好", "世界",
            "a", "b", "c", "1", "2", "3"
        ]
        
        for i in range(iterations):
            try:
                query = random.choice(queries)
                k = random.randint(-10, 100)
                
                results = self.kg.recall(query, k=k)
                self.query_count += 1
                
                if i % 2000 == 0:
                    elapsed = time.time() - start_time
                    print(f"   ⏱️  进度: {i}/{iterations} ({elapsed:.1f}s)")
                    
            except Exception as e:
                self.record_error("query", e, f"iteration={i}")
        
        elapsed = time.time() - start_time
        print(f"✅ 超极端查询测试: {iterations}次, {elapsed:.2f}s")
    
    def extreme_semantic_search_test(self, iterations: int = 10000):
        """极端语义搜索测试 - 大规模"""
        print(f"\n🧪 超极端语义搜索测试: {iterations}次")
        start_time = time.time()
        
        queries = [
            None, "", " ", "\t", "\n",
            "similar", "related", "测试节点", "Test",
            "A", "B", "C", "你好", "世界"
        ]
        
        for i in range(iterations):
            try:
                query = random.choice(queries)
                k = random.randint(-5, 50)
                
                results = self.kg.semantic_search(query, k=k)
                self.semantic_search_count += 1
                
                if i % 1000 == 0:
                    elapsed = time.time() - start_time
                    print(f"   ⏱️  进度: {i}/{iterations} ({elapsed:.1f}s)")
                    
            except Exception as e:
                self.record_error("semantic_search", e, f"iteration={i}")
        
        elapsed = time.time() - start_time
        print(f"✅ 超极端语义搜索测试: {iterations}次, {elapsed:.2f}s")
    
    def extreme_infer_test(self, iterations: int = 5000):
        """极端推理测试 - 大规模"""
        print(f"\n🧪 超极端推理测试: {iterations}次")
        start_time = time.time()
        
        concepts = [
            None, "", " ", "\t", "\n",
            "测试", "Test", "Node", "不存在的节点"
        ]
        
        for i in range(iterations):
            try:
                concept = random.choice(concepts)
                depth = random.randint(-3, 10)
                
                results = self.kg.infer(concept, max_depth=depth)
                self.infer_count += 1
                
                if i % 500 == 0:
                    elapsed = time.time() - start_time
                    print(f"   ⏱️  进度: {i}/{iterations} ({elapsed:.1f}s)")
                    
            except Exception as e:
                self.record_error("infer", e, f"iteration={i}")
        
        elapsed = time.time() - start_time
        print(f"✅ 超极端推理测试: {iterations}次, {elapsed:.2f}s")
    
    def extreme_concurrent_test(self, threads: int = 50, duration: int = 120):
        """超极端并发测试 - 长时间"""
        print(f"\n🧪 超极端并发测试: {threads}线程, {duration}秒")
        
        def worker(worker_id: int):
            start_time = time.time()
            while time.time() - start_time < duration:
                try:
                    operation = random.choice([
                        "add", "connect", "query", "semantic_search", "infer"
                    ])
                    
                    if operation == "add":
                        label = f"Worker{worker_id}_{time.time()}"
                        self.kg.remember(label)
                    elif operation == "connect":
                        with self.kg._node_lock:
                            nodes = list(self.kg._label_to_node.keys())
                        if nodes and len(nodes) >= 2:
                            self.kg.connect(
                                random.choice(nodes),
                                random.choice(nodes)
                            )
                    elif operation == "query":
                        self.kg.recall("Node", k=random.randint(1, 20))
                    elif operation == "semantic_search":
                        self.kg.semantic_search("Test", k=random.randint(1, 10))
                    elif operation == "infer":
                        with self.kg._node_lock:
                            nodes = list(self.kg._label_to_node.keys())
                        if nodes:
                            self.kg.infer(random.choice(nodes), max_depth=random.randint(1, 3))
                except Exception as e:
                    self.record_error(f"worker_{worker_id}", e)
        
        thread_list = []
        start_time = time.time()
        
        for i in range(threads):
            t = threading.Thread(target=worker, args=(i,), daemon=True)
            t.start()
            thread_list.append(t)
        
        # 监控进度
        while time.time() - start_time < duration:
            elapsed = time.time() - start_time
            print(f"   ⏱️  并发测试进度: {elapsed:.0f}s/{duration}s")
            time.sleep(10)
        
        print("   等待线程结束...")
        for t in thread_list:
            t.join(timeout=5)
        
        elapsed = time.time() - start_time
        print(f"✅ 超极端并发测试: {threads}线程, {elapsed:.2f}s")
    
    def run_full_test(self):
        """运行完整的超极端测试套件"""
        print("="*80)
        print("🚀 v7.7 超极端压力测试 - 极限版")
        print("="*80)
        
        start_time = time.time()
        
        # 超极端测试
        self.extreme_node_test(50000)
        self.extreme_connect_test(30000)
        self.extreme_query_test(20000)
        self.extreme_semantic_search_test(10000)
        self.extreme_infer_test(5000)
        self.extreme_concurrent_test(threads=50, duration=120)
        
        total_elapsed = time.time() - start_time
        
        # 总结
        print("\n" + "="*80)
        print("📊 超极端测试总结")
        print("="*80)
        print(f"总耗时: {total_elapsed:.2f}秒")
        print(f"节点添加: {self.node_count}次")
        print(f"边添加: {self.edge_count}次")
        print(f"查询: {self.query_count}次")
        print(f"语义搜索: {self.semantic_search_count}次")
        print(f"推理: {self.infer_count}次")
        
        if self.errors:
            print(f"\n❌ 发现 {len(self.errors)} 个错误:")
            for i, error in enumerate(self.errors[:10], 1):
                print(f"  {i}. [{error['operation']}] {error['type']}: {error['error']}")
            if len(self.errors) > 10:
                print(f"  ... 还有 {len(self.errors)-10} 个错误")
        else:
            print("\n✅ 太棒了！没有发现任何问题！系统极其稳定！")
        
        print("="*80)
        
        return len(self.errors) == 0

if __name__ == "__main__":
    test = ExtremeChaosTest()
    passed = test.run_full_test()
    sys.exit(0 if passed else 1)
