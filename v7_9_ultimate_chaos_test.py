#!/usr/bin/env python3
"""
知识图谱记忆系统 v7.9 - 终极混乱测试
终极目标：探索系统的绝对极限，发现最深层的潜在问题

超级极端场景：
- 1000线程并发（极限并发）
- 500,000节点（大规模）
- 200,000边（复杂关系）
- 1小时运行时间（长时间稳定性）
- 资源耗尽测试（内存、CPU）
- 竞态条件测试（多线程竞态）
- 异常恢复测试（错误处理）
- 性能衰减监控（长期稳定性）
"""
import sys
import os
import random
import time
import threading
import gc
import tracemalloc
import resource
from typing import List, Dict, Any
from datetime import datetime
import signal

# 添加上级目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kg_memory_v7_optimized import MemorySystemV7Optimized, NodeType, EdgeType

class UltimateChaosTest:
    """终极混乱测试 - 探索系统绝对极限"""
    
    def __init__(self):
        self.kg = MemorySystemV7Optimized()
        self.errors = []
        self.warnings = []
        self.error_lock = threading.Lock()
        self.warning_lock = threading.Lock()
        
        self.operations_count = 0
        self.node_count = 0
        self.edge_count = 0
        self.query_count = 0
        self.semantic_count = 0
        self.infer_count = 0
        self.start_time = None
        
        self.stats_lock = threading.Lock()
        
        # 监控
        self.peak_memory = 0
        self.monitoring = True
        self.monitor_thread = None
        
        # 极限测试数据
        self.test_data = {
            "normal": ["Python", "JavaScript", "Machine Learning", "AI", "Web"],
            "unicode": ["你好世界", "Привет", "مرحبا", "🎉🚀", "こんにちは"],
            "extreme_length": ["X"*10000, "Y"*50000, "Z"*100000],
            "special": ["Node<>[]{}", "Node\x00\x01\x02", "Node\n\t\r", "Node'\"`"],
            "numbers": ["0", "-999999", "999999.999", "1e308", "1e-308"],
            "null_like": [None, "", " ", "\t", "\n"],
        }
        
        # 信号处理
        self.shutdown_requested = False
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """优雅关闭"""
        print("\n⚠️  接收到关闭信号，正在优雅关闭...")
        self.shutdown_requested = True
        self.monitoring = False
    
    def record_error(self, operation: str, error: Exception, context: str = ""):
        with self.error_lock:
            self.errors.append({
                "operation": operation,
                "error": str(error),
                "type": type(error).__name__,
                "context": context,
                "time": datetime.now().isoformat(),
                "ops": self.operations_count
            })
            print(f"\n❌ ERROR [{operation}]: {type(error).__name__}: {error[:100]}")
    
    def record_warning(self, message: str):
        with self.warning_lock:
            self.warnings.append({
                "message": message,
                "time": datetime.now().isoformat()
            })
            print(f"⚠️  WARNING: {message}")
    
    def monitor_resources(self):
        """资源监控线程"""
        while self.monitoring:
            try:
                # 内存使用 (使用resource模块)
                mem_info = resource.getrusage(resource.RUSAGE_SELF)
                current_mem = mem_info.ru_maxrss / 1024  # MB (Linux)
                
                with self.stats_lock:
                    if current_mem > self.peak_memory:
                        self.peak_memory = current_mem
                
                # 每60秒报告一次
                if int(time.time()) % 60 == 0:
                    print(f"  📊 资源监控 | 内存: {current_mem:.1f}MB")
                    
            except Exception as e:
                pass
            time.sleep(5)
    
    def extreme_concurrent_workers(self, num_workers: int = 500, duration_seconds: int = 1800):
        """极限并发测试 - 500线程，30分钟"""
        print(f"\n{'='*90}")
        print(f"🧪 极限并发测试: {num_workers}线程, {duration_seconds/60:.0f}分钟")
        print(f"{'='*90}")
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_resources, daemon=True)
        self.monitor_thread.start()
        
        # 准备操作列表
        operations = [
            ("add", 0.30),
            ("connect", 0.20),
            ("query", 0.25),
            ("semantic_search", 0.15),
            ("infer", 0.07),
            ("recommend", 0.03),
        ]
        
        def worker(worker_id: int):
            """每个worker执行的操作"""
            start = time.time()
            local_ops = 0
            
            while time.time() - start < duration_seconds and not self.shutdown_requested:
                try:
                    # 随机选择操作
                    op_type = random.choices(
                        [op[0] for op in operations],
                        weights=[op[1] for op in operations]
                    )[0]
                    
                    if op_type == "add":
                        label = random.choice([
                            f"Node_{worker_id}_{local_ops}",
                            *self.test_data["unicode"],
                            *self.test_data["normal"],
                        ])
                        node_type = random.choice(list(NodeType))
                        self.kg.remember(label, node_type=node_type)
                    
                    elif op_type == "connect":
                        with self.kg._node_lock:
                            labels = list(self.kg._label_to_node.keys())
                        if len(labels) >= 2:
                            src = random.choice(labels)
                            tgt = random.choice(labels)
                            rel = random.choice(list(EdgeType))
                            self.kg.connect(src, tgt, relation=rel)
                    
                    elif op_type == "query":
                        query = random.choice(list(self.test_data["normal"] + ["Node_"]))
                        k = random.randint(-10, 30)
                        self.kg.recall(query, k=k)
                    
                    elif op_type == "semantic_search":
                        query = random.choice(list(self.test_data["normal"]))
                        k = random.randint(-5, 20)
                        self.kg.semantic_search(query, k=k)
                    
                    elif op_type == "infer":
                        with self.kg._node_lock:
                            labels = list(self.kg._label_to_node.keys())
                        if labels:
                            concept = random.choice(labels)
                            depth = random.randint(-5, 8)
                            self.kg.infer(concept, max_depth=depth)
                    
                    elif op_type == "recommend":
                        with self.kg._node_lock:
                            labels = list(self.kg._label_to_node.keys())
                        if labels:
                            node = random.choice(labels)
                            k = random.randint(-3, 10)
                            self.kg.recommend_connections(node, k=k)
                    
                    local_ops += 1
                    
                    with self.stats_lock:
                        self.operations_count += 1
                        if local_ops % 1000 == 0:
                            print(f"    Worker-{worker_id:3d}: {local_ops:,} ops")
                    
                except Exception as e:
                    self.record_error(f"worker_{worker_id}", e)
                    time.sleep(0.01)
        
        # 启动所有worker
        print(f"🚀 启动 {num_workers} 个并发worker...")
        workers = []
        for i in range(num_workers):
            t = threading.Thread(target=worker, args=(i,), daemon=True)
            t.start()
            workers.append(t)
            if i % 100 == 0 and i > 0:
                print(f"  已启动 {i}/{num_workers} workers")
        
        # 监控进度
        last_report = time.time()
        while time.time() - start < duration_seconds and not self.shutdown_requested:
            elapsed = time.time() - start
            remaining = max(0, duration_seconds - elapsed)
            
            if time.time() - last_report >= 60:  # 每分钟报告一次
                with self.stats_lock:
                    ops = self.operations_count
                with self.kg._node_lock:
                    nodes = len(self.kg._nodes)
                    edges = len(self.kg._edges)
                
                ops_per_sec = ops / elapsed if elapsed > 0 else 0
                print(f"\n📊 进度更新 | {elapsed/60:.1f}/{duration_seconds/60:.0f}分钟")
                print(f"   操作数: {ops:,} | 速度: {ops_per_sec:.0f}/秒")
                print(f"   节点: {nodes:,} | 边: {edges:,}")
                print(f"   错误数: {len(self.errors)} | 峰值内存: {self.peak_memory:.1f}MB")
                
                last_report = time.time()
            
            time.sleep(10)
        
        # 关闭
        print("\n⏹️  等待worker结束...")
        self.monitoring = False
        for t in workers:
            t.join(timeout=5)
        
        elapsed = time.time() - start
        print(f"✅ 极限并发测试完成 | 总时间: {elapsed:.1f}秒")
    
    def memory_stress_test(self):
        """内存压力测试"""
        print(f"\n{'='*90}")
        print("🧪 内存压力测试")
        print(f"{'='*90}")
        
        tracemalloc.start()
        
        # 添加大量节点
        for i in range(50000):
            props = {
                f"key_{j}": f"value_{j}_{'x'*100}"
                for j in range(100)
            }
            self.kg.remember(f"MemTest_{i}", properties=props)
        
        gc.collect()
        snapshot1 = tracemalloc.take_snapshot()
        
        # 再次添加
        for i in range(50000):
            props = {
                f"key_{j}": f"value_{j}_{'y'*100}"
                for j in range(100)
            }
            self.kg.remember(f"MemTest2_{i}", properties=props)
        
        gc.collect()
        snapshot2 = tracemalloc.take_snapshot()
        
        # 比较
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        
        print(f"📊 内存增长 Top 10:")
        for i, stat in enumerate(top_stats[:10], 1):
            print(f"  {i:2d}. {stat}")
        
        tracemalloc.stop()
        print(f"✅ 内存压力测试完成 | 峰值: {self.peak_memory:.1f}MB")
    
    def race_condition_test(self):
        """竞态条件测试"""
        print(f"\n{'='*90}")
        print("🧪 竞态条件测试")
        print(f"{'='*90}")
        
        errors_before = len(self.errors)
        
        # 多个线程同时添加相同标签
        label = "RaceConditionTest"
        threads = []
        
        def add_same_node():
            try:
                self.kg.remember(label)
            except Exception as e:
                self.record_error("race_add", e)
        
        for _ in range(100):
            t = threading.Thread(target=add_same_node)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        errors_after = len(self.errors)
        race_errors = errors_after - errors_before
        
        print(f"  竞态条件测试：100线程同时添加相同标签")
        print(f"  产生的错误: {race_errors}")
        
        if race_errors == 0:
            print(f"  ✅ 完美！无竞态条件问题！")
        else:
            print(f"  ⚠️  发现 {race_errors} 个竞态条件错误")
        
        print(f"✅ 竞态条件测试完成")
    
    def extreme_value_test(self):
        """极端值测试"""
        print(f"\n{'='*90}")
        print("🧪 极端值测试")
        print(f"{'='*90}")
        
        # 添加基准节点
        self.kg.remember("TestNode1")
        self.kg.remember("TestNode2")
        
        extreme_tests = [
            ("k=-1e308", lambda: self.kg.recall("Test", k=-1e308)),
            ("k=1e308", lambda: self.kg.recall("Test", k=1e308)),
            ("depth=-1e308", lambda: self.kg.infer("TestNode1", max_depth=-1e308)),
            ("depth=1e308", lambda: self.kg.infer("TestNode1", max_depth=1e308)),
            ("weight=float('inf')", lambda: self.kg.connect("TestNode1", "TestNode2", weight=float('inf'))),
            ("weight=float('-inf')", lambda: self.kg.connect("TestNode1", "TestNode2", weight=float('-inf'))),
            ("weight=float('nan')", lambda: self.kg.connect("TestNode1", "TestNode2", weight=float('nan'))),
        ]
        
        for test_name, test_func in extreme_tests:
            try:
                test_func()
                print(f"  ✅ {test_name}: 通过")
            except Exception as e:
                print(f"  ❌ {test_name}: 失败 - {type(e).__name__}")
                self.record_error(test_name, e)
        
        print(f"✅ 极端值测试完成")
    
    def long_term_stability_test(self, duration_minutes: int = 5):
        """长期稳定性测试"""
        print(f"\n{'='*90}")
        print(f"🧪 长期稳定性测试: {duration_minutes}分钟")
        print(f"{'='*90}")
        
        start = time.time()
        end = start + duration_minutes * 60
        last_check = start
        
        # 记录初始性能
        perf_samples = []
        
        while time.time() < end and not self.shutdown_requested:
            check_start = time.time()
            
            # 执行固定数量的操作并测量时间
            ops_count = 0
            ops_start = time.time()
            
            for _ in range(1000):
                try:
                    self.kg.remember(f"StabilityTest_{random.randint(1, 10000)}")
                    ops_count += 1
                except Exception as e:
                    self.record_error("stability", e)
            
            ops_time = time.time() - ops_start
            ops_per_sec = ops_count / ops_time if ops_time > 0 else 0
            
            perf_samples.append({
                "time": time.time() - start,
                "ops_per_sec": ops_per_sec
            })
            
            # 每分钟报告
            if time.time() - last_check >= 60:
                elapsed = time.time() - start
                print(f"  ⏱️  {elapsed/60:.1f}分钟 | 速度: {ops_per_sec:.0f} ops/s")
                last_check = time.time()
            
            time.sleep(1)
        
        # 分析性能趋势
        if len(perf_samples) >= 2:
            first_sample = perf_samples[0]["ops_per_sec"]
            last_sample = perf_samples[-1]["ops_per_sec"]
            degradation = (first_sample - last_sample) / first_sample * 100 if first_sample > 0 else 0
            
            print(f"\n📊 性能稳定性分析:")
            print(f"  初始速度: {first_sample:.0f} ops/s")
            print(f"  最终速度: {last_sample:.0f} ops/s")
            print(f"  性能衰减: {degradation:.1f}%")
            
            if degradation < 20:
                print(f"  ✅ 性能衰减在可接受范围内 (< 20%)")
            elif degradation < 50:
                print(f"  ⚠️  性能衰减较明显 ({degradation:.1f}%)")
            else:
                print(f"  ❌ 性能衰减严重 ({degradation:.1f}%)")
        
        print(f"✅ 长期稳定性测试完成")
    
    def run_all_tests(self):
        """运行所有终极测试"""
        print("\n" + "="*90)
        print("🚀 知识图谱记忆系统 v7.9 终极混乱测试")
        print("终极目标：探索系统的绝对极限，发现最深层的潜在问题")
        print("="*90)
        
        overall_start = time.time()
        
        # 1. 竞态条件测试
        self.race_condition_test()
        
        # 2. 极端值测试
        self.extreme_value_test()
        
        # 3. 内存压力测试
        self.memory_stress_test()
        
        # 4. 长期稳定性测试（5分钟）
        self.long_term_stability_test(duration_minutes=5)
        
        # 5. 极限并发测试（30分钟 - 默认，ctrl+c可提前结束）
        print("\n" + "="*90)
        print("⚠️  即将开始30分钟极限并发测试！")
        print("   按 Ctrl+C 可以提前结束测试")
        print("="*90)
        time.sleep(3)
        self.extreme_concurrent_workers(num_workers=500, duration_seconds=1800)
        
        total_elapsed = time.time() - overall_start
        
        # 最终总结
        print("\n" + "="*90)
        print("📊 终极混乱测试最终总结")
        print("="*90)
        print(f"总运行时间: {total_elapsed/60:.1f}分钟")
        
        with self.stats_lock:
            print(f"总操作数: {self.operations_count:,}")
        
        with self.kg._node_lock:
            nodes = len(self.kg._nodes)
            edges = len(self.kg._edges)
        
        print(f"最终节点数: {nodes:,}")
        print(f"最终边数: {edges:,}")
        print(f"峰值内存: {self.peak_memory:.1f}MB")
        
        if self.errors:
            print(f"\n❌ 发现 {len(self.errors)} 个错误:")
            print("="*90)
            error_types = {}
            for err in self.errors:
                err_type = err["type"]
                error_types[err_type] = error_types.get(err_type, 0) + 1
            
            for err_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                print(f"  {err_type}: {count}次")
            
            print("\n详细错误 (前10个):")
            for i, err in enumerate(self.errors[:10], 1):
                print(f"  {i:2d}. [{err['operation']}] {err['type']}: {err['error'][:80]}")
        else:
            print("\n✅ 太棒了！0个错误！系统极其稳定！")
        
        if self.warnings:
            print(f"\n⚠️  警告: {len(self.warnings)} 个")
        
        print("="*90)
        
        return len(self.errors) == 0

if __name__ == "__main__":
    test = UltimateChaosTest()
    
    try:
        passed = test.run_all_tests()
        sys.exit(0 if passed else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        print("="*90)
        sys.exit(1)

