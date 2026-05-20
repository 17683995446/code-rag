#!/usr/bin/env python3
"""
知识图谱记忆系统 v8.0 - 超长时间真实场景测试
连续运行2小时，模拟真实用户行为，监控内存泄漏和性能衰减

测试内容：
1. 真实用户行为模拟（添加、查询、搜索、推理、连接）
2. 每30分钟完整测试快照
3. 内存使用监控
4. 性能趋势监控
5. 错误记录和报警
"""
import sys
import os
import random
import time
import threading
import gc
import tracemalloc
from typing import List, Dict, Any
from datetime import datetime
import json

# 添加上级目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kg_memory_v7_optimized import MemorySystemV7Optimized, NodeType, EdgeType

class UltraLongTermStabilityTest:
    """超长时间稳定性测试"""
    
    def __init__(self, duration_hours: float = 2.0):
        self.kg = MemorySystemV7Optimized()
        self.duration_hours = duration_hours
        self.errors = []
        self.warnings = []
        self.performance_data = []
        self.memory_data = []
        
        self.lock = threading.Lock()
        self.running = True
        
        # 真实知识数据
        self.knowledge_domains = {
            "tech": ["Python", "JavaScript", "TypeScript", "Go", "Rust", "React", "Vue", "Node.js", 
                    "Docker", "Kubernetes", "PostgreSQL", "MongoDB", "Redis", "AWS", "GCP", "Azure"],
            "business": ["E-Commerce", "FinTech", "Healthcare", "EdTech", "IoT", "AI", "ML", 
                        "Blockchain", "Metaverse", "AR", "VR"],
            "people": ["Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Henry"],
            "projects": ["Project Alpha", "Project Beta", "Project Gamma", "Project Delta"],
        }
        
        self.operations = [
            ("add", 0.35),
            ("connect", 0.20),
            ("query", 0.25),
            ("semantic", 0.12),
            ("infer", 0.06),
            ("recommend", 0.02),
        ]
        
        # 记录开始时间
        self.start_time = time.time()
        self.end_time = self.start_time + duration_hours * 3600
        
        print("="*100)
        print(f"🚀 知识图谱记忆系统 v8.0 - 超长时间真实场景测试")
        print(f"⏱️  测试时长: {duration_hours:.1f}小时")
        print(f"🚀 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*100)
    
    def log_error(self, op: str, e: Exception, context: str = ""):
        with self.lock:
            err = {
                "operation": op,
                "error_type": type(e).__name__,
                "error_msg": str(e),
                "context": context,
                "time": datetime.now().isoformat(),
            }
            self.errors.append(err)
            print(f"\n❌ ERROR [{op}]: {type(e).__name__}: {str(e)[:100]}")
    
    def log_warning(self, msg: str):
        with self.lock:
            warn = {
                "message": msg,
                "time": datetime.now().isoformat(),
            }
            self.warnings.append(warn)
            print(f"\n⚠️  WARNING: {msg}")
    
    def get_memory_usage(self) -> float:
        """获取当前内存使用(MB)"""
        try:
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            return usage.ru_maxrss / 1024  # MB
        except Exception:
            return 0.0
    
    def record_performance_snapshot(self, phase: int):
        """记录性能快照"""
        snapshot = {
            "phase": phase,
            "time_elapsed": time.time() - self.start_time,
            "time": datetime.now().isoformat(),
            "memory_mb": self.get_memory_usage(),
        }
        
        # 测量各操作的性能
        performance = {}
        operations_test = [
            ("add", lambda: self.kg.remember(f"Snapshot_{phase}_Test_{time.time()}")),
            ("query", lambda: self.kg.recall("Python", k=10)),
            ("semantic", lambda: self.kg.semantic_search("Python", k=5)),
        ]
        
        for op_name, func in operations_test:
            try:
                start = time.time()
                for i in range(100):
                    func()
                elapsed = time.time() - start
                performance[op_name] = elapsed / 100
            except Exception as e:
                self.log_error(f"snapshot_{op_name}", e)
                performance[op_name] = -1
        
        snapshot["operations"] = performance
        
        # 统计数据
        with self.kg._node_lock:
            snapshot["nodes"] = len(self.kg._nodes)
            snapshot["edges"] = len(self.kg._edges)
        
        with self.lock:
            self.performance_data.append(snapshot)
            self.memory_data.append(snapshot["memory_mb"])
        
        print(f"\n{'='*100}")
        print(f"📊 阶段 {phase} - 性能快照")
        print(f"{'='*100}")
        print(f"时间: {snapshot['time']}")
        print(f"节点: {snapshot['nodes']:,} | 边: {snapshot['edges']:,}")
        print(f"内存: {snapshot['memory_mb']:.1f}MB")
        print(f"操作性能(平均/100次):")
        for op, t in performance.items():
            if t >= 0:
                print(f"  {op}: {t*1000:.1f}ms")
        print("="*100)
    
    def simulate_real_user_behavior(self):
        """模拟真实用户行为"""
        phase = 0
        last_snapshot = time.time()
        last_report = time.time()
        
        operations_total = 0
        
        while time.time() < self.end_time and self.running:
            try:
                # 随机选择操作
                op_type = random.choices([o[0] for o in self.operations], weights=[o[1] for o in self.operations])[0]
                
                if op_type == "add":
                    domain = random.choice(list(self.knowledge_domains.keys()))
                    base = random.choice(self.knowledge_domains[domain])
                    suffix = random.randint(1, 1000) if random.random() > 0.3 else ""
                    label = f"{base}{suffix}"
                    node_type = random.choice(list(NodeType))
                    self.kg.remember(label, node_type=node_type)
                
                elif op_type == "connect":
                    with self.kg._node_lock:
                        labels = list(self.kg._label_to_node.keys())
                    if len(labels) >= 2:
                        src = random.choice(labels)
                        tgt = random.choice(labels)
                        rel_type = random.choice(list(EdgeType))
                        weight = random.random() * 2
                        self.kg.connect(src, tgt, relation=rel_type, weight=weight)
                
                elif op_type == "query":
                    domain = random.choice(list(self.knowledge_domains.keys()))
                    search_term = random.choice(self.knowledge_domains[domain])
                    k = random.randint(1, 20)
                    self.kg.recall(search_term, k=k)
                
                elif op_type == "semantic":
                    domain = random.choice(list(self.knowledge_domains.keys()))
                    search_term = random.choice(self.knowledge_domains[domain])
                    k = random.randint(1, 10)
                    self.kg.semantic_search(search_term, k=k)
                
                elif op_type == "infer":
                    with self.kg._node_lock:
                        labels = list(self.kg._label_to_node.keys())
                    if labels:
                        concept = random.choice(labels)
                        depth = random.randint(1, 4)
                        self.kg.infer(concept, max_depth=depth)
                
                elif op_type == "recommend":
                    with self.kg._node_lock:
                        labels = list(self.kg._label_to_node.keys())
                    if labels:
                        label = random.choice(labels)
                        k = random.randint(1, 5)
                        self.kg.recommend_connections(label, k=k)
                
                operations_total += 1
                
                # 每30分钟记录快照
                if time.time() - last_snapshot >= 1800:
                    phase += 1
                    self.record_performance_snapshot(phase)
                    last_snapshot = time.time()
                    gc.collect()
                
                # 每10分钟报告进度
                if time.time() - last_report >= 600:
                    elapsed = time.time() - self.start_time
                    remaining = max(0, self.end_time - time.time())
                    current_memory = self.get_memory_usage()
                    
                    with self.kg._node_lock:
                        nodes = len(self.kg._nodes)
                        edges = len(self.kg._edges)
                    
                    print(f"\n⏱️  [{datetime.now().strftime('%H:%M:%S')}] 进度更新")
                    print(f"  已运行: {elapsed/60:.1f}分钟 | 剩余: {remaining/60:.1f}分钟")
                    print(f"  总操作: {operations_total:,}")
                    print(f"  节点: {nodes:,} | 边: {edges:,}")
                    print(f"  内存: {current_memory:.1f}MB")
                    print(f"  错误数: {len(self.errors)} | 警告数: {len(self.warnings)}")
                    
                    last_report = time.time()
            
            except Exception as e:
                self.log_error(f"simulate_{op_type}", e)
                time.sleep(0.1)
        
        print(f"\n✅ 模拟用户行为结束!")
    
    def analyze_results(self):
        """分析测试结果"""
        print("\n" + "="*100)
        print("📊 超长时间测试 - 结果分析")
        print("="*100)
        
        total_elapsed = time.time() - self.start_time
        
        with self.kg._node_lock:
            final_nodes = len(self.kg._nodes)
            final_edges = len(self.kg._edges)
        
        final_memory = self.get_memory_usage()
        
        print(f"\n📈 总体统计:")
        print(f"  总运行时间: {total_elapsed/3600:.1f}小时")
        print(f"  最终节点: {final_nodes:,}")
        print(f"  最终边: {final_edges:,}")
        print(f"  最终内存: {final_memory:.1f}MB")
        
        # 性能趋势分析
        if len(self.performance_data) >= 2:
            first = self.performance_data[0]
            last = self.performance_data[-1]
            
            print(f"\n📊 性能趋势:")
            for op in ["add", "query", "semantic"]:
                if first["operations"].get(op, -1) >= 0 and last["operations"].get(op, -1) >= 0:
                    delta = (last["operations"][op] - first["operations"][op]) / first["operations"][op] * 100 if first["operations"][op] > 0 else 0
                    print(f"  {op}: {delta:+.1f}%")
            
            memory_delta = (last["memory_mb"] - first["memory_mb"]) / first["memory_mb"] * 100 if first["memory_mb"] > 0 else 0
            print(f"  内存增长: {memory_delta:+.1f}%")
        
        # 错误分析
        if self.errors:
            print(f"\n❌ 发现 {len(self.errors)} 个错误:")
            error_types = {}
            for err in self.errors:
                err_type = err["error_type"]
                error_types[err_type] = error_types.get(err_type, 0) + 1
            
            for err_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {err_type}: {count}次")
            
            print("\n详细错误(前10个):")
            for i, err in enumerate(self.errors[:10], 1):
                print(f"{i:2d}. [{err['operation']}] {err['error_type']}: {err['error_msg'][:80]}")
        else:
            print(f"\n✅ 太棒了! 0个错误!")
        
        if self.warnings:
            print(f"\n⚠️  警告({len(self.warnings)}):")
            for i, warn in enumerate(self.warnings[:3], 1):
                print(f"  {i}. {warn['message']}")
        
        print("\n" + "="*100)
        
        # 保存结果到JSON
        output = {
            "summary": {
                "total_elapsed_hours": total_elapsed/3600,
                "final_nodes": final_nodes,
                "final_edges": final_edges,
                "final_memory_mb": final_memory,
                "error_count": len(self.errors),
                "warning_count": len(self.warnings),
            },
            "performance_data": self.performance_data,
            "errors": self.errors,
            "warnings": self.warnings,
        }
        
        filename = f"v8_ultra_long_term_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            print(f"\n📁 结果已保存到: {filename}")
        except Exception as e:
            print(f"⚠️  无法保存结果: {e}")
        
        print("="*100)
        
        return len(self.errors) == 0
    
    def run(self):
        """运行测试"""
        print(f"\n🚀 开始模拟真实用户行为...")
        print(f"   每10分钟报告进度, 每30分钟记录性能快照\n")
        
        # 初始快照
        self.record_performance_snapshot(0)
        
        # 开始模拟
        self.simulate_real_user_behavior()
        
        # 分析结果
        return self.analyze_results()

if __name__ == "__main__":
    try:
        # 默认运行30分钟快速测试(避免过长), 可通过参数修改时间
        duration = 0.5  # 0.5小时=30分钟
        if len(sys.argv) > 1:
            try:
                duration = float(sys.argv[1])
            except ValueError:
                pass
        
        test = UltraLongTermStabilityTest(duration_hours=duration)
        passed = test.run()
        sys.exit(0 if passed else 1)
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️  测试被用户中断")
        sys.exit(1)

