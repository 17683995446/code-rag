#!/usr/bin/env python3
"""
知识图谱记忆系统 v7.0 - 基于第一性原理的最严格测试
从核心数据结构开始，测试所有可能的边缘情况、并发冲突、资源极限
"""
import sys
import os
import time
import random
import json
import threading
import uuid
from datetime import datetime
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kg_memory_v7 import MemorySystemV7, NodeType, EdgeType


class FirstPrinciplesTest:
    """基于第一性原理的测试"""
    
    def __init__(self):
        self.results = {
            "start_time": None,
            "end_time": None,
            "tests_passed": 0,
            "tests_failed": 0,
            "issues_found": [],
            "performance_metrics": {}
        }
        self.issue_lock = threading.Lock()
    
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def record_issue(self, issue_type, description, details=None):
        with self.issue_lock:
            issue = {
                "type": issue_type,
                "description": description,
                "details": details,
                "time": datetime.now().isoformat()
            }
            self.results["issues_found"].append(issue)
        self.log(f"⚠️  ISSUE: {issue_type} - {description}")
    
    # ============================================
    # 第一部分：基础数据结构与API测试
    # ============================================
    
    def test_1_basic_data_structures(self):
        """测试1：基础数据结构与API的正确性"""
        self.log("=" * 80)
        self.log("测试1：基础数据结构与API的正确性")
        self.log("=" * 80)
        
        try:
            memory = MemorySystemV7()
            
            # 测试1.1：添加单个节点
            self.log("  1.1 测试添加单个节点")
            node_id = memory.remember("test_node_1", node_type=NodeType.ENTITY)
            assert node_id is not None, "节点ID应该不为None"
            
            # 测试1.2：查找已添加的节点
            self.log("  1.2 测试召回已添加的节点")
            recall_results = memory.recall("test_node_1")
            assert len(recall_results) >= 1, "应该找到添加的节点"
            assert "test_node_1" in recall_results[0]["label"], "节点标签不正确"
            
            # 测试1.3：添加相同标签（应该返回现有节点）
            self.log("  1.3 测试添加重复标签的节点（幂等性）")
            node_id2 = memory.remember("test_node_1", node_type=NodeType.ENTITY)
            assert node_id == node_id2, "相同标签应该返回相同的节点ID"
            
            # 测试1.4：添加多个节点
            self.log("  1.4 测试添加多个节点")
            nodes_to_add = []
            for i in range(10):
                label = f"multi_node_{i}"
                nid = memory.remember(label)
                nodes_to_add.append((label, nid))
            
            stats = memory.get_statistics()
            assert stats["nodes"] == 11, f"节点数应该是11，实际是 {stats['nodes']}"
            
            # 测试1.5：建立边连接
            self.log("  1.5 测试建立边连接")
            for i in range(5):
                src = f"multi_node_{i}"
                target = f"multi_node_{i+1}"
                edge_id = memory.connect(src, target, EdgeType.RELATED_TO)
                assert edge_id is not None, "边应该成功创建"
            
            stats = memory.get_statistics()
            assert stats["edges"] == 5, f"边数应该是5，实际是 {stats['edges']}"
            
            self.log("  ✅ 测试1通过！")
            return True
            
        except Exception as e:
            self.record_issue("basic_data_structures", str(e))
            self.log(f"  ❌ 测试1失败：{e}")
            import traceback
            self.log(traceback.format_exc())
            return False
    
    # ============================================
    # 第二部分：边缘情况与异常输入测试
    # ============================================
    
    def test_2_edge_cases(self):
        """测试2：边缘情况与异常输入"""
        self.log("=" * 80)
        self.log("测试2：边缘情况与异常输入")
        self.log("=" * 80)
        
        try:
            memory = MemorySystemV7()
            
            # 测试2.1：空字符串查询
            self.log("  2.1 测试空字符串查询")
            empty_result = memory.recall("")
            self.log(f"    空查询返回 {len(empty_result)} 个结果")
            
            # 测试2.2：None查询
            self.log("  2.2 测试None查询")
            none_result = memory.recall(None)
            self.log(f"    None查询返回 {len(none_result)} 个结果")
            
            # 测试2.3：极长标签
            self.log("  2.3 测试极长标签（10000字符）")
            long_label = "x" * 10000
            long_node_id = memory.remember(long_label)
            assert long_node_id is not None, "极长标签应该能被处理"
            
            # 测试2.4：特殊字符标签
            self.log("  2.4 测试特殊字符标签")
            special_labels = [
                "", " ", "\t", "\n", "\0",
                "!@#$%^&*()_+",
                "测试中文标签",
                "mixed_Label-123"
            ]
            for label in special_labels:
                try:
                    memory.remember(label)
                except Exception as e:
                    self.record_issue("special_label", f"标签 '{label}' 处理出错", str(e))
            
            # 测试2.5：不存在的节点召回
            self.log("  2.5 测试不存在节点的召回")
            non_existent = memory.recall("this_does_not_exist_at_all_abcxyz")
            self.log(f"    不存在节点查询返回 {len(non_existent)} 个结果")
            
            self.log("  ✅ 测试2通过！")
            return True
            
        except Exception as e:
            self.record_issue("edge_cases", str(e))
            self.log(f"  ❌ 测试2失败：{e}")
            import traceback
            self.log(traceback.format_exc())
            return False
    
    # ============================================
    # 第三部分：极端数据规模测试
    # ============================================
    
    def test_3_extreme_data_size(self):
        """测试3：极端数据规模"""
        self.log("=" * 80)
        self.log("测试3：极端数据规模")
        self.log("=" * 80)
        
        try:
            memory = MemorySystemV7()
            
            # 测试3.1：添加大量节点
            self.log("  3.1 测试添加10000个节点")
            start_time = time.time()
            
            nodes_added = 0
            for i in range(10000):
                label = f"mass_node_{i}"
                memory.remember(label)
                nodes_added += 1
                
                if i % 2000 == 0 and i > 0:
                    self.log(f"    已添加 {i} 个节点...")
            
            nodes_time = time.time() - start_time
            stats = memory.get_statistics()
            assert stats["nodes"] == 10000, f"节点数应该是10000，实际是 {stats['nodes']}"
            
            self.log(f"    10000个节点添加完成，耗时 {nodes_time:.2f}秒，平均 {(10000/nodes_time):.0f} 节点/秒")
            
            # 测试3.2：添加大量边
            self.log("  3.2 测试添加20000条边")
            start_time = time.time()
            
            for i in range(20000):
                src_idx = random.randint(0, 9999)
                target_idx = random.randint(0, 9999)
                if src_idx != target_idx:
                    memory.connect(f"mass_node_{src_idx}", f"mass_node_{target_idx}")
            
            edges_time = time.time() - start_time
            stats = memory.get_statistics()
            self.log(f"    20000条边添加完成，耗时 {edges_time:.2f}秒，最终边数 {stats['edges']}")
            
            # 测试3.3：大规模查询
            self.log("  3.3 测试大规模查询")
            query_start = time.time()
            queries = 0
            for i in range(1000):
                query = f"mass_node_{random.randint(0, 9999)}"
                memory.recall(query)
                queries += 1
            
            query_time = time.time() - query_start
            self.log(f"    1000次查询完成，耗时 {query_time:.2f}秒，平均 {(1000/query_time):.0f} 查询/秒")
            
            self.log("  ✅ 测试3通过！")
            return True
            
        except Exception as e:
            self.record_issue("extreme_data_size", str(e))
            self.log(f"  ❌ 测试3失败：{e}")
            import traceback
            self.log(traceback.format_exc())
            return False
    
    # ============================================
    # 第四部分：极端并发与冲突测试
    # ============================================
    
    def test_4_extreme_concurrency(self):
        """测试4：极端并发与冲突"""
        self.log("=" * 80)
        self.log("测试4：极端并发与冲突")
        self.log("=" * 80)
        
        try:
            memory = MemorySystemV7()
            
            # 先添加一些基础数据
            self.log("  准备基础数据...")
            for i in range(1000):
                memory.remember(f"base_node_{i}")
            
            num_threads = 100
            operations_per_thread = 200
            errors = []
            errors_lock = threading.Lock()
            completed_operations = [0]
            completed_lock = threading.Lock()
            
            self.log(f"  启动 {num_threads} 个并发线程，每个线程 {operations_per_thread} 个操作...")
            
            def concurrent_worker(worker_id):
                thread_errors = 0
                ops_done = 0
                
                for i in range(operations_per_thread):
                    try:
                        # 混合操作类型
                        op_type = random.randint(0, 4)
                        
                        if op_type == 0:
                            # 添加节点
                            label = f"concurrent_{worker_id}_{i}_{uuid.uuid4().hex[:8]}"
                            memory.remember(label)
                            
                        elif op_type == 1:
                            # 添加边
                            src = f"base_node_{random.randint(0, 999)}"
                            target = f"base_node_{random.randint(0, 999)}"
                            if src != target:
                                memory.connect(src, target)
                            
                        elif op_type == 2:
                            # 查询
                            query = f"base_node_{random.randint(0, 999)}"
                            memory.recall(query)
                            
                        elif op_type == 3:
                            # 语义搜索
                            query = f"base_{random.randint(0, 100)}"
                            memory.semantic_search(query)
                            
                        elif op_type == 4:
                            # 推荐
                            src_label = f"base_node_{random.randint(0, 999)}"
                            memory.recommend_connections(src_label)
                        
                        ops_done += 1
                        
                    except Exception as e:
                        thread_errors += 1
                        if thread_errors < 10:
                            with errors_lock:
                                errors.append(str(e))
                
                with completed_lock:
                    completed_operations[0] += ops_done
            
            start_time = time.time()
            threads = []
            for i in range(num_threads):
                t = threading.Thread(target=concurrent_worker, args=(i,))
                t.daemon = True
                t.start()
                threads.append(t)
            
            # 等待完成
            for t in threads:
                t.join()
            
            total_time = time.time() - start_time
            total_ops = completed_operations[0]
            
            self.log(f"  并发测试完成！总操作数 {total_ops}，总耗时 {total_time:.2f}秒")
            self.log(f"  错误数：{len(errors)}")
            if errors:
                self.log(f"  示例错误：{errors[:5]}")
                for err in errors[:5]:
                    self.record_issue("concurrency_error", err)
            
            # 验证最终状态一致性
            stats = memory.get_statistics()
            self.log(f"  最终状态：节点 {stats['nodes']}，边 {stats['edges']}")
            
            self.log("  ✅ 测试4完成！")
            return len(errors) == 0
            
        except Exception as e:
            self.record_issue("extreme_concurrency", str(e))
            self.log(f"  ❌ 测试4失败：{e}")
            import traceback
            self.log(traceback.format_exc())
            return False
    
    # ============================================
    # 第五部分：持久化与恢复测试
    # ============================================
    
    def test_5_persistence_recovery(self):
        """测试5：持久化与恢复"""
        self.log("=" * 80)
        self.log("测试5：持久化与恢复")
        self.log("=" * 80)
        
        import tempfile
        
        try:
            # 5.1 创建初始状态
            self.log("  5.1 创建初始知识图谱...")
            memory = MemorySystemV7()
            
            for i in range(500):
                memory.remember(f"persist_node_{i}", properties={"index": i})
            
            for i in range(300):
                src = random.randint(0, 499)
                target = random.randint(0, 499)
                if src != target:
                    memory.connect(f"persist_node_{src}", f"persist_node_{target}")
            
            initial_stats = memory.get_statistics()
            self.log(f"    初始状态：节点 {initial_stats['nodes']}，边 {initial_stats['edges']}")
            
            # 5.2 保存到临时文件
            self.log("  5.2 保存到文件...")
            temp_dir = tempfile.mkdtemp()
            save_path = os.path.join(temp_dir, "test_save.json")
            save_start = time.time()
            success = memory.save(save_path)
            save_time = time.time() - save_start
            
            if success:
                file_size = os.path.getsize(save_path) / 1024
                self.log(f"    保存成功！文件大小 {file_size:.1f}KB，耗时 {save_time:.2f}秒")
            else:
                self.record_issue("persistence_save", "保存失败")
                self.log(f"    ⚠️ 保存失败")
                return False
            
            # 5.3 重新加载
            self.log("  5.3 重新加载...")
            memory2 = MemorySystemV7()
            load_start = time.time()
            memory2.load(save_path)
            load_time = time.time() - load_start
            self.log(f"    加载完成，耗时 {load_time:.2f}秒")
            
            # 5.4 验证一致性
            self.log("  5.4 验证一致性...")
            final_stats = memory2.get_statistics()
            
            node_match = initial_stats["nodes"] == final_stats["nodes"]
            edge_match = initial_stats["edges"] == final_stats["edges"]
            
            if not node_match:
                self.record_issue("persistence_node_count", f"节点不匹配：初始 {initial_stats['nodes']}，最终 {final_stats['nodes']}")
            
            if not edge_match:
                self.record_issue("persistence_edge_count", f"边数不匹配：初始 {initial_stats['edges']}，最终 {final_stats['edges']}")
            
            if node_match and edge_match:
                self.log("    ✅ 持久化与恢复完全一致！")
            else:
                self.log(f"    ⚠️ 存在不一致")
            
            # 5.5 测试清空
            self.log("  5.5 测试清空功能...")
            memory2.clear()
            cleared_stats = memory2.get_statistics()
            self.log(f"    清空后状态：节点 {cleared_stats['nodes']}，边 {cleared_stats['edges']}")
            
            if cleared_stats["nodes"] == 0 and cleared_stats["edges"] == 0:
                self.log("    ✅ 清空功能正常")
            else:
                self.record_issue("clear_function", "清空功能未完全清除数据")
            
            self.log("  ✅ 测试5通过！")
            return node_match and edge_match
            
        except Exception as e:
            self.record_issue("persistence_recovery", str(e))
            self.log(f"  ❌ 测试5失败：{e}")
            import traceback
            self.log(traceback.format_exc())
            return False
    
    # ============================================
    # 第六部分：高级功能综合测试
    # ============================================
    
    def test_6_advanced_features(self):
        """测试6：高级功能综合"""
        self.log("=" * 80)
        self.log("测试6：高级功能综合")
        self.log("=" * 80)
        
        try:
            memory = MemorySystemV7()
            
            # 6.1 构建一些有结构的知识
            self.log("  6.1 构建结构化知识...")
            topics = ["machine_learning", "deep_learning", "neural_networks", "python", "tensorflow"]
            for topic in topics:
                memory.remember(topic, node_type=NodeType.CONCEPT)
            
            # 创建关系
            memory.connect("machine_learning", "deep_learning", EdgeType.IS_A)
            memory.connect("deep_learning", "neural_networks", EdgeType.USES)
            memory.connect("tensorflow", "deep_learning", EdgeType.USES)
            memory.connect("python", "tensorflow", EdgeType.RELATED_TO)
            
            # 6.2 测试图推理
            self.log("  6.2 测试图推理...")
            infer_results = memory.infer("machine_learning", max_depth=3)
            self.log(f"    推理返回 {len(infer_results)} 个结果")
            
            # 6.3 测试GNN计算
            self.log("  6.3 测试GNN嵌入计算...")
            gnn_start = time.time()
            memory.compute_gnn_embeddings()
            gnn_time = time.time() - gnn_start
            self.log(f"    GNN计算完成，耗时 {gnn_time:.2f}秒")
            
            # 6.4 测试语义搜索
            self.log("  6.4 测试语义搜索...")
            semantic_results = memory.semantic_search("learning", k=3)
            self.log(f"    语义搜索返回 {len(semantic_results)} 个结果")
            
            # 6.5 测试推荐系统
            self.log("  6.5 测试推荐系统...")
            recs = memory.recommend_connections("python", k=2)
            self.log(f"    推荐系统返回 {len(recs)} 个推荐")
            
            # 6.6 测试可视化数据获取
            self.log("  6.6 测试可视化数据获取...")
            viz_data = memory.get_graph_for_visualization()
            self.log(f"    可视化数据包含 {len(viz_data['nodes'])} 个节点，{len(viz_data['edges'])} 条边")
            
            self.log("  ✅ 测试6通过！")
            return True
            
        except Exception as e:
            self.record_issue("advanced_features", str(e))
            self.log(f"  ❌ 测试6失败：{e}")
            import traceback
            self.log(traceback.format_exc())
            return False
    
    # ============================================
    # 第七部分：长时间稳定性测试
    # ============================================
    
    def test_7_long_term_stability(self, duration_seconds=60):
        """测试7：长时间稳定性"""
        self.log("=" * 80)
        self.log(f"测试7：长时间稳定性测试（{duration_seconds}秒）")
        self.log("=" * 80)
        
        try:
            memory = MemorySystemV7()
            start_time = time.time()
            last_check = 0
            errors_count = 0
            
            self.log("  启动长时间稳定性测试...")
            
            while time.time() - start_time < duration_seconds:
                elapsed = time.time() - start_time
                
                # 随机混合操作
                try:
                    # 添加节点
                    memory.remember(f"stability_{uuid.uuid4().hex[:8]}")
                    
                    # 查询
                    memory.recall(f"stability_{random.randint(0, 100)}")
                    
                    # 连接（如果有足够节点）
                    stats = memory.get_statistics()
                    if stats["nodes"] > 10:
                        # 只尝试连接，不关心是否成功
                        try:
                            memory.connect(
                                f"stability_{random.randint(0, 100)}", 
                                f"stability_{random.randint(0, 100)}"
                            )
                        except:
                            pass
                
                except Exception as e:
                    errors_count += 1
                    if errors_count <= 10:
                        self.record_issue("long_term_error", str(e))
                
                # 检查点
                if elapsed - last_check >= 10:
                    stats = memory.get_statistics()
                    self.log(f"    检查点 [{int(elapsed)}秒]：节点 {stats['nodes']}，边 {stats['edges']}，错误 {errors_count}")
                    last_check = elapsed
                
                time.sleep(0.01)
            
            total_time = time.time() - start_time
            final_stats = memory.get_statistics()
            
            self.log(f"  稳定性测试完成！总耗时 {total_time:.1f}秒")
            self.log(f"  最终状态：节点 {final_stats['nodes']}，边 {final_stats['edges']}")
            self.log(f"  错误数：{errors_count}")
            
            if errors_count == 0:
                self.log("  ✅ 测试7完美通过！0错误！")
                return True
            else:
                self.log("  ⚠️ 测试7通过，但有错误")
                return False
            
        except Exception as e:
            self.record_issue("long_term_stability", str(e))
            self.log(f"  ❌ 测试7失败：{e}")
            import traceback
            self.log(traceback.format_exc())
            return False
    
    # ============================================
    # 主测试执行
    # ============================================
    
    def run_all_tests(self):
        self.log("=" * 80)
        self.log("知识图谱记忆系统 v7.0 - 基于第一性原理的完整测试")
        self.log("=" * 80)
        
        self.results["start_time"] = datetime.now().isoformat()
        
        tests = [
            ("测试1：基础数据结构与API", self.test_1_basic_data_structures),
            ("测试2：边缘情况与异常输入", self.test_2_edge_cases),
            ("测试3：极端数据规模", self.test_3_extreme_data_size),
            ("测试4：极端并发与冲突", self.test_4_extreme_concurrency),
            ("测试5：持久化与恢复", self.test_5_persistence_recovery),
            ("测试6：高级功能综合", self.test_6_advanced_features),
            ("测试7：长时间稳定性", self.test_7_long_term_stability)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            success = test_func()
            if success:
                passed += 1
            else:
                failed += 1
            self.log("")
        
        self.results["tests_passed"] = passed
        self.results["tests_failed"] = failed
        self.results["end_time"] = datetime.now().isoformat()
        
        # 最终总结
        self.log("=" * 80)
        self.log("最终测试总结")
        self.log("=" * 80)
        self.log(f" 通过测试：{passed}/{len(tests)}")
        self.log(f" 失败测试：{failed}/{len(tests)}")
        self.log(f" 发现问题：{len(self.results['issues_found'])}")
        
        if self.results["issues_found"]:
            self.log("")
            self.log("问题列表：")
            for i, issue in enumerate(self.results["issues_found"]):
                self.log(f"  {i+1}. [{issue['type']}] {issue['description']}")
        
        self.log("=" * 80)
        
        # 保存结果
        report_path = os.path.join(os.path.dirname(__file__), "v7_first_principles_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, default=str)
        
        self.log(f"报告保存到：{report_path}")
        
        return passed == len(tests) and len(self.results["issues_found"]) == 0


if __name__ == "__main__":
    tester = FirstPrinciplesTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
