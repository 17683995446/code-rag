"""
✅ 问题修复与增强版本 v2.0
修复发现的问题并实现重大改进！
"""

import json
import os
import pickle
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Union
from datetime import datetime, timedelta
from collections import defaultdict
import uuid
from dataclasses import dataclass, field
from enum import Enum


# ============================================
# 修复 1：重新定义核心模型（优化版）
# ============================================
class KnowledgeType(Enum):
    """知识类型枚举"""
    ENTITY = "entity"
    CONCEPT = "concept"
    FACT = "fact"
    PROCESS = "process"
    DOCUMENT = "document"
    USER = "user"
    SESSION = "session"


class RelationType(Enum):
    """关系类型枚举"""
    IS_A = "is_a"
    HAS_A = "has_a"
    USES = "uses"
    RELATED_TO = "related_to"
    DEPENDS_ON = "depends_on"
    PART_OF = "part_of"
    CREATED_BY = "created_by"
    DOCUMENTS = "documents"
    REMEMBERS = "remembers"


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
    weight: float = 1.0
    
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
    """记忆会话"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    nodes: List[str] = field(default_factory=list)
    edges: List[str] = field(default_factory=list)
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


# ============================================
# 修复 2：增强版知识图谱（包含完整删除级联）
# ============================================
class KnowledgeGraph:
    """增强版知识图谱"""
    
    def __init__(self):
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.edges: Dict[str, KnowledgeEdge] = {}
        self.outgoing_edges: Dict[str, List[str]] = defaultdict(list)
        self.incoming_edges: Dict[str, List[str]] = defaultdict(list)
        self.label_index: Dict[str, Set[str]] = defaultdict(set)
        self._lock = threading.Lock()  # 新增：线程安全锁！
    
    def add_node(self, node: KnowledgeNode) -> str:
        """添加知识节点（线程安全）"""
        with self._lock:
            self.nodes[node.id] = node
            label_lower = node.label.lower()
            self.label_index[label_lower].add(node.id)
            if node.id not in self.outgoing_edges:
                self.outgoing_edges[node.id] = []
            if node.id not in self.incoming_edges:
                self.incoming_edges[node.id] = []
        return node.id
    
    def add_edge(self, edge: KnowledgeEdge) -> str:
        """添加知识边（线程安全）"""
        with self._lock:
            if edge.source_id not in self.nodes or edge.target_id not in self.nodes:
                raise ValueError(f"源或目标节点不存在: {edge.source_id}, {edge.target_id}")
            
            self.edges[edge.id] = edge
            self.outgoing_edges[edge.source_id].append(edge.id)
            self.incoming_edges[edge.target_id].append(edge.id)
        return edge.id
    
    def delete_node(self, node_id: str, cascade: bool = True) -> bool:
        """✅ 修复：完整级联删除！"""
        with self._lock:
            if node_id not in self.nodes:
                return False
            
            # 找出所有相关的边
            related_edge_ids = []
            if node_id in self.outgoing_edges:
                related_edge_ids.extend(self.outgoing_edges[node_id])
            if node_id in self.incoming_edges:
                related_edge_ids.extend(self.incoming_edges[node_id])
            
            # 删除边
            for edge_id in related_edge_ids:
                self._delete_edge_internal(edge_id)
            
            # 清理节点
            node = self.nodes[node_id]
            label_lower = node.label.lower()
            if label_lower in self.label_index and node_id in self.label_index[label_lower]:
                self.label_index[label_lower].remove(node_id)
                if not self.label_index[label_lower]:
                    del self.label_index[label_lower]
            
            del self.nodes[node_id]
            if node_id in self.outgoing_edges:
                del self.outgoing_edges[node_id]
            if node_id in self.incoming_edges:
                del self.incoming_edges[node_id]
            
            return True
    
    def _delete_edge_internal(self, edge_id: str):
        """内部删除边函数"""
        if edge_id not in self.edges:
            return
        
        edge = self.edges[edge_id]
        
        # 从源节点的出边删除
        if edge.source_id in self.outgoing_edges:
            try:
                self.outgoing_edges[edge.source_id].remove(edge_id)
            except ValueError:
                pass
        
        # 从目标节点的入边删除
        if edge.target_id in self.incoming_edges:
            try:
                self.incoming_edges[edge.target_id].remove(edge_id)
            except ValueError:
                pass
        
        del self.edges[edge_id]
    
    def connect(self, source_label: str, target_label: str, 
                relation_type: RelationType = RelationType.RELATED_TO,
                weight: float = 1.0) -> str:
        """通过标签连接两个节点"""
        with self._lock:
            source_nodes = list(self._find_nodes_by_label_internal(source_label))
            if source_nodes:
                source_node = source_nodes[0]
            else:
                source_node = KnowledgeNode(source_label, type=KnowledgeType.ENTITY)
                self._add_node_internal(source_node)
            
            target_nodes = list(self._find_nodes_by_label_internal(target_label))
            if target_nodes:
                target_node = target_nodes[0]
            else:
                target_node = KnowledgeNode(target_label, type=KnowledgeType.ENTITY)
                self._add_node_internal(target_node)
            
            edge = KnowledgeEdge(source_node.id, target_node.id, type=relation_type, weight=weight)
            return self._add_edge_internal(edge)
    
    def _add_node_internal(self, node: KnowledgeNode):
        """内部添加（无锁）"""
        self.nodes[node.id] = node
        label_lower = node.label.lower()
        self.label_index[label_lower].add(node.id)
        if node.id not in self.outgoing_edges:
            self.outgoing_edges[node.id] = []
        if node.id not in self.incoming_edges:
            self.incoming_edges[node.id] = []
    
    def _add_edge_internal(self, edge: KnowledgeEdge):
        """内部添加边（无锁）"""
        self.edges[edge.id] = edge
        self.outgoing_edges[edge.source_id].append(edge.id)
        self.incoming_edges[edge.target_id].append(edge.id)
        return edge.id
    
    def _find_nodes_by_label_internal(self, label: str):
        """内部查找（无锁）"""
        label_lower = label.lower()
        for node_id in self.label_index.get(label_lower, []):
            if node_id in self.nodes:
                yield self.nodes[node_id]
    
    def find_nodes_by_label(self, label: str) -> List[KnowledgeNode]:
        """查找节点（线程安全）"""
        with self._lock:
            return list(self._find_nodes_by_label_internal(label))
    
    def get_neighbors(self, node_id: str, direction: str = "both") -> List[KnowledgeNode]:
        """获取邻居（线程安全）"""
        with self._lock:
            neighbor_ids = set()
            if direction in ["both", "out"]:
                for edge_id in self.outgoing_edges.get(node_id, []):
                    if edge_id in self.edges:
                        neighbor_ids.add(self.edges[edge_id].target_id)
            
            if direction in ["both", "in"]:
                for edge_id in self.incoming_edges.get(node_id, []):
                    if edge_id in self.edges:
                        neighbor_ids.add(self.edges[edge_id].source_id)
            
            return [self.nodes[nid] for nid in neighbor_ids if nid in self.nodes]
    
    def search(self, query: str, k: int = 10) -> List[KnowledgeNode]:
        """搜索（线程安全）"""
        with self._lock:
            results = []
            query_lower = query.lower()
            seen = set()
            
            for label_lower, node_ids in self.label_index.items():
                if query_lower in label_lower:
                    for node_id in node_ids:
                        if node_id in self.nodes and node_id not in seen:
                            results.append(self.nodes[node_id])
                            seen.add(node_id)
                            if len(results) >= k:
                                break
                if len(results) >= k:
                    break
            
            return results
    
    def to_json(self) -> str:
        """导出为 JSON（线程安全）"""
        with self._lock:
            return json.dumps({
                "nodes": [node.to_dict() for node in self.nodes.values()],
                "edges": [edge.to_dict() for edge in self.edges.values()]
            }, indent=2, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'KnowledgeGraph':
        """从 JSON 导入"""
        data = json.loads(json_str)
        graph = cls()
        for node_data in data.get("nodes", []):
            graph._add_node_internal(KnowledgeNode.from_dict(node_data))
        for edge_data in data.get("edges", []):
            graph._add_edge_internal(KnowledgeEdge.from_dict(edge_data))
        return graph
    
    def export_for_vis(self) -> Dict[str, Any]:
        """导出为 Vis.js 格式"""
        with self._lock:
            vis_nodes = [
                {"id": node.id, "label": node.label, "type": node.type.value}
                for node in self.nodes.values()
            ]
            vis_edges = [
                {"from": edge.source_id, "to": edge.target_id, 
                 "label": edge.type.value, "width": edge.weight * 3}
                for edge in self.edges.values()
            ]
            return {"nodes": vis_nodes, "edges": vis_edges}


# ============================================
# 修复 3：增强版存储引擎与记忆系统
# ============================================
class KnowledgeStore:
    """增强版存储引擎"""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.graph_file = self.data_dir / "knowledge_graph.json"
        self.sessions_file = self.data_dir / "sessions.pkl"
        self.memory_file = self.data_dir / "memory_index.json"
        
        self.graph = KnowledgeGraph()
        self.sessions: Dict[str, MemorySession] = {}
        self.memory_index: Dict[str, List[str]] = defaultdict(list)
        self._lock = threading.Lock()
        
        self._load()
    
    def _load(self):
        """从磁盘加载"""
        if self.graph_file.exists():
            try:
                with open(self.graph_file, 'r', encoding='utf-8') as f:
                    self.graph = KnowledgeGraph.from_json(f.read())
            except Exception as e:
                print(f"加载图数据失败: {e}")
        
        if self.sessions_file.exists():
            try:
                with open(self.sessions_file, 'rb') as f:
                    self.sessions = pickle.load(f)
            except Exception as e:
                print(f"加载会话数据失败: {e}")
        
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.memory_index = defaultdict(list, data)
            except Exception as e:
                print(f"加载记忆索引失败: {e}")
    
    def save(self):
        """保存到磁盘"""
        with self._lock:
            with open(self.graph_file, 'w', encoding='utf-8') as f:
                f.write(self.graph.to_json())
            
            with open(self.sessions_file, 'wb') as f:
                pickle.dump(self.sessions, f)
            
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(dict(self.memory_index), f, ensure_ascii=False, indent=2)
    
    def clear_all(self):
        """清空所有"""
        with self._lock:
            self.graph = KnowledgeGraph()
            self.sessions = {}
            self.memory_index = defaultdict(list)
            self.save()


class MemorySystem:
    """增强版记忆系统"""
    
    def __init__(self, data_dir: str = "./data"):
        self.store = KnowledgeStore(data_dir)
        self.current_session: Optional[MemorySession] = None
        self.recent_nodes: List[str] = []
        self.max_recent = 50
        self._lock = threading.Lock()
    
    def start_session(self, user_id: Optional[str] = None) -> str:
        with self._lock:
            session = MemorySession(user_id=user_id)
            self.store.sessions[session.id] = session
            self.current_session = session
            self.store.save()
            return session.id
    
    def remember(self, knowledge: str, metadata: Optional[Dict] = None) -> str:
        """记住知识（修复关键词索引！）"""
        with self._lock:
            if self.current_session is None:
                self.start_session()
            
            node = KnowledgeNode(
                knowledge,
                type=KnowledgeType.FACT,
                properties=metadata or {}
            )
            node_id = self.store.graph.add_node(node)
            
            # 修复：正确添加关键词索引！
            keywords = self._extract_keywords(knowledge)
            for keyword in keywords:
                self.store.memory_index[keyword.lower()].append(node_id)
            
            self.current_session.nodes.append(node_id)
            
            self.recent_nodes.insert(0, node_id)
            if len(self.recent_nodes) > self.max_recent:
                self.recent_nodes.pop()
            
            self.store.save()
            return node_id
    
    def connect_knowledge(self, source: str, target: str, 
                         relation: str = "related_to") -> str:
        with self._lock:
            rt_map = {rt.value: rt for rt in RelationType}
            rt = rt_map.get(relation, RelationType.RELATED_TO)
            return self.store.graph.connect(source, target, rt)
    
    def recall(self, query: str, k: int = 10) -> List[Dict]:
        """回忆知识（优化搜索策略）"""
        with self._lock:
            query_lower = query.lower()
            
            # 策略 1：标签直接匹配
            direct = self.store.graph.search(query, k=k)
            results = [n.to_dict() for n in direct]
            seen_ids = set(n['id'] for n in results)
            
            # 策略 2：关键词索引匹配
            query_keywords = self._extract_keywords(query)
            for keyword in query_keywords:
                kw_lower = keyword.lower()
                for node_id in self.store.memory_index.get(kw_lower, []):
                    if node_id in self.store.graph.nodes and node_id not in seen_ids:
                        node = self.store.graph.nodes[node_id]
                        results.append(node.to_dict())
                        seen_ids.add(node_id)
                        if len(results) >= k:
                            break
                if len(results) >= k:
                    break
            
            # 策略 3：最近优先补全
            for node_id in self.recent_nodes:
                if len(results) >= k:
                    break
                if node_id in self.store.graph.nodes and node_id not in seen_ids:
                    results.append(self.store.graph.nodes[node_id].to_dict())
                    seen_ids.add(node_id)
            
            return results[:k]
    
    def get_context(self) -> List[Dict]:
        with self._lock:
            if not self.current_session:
                return []
            ctx = []
            for node_id in self.current_session.nodes[-20:]:
                if node_id in self.store.graph.nodes:
                    ctx.append(self.store.graph.nodes[node_id].to_dict())
            return ctx
    
    def infer(self, concept: str, max_depth: int = 2) -> List[Dict]:
        """✅ 增强：支持深度推理！"""
        with self._lock:
            start_nodes = self.store.graph.find_nodes_by_label(concept)
            results = []
            seen = set()
            
            for start_node in start_nodes:
                queue = [(start_node.id, 0)]
                while queue:
                    node_id, depth = queue.pop(0)
                    if depth > max_depth or node_id in seen:
                        continue
                    seen.add(node_id)
                    
                    # 获取邻居
                    for edge_id in self.store.graph.outgoing_edges.get(node_id, []):
                        if edge_id not in self.store.graph.edges:
                            continue
                        edge = self.store.graph.edges[edge_id]
                        
                        if edge.target_id in self.store.graph.nodes and edge.target_id not in seen:
                            target_node = self.store.graph.nodes[edge.target_id]
                            results.append({
                                "source": self.store.graph.nodes[node_id].label,
                                "target": target_node.label,
                                "relation": edge.type.value,
                                "depth": depth + 1
                            })
                            queue.append((edge.target_id, depth + 1))
            
            return results
    
    def forget(self, knowledge_id: str) -> bool:
        """✅ 修复：完整级联遗忘！"""
        with self._lock:
            # 从关键词索引中删除
            to_remove = []
            for keyword, node_ids in self.store.memory_index.items():
                if knowledge_id in node_ids:
                    self.store.memory_index[keyword] = [nid for nid in node_ids if nid != knowledge_id]
                    if not self.store.memory_index[keyword]:
                        to_remove.append(keyword)
            for kw in to_remove:
                del self.store.memory_index[kw]
            
            # 从最近节点中删除
            if knowledge_id in self.recent_nodes:
                self.recent_nodes.remove(knowledge_id)
            
            # 从会话中删除
            if self.current_session and knowledge_id in self.current_session.nodes:
                self.current_session.nodes.remove(knowledge_id)
            
            # 删除节点和边
            success = self.store.graph.delete_node(knowledge_id, cascade=True)
            
            self.store.save()
            return success
    
    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_nodes": len(self.store.graph.nodes),
                "total_edges": len(self.store.graph.edges),
                "total_sessions": len(self.store.sessions),
                "total_keywords": len(self.store.memory_index),
                "current_session": self.current_session.id if self.current_session else None,
                "recent_nodes": len(self.recent_nodes)
            }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """优化：更好的关键词提取"""
        import re
        # 分词
        words = re.findall(r'[\w\']+', text, re.UNICODE)
        
        # 停用词
        stopwords = {
            "的", "是", "在", "和", "了", "着", "与", "及", "或", "但",
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "with", "is", "was", "are"
        }
        
        keywords = [w for w in words if w.lower() not in stopwords and len(w) > 1]
        return keywords[:10]
