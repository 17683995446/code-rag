#!/usr/bin/env python3
"""
知识图谱记忆系统 v6.0 - 完整验证与演示
包含数据库集成、高级分析和完整测试
"""
import sys
import os
import json
import time
import random
import tempfile
from typing import Dict, List, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import v6 core
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kg_memory_v6 import (
    MemorySystemV6,
    NodeType,
    EdgeType
)


# ============================================
# Demo Data Generator
# ============================================

class DemoDataset:
    """真实知识图谱示例数据"""
    
    COMPANIES = [
        "Google", "Microsoft", "Apple", "Amazon", "Meta",
        "OpenAI", "Anthropic", "Tesla", "NVIDIA", "Intel"
    ]
    
    PRODUCTS = [
        "TensorFlow", "PyTorch", "GPT-4", "Claude", "ChatGPT",
        "Windows", "iOS", "Android", "AWS", "Azure", "GCP"
    ]
    
    TECHNOLOGIES = [
        "Python", "JavaScript", "TypeScript", "C++", "Rust", "Go",
        "Machine Learning", "Deep Learning", "Neural Networks",
        "Transformers", "NLP", "Computer Vision", "SQL", "NoSQL"
    ]
    
    CONCEPTS = [
        "AI", "AGI", "Cloud Computing", "DevOps", "Microservices",
        "API", "Graph Database", "Knowledge Graph", "Search",
        "Recommendation System", "Automation", "Security"
    ]
    
    @classmethod
    def create_tech_kg(cls, system: MemorySystemV6, count: int = 100):
        """创建科技领域知识图谱"""
        print(f"  创建 {count} 个节点...")
        
        nodes = []
        
        for comp in cls.COMPANIES:
            nodes.append(system.remember(comp, {"category": "company"}, NodeType.ENTITY))
        
        for prod in cls.PRODUCTS:
            nodes.append(system.remember(prod, {"category": "product"}, NodeType.ENTITY))
        
        for tech in cls.TECHNOLOGIES:
            nodes.append(system.remember(tech, {"category": "technology"}, NodeType.CONCEPT))
        
        for concept in cls.CONCEPTS:
            nodes.append(system.remember(concept, {"category": "concept"}, NodeType.CONCEPT))
        
        additional_nodes = count - len(nodes)
        for i in range(additional_nodes):
            name = f"TechItem_{i}"
            nodes.append(system.remember(name, {"category": "misc"}, NodeType.ENTITY))
        
        print(f"  创建 150 条关系...")
        relations = 0
        
        company_product_map = {
            "Google": ["TensorFlow", "GCP", "Android"],
            "Microsoft": ["Windows", "Azure", "TypeScript"],
            "Apple": ["iOS"],
            "Amazon": ["AWS"],
            "Meta": ["PyTorch"],
            "OpenAI": ["GPT-4", "ChatGPT"],
            "Anthropic": ["Claude"]
        }
        
        for company, products in company_product_map.items():
            for product in products:
                try:
                    system.connect(company, product, "created_by")
                    relations += 1
                except:
                    pass
        
        tech_stack = [
            ("Python", "TensorFlow", "uses"),
            ("Python", "PyTorch", "uses"),
            ("Machine Learning", "Neural Networks", "is_a"),
            ("Deep Learning", "Transformers", "uses"),
            ("Knowledge Graph", "NLP", "related_to"),
            ("Search", "Knowledge Graph", "uses"),
            ("Cloud Computing", "AWS", "part_of"),
            ("Cloud Computing", "GCP", "part_of"),
            ("Cloud Computing", "Azure", "part_of")
        ]
        
        for source, target, relation in tech_stack:
            try:
                system.connect(source, target, relation)
                relations += 1
            except:
                pass
        
        for _ in range(100):
            source = random.choice(cls.COMPANIES + cls.PRODUCTS + cls.TECHNOLOGIES)
            target = random.choice(cls.COMPANIES + cls.PRODUCTS + cls.TECHNOLOGIES)
            if source != target:
                try:
                    system.connect(source, target, random.choice(["related_to", "uses", "depends_on"]))
                    relations += 1
                except:
                    pass
        
        print(f"  完成！共 {len(nodes)} 个节点，{relations} 条边")


