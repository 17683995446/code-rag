#!/usr/bin/env python3
"""
知识图谱记忆系统 v7.0 - 真实世界压力测试与Bug修复
包含长时间运行测试、边缘情况、并发压力、内存泄漏检测等
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
# 真实世界场景生成器
# ============================================

class RealWorldScenarioGenerator:
    """生成真实世界的知识图谱场景"""
    
    TECH_DOMAINS = [
        "人工智能", "机器学习", "深度学习", "神经网络", "自然语言处理",
        "计算机视觉", "知识图谱", "图神经网络", "强化学习", "监督学习",
        "Python", "JavaScript", "Java", "Go", "Rust", "C++", "TypeScript",
        "FastAPI", "Django", "Flask", "React", "Vue", "Angular",
        "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy"
    ]
    
    COMPANIES = [
        "Google", "Microsoft", "Apple", "Amazon", "Meta", "OpenAI", "Anthropic",
        "Tesla", "NVIDIA", "Intel", "AMD", "Salesforce", "Netflix", "Spotify"
    ]
    
    CONCEPTS = [
        "算法", "数据结构", "设计模式", "架构", "性能优化", "测试", "部署",
        "容器化", "微服务", "云原生", "DevOps", "CI/CD", "API", "REST", "GraphQL"
    ]
    
    @classmethod
    def generate_realistic_nodes(cls, count: int) -> List[Dict]:
        """生成真实节点"""
        nodes = []
        
        all_terms = cls.TECH_DOMAINS + cls.COMPANIES + cls.CONCEPTS
        
        for i in range(count):
            if i < len(all_terms):
                label = all_terms[i]
            else:
                base = random.choice(all_terms)
                label = f"{base}_{i}"
            
            if label in cls.COMPANIES:
                node_type = NodeType.ENTITY
            elif label in cls.TECH_DOMAINS:
                node_type = NodeType.CONCEPT
            else:
                node_type = NodeType.CONCEPT
            
            nodes.append({
                "label": label,
                "type": node_type,
                "properties": {
                    "source": "test",
                    "index": i,
                    "random_value": random.random(),
                    "timestamp": time.time()
                }
            })
        
        return nodes
    
    @classmethod
    def generate_realistic_edges(cls, node_labels: List[str], count: int) -> List[Dict]:
        """生成真实关系"""
        edges = []
        # 使用EdgeType的值列表
        relation_types = [e.value for e in EdgeType.all()]
        
        for i in range(count):
            source = random.choice(node_labels)
            target = random.choice(node_labels)
            
            while source == target:
                target = random.choice(node_labels)
            
            edges.append({
                "source": source,
                "target": target,
                "relation": random.choice(relation_types),
                "weight": random.uniform(0.5, 2.0)
            })
        
        return edges


# ============================================
# Bug发现与追踪系统
# ============================================

class BugTracker:
    """Bug跟踪器"""
    
    def __init__(self):
        self.bugs = []
        self.warnings = []
        self.performance_issues = []
    
    def report_bug(self, test_name: str, problem: str, 
                  severity: str = "high", details: Any = None):
        """报告Bug"""
        bug = {
            "id": str(uuid.uuid4())[:8],
            "test": test_name,
            "problem": problem,
            "severity": severity,
            "details": details,
            "time": datetime.now().isoformat()
        }
        self.bugs.append(bug)
        print(f"❌  [{severity.upper()}] {test_name}: {problem}")
    
    def report_warning(self, test_name: str, problem: str, details: Any = None):
        """报告警告"""
        warning = {
            "test": test_name,
            "problem": problem,
            "details": details,
            "time": datetime.now().isoformat()
        }
        self.warnings.append(warning)
        print(f"⚠️  {test_name}: {problem}")
    
    def report_performance(self, test_name: str, metric: str, 
                          actual: float, threshold: float):
        """报告性能问题"""
        if actual < threshold:
            issue = {
                "test": test_name,
                "metric": metric,
                "actual": actual,
                "threshold": threshold,
                "time": datetime.now().isoformat()
            }
            self.performance_issues.append(issue)
            print(f"🐢 {test_name}: {metric}={actual:.2f} (阈值={threshold:.2f})")
    
    def get_summary(self) -> Dict:
        """获取总结"""
        return {
            "total_bugs": len(self.bugs),
            "total_warnings": len(self.warnings),
            "performance_issues": len(self.performance_issues),
            "bugs": self.bugs,
            "warnings": self.warnings,
            "performance": self.performance_issues
        }


# ============================================
# 内存泄漏检测器
# ============================================

class MemoryLeakDetector:
    """内存泄漏检测器"""
    
    def __init__(self):
        self.history = []
        self.process = None
        
        try:
            import psutil
            self.process = psutil.Process()
        except ImportError:
            print("⚠️  psutil 不可用，部分内存检测功能受限")
    
    def get_memory_mb(self) -> float:
        """获取当前内存使用"""
        if self.process:
            try:
                return self.process.memory_info().rss / 1024 / 1024
            except:
                pass
        return 0.0
    
    def record(self, label: str):
        """记录内存使用"""
        gc.collect()
        memory = self.get_memory_mb()
        self.history.append({
            "label": label,
            "memory": memory,
            "time": datetime.now().isoformat()
        })
        print(f"📊 {label}: {memory:.2f} MB")
    
    def check_leak(self, initial: float, final: float, 
                  threshold: float = 50.0) -> bool:
        """检查是否泄漏"""
        growth = final - initial
        if growth > threshold:
            print(f"⚠️  内存增长警告: {growth:.2f} MB")
            return True
        return False


# ============================================
# 压力测试套件
# ============================================

class StressTestSuite:
    """压力测试套件"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.system = MemorySystemV7()
        self.bug_tracker = BugTracker()
        self.memory_detector = MemoryLeakDetector()
        self.test_results = {}
        self.lock = threading.Lock()
    
    def test_large_scale_knowledge_graph(self) -> Dict:
        """测试大规模知识图谱构建"""
        test_name = "大规模知识图谱"
        print("\n" + "="*80)
        print(f"🔮 测试 1: {test_name}")
        print("="*80)
        
        start = time.time()
        self.memory_detector.record("开始大规模测试")
        
        try:
            node_count = 1000
            edge_count = 2000
            
            # 生成数据
            print(f"  📦 生成 {node_count} 节点, {edge_count} 边...")
            nodes = RealWorldScenarioGenerator.generate_realistic_nodes(node_count)
            node_labels = [n["label"] for n in nodes]
            edges = RealWorldScenarioGenerator.generate_realistic_edges(node_labels, edge_count)
            
            # 添加节点
            print(f"  ➕ 添加节点...")
            node_start = time.time()
            for node_data in nodes:
                try:
                    self.system.remember(
                        node_data["label"],
                        properties=node_data["properties"],
                        node_type=node_data["type"],
                        compute_embedding=(random.random() > 0.5)
                    )
                except Exception as e:
                    self.bug_tracker.report_bug(
                        test_name, f"节点添加失败: {e}", "high", node_data
                    )
            
            node_time = time.time() - node_start
            node_rate = node_count / node_time if node_time > 0 else 0
            print(f"  ✅ 节点: {node_rate:.0f} node/s")
            
            # 添加边
            print(f"  🔗 添加边...")
            edge_start = time.time()
            edge_success = 0
            for edge_data in edges:
                try:
                    self.system.connect(
                        edge_data["source"],
                        edge_data["target"],
                        edge_data["relation"],
                        edge_data["weight"]
                    )
                    edge_success += 1
                except Exception as e:
                    self.bug_tracker.report_bug(
                        test_name, f"边添加失败: {e}", "medium", edge_data
                    )
            
            edge_time = time.time() - edge_start
            edge_rate = edge_success / edge_time if edge_time > 0 else 0
            print(f"  ✅ 边: {edge_rate:.0f} edge/s")
            
            # 验证
            stats = self.system.get_statistics()
            print(f"  📊 最终统计: {stats['nodes']} 节点, {stats['edges']} 边")
            
            # 性能检查
            self.bug_tracker.report_performance(test_name, "node_rate", node_rate, 1000)
            
            self.memory_detector.record("大规模测试结束")
            
            return {
                "passed": len(self.bug_tracker.bugs) == 0,
                "nodes_added": stats["nodes"],
                "edges_added": stats["edges"],
                "node_rate": node_rate,
                "edge_rate": edge_rate,
                "elapsed": time.time() - start
            }
            
        except Exception as e:
            self.bug_tracker.report_bug(test_name, f"测试崩溃: {e}", "critical")
            return {"passed": False, "error": str(e)}
    
    def test_concurrent_stress(self) -> Dict:
        """测试并发压力"""
        test_name = "并发压力测试"
        print("\n" + "="*80)
        print(f"🔄 测试 2: {test_name}")
        print("="*80)
        
        self.system.clear()
        
        # 初始化基础数据
        for i in range(100):
            self.system.remember(f"并发测试_{i}")
        
        thread_count = 20
        ops_per_thread = 500
        total_ops = thread_count * ops_per_thread
        
        print(f"  🧵 {thread_count} 线程 x {ops_per_thread} = {total_ops} 操作")
        
        errors = 0
        operations = defaultdict(int)
        start = time.time()
        
        def worker(thread_id: int):
            nonlocal errors
            for i in range(ops_per_thread):
                try:
                    op_type = random.choice([
                        "recall", "infer", "semantic", "recommend"
                    ])
                    
                    query = f"并发测试_{random.randint(0, 99)}"
                    
                    if op_type == "recall":
                        self.system.recall(query, k=3)
                    elif op_type == "infer":
                        self.system.infer(query, max_depth=2)
                    elif op_type == "semantic":
                        self.system.semantic_search(query, k=3)
                    elif op_type == "recommend":
                        self.system.recommend_connections(query, k=2)
                    
                    with self.lock:
                        operations[op_type] += 1
                        
                except Exception as e:
                    with self.lock:
                        errors += 1
                    if errors <= 5:
                        self.bug_tracker.report_bug(
                            test_name, f"线程{thread_id}操作失败: {e}", "high"
                        )
        
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            futures = [executor.submit(worker, tid) for tid in range(thread_count)]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    self.bug_tracker.report_bug(
                        test_name, f"线程异常: {e}", "critical"
                    )
        
        elapsed = time.time() - start
        throughput = total_ops / elapsed
        
        print(f"\n  📊 结果:")
        print(f"    总操作: {total_ops}")
        print(f"    成功: {total_ops - errors}")
        print(f"    失败: {errors}")
        print(f"    吞吐量: {throughput:.0f} ops/s")
        print(f"    操作分布: {dict(operations)}")
        
        if errors > total_ops * 0.01:
            self.bug_tracker.report_bug(
                test_name, f"错误率过高: {errors}/{total_ops}", "high"
            )
        
        return {
            "passed": errors <= total_ops * 0.01,
            "throughput": throughput,
            "errors": errors,
            "elapsed": elapsed
        }
    
    def test_extreme_edge_cases(self) -> Dict:
        """测试极端边缘情况"""
        test_name = "极端边缘情况"
        print("\n" + "="*80)
        print(f"🎯 测试 3: {test_name}")
        print("="*80)
        
        self.system.clear()
        test_cases = []
        
        # 测试1: 空字符串
        print(f"  1️⃣ 测试空字符串...")
        try:
            node_id = self.system.remember("")
            test_cases.append({"case": "empty_string", "result": "ok"})
            print(f"    ✅ 空字符串处理")
        except Exception as e:
            self.bug_tracker.report_bug(
                test_name, f"空字符串失败: {e}", "medium"
            )
            test_cases.append({"case": "empty_string", "result": "failed"})
        
        # 测试2: 超长字符串
        print(f"  2️⃣ 测试超长字符串...")
        try:
            long_label = "X" * 10000
            node_id = self.system.remember(long_label)
            test_cases.append({"case": "long_string", "result": "ok"})
            print(f"    ✅ 超长字符串处理")
        except Exception as e:
            self.bug_tracker.report_bug(
                test_name, f"超长字符串失败: {e}", "medium"
            )
        
        # 测试3: 特殊字符
        print(f"  3️⃣ 测试特殊字符...")
        special_labels = ["测试_😊", "a@#$%^&*", "123_+_<>?"]
        for label in special_labels:
            try:
                self.system.remember(label)
                print(f"    ✅ {label}")
            except Exception as e:
                self.bug_tracker.report_bug(
                    test_name, f"特殊字符失败({label}): {e}", "low"
                )
        
        # 测试4: 大数据量属性
        print(f"  4️⃣ 测试大数据量属性...")
        try:
            big_props = {f"key_{i}": f"value_{i}" for i in range(1000)}
            self.system.remember("大属性节点", properties=big_props)
            test_cases.append({"case": "big_properties", "result": "ok"})
            print(f"    ✅ 大数据量属性")
        except Exception as e:
            self.bug_tracker.report_bug(
                test_name, f"大属性失败: {e}", "medium"
            )
        
        # 测试5: 重复连接
        print(f"  5️⃣ 测试重复连接...")
        try:
            self.system.remember("A")
            self.system.remember("B")
            for i in range(100):
                self.system.connect("A", "B", f"rel_{i}")
            test_cases.append({"case": "duplicate_connections", "result": "ok"})
            print(f"    ✅ 重复连接")
        except Exception as e:
            self.bug_tracker.report_bug(
                test_name, f"重复连接失败: {e}", "medium"
            )
        
        # 测试6: 边界参数
        print(f"  6️⃣ 测试边界参数...")
        try:
            self.system.remember("边界测试")
            self.system.recall("边界测试", k=0)
            self.system.recall("边界测试", k=10000)
            self.system.infer("边界测试", max_depth=100)
            print(f"    ✅ 边界参数")
        except Exception as e:
            self.bug_tracker.report_bug(
                test_name, f"边界参数失败: {e}", "medium"
            )
        
        return {
            "passed": len(self.bug_tracker.bugs) == 0,
            "test_cases": test_cases
        }
    
    def test_memory_stability(self) -> Dict:
        """测试内存稳定性与泄漏"""
        test_name = "内存稳定性"
        print("\n" + "="*80)
        print(f"💾 测试 4: {test_name}")
        print("="*80)
        
        self.system.clear()
        self.memory_detector.record("内存测试开始")
        
        rounds = 20
        operations_per_round = 200
        
        initial_memory = self.memory_detector.get_memory_mb()
        
        for r in range(rounds):
            # 添加数据
            for i in range(operations_per_round):
                self.system.remember(f"内存测试_{r}_{i}")
            
            # 查询
            for i in range(100):
                query = f"内存测试_{random.randint(0, operations_per_round-1)}"
                self.system.recall(query, k=3)
            
            # 部分清理
            if r % 5 == 0:
                self.memory_detector.record(f"第{r}轮结束")
        
        final_memory = self.memory_detector.get_memory_mb()
        self.memory_detector.record("内存测试结束")
        
        memory_growth = final_memory - initial_memory
        
        print(f"\n  📊 内存分析:")
        print(f"    初始: {initial_memory:.2f} MB")
        print(f"    最终: {final_memory:.2f} MB")
        print(f"    增长: {memory_growth:.2f} MB")
        
        has_leak = self.memory_detector.check_leak(initial_memory, final_memory, 100)
        if has_leak:
            self.bug_tracker.report_warning(
                test_name, f"内存增长较高: {memory_growth:.2f} MB"
            )
        
        return {
            "passed": memory_growth < 200,
            "memory_growth": memory_growth,
            "initial_memory": initial_memory,
            "final_memory": final_memory
        }
    
    def test_long_running_stability(self) -> Dict:
        """测试长时间运行稳定性"""
        test_name = "长时间运行稳定性"
        print("\n" + "="*80)
        print(f"⏱️  测试 5: {test_name}")
        print("="*80)
        
        self.system.clear()
        
        duration = 30  # 秒 (演示模式)
        print(f"  📅 运行 {duration} 秒...")
        
        start = time.time()
        operation_count = 0
        error_count = 0
        last_report = start
        
        while time.time() - start < duration:
            try:
                # 混合操作
                op_type = random.choice([
                    "remember", "connect", "recall", "infer", 
                    "semantic", "recommend"
                ])
                
                if op_type == "remember":
                    label = f"长时间_{random.randint(0, 10000)}"
                    self.system.remember(label)
                elif op_type == "connect":
                    source = f"长时间_{random.randint(0, 100)}"
                    target = f"长时间_{random.randint(0, 100)}"
                    try:
                        self.system.connect(source, target)
                    except:
                        pass
                elif op_type == "recall":
                    query = f"长时间_{random.randint(0, 100)}"
                    self.system.recall(query, k=3)
                elif op_type == "infer":
                    query = f"长时间_{random.randint(0, 100)}"
                    self.system.infer(query, max_depth=2)
                elif op_type == "semantic":
                    query = f"长时间_{random.randint(0, 100)}"
                    self.system.semantic_search(query, k=3)
                else:
                    query = f"长时间_{random.randint(0, 100)}"
                    self.system.recommend_connections(query, k=2)
                
                operation_count += 1
                
                # 定期报告
                if time.time() - last_report >= 5:
                    stats = self.system.get_statistics()
                    elapsed = time.time() - start
                    print(f"    ⏱️  {int(elapsed)}s: {operation_count} 操作, "
                          f"{stats['nodes']} 节点, {stats['edges']} 边")
                    last_report = time.time()
                
            except Exception as e:
                error_count += 1
                if error_count <= 3:
                    self.bug_tracker.report_bug(
                        test_name, f"长时间运行错误: {e}", "medium"
                    )
        
        total_time = time.time() - start
        ops_per_second = operation_count / total_time if total_time > 0 else 0
        
        stats = self.system.get_statistics()
        
        print(f"\n  📊 最终结果:")
        print(f"    总操作: {operation_count}")
        print(f"    错误: {error_count}")
        print(f"    平均: {ops_per_second:.0f} ops/s")
        print(f"    最终: {stats['nodes']} 节点, {stats['edges']} 边")
        
        return {
            "passed": error_count == 0,
            "total_operations": operation_count,
            "error_count": error_count,
            "throughput": ops_per_second,
            "elapsed": total_time,
            "final_nodes": stats['nodes'],
            "final_edges": stats['edges']
        }
    
    def test_gnn_and_embeddings(self) -> Dict:
        """测试GNN和嵌入功能"""
        test_name = "GNN与嵌入测试"
        print("\n" + "="*80)
        print(f"🧠 测试 6: {test_name}")
        print("="*80)
        
        self.system.clear()
        
        # 创建测试图
        tech_terms = ["Python", "JavaScript", "机器学习", "深度学习", 
                     "FastAPI", "React", "PyTorch", "TensorFlow"]
        
        for term in tech_terms:
            self.system.remember(term, compute_embedding=True)
        
        self.system.connect("Python", "FastAPI", EdgeType.USES)
        self.system.connect("Python", "PyTorch", EdgeType.USES)
        self.system.connect("Python", "TensorFlow", EdgeType.USES)
        self.system.connect("JavaScript", "React", EdgeType.USES)
        self.system.connect("机器学习", "深度学习", EdgeType.IS_A)
        self.system.connect("深度学习", "PyTorch", EdgeType.RELATED_TO)
        self.system.connect("深度学习", "TensorFlow", EdgeType.RELATED_TO)
        
        # 测试GNN计算
        print(f"  🤖 计算GNN嵌入...")
        try:
            self.system.compute_gnn_embeddings()
            print(f"    ✅ GNN计算成功")
        except Exception as e:
            self.bug_tracker.report_bug(
                test_name, f"GNN计算失败: {e}", "high"
            )
        
        # 测试语义搜索
        print(f"  🔍 语义搜索测试...")
        try:
            results = self.system.semantic_search("Python", k=5)
            print(f"    ✅ 语义搜索: {len(results)} 结果")
        except Exception as e:
            self.bug_tracker.report_bug(
                test_name, f"语义搜索失败: {e}", "high"
            )
        
        # 测试推荐
        print(f"  💡 推荐功能测试...")
        try:
            recommendations = self.system.recommend_connections("Python", k=3)
            print(f"    ✅ 推荐: {len(recommendations)} 结果")
        except Exception as e:
            self.bug_tracker.report_bug(
                test_name, f"推荐失败: {e}", "high"
            )
        
        stats = self.system.get_statistics()
        
        return {
            "passed": len(self.bug_tracker.bugs) == 0,
            "embeddings_count": stats.get("embeddings_count", 0)
        }
    
    def run_all_tests(self) -> Dict:
        """运行所有测试"""
        print("\n" + "="*80)
        print("🚀 知识图谱记忆系统 v7.0 - 真实世界压力测试")
        print("="*80)
        print(f"开始时间: {datetime.now().isoformat()}")
        
        # 运行测试
        self.test_results["large_scale"] = self.test_large_scale_knowledge_graph()
        self.test_results["concurrent"] = self.test_concurrent_stress()
        self.test_results["edge_cases"] = self.test_extreme_edge_cases()
        self.test_results["memory"] = self.test_memory_stability()
        self.test_results["long_running"] = self.test_long_running_stability()
        self.test_results["gnn"] = self.test_gnn_and_embeddings()
        
        # 生成报告
        self.generate_final_report()
        
        return self.test_results
    
    def generate_final_report(self):
        """生成最终报告"""
        print("\n" + "="*80)
        print("📋 压力测试 - 最终报告")
        print("="*80)
        
        summary = self.bug_tracker.get_summary()
        
        print(f"\n📊 总体统计:")
        print(f"  发现Bug: {summary['total_bugs']}")
        print(f"  警告: {summary['total_warnings']}")
        print(f"  性能问题: {summary['performance_issues']}")
        
        if summary['total_bugs'] > 0:
            print(f"\n❌ 发现的Bug:")
            for bug in summary['bugs']:
                print(f"  - [{bug['severity']}] {bug['test']}: {bug['problem']}")
        
        # 保存报告
        report = {
            "summary": summary,
            "test_results": self.test_results,
            "timestamp": datetime.now().isoformat()
        }
        
        report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                   "v7_stress_test_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📝 完整报告已保存: {report_path}")
        
        if summary['total_bugs'] == 0:
            print("\n🎉 没有发现Bug！系统表现完美！")
        else:
            print("\n⚠️  发现问题，需要修复")


# ============================================
# 主函数
# ============================================

def main():
    """主函数"""
    suite = StressTestSuite()
    results = suite.run_all_tests()
    
    print("\n" + "="*80)
    print("🎯 压力测试完成！")
    print("="*80)


if __name__ == "__main__":
    main()
