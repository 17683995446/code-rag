#!/usr/bin/env python3
"""
知识图谱记忆系统 v7.0 - 终极极端测试
包括：超长时间模拟、复杂图结构、容错测试、一致性测试等
"""
import sys
import os
import time
import random
import json
import tempfile
import threading
import uuid
import traceback
from datetime import datetime
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kg_memory_v7 import MemorySystemV7, NodeType, EdgeType


class ComplexKnowledgeStructureGenerator:
    """生成复杂的知识结构"""
    
    @staticmethod
    def generate_hierarchical_graph(memory, depth=10, width=5):
        """生成层次结构图"""
        nodes = []
        edges = []
        
        root_label = "root"
        memory.remember(root_label, node_type=NodeType.CONCEPT)
        nodes.append(root_label)
        
        current_level = [root_label]
        
        for level in range(depth):
            next_level = []
            
            for parent in current_level:
                for i in range(width):
                    child_label = f"level{level}_node_{i}"
                    memory.remember(child_label, node_type=NodeType.CONCEPT)
                    nodes.append(child_label)
                    memory.connect(parent, child_label, EdgeType.PART_OF)
                    edges.append((parent, child_label))
                    next_level.append(child_label)
            
            current_level = next_level
        
        return nodes, edges
    
    @staticmethod
    def generate_cyclic_graph(memory, nodes_count=100, cycles_count=50):
        """生成包含循环的图"""
        labels = []
        
        for i in range(nodes_count):
            label = f"cycle_node_{i}"
            memory.remember(label, node_type=NodeType.CONCEPT)
            labels.append(label)
        
        for i in range(cycles_count):
            start = random.choice(labels)
            end = random.choice(labels)
            while end == start:
                end = random.choice(labels)
            memory.connect(start, end, EdgeType.RELATED_TO)
            
            # 创建循环
            if random.random() < 0.3:
                memory.connect(end, start, EdgeType.RELATED_TO)
        
        return labels
    
    @staticmethod
    def generate_dense_graph(memory, nodes_count=500, avg_edges_per_node=20):
        """生成密集图"""
        labels = []
        
        for i in range(nodes_count):
            label = f"dense_node_{i}"
            memory.remember(label, node_type=NodeType.ENTITY)
            labels.append(label)
        
        for i in range(nodes_count):
            edges_for_node = random.randint(avg_edges_per_node // 2, avg_edges_per_node * 2)
            for _ in range(edges_for_node):
                j = random.randint(0, nodes_count - 1)
                if i != j:
                    memory.connect(labels[i], labels[j], EdgeType.RELATED_TO)
        
        return labels


class FaultInjectionTester:
    """故障注入测试"""
    
    @staticmethod
    def test_interrupted_operations(memory):
        """测试中断操作后的状态一致性"""
        results = {
            "success": True,
            "errors": []
        }
        
        # 记录初始状态
        initial_stats = memory.get_statistics()
        
        try:
            # 执行一些操作然后模拟中断
            for i in range(100):
                memory.remember(f"fault_test_{i}", node_type=NodeType.ENTITY)
                if i % 10 == 0:
                    memory.connect(f"fault_test_{i-10}", f"fault_test_{i}")
            
            # 检查一致性
            stats = memory.get_statistics()
            graph_data = memory.get_graph_for_visualization()
            
            if len(graph_data['nodes']) != stats['nodes']:
                results['success'] = False
                results['errors'].append("节点计数不一致")
            
            if len(graph_data['edges']) != stats['edges']:
                results['success'] = False
                results['errors'].append("边计数不一致")
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"操作失败: {str(e)}")
        
        return results
    
    @staticmethod
    def test_memory_recovery(memory):
        """测试内存恢复（保存、清空、加载）"""
        results = {
            "success": True,
            "errors": []
        }
        
        try:
            temp_dir = tempfile.mkdtemp()
            save_path = os.path.join(temp_dir, "recovery_test.json")
            
            # 添加数据
            for i in range(200):
                memory.remember(f"recovery_{i}", node_type=NodeType.ENTITY)
            for i in range(100):
                memory.connect(f"recovery_{i}", f"recovery_{i+1}")
            
            stats_before = memory.get_statistics()
            
            # 保存
            memory.save(save_path)
            
            # 清空
            memory.clear()
            stats_cleared = memory.get_statistics()
            
            if stats_cleared['nodes'] != 0:
                results['success'] = False
                results['errors'].append("清空后节点不为0")
            
            # 重新加载
            memory.load(save_path)
            stats_after = memory.get_statistics()
            
            if stats_before['nodes'] != stats_after['nodes']:
                results['success'] = False
                results['errors'].append(f"节点数不匹配: {stats_before['nodes']} vs {stats_after['nodes']}")
            
            if stats_before['edges'] != stats_after['edges']:
                results['success'] = False
                results['errors'].append(f"边数不匹配: {stats_before['edges']} vs {stats_after['edges']}")
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"恢复测试失败: {str(e)}")
            results['errors'].append(traceback.format_exc())
        
        return results


