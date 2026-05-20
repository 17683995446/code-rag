#!/usr/bin/env python3
"""
知识图谱记忆系统 v7.9 - 简化版终极测试
专注于核心极限场景，资源消耗更小
"""
import sys
import os
import random
import time
import threading
import gc
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kg_memory_v7_optimized import MemorySystemV7Optimized, NodeType, EdgeType

class SimplifiedUltimateTest:
    """简化版终极测试"""
    
    def __init__(self):
        self.kg = MemorySystemV7Optimized()
        self.errors = []
        self.ops_count = 0
        self.ops_lock = threading.Lock()
    
    def record_error(self, msg):
        self.errors.append({"msg": msg, "time": datetime.now().isoformat()})
        print(f"❌ {msg}")
    
    def test_race_condition(self):
        """竞态条件测试"""
        print("\n🧪 竞态条件测试: 200线程同时添加相同标签")
        label = "UltimateRaceTest"
        
        def worker():
            try:
                self.kg.remember(label)
                with self.ops_lock:
                    self.ops_count += 1
            except Exception as e:
                self.record_error(f"竞态错误: {e}")
        
        threads = [threading.Thread(target=worker) for _ in range(200)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        print(f"  ✅ 完成 | {self.ops_count}次操作 | {len(self.errors)}个错误")
    
    def test_extreme_values(self):
        """极端值测试"""
        print("\n🧪 极端值测试")
        
        self.kg.remember("Node1")
        self.kg.remember("Node2")
        
        tests = [
            ("k=-9999999999", lambda: self.kg.recall("X", k=-9999999999)),
            ("k=9999999999", lambda: self.kg.recall("X", k=9999999999)),
            ("depth=-999999", lambda: self.kg.infer("Node1", max_depth=-999999)),
            ("depth=999999", lambda: self.kg.infer("Node1", max_depth=999999)),
            ("weight=inf", lambda: self.kg.connect("Node1", "Node2", weight=float('inf'))),
            ("weight=nan", lambda: self.kg.connect("Node1", "Node2", weight=float('nan'))),
            ("weight=-inf", lambda: self.kg.connect("Node1", "Node2", weight=float('-inf'))),
        ]
        
        for name, func in tests:
            try:
                func()
                print(f"  ✅ {name}")
                with self.ops_lock:
                    self.ops_count += 1
            except Exception as e:
                self.record_error(f"{name}: {type(e).__name__}")
        
        print(f"  ✅ 完成 | {len([t for t in tests if t[1] not in [e.get('msg', '') for e in self.errors]])}/{len(tests)} 通过")
    
    def test_massive_concurrent(self):
        """大规模并发测试"""
        print("\n🧪 大规模并发测试: 200线程，30秒")
        
        def worker(wid):
            start = time.time()
            local_ops = 0
            while time.time() - start < 30:
                try:
                    op = random.choice(["add", "query", "semantic"])
                    if op == "add":
                        self.kg.remember(f"Concurrent_{wid}_{local_ops}")
                    elif op == "query":
                        self.kg.recall("Test", k=10)
                    else:
                        self.kg.semantic_search("Test", k=5)
                    local_ops += 1
                except Exception as e:
                    self.record_error(f"并发错误: {e}")
                    time.sleep(0.01)
            
            with self.ops_lock:
                self.ops_count += local_ops
        
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(200)]
        for t in threads:
            t.start()
        
        # 监控进度
        for i in range(6):
            time.sleep(5)
            with self.ops_lock:
                ops = self.ops_count
            print(f"  ⏱️  {(i+1)*5}s | 操作数: {ops:,}")
        
        for t in threads:
            t.join()
        
        print(f"  ✅ 完成 | 总操作: {self.ops_count:,}")
    
    def test_performance_degradation(self):
        """性能衰减测试"""
        print("\n🧪 性能衰减测试: 3个阶段，每个1000操作")
        
        stages = []
        for stage in range(1, 4):
            start = time.time()
            for i in range(1000):
                try:
                    self.kg.remember(f"PerfTest_{stage}_{i}")
                except Exception as e:
                    self.record_error(f"性能测试错误: {e}")
            
            elapsed = time.time() - start
            ops_per_sec = 1000 / elapsed if elapsed > 0 else 0
            stages.append(ops_per_sec)
            print(f"  阶段{stage}: {ops_per_sec:.0f} ops/s ({elapsed:.2f}s)")
        
        if len(stages) >= 2:
            degradation = (stages[0] - stages[-1]) / stages[0] * 100 if stages[0] > 0 else 0
            print(f"  📊 性能衰减: {degradation:.1f}%")
            if degradation < 30:
                print(f"  ✅ 性能衰减可接受")
            else:
                print(f"  ⚠️  性能衰减较明显")
    
    def run_all(self):
        """运行所有测试"""
        print("="*80)
        print("🚀 v7.9 简化版终极测试")
        print("="*80)
        
        start = time.time()
        
        self.test_race_condition()
        self.test_extreme_values()
        self.test_massive_concurrent()
        self.test_performance_degradation()
        
        total = time.time() - start
        
        print("\n" + "="*80)
        print("📊 测试总结")
        print("="*80)
        print(f"总时间: {total:.1f}秒")
        print(f"总操作: {self.ops_count:,}")
        
        with self.kg._node_lock:
            nodes = len(self.kg._nodes)
            edges = len(self.kg._edges)
        
        print(f"节点: {nodes:,} | 边: {edges:,}")
        
        if self.errors:
            print(f"\n❌ 错误数: {len(self.errors)}")
            error_types = {}
            for e in self.errors:
                msg = e['msg']
                err_type = msg.split(':')[0] if ':' in msg else msg
                error_types[err_type] = error_types.get(err_type, 0) + 1
            
            for t, c in sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {t}: {c}次")
        else:
            print("\n✅ 太棒了！0个错误！")
        
        print("="*80)
        return len(self.errors) == 0

if __name__ == "__main__":
    test = SimplifiedUltimateTest()
    passed = test.run_all()
    sys.exit(0 if passed else 1)

