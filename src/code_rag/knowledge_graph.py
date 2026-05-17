"""
知识图谱记忆系统 - 核心数据模型
基于图论的知识表示与存储
"""

from typing import Dict, List, Optional, Any, Set, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import uuid
import json


class KnowledgeType(Enum):
    """知识类型枚举"""
    ENTITY = "entity"        # 实体（如"Python"、"Docker"）
    CONCEPT = "concept"      # 概念（如"容器化"、"微服务"）
    FACT = "fact"            # 事实（如"Kubernetes是容器编排工具"）
    PROCESS = "process"      # 流程/步骤
    DOCUMENT = "document"    # 文档/知识源
    USER = "user"            # 用户实体
    SESSION = "session"      # 会话实体


class RelationType(Enum):
    """关系类型枚举"""
    IS_A = "is_a"            # 是...（子类关系）
    HAS_A = "has_a"          # 有...（拥有关系）
    USES = "uses"            # 使用
    RELATED_TO = "related_to"  # 相关于
    DEPENDS_ON = "depends_on"  # 依赖于
    PART_OF = "part_of"      # 属于...的一部分
    CREATED_BY = "created_by"  # 由...创建
    DOCUMENTS = "documents"  # 记录...
    REMEMBERS = "remembers"  # 记得...


@dataclass
class KnowledgeNode:
    """知识节点（实体/概念）"""
    label: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: KnowledgeType = KnowledgeType.ENTITY
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "type": self.type.value,
            "properties": self.properties,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeNode':
        return cls(
            label=data["label"],
            id=data["id"],
            type=KnowledgeType(data["type"]),
            properties=data["properties"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )


@dataclass
class KnowledgeEdge:
    """知识边（关系）"""
    source_id: str
    target_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: RelationType = RelationType.RELATED_TO
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    weight: float = 1.0  # 关系权重，用于记忆强度
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "type": self.type.value,
            "properties": self.properties,
            "created_at": self.created_at.isoformat(),
            "weight": self.weight
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeEdge':
        return cls(
            source_id=data["source_id"],
            target_id=data["target_id"],
            id=data["id"],
            type=RelationType(data["type"]),
            properties=data.get("properties", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            weight=data.get("weight", 1.0)
        )


@dataclass
class MemorySession:
    """记忆会话（用于用户会话管理）"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    nodes: List[str] = field(default_factory=list)  # 关联的节点ID
    edges: List[str] = field(default_factory=list)  # 关联的边ID
    created_at: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "nodes": self.nodes,
            "edges": self.edges,
            "created_at": self.created_at.isoformat(),
            "context": self.context
        }


class KnowledgeGraph:
    """知识图谱核心类"""
    
    def __init__(self):
        self.nodes: Dict[str, KnowledgeNode] = {}  # 节点字典 {node_id: node}
        self.edges: Dict[str, KnowledgeEdge] = {}  # 边字典 {edge_id: edge}
        self.outgoing_edges: Dict[str, List[str]] = {}  # 出边索引 {node_id: [edge_ids]}
        self.incoming_edges: Dict[str, List[str]] = {}  # 入边索引 {node_id: [edge_ids]}
        self.label_index: Dict[str, Set[str]] = {}  # 标签索引 {label_lower: {node_ids}}
    
    def add_node(self, node: KnowledgeNode) -> str:
        """添加知识节点"""
        self.nodes[node.id] = node
        
        # 更新标签索引
        label_lower = node.label.lower()
        if label_lower not in self.label_index:
            self.label_index[label_lower] = set()
        self.label_index[label_lower].add(node.id)
        
        # 初始化邻接索引
        if node.id not in self.outgoing_edges:
            self.outgoing_edges[node.id] = []
        if node.id not in self.incoming_edges:
            self.incoming_edges[node.id] = []
        
        return node.id
    
    def add_edge(self, edge: KnowledgeEdge) -> str:
        """添加知识边"""
        # 验证节点存在
        if edge.source_id not in self.nodes or edge.target_id not in self.nodes:
            raise ValueError("Source or target node does not exist")
        
        self.edges[edge.id] = edge
        
        # 更新邻接索引
        if edge.source_id not in self.outgoing_edges:
            self.outgoing_edges[edge.source_id] = []
        self.outgoing_edges[edge.source_id].append(edge.id)
        
        if edge.target_id not in self.incoming_edges:
            self.incoming_edges[edge.target_id] = []
        self.incoming_edges[edge.target_id].append(edge.id)
        
        return edge.id
    
    def connect(self, source_label: str, target_label: str, 
                relation_type: RelationType = RelationType.RELATED_TO,
                weight: float = 1.0) -> str:
        """通过标签连接两个节点（自动查找或创建）"""
        # 查找或创建源节点
        source_nodes = self.find_nodes_by_label(source_label)
        if source_nodes:
            source_node = source_nodes[0]
        else:
            source_node = KnowledgeNode(label=source_label, type=KnowledgeType.ENTITY)
            self.add_node(source_node)
        
        # 查找或创建目标节点
        target_nodes = self.find_nodes_by_label(target_label)
        if target_nodes:
            target_node = target_nodes[0]
        else:
            target_node = KnowledgeNode(label=target_label, type=KnowledgeType.ENTITY)
            self.add_node(target_node)
        
        # 创建边
        edge = KnowledgeEdge(
            source_id=source_node.id,
            target_id=target_node.id,
            type=relation_type,
            weight=weight
        )
        return self.add_edge(edge)
    
    def find_nodes_by_label(self, label: str) -> List[KnowledgeNode]:
        """通过标签查找节点（不区分大小写）"""
        label_lower = label.lower()
        node_ids = self.label_index.get(label_lower, set())
        return [self.nodes[id] for id in node_ids]
    
    def get_neighbors(self, node_id: str, direction: str = "both") -> List[KnowledgeNode]:
        """获取节点邻居"""
        neighbor_ids = set()
        
        if direction in ["both", "out"]:
            for edge_id in self.outgoing_edges.get(node_id, []):
                edge = self.edges[edge_id]
                neighbor_ids.add(edge.target_id)
        
        if direction in ["both", "in"]:
            for edge_id in self.incoming_edges.get(node_id, []):
                edge = self.edges[edge_id]
                neighbor_ids.add(edge.source_id)
        
        return [self.nodes[id] for id in neighbor_ids]
    
    def search(self, query: str, k: int = 10) -> List[KnowledgeNode]:
        """简单搜索（基于标签匹配）"""
        results = []
        query_lower = query.lower()
        
        for label_lower, node_ids in self.label_index.items():
            if query_lower in label_lower:
                for node_id in node_ids:
                    results.append(self.nodes[node_id])
        
        return results[:k]
    
    def to_json(self) -> str:
        """导出为JSON"""
        return json.dumps({
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [edge.to_dict() for edge in self.edges.values()]
        }, indent=2, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'KnowledgeGraph':
        """从JSON导入"""
        data = json.loads(json_str)
        graph = cls()
        
        for node_data in data.get("nodes", []):
            graph.add_node(KnowledgeNode.from_dict(node_data))
        
        for edge_data in data.get("edges", []):
            graph.add_edge(KnowledgeEdge.from_dict(edge_data))
        
        return graph
    
    def export_for_vis(self) -> Dict[str, Any]:
        """导出为vis.js格式用于可视化"""
        vis_nodes = []
        for node in self.nodes.values():
            vis_nodes.append({
                "id": node.id,
                "label": node.label,
                "type": node.type.value
            })
        
        vis_edges = []
        for edge in self.edges.values():
            vis_edges.append({
                "from": edge.source_id,
                "to": edge.target_id,
                "label": edge.type.value,
                "width": edge.weight * 3
            })
        
        return {"nodes": vis_nodes, "edges": vis_edges}
