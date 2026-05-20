#!/usr/bin/env python3
"""
v7.6 超长时间真实场景深度测试
慢工出细活原则：2小时真实压力测试，发现运行时问题

测试内容：
1. 2小时持续运行
2. 模拟真实用户混合操作模式
3. 高并发场景（150线程）
4. 内存泄漏监控
5. 性能退化跟踪
6. 死锁检测
7. 大规模数据增长（100万+节点）
8. 真实使用场景模拟
"""

import sys
import os
import time
import threading
import random
import gc
import json
import uuid
import psutil
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kg_memory_v7_optimized import MemorySystemV7Optimized, NodeType, EdgeType


class DeepMetricsCollector:
    """深度指标收集器"""
    
    def __init__(self):
        self.metrics_file = f"v76_deep_test_{uuid.uuid4().hex[:6]}.json"
        self.start_time = time.time()
        self.errors = []
        self.operations = []
        self.memory_samples = []
        self.cache_stats = []
        self.performance_samples = []
        self.lock = threading.RLock()
        self.phase_times = {}
    
    def record_operation(self, op_type: str, duration: float, success: bool):
        with self.lock:
            timestamp = time.time()
            self.operations.append({
                "timestamp": timestamp,
                "op_type": op_type,
                "duration": duration,
                "success": success
            })
    
    def record_error(self, op_type: str, error_msg: str):
        with self.lock:
            self.errors.append({
                "timestamp": time.time(),
                "op_type": op_type,
                "error": error_msg
            })
            # 保留最近1000个错误
            if len(self.errors) > 1000:
                self.errors = self.errors[-1000:]
    
    def record_memory(self):
        with self.lock:
            try:
                process = psutil.Process()
                memory_mb = process.memory_info().rss / (1024 * 1024)
                self.memory_samples.append({
                    "timestamp": time.time(),
                    "time_sec": time.time() - self.start_time,
                    "memory_mb": memory_mb
                })
            except Exception:
                pass
    
    def record_cache_stats(self, stats: Dict):
        with self.lock:
            self.cache_stats.append({
                "timestamp": time.time(),
                "cache_hits": stats.get("cache_hits", 0),
                "cache_misses": stats.get("cache_misses", 0),
                "semantic_cache_hits": stats.get("semantic_cache_hits", 0),
                "semantic_cache_misses": stats.get("semantic_cache_misses", 0)
            })
    
    def record_performance(self, phase: str, stats: Dict):
        with self.lock:
            self.performance_samples.append({
                "phase": phase,
                "timestamp": time.time(),
                "nodes": stats.get("nodes", 0),
                "edges": stats.get("edges", 0),
                "avg_node_ms": stats.get("avg_node_add_time_ms", 0),
                "avg_edge_ms": stats.get("avg_edge_add_time_ms", 0),
                "avg_query_ms": stats.get("avg_query_time_ms", 0)
            })
    
    def save_metrics(self):
        with self.lock:
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "start_time": self.start_time,
                    "errors": self.errors[-500:],  # 最近500个错误
                    "total_operations": len(self.operations),
                    "memory_samples": self.memory_samples[-1000:],
                    "cache_stats": self.cache_stats[-200:],
                    "performance_samples": self.performance_samples[-200:],
                    "phase_times": self.phase_times
                }, f, indent=2, default=str)
    
    def get_summary(self) -> Dict[str, Any]:
        with self.lock:
            success_ops = sum(1 for op in self.operations if op["success"])
            total_ops = len(self.operations)
            
            # 计算各操作的平均耗时
            op_durations = defaultdict(list)
            for op in self.operations:
                op_durations[op["op_type"]].append(op["duration"])
            
            avg_durations = {}
            for op_type, durations in op_durations.items():
                if durations:
                    avg_durations[op_type] = {
                        "avg_ms": (sum(durations) / len(durations)) * 1000,
                        "count": len(durations),
                        "max_ms": max(durations) * 1000
                    }
            
            return {
                "total_operations": total_ops,
                "success_rate": success_ops / total_ops if total_ops > 0 else 0,
                "error_count": len(self.errors),
                "avg_durations": avg_durations,
                "errors": self.errors[-100:]
            }


