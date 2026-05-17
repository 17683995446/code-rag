"""
🚀 知识图谱记忆系统 - v3.0 超级优化版！

包含：
- 极致性能优化
- 完善的容错机制
- 智能内存管理
- 批量操作支持
- 高效索引系统
- 完整异常处理
"""

import json
import os
import pickle
import threading
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from collections import defaultdict, OrderedDict
from datetime import datetime
import time


# ------------------------------
# 核心数据模型
# ------------------------------

class KnowledgeType(Enum):
    ENTITY = "entity"
    CONCEPT = "concept"
    FACT = "fact"
    PROCESS = "process"
    DOCUMENT = "document"
    USER = "user"
    SESSION = "session"


class RelationType(Enum):
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
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    node_ids: List[str] = field(default_factory=list)
    edge_ids: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)


# ------------------------------
# 性能优化 - LRU Cache
# ------------------------------

class LRUCache:
    """简单高效的LRU缓存"""
    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.cache: OrderedDict[str, Any] = OrderedDict()
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self.cache:
                return None
            self.cache.move_to_end(key)
            return self.cache[key]
    
    def put(self, key: str, value: Any) -> None:
        with self._lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            else:
                if len(self.cache) >= self.capacity:
                    self.cache.popitem(last=False)
            self.cache[key] = value
    
    def clear(self) -> None:
        with self._lock:
            self.cache.clear()


# ------------------------------
# 超级优化版 - Knowledge Graph
# ------------------------------

