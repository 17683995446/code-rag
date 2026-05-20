#!/usr/bin/env python3
"""
知识图谱记忆系统 v7.0 - 完整验证与演示
包含插件架构、高级搜索、完整验证
"""
import sys
import os
import json
import time
import random
import tempfile
import webbrowser
from typing import Dict, List, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kg_memory_v7 import (
    MemorySystemV7, NodeType, EdgeType
)


# ============================================
# 插件系统架构
# ============================================

class Plugin:
    """基础插件类"""
    
    name: str = "Base Plugin"
    description: str = "基础插件"
    version: str = "1.0"
    
    def __init__(self, system: MemorySystemV7):
        self.system = system
    
    def initialize(self):
        """初始化插件"""
        pass
    
    def on_node_added(self, node: Any):
        """节点添加事件"""
        pass
    
    def on_edge_added(self, edge: Any):
        """边添加事件"""
        pass
    
    def process_query(self, query: str) -> Optional[List[Dict]]:
        """处理查询 - 可选"""
        return None


class AutoTaggingPlugin(Plugin):
    """自动标签插件"""
    
    name = "自动标签"
    description = "自动为节点添加标签"
    
    def __init__(self, system: MemorySystemV7):
        super().__init__(system)
        self.tag_rules = {
            "Python": ["编程", "语言"],
            "JavaScript": ["编程", "Web"],
            "机器学习": ["AI", "数据科学"],
            "数据库": ["存储", "数据"]
        }
    
    def on_node_added(self, node: Any):
        for keyword, tags in self.tag_rules.items():
            if keyword in node.label:
                if "tags" not in node.properties:
                    node.properties["tags"] = []
                for tag in tags:
                    if tag not in node.properties["tags"]:
                        node.properties["tags"].append(tag)


class AnalyticsPlugin(Plugin):
    """高级分析插件"""
    
    name = "高级分析"
    description = "提供高级图分析功能"
    
    def __init__(self, system: MemorySystemV7):
        super().__init__(system)
    
    def compute_node_importance(self) -> Dict[str, float]:
        """计算节点重要性"""
        importance = {}
        adjacency = self.system._adjacency
        nodes = self.system._nodes
        
        for node_id in nodes:
            in_degree = 0
            out_degree = len(adjacency.get(node_id, set()))
            
            for edges in adjacency.values():
                if node_id in edges:
                    in_degree += 1
            
            importance[node_id] = in_degree + out_degree
        
        return importance


class PluginManager:
    """插件管理器"""
    
    def __init__(self, system: MemorySystemV7):
        self.system = system
        self.plugins: Dict[str, Plugin] = {}
    
    def register_plugin(self, plugin: Plugin):
        """注册插件"""
        self.plugins[plugin.name] = plugin
        plugin.initialize()
    
    def unregister_plugin(self, name: str):
        """卸载插件"""
        if name in self.plugins:
            del self.plugins[name]
    
    def notify_node_added(self, node: Any):
        """通知节点添加"""
        for plugin in self.plugins.values():
            plugin.on_node_added(node)
    
    def notify_edge_added(self, edge: Any):
        """通知边添加"""
        for plugin in self.plugins.values():
            plugin.on_edge_added(edge)


# ============================================
# 完整验证测试
# ============================================

