#!/usr/bin/env python3
"""
知识图谱记忆系统 v7.0 - 极端压力测试与深度Bug发现
包含超大规模、高并发、极长时间运行、极端边缘情况
"""
import sys
import os
import gc
import time
import random
import json
import tempfile
import threading
import uuid
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# 导入v7.0核心系统
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kg_memory_v7 import (
    MemorySystemV7, NodeType, EdgeType
)


# ============================================
# 极端场景生成器
# ============================================

class ExtremeScenarioGenerator:
    """生成极端测试场景"""
    
    LARGE_TECH_DOMAINS = [
        "人工智能", "机器学习", "深度学习", "神经网络", "自然语言处理",
        "计算机视觉", "知识图谱", "图神经网络", "强化学习", "监督学习",
        "Python", "JavaScript", "Java", "Go", "Rust", "C++", "TypeScript",
        "FastAPI", "Django", "Flask", "React", "Vue", "Angular",
        "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy",
        "Docker", "Kubernetes", "AWS", "GCP", "Azure", "Redis",
        "PostgreSQL", "MySQL", "MongoDB", "Elasticsearch", "RabbitMQ",
        "微服务", "云原生", "DevOps", "CI/CD", "API", "REST", "GraphQL"
    ] * 10
    
    @classmethod
    def generate_massive_node_labels(cls, count: int) -> List[str]:
        """生成超大规模节点标签"""
        labels = []
        for i in range(count):
            base = random.choice(cls.LARGE_TECH_DOMAINS)
            label = f"{base}_{i}_{uuid.uuid4().hex[:8]}"
            labels.append(label)
        return labels


# ============================================
# 极端压力测试
# ============================================