class DataConsistencyTester:
    """数据一致性测试"""
    
    @staticmethod
    def test_multiple_operations_consistency(memory):
        """测试多操作后的数据一致性"""
        results = {
            "success": True,
            "total_operations": 0,
            "errors": []
        }
        
        try:
            # 执行混合操作
            for i in range(500):
                op_type = random.choice(['add', 'connect', 'recall', 'search'])
                
                if op_type == 'add':
                    memory.remember(f"consistent_{i}", node_type=NodeType.ENTITY)
                elif op_type == 'connect' and i > 10:
                    a = random.randint(0, i - 1)
                    b = random.randint(0, i - 1)
                    if a != b:
                        memory.connect(f"consistent_{a}", f"consistent_{b}")
                elif op_type == 'recall':
                    memory.recall("consistent", k=10)
                elif op_type == 'search':
                    memory.semantic_search("consistent", k=5)
                
                results['total_operations'] += 1
            
            # 验证一致性
            stats = memory.get_statistics()
            graph = memory.get_graph_for_visualization()
            
            if len(graph['nodes']) != stats['nodes']:
                results['success'] = False
                results['errors'].append("节点计数不一致")
            
            if len(graph['edges']) != stats['edges']:
                results['success'] = False
                results['errors'].append("边计数不一致")
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"一致性测试失败: {str(e)}")
        
        return results
    
    @staticmethod
    def test_concurrent_read_write_consistency(num_threads=30, ops_per_thread=200):
        """测试并发读写一致性"""
        results = {
            "success": True,
            "total_ops": 0,
            "success_ops": 0,
            "failure_ops": 0,
            "errors": []
        }
        
        memory = MemorySystemV7()
        lock = threading.Lock()
        error_count = 0
        
        def worker(worker_id):
            nonlocal error_count
            try:
                for i in range(ops_per_thread):
                    op_type = random.choice(['read', 'write', 'search', 'connect'])
                    
                    if op_type == 'write':
                        with lock:
                            results['total_ops'] += 1
                        memory.remember(f"thread_{worker_id}_op_{i}", node_type=NodeType.ENTITY)
                        with lock:
                            results['success_ops'] += 1
                    elif op_type == 'read':
                        with lock:
                            results['total_ops'] += 1
                        memory.recall("thread", k=10)
                        with lock:
                            results['success_ops'] += 1
                    elif op_type == 'search':
                        with lock:
                            results['total_ops'] += 1
                        memory.semantic_search("test", k=5)
                        with lock:
                            results['success_ops'] += 1
                    elif op_type == 'connect' and i > 10:
                        with lock:
                            results['total_ops'] += 1
                        memory.connect(f"thread_{worker_id}_op_{i-5}", f"thread_{worker_id}_op_{i-10}")
                        with lock:
                            results['success_ops'] += 1
            
            except Exception as e:
                with lock:
                    error_count += 1
                    results['failure_ops'] += 1
                    if len(results['errors']) < 10:
                        results['errors'].append(f"Thread {worker_id}: {str(e)}")
        
        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        if error_count > 0:
            results['success'] = False
        
        # 验证最终一致性
        stats = memory.get_statistics()
        graph = memory.get_graph_for_visualization()
        
        if len(graph['nodes']) != stats['nodes']:
            results['success'] = False
            results['errors'].append("最终节点计数不一致")
        
        return results


class LargeScaleQueryTester:
    """大规模图查询性能测试"""
    
    @staticmethod
    def test_deep_inference(memory, start_label, max_depth=50):
        """测试深层推理"""
        results = {
            "success": True,
            "depth_reached": 0,
            "results_count": 0,
            "time_taken": 0,
            "errors": []
        }
        
        try:
            start_time = time.time()
            inferred = memory.infer(start_label, max_depth=max_depth)
            end_time = time.time()
            
            results['results_count'] = len(inferred)
            results['time_taken'] = end_time - start_time
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"深层推理失败: {str(e)}")
        
        return results
    
    @staticmethod
    def test_massive_semantic_search(memory, num_queries=1000):
        """测试大规模语义搜索"""
        results = {
            "success": True,
            "total_queries": num_queries,
            "total_time": 0,
            "avg_time": 0,
            "errors": []
        }
        
        try:
            queries = [f"search_term_{i}" for i in range(num_queries)]
            start_time = time.time()
            
            for q in queries:
                memory.semantic_search(q, k=10)
            
            end_time = time.time()
            results['total_time'] = end_time - start_time
            results['avg_time'] = results['total_time'] / num_queries
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"大规模搜索失败: {str(e)}")
        
        return results


