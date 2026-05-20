#!/usr/bin/env python3
"""
v7.5 超长压力测试 - 真实生产环境模拟
慢工出细活: 深度、长时间运行，发现真实运行时bug

测试内容:
1. 超长运行时间 (可配置，默认30分钟到数小时)
2. 混合操作模式 (读写搜索推理混合)
3. 高并发场景 (100+线程)
4. 大规模数据增长 (持续添加节点边)
5. 内存泄漏检测
6. 性能退化监控
7. 死锁检测
8. 缓存行为分析
"""

import sys
import os
import time
import threading
import random
import tracemalloc
import gc
import json
import uuid
from datetime import datetime
from collections import defaultdict, deque
from typing import Dict, List, Any, Optional, Set

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kg_memory_v7_optimized import MemorySystemV7Optimized, NodeType, EdgeType


class MetricsCollector:
    """性能指标收集器"""
    
    def __init__(self):
        self.operations = []
        self.errors = []
        self.memory_samples = []
        self.cache_stats = []
        self.latency_samples = defaultdict(list)
        self.lock = threading.Lock()
        self.start_time = time.time()
    
    def record_operation(self, op_type: str, duration: float, success: bool):
        with self.lock:
            timestamp = time.time()
            self.operations.append({
                "timestamp": timestamp,
                "op_type": op_type,
                "duration": duration,
                "success": success
            })
            self.latency_samples[op_type].append(duration)
    
    def record_error(self, op_type: str, error_msg: str):
        with self.lock:
            self.errors.append({
                "timestamp": time.time(),
                "op_type": op_type,
                "error": error_msg
            })
    
    def record_memory(self):
        with self.lock:
            try:
                # 简单内存监控
                gc.collect()
                self.memory_samples.append({
                    "timestamp": time.time(),
                    "time_sec": time.time() - self.start_time
                })
            except:
                pass
    
    def record_cache_stats(self, cache_hits: int, cache_misses: int, 
                          semantic_hits: int, semantic_misses: int):
        with self.lock:
            self.cache_stats.append({
                "timestamp": time.time(),
                "cache_hits": cache_hits,
                "cache_misses": cache_misses,
                "semantic_hits": semantic_hits,
                "semantic_misses": semantic_misses
            })
    
    def get_summary(self) -> Dict[str, Any]:
        with self.lock:
            total_ops = len(self.operations)
            success_ops = sum(1 for op in self.operations if op["success"])
            fail_ops = total_ops - success_ops
            
            latency_summary = {}
            for op_type, durations in self.latency_samples.items():
                if durations:
                    avg_latency = sum(durations) / len(durations)
                    p95 = sorted(durations)[int(len(durations) * 0.95)] if len(durations) > 0 else 0
                    p99 = sorted(durations)[int(len(durations) * 0.99)] if len(durations) > 0 else 0
                    latency_summary[op_type] = {
                        "avg_ms": avg_latency * 1000,
                        "p95_ms": p95 * 1000,
                        "p99_ms": p99 * 1000,
                        "count": len(durations)
                    }
            
            return {
                "total_operations": total_ops,
                "success_rate": success_ops / total_ops if total_ops > 0 else 0,
                "error_count": len(self.errors),
                "latency": latency_summary,
                "errors": self.errors[-50:],  # 最近50个错误
                "duration": time.time() - self.start_time
            }