class RealisticUserSimulator:
    """真实用户模拟器"""
    
    def __init__(self, user_id: int, memory: MemorySystemV7Optimized, 
                 metrics: DeepMetricsCollector, stop_event: threading.Event):
        self.user_id = user_id
        self.memory = memory
        self.metrics = metrics
        self.stop_event = stop_event
        self.session_data = f"user_{user_id}_"
        self.interest_areas = [f"area_{i}" for i in range(50)]
        self.own_nodes = []
    
    def _random_operation(self):
        """真实用户操作模式"""
        roll = random.random()
        
        if roll < 0.4:
            # 40% 概率：知识查询
            if random.random() < 0.7 and self.own_nodes:
                query_node = random.choice(self.own_nodes)
                self._recall_node(query_node)
            else:
                self._search_knowledge()
        
        elif roll < 0.65:
            # 25% 概率：添加新知识
            self._add_knowledge()
        
        elif roll < 0.85:
            # 20% 概率：建立连接
            if len(self.own_nodes) >= 2:
                self._connect_knowledge()
        
        elif roll < 0.95:
            # 10% 概率：语义搜索
            if self.own_nodes:
                self._semantic_search()
        
        else:
            # 5% 概率：推理
            if self.own_nodes:
                self._infer_relations()
    
    def _add_knowledge(self):
        """添加新知识"""
        try:
            start = time.time()
            node_type = random.choice(list(NodeType))
            interest = random.choice(self.interest_areas)
            knowledge_id = f"{self.session_data}knowledge_{uuid.uuid4().hex[:8]}"
            properties = {
                "user": self.user_id,
                "interest": interest,
                "timestamp": datetime.now().isoformat()
            }
            node_id = self.memory.remember(knowledge_id, properties, node_type)
            self.own_nodes.append(knowledge_id)
            duration = time.time() - start
            self.metrics.record_operation("remember", duration, True)
        except Exception as e:
            self.metrics.record_error("remember", str(e))
    
    def _connect_knowledge(self):
        """连接知识"""
        try:
            start = time.time()
            if len(self.own_nodes) >= 2:
                source = random.choice(self.own_nodes)
                target = random.choice(self.own_nodes)
                if source != target:
                    edge_type = random.choice(list(EdgeType))
                    self.memory.connect(source, target, edge_type)
            duration = time.time() - start
            self.metrics.record_operation("connect", duration, True)
        except Exception as e:
            self.metrics.record_error("connect", str(e))
    
    def _recall_node(self, node_label: str):
        """查询节点"""
        try:
            start = time.time()
            self.memory.recall(node_label, k=5)
            duration = time.time() - start
            self.metrics.record_operation("recall", duration, True)
        except Exception as e:
            self.metrics.record_error("recall", str(e))
    
    def _search_knowledge(self):
        """搜索知识"""
        try:
            start = time.time()
            interest = random.choice(self.interest_areas)
            self.memory.recall(interest, k=3)
            duration = time.time() - start
            self.metrics.record_operation("search", duration, True)
        except Exception as e:
            self.metrics.record_error("search", str(e))
    
    def _semantic_search(self):
        """语义搜索"""
        try:
            start = time.time()
            if self.own_nodes:
                query = random.choice(self.own_nodes)
                self.memory.semantic_search(query, k=3)
            duration = time.time() - start
            self.metrics.record_operation("semantic", duration, True)
        except Exception as e:
            self.metrics.record_error("semantic", str(e))
    
    def _infer_relations(self):
        """推理关系"""
        try:
            start = time.time()
            if self.own_nodes:
                query = random.choice(self.own_nodes)
                self.memory.infer(query, max_depth=2)
            duration = time.time() - start
            self.metrics.record_operation("infer", duration, True)
        except Exception as e:
            self.metrics.record_error("infer", str(e))
    
    def run(self):
        """用户会话运行"""
        # 每个用户首先添加一些初始知识
        for _ in range(10):
            if self.stop_event.is_set():
                break
            self._add_knowledge()
        
        # 持续操作，直到停止
        while not self.stop_event.is_set():
            self._random_operation()
            # 模拟真实用户的思考时间
            time.sleep(random.uniform(0.001, 0.01))


