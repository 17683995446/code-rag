#!/usr/bin/env python3
"""调试边创建问题"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from kg_memory.core import MemorySystem
import tempfile

temp_dir = tempfile.mkdtemp()
ms = MemorySystem(temp_dir)
ms.clear()

print("=" * 80)
print("调试边创建问题")
print("=" * 80)

print("\n1. 添加节点...")
for i in range(5):
    node_id = ms.remember(f"DebugNode_{i}")
    print(f"   记住 DebugNode_{i}: {node_id}")

print(f"\n初始统计: {ms.stats()}")

print("\n2. 尝试创建边...")
success_count = 0
for i in range(4):
    try:
        edge_id = ms.connect(f"DebugNode_{i}", f"DebugNode_{i+1}", "related_to")
        print(f"   连接 DebugNode_{i} -> DebugNode_{i+1}: {edge_id}")
        success_count += 1
    except Exception as e:
        print(f"   ❌ 连接失败: {e}")
        import traceback
        traceback.print_exc()

print(f"\n成功创建边: {success_count}")
print(f"\n3. 最终统计: {ms.stats()}")

print("\n4. 检查图引擎状态...")
print(f"   图节点数: {len(ms._graph._nodes)}")
print(f"   图边数: {len(ms._graph._edges)}")
print(f"   NetworkX 节点数: {ms._graph._nx_graph.number_of_nodes()}")
print(f"   NetworkX 边数: {ms._graph._nx_graph.number_of_edges()}")

print("\n5. 测试搜索和推理...")
results = ms.recall("DebugNode", k=10)
print(f"   搜索结果: {len(results)} 个")
for r in results:
    print(f"      - {r['label']}")

print("\n6. 尝试使用图引擎直接创建边...")
for i in range(4):
    try:
        edge_id = ms._graph.connect(f"DebugNode_{i}", f"DebugNode_{i+1}")
        print(f"   直接连接 DebugNode_{i} -> DebugNode_{i+1}: {edge_id}")
    except Exception as e:
        print(f"   ❌ 直接连接失败: {e}")

print(f"\n7. 再次检查统计: {ms.stats()}")
print(f"   NetworkX 边数现在: {ms._graph._nx_graph.number_of_edges()}")
