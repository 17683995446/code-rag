#!/usr/bin/env python3
"""
知识图谱记忆系统 v7.8 - 超长时间、超大规模极端压力测试
100,000节点 + 50,000边 + 50,000查询 + 20,000语义搜索 + 10,000推理 + 100线程并发测试
"""
import sys
import os
import random
import time
import threading
import gc
from typing import List, Dict, Any
from datetime import datetime

# 添加上级目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kg_memory_v7_optimized import MemorySystemV7Optimized, NodeType, EdgeType

class UltraExtremeChaosTest:
    """超极端压力测试 - 超长时间版"""
    
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
        self.start_time = None
        
        # 测试数据
        self.test_labels = [
            None, "", " ", "\t", "\n", "😀", "测试节点", "Test Node",
            "Node with spaces", "Node_with_underscores", "Node-with-dashes",
            "你好世界", "こんにちは世界", "안녕하세요세계", "مرحبا بالعالم", "Привет мир",
            "A"*100, "B"*200, "C"*500, "D"*1000,
        ]
        
        for i in range(100):
            self.test_labels.append(f"Generated Node {i}")
    
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
    
    def print_progress(self, phase: str, current: int, total: int, elapsed: float):
        progress = (current / total) * 100
        print(f"  [{phase}] {current}/{total} ({progress:.1f}%) - {elapsed:.1f}s")
    
    def ultra_extreme_node_test(self, iterations: int = 100000):
        """超极端节点添加测试 - 100,000节点"""
        print(f"\n🧪 超极端节点添加测试: {iterations}次")
        self.start_time = time.time()
        
        for i in range(iterations):
            try:
                label = random.choice(self.test_labels)
                properties = {
                    "index": i,
                    "random": random.random(),
                    "timestamp": time.time(),
                    "large_data": "x" * random.randint(0, 2000) if random.random() > 0.9 else None
                }
                node_type = random.choice(list(NodeType))
                
                self.kg.remember(
                    label, 
                    properties=properties, 
                    node_type=node_type,
                    compute_embedding=random.choice([True, False])
                )
                self.node_count += 1
                
                if i % 10000 == 0 and i > 0:
                    elapsed = time.time() - self.start_time
                    self.print_progress("Nodes", i, iterations, elapsed)
                    
                    # 偶尔清理内存
                    if i % 50000 == 0:
                        gc.collect()
                    
            except Exception as e:
                self.record_error("add_node", e, f"iteration={i}")
        
        elapsed = time.time() - self.start_time
        print(f"✅ 超极端节点添加测试: {iterations}次, {elapsed:.2f}s, 平均: {elapsed/iterations:.6f}s/个")
    
    def ultra_extreme_connect_test(self, iterations: int = 50000):
        """超极端连接测试 - 50,000边"""
        print(f"\n🧪 超极端连接测试: {iterations}次")
        self.start_time = time.time()
        
        # 获取节点标签
        with self.kg._node_lock:
            node_labels = list(self.kg._label_to_node.keys())
        
        if len(node_labels) < 2:
            print("⚠️  节点不足，跳过连接测试")
            return
        
        for i in range(iterations):
            try:
                source = random.choice(node_labels) if random.random() > 0.05 else None
                target = random.choice(node_labels) if random.random() > 0.05 else None
                
                relation = random.choice(list(EdgeType))
                weight = random.random() * 10
                
                self.kg.connect(
                    source, target,
                    relation=relation,
                    weight=weight
                )
                self.edge_count += 1
                
                if i % 5000 == 0 and i > 0:
                    elapsed = time.time() - self.start_time
                    self.print_progress("Edges", i, iterations, elapsed)
                    
            except Exception as e:
                self.record_error("connect", e, f"iteration={i}")
        
        elapsed = time.time() - self.start_time
        print(f"✅ 超极端连接测试: {iterations}次, {elapsed:.2f}s, 平均: {elapsed/iterations:.6f}s/个")
    
    def ultra_extreme_query_test(self, iterations: int = 50000):
        """超极端查询测试 - 50,000次"""
        print(f"\n🧪 超极端查询测试: {iterations}次")
        self.start_time = time.time()
        
        queries = self.test_labels.copy()
        
        for i in range(iterations):
            try:
                query = random.choice(queries)
                k = random.randint(-10, 50)
                
                results = self.kg.recall(query, k=k)
                self.query_count += 1
                
                if i % 5000 == 0 and i > 0:
                    elapsed = time.time() - self.start_time
                    self.print_progress("Queries", i, iterations, elapsed)
                    
            except Exception as e:
                self.record_error("query", e, f"iteration={i}")
        
        elapsed = time.time() - self.start_time
        print(f"✅ 超极端查询测试: {iterations}次, {elapsed:.2f}s, 平均: {elapsed/iterations:.6f}s/次")
    
    def ultra_extreme_semantic_search_test(self, iterations: int = 20000):
        """超极端语义搜索测试 - 20,000次"""
        print(f"\n🧪 超极端语义搜索测试: {iterations}次")
        self.start_time = time.time()
        
        queries = self.test_labels.copy()
        
        for i in range(iterations):
            try:
                query = random.choice(queries)
                k = random.randint(-5, 30)
                
                results = self.kg.semantic_search(query, k=k)
                self.semantic_search_count += 1
                
                if i % 2000 == 0 and i > 0:
                    elapsed = time.time() - self.start_time
                    self.print_progress("Semantic Search", i, iterations, elapsed)
                    
            except Exception as e:
                self.record_error("semantic_search", e, f"iteration={i}")
        
        elapsed = time.time() - self.start_time
        print(f"✅ 超极端语义搜索测试: {iterations}次, {elapsed:.2f}s, 平均: {elapsed/iterations:.6f}s/次")
    
    def ultra_extreme_infer_test(self, iterations: int = 10000):
        """超极端推理测试 - 10,000次"""
        print(f"\n🧪 超极端推理测试: {iterations}次")
        self.start_time = time.time()
        
        with self.kg._node_lock:
            node_labels = list(self.kg._label_to_node.keys())
        
        concepts = self.test_labels.copy()
        if node_labels:
            concepts.extend(random.sample(node_labels, min(50, len(node_labels))))
        
        for i in range(iterations):
            try:
                concept = random.choice(concepts)
                max_depth = random.randint(-2, 10)
                
                results = self.kg.infer(concept, max_depth=max_depth)
                self.infer_count += 1
                
                if i % 1000 == 0 and i > 0:
                    elapsed = time.time() - self.start_time
                    self.print_progress("Inference", i, iterations, elapsed)
                    
            except Exception as e:
                self.record_error("infer", e, f"iteration={i}")
        
        elapsed = time.time() - self.start_time
        print(f"✅ 超极端推理测试: {iterations}次, {elapsed:.2f}s, 平均: {elapsed/iterations:.6f}s/次")
    
    def ultra_extreme_concurrent_test(self, threads: int = 100, duration: int = 180):
        """超极端并发测试 - 100线程，180秒"""
        print(f"\n🧪 超极端并发测试: {threads}线程, {duration}秒")
        
        with self.kg._node_lock:
            node_labels = list(self.kg._label_to_node.keys())
        
        def worker(worker_id: int):
            worker_start = time.time()
            while time.time() - worker_start < duration:
                try:
                    operation = random.choice([
                        "add", "connect", "query", "semantic_search", "infer"
                    ])
                    
                    if operation == "add":
                        label = random.choice(self.test_labels)
                        self.kg.remember(label)
                    elif operation == "connect":
                        if len(node_labels) >= 2:
                            self.kg.connect(
                                random.choice(node_labels),
                                random.choice(node_labels)
                            )
                    elif operation == "query":
                        self.kg.recall(random.choice(self.test_labels), k=random.randint(1, 10))
                    elif operation == "semantic_search":
                        self.kg.semantic_search(random.choice(self.test_labels), k=random.randint(1, 5))
                    elif operation == "infer" and node_labels:
                        self.kg.infer(random.choice(node_labels), max_depth=random.randint(1, 3))
                except Exception as e:
                    self.record_error(f"worker_{worker_id}", e)
        
        thread_list = []
        self.start_time = time.time()
        
        for i in range(threads):
            t = threading.Thread(target=worker, args=(i,), daemon=True)
            t.start()
            thread_list.append(t)
        
        # 监控进度
        while time.time() - self.start_time < duration:
            elapsed = time.time() - self.start_time
            print(f"  [Concurrent] {elapsed:.0f}s/{duration}s")
            time.sleep(30)
        
        print("  等待线程结束...")
        for t in thread_list:
            t.join(timeout=10)
        
        elapsed = time.time() - self.start_time
        print(f"✅ 超极端并发测试: {threads}线程, {elapsed:.2f}s")
    
    def run_full_test(self):
        """运行完整的超极端测试"""
        print("="*90)
        print("🚀 v7.8 超长时间、超大规模极端压力测试")
        print("="*90)
        
        overall_start = time.time()
        
        # 运行所有测试
        self.ultra_extreme_node_test(100000)
        self.ultra_extreme_connect_test(50000)
        self.ultra_extreme_query_test(50000)
        self.ultra_extreme_semantic_search_test(20000)
        self.ultra_extreme_infer_test(10000)
        self.ultra_extreme_concurrent_test(threads=100, duration=180)
        
        total_elapsed = time.time() - overall_start
        
        # 总结
        print("\n" + "="*90)
        print("📊 超极端测试最终总结")
        print("="*90)
        print(f"总耗时: {total_elapsed:.2f}秒 ({total_elapsed/60:.1f}分钟)")
        print(f"节点添加: {self.node_count:,}次")
        print(f"边添加: {self.edge_count:,}次")
        print(f"查询: {self.query_count:,}次")
        print(f"语义搜索: {self.semantic_search_count:,}次")
        print(f"推理: {self.infer_count:,}次")
        
        if self.errors:
            print(f"\n❌ 发现 {len(self.errors)} 个错误!")
            print("="*90)
            for i, error in enumerate(self.errors[:15], 1):
                print(f"{i:2d}. [{error['operation']}] {error['type']}")
                print(f"    {error['error'][:100]}")
            if len(self.errors) > 15:
                print(f"... 还有 {len(self.errors)-15} 个错误")
        else:
            print("\n✅ 太棒了! 没有发现任何问题! 系统极其稳定!")
        
        print("="*90)
        
        # 保存错误报告
        if self.errors:
            report_file = f"v78_ultra_extreme_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            import json
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.errors, f, ensure_ascii=False, indent=2)
            print(f"\n📝 错误报告已保存到: {report_file}")
        
        return len(self.errors) == 0

if __name__ == "__main__":
    test = UltraExtremeChaosTest()
    passed = test.run_full_test()
    sys.exit(0 if passed else 1)

