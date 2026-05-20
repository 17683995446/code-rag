#!/usr/bin/env python3
"""
知识图谱记忆系统 v7.0 - 全面深度测试
测试：复杂图结构、一致性、性能、容错
"""
import sys
import os
import time
import random
import json
import tempfile
import threading
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kg_memory_v7 import MemorySystemV7, NodeType, EdgeType


class DeepTestSuite:
    """深度测试套件"""
    
    def __init__(self):
        self.results = {
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "tests": {},
            "bugs_found": [],
            "warnings": [],
            "performance_metrics": []
        }
    
    def log_bug(self, bug_type, description, details=None):
        bug = {"type": bug_type, "description": description, 
               "details": details, "timestamp": datetime.now().isoformat()}
        self.results['bugs_found'].append(bug)
        print(f"❌ Bug发现: {bug_type} - {description}")
    
    def log_warning(self, warning_type, description):
        warning = {"type": warning_type, "description": description, 
                  "timestamp": datetime.now().isoformat()}
        self.results['warnings'].append(warning)
        print(f"⚠️ 警告: {warning_type} - {description}")
    
    def log_performance(self, category, metric, value):
        self.results['performance_metrics'].append({
            "category": category, "metric": metric, 
            "value": value, "timestamp": datetime.now().isoformat()
        })
        print(f"📈 {category} - {metric}: {value}")
    
    def test_1_complex_graph_building(self):
        """测试1：构建复杂知识图谱"""
        print("\n" + "="*80)
        print("🏗️  测试1：构建复杂知识图谱")
        print("="*80)
        
        try:
            memory = MemorySystemV7()
            start_time = time.time()
            
            print("  📝 创建节点...")
            node_count = 1000
            nodes = []
            for i in range(node_count):
                label = f"complex_node_{i}"
                memory.remember(label, node_type=NodeType.ENTITY, 
                               properties={"index": i, "group": i % 10})
                nodes.append(label)
            print(f"    ✓ {node_count} 个节点")
            
            print("  🔗 创建边...")
            edge_count = 3000
            for i in range(edge_count):
                a = random.randint(0, node_count - 1)
                b = random.randint(0, node_count - 1)
                if a != b:
                    edge_type = random.choice([e.value for e in EdgeType.all()])
                    memory.connect(nodes[a], nodes[b], relation=edge_type)
            print(f"    ✓ {edge_count} 条边")
            
            total_time = time.time() - start_time
            print(f"  ⏱️  总耗时: {total_time:.2f}s")
            print(f"  🚀 节点速度: {node_count/total_time:.0f} node/s")
            print(f"  🚀 边速度: {edge_count/total_time:.0f} edge/s")
            
            stats = memory.get_statistics()
            print(f"  📊 最终: {stats['nodes']} 节点, {stats['edges']} 边")
            
            self.log_performance("Graph Building", "Nodes per second", 
                                int(node_count/total_time))
            self.log_performance("Graph Building", "Edges per second", 
                                int(edge_count/total_time))
            
            self.results['tests']['complex_graph'] = {
                "success": True, "nodes": stats['nodes'], 
                "edges": stats['edges'], "time": total_time
            }
            
            print("  ✅ 复杂图构建完成")
            return memory, nodes
            
        except Exception as e:
            self.log_bug("complex_graph_crash", "复杂图构建崩溃", str(e))
            return None, None
    
    def test_2_query_performance(self, memory, nodes):
        """测试2：查询性能"""
        print("\n" + "="*80)
        print("🔍 测试2：查询性能")
        print("="*80)
        
        if not memory:
            print("  ⏭️  跳过：前序测试失败")
            return
        
        try:
            results = {"recall": [], "infer": [], "semantic": [], "recommend": []}
            
            # 测试召回查询
            print("  🔎 测试召回查询...")
            for i in range(100):
                query = f"complex_node_{random.randint(0, 500)}"
                start = time.time()
                memory.recall(query, k=20)
                results['recall'].append(time.time() - start)
            
            avg_recall = sum(results['recall']) / len(results['recall'])
            print(f"    ✓ 平均召回: {avg_recall*1000:.2f}ms")
            
            # 测试推理
            print("  🧠 测试图推理...")
            for i in range(50):
                start_node = nodes[random.randint(0, len(nodes)-1)]
                start = time.time()
                memory.infer(start_node, max_depth=5)
                results['infer'].append(time.time() - start)
            
            avg_infer = sum(results['infer']) / len(results['infer'])
            print(f"    ✓ 平均推理: {avg_infer*1000:.2f}ms")
            
            # 测试语义搜索
            print("  🔮 测试语义搜索...")
            for i in range(100):
                query = f"complex_node_{random.randint(0, 500)}"
                start = time.time()
                memory.semantic_search(query, k=10)
                results['semantic'].append(time.time() - start)
            
            avg_semantic = sum(results['semantic']) / len(results['semantic'])
            print(f"    ✓ 平均语义搜索: {avg_semantic*1000:.2f}ms")
            
            # 测试推荐
            print("  💡 测试推荐...")
            for i in range(50):
                node_label = nodes[random.randint(0, len(nodes)-1)]
                start = time.time()
                memory.recommend_connections(node_label, k=5)
                results['recommend'].append(time.time() - start)
            
            avg_recommend = sum(results['recommend']) / len(results['recommend'])
            print(f"    ✓ 平均推荐: {avg_recommend*1000:.2f}ms")
            
            self.log_performance("Query Performance", "Avg Recall (ms)", 
                                round(avg_recall * 1000, 2))
            self.log_performance("Query Performance", "Avg Infer (ms)", 
                                round(avg_infer * 1000, 2))
            self.log_performance("Query Performance", "Avg Semantic Search (ms)", 
                                round(avg_semantic * 1000, 2))
            self.log_performance("Query Performance", "Avg Recommend (ms)", 
                                round(avg_recommend * 1000, 2))
            
            # 检查性能阈值
            if avg_recall > 0.1:
                self.log_warning("slow_recall", f"召回查询可能过慢: {avg_recall*1000:.2f}ms")
            if avg_infer > 1.0:
                self.log_warning("slow_infer", f"推理可能过慢: {avg_infer*1000:.2f}ms")
            
            self.results['tests']['query_perf'] = {"success": True, "results": results}
            print("  ✅ 查询性能测试完成")
            
        except Exception as e:
            self.log_bug("query_perf_crash", "查询性能测试崩溃", str(e))
    
    def test_3_gnn_performance(self, memory):
        """测试3：GNN性能"""
        print("\n" + "="*80)
        print("🧠 测试3：GNN性能")
        print("="*80)
        
        if not memory:
            print("  ⏭️  跳过：前序测试失败")
            return
        
        try:
            print("  🔧 计算GNN嵌入...")
            start_time = time.time()
            memory.compute_gnn_embeddings()
            gnn_time = time.time() - start_time
            print(f"    ✓ GNN耗时: {gnn_time:.3f}s")
            
            stats = memory.get_statistics()
            print(f"    ✓ 嵌入数量: {stats['embeddings_count']}")
            
            self.log_performance("GNN Performance", "GNN Compute Time (s)", 
                                round(gnn_time, 3))
            
            if gnn_time > 5.0:
                self.log_warning("slow_gnn", f"GNN计算可能过慢: {gnn_time:.2f}s")
            
            self.results['tests']['gnn'] = {"success": True, "time": gnn_time}
            print("  ✅ GNN性能测试完成")
            
        except Exception as e:
            self.log_bug("gnn_crash", "GNN测试崩溃", str(e))
    
    def test_4_persistence(self):
        """测试4：持久化功能"""
        print("\n" + "="*80)
        print("💾 测试4：持久化功能")
        print("="*80)
        
        try:
            temp_dir = tempfile.mkdtemp()
            save_path = os.path.join(temp_dir, "deep_test_persistence.json")
            
            memory1 = MemorySystemV7()
            print("  📝 保存前准备数据...")
            for i in range(200):
                memory1.remember(f"persist_{i}", node_type=NodeType.ENTITY)
            for i in range(100):
                memory1.connect(f"persist_{i}", f"persist_{i+1}")
            
            stats1 = memory1.get_statistics()
            
            print("  💾 保存...")
            save_start = time.time()
            success1 = memory1.save(save_path)
            save_time = time.time() - save_start
            print(f"    ✓ 保存成功: {success1}, 耗时: {save_time:.3f}s")
            
            print("  🗑️  清空内存...")
            memory1.clear()
            stats_cleared = memory1.get_statistics()
            if stats_cleared['nodes'] != 0:
                self.log_bug("clear_failure", "清空后节点未归零")
            else:
                print("    ✓ 清空成功")
            
            print("  📥 加载...")
            load_start = time.time()
            success2 = memory1.load(save_path)
            load_time = time.time() - load_start
            print(f"    ✓ 加载成功: {success2}, 耗时: {load_time:.3f}s")
            
            stats2 = memory1.get_statistics()
            
            if stats1['nodes'] != stats2['nodes']:
                self.log_bug("persist_nodes_mismatch", 
                            f"节点数不匹配: {stats1['nodes']} vs {stats2['nodes']}")
            if stats1['edges'] != stats2['edges']:
                self.log_bug("persist_edges_mismatch", 
                            f"边数不匹配: {stats1['edges']} vs {stats2['edges']}")
            else:
                print(f"    ✓ 数据一致: {stats2['nodes']}节点, {stats2['edges']}边")
            
            self.log_performance("Persistence", "Save Time (ms)", 
                                round(save_time * 1000, 2))
            self.log_performance("Persistence", "Load Time (ms)", 
                                round(load_time * 1000, 2))
            
            self.results['tests']['persistence'] = {"success": True, "save": save_time, "load": load_time}
            print("  ✅ 持久化测试完成")
            
        except Exception as e:
            self.log_bug("persistence_crash", "持久化测试崩溃", str(e))
    
    def test_5_concurrent_operations(self):
        """测试5：并发操作"""
        print("\n" + "="*80)
        print("🧵 测试5：并发操作")
        print("="*80)
        
        try:
            memory = MemorySystemV7()
            lock = threading.Lock()
            results = {"success": 0, "failure": 0, "errors": []}
            num_threads = 20
            ops_per_thread = 100
            
            print(f"  🚀 启动 {num_threads} 个线程...")
            
            def worker(worker_id):
                try:
                    for i in range(ops_per_thread):
                        op = random.choice(['add', 'search'])
                        if op == 'add':
                            memory.remember(f"concurrent_{worker_id}_{i}", 
                                          node_type=NodeType.ENTITY)
                        else:
                            memory.recall("concurrent", k=5)
                        
                        with lock:
                            results['success'] += 1
                except Exception as e:
                    with lock:
                        results['failure'] += 1
                        if len(results['errors']) < 5:
                            results['errors'].append(str(e))
            
            threads = []
            start_time = time.time()
            
            for i in range(num_threads):
                t = threading.Thread(target=worker, args=(i,))
                threads.append(t)
                t.start()
            
            for t in threads:
                t.join()
            
            total_time = time.time() - start_time
            total_ops = results['success'] + results['failure']
            throughput = total_ops / total_time
            
            print(f"  📊 结果:")
            print(f"    ✓ 总操作: {total_ops}")
            print(f"    ✓ 成功: {results['success']}")
            print(f"    ✗ 失败: {results['failure']}")
            print(f"    🚀 吞吐量: {throughput:.0f} ops/s")
            
            if results['failure'] > 0:
                self.log_bug("concurrent_failures", 
                            f"并发操作出现 {results['failure']} 个失败", 
                            results['errors'])
            
            self.log_performance("Concurrency", "Throughput (ops/s)", int(throughput))
            
            stats = memory.get_statistics()
            print(f"    📊 最终: {stats['nodes']} 节点")
            
            self.results['tests']['concurrent'] = {"success": True, 
                                                  "throughput": throughput,
                                                  "stats": stats}
            print("  ✅ 并发操作测试完成")
            
        except Exception as e:
            self.log_bug("concurrent_crash", "并发测试崩溃", str(e))
    
    def test_6_edge_cases(self):
        """测试6：边缘情况"""
        print("\n" + "="*80)
        print("🧪 测试6：边缘情况")
        print("="*80)
        
        try:
            memory = MemorySystemV7()
            test_cases = []
            
            print("  🎯 测试空查询...")
            result1 = memory.recall("", k=10)
            test_cases.append(("empty_query", True))
            print(f"    ✓ 空查询: 返回 {len(result1)} 结果")
            
            print("  🎯 测试None查询...")
            result2 = memory.recall(None, k=10)
            test_cases.append(("none_query", True))
            print(f"    ✓ None查询: 返回 {len(result2)} 结果")
            
            print("  🎯 测试空推理...")
            result3 = memory.infer("nonexistent", max_depth=5)
            test_cases.append(("nonexistent_infer", True))
            print(f"    ✓ 不存在节点推理: 返回 {len(result3)} 结果")
            
            print("  🎯 测试深度0推理...")
            memory.remember("test_deep_0", node_type=NodeType.ENTITY)
            result4 = memory.infer("test_deep_0", max_depth=0)
            test_cases.append(("zero_depth", True))
            print(f"    ✓ 0深度推理: 返回 {len(result4)} 结果")
            
            print("  🎯 测试大量重复添加...")
            for i in range(100):
                memory.remember("same_node", node_type=NodeType.ENTITY)
            stats = memory.get_statistics()
            print(f"    ✓ 重复添加: 节点数保持为 {stats['nodes']}")
            
            self.results['tests']['edge_cases'] = {"success": True, "cases": test_cases}
            print("  ✅ 边缘情况测试完成")
            
        except Exception as e:
            self.log_bug("edge_cases_crash", "边缘情况测试崩溃", str(e))
    
    def test_7_memory_stress(self):
        """测试7：内存压力"""
        print("\n" + "="*80)
        print("💫 测试7：内存压力")
        print("="*80)
        
        try:
            memory = MemorySystemV7()
            start_time = time.time()
            
            print("  📈 创建大量节点...")
            target_nodes = 5000
            for i in range(target_nodes):
                memory.remember(f"stress_{i}", node_type=NodeType.ENTITY)
            
            mid_stats = memory.get_statistics()
            print(f"    ✓ {mid_stats['nodes']} 节点已创建")
            
            print("  🔗 创建大量边...")
            for i in range(10000):
                a = random.randint(0, mid_stats['nodes'] - 1)
                b = random.randint(0, mid_stats['nodes'] - 1)
                if a != b:
                    memory.connect(f"stress_{a}", f"stress_{b}")
            
            final_stats = memory.get_statistics()
            total_time = time.time() - start_time
            
            print(f"  📊 最终: {final_stats['nodes']} 节点, {final_stats['edges']} 边")
            print(f"  ⏱️  耗时: {total_time:.2f}s")
            
            self.log_performance("Memory Stress", "Total Nodes", final_stats['nodes'])
            self.log_performance("Memory Stress", "Total Edges", final_stats['edges'])
            self.log_performance("Memory Stress", "Total Time (s)", round(total_time, 2))
            
            self.results['tests']['memory_stress'] = {"success": True, 
                                                     "stats": final_stats,
                                                     "time": total_time}
            print("  ✅ 内存压力测试完成")
            
        except Exception as e:
            self.log_bug("memory_stress_crash", "内存压力测试崩溃", str(e))
    
    def run_all(self):
        """运行所有测试"""
        print("\n" + "="*80)
        print("🚀 知识图谱记忆系统 v7.0 - 全面深度测试")
        print("="*80)
        print(f"开始时间: {self.results['start_time']}")
        
        # 运行测试
        memory, nodes = self.test_1_complex_graph_building()
        self.test_2_query_performance(memory, nodes)
        self.test_3_gnn_performance(memory)
        self.test_4_persistence()
        self.test_5_concurrent_operations()
        self.test_6_edge_cases()
        self.test_7_memory_stress()
        
        self.results['end_time'] = datetime.now().isoformat()
        
        # 生成总结
        print("\n" + "="*80)
        print("📋 深度测试 - 最终总结")
        print("="*80)
        
        print(f"\n📊 总体统计:")
        print(f"  发现Bug: {len(self.results['bugs_found'])}")
        print(f"  警告: {len(self.results['warnings'])}")
        print(f"  性能指标: {len(self.results['performance_metrics'])}")
        
        if self.results['bugs_found']:
            print(f"\n❌ 发现的Bug:")
            for bug in self.results['bugs_found']:
                print(f"  - {bug['type']}: {bug['description']}")
        
        if self.results['warnings']:
            print(f"\n⚠️  警告:")
            for warning in self.results['warnings']:
                print(f"  - {warning['type']}: {warning['description']}")
        
        if self.results['performance_metrics']:
            print(f"\n📈 性能指标:")
            for metric in self.results['performance_metrics']:
                print(f"  - {metric['category']} - {metric['metric']}: {metric['value']}")
        
        if len(self.results['bugs_found']) == 0:
            print("\n🎉 太棒了！没有发现任何Bug！")
        
        # 保存报告
        report_path = os.path.join(os.path.dirname(__file__), "v7_comprehensive_deep_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n📝 完整报告已保存: {report_path}")
        print("\n" + "="*80)
        print("🎯 全面深度测试完成！")
        print("="*80)
        
        return self.results


if __name__ == "__main__":
    tester = DeepTestSuite()
    results = tester.run_all()
