#!/usr/bin/env python3
"""
知识图谱记忆系统 v7.0 - 超深度压力测试套件
基于第一性原理的极限测试：超大规模、超高并发、深度内存检测、性能退化测试
"""
import sys
import os
import time
import random
import json
import threading
import uuid
import tracemalloc
import gc
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kg_memory_v7 import MemorySystemV7, NodeType, EdgeType


class UltraDeepStressTest:
    """超深度压力测试套件"""
    
    def __init__(self):
        self.results = {
            "start_time": None,
            "end_time": None,
            "tests": [],
            "issues": [],
            "performance_data": []
        }
        self.results_lock = threading.Lock()
        self.memory = None
        self.stop_flag = threading.Event()
    
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}", flush=True)
    
    def record_test(self, test_name, passed, metrics, duration):
        with self.results_lock:
            self.results["tests"].append({
                "name": test_name,
                "passed": passed,
                "metrics": metrics,
                "duration": duration
            })
    
    def record_issue(self, issue_type, description):
        with self.results_lock:
            self.results["issues"].append({
                "type": issue_type,
                "description": description,
                "time": datetime.now().isoformat()
            })
        self.log(f"⚠️  ISSUE: {issue_type} - {description}")
    
    def test_1_ultra_large_scale(self):
        """测试1：超大规模数据测试"""
        self.log("=" * 80)
        self.log("测试1：超大规模数据测试（50,000+节点）")
        self.log("=" * 80)
        
        try:
            memory = MemorySystemV7()
            
            self.log("  1.1 添加50,000个节点...")
            start_time = time.time()
            
            nodes_target = 50000
            nodes_added = 0
            last_checkpoint = 0
            
            for i in range(nodes_target):
                label = f"ultra_node_{i}_{uuid.uuid4().hex[:8]}"
                memory.remember(label, node_type=NodeType.ENTITY)
                nodes_added += 1
                
                if i - last_checkpoint >= 10000:
                    elapsed = time.time() - start_time
                    rate = nodes_added / elapsed
                    self.log(f"    进度: {nodes_added}/{nodes_target} ({rate:.0f} 节点/秒)")
                    last_checkpoint = i
            
            nodes_time = time.time() - start_time
            stats = memory.get_statistics()
            
            self.log(f"    ✅ 添加完成！节点数: {stats['nodes']:,}, 耗时: {nodes_time:.2f}秒")
            
            # 1.2 添加100,000条边
            self.log("  1.2 添加100,000条边...")
            start_time = time.time()
            
            edges_target = 100000
            edges_added = 0
            last_checkpoint = 0
            
            for i in range(edges_target):
                src_idx = random.randint(0, stats['nodes']-1)
                target_idx = random.randint(0, stats['nodes']-1)
                if src_idx != target_idx:
                    src_label = f"ultra_node_{src_idx}_" + "x" * 8
                    target_label = f"ultra_node_{target_idx}_" + "x" * 8
                    try:
                        memory.connect(src_label, target_label)
                        edges_added += 1
                    except:
                        pass
                
                if i % 20000 == 0 and i > 0:
                    self.log(f"    进度: {edges_added}/{edges_target}")
            
            edges_time = time.time() - start_time
            stats_after = memory.get_statistics()
            
            self.log(f"    ✅ 边添加完成！边数: {stats_after['edges']:,}, 耗时: {edges_time:.2f}秒")
            
            # 1.3 大规模查询测试
            self.log("  1.3 大规模查询测试...")
            query_start = time.time()
            query_count = 5000
            
            for i in range(query_count):
                idx = random.randint(0, stats['nodes']-1)
                label = f"ultra_node_{idx}_" + "x" * 8
                memory.recall(label)
            
            query_time = time.time() - query_start
            
            self.log(f"    ✅ 查询完成！查询数: {query_count:,}, 速率: {(query_count/query_time):.0f} 查询/秒")
            
            metrics = {
                "nodes_added": stats['nodes'],
                "edges_added": stats_after['edges'],
                "node_rate": stats['nodes']/nodes_time,
                "query_rate": query_count/query_time
            }
            
            self.record_test("超大规模数据测试", True, metrics, nodes_time + edges_time + query_time)
            
            self.log("  ✅ 测试1通过！")
            return True
            
        except Exception as e:
            self.log(f"  ❌ 测试1失败：{e}")
            import traceback
            self.log(traceback.format_exc())
            self.record_test("超大规模数据测试", False, {}, 0)
            self.record_issue("ultra_large_scale", str(e))
            return False
    
    def test_2_ultra_concurrency(self):
        """测试2：超并发压力测试"""
        self.log("=" * 80)
        self.log("测试2：超并发压力测试（200线程）")
        self.log("=" * 80)
        
        try:
            memory = MemorySystemV7()
            
            self.log("  准备基础数据...")
            for i in range(5000):
                memory.remember(f"base_{i}", node_type=NodeType.ENTITY)
            
            num_threads = 200
            ops_per_thread = 500
            
            self.log(f"  启动 {num_threads} 个并发线程...")
            
            errors = []
            errors_lock = threading.Lock()
            completed_ops = [0]
            ops_lock = threading.Lock()
            
            def ultra_worker(worker_id):
                for i in range(ops_per_thread):
                    try:
                        op = random.randint(0, 6)
                        
                        if op == 0:
                            label = f"concurrent_{worker_id}_{uuid.uuid4().hex[:12]}"
                            memory.remember(label)
                        elif op == 1:
                            src_idx = random.randint(0, 4999)
                            target_idx = random.randint(0, 4999)
                            if src_idx != target_idx:
                                memory.connect(f"base_{src_idx}", f"base_{target_idx}")
                        elif op == 2:
                            memory.recall(f"base_{random.randint(0, 4999)}")
                        elif op == 3:
                            memory.semantic_search(f"base_{random.randint(0, 100)}")
                        elif op == 4:
                            memory.recommend_connections(f"base_{random.randint(0, 4999)}")
                        elif op == 5:
                            memory.infer(f"base_{random.randint(0, 4999)}", max_depth=3)
                        elif op == 6:
                            memory.get_graph_for_visualization()
                        
                        with ops_lock:
                            completed_ops[0] += 1
                        
                    except Exception as e:
                        with errors_lock:
                            if len(errors) < 10:
                                errors.append(str(e))
            
            start_time = time.time()
            threads = []
            
            for i in range(num_threads):
                t = threading.Thread(target=ultra_worker, args=(i,))
                t.daemon = True
                t.start()
                threads.append(t)
            
            # 等待完成
            for t in threads:
                t.join()
            
            total_time = time.time() - start_time
            final_stats = memory.get_statistics()
            
            self.log(f"    ✅ 超并发测试完成！总操作: {completed_ops[0]:,}, 耗时: {total_time:.2f}秒")
            self.log(f"    速率: {(completed_ops[0]/total_time):.0f} 操作/秒, 错误数: {len(errors)}")
            self.log(f"    最终节点: {final_stats['nodes']:,}, 最终边: {final_stats['edges']:,}")
            
            if errors:
                for err in errors[:3]:
                    self.log(f"    错误示例: {err}")
                    self.record_issue("ultra_concurrency_error", err)
            
            metrics = {
                "total_ops": completed_ops[0],
                "ops_rate": completed_ops[0]/total_time,
                "errors": len(errors),
                "final_nodes": final_stats['nodes'],
                "final_edges": final_stats['edges']
            }
            
            self.record_test("超并发压力测试", len(errors) == 0, metrics, total_time)
            
            self.log("  ✅ 测试2完成！")
            return len(errors) == 0
            
        except Exception as e:
            self.log(f"  ❌ 测试2失败：{e}")
            self.record_test("超并发压力测试", False, {}, 0)
            self.record_issue("ultra_concurrency", str(e))
            return False
    
    def test_3_memory_leak_detection(self):
        """测试3：内存泄漏深度检测"""
        self.log("=" * 80)
        self.log("测试3：内存泄漏深度检测")
        self.log("=" * 80)
        
        try:
            tracemalloc.start()
            
            memory = MemorySystemV7()
            
            self.log("  3.1 初始内存状态记录...")
            initial_size = sum(stat.size for stat in tracemalloc.take_snapshot().statistics('lineno'))
            self.log(f"      初始内存: {initial_size / 1024 / 1024:.2f} MB")
            
            self.log("  3.2 执行大量操作...")
            operations = 50000
            
            for i in range(operations):
                label = f"mem_test_{i}_{uuid.uuid4().hex[:8]}"
                memory.remember(label)
                
                if i % 10000 == 0 and i > 0:
                    current_mb = sum(stat.size for stat in tracemalloc.take_snapshot().statistics('lineno')) / 1024 / 1024
                    self.log(f"      进度: {i}/{operations} ({current_mb:.2f} MB)")
            
            gc.collect()
            
            self.log("  3.3 最终内存状态...")
            final_size = sum(stat.size for stat in tracemalloc.take_snapshot().statistics('lineno'))
            final_mb = final_size / 1024 / 1024
            
            memory_growth = (final_size - initial_size) / 1024 / 1024
            growth_per_op = memory_growth / operations * 1024
            
            self.log(f"      初始内存: {initial_size / 1024 / 1024:.2f} MB")
            self.log(f"      最终内存: {final_mb:.2f} MB")
            self.log(f"      内存增长: {memory_growth:.2f} MB")
            self.log(f"      每千操作增长: {growth_per_op:.4f} KB")
            
            has_leak = growth_per_op > 1.0
            
            if has_leak:
                self.log(f"      ⚠️  可能存在内存泄漏")
                self.record_issue("memory_leak", f"检测到潜在内存泄漏: {growth_per_op:.4f} KB/1000ops")
            else:
                self.log(f"      ✅ 内存增长正常，无泄漏")
            
            tracemalloc.stop()
            
            metrics = {
                "initial_mb": initial_size / 1024 / 1024,
                "final_mb": final_mb,
                "growth_mb": memory_growth,
                "growth_per_1k_ops_kb": growth_per_op,
                "has_leak": has_leak
            }
            
            self.record_test("内存泄漏检测", not has_leak, metrics, 0)
            
            self.log("  ✅ 测试3完成！")
            return not has_leak
            
        except Exception as e:
            self.log(f"  ❌ 测试3失败：{e}")
            self.record_test("内存泄漏检测", False, {}, 0)
            self.record_issue("memory_leak_detection", str(e))
            return False
    
    def test_4_performance_degradation(self):
        """测试4：性能退化测试"""
        self.log("=" * 80)
        self.log("测试4：性能退化测试")
        self.log("=" * 80)
        
        try:
            memory = MemorySystemV7()
            
            phases = [
                ("初始阶段 (0-5k)", 0, 5000),
                ("中期阶段 (5k-15k)", 5000, 15000),
                ("后期阶段 (15k-30k)", 15000, 30000),
                ("极限阶段 (30k-50k)", 30000, 50000)
            ]
            
            phase_results = []
            
            for phase_name, start, end in phases:
                self.log(f"  {phase_name}...")
                
                phase_start = time.time()
                nodes_added = 0
                
                for i in range(start, end):
                    label = f"perf_test_{i}_{uuid.uuid4().hex[:8]}"
                    memory.remember(label)
                    nodes_added += 1
                
                add_time = time.time() - phase_start
                add_rate = nodes_added / add_time
                
                query_start = time.time()
                for i in range(1000):
                    idx = random.randint(start, end-1)
                    label = f"perf_test_{idx}_" + "x" * 8
                    memory.recall(label)
                
                query_time = time.time() - query_start
                query_rate = 1000 / query_time
                
                result = {
                    "phase": phase_name,
                    "add_rate": add_rate,
                    "query_rate": query_rate
                }
                phase_results.append(result)
                
                self.log(f"      节点添加: {add_rate:.0f} 节点/秒, 查询: {query_rate:.0f} 查询/秒")
            
            initial_add_rate = phase_results[0]["add_rate"]
            final_add_rate = phase_results[-1]["add_rate"]
            add_degradation = (initial_add_rate - final_add_rate) / initial_add_rate * 100
            
            initial_query_rate = phase_results[0]["query_rate"]
            final_query_rate = phase_results[-1]["query_rate"]
            query_degradation = (initial_query_rate - final_query_rate) / initial_query_rate * 100
            
            self.log(f"  性能退化分析:")
            self.log(f"      节点添加性能退化: {add_degradation:.1f}%")
            self.log(f"      查询性能退化: {query_degradation:.1f}%")
            
            severe_degradation = add_degradation > 50 or query_degradation > 50
            
            if severe_degradation:
                self.log(f"      ⚠️  检测到严重性能退化")
                self.record_issue("performance_degradation", 
                                f"严重性能退化: 添加{add_degradation:.1f}%, 查询{query_degradation:.1f}%")
            else:
                self.log(f"      ✅ 性能退化在可接受范围内")
            
            metrics = {
                "add_degradation_percent": add_degradation,
                "query_degradation_percent": query_degradation,
                "phases": phase_results
            }
            
            self.record_test("性能退化测试", not severe_degradation, metrics, 0)
            
            self.log("  ✅ 测试4完成！")
            return not severe_degradation
            
        except Exception as e:
            self.log(f"  ❌ 测试4失败：{e}")
            self.record_test("性能退化测试", False, {}, 0)
            self.record_issue("performance_degradation_test", str(e))
            return False
    
    def test_5_data_consistency(self):
        """测试5：数据一致性深度验证"""
        self.log("=" * 80)
        self.log("测试5：数据一致性深度验证")
        self.log("=" * 80)
        
        try:
            memory = MemorySystemV7()
            
            self.log("  5.1 构建测试数据...")
            
            test_labels = [f"consistency_{i}" for i in range(1000)]
            for label in test_labels:
                memory.remember(label, node_type=NodeType.ENTITY)
            
            for i in range(500):
                src_idx = random.randint(0, 999)
                target_idx = random.randint(0, 999)
                if src_idx != target_idx:
                    memory.connect(test_labels[src_idx], test_labels[target_idx])
            
            initial_stats = memory.get_statistics()
            self.log(f"      初始状态: {initial_stats['nodes']} 节点, {initial_stats['edges']} 边")
            
            self.log("  5.2 大量并发操作...")
            num_threads = 100
            ops_per_thread = 100
            
            def consistency_worker(worker_id):
                for i in range(ops_per_thread):
                    op = random.randint(0, 3)
                    if op == 0:
                        memory.remember(f"worker_{worker_id}_node_{i}", node_type=NodeType.ENTITY)
                    elif op == 1:
                        src_idx = random.randint(0, 999)
                        target_idx = random.randint(0, 999)
                        if src_idx != target_idx:
                            memory.connect(test_labels[src_idx], test_labels[target_idx])
                    elif op == 2:
                        memory.recall(test_labels[random.randint(0, 999)])
                    elif op == 3:
                        new_mem = MemorySystemV7()
                        new_mem.remember("temp", node_type=NodeType.ENTITY)
            
            threads = []
            for i in range(num_threads):
                t = threading.Thread(target=consistency_worker, args=(i,))
                t.daemon = True
                t.start()
                threads.append(t)
            
            for t in threads:
                t.join()
            
            self.log("  5.3 验证数据一致性...")
            
            final_stats = memory.get_statistics()
            self.log(f"      最终状态: {final_stats['nodes']} 节点, {final_stats['edges']} 边")
            
            original_exists = 0
            for label in test_labels[:100]:
                results = memory.recall(label)
                if any(r["label"] == label for r in results):
                    original_exists += 1
            
            consistency_rate = original_exists / 100 * 100
            self.log(f"      原始数据完整性: {consistency_rate:.1f}%")
            
            nodes_consistent = final_stats['nodes'] == len(memory._nodes)
            self.log(f"      节点统计一致性: {'✅ 一致' if nodes_consistent else '⚠️ 不一致'}")
            
            self.log("  5.4 持久化一致性测试...")
            import tempfile
            temp_dir = tempfile.mkdtemp()
            save_path = os.path.join(temp_dir, "consistency_test.json")
            
            memory.save(save_path)
            
            new_memory = MemorySystemV7()
            new_memory.load(save_path)
            
            loaded_stats = new_memory.get_statistics()
            self.log(f"      加载后状态: {loaded_stats['nodes']} 节点, {loaded_stats['edges']} 边")
            
            nodes_match = initial_stats['nodes'] == loaded_stats['nodes']
            edges_match = initial_stats['edges'] == loaded_stats['edges']
            
            self.log(f"      持久化一致性: {'✅ 完全一致' if (nodes_match and edges_match) else '⚠️ 不一致'}")
            
            is_consistent = consistency_rate >= 95 and nodes_consistent and nodes_match and edges_match
            
            if not is_consistent:
                self.record_issue("data_consistency", f"数据一致性检查失败")
            
            metrics = {
                "original_consistency": consistency_rate,
                "nodes_consistent": nodes_consistent,
                "persistence_nodes_match": nodes_match,
                "persistence_edges_match": edges_match
            }
            
            self.record_test("数据一致性深度验证", is_consistent, metrics, 0)
            
            self.log("  ✅ 测试5完成！")
            return is_consistent
            
        except Exception as e:
            self.log(f"  ❌ 测试5失败：{e}")
            self.record_test("数据一致性深度验证", False, {}, 0)
            self.record_issue("data_consistency_test", str(e))
            return False
    
    def test_6_extended_stability(self, duration_seconds=600):
        """测试6：超长时间稳定性测试"""
        self.log("=" * 80)
        self.log(f"测试6：超长时间稳定性测试（{duration_seconds}秒）")
        self.log("=" * 80)
        
        try:
            memory = MemorySystemV7()
            start_time = time.time()
            
            self.log("  准备初始数据...")
            for i in range(5000):
                memory.remember(f"stable_{i}", node_type=NodeType.ENTITY)
            
            self.log(f"  开始 {duration_seconds}秒 稳定性测试...")
            
            last_checkpoint = 0
            total_ops = 0
            total_errors = 0
            
            while time.time() - start_time < duration_seconds:
                elapsed = time.time() - start_time
                
                try:
                    op = random.randint(0, 5)
                    
                    if op == 0:
                        memory.remember(f"stability_{uuid.uuid4().hex[:8]}")
                    elif op == 1:
                        memory.recall(f"stable_{random.randint(0, 4999)}")
                    elif op == 2:
                        memory.semantic_search("stable")
                    elif op == 3:
                        memory.infer(f"stable_{random.randint(0, 4999)}", max_depth=3)
                    elif op == 4:
                        memory.recommend_connections(f"stable_{random.randint(0, 4999)}")
                    elif op == 5:
                        memory.get_graph_for_visualization()
                    
                    total_ops += 1
                    
                except Exception as e:
                    total_errors += 1
                    if total_errors <= 5:
                        self.record_issue("extended_stability_error", str(e))
                
                if elapsed - last_checkpoint >= 60:
                    stats = memory.get_statistics()
                    rate = total_ops / elapsed if elapsed > 0 else 0
                    
                    self.log(f"    [{int(elapsed)}秒] 节点:{stats['nodes']:,} 边:{stats['edges']:,} "
                            f"操作:{total_ops:,} 速率:{rate:.0f} 错误:{total_errors}")
                    
                    last_checkpoint = elapsed
                
                time.sleep(0.01)
            
            total_time = time.time() - start_time
            final_stats = memory.get_statistics()
            
            self.log(f"    ✅ 超长时间稳定性测试完成！")
            self.log(f"       总操作: {total_ops:,}, 速率: {(total_ops/total_time):.0f} 操作/秒")
            self.log(f"       错误数: {total_errors}, 最终节点: {final_stats['nodes']:,}")
            
            success = total_errors == 0
            if total_errors > 0:
                self.record_issue("extended_stability", f"长时间运行出现 {total_errors} 个错误")
            
            metrics = {
                "total_ops": total_ops,
                "ops_rate": total_ops/total_time,
                "errors": total_errors,
                "final_nodes": final_stats['nodes'],
                "final_edges": final_stats['edges']
            }
            
            self.record_test("超长时间稳定性测试", success, metrics, total_time)
            
            self.log("  ✅ 测试6完成！")
            return success
            
        except Exception as e:
            self.log(f"  ❌ 测试6失败：{e}")
            self.record_test("超长时间稳定性测试", False, {}, 0)
            self.record_issue("extended_stability_test", str(e))
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        self.log("=" * 80)
        self.log("🚀 知识图谱记忆系统 v7.0 - 超深度压力测试套件")
        self.log("基于第一性原理的极限测试")
        self.log("=" * 80)
        
        self.results["start_time"] = datetime.now().isoformat()
        
        tests = [
            ("测试1: 超大规模数据", self.test_1_ultra_large_scale),
            ("测试2: 超并发压力", self.test_2_ultra_concurrency),
            ("测试3: 内存泄漏检测", self.test_3_memory_leak_detection),
            ("测试4: 性能退化测试", self.test_4_performance_degradation),
            ("测试5: 数据一致性", self.test_5_data_consistency),
            ("测试6: 超长时间稳定性", lambda: self.test_6_extended_stability(600)),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            self.log("")
            success = test_func()
            if success:
                passed += 1
                self.log(f"✅ {test_name} - 通过")
            else:
                failed += 1
                self.log(f"❌ {test_name} - 失败")
        
        self.results["end_time"] = datetime.now().isoformat()
        
        self.log("")
        self.log("=" * 80)
        self.log("📊 超深度压力测试 - 最终总结")
        self.log("=" * 80)
        self.log(f" 通过测试: {passed}/{len(tests)}")
        self.log(f" 失败测试: {failed}/{len(tests)}")
        self.log(f" 发现问题: {len(self.results['issues'])}")
        
        if self.results["issues"]:
            self.log("")
            self.log("问题列表:")
            for i, issue in enumerate(self.results["issues"], 1):
                self.log(f"  {i}. [{issue['type']}] {issue['description']}")
        
        self.log("=" * 80)
        
        report_path = os.path.join(os.path.dirname(__file__), "v7_ultra_deep_test_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, default=str)
        
        self.log(f"报告保存到: {report_path}")
        
        return passed == len(tests) and len(self.results["issues"]) == 0


if __name__ == "__main__":
    tester = UltraDeepStressTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