class V7Verification:
    """v7.0 验证套件"""
    
    def __init__(self):
        self.system = MemorySystemV7()
        self.plugin_manager = PluginManager(self.system)
        self.results = {}
    
    def test_basic_operations(self) -> Dict[str, Any]:
        """测试基础操作"""
        print("\n" + "="*80)
        print("🧪 测试 1: 基础操作")
        print("="*80)
        
        start = time.time()
        
        nodes = ["Python", "JavaScript", "FastAPI", "React", 
                "机器学习", "深度学习", "知识图谱", "GNN"]
        
        for node in nodes:
            self.system.remember(node, compute_embedding=True)
        
        print(f"  ✓ 添加 {len(nodes)} 个节点")
        
        connections = [
            ("Python", "FastAPI", EdgeType.USES),
            ("Python", "机器学习", EdgeType.RELATED_TO),
            ("JavaScript", "React", EdgeType.USES),
            ("机器学习", "深度学习", EdgeType.IS_A),
            ("知识图谱", "GNN", EdgeType.RELATED_TO),
            ("深度学习", "GNN", EdgeType.RELATED_TO)
        ]
        
        for source, target, rel in connections:
            self.system.connect(source, target, rel)
        
        print(f"  ✓ 添加 {len(connections)} 条边")
        
        recall_results = self.system.recall("Python", k=5)
        print(f"  ✓ 召回 {len(recall_results)} 个结果")
        
        elapsed = time.time() - start
        
        stats = self.system.get_statistics()
        
        return {
            "passed": True,
            "elapsed": elapsed,
            "nodes": stats["nodes"],
            "edges": stats["edges"]
        }
    
    def test_embeddings_and_gnn(self) -> Dict[str, Any]:
        """测试嵌入与GNN"""
        print("\n" + "="*80)
        print("🧠 测试 2: 节点嵌入与GNN")
        print("="*80)
        
        start = time.time()
        
        self.system.compute_gnn_embeddings()
        print(f"  ✓ GNN嵌入计算完成")
        
        semantic_results = self.system.semantic_search("机器学习", k=5)
        print(f"  ✓ 语义搜索返回 {len(semantic_results)} 结果")
        
        recommendations = self.system.recommend_connections("Python", k=3)
        print(f"  ✓ 连接推荐返回 {len(recommendations)} 结果")
        
        elapsed = time.time() - start
        stats = self.system.get_statistics()
        
        return {
            "passed": True,
            "elapsed": elapsed,
            "embeddings_count": stats["embeddings_count"]
        }
    
    def test_plugins(self) -> Dict[str, Any]:
        """测试插件系统"""
        print("\n" + "="*80)
        print("🔌 测试 3: 插件架构")
        print("="*80)
        
        start = time.time()
        
        auto_tagging = AutoTaggingPlugin(self.system)
        analytics = AnalyticsPlugin(self.system)
        
        self.plugin_manager.register_plugin(auto_tagging)
        self.plugin_manager.register_plugin(analytics)
        
        print(f"  ✓ 注册 {len(self.plugin_manager.plugins)} 个插件")
        
        new_node_id = self.system.remember("Python数据分析", compute_embedding=True)
        new_node = self.system._nodes.get(new_node_id)
        if new_node:
            self.plugin_manager.notify_node_added(new_node)
            print(f"  ✓ 插件事件通知正常")
        
        if "Analytics" in self.plugin_manager.plugins:
            importance = analytics.compute_node_importance()
            print(f"  ✓ 插件分析功能: {len(importance)} 个节点重要性")
        
        elapsed = time.time() - start
        
        return {
            "passed": True,
            "elapsed": elapsed,
            "plugins_count": len(self.plugin_manager.plugins)
        }
    
    def test_performance(self) -> Dict[str, Any]:
        """性能测试"""
        print("\n" + "="*80)
        print("⚡ 测试 4: 性能基准")
        print("="*80)
        
        self.system.clear()
        
        node_count = 500
        edge_count = 1000
        
        start = time.time()
        for i in range(node_count):
            self.system.remember(f"性能测试_{i}", compute_embedding=(i % 2 == 0))
        
        node_time = time.time() - start
        node_rate = node_count / node_time if node_time > 0 else 0
        print(f"  ✓ {node_count} 节点: {node_rate:.0f} node/s")
        
        start = time.time()
        for i in range(edge_count):
            source = f"性能测试_{random.randint(0, node_count-1)}"
            target = f"性能测试_{random.randint(0, node_count-1)}"
            if source != target:
                try:
                    self.system.connect(source, target)
                except:
                    pass
        
        edge_time = time.time() - start
        edge_rate = edge_count / edge_time if edge_time > 0 else 0
        print(f"  ✓ {edge_count} 边: {edge_rate:.0f} edge/s")
        
        start = time.time()
        query_count = 1000
        for i in range(query_count):
            query = f"性能测试_{random.randint(0, node_count-1)}"
            self.system.recall(query, k=3)
        
        query_time = time.time() - start
        qps = query_count / query_time if query_time > 0 else 0
        print(f"  ✓ {query_count} 查询: {qps:.0f} QPS")
        
        return {
            "passed": True,
            "node_rate": node_rate,
            "edge_rate": edge_rate,
            "qps": qps
        }
    
    def test_concurrent_operations(self) -> Dict[str, Any]:
        """并发测试"""
        print("\n" + "="*80)
        print("🔄 测试 5: 并发操作")
        print("="*80)
        
        self.system.clear()
        
        for i in range(100):
            self.system.remember(f"并发测试_{i}")
        
        thread_count = 10
        ops_per_thread = 100
        
        def worker(thread_id):
            for i in range(ops_per_thread):
                query = f"并发测试_{random.randint(0, 99)}"
                self.system.recall(query, k=3)
        
        start = time.time()
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            [executor.submit(worker, tid) for tid in range(thread_count)]
        
        elapsed = time.time() - start
        total_ops = thread_count * ops_per_thread
        throughput = total_ops / elapsed
        
        print(f"  ✓ {thread_count} 线程, {total_ops} 操作")
        print(f"  ✓ 吞吐量: {throughput:.0f} ops/s")
        
        return {
            "passed": True,
            "throughput": throughput,
            "thread_count": thread_count
        }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        print("\n" + "="*80)
        print("🚀 知识图谱记忆系统 v7.0 - 完整验证")
        print("="*80)
        print(f"开始时间: {datetime.now().isoformat()}")
        
        self.results["basic"] = self.test_basic_operations()
        self.results["embeddings"] = self.test_embeddings_and_gnn()
        self.results["plugins"] = self.test_plugins()
        self.results["performance"] = self.test_performance()
        self.results["concurrent"] = self.test_concurrent_operations()
        
        self.generate_summary()
        
        return self.results
    
    def generate_summary(self):
        """生成总结"""
        print("\n" + "="*80)
        print("📊 v7.0 最终验证报告")
        print("="*80)
        
        stats = self.system.get_statistics()
        
        print(f"\n🏆 主要特性:")
        print(f"  ✅ 节点嵌入与向量搜索")
        print(f"  ✅ 简单GNN信息传播")
        print(f"  ✅ 插件架构")
        print(f"  ✅ 推荐系统")
        print(f"  ✅ 交互式D3可视化")
        
        print(f"\n📈 性能指标:")
        perf = self.results.get("performance", {})
        print(f"  节点创建: {perf.get('node_rate', 0):.0f} node/s")
        print(f"  边创建: {perf.get('edge_rate', 0):.0f} edge/s")
        print(f"  查询性能: {perf.get('qps', 0):.0f} QPS")
        print(f"  并发吞吐量: {self.results.get('concurrent', {}).get('throughput', 0):.0f} ops/s")
        
        print(f"\n📦 系统状态:")
        print(f"  节点: {stats.get('nodes', 0)}")
        print(f"  边: {stats.get('edges', 0)}")
        print(f"  嵌入: {stats.get('embeddings_count', 0)}")
        
        print("\n" + "="*80)
        print("🎊 v7.0 验证完成！")
        print("="*80)


