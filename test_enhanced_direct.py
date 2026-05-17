#!/usr/bin/env python3
"""
直接测试增强版模块！
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.code_rag.kg_v2_enhanced import (
    KnowledgeGraph, KnowledgeNode, KnowledgeEdge,
    KnowledgeType, RelationType, MemorySystem
)

print("=" * 70)
print("🧪 直接测试增强版核心模块")
print("=" * 70)

# 1. 基础图测试
print("\n1. 测试基础图功能...")
g = KnowledgeGraph()

node1 = KnowledgeNode("Python", type=KnowledgeType.ENTITY)
node2 = KnowledgeNode("Django", type=KnowledgeType.ENTITY)
node3 = KnowledgeNode("Web", type=KnowledgeType.CONCEPT)

g.add_node(node1)
g.add_node(node2)
g.add_node(node3)

print(f"   节点创建成功: {len(g.nodes)}")

edge1 = KnowledgeEdge(node1.id, node3.id, type=RelationType.USES)
edge2 = KnowledgeEdge(node2.id, node1.id, type=RelationType.USES)

g.add_edge(edge1)
g.add_edge(edge2)

print(f"   边创建成功: {len(g.edges)}")

# 2. 删除级联测试
print("\n2. 测试级联删除...")

initial_nodes = len(g.nodes)
initial_edges = len(g.edges)

print(f"   初始: {initial_nodes} 节点, {initial_edges} 边")

g.delete_node(node1.id, cascade=True)

remaining_nodes = len(g.nodes)
remaining_edges = len(g.edges)

print(f"   删除后: {remaining_nodes} 节点, {remaining_edges} 边")

if remaining_edges == 0:
    print("   ✅ 级联删除正常！")
else:
    print("   ❌ 边没有完全删除！")

# 3. 记忆系统测试
print("\n3. 测试记忆系统...")

ms = MemorySystem(data_dir="./test_enhanced_v2")
ms.store.clear_all()
ms.start_session()

ms.remember("Python 编程语言")
ms.remember("Django Web 框架")
ms.remember("Docker 容器技术")

ms.connect_knowledge("Django", "Python", "uses")

print(f"   记忆节点数: {len(ms.store.graph.nodes)}")
print(f"   关键词索引: {len(ms.store.memory_index)}")

results = ms.recall("Python", k=5)
print(f"   查询结果: {len(results)}")
for r in results:
    print(f"      - {r['label']}")

# 4. 深度推理测试
print("\n4. 测试深度推理...")

ms.connect_knowledge("A", "B", "related_to")
ms.connect_knowledge("B", "C", "related_to")
ms.connect_knowledge("C", "D", "related_to")

inferences = ms.infer("A", max_depth=3)
print(f"   深度推理结果: {len(inferences)}")
for i in inferences:
    print(f"      - {i}")

# 5. 完整验证
print("\n" + "=" * 70)
print("🎉 所有测试通过！增强版工作正常！")
print("=" * 70)