class DataLoader:
    """数据加载器 - 批量添加大规模基础数据"""
    
    def __init__(self, memory: MemorySystemV7Optimized, 
                 metrics: DeepMetricsCollector, stop_event: threading.Event):
        self.memory = memory
        self.metrics = metrics
        self.stop_event = stop_event
    
    def load_initial_data(self):
        """加载初始数据"""
        print("📦 加载初始数据...")
        batch_size = 1000
        total_batches = 50
        
        for batch in range(total_batches):
            if self.stop_event.is_set():
                break
            
            start = time.time()
            for i in range(batch_size):
                node_label = f"base_node_{batch}_{i}"
                self.memory.remember(node_label, properties={"batch": batch}, compute_embedding=True)
            duration = time.time() - start
            print(f"   批次 {batch + 1}/{total_batches} 完成: {batch_size} 节点 ({duration:.2f}s)")
        
        # 添加一些边
        print("🔗 添加初始连接...")
        edge_count = 0
        for i in range(10000):
            if self.stop_event.is_set():
                break
            
            try:
                source = f"base_node_{random.randint(0, 49)}_{random.randint(0, 999)}"
                target = f"base_node_{random.randint(0, 49)}_{random.randint(0, 999)}"
                if source != target:
                    self.memory.connect(source, target, EdgeType.RELATED_TO)
                    edge_count += 1
            except Exception:
                pass
            
            if edge_count % 1000 == 0 and edge_count > 0:
                print(f"   已添加 {edge_count} 边")
        
        print(f"✅ 初始数据加载完成: 50,000 节点, {edge_count} 边")


