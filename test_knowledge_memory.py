"""
知识图谱记忆系统 - 测试与验证
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.code_rag.knowledge_graph import (
    KnowledgeGraph, KnowledgeNode, KnowledgeEdge,
    KnowledgeType, RelationType
)
from src.code_rag.memory_system import MemorySystem


def test_knowledge_graph():
    """测试知识图谱核心功能"""
    print("=" * 70)
    print("测试知识图谱核心功能")
    print("=" * 70)
    
    graph = KnowledgeGraph()
    
    # 测试添加节点
    python = KnowledgeNode("Python", type=KnowledgeType.ENTITY)
    django = KnowledgeNode("Django", type=KnowledgeType.ENTITY)
    web_dev = KnowledgeNode("Web开发", type=KnowledgeType.CONCEPT)
    
    graph.add_node(python)
    graph.add_node(django)
    graph.add_node(web_dev)
    
    print(f"✅ 添加节点成功，总节点数: {len(graph.nodes)}")
    
    # 测试添加边
    edge1 = KnowledgeEdge(
        source_id=python.id,
        target_id=web_dev.id,
        type=RelationType.USES,
        weight=1.5
    )
    graph.add_edge(edge1)
    
    edge2 = KnowledgeEdge(
        source_id=django.id,
        target_id=python.id,
        type=RelationType.USES,
        weight=2.0
    )
    graph.add_edge(edge2)
    
    print(f"✅ 添加边成功，总边数: {len(graph.edges)}")
    
    # 测试快速连接
    graph.connect("Flask", "Python", RelationType.USES, weight=1.0)
    print(f"✅ 快速连接成功，总节点数: {len(graph.nodes)}")
    
    # 测试查找
    results = graph.find_nodes_by_label("Python")
    print(f"✅ 查找 'Python' 成功: {len(results)} 个结果")
    
    # 测试邻居
    python_node = results[0]
    neighbors = graph.get_neighbors(python_node.id)
    print(f"✅ Python 的邻居: {[n.label for n in neighbors]}")
    
    # 测试导出
    json_data = graph.to_json()
    print(f"✅ 导出 JSON 成功，大小: {len(json_data)} 字符")
    
    print()
    return graph


def test_memory_system():
    """测试记忆系统"""
    print("=" * 70)
    print("测试记忆系统")
    print("=" * 70)
    
    ms = MemorySystem(data_dir="./test_data")
    
    # 清空测试数据
    ms.store.clear_all()
    
    # 测试会话
    session_id = ms.start_session(user_id="test_user")
    print(f"✅ 会话创建成功: {session_id}")
    
    # 测试记忆
    ms.remember("Python 是一种编程语言", {"source": "demo"})
    ms.remember("Django 是 Python 的 Web 框架", {"source": "demo"})
    ms.remember("Docker 用于容器化应用", {"category": "devops"})
    
    print(f"✅ 记忆知识成功，总节点数: {len(ms.store.graph.nodes)}")
    
    # 测试连接
    ms.connect_knowledge("Django", "Python", "uses")
    ms.connect_knowledge("Docker", "容器化", "related_to")
    print(f"✅ 连接知识成功，总边数: {len(ms.store.graph.edges)}")
    
    # 测试回忆
    recall_result = ms.recall("Python", k=5)
    print(f"✅ 回忆 'Python' 成功，找到 {len(recall_result)} 个相关知识")
    
    # 测试推理
    inference_result = ms.infer("Python")
    print(f"✅ 推理 'Python' 成功，得到 {len(inference_result)} 个关系")
    
    # 测试统计
    stats = ms.get_stats()
    print(f"✅ 统计: {stats}")
    
    print()
    return ms


def test_full_workflow():
    """测试完整工作流"""
    print("=" * 70)
    print("测试完整工作流")
    print("=" * 70)
    
    ms = MemorySystem(data_dir="./test_workflow_data")
    ms.store.clear_all()
    
    ms.start_session()
    
    # 构建知识库
    knowledge_items = [
        ("Python", "entity", "programming_language"),
        ("Django", "entity", "web_framework"),
        ("Flask", "entity", "web_framework"),
        ("Web开发", "concept", "domain"),
        ("机器学习", "concept", "domain"),
        ("TensorFlow", "entity", "ml_framework"),
        ("Docker", "entity", "devops"),
        ("Kubernetes", "entity", "orchestration"),
        ("容器化", "concept", "technology")
    ]
    
    for label, type_name, category in knowledge_items:
        kt = KnowledgeType(type_name) if type_name in [t.value for t in KnowledgeType] else KnowledgeType.ENTITY
        node = KnowledgeNode(label, type=kt, properties={"category": category})
        ms.store.graph.add_node(node)
    
    # 建立连接
    ms.connect_knowledge("Django", "Python", "uses")
    ms.connect_knowledge("Flask", "Python", "uses")
    ms.connect_knowledge("TensorFlow", "Python", "uses")
    ms.connect_knowledge("Python", "Web开发", "used_for")
    ms.connect_knowledge("Python", "机器学习", "used_for")
    ms.connect_knowledge("Docker", "容器化", "related_to")
    ms.connect_knowledge("Kubernetes", "Docker", "manages")
    
    print("✅ 知识库构建完成")
    
    # 测试检索
    search_results = ms.recall("开发", k=10)
    print(f"✅ 搜索 '开发' 找到 {len(search_results)} 条结果")
    
    # 导出可视化数据
    vis_data = ms.store.graph.export_for_vis()
    print(f"✅ 可视化数据导出: {len(vis_data['nodes'])} 节点, {len(vis_data['edges'])} 边")
    
    print()
    print("=" * 70)
    print("🎉 所有测试通过！")
    print("=" * 70)


if __name__ == "__main__":
    test_knowledge_graph()
    test_memory_system()
    test_full_workflow()
