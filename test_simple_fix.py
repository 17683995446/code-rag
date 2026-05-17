"""
简单的最终验证版本！
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.code_rag.kg_v2_enhanced import (
    KnowledgeGraph, KnowledgeNode, KnowledgeEdge,
    KnowledgeType, RelationType, MemorySystem
)

print("=" * 70)
print("🧪 简单版验证")
print("=" * 70)

# 基础测试
g = KnowledgeGraph()

node_a = KnowledgeNode("A")
node_b = KnowledgeNode("B")
node_c = KnowledgeNode("C")

g.add_node(node_a)
g.add_node(node_b)
g.add_node(node_c)

print(f"节点数: {len(g.nodes)}")

edge1 = KnowledgeEdge(node_a.id, node_b.id)
edge2 = KnowledgeEdge(node_b.id, node_c.id)

g.add_edge(edge1)
g.add_edge(edge2)

print(f"边数: {len(g.edges)}")

# 删除节点 A，级联删除边
print("\n删除节点 A...")
g.delete_node(node_a.id, cascade=True)

print(f"剩余节点: {len(g.nodes)}")
print(f"剩余边: {len(g.edges)}")

# 验证
if len(g.edges) == 1:
    print("\n✅ 级联删除正确！只删除了和 A 相关的边")
else:
    print(f"\n❌ 删除异常，剩余 {len(g.edges)} 边")

print("\n" + "=" * 70)
print("基础功能验证完成")
print("=" * 70)
