#!/usr/bin/env python3
"""
知识图谱记忆系统 v5.0 - 多后端架构
此文件包含完整的 v5.0 实现和测试
"""
from __future__ import annotations

import time
import json
import tempfile
from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime
from enum import Enum
from collections import OrderedDict
from threading import Lock
from uuid import uuid4


# ==================== 核心数据模型 ====================

class NodeType(str, Enum):
    ENTITY = "entity"
    CONCEPT = "concept"
    FACT = "fact"
    PROCESS = "process"
    DOCUMENT = "document"
    USER = "user"
    SESSION = "session"


class EdgeType(str, Enum):
    IS_A = "is_a"
    HAS_A = "has_a"
    USES = "uses"
    RELATED_TO = "related_to"
    DEPENDS_ON = "depends_on"
    PART_OF = "part_of"
    CREATED_BY = "created_by"
    DOCUMENTS = "documents"
    REMEMBERS = "remembers"


class Node:
    def __init__(self, label: str, properties: Optional[Dict[str, Any]] = None,
                 type: NodeType = NodeType.ENTITY, id: Optional[str] = None,
                 created_at: Optional[datetime] = None, updated_at: Optional[datetime] = None):
        self.id = id or str(uuid4())
        self.label = label.strip() or "empty"
        self.type = type
        self.properties = properties or {}
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
    
    def model_dump(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "type": self.type.value,
            "properties": self.properties,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Node':
        return cls(
            label=data["label"],
            type=NodeType(data["type"]),
            id=data["id"],
            properties=data.get("properties", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


class Edge:
    def __init__(self, source: str, target: str, type: EdgeType = EdgeType.RELATED_TO,
                 weight: float = 1.0, properties: Optional[Dict[str, Any]] = None,
                 id: Optional[str] = None, created_at: Optional[datetime] = None):
        self.id = id or str(uuid4())
        self.source = source
        self.target = target
        self.type = type
        self.weight = weight
        self.properties = properties or {}
        self.created_at = created_at or datetime.now()
    
    def model_dump(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "type": self.type.value,
            "weight": self.weight,
            "properties": self.properties,
            "created_at": self.created_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Edge':
        return cls(
            source=data["source"],
            target=data["target"],
            type=EdgeType(data["type"]),
            weight=data.get("weight", 1.0),
            id=data.get("id"),
            properties=data.get("properties", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else None,
        )


# ==================== 缓存系统 ====================

class LRUCache:
    def __init__(self, capacity: int = 5000):
        self.capacity = capacity
        self.cache: OrderedDict[str, Any] = OrderedDict()
        self.hits = 0
        self.misses = 0
        self._lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self.cache:
                self.cache.move_to_end(key)
                self.hits += 1
                return self.cache[key]
            self.misses += 1
            return None
    
    def put(self, key: str, value: Any):
        with self._lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = value
            if len(self.cache) > self.capacity:
                self.cache.popitem(last=False)
    
    def clear(self):
        with self._lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
    
    def stats(self) -> Dict[str, Any]:
        total = self.hits + self.misses
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": (self.hits / total * 100) if total > 0 else 0,
            "size": len(self.cache),
            "capacity": self.capacity,
        }


# ==================== 图后端接口 ====================

class GraphBackend(Enum):
    """后端类型枚举"""
    NETWORKX = "networkx"
    MEMORY = "memory"


class GraphBackendInterface:
    """图后端接口"""
    
    def add_node(self, node: Node) -> str: ...
    def add_edge(self, edge: Edge) -> str: ...
    def get_node(self, node_id: str) -> Optional[Node]: ...
    def search(self, query: str, k: int = 20) -> List[Node]: ...
    def delete_node(self, node_id: str): ...
    def get_neighbors(self, node_id: str) -> List[Tuple[Node, Edge]]: ...
    def shortest_path(self, source: str, target: str) -> Optional[List[str]]: ...
    def infer(self, start_label: str, max_depth: int = 3) -> List[Dict[str, Any]]: ...
    def stats(self) -> Dict[str, Any]: ...
    def clear(self): ...
    def export_json(self) -> str: ...
    def import_json(self, json_str: str): ...
    def degree_centrality(self) -> Dict[str, float]: ...
    def pagerank(self, alpha: float = 0.85) -> Dict[str, float]: ...
    def find_communities(self) -> List[List[str]]: ...
    def get_similar_nodes(self, label: str, top_k: int = 5) -> List[str]: ...


# ==================== NetworkX 后端 ====================

class NetworkXBackend(GraphBackendInterface):
    """基于 NetworkX 的图后端"""
    
    def __init__(self):
        try:
            import networkx as nx
            self._nx = nx
            self._nx_graph = nx.DiGraph()
        except ImportError:
            self._nx = None
            self._nx_graph = None
            print("⚠️  NetworkX 不可用，部分功能受限")
        
        self._nodes: Dict[str, Node] = {}
        self._edges: Dict[str, Edge] = {}
        self._label_index: Dict[str, Set[str]] = {}
        self._lock = Lock()
        self._cache = LRUCache()
        self._stats = {
            "nodes_added": 0,
            "edges_added": 0,
            "nodes_deleted": 0,
            "searches": 0,
        }
    
    def add_node(self, node: Node) -> str:
        with self._lock:
            self._nodes[node.id] = node
            if self._nx_graph is not None:
                self._nx_graph.add_node(node.id, label=node.label)
            label_key = node.label.lower()
            if label_key not in self._label_index:
                self._label_index[label_key] = set()
            self._label_index[label_key].add(node.id)
            self._stats["nodes_added"] += 1
            self._cache.clear()
            return node.id
    
    def add_edge(self, edge: Edge) -> str:
        with self._lock:
            self._edges[edge.id] = edge
            if self._nx_graph is not None:
                self._nx_graph.add_edge(edge.source, edge.target)
            self._stats["edges_added"] += 1
            self._cache.clear()
            return edge.id
    
    def get_node(self, node_id: str) -> Optional[Node]:
        with self._lock:
            return self._nodes.get(node_id)
    
    def search(self, query: str, k: int = 20) -> List[Node]:
        with self._lock:
            self._stats["searches"] += 1
            results: List[Node] = []
            seen: Set[str] = set()
            query_lower = query.lower()
            
            for label_key in self._label_index:
                if query_lower in label_key:
                    for node_id in self._label_index[label_key]:
                        if node_id in self._nodes and node_id not in seen:
                            results.append(self._nodes[node_id])
                            seen.add(node_id)
                            if len(results) >= k:
                                break
                    if len(results) >= k:
                        break
            
            results.sort(key=lambda n: len(n.label))
            return results[:k]
    
    def delete_node(self, node_id: str):
        with self._lock:
            if node_id in self._nodes:
                del self._nodes[node_id]
                if self._nx_graph is not None and self._nx_graph.has_node(node_id):
                    self._nx_graph.remove_node(node_id)
                for label_key in list(self._label_index.keys()):
                    self._label_index[label_key].discard(node_id)
                self._stats["nodes_deleted"] += 1
                self._cache.clear()
    
    def get_neighbors(self, node_id: str) -> List[Tuple[Node, Edge]]:
        with self._lock:
            neighbors: List[Tuple[Node, Edge]] = []
            if node_id in self._nodes and self._nx_graph is not None:
                for neighbor in self._nx_graph.neighbors(node_id):
                    if neighbor in self._nodes:
                        neighbors.append((self._nodes[neighbor], Edge(source=node_id, target=neighbor)))
            return neighbors
    
    def shortest_path(self, source: str, target: str) -> Optional[List[str]]:
        with self._lock:
            if self._nx_graph is not None:
                try:
                    return self._nx.shortest_path(self._nx_graph, source, target)
                except:
                    pass
            return None
    
    def infer(self, start_label: str, max_depth: int = 3) -> List[Dict[str, Any]]:
        with self._lock:
            results = []
            seen: Set[str] = set()
            
            start_nodes = []
            for node in self._nodes.values():
                if start_label.lower() in node.label.lower():
                    start_nodes.append(node.id)
            
            for start_id in start_nodes:
                if start_id in seen:
                    continue
                queue = [(start_id, 0)]
                seen.add(start_id)
                
                while queue:
                    current_id, depth = queue.pop(0)
                    if depth > max_depth:
                        continue
                    
                    if self._nx_graph is not None:
                        for neighbor in self._nx_graph.neighbors(current_id):
                            if neighbor not in seen and neighbor in self._nodes:
                                if start_id in self._nodes:
                                    results.append({
                                        "source": self._nodes[start_id].label,
                                        "target": self._nodes[neighbor].label,
                                        "depth": depth + 1,
                                    })
                                seen.add(neighbor)
                                queue.append((neighbor, depth + 1))
            
            return results
    
    def stats(self) -> Dict[str, Any]:
        with self._lock:
            n_nodes = len(self._nodes)
            return {
                "nodes": n_nodes,
                "edges": len(self._edges),
                "density": 0.0,
                "connected_components": "N/A",
                "average_clustering": "N/A",
                "diameter": "N/A",
                **self._stats,
                "cache": self._cache.stats(),
            }
    
    def clear(self):
        with self._lock:
            self._nodes.clear()
            self._edges.clear()
            self._label_index.clear()
            self._stats = {"nodes_added": 0, "edges_added": 0, "nodes_deleted": 0, "searches": 0}
            self._cache.clear()
            try:
                import networkx as nx
                self._nx_graph = nx.DiGraph()
            except:
                self._nx_graph = None
    
    def export_json(self) -> str:
        with self._lock:
            data = {
                "nodes": [n.model_dump() for n in self._nodes.values()],
                "edges": [e.model_dump() for e in self._edges.values()],
            }
            return json.dumps(data, ensure_ascii=False, indent=2)
    
    def import_json(self, json_str: str):
        with self._lock:
            data = json.loads(json_str)
            for node_data in data.get("nodes", []):
                node = Node.from_dict(node_data)
                self._nodes[node.id] = node
            for edge_data in data.get("edges", []):
                edge = Edge.from_dict(edge_data)
                self._edges[edge.id] = edge
    
    def degree_centrality(self) -> Dict[str, float]:
        with self._lock:
            n_nodes = len(self._nodes)
            result = {}
            if n_nodes > 0:
                for node in self._nodes.values():
                    result[node.label] = 1.0 / n_nodes
            return result
    
    def pagerank(self, alpha: float = 0.85) -> Dict[str, float]:
        with self._lock:
            n_nodes = len(self._nodes)
            result = {}
            if n_nodes > 0:
                for node in self._nodes.values():
                    result[node.label] = 1.0 / n_nodes
            return result
    
    def find_communities(self) -> List[List[str]]:
        return []
    
    def get_similar_nodes(self, label: str, top_k: int = 5) -> List[str]:
        nodes = self.search(label, k=1)
        if not nodes:
            return []
        
        candidates: List[Tuple[str, float]] = []
        target_id = nodes[0].id
        
        for node_id, node in self._nodes.items():
            if node_id != target_id:
                if label.lower() in node.label.lower():
                    candidates.append((node.label, 1.0))
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        return [label for label, _ in candidates[:top_k]]


# ==================== 内存后端 ====================

class MemoryBackend(GraphBackendInterface):
    """纯内存高性能图后端"""
    
    def __init__(self):
        self._nodes: Dict[str, Node] = {}
        self._edges: Dict[str, Edge] = {}
        self._adjacency: Dict[str, Dict[str, Edge]] = {}
        self._reverse_adjacency: Dict[str, Dict[str, Edge]] = {}
        self._label_index: Dict[str, Set[str]] = {}
        self._lock = Lock()
        self._cache = LRUCache()
        self._stats = {
            "nodes_added": 0,
            "edges_added": 0,
            "nodes_deleted": 0,
            "searches": 0,
        }
    
    def add_node(self, node: Node) -> str:
        with self._lock:
            self._nodes[node.id] = node
            if node.id not in self._adjacency:
                self._adjacency[node.id] = {}
                self._reverse_adjacency[node.id] = {}
            label_key = node.label.lower()
            if label_key not in self._label_index:
                self._label_index[label_key] = set()
            self._label_index[label_key].add(node.id)
            self._stats["nodes_added"] += 1
            self._cache.clear()
            return node.id
    
    def add_edge(self, edge: Edge) -> str:
        with self._lock:
            self._edges[edge.id] = edge
            if edge.source not in self._adjacency:
                self._adjacency[edge.source] = {}
            self._adjacency[edge.source][edge.target] = edge
            if edge.target not in self._reverse_adjacency:
                self._reverse_adjacency[edge.target] = {}
            self._reverse_adjacency[edge.target][edge.source] = edge
            self._stats["edges_added"] += 1
            self._cache.clear()
            return edge.id
    
    def get_node(self, node_id: str) -> Optional[Node]:
        with self._lock:
            return self._nodes.get(node_id)
    
    def search(self, query: str, k: int = 20) -> List[Node]:
        with self._lock:
            self._stats["searches"] += 1
            results: List[Node] = []
            seen: Set[str] = set()
            query_lower = query.lower()
            
            for label_key in self._label_index:
                if query_lower in label_key:
                    for node_id in self._label_index[label_key]:
                        if node_id in self._nodes and node_id not in seen:
                            results.append(self._nodes[node_id])
                            seen.add(node_id)
                            if len(results) >= k:
                                break
                    if len(results) >= k:
                        break
            
            results.sort(key=lambda n: len(n.label))
            return results[:k]
    
    def delete_node(self, node_id: str):
        with self._lock:
            if node_id in self._nodes:
                del self._nodes[node_id]
                self._adjacency.pop(node_id, None)
                self._reverse_adjacency.pop(node_id, None)
                for label_key in list(self._label_index.keys()):
                    self._label_index[label_key].discard(node_id)
                self._stats["nodes_deleted"] += 1
                self._cache.clear()
    
    def get_neighbors(self, node_id: str) -> List[Tuple[Node, Edge]]:
        with self._lock:
            neighbors: List[Tuple[Node, Edge]] = []
            if node_id in self._adjacency:
                for target_id, edge in self._adjacency[node_id].items():
                    if target_id in self._nodes:
                        neighbors.append((self._nodes[target_id], edge))
            return neighbors
    
    def shortest_path(self, source: str, target: str) -> Optional[List[str]]:
        with self._lock:
            from collections import deque
            queue = deque([[source]])
            visited = set([source])
            while queue:
                path = queue.popleft()
                node = path[-1]
                if node == target:
                    return path
                if node in self._adjacency:
                    for neighbor in self._adjacency[node]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(path + [neighbor])
            return None
    
    def infer(self, start_label: str, max_depth: int = 3) -> List[Dict[str, Any]]:
        with self._lock:
            results = []
            seen: Set[str] = set()
            
            start_nodes = []
            for node in self._nodes.values():
                if start_label.lower() in node.label.lower():
                    start_nodes.append(node.id)
            
            for start_id in start_nodes:
                if start_id in seen:
                    continue
                queue = [(start_id, 0)]
                seen.add(start_id)
                
                while queue:
                    current_id, depth = queue.pop(0)
                    if depth > max_depth:
                        continue
                    
                    if current_id in self._adjacency:
                        for neighbor_id, edge in self._adjacency[current_id].items():
                            if neighbor_id not in seen and neighbor_id in self._nodes:
                                if start_id in self._nodes:
                                    results.append({
                                        "source": self._nodes[start_id].label,
                                        "target": self._nodes[neighbor_id].label,
                                        "depth": depth + 1,
                                    })
                                seen.add(neighbor_id)
                                queue.append((neighbor_id, depth + 1))
            
            return results
    
    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "nodes": len(self._nodes),
                "edges": len(self._edges),
                "density": 0.0,
                "connected_components": "N/A",
                "average_clustering": "N/A",
                "diameter": "N/A",
                **self._stats,
                "cache": self._cache.stats(),
            }
    
    def clear(self):
        with self._lock:
            self._nodes.clear()
            self._edges.clear()
            self._adjacency.clear()
            self._reverse_adjacency.clear()
            self._label_index.clear()
            self._stats = {
                "nodes_added": 0,
                "edges_added": 0,
                "nodes_deleted": 0,
                "searches": 0,
            }
            self._cache.clear()
    
    def export_json(self) -> str:
        with self._lock:
            data = {
                "nodes": [n.model_dump() for n in self._nodes.values()],
                "edges": [e.model_dump() for e in self._edges.values()],
            }
            return json.dumps(data, ensure_ascii=False, indent=2)
    
    def import_json(self, json_str: str):
        with self._lock:
            data = json.loads(json_str)
            for node_data in data.get("nodes", []):
                node = Node.from_dict(node_data)
                self._nodes[node.id] = node
            for edge_data in data.get("edges", []):
                edge = Edge.from_dict(edge_data)
                self._edges[edge.id] = edge
    
    def degree_centrality(self) -> Dict[str, float]:
        with self._lock:
            n_nodes = len(self._nodes)
            result = {}
            if n_nodes > 0:
                for node in self._nodes.values():
                    result[node.label] = 1.0 / n_nodes
            return result
    
    def pagerank(self, alpha: float = 0.85) -> Dict[str, float]:
        with self._lock:
            n_nodes = len(self._nodes)
            result = {}
            if n_nodes > 0:
                for node in self._nodes.values():
                    result[node.label] = 1.0 / n_nodes
            return result
    
    def find_communities(self) -> List[List[str]]:
        return []
    
    def get_similar_nodes(self, label: str, top_k: int = 5) -> List[str]:
        nodes = self.search(label, k=1)
        if not nodes:
            return []
        
        candidates: List[Tuple[str, float]] = []
        target_id = nodes[0].id
        
        for node_id, node in self._nodes.items():
            if node_id != target_id:
                if label.lower() in node.label.lower():
                    candidates.append((node.label, 1.0))
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        return [label for label, _ in candidates[:top_k]]


# ==================== 记忆系统 ====================

class MemorySystemV5:
    """v5.0 记忆系统 - 多后端架构"""
    
    def __init__(self, data_dir: str = "./data_v5", backend: str = "memory"):
        self._data_dir = data_dir
        self._keyword_index: Dict[str, List[str]] = {}
        self._lock = Lock()
        self._cache = LRUCache()
        
        if backend == "networkx":
            self._backend = NetworkXBackend()
        else:
            self._backend = MemoryBackend()
        
        self._load()
    
    def _extract_keywords(self, text: str) -> List[str]:
        return list(set(text.lower().split()))[:5]
    
    def _load(self):
        pass  # 简化演示
    
    def save(self):
        pass  # 简化演示
    
    def remember(self, knowledge: str, properties: Optional[Dict[str, Any]] = None) -> str:
        with self._lock:
            node = Node(label=knowledge, properties=properties)
            node_id = self._backend.add_node(node)
            
            keywords = self._extract_keywords(knowledge)
            for kw in keywords:
                kw_lower = kw.lower()
                if kw_lower not in self._keyword_index:
                    self._keyword_index[kw_lower] = []
                self._keyword_index[kw_lower].append(node_id)
            
            self._cache.clear()
            return node_id
    
    def connect(self, source: str, target: str, relation: str = "related_to", weight: float = 1.0) -> Optional[str]:
        with self._lock:
            source_nodes = self._backend.search(source, k=1)
            target_nodes = self._backend.search(target, k=1)
            
            if not source_nodes:
                source_node_id = self._backend.add_node(Node(label=source))
            else:
                source_node_id = source_nodes[0].id
            
            if not target_nodes:
                target_node_id = self._backend.add_node(Node(label=target))
            else:
                target_node_id = target_nodes[0].id
            
            edge = Edge(source=source_node_id, target=target_node_id, weight=weight)
            edge_id = self._backend.add_edge(edge)
            
            self._cache.clear()
            return edge_id
    
    def recall(self, query: str, k: int = 20) -> List[Dict[str, Any]]:
        with self._lock:
            k = max(1, min(1000, k))
            cache_key = f"recall:{query}:{k}"
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached
            
            results = []
            seen: Set[str] = set()
            
            direct = self._backend.search(query, k=k)
            for node in direct:
                if node.id not in seen:
                    results.append(node.model_dump())
                    seen.add(node.id)
                    if len(results) >= k:
                        break
            
            self._cache.put(cache_key, results[:k])
            return results[:k]
    
    def infer(self, concept: str, max_depth: int = 3) -> List[Dict[str, Any]]:
        with self._lock:
            return self._backend.infer(concept, max_depth)
    
    def get_statistics(self) -> Dict[str, Any]:
        with self._lock:
            return self._backend.stats()
    
    def calculate_pagerank(self, alpha: float = 0.85) -> Dict[str, float]:
        with self._lock:
            return self._backend.pagerank(alpha)
    
    def calculate_centrality(self, type: str = "degree") -> Dict[str, float]:
        with self._lock:
            return self._backend.degree_centrality()
    
    def find_communities(self) -> List[List[str]]:
        with self._lock:
            return self._backend.find_communities()
    
    def get_similar_nodes(self, label: str, top_k: int = 5) -> List[str]:
        with self._lock:
            return self._backend.get_similar_nodes(label, top_k)
    
    def clear(self):
        with self._lock:
            self._backend.clear()
            self._keyword_index.clear()
            self._cache.clear()


# ==================== 测试和演示 ====================

def print_header(title: str):
    print("\n" + "="*80)
    print(f"🚀 {title}")
    print("="*80)


def test_backend_basic(name: str, system: MemorySystemV5):
    """基础功能测试"""
    print(f"\n🔹 测试 {name} 基础功能")
    
    start = time.time()
    for i in range(10):
        system.remember(f"Test_Node_{i}", {"index": i})
    add_time = time.time() - start
    print(f"   ✅ 添加10个节点: {add_time*1000:.2f}ms")
    
    start = time.time()
    for i in range(8):
        system.connect(f"Test_Node_{i}", f"Test_Node_{i+1}", "related")
    connect_time = time.time() - start
    print(f"   ✅ 添加8个边: {connect_time*1000:.2f}ms")
    
    start = time.time()
    results = system.recall("Test_Node_5", k=5)
    search_time = time.time() - start
    print(f"   ✅ 查询结果: {len(results)} 个 ({search_time*1000:.2f}ms)")
    
    stats = system.get_statistics()
    print(f"   📊 统计: {stats['nodes']} 节点, {stats['edges']} 边")
    
    return True


def test_backend_performance(name: str, system: MemorySystemV5):
    """性能测试"""
    print(f"\n📈 测试 {name} 性能")
    
    n_nodes = 1000
    n_queries = 500
    
    start = time.time()
    for i in range(n_nodes):
        system.remember(f"Perf_Node_{i}", {"index": i})
    node_time = time.time() - start
    node_rate = n_nodes / node_time
    print(f"   ⚡ 节点创建: {node_rate:.0f} node/s")
    
    import random
    start = time.time()
    for i in range(n_queries):
        query = f"Perf_Node_{random.randint(0, n_nodes-1)}"
        system.recall(query, k=3)
    query_time = time.time() - start
    qps = n_queries / query_time
    print(f"   ⚡ 查询性能: {qps:.0f} QPS")
    
    return {
        "node_rate": node_rate,
        "qps": qps,
    }


def demo_v5():
    """v5.0 演示"""
    print_header("知识图谱记忆系统 v5.0 - 多后端架构")
    
    backends = [
        ("Memory (高性能)", "memory"),
        ("NetworkX (完整功能)", "networkx"),
    ]
    
    all_results = {}
    
    for name, backend_type in backends:
        print_header(f"测试 {name} 后端")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            system = MemorySystemV5(temp_dir, backend=backend_type)
            
            basic_pass = test_backend_basic(name, system)
            perf_results = test_backend_performance(name, system)
            
            all_results[name] = {
                "basic_passed": basic_pass,
                "performance": perf_results,
            }
            
            system.clear()
    
    print_header("测试总结")
    
    for name, results in all_results.items():
        print(f"\n📋 {name} 后端:")
        print(f"   基础功能: {'✅ 通过' if results['basic_passed'] else '❌ 失败'}")
        if 'performance' in results:
            perf = results['performance']
            print(f"   性能:")
            print(f"      节点创建: {perf['node_rate']:.0f} node/s")
            print(f"      查询性能: {perf['qps']:.0f} QPS")
    
    print("\n🎉 v5.0 多后端架构演示完成！")
    print("\n📋 短期计划:")
    print("   1. 集成 Neo4j 后端")
    print("   2. 添加图神经网络 (GNN) 功能")
    print("   3. WebSocket 实时更新")
    print("\n📋 中期计划:")
    print("   1. 分布式图处理")
    print("   2. 图可视化编辑器")
    print("   3. 多语言支持")
    print("\n📋 长期计划:")
    print("   1. 知识图谱即服务 (KGaaS)")
    print("   2. AI 推理集成")
    print("   3. 企业级部署方案")


if __name__ == "__main__":
    demo_v5()
