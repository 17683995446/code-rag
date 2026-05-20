#!/usr/bin/env python3
"""
v7.7 极度混乱场景压力测试 - 慢工出细活原则
发现真实运行时bug的高难度测试
"""

import sys
import os
import time
import threading
import random
import gc
import json
import uuid
from datetime import datetime
from collections import defaultdict, deque
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath('.')))

from kg_memory_v7_optimized import MemorySystemV7Optimized, NodeType, EdgeType


class ChaosMetrics:
    """混乱场景指标收集器"""
    
    def __init__(self):
        self.start_time = time.time()
        self.operations = defaultdict(int)
        self.errors = []
        self.latencies = defaultdict(list)
        self.concurrent_ops = 0
        self.max_concurrent = 0
        self.lock = threading.RLock()
        self.memory_samples = []
    
    def record_operation(self, op_type: str, success: bool, duration: float):
        with self.lock:
            self.operations[op_type] += 1
            self.latencies[op_type].append(duration)
            if not success:
                self.errors.append({
                    "timestamp": time.time(),
                    "type": op_type,
                    "duration": duration
                })
    
    def record_concurrency(self, current: int):
        with self.lock:
            self.concurrent_ops = current
            if current > self.max_concurrent:
                self.max_concurrent = current
    
    def record_memory(self):
        try:
            import psutil
            process = psutil.Process()
            self.memory_samples.append({
                "time": time.time() - self.start_time,
                "rss": process.memory_info().rss
            })
        except Exception:
            pass
    
    def get_summary(self) -> Dict[str, Any]:
        with self.lock:
            total_ops = sum(self.operations.values())
            avg_latencies = {}
            for op_type, lats in self.latencies.items():
                if lats:
                    avg_latencies[op_type] = {
                        "avg_ms": (sum(lats) / len(lats)) * 1000,
                        "max_ms": max(lats) * 1000,
                        "p99_ms": sorted(lats)[int(len(lats)*0.99)] * 1000
                    }
            
            return {
                "total_operations": total_ops,
                "operations_by_type": dict(self.operations),
                "error_count": len(self.errors),
                "max_concurrent": self.max_concurrent,
                "latencies": avg_latencies
            }


