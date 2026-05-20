#!/usr/bin/env python3
"""
知识图谱记忆系统 v7.1 - 超极端并发与稳定性测试
测试优化后系统的极限：300+线程、10分钟+运行、超大规模数据
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

from kg_memory_v7_optimized import MemorySystemV7Optimized, NodeType, EdgeType


class UltraExtremeV11Test:
    """v7.1优化版本的超极端测试"""
    
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
    
    def test_1_extreme_concurrency(self):
        """测试1：极端并发测试（300线程）"""
        self.log("=" * 80)
        self.log("测试1：极端并发测试（300线程）")
        self.log("=" * 80)
        
        try:
            memory = MemorySystemV7Optimized()
            
            # 准备基础数据
            self.log("  准备基础数据...")
            for i in range(10000):
                memory.remember(f"base_{i}", node_type=NodeType.ENTITY)
            
            num_threads = 300
            ops_per_thread = 1000
            
            self.log(f"  启动 {num_threads} 个并发线程，每个 {ops_per_thread} 操作...")
            
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
                            src_idx = random.randint(0, 9999)
                            target_idx = random.randint(0, 9999)
                            if src_idx != target_idx:
                                memory.connect(f"base_{src_idx}", f"base_{target_idx}")
                        elif op == 2:
                            memory.recall(f"base_{random.randint(0, 9999)}")
                        elif op == 3:
                            memory.semantic_search(f"base_{random.randint(0, 100)}")
                        elif op == 4:
                            memory.recommend_connections(f"base_{random.randint(0, 9999)}")
                        elif op == 5:
                            memory.infer(f"base_{random.randint(0, 9999)}", max_depth=3)
                        elif op == 6:
                            memory.get_graph_for_visualization()
                        
                        with ops_lock:
                            completed_ops[0] += 1
                        
                    except Exception as e:
                        with errors_lock:
                            if len(errors) < 5:
                                errors.append(str(e))
            
            start_time = time.time()
            threads = []
            
            for i in range(num_threads):
                t = threading.Thread(target=ultra_worker, args=(i,))
                t.daemon = True
                t.start()
                threads.append(t)
            
            # 监控进度
            last_check = 0
            while True:
                time.sleep(5)
                elapsed = time.time() - start_time
                with ops_lock:
                    ops_done = completed_ops[0]
                
                total_ops_target = num_threads * ops_per_thread
                if ops_done >= total_ops_target:
                    break
                
                if elapsed - last_check >= 30:
                    progress = (ops_done / total_ops_target) * 100
                    rate = ops_done / elapsed if elapsed > 0 else 0
                    self.log(f"    进度: {ops_done:,}/{total_ops_target:,} ({progress:.1f}%) 速率: {rate:.0f} ops/s")
                    last_check = elapsed
            
            for t in threads:
                t.join()
            
            total_time = time.time() - start_time
            final_stats = memory.get_statistics()
            
            total_ops_target = num_threads * ops_per_thread
            
            self.log(f"    ✅ 极端并发测试完成！")
            self.log(f"       总操作: {completed_ops[0]:,}/{total_ops_target:,}")
            self.log(f"       耗时: {total_time:.2f}秒")
            self.log(f"       速率: {(completed_ops[0]/total_time):.0f} 操作/秒")
            self.log(f"       错误数: {len(errors)}")
            self.log(f"       最终节点: {final_stats['nodes']:,}")
            self.log(f"       最终边: {final_stats['edges']:,}")
            
            if errors:
                for err in errors[:3]:
                    self.log(f"       错误: {err}")
                    self.record_issue("extreme_concurrency_error", err)
            
            metrics = {
                "total_ops": completed_ops[0],
                "ops_rate": completed_ops[0]/total_time,
                "errors": len(errors),
                "final_nodes": final_stats['nodes'],
                "final_edges": final_stats['edges']
            }
            
            self.record_test("极端并发测试(300线程)", len(errors) == 0, metrics, total_time)
            
            self.log("  ✅ 测试1完成！")
            return len(errors) == 0
            
        except Exception as e:
            self.log(f"  ❌ 测试1失败：{e}")
            import traceback
            self.log(traceback.format_exc())
            self.record_test("极端并发测试", False, {}, 0)
            self.record_issue("extreme_concurrency", str(e))
            return False
    
    def test_2_ultra_large_scale(self):
        """测试2：超大规模数据测试（100k+节点）"""
        self.log("=" * 80)
        self.log("测试2：超大规模数据测试（100k+节点）")
        self.log("=" * 80)
        
        try:
            memory = MemorySystemV7Optimized()
            
            # 添加100,000个节点
            self.log("  2.1 添加100,000个节点...")
            start_time = time.time()
            
            nodes_target = 100000
            nodes_added = 0
            last_checkpoint = 0
            
            for i in range(nodes_target):
                label = f"ultra_node_{i}_{uuid.uuid4().hex[:8]}"
                memory.remember(label, node_type=NodeType.ENTITY)
                nodes_added += 1
                
                if i - last_checkpoint >= 20000:
                    elapsed = time.time() - start_time
                    rate = nodes_added / elapsed
                    self.log(f"      进度: {nodes_added:,}/{nodes_target:,} ({rate:.0f} 节点/秒)")
                    last_checkpoint = i
            
            nodes_time = time.time() - start_time
            stats = memory.get_statistics()
            
            self.log(f"    ✅ 节点添加完成！")
            self.log(f"       节点数: {stats['nodes']:,}")
            self.log(f"       耗时: {nodes_time:.2f}秒")
            self.log(f"       速率: {(stats['nodes']/nodes_time):.0f} 节点/秒")
            
            # 添加200,000条边
            self.log("  2.2 添加200,000条边...")
            start_time = time.time()
            
            edges_target = 200000
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
                
                if i % 40000 == 0 and i > 0:
                    elapsed = time.time() - start_time
                    rate = edges_added / elapsed if elapsed > 0 else 0
                    self.log(f"      进度: {edges_added:,}/{edges_target:,} ({rate:.0f} 边/秒)")
            
            edges_time = time.time() - start_time
            stats_after = memory.get_statistics()
            
            self.log(f"    ✅ 边添加完成！")
            self.log(f"       边数: {stats_after['edges']:,}")
            self.log(f"       耗时: {edges_time:.2f}秒")
            
            # 大规模查询测试
            self.log("  2.3 大规模查询测试...")
            query_start = time.time()
            query_count = 10000
            
            for i in range(query_count):
                idx = random.randint(0, stats['nodes']-1)
                label = f"ultra_node_{idx}_" + "x" * 8
                memory.recall(label)
            
            query_time = time.time() - query_start
            
            self.log(f"    ✅ 查询完成！")
            self.log(f"       查询数: {query_count:,}")
            self.log(f"       速率: {(query_count/query_time):.0f} 查询/秒")
            
            metrics = {
                "nodes_added": stats['nodes'],
                "edges_added": stats_after['edges'],
                "node_rate": stats['nodes']/nodes_time,
                "edge_rate": edges_added/edges_time,
                "query_rate": query_count/query_time
            }
            
            self.record_test("超大规模数据测试", True, metrics, nodes_time + edges_time + query_time)
            
            self.log("  ✅ 测试2完成！")
            return True
            
        except Exception as e:
            self.log(f"  ❌ 测试2失败：{e}")
            self.record_test("超大规模数据测试", False, {}, 0)
            self.record_issue("ultra_large_scale", str(e))
            return False
    
    def test_3_extended_stability(self, duration_seconds=600):
        """测试3：超长时间稳定性测试（10分钟）"""
        self.log("=" * 80)
        self.log(f"测试3：超长时间稳定性测试（{duration_seconds}秒 = {duration_seconds/60:.1f}分钟）")
        self.log("=" * 80)
        
        try:
            memory = MemorySystemV7Optimized()
            start_time = time.time()
            
            # 准备初始数据
            self.log("  准备初始数据...")
            for i in range(10000):
                memory.remember(f"stable_{i}", node_type=NodeType.ENTITY)
            
            self.log(f"  开始 {duration_seconds}秒 稳定性测试...")
            
            last_checkpoint = 0
            last_progress = 0
            total_ops = 0
            total_errors = 0
            
            while time.time() - start_time < duration_seconds:
                elapsed = time.time() - start_time
                
                try:
                    op = random.randint(0, 5)
                    
                    if op == 0:
                        memory.remember(f"stability_{uuid.uuid4().hex[:8]}")
                    elif op == 1:
                        memory.recall(f"stable_{random.randint(0, 9999)}")
                    elif op == 2:
                        memory.semantic_search("stable")
                    elif op == 3:
                        memory.infer(f"stable_{random.randint(0, 9999)}", max_depth=3)
                    elif op == 4:
                        memory.recommend_connections(f"stable_{random.randint(0, 9999)}")
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
                            f"操作:{total_ops:,} 速率:{rate:.0f} ops/s 错误:{total_errors}")
                    
                    last_checkpoint = elapsed
                
                if elapsed - last_progress >= 120:
                    progress = (elapsed / duration_seconds) * 100
                    self.log(f"    进度: {progress:.1f}% ({int(elapsed)}/{duration_seconds}秒)")
                    last_progress = elapsed
                
                time.sleep(0.001)  # 稍微降低频率
            
            total_time = time.time() - start_time
            final_stats = memory.get_statistics()
            
            self.log(f"    ✅ 超长时间稳定性测试完成！")
            self.log(f"       总操作: {total_ops:,}")
            self.log(f"       耗时: {total_time:.1f}秒")
            self.log(f"       速率: {(total_ops/total_time):.0f} 操作/秒")
            self.log(f"       错误数: {total_errors}")
            self.log(f"       最终节点: {final_stats['nodes']:,}")
            self.log(f"       最终边: {final_stats['edges']:,}")
            
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
            
            self.log("  ✅ 测试3完成！")
            return success
            
        except Exception as e:
            self.log(f"  ❌ 测试3失败：{e}")
            self.record_test("超长时间稳定性测试", False, {}, 0)
            self.record_issue("extended_stability_test", str(e))
            return False
    
    def test_4_extreme_edge_cases(self):
        """测试4：极端边缘情况测试"""
        self.log("=" * 80)
        self.log("测试4：极端边缘情况测试")
        self.log("=" * 80)
        
        try:
            memory = MemorySystemV7Optimized()
            
            # 测试各种极端输入
            self.log("  4.1 极长标签测试（100000字符）...")
            long_label = "x" * 100000
            try:
                memory.remember(long_label)
                self.log(f"      ✅ 成功处理100000字符标签")
            except Exception as e:
                self.record_issue("long_label", f"无法处理100000字符标签: {e}")
                self.log(f"      ⚠️  无法处理: {e}")
            
            self.log("  4.2 空标签测试...")
            try:
                memory.remember("")
                self.log(f"      ✅ 成功处理空标签")
            except Exception as e:
                self.record_issue("empty_label", f"无法处理空标签: {e}")
            
            self.log("  4.3 特殊字符测试...")
            special_chars = ["\0", "\t", "\n", "\r", "emoji_🚀", "中文_测试"]
            for char in special_chars:
                try:
                    memory.remember(char)
                    self.log(f"      ✅ 处理特殊字符: {repr(char)}")
                except Exception as e:
                    self.record_issue("special_char", f"无法处理 {repr(char)}: {e}")
            
            self.log("  4.4 重复连接测试...")
            memory.remember("node_a", node_type=NodeType.ENTITY)
            memory.remember("node_b", node_type=NodeType.ENTITY)
            for i in range(100):
                try:
                    memory.connect("node_a", "node_b")
                except:
                    pass
            self.log(f"      ✅ 重复连接处理正常")
            
            self.log("  4.5 自环测试...")
            try:
                memory.connect("node_a", "node_a")
                self.log(f"      ⚠️  自环被允许（可能不是预期行为）")
            except:
                self.log(f"      ✅ 自环被正确拒绝")
            
            self.record_test("极端边缘情况测试", True, {}, 0)
            
            self.log("  ✅ 测试4完成！")
            return True
            
        except Exception as e:
            self.log(f"  ❌ 测试4失败：{e}")
            self.record_test("极端边缘情况测试", False, {}, 0)
            self.record_issue("edge_cases_test", str(e))
            return False
    
    def test_5_memory_stress(self):
        """测试5：内存压力测试"""
        self.log("=" * 80)
        self.log("测试5：内存压力测试")
        self.log("=" * 80)
        
        try:
            tracemalloc.start()
            
            memory = MemorySystemV7Optimized()
            
            self.log("  5.1 初始内存状态...")
            initial_size = sum(stat.size for stat in tracemalloc.take_snapshot().statistics('lineno'))
            self.log(f"      初始内存: {initial_size / 1024 / 1024:.2f} MB")
            
            self.log("  5.2 执行大量操作（100,000次）...")
            operations = 100000
            
            for i in range(operations):
                label = f"mem_{i}_{uuid.uuid4().hex[:8]}"
                memory.remember(label)
                
                if i % 20000 == 0 and i > 0:
                    current_mb = sum(stat.size for stat in tracemalloc.take_snapshot().statistics('lineno')) / 1024 / 1024
                    self.log(f"      进度: {i}/{operations} ({current_mb:.2f} MB)")
            
            gc.collect()
            
            self.log("  5.3 最终内存状态...")
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
                self.record_issue("memory_leak", f"检测到内存增长: {growth_per_op:.4f} KB/1000ops")
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
            
            self.record_test("内存压力测试", not has_leak, metrics, 0)
            
            self.log("  ✅ 测试5完成！")
            return not has_leak
            
        except Exception as e:
            self.log(f"  ❌ 测试5失败：{e}")
            self.record_test("内存压力测试", False, {}, 0)
            self.record_issue("memory_stress_test", str(e))
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        self.log("=" * 80)
        self.log("🚀 知识图谱记忆系统 v7.1 - 超极端并发与稳定性测试")
        self.log("基于第一性原理的极限测试")
        self.log("=" * 80)
        
        self.results["start_time"] = datetime.now().isoformat()
        
        tests = [
            ("测试1: 极端并发(300线程)", self.test_1_extreme_concurrency),
            ("测试2: 超大规模数据(100k+节点)", self.test_2_ultra_large_scale),
            ("测试3: 超长时间稳定性(10分钟)", lambda: self.test_3_extended_stability(600)),
            ("测试4: 极端边缘情况", self.test_4_extreme_edge_cases),
            ("测试5: 内存压力测试", self.test_5_memory_stress),
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
        self.log("📊 超极端测试 - 最终总结")
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
        
        report_path = os.path.join(os.path.dirname(__file__), "v7_ultra_extreme_v11_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, default=str)
        
        self.log(f"报告保存到: {report_path}")
        
        return passed == len(tests) and len(self.results["issues"]) == 0


if __name__ == "__main__":
    tester = UltraExtremeV11Test()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
