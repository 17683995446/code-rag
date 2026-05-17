"""
知识图谱记忆系统 v4.0

基于NetworkX的工业化知识图谱记忆系统

主要模块:
- core: 核心数据结构和记忆系统
- cli: 命令行界面
- web: Web API和可视化
- scoring: 多维度评分系统
"""

__version__ = "4.0.0"
__author__ = "Knowledge Graph Team"

from kg_memory.core import (
    MemorySystem,
    NetworkXGraphEngine,
    Node,
    Edge,
    NodeType,
    EdgeType,
    LRUCache
)

__all__ = [
    "MemorySystem",
    "NetworkXGraphEngine",
    "Node",
    "Edge",
    "NodeType",
    "EdgeType",
    "LRUCache"
]