class ChaosWorker:
    """混乱场景工作线程 - 模拟真实用户的极端行为"""
    
    def __init__(self, worker_id: int, memory: MemorySystemV7Optimized,
                 metrics: ChaosMetrics, stop_event: threading.Event):
        self.worker_id = worker_id
        self.memory = memory
        self.metrics = metrics
        self.stop_event = stop_event
        self.personal_nodes = []
        self.personal_edges = []
        self.failure_rate = random.uniform(0, 0.3)  # 随机失败率
    
    def chaotic_remember(self) -> bool:
        """混乱的记忆操作 - 各种边缘情况"""
        try:
            start = time.time()
            
            operation_mode = random.randint(0, 5)
            
            if operation_mode == 0:
                # 正常节点添加
                label = f"chaos_{self.worker_id}_{uuid.uuid4().hex[:8]}"
                node_id = self.memory.remember(label)
                self.personal_nodes.append(label)
            
            elif operation_mode == 1:
                # 重复添加相同节点
                if self.personal_nodes:
                    repeat_label = random.choice(self.personal_nodes)
                    self.memory.remember(repeat_label)
            
            elif operation_mode == 2:
                # 非常长的标签
                long_label = f"long_label_{self.worker_id}_{'x' * random.randint(100, 1000)}"
                self.memory.remember(long_label)
                self.personal_nodes.append(long_label)
            
            elif operation_mode == 3:
                # 特殊字符标签
                special_label = f"spec_{self.worker_id}_{'!@#$%^&*()_+-=[]{}|;:,.<>? ' * 5}"
                self.memory.remember(special_label)
                self.personal_nodes.append(special_label)
            
            elif operation_mode == 4:
                # 大量属性
                big_props = {
                    f"field_{i}": f"value_{i}_{uuid.uuid4().hex[:16]}"
                    for i in range(random.randint(10, 100))
                }
                label = f"big_prop_{self.worker_id}_{uuid.uuid4().hex[:8]}"
                self.memory.remember(label, properties=big_props)
                self.personal_nodes.append(label)
            
            elif operation_mode == 5:
                # 不计算向量
                label = f"no_emb_{self.worker_id}_{uuid.uuid4().hex[:8]}"
                self.memory.remember(label, compute_embedding=False)
                self.personal_nodes.append(label)
            
            duration = time.time() - start
            self.metrics.record_operation("remember", True, duration)
            return True
        
        except Exception as e:
            self.metrics.record_operation("remember", False, time.time() - start)
            return False
    
    def chaotic_connect(self) -> bool:
        """混乱的连接操作"""
        try:
            start = time.time()
            
            if len(self.personal_nodes) < 2:
                time.sleep(0.001)
                return True
            
            # 各种连接模式
            connect_mode = random.randint(0, 4)
            
            if connect_mode == 0:
                # 正常连接
                source = random.choice(self.personal_nodes)
                target = random.choice(self.personal_nodes)
                edge_id = self.memory.connect(source, target)
                if edge_id:
                    self.personal_edges.append(edge_id)
            
            elif connect_mode == 1:
                # 自连接
                label = random.choice(self.personal_nodes)
                self.memory.connect(label, label)
            
            elif connect_mode == 2:
                # 尝试连接不存在的节点
                fake_source = f"fake_{uuid.uuid4().hex}"
                fake_target = f"fake_{uuid.uuid4().hex}"
                self.memory.connect(fake_source, fake_target)
            
            elif connect_mode == 3:
                # 多种关系类型
                source = random.choice(self.personal_nodes)
                target = random.choice(self.personal_nodes)
                edge_types = list(EdgeType)
                random_type = random.choice(edge_types)
                self.memory.connect(source, target, random_type)
            
            elif connect_mode == 4:
                # 高权重
                source = random.choice(self.personal_nodes)
                target = random.choice(self.personal_nodes)
                self.memory.connect(source, target, weight=random.uniform(0.001, 1000))
            
            duration = time.time() - start
            self.metrics.record_operation("connect", True, duration)
            return True
        
        except Exception as e:
            self.metrics.record_operation("connect", False, time.time() - start)
            return False
    
    def chaotic_query(self) -> bool:
        """混乱的查询操作"""
        try:
            start = time.time()
            
            query_mode = random.randint(0, 5)
            
            if query_mode == 0:
                # 正常查询
                if self.personal_nodes:
                    label = random.choice(self.personal_nodes)
                    self.memory.recall(label, k=random.randint(1, 20))
            
            elif query_mode == 1:
                # 空查询
                self.memory.recall("", k=random.randint(1, 20))
            
            elif query_mode == 2:
                # 不存在的节点查询
                fake_query = f"not_exists_{uuid.uuid4().hex}"
                self.memory.recall(fake_query)
            
            elif query_mode == 3:
                # 大规模k值查询
                if self.personal_nodes:
                    label = random.choice(self.personal_nodes)
                    self.memory.recall(label, k=random.randint(100, 1000))
            
            elif query_mode == 4:
                # 重复查询相同内容（测试缓存）
                if self.personal_nodes:
                    label = random.choice(self.personal_nodes)
                    for _ in range(random.randint(10, 100)):
                        self.memory.recall(label, k=5)
            
            elif query_mode == 5:
                # 空字符串查询
                self.memory.recall(None)
            
            duration = time.time() - start
            self.metrics.record_operation("query", True, duration)
            return True
        
        except Exception as e:
            self.metrics.record_operation("query", False, time.time() - start)
            return False
    
    def chaotic_semantic_search(self) -> bool:
        """混乱的语义搜索"""
        try:
            start = time.time()
            
            search_mode = random.randint(0, 3)
            
            if search_mode == 0:
                # 正常语义搜索
                if self.personal_nodes:
                    label = random.choice(self.personal_nodes)
                    self.memory.semantic_search(label, k=random.randint(5, 50))
            
            elif search_mode == 1:
                # 不存在节点搜索
                self.memory.semantic_search(f"not_exists_{uuid.uuid4().hex}")
            
            elif search_mode == 2:
                # 极小k值
                if self.personal_nodes:
                    label = random.choice(self.personal_nodes)
                    self.memory.semantic_search(label, k=1)
            
            elif search_mode == 3:
                # 极大k值
                if self.personal_nodes:
                    label = random.choice(self.personal_nodes)
                    self.memory.semantic_search(label, k=random.randint(100, 1000))
            
            duration = time.time() - start
            self.metrics.record_operation("semantic", True, duration)
            return True
        
        except Exception as e:
            self.metrics.record_operation("semantic", False, time.time() - start)
            return False
    
    def chaotic_inference(self) -> bool:
        """混乱的推理操作"""
        try:
            start = time.time()
            
            if self.personal_nodes:
                label = random.choice(self.personal_nodes)
                depth = random.randint(1, 10)
                self.memory.infer(label, max_depth=depth)
            
            duration = time.time() - start
            self.metrics.record_operation("infer", True, duration)
            return True
        
        except Exception as e:
            self.metrics.record_operation("infer", False, time.time() - start)
            return False
    
    def chaotic_mixed(self) -> bool:
        """混合多种操作 - 最混乱的模式"""
        start = time.time()
        success = True
        
        num_ops = random.randint(2, 10)
        for _ in range(num_ops):
            op_choice = random.randint(0, 4)
            if op_choice == 0:
                if not self.chaotic_remember():
                    success = False
            elif op_choice == 1:
                if not self.chaotic_connect():
                    success = False
            elif op_choice == 2:
                if not self.chaotic_query():
                    success = False
            elif op_choice == 3:
                if not self.chaotic_semantic_search():
                    success = False
            elif op_choice == 4:
                if not self.chaotic_inference():
                    success = False
        
        duration = time.time() - start
        self.metrics.record_operation("mixed", success, duration)
        return success
    
    def run(self):
        """运行混乱场景"""
        active_threads = threading.active_count()
        
        # 随机预热
        for _ in range(random.randint(5, 20)):
            if self.stop_event.is_set():
                return
            self.chaotic_remember()
        
        # 混乱主循环
        while not self.stop_event.is_set():
            try:
                self.metrics.record_concurrency(threading.active_count())
                
                # 随机操作模式
                mode = random.randint(0, 100)
                
                if mode < 30:
                    self.chaotic_remember()
                elif mode < 50:
                    self.chaotic_connect()
                elif mode < 70:
                    self.chaotic_query()
                elif mode < 85:
                    self.chaotic_semantic_search()
                elif mode < 95:
                    self.chaotic_inference()
                else:
                    self.chaotic_mixed()
                
                # 随机延迟 - 模拟真实用户思考时间
                if random.random() < 0.3:
                    delay = random.uniform(0.0001, 0.01)
                    time.sleep(delay)
                
                # 随机失败模拟
                if random.random() < self.failure_rate:
                    raise Exception("Chaotic failure injection")
            
            except Exception:
                pass  # 故意忽略异常，继续测试


