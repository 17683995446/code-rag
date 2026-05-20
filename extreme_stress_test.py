#!/usr/bin/env python3
"""
知识图谱记忆系统 v5.0 - 超极限压力测试
发现系统缺陷和性能瓶颈
"""
import sys
import os
import tempfile
import time
import threading
import random
import gc
from datetime import datetime
from typing import List, Dict, Any, Set, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from kg_memory.core import (
    MemorySystem,
    NetworkXGraphEngine,
    Node,
    Edge,
    NodeType,
    EdgeType,
    LRUCache
)


class ExtremeStressTester:
    """超极限压力测试器"""
    
    def __init__(self):
        self.issues_found: List[Dict] = []
        self.performance_metrics: Dict[str, Any] = {}
        self.test_results: Dict[str, bool] = {}
        self.start_time = time.time()
        self.memory_snapshots: List[Tuple[float, float]] = []
    
    def log_issue(self, test_name: str, issue: str, severity: str = "medium", 
                  details: Any = None):
        """记录发现的问题"""
        self.issues_found.append({
            "test": test_name,
            "issue": issue,
            "severity": severity,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        print(f"⚠️  [{severity.upper()}] {test_name}: {issue}")
        if details:
            print(f"   详情: {details}")
    
    def log_metric(self, name: str, value: Any):
        """记录性能指标"""
        self.performance_metrics[name] = value
        print(f"📊 {name}: {value}")
    
    def check_memory(self):
        """检查内存使用"""
        process = psutil.Process()
        mem_mb = process.memory_info().rss / 1024 / 1024
        self.memory_snapshots.append((time.time() - self.start_time, mem_mb))
        return mem_mb
    
    def test_extreme_data_scaling(self):
        """测试1: 超大规模数据扩展"""
        print(f"\n{'='*80}")
        print(f"🔥 测试1: 超大规模数据扩展")
        print(f"{'='*80}")
        
        test_name = "extreme_data_scaling"
        temp_dir = tempfile.mkdtemp()
        
        try:
            ms = MemorySystem(temp_dir)
            ms.clear()
            
            start_mem = self.check_memory()
            
            # 测试不同规模
            scale_tests = [100, 500, 1000, 2000, 5000]
            
            for n_nodes in scale_tests:
                print(f"\n📈 测试 {n_nodes} 个节点...")
                
                nodes = []
                edges = []
                
                # 创建节点
                t0 = time.time()
                for i in range(n_nodes):
                    node_label = f"Node_{i}_{random.randint(0, 9999)}"
                    node_id = ms.remember(node_label, {
                        "index": i,
                        "random": random.random(),
                        "type": random.choice(["concept", "entity", "category"])
                    })
                    nodes.append((node_id, node_label))
                t1 = time.time()
                
                # 创建边（随机连接）
                n_edges = 0
                for i, (node_id, label) in enumerate(nodes):
                    # 每个节点连接3-8个其他节点
                    n_connections = random.randint(3, 8)
                    targets = random.sample(nodes, min(n_connections, len(nodes)))
                    for target_id, target_label in targets:
                        if target_id != node_id:
                            try:
                                ms.connect(label, target_label, 
                                         relation_type=random.choice(["related", "uses", "part_of", "similar"]))
                                n_edges += 1
                            except Exception:
                                pass
                t2 = time.time()
                
                # 记录性能
                node_rate = n_nodes / (t1 - t0)
                edge_rate = n_edges / (t2 - t1) if (t2 - t1) > 0 else 0
                
                self.log_metric(f"{n_nodes}_nodes_rate", f"{node_rate:.1f} node/s")
                self.log_metric(f"{n_nodes}_edges_rate", f"{edge_rate:.1f} edge/s")
                print(f"   ✅ {n_nodes} 节点, {n_edges} 边: {node_rate:.0f} 节点/秒, {edge_rate:.0f} 边/秒")
                
                # 测试查询
                t3 = time.time()
                for _ in range(min(100, n_nodes)):
                    idx = random.randint(0, len(nodes)-1)
                    results = ms.recall(nodes[idx][1])
                    if len(results) == 0:
                        self.log_issue(test_name, f"查询返回空结果: {nodes[idx][1]}", "low")
                t4 = time.time()
                
                self.log_metric(f"{n_nodes}_query_rate", 
                              f"{min(100, n_nodes)/(t4-t3):.0f}  queries/s")
                
                # 检查内存增长
                current_mem = self.check_memory()
                mem_growth = current_mem - start_mem
                self.log_metric(f"{n_nodes}_memory", f"{mem_growth:.1f} MB")
                
                if mem_growth > 1000 and n_nodes < 5000:
                    self.log_issue(test_name, "内存增长过快", "medium", 
                                  f"{n_nodes} 节点使用 {mem_growth:.1f} MB")
                
                gc.collect()
            
            stats = ms.stats()
            print(f"\n📊 最终统计: {stats}")
            
            self.test_results[test_name] = True
            
        except Exception as e:
            self.log_issue(test_name, f"异常: {e}", "high")
            import traceback
            print(f"   Stacktrace: {traceback.format_exc()}")
            self.test_results[test_name] = False
    
    def test_concurrent_conflicts(self):
        """测试2: 并发冲突和数据一致性"""
        print(f"\n{'='*80}")
        print(f"🔀 测试2: 并发冲突和数据一致性")
        print(f"{'='*80}")
        
        test_name = "concurrent_conflicts"
        temp_dir = tempfile.mkdtemp()
        
        try:
            ms = MemorySystem(temp_dir)
            ms.clear()
            
            # 先创建一些基础节点
            base_nodes = []
            for i in range(20):
                node_id = ms.remember(f"BaseNode_{i}")
                base_nodes.append(node_id)
            
            errors: List[str] = []
            successful_operations = 0
            failed_operations = 0
            
            n_threads = 50
            operations_per_thread = 200
            
            def worker(thread_id: int):
                nonlocal successful_operations, failed_operations
                local_errors = []
                
                try:
                    thread_ms = MemorySystem(temp_dir)
                    
                    for i in range(operations_per_thread):
                        try:
                            op_type = random.choice([
                                "remember", "connect", "recall", "infer", "get_stats"
                            ])
                            
                            if op_type == "remember":
                                # 添加新节点
                                label = f"Thread{thread_id}_Node{thread_id}_{i}_{random.randint(0,9999)}"
                                thread_ms.remember(label, {"thread": thread_id})
                                successful_operations += 1
                            
                            elif op_type == "connect":
                                # 连接随机节点
                                src_idx = random.randint(0, 19)
                                dst_idx = random.randint(0, 19)
                                try:
                                    thread_ms.connect(f"BaseNode_{src_idx}", 
                                                   f"BaseNode_{dst_idx}", 
                                                   f"thread_{thread_id}_rel")
                                    successful_operations += 1
                                except Exception:
                                    # 连接已存在是正常的
                                    pass
                            
                            elif op_type == "recall":
                                # 搜索节点
                                thread_ms.recall("BaseNode")
                                successful_operations += 1
                            
                            elif op_type == "infer":
                                # 推理
                                thread_ms.infer(f"BaseNode_{random.randint(0,19)}")
                                successful_operations += 1
                            
                            elif op_type == "get_stats":
                                thread_ms.stats()
                                successful_operations += 1
                        
                        except Exception as e:
                            failed_operations += 1
                            local_errors.append(f"Operation {i} failed: {str(e)[:100]}")
                
                except Exception as e:
                    local_errors.append(f"Thread failed: {str(e)}")
                
                return local_errors
            
            t0 = time.time()
            
            # 启动所有线程
            with ThreadPoolExecutor(max_workers=n_threads) as executor:
                futures = [executor.submit(worker, i) for i in range(n_threads)]
                
                for future in as_completed(futures):
                    thread_errors = future.result()
                    errors.extend(thread_errors)
            
            t1 = time.time()
            
            # 分析结果
            total_ops = n_threads * operations_per_thread
            throughput = total_ops / (t1 - t0)
            failure_rate = failed_operations / total_ops if total_ops > 0 else 0
            
            self.log_metric("concurrent_throughput", f"{throughput:.0f} ops/s")
            self.log_metric("concurrent_success_rate", f"{(1-failure_rate)*100:.1f}%")
            
            if errors:
                self.log_issue(test_name, f"并发错误: {len(errors)} 个", "high", 
                              f"前10个错误: {errors[:10]}")
            
            if failure_rate > 0.05:
                self.log_issue(test_name, "失败率过高", "high", 
                              f"{failure_rate*100:.1f}%")
            
            # 最终数据一致性检查
            final_stats = ms.stats()
            print(f"📊 最终状态: {final_stats}")
            
            self.test_results[test_name] = len(errors) < 10
            
        except Exception as e:
            self.log_issue(test_name, f"异常: {e}", "high")
            import traceback
            print(f"   Stacktrace: {traceback.format_exc()}")
            self.test_results[test_name] = False
    
    def test_boundary_conditions(self):
        """测试3: 边界条件和错误处理"""
        print(f"\n{'='*80}")
        print(f"🔍 测试3: 边界条件和错误处理")
        print(f"{'='*80}")
        
        test_name = "boundary_conditions"
        temp_dir = tempfile.mkdtemp()
        
        try:
            ms = MemorySystem(temp_dir)
            ms.clear()
            
            test_cases = [
                ("空字符串", lambda: ms.remember("")),
                ("超长字符串", lambda: ms.remember("a"*1000000)),
                ("搜索不存在节点", lambda: ms.recall("NON_EXISTENT_NODE_12345")),
                ("连接不存在节点", lambda: ms.connect("NODE_A", "NODE_B", "rel")),
                ("空图路径查找", lambda: ms.shortest_path("A", "B")),
                ("重复添加相同节点", lambda: ms.remember("DuplicateNode") or ms.remember("DuplicateNode")),
                ("添加空属性", lambda: ms.remember("EmptyProps", {})),
                ("大量属性", lambda: ms.remember("ManyProps", {f"k{i}": f"v{i}" for i in range(100)})),
                ("特殊字符", lambda: ms.remember("SpecialChars_!@#$%^&*()")),
                ("Unicode字符", lambda: ms.remember("测试节点_中文_日本語_ðñ")),
            ]
            
            passed = 0
            failed = 0
            
            for case_name, test_func in test_cases:
                try:
                    result = test_func()
                    print(f"✅ {case_name}")
                    passed += 1
                except Exception as e:
                    print(f"⚠️ {case_name}: {type(e).__name__} - {str(e)[:50]}")
                    if "not found" in str(e) or "不存在" in str(e):
                        # 这是合理的错误处理
                        passed += 1
                    else:
                        self.log_issue(test_name, f"边界条件处理不当: {case_name}", 
                                      "medium", str(e))
                        failed += 1
            
            self.log_metric("boundary_tests_passed", f"{passed}/{len(test_cases)}")
            
            self.test_results[test_name] = failed == 0
            
        except Exception as e:
            self.log_issue(test_name, f"异常: {e}", "high")
            import traceback
            print(f"   Stacktrace: {traceback.format_exc()}")
            self.test_results[test_name] = False
    
    def test_algorithm_robustness(self):
        """测试4: 图算法健壮性"""
        print(f"\n{'='*80}")
        print(f"🧠 测试4: 图算法健壮性")
        print(f"{'='*80}")
        
        test_name = "algorithm_robustness"
        temp_dir = tempfile.mkdtemp()
        
        try:
            ms = MemorySystem(temp_dir)
            ms.clear()
            
            # 创建不同类型的图结构进行测试
            graph_configs = [
                ("完全空图", 0, 0),
                ("单个孤立节点", 1, 0),
                ("两个节点无边", 2, 0),
                ("简单链", 10, 9),
                ("完全图", 5, 20),
                ("星型图", 10, 9),
                ("随机稀疏图", 50, 100),
                ("随机稠密图", 30, 300),
            ]
            
            for config_name, n_nodes, n_edges in graph_configs:
                print(f"\n测试图类型: {config_name}")
                
                ms.clear()
                
                # 创建图
                for i in range(n_nodes):
                    ms.remember(f"AlgoTest_{i}")
                
                edges_added = 0
                while edges_added < n_edges:
                    src = random.randint(0, n_nodes-1)
                    dst = random.randint(0, n_nodes-1)
                    if src != dst:
                        try:
                            ms.connect(f"AlgoTest_{src}", f"AlgoTest_{dst}", "test_rel")
                            edges_added += 1
                        except Exception:
                            pass
                
                # 测试所有算法
                algorithms = {
                    "betweenness": lambda: ms._graph.betweenness_centrality(),
                    "degree": lambda: ms.degree_centrality(),
                    "closeness": lambda: ms.closeness_centrality(),
                    "eigenvector": lambda: ms.eigenvector_centrality(),
                    "pagerank": lambda: ms.pagerank(),
                    "communities": lambda: ms.find_communities(),
                }
                
                for algo_name, algo_func in algorithms.items():
                    try:
                        t0 = time.time()
                        result = algo_func()
                        t1 = time.time()
                        
                        if isinstance(result, dict):
                            print(f"   ✅ {algo_name}: {len(result)} 结果, {t1-t0:.4f}s")
                        elif isinstance(result, list):
                            print(f"   ✅ {algo_name}: {len(result)} 结果, {t1-t0:.4f}s")
                        else:
                            print(f"   ✅ {algo_name}: 结果: {result}, {t1-t0:.4f}s")
                    except Exception as e:
                        if n_nodes > 0:
                            self.log_issue(test_name, 
                                          f"算法在{config_name}上失败: {algo_name}", 
                                          "medium", str(e))
                        print(f"   ⚠️ {algo_name}: {type(e).__name__}")
            
            # 测试路径查找在复杂图上
            if n_nodes >= 10:
                print("\n测试路径查找...")
                for _ in range(20):
                    src = random.randint(0, min(9, n_nodes-1))
                    dst = random.randint(0, min(9, n_nodes-1))
                    try:
                        path = ms.shortest_path(f"AlgoTest_{src}", f"AlgoTest_{dst}")
                        if path:
                            print(f"   路径: {src}->{dst}: {len(path)} 步")
                        else:
                            pass  # 无路径是正常的
                    except Exception as e:
                        self.log_issue(test_name, f"路径查找失败", "medium", str(e))
            
            self.test_results[test_name] = True
            
        except Exception as e:
            self.log_issue(test_name, f"异常: {e}", "high")
            import traceback
            print(f"   Stacktrace: {traceback.format_exc()}")
            self.test_results[test_name] = False
    
    def test_performance_regression(self):
        """测试5: 性能回归和缓存有效性"""
        print(f"\n{'='*80}")
        print(f"⚡ 测试5: 性能回归和缓存有效性")
        print(f"{'='*80}")
        
        test_name = "performance_regression"
        temp_dir = tempfile.mkdtemp()
        
        try:
            ms = MemorySystem(temp_dir)
            ms.clear()
            
            # 添加数据
            n_test_nodes = 200
            for i in range(n_test_nodes):
                ms.remember(f"PerfTest_{i}", {"index": i})
            
            # 添加一些边
            for i in range(n_test_nodes):
                if i > 0:
                    ms.connect(f"PerfTest_{i}", f"PerfTest_{i-1}", "prev")
                if i % 10 == 0:
                    ms.connect(f"PerfTest_{i}", "PerfTest_0", "related")
            
            # 测试缓存 - 多次相同查询
            print("\n测试缓存效果...")
            
            queries = [f"PerfTest_{i}" for i in range(10)]
            
            # 第一次查询（冷缓存）
            t0 = time.time()
            for q in queries:
                ms.recall(q)
            cold_time = time.time() - t0
            
            # 清除缓存
            ms._cache.clear()
            ms._graph._cache.clear()
            
            # 预热
            for q in queries:
                ms.recall(q)
            
            # 第二次查询（暖缓存）
            t1 = time.time()
            for q in queries:
                ms.recall(q)
            warm_time = time.time() - t1
            
            speedup = cold_time / warm_time if warm_time > 0 else 0
            self.log_metric("cache_speedup", f"{speedup:.1f}x")
            print(f"   冷缓存: {cold_time*1000:.1f}ms")
            print(f"   暖缓存: {warm_time*1000:.1f}ms")
            print(f"   加速: {speedup:.1f}x")
            
            if speedup < 1.5:
                self.log_issue(test_name, "缓存加速效果不明显", "medium", 
                              f"仅 {speedup:.1f}x 加速")
            
            # 测试缓存命中率
            cache_stats1 = ms._cache.stats()
            cache_stats2 = ms._graph._cache.stats()
            print(f"   MemorySystem缓存: {cache_stats1}")
            print(f"   GraphEngine缓存: {cache_stats2}")
            
            self.test_results[test_name] = True
            
        except Exception as e:
            self.log_issue(test_name, f"异常: {e}", "high")
            import traceback
            print(f"   Stacktrace: {traceback.format_exc()}")
            self.test_results[test_name] = False
    
    def test_long_running_stability(self):
        """测试6: 长时间运行稳定性"""
        print(f"\n{'='*80}")
        print(f"⏱️ 测试6: 长时间运行稳定性")
        print(f"{'='*80}")
        
        test_name = "long_running_stability"
        temp_dir = tempfile.mkdtemp()
        
        try:
            ms = MemorySystem(temp_dir)
            ms.clear()
            
            start_mem = self.check_memory()
            start_time = time.time()
            duration = 30  # 30秒测试（为了演示时间短）
            iterations = 0
            
            print(f"运行 {duration} 秒稳定性测试...")
            
            while (time.time() - start_time) < duration:
                # 执行各种操作
                for _ in range(10):
                    ms.remember(f"Stress_{iterations}_{random.randint(0,9999)}")
                
                for _ in range(5):
                    ms.recall("Stress")
                
                ms.stats()
                
                if iterations % 5 == 0:
                    gc.collect()
                    current_mem = self.check_memory()
                    print(f"   迭代 {iterations}: {current_mem - start_mem:.1f} MB")
                
                iterations += 1
            
            end_time = time.time()
            end_mem = self.check_memory()
            
            total_ops = iterations * 15
            memory_growth = end_mem - start_mem
            ops_per_sec = total_ops / (end_time - start_time)
            
            self.log_metric("long_run_ops", total_ops)
            self.log_metric("long_run_mem_growth", f"{memory_growth:.1f} MB")
            self.log_metric("long_run_ops_per_sec", f"{ops_per_sec:.0f}")
            
            # 检查内存泄漏
            if memory_growth > 100:
                self.log_issue(test_name, "内存显著增长", "medium", 
                              f"{memory_growth:.1f} MB 在 {int(end_time-start_time)}s")
            
            print(f"\n✅ 长时间运行完成: {total_ops} 操作")
            
            self.test_results[test_name] = True
            
        except Exception as e:
            self.log_issue(test_name, f"异常: {e}", "high")
            import traceback
            print(f"   Stacktrace: {traceback.format_exc()}")
            self.test_results[test_name] = False
    
    def generate_final_report(self):
        """生成最终报告"""
        print(f"\n{'='*80}")
        print(f"📋 超极限压力测试 - 最终报告")
        print(f"{'='*80}")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for v in self.test_results.values() if v)
        total_issues = len(self.issues_found)
        
        print(f"\n📊 测试结果:")
        print(f"   总测试数: {total_tests}")
        print(f"   通过: {passed_tests}/{total_tests}")
        print(f"   发现问题: {total_issues}")
        
        if self.issues_found:
            print(f"\n⚠️ 发现的问题:")
            for issue in self.issues_found:
                print(f"   [{issue['severity'].upper()}] {issue['test']}: {issue['issue']}")
        
        print(f"\n📈 性能指标:")
        for name, value in self.performance_metrics.items():
            print(f"   {name}: {value}")
        
        return {
            "test_results": self.test_results,
            "issues_found": self.issues_found,
            "performance_metrics": self.performance_metrics,
            "memory_snapshots": self.memory_snapshots
        }
    
    def run_all_tests(self):
        """运行所有测试"""
        print(f"\n{'='*80}")
        print(f"🚀 知识图谱记忆系统 v5.0 - 超极限压力测试")
        print(f"{'='*80}")
        print(f"开始时间: {datetime.now().isoformat()}")
        
        self.test_extreme_data_scaling()
        self.test_concurrent_conflicts()
        self.test_boundary_conditions()
        self.test_algorithm_robustness()
        self.test_performance_regression()
        self.test_long_running_stability()
        
        return self.generate_final_report()


if __name__ == "__main__":
    tester = ExtremeStressTester()
    report = tester.run_all_tests()
    
    # 保存报告
    import json
    with open("extreme_stress_report.json", "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n✅ 报告已保存到: extreme_stress_report.json")