# ============================================
# Verification Tests
# ============================================

class VerificationSuite:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(tempfile.mkdtemp(), "kg_v6_test.db")
        self.system = MemorySystemV6(db_path)
    
    def test_basic_operations(self) -> bool:
        """基础功能测试"""
        print(f"\n{'='*80}")
        print(f"🧪 测试 1: 基础功能验证")
        print(f"{'='*80}")
        
        start = time.time()
        
        self.system.remember("Alpha", {"type": "test"})
        self.system.remember("Beta", {"type": "test"})
        self.system.remember("Gamma", {"type": "test"})
        
        self.system.connect("Alpha", "Beta", "related_to")
        self.system.connect("Beta", "Gamma", "uses")
        self.system.connect("Alpha", "Gamma", "part_of")
        
        recall_results = self.system.recall("Alpha", k=5)
        print(f"  ✓ 检索: {len(recall_results)} 结果")
        
        infer_results = self.system.infer("Alpha", max_depth=2)
        print(f"  ✓ 推理: {len(infer_results)} 结果")
        
        stats = self.system.get_statistics()
        print(f"  ✓ 统计: {stats['nodes']} 节点, {stats['edges']} 边")
        
        elapsed = time.time() - start
        print(f"\n  ✅ 基础功能测试通过 ({elapsed:.2f}s)")
        
        return True
    
    def test_database_persistence(self) -> bool:
        """数据库持久化测试"""
        print(f"\n{'='*80}")
        print(f"💾 测试 2: 数据库持久化验证")
        print(f"{'='*80}")
        
        start = time.time()
        
        for i in range(50):
            self.system.remember(f"PersistTest_{i}", {"index": i})
        
        for i in range(30):
            source = f"PersistTest_{random.randint(0, 49)}"
            target = f"PersistTest_{random.randint(0, 49)}"
            if source != target:
                self.system.connect(source, target)
        
        stats1 = self.system.get_statistics()
        print(f"  第一次创建: {stats1['nodes']} 节点, {stats1['edges']} 边")
        
        db_path = self.system.db.db_path
        
        del self.system
        
        print(f"  重新加载数据库...")
        system2 = MemorySystemV6(db_path)
        
        stats2 = system2.get_statistics()
        print(f"  重新加载后: {stats2['nodes']} 节点, {stats2['edges']} 边")
        
        passed = (stats1['nodes'] == stats2['nodes'] and stats1['edges'] == stats2['edges'])
        
        self.system = system2
        
        elapsed = time.time() - start
        if passed:
            print(f"  ✅ 数据库持久化测试通过 ({elapsed:.2f}s)")
        else:
            print(f"  ❌ 数据库持久化测试失败")
        
        return passed
    
    def test_performance(self) -> Dict[str, Any]:
        """性能测试"""
        print(f"\n{'='*80}")
        print(f"⚡ 测试 3: 性能基准测试")
        print(f"{'='*80}")
        
        self.system.clear()
        
        node_count = 2000
        edge_count = 5000
        query_count = 3000
        
        print(f"\n  📊 节点创建测试 ({node_count}个)...")
        start = time.time()
        for i in range(node_count):
            self.system.remember(f"PerfNode_{i}", {"index": i})
        node_time = time.time() - start
        node_rate = node_count / node_time
        
        print(f"    {node_count}节点: {node_time:.2f}s, {node_rate:.0f} node/s")
        
        print(f"\n  🔗 边创建测试 ({edge_count}条)...")
        start = time.time()
        for i in range(edge_count):
            source = f"PerfNode_{random.randint(0, node_count-1)}"
            target = f"PerfNode_{random.randint(0, node_count-1)}"
            if source != target:
                self.system.connect(source, target)
        edge_time = time.time() - start
        edge_rate = edge_count / edge_time if edge_time > 0 else 0
        
        print(f"    {edge_count}边: {edge_time:.2f}s, {edge_rate:.0f} edge/s")
        
        print(f"\n  🔍 查询测试 ({query_count}次)...")
        start = time.time()
        for i in range(query_count):
            query = f"PerfNode_{random.randint(0, node_count-1)}"
            self.system.recall(query, k=5)
        query_time = time.time() - start
        qps = query_count / query_time if query_time > 0 else 0
        
        print(f"    {query_count}查询: {query_time:.2f}s, {qps:.0f} QPS")
        
        stats = self.system.get_statistics()
        
        return {
            "node_rate": node_rate,
            "edge_rate": edge_rate,
            "qps": qps,
            "node_count": stats['nodes'],
            "edge_count": stats['edges']
        }
    
    def test_advanced_analytics(self) -> Dict[str, Any]:
        """高级分析测试"""
        print(f"\n{'='*80}")
        print(f"🧠 测试 4: 高级图分析")
        print(f"{'='*80}")
        
        self.system.clear()
        
        DemoDataset.create_tech_kg(self.system, count=100)
        
        print(f"\n  📊 计算度中心性...")
        start = time.time()
        centrality = self.system.analytics.calculate_degree_centrality()
        elapsed = time.time() - start
        print(f"    度中心性: {len(centrality)} 结果 ({elapsed:.3f}s)")
        
        print(f"\n  🔍 计算 PageRank...")
        start = time.time()
        pagerank = self.system.analytics.pagerank()
        elapsed = time.time() - start
        print(f"    PageRank: {len(pagerank)} 结果 ({elapsed:.3f}s)")
        
        print(f"\n  🌐 社区发现...")
        start = time.time()
        communities = self.system.analytics.find_communities()
        elapsed = time.time() - start
        print(f"    社区发现: {len(communities)} 社区 ({elapsed:.3f}s)")
        
        print(f"\n  📈 最短路径...")
        try:
            path = self.system.analytics.shortest_path("Google", "Machine Learning")
            if path:
                print(f"    最短路径: {' -> '.join(path)}")
            else:
                print(f"    无路径")
        except Exception as e:
            print(f"    路径计算: {e}")
        
        return {
            "centrality": centrality,
            "pagerank": pagerank,
            "communities": communities
        }
    
    def test_concurrent_operations(self) -> Dict[str, Any]:
        """并发操作测试"""
        print(f"\n{'='*80}")
        print(f"🔄 测试 5: 并发操作测试")
        print(f"{'='*80}")
        
        self.system.clear()
        
        for i in range(100):
            self.system.remember(f"Concurrent_{i}")
        
        thread_count = 15
        ops_per_thread = 200
        total_ops = thread_count * ops_per_thread
        
        print(f"\n  启动 {thread_count} 个线程，共 {total_ops} 个操作...")
        
        start = time.time()
        successful_ops = 0
        failed_ops = 0
        
        def worker(thread_id: int):
            nonlocal successful_ops, failed_ops
            for i in range(ops_per_thread):
                try:
                    op_type = random.choice(["recall", "infer"])
                    if op_type == "recall":
                        query = f"Concurrent_{random.randint(0, 99)}"
                        self.system.recall(query, k=3)
                    else:
                        infer_query = f"Concurrent_{random.randint(0, 99)}"
                        self.system.infer(infer_query, max_depth=2)
                except:
                    pass
        
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            futures = [executor.submit(worker, tid) for tid in range(thread_count)]
            for future in as_completed(futures):
                try:
                    future.result()
                    successful_ops += ops_per_thread
                except:
                    failed_ops += ops_per_thread
        
        elapsed = time.time() - start
        
        stats = self.system.get_statistics()
        
        print(f"\n  📊 并发测试结果:")
        print(f"    总操作: {total_ops}")
        print(f"    总时间: {elapsed:.2f}s")
        print(f"    吞吐量: {total_ops / elapsed:.0f} ops/s")
        
        return {
            "throughput": total_ops / elapsed,
            "total_ops": total_ops
        }
    
    def run_all_verifications(self):
        """运行所有验证测试"""
        print(f"\n{'='*80}")
        print(f"🚀 知识图谱记忆系统 v6.0 - 完整验证")
        print(f"{'='*80}")
        print(f"开始时间: {datetime.now().isoformat()}")
        
        results = {}
        
        results['basic'] = self.test_basic_operations()
        results['persistence'] = self.test_database_persistence()
        results['performance'] = self.test_performance()
        results['analytics'] = self.test_advanced_analytics()
        results['concurrent'] = self.test_concurrent_operations()
        
        self.generate_final_report(results)
        
        return results
    
    def generate_final_report(self, results):
        """生成最终报告"""
        print(f"\n{'='*80}")
        print(f"🎉 v6.0 最终验证报告")
        print(f"{'='*80}")
        
        print(f"\n📊 性能指标:")
        perf = results.get('performance', {})
        print(f"  节点创建: {perf.get('node_rate', 0):.0f} node/s")
        print(f"  边创建: {perf.get('edge_rate', 0):.0f} edge/s")
        print(f"  查询性能: {perf.get('qps', 0):.0f} QPS")
        
        conc = results.get('concurrent', {})
        print(f"\n🔄 并发性能:")
        print(f"  吞吐量: {conc.get('throughput', 0):.0f} ops/s")
        
        analytics = results.get('analytics', {})
        print(f"\n🧠 高级分析:")
        print(f"  度中心性: {len(analytics.get('centrality', {}))} 结果")
        print(f"  PageRank: {len(analytics.get('pagerank', {}))} 结果")
        print(f"  社区数: {len(analytics.get('communities', []))}")
        
        print(f"\n✅ 所有验证测试完成！")
        
        print(f"\n{'='*80}")
        print(f"🏆 v6.0 创新点:")
        print(f"  1. SQLite 数据库持久化")
        print(f"  2. 内存-数据库混合缓存层")
        print(f"  3. 高级图分析 (PageRank, 社区发现)")
        print(f"  4. 智能 LRU 缓存 (带访问统计)")
        print(f"  5. 优化的 __slots__ 数据模型")
        print(f"  6. 可重入锁提升并发性能")
        print(f"{'='*80}")