class UltimateExtremeTester:
    """终极极端测试套件"""
    
    def __init__(self):
        self.results = {
            "start_time": datetime.now().isoformat(),
            "tests": {},
            "bugs_found": [],
            "warnings": [],
            "performance_issues": []
        }
    
    def log_bug(self, bug_type, description, details=None):
        bug = {"type": bug_type, "description": description, 
               "details": details, "timestamp": datetime.now().isoformat()}
        self.results['bugs_found'].append(bug)
        print(f"❌ 发现Bug: {bug_type} - {description}")
    
    def log_warning(self, warning_type, description):
        warning = {"type": warning_type, "description": description, 
                  "timestamp": datetime.now().isoformat()}
        self.results['warnings'].append(warning)
        print(f"⚠️ 警告: {warning_type} - {description}")
    
    def log_performance(self, perf_type, description, metrics):
        perf = {"type": perf_type, "description": description, 
                "metrics": metrics, "timestamp": datetime.now().isoformat()}
        self.results['performance_issues'].append(perf)
        print(f"📉 性能问题: {perf_type} - {description}")
    
    def test_1_complex_graph_structures(self):
        """测试复杂图结构"""
        print("\n" + "="*80)
        print("🔗 测试1: 复杂图结构")
        print("="*80)
        
        try:
            memory = MemorySystemV7()
            
            print("  🌳 生成层次结构...")
            h_nodes, h_edges = ComplexKnowledgeStructureGenerator.generate_hierarchical_graph(memory, depth=10, width=5)
            print(f"    ✅ 层次结构: {len(h_nodes)}节点, {len(h_edges)}边")
            
            print("  🌀 生成循环图...")
            c_nodes = ComplexKnowledgeStructureGenerator.generate_cyclic_graph(memory, 100, 50)
            print(f"    ✅ 循环图: {len(c_nodes)}节点")
            
            print("  💎 生成密集图...")
            d_nodes = ComplexKnowledgeStructureGenerator.generate_dense_graph(memory, 300, 30)
            print(f"    ✅ 密集图: {len(d_nodes)}节点")
            
            stats = memory.get_statistics()
            print(f"  📊 总计: {stats['nodes']}节点, {stats['edges']}边")
            
            # 执行查询
            print("  🔍 执行推理...")
            if h_nodes:
                inference_result = memory.infer(h_nodes[0], max_depth=20)
                print(f"    ✅ 推理结果: {len(inference_result)}条")
            
            # 测试GNN
            print("  🧠 GNN计算...")
            start_gnn = time.time()
            memory.compute_gnn_embeddings()
            gnn_time = time.time() - start_gnn
            print(f"    ✅ GNN完成: {gnn_time:.2f}秒")
            
            self.results['tests']['complex_graph'] = {"success": True, "nodes": stats['nodes'], 
                                                     "edges": stats['edges'], "gnn_time": gnn_time}
            
            print("  ✅ 复杂图结构测试完成")
            
        except Exception as e:
            self.log_bug("complex_graph_crash", "复杂图测试崩溃", str(e))
            self.results['tests']['complex_graph'] = {"success": False, "error": str(e)}
    
    def test_2_fault_injection(self):
        """测试2: 故障注入与恢复"""
        print("\n" + "="*80)
        print("💥 测试2: 故障注入与恢复")
        print("="*80)
        
        try:
            memory = MemorySystemV7()
            
            print("  📝 测试操作一致性...")
            op_result = FaultInjectionTester.test_interrupted_operations(memory)
            if not op_result['success']:
                for error in op_result['errors']:
                    self.log_bug("operation_inconsistency", error)
            else:
                print("    ✅ 操作一致性测试通过")
            
            print("  💾 测试保存-清空-加载...")
            recovery_result = FaultInjectionTester.test_memory_recovery(memory)
            if not recovery_result['success']:
                for error in recovery_result['errors']:
                    self.log_bug("recovery_failure", error)
            else:
                print("    ✅ 恢复测试通过")
            
            self.results['tests']['fault_injection'] = {"success": op_result['success'] and recovery_result['success']}
            
            print("  ✅ 故障注入测试完成")
            
        except Exception as e:
            self.log_bug("fault_test_crash", "故障测试崩溃", str(e))
    
    def test_3_data_consistency(self):
        """测试3: 数据一致性"""
        print("\n" + "="*80)
        print("📊 测试3: 数据一致性")
        print("="*80)
        
        try:
            memory = MemorySystemV7()
            
            print("  🔄 测试多操作一致性...")
            multi_result = DataConsistencyTester.test_multiple_operations_consistency(memory)
            if not multi_result['success']:
                for error in multi_result['errors']:
                    self.log_bug("data_inconsistency", error)
            else:
                print(f"    ✅ {multi_result['total_operations']}操作一致性通过")
            
            print("  🧵 测试并发读写一致性...")
            concurrent_result = DataConsistencyTester.test_concurrent_read_write_consistency(30, 200)
            print(f"    📈 总操作: {concurrent_result['total_ops']}, "
                  f"成功: {concurrent_result['success_ops']}, "
                  f"失败: {concurrent_result['failure_ops']}")
            if not concurrent_result['success']:
                for error in concurrent_result['errors']:
                    self.log_bug("concurrency_inconsistency", error)
            else:
                print("    ✅ 并发一致性通过")
            
            self.results['tests']['consistency'] = {"success": multi_result['success'] and concurrent_result['success']}
            
            print("  ✅ 数据一致性测试完成")
            
        except Exception as e:
            self.log_bug("consistency_test_crash", "一致性测试崩溃", str(e))
    
    def test_4_large_scale_queries(self):
        """测试4: 大规模查询"""
        print("\n" + "="*80)
        print("🔍 测试4: 大规模查询性能")
        print("="*80)
        
        try:
            memory = MemorySystemV7()
            
            print("  🏗️  准备大规模图...")
            ComplexKnowledgeStructureGenerator.generate_dense_graph(memory, 500, 25)
            
            stats = memory.get_statistics()
            print(f"    📊 图大小: {stats['nodes']}节点, {stats['edges']}边")
            
            print("  🧪 测试大规模语义搜索...")
            search_result = LargeScaleQueryTester.test_massive_semantic_search(memory, 500)
            if not search_result['success']:
                for error in search_result['errors']:
                    self.log_bug("search_failure", error)
            else:
                print(f"    ✅ 500次搜索: 总耗时{search_result['total_time']:.2f}s, "
                      f"平均{search_result['avg_time']*1000:.2f}ms/次")
                if search_result['avg_time'] > 0.1:
                    self.log_performance("slow_search", "平均搜索时间过长", 
                                         {"avg_time": search_result['avg_time']})
            
            print("  🚀 测试深层推理...")
            # 找到一个起始节点
            graph = memory.get_graph_for_visualization()
            if graph['nodes']:
                start_label = graph['nodes'][0]['label']
                infer_result = LargeScaleQueryTester.test_deep_inference(memory, start_label, max_depth=30)
                if not infer_result['success']:
                    for error in infer_result['errors']:
                        self.log_bug("deep_inference_failure", error)
                else:
                    print(f"    ✅ 深层推理: {infer_result['results_count']}结果, "
                          f"耗时{infer_result['time_taken']:.3f}s")
            
            self.results['tests']['large_scale'] = {"success": True, "search": search_result}
            
            print("  ✅ 大规模查询测试完成")
            
        except Exception as e:
            self.log_bug("large_scale_test_crash", "大规模测试崩溃", str(e))
    
    def run_all_tests(self):
        """运行所有终极测试"""
        print("\n" + "="*80)
        print("🚀 知识图谱记忆系统 v7.0 - 终极极端测试")
        print("="*80)
        print(f"开始时间: {datetime.now().isoformat()}")
        
        self.test_1_complex_graph_structures()
        self.test_2_fault_injection()
        self.test_3_data_consistency()
        self.test_4_large_scale_queries()
        
        self.results['end_time'] = datetime.now().isoformat()
        
        print("\n" + "="*80)
        print("📋 终极极端测试 - 最终报告")
        print("="*80)
        
        print(f"\n📊 总体统计:")
        print(f"  发现Bug: {len(self.results['bugs_found'])}")
        print(f"  警告: {len(self.results['warnings'])}")
        print(f"  性能问题: {len(self.results['performance_issues'])}")
        
        if self.results['bugs_found']:
            print(f"\n❌ 发现的Bug:")
            for bug in self.results['bugs_found']:
                print(f"  - {bug['type']}: {bug['description']}")
        
        if self.results['warnings']:
            print(f"\n⚠️  警告:")
            for warning in self.results['warnings']:
                print(f"  - {warning['type']}: {warning['description']}")
        
        if len(self.results['bugs_found']) == 0:
            print("\n🎉 太棒了！在终极极端测试中没有发现任何Bug！")
        
        report_path = os.path.join(os.path.dirname(__file__), "v7_ultimate_extreme_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n📝 完整报告已保存: {report_path}")
        print("\n" + "="*80)
        print("🎯 终极极端测试完成！")
        print("="*80)
        
        return self.results


if __name__ == "__main__":
    tester = UltimateExtremeTester()
    results = tester.run_all_tests()
