#!/usr/bin/env python3
"""
知识图谱记忆系统 v5.0 - 深度极限测试
包含：长时间运行、大数据量、并发、内存泄漏、边缘情况等
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import tempfile
import time
import gc
import threading
import random
import psutil
from typing import List, Dict, Any, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from kg_memory.core import MemorySystem, NetworkXGraphEngine


class DeepTester:
    """深度极限测试器"""
    
    def __init__(self):
        self.issues: List[Dict] = []
        self.performance_metrics: Dict = {}
        self.test_results: Dict[str, bool] = {}
        self.memory_history: List[Tuple[float, float]] = []
        self.initial_memory = 0.0
        self.start_time = 0.0
        
    def log_issue(self, test_name: str, problem: str, severity: str = "medium", details: Any = None):
        """记录发现的问题"""
        issue = {
            'test': test_name,
            'problem': problem,
            'severity': severity,
            'details': details,
            'time': datetime.now().isoformat()
        }
        self.issues.append(issue)
        print(f"⚠️  [{severity}] {test_name}: {problem}")
        
    def log_performance(self, name: str, value: Any):
        """记录性能指标"""
        self.performance_metrics[name] = value
        print(f"📊 {name}: {value}")
        
    def record_memory(self):
        """记录当前内存使用"""
        current_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        elapsed = time.time() - self.start_time
        self.memory_history.append((elapsed, current_memory))
        return current_memory
        
    def test_long_running_stability(self, duration_seconds: int = 60):
        """测试长时间运行稳定性"""
        print(f"\n{'='*80}")
        print(f"⏱️ 测试 1: 长时间运行稳定性 ({duration_seconds}秒)")
        print(f"{'='*80}")
        
        temp_dir = tempfile.mkdtemp()
        ms = MemorySystem(temp_dir)
        ms.clear()
        
        start_time = time.time()
        operation_count = 0
        errors = 0
        last_report = 0
        
        print(f"📊 监控内存使用和操作稳定性...")
        
        while time.time() - start_time < duration_seconds:
            try:
                # 执行随机操作
                op_type = random.choice(['remember', 'connect', 'recall', 'infer', 'stats'])
                
                if op_type == 'remember':
                    knowledge = f"LongTest_Node_{random.randint(0, 100000)}"
                    props = {'value': random.random(), 'timestamp': time.time()}
                    ms.remember(knowledge, props)
                elif op_type == 'connect':
                    try:
                        source = f"LongTest_Node_{random.randint(0, 5000)}"
                        target = f"LongTest_Node_{random.randint(0, 5000)}"
                        ms.connect(source, target, 'related')
                    except Exception:
                        pass
                elif op_type == 'recall':
                    ms.recall(f"LongTest_Node_{random.randint(0, 1000)}", k=10)
                elif op_type == 'infer':
                    try:
                        ms.infer(f"LongTest_Node_{random.randint(0, 100)}")
                    except Exception:
                        pass
                elif op_type == 'stats':
                    ms.stats()
                
                operation_count += 1
                
                # 定期报告
                if time.time() - last_report >= 5:
                    current_memory = self.record_memory()
                    print(f"  📈 已运行 {int(time.time()-start_time)}s, "
                          f"操作数: {operation_count}, "
                          f"内存: {current_memory:.1f}MB, "
                          f"错误: {errors}")
                    last_report = time.time()
                    
            except Exception as e:
                errors += 1
                if errors <= 5:  # 只记录前5个错误
                    self.log_issue('long_running', f"运行错误: {e}", "medium")
        
        final_memory = self.record_memory()
        elapsed = time.time() - start_time
        ops_per_second = operation_count / elapsed
        
        print(f"\n✅ 长时间运行测试完成")
        print(f"   总操作数: {operation_count}")
        print(f"   平均性能: {ops_per_second:.1f} 操作/秒")
        print(f"   错误数: {errors}")
        print(f"   最终内存: {final_memory:.1f}MB")
        
        memory_growth = final_memory - self.initial_memory
        if memory_growth > 50:  # 超过50MB视为可能泄漏
            self.log_issue('long_running', 
                          f"内存增长 {memory_growth:.1f}MB，可能存在内存泄漏", 
                          "high")
        
        self.log_performance('long_running_ops_per_sec', ops_per_second)
        self.log_performance('long_running_total_ops', operation_count)
        self.log_performance('long_running_memory_growth', memory_growth)
        
        self.test_results['long_running'] = errors == 0
        
        return errors == 0
        
    def test_massive_data_scaling(self, node_counts: List[int] = [100, 500, 1000, 5000, 10000]):
        """测试大规模数据扩展"""
        print(f"\n{'='*80}")
        print(f"📈 测试 2: 大规模数据扩展性能")
        print(f"{'='*80}")
        
        temp_dir = tempfile.mkdtemp()
        ms = MemorySystem(temp_dir)
        
        scaling_performance = []
        
        for count in node_counts:
            ms.clear()
            gc.collect()
            
            start_memory = self.record_memory()
            start_time = time.time()
            
            print(f"\n  🔹 {count}个节点...")
            
            for i in range(count):
                ms.remember(f"ScaleTest_Node_{i}", 
                          {'index': i, 
                           'type': random.choice(['A', 'B', 'C', 'D']),
                           'value': random.random()})
            
            node_time = time.time() - start_time
            node_rate = count / node_time
            
            # 添加边
            edge_start = time.time()
            edge_count = 0
            for i in range(min(count * 3, 30000)):
                try:
                    source = f"ScaleTest_Node_{random.randint(0, count-1)}"
                    target = f"ScaleTest_Node_{random.randint(0, count-1)}"
                    ms.connect(source, target, 'link')
                    edge_count += 1
                except Exception:
                    pass
            edge_time = time.time() - edge_start
            edge_rate = edge_count / edge_time if edge_time > 0 else 0
            
            # 测试查询
            query_start = time.time()
            query_count = 0
            for _ in range(100):
                ms.recall(f"ScaleTest_Node_{random.randint(0, count-1)}", k=5)
                query_count += 1
            query_time = time.time() - query_start
            query_rate = query_count / query_time
            
            final_memory = self.record_memory()
            
            print(f"    ✅ {count}节点完成")
            print(f"      节点创建: {node_rate:.0f} 节点/秒")
            print(f"      边创建: {edge_rate:.0f} 边/秒")
            print(f"      查询: {query_rate:.1f} 查询/秒")
            print(f"      内存使用: {final_memory - start_memory:.1f}MB")
            
            scaling_performance.append({
                'nodes': count,
                'node_rate': node_rate,
                'edge_rate': edge_rate,
                'query_rate': query_rate,
                'memory': final_memory - start_memory
            })
            
            # 检查性能是否显著下降
            if count > 100 and len(scaling_performance) >= 2:
                prev_rate = scaling_performance[-2]['query_rate']
                current_rate = scaling_performance[-1]['query_rate']
                drop_ratio = 1 - (current_rate / prev_rate if prev_rate > 0 else 0)
                if drop_ratio > 0.5:
                    self.log_issue('scaling', 
                                  f"查询性能下降 {drop_ratio*100:.1f}%", 
                                  "medium")
        
        self.log_performance('scaling_data', scaling_performance)
        self.test_results['massive_scaling'] = True
        
    def test_concurrent_race_conditions(self):
        """测试并发竞争条件"""
        print(f"\n{'='*80}")
        print(f"🔄 测试 3: 并发竞争条件")
        print(f"{'='*80}")
        
        temp_dir = tempfile.mkdtemp()
        ms = MemorySystem(temp_dir)
        ms.clear()
        
        num_threads = 20
        operations_per_thread = 200
        errors = 0
        
        # 先创建一些基础节点
        for i in range(100):
            ms.remember(f"RaceTest_Node_{i}")
        
        shared_counter = [0]
        lock = threading.Lock()
        
        def worker(thread_id):
            nonlocal errors
            thread_errors = 0
            for _ in range(operations_per_thread):
                try:
                    choice = random.random()
                    if choice < 0.3:
                        # 记忆新节点
                        ms.remember(f"RaceTest_{thread_id}_{random.randint(0, 1000)}")
                    elif choice < 0.5:
                        # 连接节点
                        try:
                            ms.connect(f"RaceTest_Node_{random.randint(0, 99)}",
                                     f"RaceTest_Node_{random.randint(0, 99)}",
                                     "related")
                        except Exception:
                            pass
                    elif choice < 0.8:
                        # 查询
                        ms.recall(f"RaceTest_Node_{random.randint(0, 99)}", k=5)
                    else:
                        # 推理
                        ms.infer(f"RaceTest_Node_{random.randint(0, 99)}")
                    
                    with lock:
                        shared_counter[0] += 1
                        
                except Exception as e:
                    thread_errors += 1
                    if thread_errors <= 3:
                        print(f"    线程 {thread_id} 错误: {e}")
            
            return thread_errors
        
        print(f" 🧵 启动 {num_threads} 个并发线程...")
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker, tid) for tid in range(num_threads)]
            for future in as_completed(futures):
                errors += future.result()
        
        elapsed = time.time() - start_time
        
        total_operations = shared_counter[0]
        throughput = total_operations / elapsed
        
        print(f"\n  ✅ 并发测试完成")
        print(f"    总操作数: {total_operations}")
        print(f"    错误数: {errors}")
        print(f"    吞吐量: {throughput:.1f} ops/sec")
        print(f"    线程安全: {'✅' if errors == 0 else '⚠️'}")
        
        if errors > 0:
            self.log_issue('concurrent', 
                          f"并发操作中出现 {errors} 个错误", 
                          "high")
        
        stats = ms.stats()
        print(f"    最终节点数: {stats['nodes']}")
        print(f"    最终边数: {stats['edges']}")
        
        self.log_performance('concurrent_errors', errors)
        self.log_performance('concurrent_throughput', throughput)
        self.test_results['concurrent'] = errors == 0
        
    def test_edge_cases(self):
        """测试边界情况和错误处理"""
        print(f"\n{'='*80}")
        print(f"🪤 测试 4: 边界情况和错误处理")
        print(f"{'='*80}")
        
        temp_dir = tempfile.mkdtemp()
        ms = MemorySystem(temp_dir)
        ms.clear()
        
        edge_cases = [
            ("空字符串知识", lambda: ms.remember("")),
            ("超长知识字符串", lambda: ms.remember("X" * 100000)),
            ("查询不存在的节点", lambda: ms.recall("NonExistentNode_1234567890")),
            ("连接不存在的节点", lambda: ms.connect("NotExist1", "NotExist2")),
            ("非常小的k值", lambda: ms.recall("Test", k=0)),
            ("负数k值", lambda: ms.recall("Test", k=-1)),
            ("大属性字典", lambda: ms.remember("BigProp", {f"key_{i}": f"value_{i}" for i in range(1000)})),
            ("特殊字符", lambda: ms.remember("测试_😀!@#$%^&*()")),
            ("重复节点", lambda: ms.remember("Duplicate") or ms.remember("Duplicate")),
            ("infer不存在的起点", lambda: ms.infer("NonExistentStart"))
        ]
        
        passed = 0
        failed = 0
        
        for case_name, test_func in edge_cases:
            try:
                print(f"  🧪 {case_name}...")
                result = test_func()
                passed += 1
                print(f"    ✅ 成功处理")
            except Exception as e:
                failed += 1
                print(f"    ⚠️ 返回异常: {type(e).__name__}")
        
        # 测试空图操作
        ms.clear()
        print(f"\n  🧪 空图操作:")
        
        tests_on_empty = [
            ("stats()", lambda: ms.stats()),
            ("recall()", lambda: ms.recall("anything")),
            ("infer()", lambda: ms.infer("something")),
            ("pagerank()", lambda: ms._graph.pagerank()),
            ("centrality()", lambda: ms._graph.betweenness_centrality())
        ]
        
        for name, func in tests_on_empty:
            try:
                result = func()
                print(f"    ✅ {name} - 正常完成")
                passed += 1
            except Exception as e:
                print(f"    ⚠️ {name} - 异常: {type(e).__name__}")
                failed += 1
                self.log_issue('edge_cases', 
                              f"{name} 在空图上抛出异常", 
                              "medium")
        
        total_tests = len(edge_cases) + len(tests_on_empty)
        print(f"\n  边界情况测试完成: {passed}/{total_tests} 正常处理")
        
        self.test_results['edge_cases'] = True
        
    def test_memory_leak_detection(self):
        """测试内存泄漏"""
        print(f"\n{'='*80}")
        print(f"💾 测试 5: 内存泄漏检测")
        print(f"{'='*80}")
        
        temp_dir = tempfile.mkdtemp()
        ms = MemorySystem(temp_dir)
        ms.clear()
        
        num_rounds = 20
        operations_per_round = 1000
        
        print(f"执行 {num_rounds} 轮操作，每轮 {operations_per_round} 次操作...")
        
        memory_snapshots = []
        
        for i in range(num_rounds):
            # 执行操作
            for _ in range(operations_per_round):
                ms.remember(f"MemTest_Node_{i}_{random.randint(0, 1000)}")
                ms.recall(f"MemTest_Node_{random.randint(0, i*10)}", k=3)
            
            # 清理和GC
            ms.clear()
            gc.collect()
            
            current_memory = self.record_memory()
            memory_snapshots.append(current_memory)
            
            if i % 5 == 0:
                print(f"  轮次 {i}: {current_memory:.1f}MB")
        
        # 分析内存趋势
        if len(memory_snapshots) >= 3:
            initial_avg = sum(memory_snapshots[:3]) / 3
            final_avg = sum(memory_snapshots[-3:]) / 3
            growth = final_avg - initial_avg
            
            print(f"\n  📊 内存分析:")
            print(f"    初始平均: {initial_avg:.1f}MB")
            print(f"    最终平均: {final_avg:.1f}MB")
            print(f"    增长: {growth:.1f}MB")
            
            if growth > 20:
                self.log_issue('memory_leak', 
                              f"检测到内存增长 {growth:.1f}MB，可能存在泄漏", 
                              "medium")
            elif growth > 5:
                print(f"    ⚠️ 内存轻度增长 {growth:.1f}MB")
            else:
                print(f"    ✅ 内存稳定")
        
        self.log_performance('memory_growth', growth if 'growth' in locals() else 0)
        self.test_results['memory_leak'] = True
        
    def test_algorithm_robustness(self):
        """测试图算法在不同规模图上的鲁棒性"""
        print(f"\n{'='*80}")
        print(f"🧠 测试 6: 图算法鲁棒性")
        print(f"{'='*80}")
        
        temp_dir = tempfile.mkdtemp()
        
        graph_sizes = [10, 50, 200, 500]
        
        for size in graph_sizes:
            print(f"\n  🔹 图规模: {size}节点")
            
            ms = MemorySystem(temp_dir)
            ms.clear()
            
            # 创建图
            for i in range(size):
                ms.remember(f"AlgoTest_Node_{i}", {'idx': i})
            
            # 添加随机边
            edge_count = 0
            for _ in range(size * 3):
                try:
                    ms.connect(f"AlgoTest_Node_{random.randint(0, size-1)}",
                             f"AlgoTest_Node_{random.randint(0, size-1)}",
                             "related")
                    edge_count += 1
                except Exception:
                    pass
            
            print(f"    图: {size}节点, {edge_count}边")
            
            # 测试各个算法
            algorithms = [
                ("pagerank", ms._graph.pagerank),
                ("betweenness", ms._graph.betweenness_centrality),
                ("degree", ms._graph.degree_centrality),
                ("closeness", ms._graph.closeness_centrality),
                ("eigenvector", ms._graph.eigenvector_centrality),
                ("communities", ms._graph.find_communities),
            ]
            
            for algo_name, algo_func in algorithms:
                try:
                    start_time = time.time()
                    result = algo_func()
                    elapsed = time.time() - start_time
                    
                    if isinstance(result, dict):
                        print(f"    ✅ {algo_name}: {len(result)}结果, {elapsed*1000:.2f}ms")
                    else:
                        print(f"    ✅ {algo_name}: {elapsed*1000:.2f}ms")
                        
                except Exception as e:
                    print(f"    ⚠️ {algo_name} 失败: {e}")
                    self.log_issue('algorithms', 
                                  f"{algo_name} 在{size}节点图上失败: {e}", 
                                  "medium")
        
        self.test_results['algorithms'] = True
        
    def generate_final_report(self):
        """生成最终报告"""
        print(f"\n{'='*80}")
        print(f"📋 深度极限测试 - 最终报告")
        print(f"{'='*80}")
        
        total_tests = len(self.test_results)
        passed = sum(1 for v in self.test_results.values() if v)
        issues_count = len(self.issues)
        
        print(f"\n📊 测试摘要:")
        print(f"  总测试数: {total_tests}")
        print(f"  通过: {passed}/{total_tests}")
        print(f"  发现问题: {issues_count}")
        
        if self.issues:
            print(f"\n⚠️ 发现的问题:")
            for issue in self.issues:
                print(f"  [{issue['severity']}] {issue['test']}: {issue['problem']}")
        
        print(f"\n📈 性能指标:")
        for key, value in self.performance_metrics.items():
            print(f"  {key}: {value}")
        
        print(f"\n✅ 测试完成")
        
        return {
            'summary': {
                'total_tests': total_tests,
                'passed': passed,
                'issues_found': issues_count
            },
            'issues': self.issues,
            'performance': self.performance_metrics,
            'test_results': self.test_results
        }
        
    def run_all_tests(self):
        """运行所有测试"""
        self.start_time = time.time()
        self.initial_memory = self.record_memory()
        
        print(f"🚀 知识图谱记忆系统 - 深度极限测试套件")
        print(f"   开始时间: {datetime.now().isoformat()}")
        
        try:
            # 运行各项测试
            self.test_long_running_stability(30)  # 30秒演示
            self.test_massive_data_scaling([100, 500, 1000, 3000])  # 较小的规模
            self.test_concurrent_race_conditions()
            self.test_edge_cases()
            self.test_memory_leak_detection()
            self.test_algorithm_robustness()
            
            report = self.generate_final_report()
            
            with open('deep_test_report.json', 'w', encoding='utf-8') as f:
                import json
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"\n📝 报告保存到 deep_test_report.json")
            
            return report
            
        except Exception as e:
            print(f"\n❌ 测试运行失败: {e}")
            import traceback
            traceback.print_exc()
            return None


if __name__ == '__main__':
    tester = DeepTester()
    report = tester.run_all_tests()