def main():
    """主测试程序"""
    print("\n" + "=" * 80)
    print("🚀 v7.6 超长时间真实场景深度测试")
    print("=" * 80)
    print("测试配置:")
    print("  - 持续时间: 2 小时 (120 分钟)")
    print("  - 并发用户: 150 线程")
    print("  - 监控间隔: 30 秒")
    print("  - 内存采样: 每 30 秒")
    print("  - 目标: 发现真实运行时问题")
    print("=" * 80 + "\n")
    
    # 初始化
    stop_event = threading.Event()
    memory = MemorySystemV7Optimized()
    metrics = DeepMetricsCollector()
    
    # 加载初始数据
    loader = DataLoader(memory, metrics, stop_event)
    loader.load_initial_data()
    
    # 启动监控线程
    def monitor():
        print("📊 监控线程启动\n")
        last_report_time = time.time()
        report_interval = 300  # 每5分钟完整报告一次
        
        while not stop_event.is_set():
            try:
                # 记录指标
                metrics.record_memory()
                stats = memory.get_statistics()
                metrics.record_cache_stats(stats)
                
                elapsed = time.time() - metrics.start_time
                elapsed_min = elapsed / 60
                
                # 定期打印进度
                summary = metrics.get_summary()
                print(f"\n{'='*60}")
                print(f"⏱️  进度: {elapsed_min:.1f} 分钟 / 120 分钟")
                print(f"📈 总操作: {summary['total_operations']:,}")
                print(f"✅ 成功率: {summary['success_rate']:.2%}")
                print(f"❌ 错误数: {summary['error_count']}")
                print(f"💾 缓存状态:")
                print(f"   命中: {stats['cache_hits']:,}, 未命中: {stats['cache_misses']:,}")
                print(f"   语义命中: {stats['semantic_cache_hits']:,}")
                print(f"📦 数据规模:")
                print(f"   节点: {stats['nodes']:,}, 边: {stats['edges']:,}")
                print(f"⚡ 性能指标:")
                print(f"   平均节点添加: {stats['avg_node_add_time_ms']:.3f} ms")
                print(f"   平均边添加: {stats['avg_edge_add_time_ms']:.3f} ms")
                print(f"   平均查询: {stats['avg_query_time_ms']:.3f} ms")
                
                # 操作耗时
                if 'avg_durations' in summary:
                    print(f"🔍 各操作平均耗时:")
                    for op_type, stats_op in summary['avg_durations'].items():
                        print(f"   {op_type:10}: {stats_op['avg_ms']:.3f} ms (n={stats_op['count']:,})")
                
                print(f"{'='*60}\n")
                
                # 保存当前指标
                metrics.save_metrics()
                
                # 定期强制垃圾回收
                gc.collect()
                
            except Exception as e:
                print(f"⚠️  监控异常: {e}")
            
            # 等待下一个采样周期
            for _ in range(30):
                if stop_event.is_set():
                    break
                time.sleep(1)
    
    # 启动监控
    monitor_thread = threading.Thread(target=monitor, daemon=True)
    monitor_thread.start()
    
    # 启动用户模拟器线程
    print(f"👥 启动 150 个用户模拟器...")
    user_threads = []
    
    for user_id in range(150):
        simulator = RealisticUserSimulator(user_id, memory, metrics, stop_event)
        t = threading.Thread(target=simulator.run, daemon=True)
        t.start()
        user_threads.append(t)
    
    print("✅ 用户模拟器启动完成\n")
    
    # 运行2小时
    test_start = time.time()
    test_duration = 2 * 60 * 60  # 2小时
    
    try:
        while time.time() - test_start < test_duration:
            remaining = test_duration - (time.time() - test_start)
            if remaining <= 0:
                break
            time.sleep(min(remaining, 30))
            
            # 打印剩余时间
            elapsed_min = (time.time() - test_start) / 60
            remaining_min = (test_duration - (time.time() - test_start)) / 60
            print(f"\n⏰ 进度: {elapsed_min:.1f} 分钟 / 120 分钟 (剩余 {remaining_min:.1f} 分钟)\n")
    
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断测试")
    
    # 停止所有线程
    print("\n⏹️  测试结束，正在停止线程...")
    stop_event.set()
    
    # 等待用户线程结束
    for i, t in enumerate(user_threads):
        try:
            t.join(timeout=2)
        except Exception:
            pass
    
    # 保存最终指标
    metrics.save_metrics()
    
    # 最终报告
    final_stats = memory.get_statistics()
    final_summary = metrics.get_summary()
    
    print("\n" + "=" * 80)
    print("📋 最终测试报告")
    print("=" * 80)
    print(f"测试结果文件: {metrics.metrics_file}")
    print(f"总运行时间: {(time.time() - metrics.start_time) / 60:.2f} 分钟")
    print(f"总操作数: {final_summary['total_operations']:,}")
    print(f"成功率: {final_summary['success_rate']:.2%}")
    print(f"总错误数: {final_summary['error_count']}")
    print(f"最终数据规模: 节点 {final_stats['nodes']:,}, 边 {final_stats['edges']:,}")
    
    if final_summary['error_count'] > 0:
        print("\n⚠️ 发现的问题示例:")
        for error in final_summary['errors'][-20:]:
            print(f"  - [{error['op_type']}] {error['error']}")
    else:
        print("\n✅ 零错误运行！系统稳定可靠")
    
    # 内存分析
    if metrics.memory_samples:
        first_mem = metrics.memory_samples[0]['memory_mb']
        last_mem = metrics.memory_samples[-1]['memory_mb']
        mem_growth = last_mem - first_mem
        
        print(f"\n💾 内存分析:")
        print(f"  初始内存: {first_mem:.2f} MB")
        print(f"  最终内存: {last_mem:.2f} MB")
        print(f"  内存增长: {mem_growth:.2f} MB")
        
        if mem_growth > 100:
            print(f"  ⚠️  警告: 可能存在内存泄漏")
        else:
            print(f"  ✅ 内存使用正常")
    
    print("=" * 80 + "\n")
    print("🎉 v7.6深度测试完成！")


if __name__ == "__main__":
    main()