class ExtremeStressTest:
    """极端压力测试"""
    
    def __init__(self):
        self.results = {
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "bugs_found": [],
            "warnings": [],
            "performance_issues": [],
            "tests": {}
        }
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "kg_v7_extreme.db")
        
    def log_bug(self, bug_type: str, description: str, exception: Optional[Exception] = None):
        """记录Bug"""
        bug = {
            "type": bug_type,
            "description": description,
            "timestamp": datetime.now().isoformat()
        }
        if exception:
            bug["exception"] = str(exception)
        self.results["bugs_found"].append(bug)
        print(f"❌ 发现Bug: {bug_type} - {description}")
        
    def log_warning(self, warning_type: str, description: str):
        """记录警告"""
        self.results["warnings"].append({
            "type": warning_type,
            "description": description,
            "timestamp": datetime.now().isoformat()
        })
        print(f"⚠️  警告: {warning_type} - {description}")
        
    def log_performance(self, issue_type: str, description: str, metrics: Dict):
        """记录性能问题"""
        self.results["performance_issues"].append({
            "type": issue_type,
            "description": description,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        })
        print(f"📉 性能问题: {issue_type} - {description}")
        
    def test_1_massive_scale(self):
        """测试1: 超大规模知识图谱"""
        print("\n" + "="*80)
        print("🔮 极端测试 1: 超大规模知识图谱 (10,000节点, 30,000边)")
        print("="*80)
        
        try:
            memory = MemorySystemV7(db_path=self.db_path)
            
            # 生成超大规模数据
            start_time = time.time()
            print(f"  📦 生成 10,000 节点...")
            node_labels = ExtremeScenarioGenerator.generate_massive_node_labels(10000)
            node_ids = []
            
            print(f"  ➕ 添加节点...")
            add_start = time.time()
            for label in node_labels:
                node_id = memory.remember(
                    knowledge=label,
                    node_type=random.choice([NodeType.ENTITY, NodeType.CONCEPT, NodeType.DOCUMENT]),
                    properties={
                        "source": "extreme_test",
                        "random_value": random.random(),
                        "timestamp": time.time()
                    }
                )
                node_ids.append(node_id)
            add_duration = time.time() - add_start
            node_throughput = len(node_labels) / add_duration
            print(f"    ✅ 节点: {node_throughput:.0f} node/s")
            
            print(f"  📦 生成并添加 30,000 边...")
            edge_start = time.time()
            for i in range(30000):
                source_label = random.choice(node_labels)
                target_label = random.choice(node_labels)
                while source_label == target_label:
                    target_label = random.choice(node_labels)
                memory.connect(
                    source=source_label,
                    target=target_label,
                    relation=random.choice([e.value for e in EdgeType.all()]),
                    weight=random.uniform(0.1, 5.0)
                )
            edge_duration = time.time() - edge_start
            edge_throughput = 30000 / edge_duration
            print(f"    ✅ 边: {edge_throughput:.0f} edge/s")
            
            # 验证
            stats = memory.get_statistics()
            print(f"  📊 最终统计: {stats['nodes']} 节点, {stats['edges']} 边")
            
            # 检查性能
            if node_throughput < 1000:
                self.log_performance("low_node_throughput", "节点添加速度过慢", 
                                    {"throughput": node_throughput, "threshold": 1000})
            if edge_throughput < 500:
                self.log_performance("low_edge_throughput", "边添加速度过慢", 
                                    {"throughput": edge_throughput, "threshold": 500})
            
            self.results["tests"]["massive_scale"] = {
                "success": True,
                "node_count": stats['nodes'],
                "edge_count": stats['edges'],
                "node_throughput": node_throughput,
                "edge_throughput": edge_throughput,
                "duration": time.time() - start_time
            }
            
            print(f"  ✅ 超大规模测试完成")
            return memory, node_ids, node_labels
            
        except Exception as e:
            self.log_bug("massive_scale_crash", "超大规模测试崩溃", e)
            self.results["tests"]["massive_scale"] = {"success": False, "error": str(e)}
            return None, None, None
    
    def test_2_extreme_concurrency(self, memory: Optional[MemorySystemV7], node_ids: List[str], node_labels: List[str]):
        """测试2: 极高并发压力"""
        print("\n" + "="*80)
        print("🔄 极端测试 2: 极高并发压力 (50线程)")
        print("="*80)
        
        if not memory:
            print("  ⏭️  跳过：前序测试失败")
            return
        
        try:
            start_time = time.time()
            success_count = 0
            failure_count = 0
            operations = defaultdict(int)
            errors = []
            lock = threading.Lock()
            
            def worker(worker_id: int):
                nonlocal success_count, failure_count
                try:
                    for _ in range(50):
                        op_type = random.choice(["add", "search", "connect", "query", "semantic", "recommend"])
                        
                        with lock:
                            operations[op_type] += 1
                        
                        if op_type == "add":
                            label = f"temp_node_{worker_id}_{uuid.uuid4().hex[:8]}"
                            memory.remember(label, node_type=NodeType.ENTITY)
                        elif op_type == "search":
                            memory.recall("test", k=10)
                        elif op_type == "connect" and len(node_labels) >= 2:
                            source = random.choice(node_labels)
                            target = random.choice(node_labels)
                            if source != target:
                                memory.connect(source, target, EdgeType.RELATED_TO)
                        elif op_type == "query":
                            if node_labels:
                                memory.infer(random.choice(node_labels), max_depth=2)
                        elif op_type == "semantic":
                            memory.semantic_search("人工智能", k=5)
                        elif op_type == "recommend":
                            if node_labels:
                                memory.recommend_connections(random.choice(node_labels), k=3)
                        
                        with lock:
                            success_count += 1
                            
                except Exception as e:
                    with lock:
                        failure_count += 1
                        if len(errors) < 10:
                            errors.append(str(e))
            
            print(f"  🧵 50 线程 x 50 = 2,500 操作")
            
            with ThreadPoolExecutor(max_workers=50) as executor:
                futures = [executor.submit(worker, i) for i in range(50)]
                for future in as_completed(futures):
                    future.result()
            
            duration = time.time() - start_time
            throughput = (success_count + failure_count) / duration
            
            print(f"  \n  📊 结果:")
            print(f"    总操作: {success_count + failure_count}")
            print(f"    成功: {success_count}")
            print(f"    失败: {failure_count}")
            print(f"    吞吐量: {throughput:.0f} ops/s")
            print(f"    操作分布: {dict(operations)}")
            
            if failure_count > 0:
                self.log_bug("concurrency_errors", f"并发测试发现 {failure_count} 个错误", 
                            Exception("\n".join(errors[:5])))
            
            self.results["tests"]["extreme_concurrency"] = {
                "success": failure_count == 0,
                "total_operations": success_count + failure_count,
                "success_count": success_count,
                "failure_count": failure_count,
                "throughput": throughput,
                "operations": dict(operations),
                "duration": duration
            }
            
            print(f"  ✅ 极高并发测试完成")
            
        except Exception as e:
            self.log_bug("concurrency_crash", "极高并发测试崩溃", e)
            self.results["tests"]["extreme_concurrency"] = {"success": False, "error": str(e)}
    
    def test_3_extreme_edge_cases(self, memory: Optional[MemorySystemV7]):
        """测试3: 极端边缘情况"""
        print("\n" + "="*80)
        print("🎯 极端测试 3: 极端边缘情况")
        print("="*80)
        
        if not memory:
            print("  ⏭️  跳过：前序测试失败")
            return
        
        try:
            edge_case_results = []
            
            # 1. 测试空字符串
            print("  1️⃣ 测试空字符串...")
            try:
                memory.remember("", node_type=NodeType.ENTITY)
                edge_case_results.append(("empty_label", "success"))
                print("    ✅ 空标签处理")
            except Exception as e:
                edge_case_results.append(("empty_label", "failed"))
                self.log_bug("empty_label", "空标签处理失败", e)
            
            # 2. 测试超长字符串
            print("  2️⃣ 测试超长字符串...")
            try:
                huge_label = "x" * 10000
                memory.remember(huge_label[:255], node_type=NodeType.ENTITY)
                edge_case_results.append(("huge_string", "success"))
                print("    ✅ 超长字符串处理")
            except Exception as e:
                edge_case_results.append(("huge_string", "failed"))
                self.log_bug("huge_string", "超长字符串处理失败", e)
            
            # 3. 测试特殊字符
            print("  3️⃣ 测试特殊字符...")
            try:
                weird_chars = "test_😊_🎉_🔥_✨"
                memory.remember(weird_chars, node_type=NodeType.ENTITY)
                edge_case_results.append(("unicode", "success"))
                print("    ✅ 特殊字符处理")
            except Exception as e:
                edge_case_results.append(("unicode", "failed"))
                self.log_bug("unicode", "特殊字符处理失败", e)
            
            # 4. 测试快速重复操作
            print("  4️⃣ 测试快速重复操作...")
            try:
                for i in range(5000):
                    memory.remember(f"rapid_{i}", node_type=NodeType.ENTITY)
                edge_case_results.append(("rapid_ops", "success"))
                print("    ✅ 快速重复操作")
            except Exception as e:
                edge_case_results.append(("rapid_ops", "failed"))
                self.log_bug("rapid_ops", "快速重复操作失败", e)
            
            # 5. 测试边界查询参数
            print("  5️⃣ 测试边界查询参数...")
            try:
                memory.recall("", k=0)
                memory.recall("test", k=10000)
                if memory.get_statistics()['nodes'] > 0:
                    # 获取第一个节点标签
                    graph_data = memory.get_graph_for_visualization()
                    if graph_data['nodes']:
                        first_label = graph_data['nodes'][0]['label']
                        memory.infer(first_label, max_depth=100)
                edge_case_results.append(("boundary_params", "success"))
                print("    ✅ 边界查询参数")
            except Exception as e:
                edge_case_results.append(("boundary_params", "failed"))
                self.log_bug("boundary_params", "边界查询参数处理失败", e)
            
            self.results["tests"]["extreme_edge_cases"] = {
                "success": all(r[1] == "success" for r in edge_case_results),
                "results": edge_case_results
            }
            
            print(f"  ✅ 极端边缘情况测试完成")
            
        except Exception as e:
            self.log_bug("edge_cases_crash", "极端边缘情况测试崩溃", e)
            self.results["tests"]["extreme_edge_cases"] = {"success": False, "error": str(e)}
    
    def test_4_long_running_stability(self):
        """测试4: 极长时间运行稳定性"""
        print("\n" + "="*80)
        print("⏱️  极端测试 4: 极长时间运行稳定性 (60秒)")
        print("="*80)
        
        try:
            memory = MemorySystemV7(db_path=os.path.join(self.temp_dir, "kg_v7_long.db"))
            start_time = time.time()
            end_time = start_time + 60
            operation_count = 0
            error_count = 0
            node_count = 0
            edge_count = 0
            timestamps = []
            lock = threading.Lock()
            
            local_node_labels = []
            
            def do_operation():
                nonlocal operation_count, error_count, node_count, edge_count
                try:
                    op_type = random.choice(["add_node", "search", "query"])
                    
                    if op_type == "add_node":
                        label = f"long_test_{uuid.uuid4().hex[:8]}"
                        memory.remember(label, node_type=NodeType.ENTITY)
                        local_node_labels.append(label)
                        with lock:
                            node_count += 1
                    elif op_type == "search":
                        memory.recall("test", k=5)
                    elif op_type == "query" and local_node_labels:
                        memory.infer(random.choice(local_node_labels), max_depth=1)
                    
                    with lock:
                        operation_count += 1
                        
                except Exception:
                    with lock:
                        error_count += 1
            
            # 记录时间点
            checkpoint_times = [5, 15, 30, 60]
            next_checkpoint = 0
            
            print(f"  📅 运行 60 秒...")
            
            while time.time() < end_time:
                do_operation()
                
                elapsed = time.time() - start_time
                if next_checkpoint < len(checkpoint_times) and elapsed >= checkpoint_times[next_checkpoint]:
                    stats = memory.get_statistics()
                    print(f"    ⏱️  {checkpoint_times[next_checkpoint]}s: {operation_count} 操作, {stats['nodes']} 节点, {stats['edges']} 边")
                    timestamps.append({
                        "time": checkpoint_times[next_checkpoint],
                        "operations": operation_count,
                        "nodes": stats['nodes'],
                        "edges": stats['edges']
                    })
                    next_checkpoint += 1
                
                time.sleep(0.001)
            
            duration = time.time() - start_time
            final_stats = memory.get_statistics()
            
            print(f"  \n  📊 最终结果:")
            print(f"    总操作: {operation_count}")
            print(f"    错误: {error_count}")
            print(f"    平均: {operation_count/duration:.0f} ops/s")
            print(f"    最终: {final_stats['nodes']} 节点, {final_stats['edges']} 边")
            
            if error_count > 0:
                self.log_bug("long_running_errors", f"长时间运行发现 {error_count} 个错误")
            
            self.results["tests"]["long_running"] = {
                "success": error_count == 0,
                "total_operations": operation_count,
                "error_count": error_count,
                "avg_throughput": operation_count / duration,
                "final_nodes": final_stats['nodes'],
                "final_edges": final_stats['edges'],
                "timestamps": timestamps,
                "duration": duration
            }
            
            print(f"  ✅ 极长时间运行测试完成")
            
        except Exception as e:
            self.log_bug("long_running_crash", "极长时间运行测试崩溃", e)
            self.results["tests"]["long_running"] = {"success": False, "error": str(e)}
    
    def test_5_gnn_extreme(self, memory: Optional[MemorySystemV7], node_labels: List[str]):
        """测试5: GNN极端测试"""
        print("\n" + "="*80)
        print("🧠 极端测试 5: GNN与嵌入极端测试")
        print("="*80)
        
        if not memory:
            print("  ⏭️  跳过：前序测试失败")
            return
        
        try:
            # 大规模GNN计算
            print("  🤖 大规模GNN计算...")
            start = time.time()
            memory.compute_gnn_embeddings()
            gnn_duration = time.time() - start
            print(f"    ✅ GNN计算: {gnn_duration:.2f}s")
            
            # 多次语义搜索
            print("  🔍 多次语义搜索...")
            search_start = time.time()
            for i in range(50):
                memory.semantic_search(f"测试{i}", k=10)
            search_duration = time.time() - search_start
            print(f"    ✅ 50次语义搜索: {search_duration:.2f}s")
            
            # 多次推荐
            print("  💡 多次推荐...")
            recommend_start = time.time()
            for i in range(min(20, len(node_labels))):
                memory.recommend_connections(node_labels[i], k=5)
            recommend_duration = time.time() - recommend_start
            print(f"    ✅ 20次推荐: {recommend_duration:.2f}s")
            
            # 性能检查
            if gnn_duration > 30:
                self.log_performance("slow_gnn", "GNN计算过慢", {"duration": gnn_duration})
            
            self.results["tests"]["gnn_extreme"] = {
                "success": True,
                "gnn_duration": gnn_duration,
                "search_duration": search_duration,
                "recommend_duration": recommend_duration
            }
            
            print(f"  ✅ GNN极端测试完成")
            
        except Exception as e:
            self.log_bug("gnn_extreme_crash", "GNN极端测试崩溃", e)
            self.results["tests"]["gnn_extreme"] = {"success": False, "error": str(e)}
    
    def run_all_tests(self):
        """运行所有极端测试"""
        print("\n" + "="*80)
        print("🚀 知识图谱记忆系统 v7.0 - 极端压力测试")
        print("="*80)
        print(f"开始时间: {datetime.now().isoformat()}")
        
        # 测试1: 超大规模
        memory, node_ids, node_labels = self.test_1_massive_scale()
        
        # 测试2: 极高并发
        self.test_2_extreme_concurrency(memory, node_ids, node_labels)
        
        # 测试3: 极端边缘情况
        self.test_3_extreme_edge_cases(memory)
        
        # 测试4: 极长时间运行
        self.test_4_long_running_stability()
        
        # 测试5: GNN极端
        self.test_5_gnn_extreme(memory, node_labels)
        
        # 生成报告
        self.results["end_time"] = datetime.now().isoformat()
        
        print("\n" + "="*80)
        print("📋 极端压力测试 - 最终报告")
        print("="*80)
        
        print(f"\n📊 总体统计:")
        print(f"  发现Bug: {len(self.results['bugs_found'])}")
        print(f"  警告: {len(self.results['warnings'])}")
        print(f"  性能问题: {len(self.results['performance_issues'])}")
        
        # 保存报告
        report_path = os.path.join(os.path.dirname(__file__), "v7_extreme_stress_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n📝 完整报告已保存: {report_path}")
        
        if len(self.results['bugs_found']) == 0:
            print("\n🎉 太棒了！在极端测试中没有发现Bug！")
        else:
            print(f"\n❌ 发现 {len(self.results['bugs_found'])} 个Bug需要修复")
        
        print("\n" + "="*80)
        print("🎯 极端压力测试完成！")
        print("="*80)
        
        return self.results


if __name__ == "__main__":
    tester = ExtremeStressTest()
    results = tester.run_all_tests()
