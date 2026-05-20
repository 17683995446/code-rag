#!/usr/bin/env python3
"""
知识图谱记忆系统 v8.0 - 超长时间测试（15分钟版）
密集运行真实场景，监控内存和性能
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

class QuickLongTermTest:
    """快速长时间测试（15分钟）"""
    
    def __init__(self):
        self.kg = MemorySystemV7Optimized()
        self.errors = []
        self.ops_total = 0
        self.lock = threading.Lock()
        self.start = time.time()
        self.end = self.start + 900  # 15分钟
        
        self.knowledge = ["Python", "React", "Docker", "AI", "FinTech", "Alice", "Bob"]
        self.ops = [("add",0.35),("connect",0.2),("query",0.25),("semantic",0.15),("infer",0.05)]
    
    def log_err(self, op, e):
        with self.lock:
            self.errors.append({"op":op,"type":type(e).__name__,"msg":str(e)[:80],"time":datetime.now().isoformat()})
        print(f"\n❌ {op} 错误: {type(e).__name__}")
    
    def snapshot(self, phase):
        with self.kg._node_lock:
            nodes = len(self.kg._nodes)
            edges = len(self.kg._edges)
        
        try:
            import resource
            mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        except Exception:
            mem = 0
        
        print(f"\n{'='*70}")
        print(f"📊 阶段 {phase}")
        print(f"{'='*70}")
        print(f"时间: {datetime.now().strftime('%H:%M:%S')}")
        print(f"节点: {nodes:,} | 边: {edges:,} | 内存: {mem:.1f}MB")
        print(f"操作数: {self.ops_total:,} | 错误数: {len(self.errors)}")
        print("="*70)
    
    def run(self):
        print("="*70)
        print("🚀 v8.0 超长时间真实场景测试（15分钟）")
        print("="*70)
        
        last_snap = time.time()
        last_report = time.time()
        
        self.snapshot(0)
        
        while time.time() < self.end:
            try:
                op = random.choices([o[0] for o in self.ops], [o[1] for o in self.ops])[0]
                
                if op == "add":
                    base = random.choice(self.knowledge)
                    suffix = random.randint(1, 1000) if random.random()>0.2 else ""
                    self.kg.remember(f"{base}{suffix}")
                
                elif op == "connect":
                    with self.kg._node_lock:
                        labels = list(self.kg._label_to_node.keys())
                    if len(labels)>=2:
                        self.kg.connect(random.choice(labels), random.choice(labels))
                
                elif op == "query":
                    self.kg.recall(random.choice(self.knowledge))
                
                elif op == "semantic":
                    self.kg.semantic_search(random.choice(self.knowledge))
                
                elif op == "infer":
                    with self.kg._node_lock:
                        labels = list(self.kg._label_to_node.keys())
                    if labels:
                        self.kg.infer(random.choice(labels))
                
                with self.lock:
                    self.ops_total += 1
                
                # 每3分钟快照
                if time.time() - last_snap >= 180:
                    self.snapshot(int((time.time()-self.start)//180))
                    gc.collect()
                    last_snap = time.time()
                
                # 每分钟报告
                if time.time() - last_report >= 60:
                    elapsed = time.time()-self.start
                    print(f"\n⏱️  [{datetime.now().strftime('%H:%M:%S')}] {elapsed/60:.1f}分钟 | 操作: {self.ops_total:,}")
                    last_report = time.time()
            
            except Exception as e:
                self.log_err(op, e)
        
        print("\n" + "="*70)
        print("📊 最终结果")
        print("="*70)
        
        self.snapshot("最终")
        
        if self.errors:
            print("\n❌ 发现问题（前10个）：")
            for i, e in enumerate(self.errors[:10],1):
                print(f"{i:2d}. {e['op']}: {e['type']}")
        else:
            print("\n✅ 太棒了！0个错误！")
        
        print("="*70)
        return len(self.errors) == 0

if __name__ == "__main__":
    test = QuickLongTermTest()
    passed = test.run()
    sys.exit(0 if passed else 1)