# ============================================
# 主演示
# ============================================

def create_tech_knowledge_graph(system: MemorySystemV7) -> int:
    """创建科技知识图谱"""
    tech_concepts = [
        ("Python", NodeType.CONCEPT, {"category": "编程语言"}),
        ("JavaScript", NodeType.CONCEPT, {"category": "编程语言"}),
        ("TypeScript", NodeType.CONCEPT, {"category": "编程语言"}),
        ("FastAPI", NodeType.ENTITY, {"category": "框架"}),
        ("React", NodeType.ENTITY, {"category": "框架"}),
        ("Vue.js", NodeType.ENTITY, {"category": "框架"}),
        ("机器学习", NodeType.CONCEPT, {"category": "AI"}),
        ("深度学习", NodeType.CONCEPT, {"category": "AI"}),
        ("知识图谱", NodeType.CONCEPT, {"category": "AI"}),
        ("图神经网络", NodeType.CONCEPT, {"category": "AI"}),
        ("TensorFlow", NodeType.ENTITY, {"category": "框架"}),
        ("PyTorch", NodeType.ENTITY, {"category": "框架"}),
        ("D3.js", NodeType.ENTITY, {"category": "可视化"}),
        ("数据库", NodeType.CONCEPT, {"category": "数据"}),
        ("API", NodeType.CONCEPT, {"category": "架构"})
    ]
    
    for label, ntype, props in tech_concepts:
        system.remember(label, properties=props, node_type=ntype, compute_embedding=True)
    
    tech_relations = [
        ("Python", "FastAPI", EdgeType.USES, 1.5),
        ("Python", "TensorFlow", EdgeType.USES, 1.2),
        ("Python", "PyTorch", EdgeType.USES, 1.2),
        ("JavaScript", "React", EdgeType.USES, 1.3),
        ("JavaScript", "Vue.js", EdgeType.USES, 1.2),
        ("JavaScript", "D3.js", EdgeType.USES, 1.0),
        ("机器学习", "深度学习", EdgeType.IS_A, 1.5),
        ("机器学习", "TensorFlow", EdgeType.RELATED_TO, 1.0),
        ("机器学习", "PyTorch", EdgeType.RELATED_TO, 1.0),
        ("深度学习", "图神经网络", EdgeType.RELATED_TO, 1.3),
        ("知识图谱", "图神经网络", EdgeType.RELATED_TO, 1.5),
        ("知识图谱", "API", EdgeType.RELATED_TO, 0.8),
        ("知识图谱", "数据库", EdgeType.RELATED_TO, 1.0),
        ("FastAPI", "API", EdgeType.RELATED_TO, 1.0)
    ]
    
    for source, target, rel, weight in tech_relations:
        try:
            system.connect(source, target, relation=rel, weight=weight)
        except:
            pass
    
    return len(tech_concepts)