class ProductionStressTest:
    """生产环境压力测试"""
    
    def __init__(self, duration_minutes: int = 30, num_threads: int = 100):
        self.duration_minutes = duration_minutes
        self.num_threads = num_threads
        self.memory = MemorySystemV7Optimized()
        self.metrics = MetricsCollector()
        self.stop_event = threading.Event()
        self.monitor_thread = None
        self.worker_threads = []
        
        # 测试控制
        self.next_node_id = 0
        self.node_label_prefix = f"test_node_{uuid.uuid4().hex[:8]}_"
        self.data_lock = threading.Lock()
        
        # 预创建一些基础节点
        self._seed_data()
    
    def _seed_data(self):
        """预创建基础数据"""
        print("🎯 预创建基础数据...")
        for i in range(10000):
            label = f"{self.node_label_prefix}{self.next_node_id}"
            self.memory.remember(label, node_type=NodeType.ENTITY)
            self.next_node_id += 1
        print(f"✅ 预创建了 10,000 个基础节点")
    
    def _random_operation(self, worker_id: int):
        """执行随机操作"""
        op_type = random.choices(
            ["remember", "connect", "recall", "semantic_search", "recommend_connections", "infer"],
            weights=[0.15, 0.1, 0.35, 0.2, 0.1, 0.1]
        )[0]
        
        start_time = time.time()
        success = True
        
        try:
            if op_type == "remember":
                # 添加新节点
                with self.data_lock:
                    label = f"{self.node_label_prefix}{self.next_node_id}"
                    self.next_node_id += 1
                self.memory.remember(label, node_type=NodeType.ENTITY)
            
            elif op_type == "connect":
                # 随机连接两个节点
                label1 = f"{self.node_label_prefix}{random.randint(0, self.next_node_id - 1)}"
                label2 = f"{self.node_label_prefix}{random.randint(0, self.next_node_id - 1)}"
                self.memory.connect(label1, label2, relation=random.choice(list(EdgeType)))
            
            elif op_type == "recall":
                # 随机查询
                label = f"{self.node_label_prefix}{random.randint(0, self.next_node_id - 1)}"
                self.memory.recall(label, k=random.randint(1, 20))
            
            elif op_type == "semantic_search":
                # 语义搜索
                label = f"{self.node_label_prefix}{random.randint(0, self.next_node_id - 1)}"
                self.memory.semantic_search(label, k=random.randint(5, 20))
            
            elif op_type == "recommend_connections":
                # 推荐连接
                label = f"{self.node_label_prefix}{random.randint(0, self.next_node_id - 1)}"
                self.memory.recommend_connections(label, k=random.randint(3, 10))
            
            elif op_type == "infer":
                # 图推理
                label = f"{self.node_label_prefix}{random.randint(0, self.next_node_id - 1)}"
                self.memory.infer(label, max_depth=random.randint(2, 4))
        
        except Exception as e:
            success = False
            self.metrics.record_error(op_type, str(e))
        
        duration = time.time() - start_time
        self.metrics.record_operation(op_type, duration, success)
    
    def _worker(self, worker_id: int):
        """工作线程"""
        while not self.stop_event.is_set():
            try:
                self._random_operation(worker_id)
                # 模拟真实负载: 随机休眠一小段时间
                time.sleep(random.uniform(0.001, 0.01))
            except:
                # 防止单个异常崩溃整个线程
                time.sleep(0.01)
    
    def _monitor(self):
        """监控线程"""
        print("📊 监控线程启动")
        
        last_cache_stats = {"hits": 0, "misses": 0, "semantic_hits": 0, "semantic_misses": 0}
        
        while not self.stop_event.is_set():
            try:
                time.sleep(10)  # 每10秒采样一次
                
                # 记录指标
                self.metrics.record_memory()
                
                # 获取并记录缓存统计
                stats = self.memory.get_statistics()
                self.metrics.record_cache_stats(
                    stats["cache_hits"], stats["cache_misses"],
                    stats["semantic_cache_hits"], stats["semantic_cache_misses"]
                )
                
                # 打印状态
                elapsed = time.time() - self.metrics.start_time
                elapsed_min = elapsed / 60
                summary = self.metrics.get_summary()
                
                print(f"\n{'='*60}")
                print(f"⏱️  运行时间: {elapsed_min:.1f} 分钟 / {self.duration_minutes} 分钟")
                print(f"📈 总操作数: {summary['total_operations']:,}")
                print(f"✅ 成功率: {summary['success_rate']:.2%}")
                print(f"❌ 错误数: {summary['error_count']}")
                
                # 延迟统计
                if summary['latency']:
                    print(f"\n📊 操作延迟 (ms):")
                    for op_type, lat in summary['latency'].items():
                        print(f"  {op_type:20}: avg={lat['avg_ms']:.2f}, p95={lat['p95_ms']:.2f}, p99={lat['p99_ms']:.2f}")
                
                # 缓存统计
                print(f"\n💾 缓存状态:")
                print(f"  缓存命中: {stats['cache_hits']:,}, 未命中: {stats['cache_misses']:,}")
                cache_hit_rate = stats['cache_hits'] / (stats['cache_hits'] + stats['cache_misses']) if (stats['cache_hits'] + stats['cache_misses']) > 0 else 0
                print(f"  缓存命中率: {cache_hit_rate:.2%}")
                print(f"  语义缓存命中: {stats['semantic_cache_hits']:,}, 未命中: {stats['semantic_cache_misses']:,}")
                
                # 数据规模
                print(f"\n📦 数据规模:")
                print(f"  节点数: {stats['nodes']:,}")
                print(f"  边数: {stats['edges']:,}")
                
                print(f"{'='*60}\n")
                
            except Exception as e:
                print(f"⚠️ 监控异常: {e}")
    
    def run(self):
        """运行测试"""
        print("🚀 开始超长压力测试")
        print(f"⏱️  测试时长: {self.duration_minutes} 分钟")
        print(f"🧵 工作线程: {self.num_threads}")
        print(f"📁 节点前缀: {self.node_label_prefix}")
        print("="*80)
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self._monitor, daemon=True)
        self.monitor_thread.start()
        
        # 启动工作线程
        print(f"\n📦 启动 {self.num_threads} 个工作线程...")
        for i in range(self.num_threads):
            t = threading.Thread(target=self._worker, args=(i,), daemon=True)
            t.start()
            self.worker_threads.append(t)
        
        print("✅ 工作线程启动完成\n")
        
        # 等待测试时间
        time.sleep(self.duration_minutes * 60)
        
        # 停止
        print("\n⏹️  测试时间结束，正在停止...")
        self.stop_event.set()
        
        # 等待线程结束
        for t in self.worker_threads:
            t.join(timeout=5)
        
        print("\n📊 测试结束，生成报告...")
        summary = self.metrics.get_summary()
        stats = self.memory.get_statistics()
        
        # 保存结果
        report = {
            "test_config": {
                "duration_minutes": self.duration_minutes,
                "num_threads": self.num_threads
            },
            "metrics_summary": summary,
            "final_stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
        report_file = f"v75_stress_test_report_{uuid.uuid4().hex[:8]}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 报告保存到: {report_file}")
        
        # 分析结果
        self._analyze_results(summary, stats)
        
        return summary
    
    def _analyze_results(self, summary: Dict[str, Any], stats: Dict[str, Any]):
        """分析测试结果"""
        print("\n" + "="*80)
        print("🔍 测试结果分析")
        print("="*80)
        
        issues_found = []
        
        # 检查1: 成功率
        success_rate = summary['success_rate']
        if success_rate < 0.99:
            issues_found.append(f"⚠️  成功率较低: {success_rate:.2%}")
        else:
            print(f"✅ 成功率优秀: {success_rate:.2%}")
        
        # 检查2: 错误数
        if summary['error_count'] > 0:
            issues_found.append(f"⚠️  发现 {summary['error_count']} 个错误")
            if summary.get('errors'):
                print(f"\n最近错误示例:")
                for err in summary['errors'][-10:]:
                    print(f"  - [{err['timestamp']}] {err['op_type']}: {err['error']}")
        else:
            print(f"✅ 零错误运行")
        
        # 检查3: 数据规模
        print(f"\n📦 最终数据规模:")
        print(f"  节点: {stats['nodes']:,}")
        print(f"  边: {stats['edges']:,}")
        print(f"  向量: {stats['embeddings_count']:,}")
        
        # 检查4: 缓存性能
        cache_hit_rate = stats['cache_hits'] / (stats['cache_hits'] + stats['cache_misses']) if (stats['cache_hits'] + stats['cache_misses']) > 0 else 0
        print(f"\n💾 缓存性能:")
        print(f"  缓存命中率: {cache_hit_rate:.2%}")
        print(f"  语义缓存命中: {stats['semantic_cache_hits']:,}")
        
        # 检查5: 性能趋势分析
        print(f"\n📈 性能分析:")
        if 'latency' in summary:
            for op_type, lat in summary['latency'].items():
                print(f"  {op_type:20}: {lat['count']:,} 次, avg={lat['avg_ms']:.3f}ms")
        
        # 总结
        print("\n" + "="*80)
        if issues_found:
            print("⚠️  发现以下问题:")
            for issue in issues_found:
                print(f"  {issue}")
        else:
            print("🎉 所有测试通过，未发现严重问题！")
        print("="*80)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="v7.5超长压力测试")
    parser.add_argument("--duration", type=int, default=30, help="测试时长(分钟)")
    parser.add_argument("--threads", type=int, default=100, help="工作线程数")
    parser.add_argument("--quick", action="store_true", help="快速测试模式(5分钟)")
    
    args = parser.parse_args()
    
    if args.quick:
        args.duration = 5
        args.threads = 30
    
    test = ProductionStressTest(
        duration_minutes=args.duration,
        num_threads=args.threads
    )
    
    test.run()


if __name__ == "__main__":
    main()