class ChaosTester:
    """混乱测试主控制器"""
    
    def __init__(self, duration_minutes: int = 60, num_workers: int = 50):
        self.duration_minutes = duration_minutes
        self.num_workers = num_workers
        self.memory = MemorySystemV7Optimized()
        self.metrics = ChaosMetrics()
        self.stop_event = threading.Event()
        self.workers = []
    
    def initialize_with_chaos(self):
        """用混乱的数据初始化系统"""
        print("🎯 初始化混乱数据...")
        
        initial_nodes = random.randint(1000, 5000)
        for i in range(initial_nodes):
            label = f"init_chaos_{i}_{uuid.uuid4().hex[:8]}"
            if random.random() < 0.7:
                self.memory.remember(label)
            else:
                self.memory.remember(label, compute_embedding=False)
        
        initial_edges = random.randint(500, 3000)
        for i in range(initial_edges):
            try:
                source = f"init_chaos_{random.randint(0, initial_nodes-1)}_xxx"
                target = f"init_chaos_{random.randint(0, initial_nodes-1)}_xxx"
                self.memory.connect(source, target)
            except Exception:
                pass
        
        print(f"✅ 初始化完成: {initial_nodes:,}节点, {initial_edges:,}边尝试")
    
    def run(self):
        """运行完整混乱测试"""
        print("\n" + "="*80)
        print("🔥 v7.7 极度混乱场景压力测试 - 发现真实运行时bug")
        print("="*80)
        print(f"测试时间: {self.duration_minutes}分钟")
        print(f"工作线程: {self.num_workers}")
        print(f"混乱级别: 极度混乱 🔥🔥🔥")
        print("="*80 + "\n")
        
        # 初始化
        self.initialize_with_chaos()
        
        # 启动工作线程
        print(f"🚀 启动 {self.num_workers} 个混乱工作线程...")
        
        for worker_id in range(self.num_workers):
            worker = ChaosWorker(worker_id, self.memory, self.metrics, self.stop_event)
            thread = threading.Thread(target=worker.run, daemon=True)
            thread.start()
            self.workers.append(thread)
        
        print("✅ 所有混乱线程启动完成！\n")
        
        # 监控循环
        start_time = time.time()
        last_report = start_time
        report_interval = 60
        
        while time.time() - start_time < self.duration_minutes * 60:
            try:
                time.sleep(10)
                
                # 定期报告
                if time.time() - last_report > report_interval:
                    self.report_progress(start_time)
                    last_report = time.time()
                
                # 记录指标
                self.metrics.record_memory()
                
                # 定期GC
                if random.random() < 0.01:
                    gc.collect()
            
            except KeyboardInterrupt:
                print("\n⚠️ 用户中断测试...")
                break
        
        # 结束测试
        self.stop_event.set()
        
        # 等待线程结束
        print("\n⏹️ 测试结束，等待线程退出...")
        time.sleep(5)
        
        # 最终报告
        self.final_report()
    
    def report_progress(self, start_time: float):
        """报告进度"""
        elapsed = time.time() - start_time
        summary = self.metrics.get_summary()
        stats = self.memory.get_statistics()
        
        print(f"\n📊 进度报告 [{elapsed/60:.1f}分钟]")
        print(f"   总操作数: {summary['total_operations']:,}")
        print(f"   数据规模: {stats['nodes']:,}节点, {stats['edges']:,}边")
        print(f"   错误数: {summary['error_count']}")
        
        if summary['latencies']:
            print(f"   操作延迟:")
            for op_type, lat in summary['latencies'].items():
                print(f"     {op_type:15} - avg: {lat['avg_ms']:.2f}ms, max: {lat['max_ms']:.2f}ms")
    
    def final_report(self):
        """生成最终报告"""
        print("\n" + "="*80)
        print("🎯 极度混乱场景测试 - 最终报告")
        print("="*80)
        
        summary = self.metrics.get_summary()
        final_stats = self.memory.get_statistics()
        
        print(f"\n📊 测试结果:")
        print(f"   总操作数: {summary['total_operations']:,}")
        print(f"   操作分布: {json.dumps(summary['operations_by_type'], indent=6)}")
        print(f"   错误数: {summary['error_count']}")
        print(f"   最大并发: {summary['max_concurrent']}")
        print(f"   最终节点数: {final_stats['nodes']:,}")
        print(f"   最终边数: {final_stats['edges']:,}")
        
        if summary['error_count'] > 0:
            print(f"\n⚠️ 发现 {summary['error_count']} 个潜在问题！")
            print(f"   需要进一步分析和修复...")
        
        print("\n" + "="*80)
        print("✅ 极度混乱场景测试完成！")
        print("="*80)
        
        # 保存报告
        report_file = f"chaos_test_report_{uuid.uuid4().hex[:8]}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": summary,
                "final_stats": final_stats,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"\n📄 报告保存至: {report_file}")


def main():
    """主程序"""
    import argparse
    
    parser = argparse.ArgumentParser(description="v7.7极度混乱场景测试")
    parser.add_argument("--duration", type=int, default=30, help="测试分钟数")
    parser.add_argument("--workers", type=int, default=50, help="工作线程数")
    parser.add_argument("--quick", action="store_true", help="快速测试模式(5分钟)")
    
    args = parser.parse_args()
    
    if args.quick:
        args.duration = 5
        args.workers = 30
    
    tester = ChaosTester(args.duration, args.workers)
    tester.run()


if __name__ == "__main__":
    main()