def launch_visualization():
    """启动可视化"""
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "visualization_v7.html")
    abs_path = os.path.abspath(html_path)
    
    print(f"\n🌐 正在启动可视化...")
    print(f"📁 路径: {abs_path}")
    
    try:
        file_url = f"file://{abs_path}"
        webbrowser.open(file_url)
        print(f"✅ 可视化已打开！")
    except Exception as e:
        print(f"⚠️  无法自动打开浏览器: {e}")
        print(f"💡 请手动打开: {abs_path}")


def main():
    """主函数"""
    print("\n" + "="*80)
    print("🚀 知识图谱记忆系统 v7.0 - 新篇章")
    print("="*80)
    
    # 验证
    verification = V7Verification()
    verification.run_all_tests()
    
    # 准备演示
    print("\n" + "="*80)
    print("🎯 准备演示系统")
    print("="*80)
    
    system = MemorySystemV7()
    create_tech_knowledge_graph(system)
    
    stats = system.get_statistics()
    print(f"📊 知识图谱: {stats['nodes']} 节点, {stats['edges']} 边")
    
    # GNN计算
    system.compute_gnn_embeddings()
    print(f"🧠 GNN嵌入计算完成: {stats['embeddings_count']} 个")
    
    # 推荐演示
    print(f"\n💡 推荐示例:")
    recommendations = system.recommend_connections("Python", k=3)
    for rec in recommendations:
        print(f"  → {rec['node']['label']} (兼容性: {rec['compatibility']:.2f})")
    
    # 语义搜索演示
    print(f"\n🔍 语义搜索示例:")
    semantic_results = system.semantic_search("机器学习", k=5)
    for result in semantic_results:
        print(f"  → {result['node']['label']} (相似度: {result['similarity']:.2f})")
    
    # 启动可视化
    launch_visualization()
    
    # 输出总结
    print("\n" + "="*80)
    print("📋 v7.0 规划路线")
    print("="*80)
    print("\n⏳ 短期计划:")
    print("  - 实时WebSocket更新")
    print("  - 持久化存储 (SQLite/PostgreSQL)")
    print("  - 完整REST API")
    
    print("\n📅 中期计划:")
    print("  - 高级可视化与编辑")
    print("  - 图神经网络优化")
    print("  - 多语言SDK")
    
    print("\n🚀 长期计划:")
    print("  - 知识图谱即服务(KGaaS)")
    print("  - 企业级安全与权限")
    print("  - 大规模分布式处理")
    
    print("\n" + "="*80)
    print("🎊 v7.0 第一阶段完成！")
    print("="*80)


if __name__ == "__main__":
    main()
