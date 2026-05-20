#!/usr/bin/env python3
"""
知识图谱记忆系统 v7.0 - 超长时间压力测试
持续运行1小时以上，进行大规模复杂操作，持续监控系统稳定性
"""
import sys
import os
import time
import random
import json
import tempfile
import threading
import traceback
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kg_memory_v7 import MemorySystemV7, NodeType, EdgeType


class HourLongStressTest:
    """超长时间压力测试"""
    
    def __init__(self, duration_seconds=3600):  # 默认1小时
        self.duration_seconds = duration_seconds
        self.results = {
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "target_duration": duration_seconds,
            "actual_duration": 0,
            "bugs_found": [],
            "warnings": [],
            "metrics": {
                "operations": {
                    "total": 0,
                    "success": 0,
                    "failure": 0,
                    "by_type": defaultdict(int)
                },
                "performance": {
                    "timestamps": [],
                    "node_counts": [],
                    "edge_counts": [],
                    "operation_rates": []
                },
                "errors": [],
                "checkpoints": []
            },
            "final_stats": {}
        }
        
        self.memory = None
        self.stop_flag = threading.Event()
        self.stats_lock = threading.Lock()
        
    def log_bug(self, bug_type, description, details=None):
        """记录发现的Bug"""
        with self.stats_lock:
            bug = {
                "type": bug_type,
                "description": description,
                "details": details,
                "timestamp": datetime.now().isoformat()
            }
            self.results['bugs_found'].append(bug)
        print(f"❌ [BUG] {bug_type}: {description}")
        if details:
            print(f"    详情: {details}")
    
    def log_warning(self, warning_type, description):
        """记录警告"""
        with self.stats_lock:
            warning = {
                "type": warning_type,
                "description": description,
                "timestamp": datetime.now().isoformat()
            }
            self.results['warnings'].append(warning)
        print(f"⚠️  [警告] {warning_type}: {description}")
    
    def record_metric(self, metric_type, value):
        """记录指标"""
        with self.stats_lock:
            self.results['metrics']['performance'][metric_type].append(value)
    
    def record_operation(self, op_type, success=True, error=None):
        """记录操作"""
        with self.stats_lock:
            self.results['metrics']['operations']['total'] += 1
            self.results['metrics']['operations']['by_type'][op_type] += 1
            if success:
                self.results['metrics']['operations']['success'] += 1
            else:
                self.results['metrics']['operations']['failure'] += 1
                if len(self.results['metrics']['errors']) < 100:
                    self.results['metrics']['errors'].append({
                        "type": op_type,
                        "error": str(error),
                        "timestamp": datetime.now().isoformat()
                    })
    
    def operation_worker(self, worker_id):
        """操作工作线程"""
        local_ops = 0
        local_success = 0
        local_failure = 0
        
        while not self.stop_flag.is_set():
            try:
                # 随机选择操作类型
                op = random.choice([
                    'add_node', 'add_edge', 'search', 'infer', 
                    'semantic', 'recommend', 'recall', 'connect'
                ])
                
                if op == 'add_node':
                    label = f"worker{worker_id}_node_{local_ops}_{time.time()}"
                    self.memory.remember(
                        label, 
                        node_type=random.choice([NodeType.ENTITY, NodeType.CONCEPT]),
                        properties={"worker": worker_id, "ops": local_ops}
                    )
                elif op == 'add_edge':
                    stats = self.memory.get_statistics()
                    if stats['nodes'] >= 2:
                        a = random.randint(0, stats['nodes']-1)
                        b = random.randint(0, stats['nodes']-1)
                        if a != b:
                            self.memory.connect(f"worker{a}_node_0", f"worker{b}_node_0")
                elif op == 'search':
                    self.memory.recall("worker", k=10)
                elif op == 'infer':
                    self.memory.infer("worker0_node_0", max_depth=3)
                elif op == 'semantic':
                    self.memory.semantic_search("test", k=5)
                elif op == 'recommend':
                    self.memory.recommend_connections("worker0_node_0", k=3)
                elif op == 'recall':
                    self.memory.recall("worker", k=20)
                elif op == 'connect':
                    stats = self.memory.get_statistics()
                    if stats['nodes'] >= 2:
                        a = random.randint(0, min(100, stats['nodes'])-1)
                        b = random.randint(0, min(100, stats['nodes'])-1)
                        if a != b:
                            self.memory.connect(f"worker{a}_node_0", f"worker{b}_node_0")
                
                local_ops += 1
                local_success += 1
                self.record_operation(op, success=True)
                
            except Exception as e:
                local_failure += 1
                self.record_operation(op, success=False, error=e)
                if local_failure < 5:
                    self.log_bug(f"{op}_error", f"{op}操作失败", str(e))
    
    def monitoring_worker(self):
        """监控工作线程"""
        checkpoint_interval = 60  # 每分钟记录一次
        last_checkpoint = 0
        
        while not self.stop_flag.is_set():
            try:
                current_time = time.time()
                elapsed = current_time - self.start_time
                
                # 检查是否该记录检查点
                if elapsed - last_checkpoint >= checkpoint_interval:
                    stats = self.memory.get_statistics()
                    
                    checkpoint = {
                        "time": elapsed,
                        "elapsed_formatted": self.format_time(elapsed),
                        "nodes": stats['nodes'],
                        "edges": stats['edges'],
                        "total_ops": self.results['metrics']['operations']['total'],
                        "success_ops": self.results['metrics']['operations']['success'],
                        "failure_ops": self.results['metrics']['operations']['failure']
                    }
                    
                    with self.stats_lock:
                        self.results['metrics']['checkpoints'].append(checkpoint)
                    
                    ops_per_second = checkpoint['total_ops'] / elapsed if elapsed > 0 else 0
                    
                    print(f"\n{'='*80}")
                    print(f"⏱️  检查点 @ {checkpoint['elapsed_formatted']}")
                    print(f"  📊 节点: {checkpoint['nodes']:,}, 边: {checkpoint['edges']:,}")
                    print(f"  ⚡ 操作: {checkpoint['total_ops']:,} (成功: {checkpoint['success_ops']:,}, 失败: {checkpoint['failure_ops']:,})")
                    print(f"  🚀 速率: {ops_per_second:.0f} ops/s")
                    print(f"{'='*80}\n")
                    
                    last_checkpoint = elapsed
                
                time.sleep(1)  # 每秒检查一次
                
            except Exception as e:
                self.log_bug("monitor_error", "监控线程出错", str(e))
    
    def format_time(self, seconds):
        """格式化时间"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def run(self):
        """运行超长时间测试"""
        print("\n" + "="*80)
        print("🚀 知识图谱记忆系统 v7.0 - 超长时间压力测试")
        print("="*80)
        print(f"🎯 目标时长: {self.format_time(self.duration_seconds)} ({self.duration_seconds}秒)")
        print(f"⏰ 开始时间: {self.results['start_time']}")
        print("="*80)
        
        self.memory = MemorySystemV7()
        self.start_time = time.time()
        
        # 准备初始数据
        print("\n📦 准备初始数据...")
        initial_nodes = 1000
        for i in range(initial_nodes):
            self.memory.remember(
                f"worker{i}_node_0", 
                node_type=NodeType.ENTITY,
                properties={"initial": True, "worker": i}
            )
        print(f"  ✅ 已创建 {initial_nodes} 个初始节点")
        
        initial_edges = 500
        for i in range(initial_edges):
            a = random.randint(0, initial_nodes-1)
            b = random.randint(0, initial_nodes-1)
            if a != b:
                self.memory.connect(f"worker{a}_node_0", f"worker{b}_node_0")
        print(f"  ✅ 已创建 {initial_edges} 条初始边")
        
        # 启动操作线程
        num_workers = 20
        print(f"\n🧵 启动 {num_workers} 个操作线程...")
        worker_threads = []
        for i in range(num_workers):
            t = threading.Thread(target=self.operation_worker, args=(i,))
            t.daemon = True
            t.start()
            worker_threads.append(t)
        
        # 启动监控线程
        print("👁️  启动监控线程...")
        monitor_thread = threading.Thread(target=self.monitoring_worker)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # 运行指定时长
        print(f"\n⏳ 开始 {self.format_time(self.duration_seconds)} 压力测试...")
        print("按 Ctrl+C 可提前结束测试\n")
        
        try:
            # 主循环
            while True:
                elapsed = time.time() - self.start_time
                remaining = self.duration_seconds - elapsed
                
                if remaining <= 0:
                    print(f"\n✅ 达到目标时长: {self.format_time(elapsed)}")
                    break
                
                # 每30秒显示一次进度
                if int(elapsed) % 30 == 0 and elapsed > 1:
                    ops = self.results['metrics']['operations']['total']
                    rate = ops / elapsed if elapsed > 0 else 0
                    remaining_formatted = self.format_time(remaining)
                    print(f"  ⏱️  已运行: {self.format_time(elapsed)} | 剩余: {remaining_formatted} | 操作: {ops:,} | 速率: {rate:.0f} ops/s")
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print(f"\n⚠️  用户中断测试 (已运行 {self.format_time(time.time() - self.start_time)})")
        finally:
            # 停止所有线程
            print("\n🛑 停止所有线程...")
            self.stop_flag.set()
            
            # 等待线程结束
            for t in worker_threads:
                t.join(timeout=2)
            monitor_thread.join(timeout=2)
            
            # 记录结束时间
            self.results['end_time'] = datetime.now().isoformat()
            self.results['actual_duration'] = time.time() - self.start_time
        
        # 收集最终统计
        print("\n📊 收集最终统计...")
        final_stats = self.memory.get_statistics()
        self.results['final_stats'] = final_stats
        
        # 生成报告
        self.generate_report()
        
        return self.results
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*80)
        print("📋 超长时间压力测试 - 最终报告")
        print("="*80)
        
        duration = self.results['actual_duration']
        ops = self.results['metrics']['operations']
        
        print(f"\n⏱️  时间统计:")
        print(f"  目标时长: {self.format_time(self.duration_seconds)}")
        print(f"  实际时长: {self.format_time(duration)}")
        print(f"  完成度: {100*duration/self.duration_seconds:.1f}%")
        
        print(f"\n⚡ 操作统计:")
        print(f"  总操作数: {ops['total']:,}")
        print(f"  成功: {ops['success']:,} ({100*ops['success']/ops['total']:.2f}%)")
        print(f"  失败: {ops['failure']:,} ({100*ops['failure']/ops['total']:.2f}%)")
        print(f"  平均速率: {ops['total']/duration:.0f} ops/s")
        
        print(f"\n📊 操作类型分布:")
        for op_type, count in sorted(ops['by_type'].items()):
            print(f"  {op_type}: {count:,} ({100*count/ops['total']:.1f}%)")
        
        print(f"\n📈 最终状态:")
        print(f"  节点数: {self.results['final_stats'].get('nodes', 0):,}")
        print(f"  边数: {self.results['final_stats'].get('edges', 0):,}")
        
        print(f"\n🐛 Bug与警告:")
        print(f"  发现Bug: {len(self.results['bugs_found'])}")
        print(f"  警告: {len(self.results['warnings'])}")
        
        if self.results['bugs_found']:
            print(f"\n❌ 发现的Bug:")
            for i, bug in enumerate(self.results['bugs_found'][:10], 1):
                print(f"  {i}. {bug['type']}: {bug['description']}")
        
        if self.results['warnings']:
            print(f"\n⚠️  警告列表:")
            for i, warning in enumerate(self.results['warnings'][:10], 1):
                print(f"  {i}. {warning['type']}: {warning['description']}")
        
        # 保存报告
        report_path = os.path.join(os.path.dirname(__file__), "v7_hour_long_test_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n📝 完整报告已保存: {report_path}")
        
        # 最终结论
        print("\n" + "="*80)
        if len(self.results['bugs_found']) == 0 and ops['failure'] == 0:
            print("🎉 太棒了！超长时间测试完美通过！")
        elif len(self.results['bugs_found']) == 0:
            print("✅ 测试完成，系统表现良好")
        else:
            print("⚠️  发现问题，需要进一步调查")
        print("="*80)


if __name__ == "__main__":
    # 运行1小时测试
    tester = HourLongStressTest(duration_seconds=3600)  # 1小时
    results = tester.run()