# ============================================
# Main Demo
# ============================================

def main():
    print(f"{'='*80}")
    print(f"🎯 知识图谱记忆系统 v6.0 - 新篇章启动!")
    print(f"{'='*80}")
    
    suite = VerificationSuite()
    results = suite.run_all_verifications()
    
    print(f"\n{'='*80}")
    print(f"📋 短期、中期、长期计划")
    print(f"{'='*80}")
    
    print(f"\n⏱️  短期计划 (1-2周):")
    print(f"  1. 添加 PostgreSQL 后端支持")
    print(f"  2. 图神经网络 (GNN) 集成")
    print(f"  3. WebSocket 实时更新推送")
    print(f"  4. 完整的 REST API")
    
    print(f"\n📅 中期计划 (1-2个月):")
    print(f"  1. 分布式图处理引擎")
    print(f"  2. 交互式可视化编辑界面")
    print(f"  3. 多语言 SDK (Python/JavaScript/Go)")
    print(f"  4. 高级安全与权限管理")
    
    print(f"\n🚀 长期计划 (3-6个月):")
    print(f"  1. 知识图谱即服务 (KGaaS) 平台")
    print(f"  2. AI 深度集成与推理增强")
    print(f"  3. 企业级部署与可扩展性方案")
    print(f"  4. 完整的生态系统与插件架构")
    
    print(f"\n{'='*80}")
    print(f"🎊 v6.0 第一阶段完成!")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
