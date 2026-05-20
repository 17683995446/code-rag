#!/usr/bin/env python3
"""
知识图谱记忆系统 v4.0 - 真实场景模拟
模拟真实世界的复杂使用场景
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import tempfile
import time
import random
from datetime import datetime

from kg_memory.core import MemorySystem, EdgeType


class RealWorldScenarioTester:
    """真实世界场景测试"""

    def __init__(self):
        self.scenarios = []

    def test_knowledge_base_construction(self):
        """场景1：构建知识库"""
        print(f"\n{'='*70}")
        print(f"📚 场景1：构建知识库")
        print(f"{'='*70}")

        temp_dir = tempfile.mkdtemp()
        ms = MemorySystem(temp_dir)
        ms.clear()

        # 知识库内容
        topics = {
            "Python": ["基础语法", "函数", "类", "模块", "异常处理", "文件操作"],
            "JavaScript": ["变量", "函数", "DOM", "异步编程", "ES6+"],
            "Machine Learning": ["监督学习", "无监督学习", "深度学习", "神经网络"],
            "Database": ["SQL", "NoSQL", "索引", "事务", "优化"],
        }

        start_time = time.time()

        # 添加知识
        for topic, concepts in topics.items():
            ms.remember(topic, {"type": "field"})
            for concept in concepts:
                ms.remember(concept, {"type": "concept", "field": topic})
                ms.connect(concept, topic, "belongs_to")

        # 添加关系
        ms.connect("Python", "Machine Learning", "uses")
        ms.connect("JavaScript", "Machine Learning", "uses")
        ms.connect("SQL", "Database", "is_a")
        ms.connect("NoSQL", "Database", "is_a")

        elapsed = time.time() - start_time

        stats = ms.stats()
        print(f"✅ 知识库构建完成")
        print(f"   节点: {stats['nodes']}")
        print(f"   边: {stats['edges']}")
        print(f"   耗时: {elapsed:.3f}s")

        # 测试推理
        print(f"\n🔍 测试知识推理:")
        print(f"   查询 'Python 相关':")
        results = ms.infer("Python", max_depth=2)
        print(f"   找到 {len(results)} 个关联")
        for r in results[:5]:
            print(f"   - {r['source']} -> {r['target']} ({r['relation']})")

        return ms

    def test_code_repository_indexing(self):
        """场景2：代码仓库索引"""
        print(f"\n{'='*70}")
        print(f"💻 场景2：代码仓库索引")
        print(f"{'='*70}")

        temp_dir = tempfile.mkdtemp()
        ms = MemorySystem(temp_dir)
        ms.clear()

        # 模拟代码仓库
        modules = [
            ("auth", ["login", "logout", "register", "password_reset"]),
            ("api", ["users", "products", "orders", "payments"]),
            ("database", ["connection", "queries", "migrations"]),
            ("utils", ["helpers", "validators", "formatters"]),
        ]

        start_time = time.time()

        for module, files in modules:
            ms.remember(module, {"type": "module"})
            for file in files:
                ms.remember(file, {"type": "file", "module": module})
                ms.connect(file, module, "in_module")

        # 添加依赖关系
        ms.connect("api", "auth", "depends_on")
        ms.connect("api", "database", "depends_on")
        ms.connect("database", "utils", "uses")
        ms.connect("payments", "api", "in_module")

        elapsed = time.time() - start_time

        stats = ms.stats()
        print(f"✅ 代码仓库索引完成")
        print(f"   模块: {len(modules)}")
        print(f"   文件: {sum(len(f) for _, f in modules)}")
        print(f"   耗时: {elapsed:.3f}s")

        # 测试依赖分析
        print(f"\n🔍 测试依赖分析:")
        pr = ms.pagerank()
        print(f"   PageRank Top 3:")
        for i, (node, score) in enumerate(list(pr.items())[:3]):
            print(f"   {i+1}. {node}: {score:.4f}")

        return ms

    def test_temporal_knowledge_tracking(self):
        """场景3：时序知识追踪"""
        print(f"\n{'='*70}")
        print(f"📅 场景3：时序知识追踪")
        print(f"{'='*70}")

        temp_dir = tempfile.mkdtemp()
        ms = MemorySystem(temp_dir)
        ms.clear()

        # 模拟项目演进
        versions = [
            ("v1.0", ["基础功能", "用户注册", "登录"]),
            ("v1.1", ["密码重置", "邮箱验证"]),
            ("v2.0", ["API重构", "性能优化"]),
            ("v3.0", ["微服务化", "容器化部署"]),
        ]

        start_time = time.time()

        for version, features in versions:
            ms.remember(version, {"type": "version", "timestamp": str(datetime.now())})
            for feature in features:
                ms.remember(feature, {"type": "feature", "version": version})
                ms.connect(feature, version, "released_in")

        # 版本关系
        ms.connect("v2.0", "v1.0", "evolved_from")
        ms.connect("v3.0", "v2.0", "evolved_from")
        ms.connect("密码重置", "v1.1", "released_in")

        elapsed = time.time() - start_time

        stats = ms.stats()
        print(f"✅ 时序知识追踪完成")
        print(f"   版本: {len(versions)}")
        print(f"   特性: {sum(len(f) for _, f in versions)}")
        print(f"   耗时: {elapsed:.3f}s")

        # 演进路径查询
        print(f"\n🔍 测试版本演进路径:")
        path = ms.shortest_path("v1.0", "v3.0")
        print(f"   v1.0 -> v3.0 路径: {' -> '.join(path)}")

        return ms

    def test_search_and_discovery(self):
        """场景4：搜索与发现"""
        print(f"\n{'='*70}")
        print(f"🔍 场景4：搜索与发现")
        print(f"{'='*70}")

        temp_dir = tempfile.mkdtemp()
        ms = MemorySystem(temp_dir)
        ms.clear()

        # 添加测试数据
        test_data = [
            "Python Programming Language",
            "Python Web Development",
            "Python Data Science",
            "JavaScript Frontend",
            "JavaScript Backend (Node.js)",
            "JavaScript Mobile Apps",
            "Machine Learning Algorithms",
            "Deep Learning Neural Networks",
            "Database SQL Queries",
            "Database NoSQL Storage",
        ]

        for item in test_data:
            ms.remember(item, {"type": "topic"})

        start_time = time.time()

        # 执行搜索
        queries = ["Python", "JavaScript", "Machine", "Database"]
        search_results = {}

        for query in queries:
            results = ms.recall(query, k=5)
            search_results[query] = results

        elapsed = time.time() - start_time

        print(f"✅ 搜索完成")
        print(f"   查询数: {len(queries)}")
        print(f"   耗时: {elapsed:.3f}s")
        print(f"   平均延迟: {elapsed/len(queries)*1000:.2f}ms")

        print(f"\n🔍 搜索结果:")
        for query, results in search_results.items():
            print(f"\n   查询 '{query}':")
            for r in results[:3]:
                print(f"   - {r['label']}")

        # 相似性发现
        print(f"\n🔗 相似性发现:")
        similar = ms.get_similar_nodes("Python Programming Language", top_k=3)
        print(f"   与 'Python Programming Language' 相似:")
        for s in similar:
            print(f"   - {s}")

        return ms

    def test_centrality_analysis(self):
        """场景5：中心性分析"""
        print(f"\n{'='*70}")
        print(f"📊 场景5：中心性分析")
        print(f"{'='*70}")

        temp_dir = tempfile.mkdtemp()
        ms = MemorySystem(temp_dir)
        ms.clear()

        # 创建复杂的图结构
        central_nodes = ["Core System", "Main API"]
        for i in range(20):
            ms.remember(f"Module_{i}")
            # 连接到中心节点
            ms.connect(f"Module_{i}", "Core System", "uses")
            ms.connect("Core System", f"Module_{i}", "provides")

        for i in range(5):
            ms.remember(f"Plugin_{i}")
            ms.connect(f"Plugin_{i}", "Main API", "integrates")

        start_time = time.time()

        # 计算各种中心性
        betweenness = ms.betweenness_centrality()
        degree = ms.degree_centrality()
        closeness = ms.closeness_centrality()
        pagerank = ms.pagerank()

        elapsed = time.time() - start_time

        print(f"✅ 中心性分析完成")
        print(f"   耗时: {elapsed:.3f}s")

        print(f"\n🔍 关键节点识别:")
        print(f"   介数中心性 Top 3:")
        for i, (node, score) in enumerate(list(betweenness.items())[:3]):
            print(f"   {i+1}. {node}: {score:.4f}")

        print(f"\n   度中心性 Top 3:")
        for i, (node, score) in enumerate(list(degree.items())[:3]):
            print(f"   {i+1}. {node}: {score:.4f}")

        print(f"\n   PageRank Top 3:")
        for i, (node, score) in enumerate(list(pagerank.items())[:3]):
            print(f"   {i+1}. {node}: {score:.4f}")

        return ms

    def run_all_scenarios(self):
        """运行所有场景"""
        print("\n" + "="*70)
        print("🚀 知识图谱记忆系统 v4.0 - 真实世界场景模拟")
        print("="*70)

        self.test_knowledge_base_construction()
        self.test_code_repository_indexing()
        self.test_temporal_knowledge_tracking()
        self.test_search_and_discovery()
        self.test_centrality_analysis()

        print("\n" + "="*70)
        print("✅ 所有真实场景测试完成！")
        print("="*70)


if __name__ == "__main__":
    tester = RealWorldScenarioTester()
    tester.run_all_scenarios()