class OptimizedKnowledgeGraph:
    """
    v3.0 优化版知识图谱
    """
    
    def __init__(self):
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.edges: Dict[str, KnowledgeEdge] = {}
        self.outgoing: Dict[str, List[str]] = defaultdict(list)
        self.incoming: Dict[str, List[str]] = defaultdict(list)
        self.label_index: Dict[str, Set[str]] = defaultdict(set)
        
        # 锁分离 - 减少粒度
        self._node_lock = threading.Lock()
        self._edge_lock = threading.Lock()
        self._search_lock = threading.Lock()
        
        # 查询缓存
        self._query_cache = LRUCache(2000)
        
        # 统计信息
        self._stats = {'adds': 0, 'deletes': 0, 'queries': 0}
    
    #
    # 节点操作
    #
    
    def add_node(self, node: KnowledgeNode) -> str:
        with self._node_lock:
            self.nodes[node.id] = node
            label_key = node.label.lower()
            self.label_index[label_key].add(node.id)
            self._stats['adds'] += 1
            self._query_cache.clear()
        return node.id
    
    def add_nodes_bulk(self, nodes: List[KnowledgeNode]) -> List[str]:
        with self._node_lock:
            ids = []
            for node in nodes:
                self.nodes[node.id] = node
                label_key = node.label.lower()
                self.label_index[label_key].add(node.id)
                ids.append(node.id)
            self._stats['adds'] += len(nodes)
            self._query_cache.clear()
        return ids
    
    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        with self._node_lock:
            return self.nodes.get(node_id)
    
    def find_nodes_by_label(self, label: str) -> List[KnowledgeNode]:
        with self._search_lock:
            label_lower = label.lower()
            node_ids = self.label_index.get(label_lower, set())
            return [self.nodes[nid] for nid in node_ids if nid in self.nodes]
    
    def delete_node(self, node_id: str, cascade: bool = True) -> bool:
        success = False
        
        with self._node_lock, self._edge_lock:
            if node_id not in self.nodes:
                return False
            
            if cascade:
                # 找出要删除的边
                to_delete = []
                if node_id in self.outgoing:
                    to_delete.extend(self.outgoing[node_id])
                if node_id in self.incoming:
                    to_delete.extend(self.incoming[node_id])
                
                # 删除边
                for edge_id in to_delete:
                    if edge_id in self.edges:
                        edge = self.edges[edge_id]
                        # 清理出边索引
                        if edge.source_id in self.outgoing and edge_id in self.outgoing[edge.source_id]:
                            self.outgoing[edge.source_id].remove(edge_id)
                        # 清理入边索引
                        if edge.target_id in self.incoming and edge_id in self.incoming[edge.target_id]:
                            self.incoming[edge.target_id].remove(edge_id)
                        del self.edges[edge_id]
            
            # 删除节点
            node = self.nodes[node_id]
            label_key = node.label.lower()
            if label_key in self.label_index and node_id in self.label_index[label_key]:
                self.label_index[label_key].remove(node_id)
                if not self.label_index[label_key]:
                    del self.label_index[label_key]
            
            if node_id in self.outgoing:
                del self.outgoing[node_id]
            if node_id in self.incoming:
                del self.incoming[node_id]
            
            del self.nodes[node_id]
            self._stats['deletes'] += 1
            self._query_cache.clear()
            success = True
        
        return success
    
    #
    # 边操作
    #
    
    def add_edge(self, edge: KnowledgeEdge) -> str:
        with self._edge_lock:
            # 快速检查节点是否存在
            if edge.source_id not in self.nodes or edge.target_id not in self.nodes:
                raise ValueError("Source or target node missing")
            self.edges[edge.id] = edge
            self.outgoing[edge.source_id].append(edge.id)
            self.incoming[edge.target_id].append(edge.id)
            self._query_cache.clear()
        return edge.id
    
    def connect(self, source_label: str, target_label: str,
                relation_type: RelationType = RelationType.RELATED_TO,
                weight: float = 1.0) -> str:
        with self._node_lock, self._edge_lock:
            # 查找或创建源节点
            s_nodes = list(self._find_nodes_by_label_internal(source_label))
            if s_nodes:
                source_node = s_nodes[0]
            else:
                source_node = KnowledgeNode(source_label)
                self.nodes[source_node.id] = source_node
                self.label_index[source_label.lower()].add(source_node.id)
            
            # 查找或创建目标节点
            t_nodes = list(self._find_nodes_by_label_internal(target_label))
            if t_nodes:
                target_node = t_nodes[0]
            else:
                target_node = KnowledgeNode(target_label)
                self.nodes[target_node.id] = target_node
                self.label_index[target_label.lower()].add(target_node.id)
            
            edge = KnowledgeEdge(
                source_node.id, target_node.id,
                type=relation_type, weight=weight
            )
            self.edges[edge.id] = edge
            self.outgoing[edge.source_id].append(edge.id)
            self.incoming[edge.target_id].append(edge.id)
            self._query_cache.clear()
        
        return edge.id
    
    def get_neighbors(self, node_id: str, direction: str = "both") -> List[KnowledgeNode]:
        result = []
        with self._node_lock, self._edge_lock:
            if direction in ["both", "out"]:
                for edge_id in self.outgoing.get(node_id, []):
                    if edge_id in self.edges:
                        tid = self.edges[edge_id].target_id
                        if tid in self.nodes:
                            result.append(self.nodes[tid])
            if direction in ["both", "in"]:
                for edge_id in self.incoming.get(node_id, []):
                    if edge_id in self.edges:
                        sid = self.edges[edge_id].source_id
                        if sid in self.nodes:
                            result.append(self.nodes[sid])
        return result
    
    #
    # 搜索与推理
    #
    
    def search(self, query: str, k: int = 10) -> List[KnowledgeNode]:
        self._stats['queries'] += 1
        
        cache_key = f"search:{query}:{k}"
        cached = self._query_cache.get(cache_key)
        if cached is not None:
            return cached
        
        results = []
        seen: Set[str] = set()
        query_lower = query.lower()
        
        with self._search_lock:
            # 快速前缀匹配
            for label_lower, node_ids in self.label_index.items():
                if query_lower in label_lower:
                    for nid in node_ids:
                        if nid not in seen and nid in self.nodes:
                            results.append(self.nodes[nid])
                            seen.add(nid)
                            if len(results) >= k:
                                break
                if len(results) >= k:
                    break
        
        self._query_cache.put(cache_key, results)
        return results[:k]
    
    def infer(self, start_label: str, max_depth: int = 2) -> List[Dict[str, Any]]:
        cache_key = f"infer:{start_label}:{max_depth}"
        cached = self._query_cache.get(cache_key)
        if cached is not None:
            return cached
        
        results: List[Dict] = []
        seen: Set[str] = set()
        
        with self._node_lock, self._edge_lock:
            start_nodes = self._find_nodes_by_label_internal(start_label)
            for start_node in start_nodes:
                if start_node.id in seen:
                    continue
                
                # BFS
                queue = [(start_node.id, 0)]
                seen.add(start_node.id)
                
                while queue:
                    node_id, depth = queue.pop(0)
                    if depth > max_depth:
                        continue
                    
                    for edge_id in self.outgoing.get(node_id, []):
                        if edge_id not in self.edges:
                            continue
                        edge = self.edges[edge_id]
                        if edge.target_id in self.nodes and edge.target_id not in seen:
                            target = self.nodes[edge.target_id]
                            results.append({
                                "source": start_node.label,
                                "target": target.label,
                                "relation": edge.type.value,
                                "depth": depth + 1
                            })
                            seen.add(edge.target_id)
                            queue.append((edge.target_id, depth + 1))
        
        self._query_cache.put(cache_key, results)
        return results
    
    #
    # 内部工具函数
    #
    
    def _find_nodes_by_label_internal(self, label: str):
        label_lower = label.lower()
        for nid in self.label_index.get(label_lower, set()):
            if nid in self.nodes:
                yield self.nodes[nid]
    
    #
    # 导入导出
    #
    
    def to_json(self) -> str:
        with self._node_lock, self._edge_lock:
            return json.dumps({
                "nodes": [n.to_dict() for n in self.nodes.values()],
                "edges": [e.to_dict() for e in self.edges.values()]
            }, ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'OptimizedKnowledgeGraph':
        data = json.loads(json_str)
        g = cls()
        
        with g._node_lock, g._edge_lock:
            for n_data in data.get("nodes", []):
                node = KnowledgeNode.from_dict(n_data)
                g.nodes[node.id] = node
                g.label_index[node.label.lower()].add(node.id)
            
            for e_data in data.get("edges", []):
                edge = KnowledgeEdge.from_dict(e_data)
                g.edges[edge.id] = edge
                g.outgoing[edge.source_id].append(edge.id)
                g.incoming[edge.target_id].append(edge.id)
        
        return g
    
    def export_for_vis(self) -> Dict[str, Any]:
        with self._node_lock, self._edge_lock:
            vis_nodes = [
                {"id": n.id, "label": n.label, "type": n.type.value}
                for n in self.nodes.values()
            ]
            vis_edges = [
                {"from": e.source_id, "to": e.target_id, "label": e.type.value, "width": e.weight * 3}
                for e in self.edges.values()
            ]
        return {"nodes": vis_nodes, "edges": vis_edges}
    
    #
    # 统计
    #
    
    def stats(self) -> Dict[str, Any]:
        with self._node_lock, self._edge_lock:
            return {
                "nodes": len(self.nodes),
                "edges": len(self.edges),
                "adds": self._stats['adds'],
                "deletes": self._stats['deletes'],
                "queries": self._stats['queries'],
                "cache_size": len(self._query_cache.cache)
            }


# ------------------------------
# 超级优化版 - 记忆系统
# ------------------------------

class OptimizedMemorySystem:
    """
    v3.0 优化版记忆系统
    """
    
    def __init__(self, data_dir: str = "./data_v3"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.graph_file = self.data_dir / "kg.json"
        self.sess_file = self.data_dir / "sessions.pkl"
        self.index_file = self.data_dir / "keywords.json"
        
        self.graph = OptimizedKnowledgeGraph()
        self.sessions: Dict[str, MemorySession] = {}
        self.keyword_index: Dict[str, List[str]] = defaultdict(list)
        
        self._lock = threading.Lock()
        self._cache = LRUCache(1000)
        
        self._load()
    
    def _load(self):
        try:
            if self.graph_file.exists():
                with open(self.graph_file, 'r', encoding='utf-8') as f:
                    self.graph = OptimizedKnowledgeGraph.from_json(f.read())
        except Exception as e:
            print(f"Load graph err: {e}")
        
        try:
            if self.sess_file.exists():
                with open(self.sess_file, 'rb') as f:
                    self.sessions = pickle.load(f)
        except Exception as e:
            print(f"Load sessions err: {e}")
        
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    d = json.load(f)
                    self.keyword_index = defaultdict(list, d)
        except Exception as e:
            print(f"Load index err: {e}")
    
    def save(self):
        with self._lock:
            with open(self.graph_file, 'w', encoding='utf-8') as f:
                f.write(self.graph.to_json())
            with open(self.sess_file, 'wb') as f:
                pickle.dump(self.sessions, f)
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(dict(self.keyword_index), f, ensure_ascii=False, indent=2)
    
    def clear_all(self):
        with self._lock:
            self.graph = OptimizedKnowledgeGraph()
            self.sessions.clear()
            self.keyword_index.clear()
            self._cache.clear()
            self.save()
    
    #
    # 会话管理
    #
    
    def start_session(self, user_id: Optional[str] = None) -> str:
        with self._lock:
            s = MemorySession(user_id=user_id)
            self.sessions[s.id] = s
            self.save()
        return s.id
    
    #
    # 记忆与搜索
    #
    
    def remember(self, knowledge: str, metadata: Optional[Dict] = None) -> str:
        with self._lock:
            node = KnowledgeNode(knowledge, properties=metadata or {})
            node_id = self.graph.add_node(node)
            
            keywords = self._extract_keywords(knowledge)
            for kw in keywords:
                self.keyword_index[kw.lower()].append(node_id)
            
            self._cache.clear()
            return node_id
    
    def connect_knowledge(self, source: str, target: str, relation: str = "related_to") -> str:
        rt_map = {rt.value: rt for rt in RelationType}
        rt = rt_map.get(relation, RelationType.RELATED_TO)
        return self.graph.connect(source, target, rt)
    
    def recall(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        cache_key = f"recall:{query}:{k}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
        
        with self._lock:
            results: List[Dict] = []
            seen: Set[str] = set()
            
            # 1. 标签直接搜索
            direct = self.graph.search(query, k=k)
            for node in direct:
                if node.id not in seen:
                    results.append(node.to_dict())
                    seen.add(node.id)
                    if len(results) >= k:
                        break
            
            # 2. 关键词搜索
            if len(results) < k:
                q_kw = self._extract_keywords(query)
                for kw in q_kw:
                    kw = kw.lower()
                    for nid in self.keyword_index.get(kw, []):
                        if len(results) >= k:
                            break
                        n = self.graph.get_node(nid)
                        if n and n.id not in seen:
                            results.append(n.to_dict())
                            seen.add(n.id)
            
            self._cache.put(cache_key, results[:k])
            return results[:k]
    
    def infer(self, concept: str, max_depth: int = 2) -> List[Dict[str, Any]]:
        return self.graph.infer(concept, max_depth)
    
    def forget(self, node_id: str) -> bool:
        with self._lock:
            success = self.graph.delete_node(node_id, cascade=True)
            if success:
                to_remove = []
                for kw, ids in self.keyword_index.items():
                    if node_id in ids:
                        ids.remove(node_id)
                        if not ids:
                            to_remove.append(kw)
                for kw in to_remove:
                    del self.keyword_index[kw]
                self._cache.clear()
                self.save()
            return success
    
    def stats(self) -> Dict[str, Any]:
        with self._lock:
            gstats = self.graph.stats()
            return {
                **gstats,
                "keywords": len(self.keyword_index),
                "sessions": len(self.sessions),
                "cache": len(self._cache.cache)
            }
    
    #
    # 工具函数
    #
    
    def _extract_keywords(self, text: str) -> List[str]:
        import re
        words = re.findall(r"[\w']+", text, re.UNICODE)
        stop = {"the", "is", "are", "of", "to", "a", "an", "and", "or", "but",
                "的", "是", "在", "和", "了", "与", "及", "或"}
        return [w for w in words if w.lower() not in stop and len(w) > 1][:10]
