"""
v5.0 - 知识图谱记忆系统 - 多后端架构！

创新升级：
- 多后端抽象层（NetworkX, Neo4j, 内存）
- 可插拔架构
- 高性能设计
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from uuid import uuid4


# ------------------------------
# 核心数据模型
# ------------------------------

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
    id: str
    label: str
    type: NodeType
    properties: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    def __init__(self, label: str, properties: Optional[Dict[str, Any]] = None, 
                 type: NodeType = NodeType.ENTITY,
                 id: Optional[str] = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
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
    id: str
    source: str
    target: str
    type: EdgeType
    weight: float
    properties: Dict[str, Any]
    created_at: datetime
    
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


# ------------------------------
# 缓存系统
# ------------------------------

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


# ------------------------------
# 多后端抽象层
# ------------------------------

class GraphBackend(ABC):
    """图数据库后端的抽象接口"""
    
    @abstractmethod
    def add_node(self, node: Node) -> str:
        """添加节点，返回节点ID"""
        pass
    
    @abstractmethod
    def add_edge(self, edge: Edge) -> str:
        """添加边，返回边ID"""
        pass
    
    @abstractmethod
    def get_node(self, node_id: str) -> Optional[Node]:
        """获取节点"""
        pass
    
    @abstractmethod
    def get_edge(self, edge_id: str) -> Optional[Edge]:
        """获取边"""
        pass
    
    @abstractmethod
    def search(self, query: str, k: int = 20) -> List[Node]:
        """搜索节点"""
        pass
    
    @abstractmethod
    def delete_node(self, node_id: str):
        """删除节点"""
        pass
    
    @abstractmethod
    def get_neighbors(self, node_id: str) -> List[Tuple[Node, Edge]]:
        """获取邻居"""
        pass
    
    @abstractmethod
    def shortest_path(self, source: str, target: str) -> Optional[List[str]]:
        """最短路径"""
        pass
    
    @abstractmethod
    def infer(self, start_label: str, max_depth: int = 3) -> List[Dict[str, Any]]:
        """推理"""
        pass
    
    @abstractmethod
    def stats(self) -> Dict[str, Any]:
        """统计信息"""
        pass
    
    @abstractmethod
    def clear(self):
        """清空图"""
        pass
    
    @abstractmethod
    def export_json(self) -> str:
        """导出JSON"""
        pass
    
    @abstractmethod
    def import_json(self, json_str: str):
        """导入JSON"""
        pass
    
    @abstractmethod
    def degree_centrality(self) -> Dict[str, float]:
        """度中心性"""
        pass
    
    @abstractmethod
    def betweenness_centrality(self) -> Dict[str, float]:
        """介数中心性"""
        pass
    
    @abstractmethod
    def closeness_centrality(self) -> Dict[str, float]:
        """接近中心性"""
        pass
    
    @abstractmethod
    def pagerank(self, alpha: float = 0.85) -> Dict[str, float]:
        """PageRank"""
        pass
    
    @abstractmethod
    def find_communities(self) -> List[List[str]]:
        """社区发现"""
        pass
    
    @abstractmethod
    def get_similar_nodes(self, label: str, top_k: int = 5) -> List[str]:
        """相似节点"""
        pass


# ------------------------------
# NetworkX 后端
# ------------------------------

class NetworkXBackend(GraphBackend):
    """NetworkX 图数据库后端"""
    
    def __init__(self):
        import networkx as nx
        self._nx_graph = nx.DiGraph()
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
            self._nx_graph.add_node(
                node.id,
                label=node.label,
                type=node.type,
                created_at=node.created_at,
                properties=node.properties,
            )
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
            self._nx_graph.add_edge(
                edge.source,
                edge.target,
                id=edge.id,
                type=edge.type,
                weight=edge.weight,
                properties=edge.properties,
            )
            self._stats["edges_added"] += 1
            self._cache.clear()
            return edge.id
    
    def get_node(self, node_id: str) -> Optional[Node]:
        with self._lock:
            return self._nodes.get(node_id)
    
    def get_edge(self, edge_id: str) -> Optional[Edge]:
        with self._lock:
            return self._edges.get(edge_id)
    
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
                if self._nx_graph.has_node(node_id):
                    self._nx_graph.remove_node(node_id)
                for label_key in list(self._label_index.keys()):
                    self._label_index[label_key].discard(node_id)
                self._stats["nodes_deleted"] += 1
                self._cache.clear()
    
    def get_neighbors(self, node_id: str) -> List[Tuple[Node, Edge]]:
        with self._lock:
            neighbors: List[Tuple[Node, Edge]] = []
            if node_id in self._nodes:
                for neighbor_id in self._nx_graph.neighbors(node_id):
                    edge_data = self._nx_graph.get_edge_data(node_id, neighbor_id)
                    edge_id = edge_data.get("id")
                    if edge_id in self._edges:
                        if neighbor_id in self._nodes:
                            neighbors.append((self._nodes[neighbor_id], self._edges[edge_id]))
            return neighbors
    
    def shortest_path(self, source: str, target: str) -> Optional[List[str]]:
        import networkx as nx
        with self._lock:
            try:
                path = nx.shortest_path(self._nx_graph, source, target)
                return path
            except:
                return None
    
    def infer(self, start_label: str, max_depth: int = 3) -> List[Dict[str, Any]]:
        import networkx as nx
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
                    
                    for neighbor_id in self._nx_graph.neighbors(current_id):
                        if neighbor_id not in seen and neighbor_id in self._nodes:
                            edge_data = self._nx_graph.get_edge_data(current_id, neighbor_id)
                            edge_id = edge_data.get("id")
                            if edge_id in self._edges:
                                edge = self._edges[edge_id]
                                if start_id in self._nodes:
                                    results.append({
                                        "source": self._nodes[start_id].label,
                                        "target": self._nodes[neighbor_id].label,
                                        "relation": edge.type.value,
                                        "depth": depth + 1,
                                        "weight": edge.weight,
                                    })
                                seen.add(neighbor_id)
                                queue.append((neighbor_id, depth + 1))
            
            return results
    
    def stats(self) -> Dict[str, Any]:
        import networkx as nx
        with self._lock:
            n_nodes = len(self._nodes)
            graph = self._nx_graph
            
            density = nx.density(graph) if n_nodes > 0 else 0.0
            
            try:
                connected_components = nx.number_weakly_connected_components(graph) if n_nodes > 0 else 0
            except:
                connected_components = n_nodes if n_nodes > 0 else 0
                
            try:
                avg_clustering = nx.average_clustering(graph.to_undirected()) if n_nodes > 0 else 0
            except:
                avg_clustering = 0.0
                
            try:
                if n_nodes == 0:
                    diameter = "N/A"
                else:
                    undirected = graph.to_undirected()
                    diameter = nx.diameter(undirected) if nx.is_connected(undirected) else "N/A"
            except:
                diameter = "N/A"
            
            return {
                "nodes": n_nodes,
                "edges": len(self._edges),
                "density": density,
                "connected_components": connected_components,
                "average_clustering": avg_clustering,
                "diameter": diameter,
                **self._stats,
                "cache": self._cache.stats(),
            }
    
    def clear(self):
        with self._lock:
            import networkx as nx
            self._nx_graph = nx.DiGraph()
            self._nodes.clear()
            self._edges.clear()
            self._label_index.clear()
            self._stats = {
                "nodes_added": 0,
                "edges_added": 0,
                "nodes_deleted": 0,
                "searches": 0,
            }
            self._cache.clear()
    
    def export_json(self) -> str:
        import json
        with self._lock:
            data = {
                "nodes": [node.model_dump() for node in self._nodes.values()],
                "edges": [edge.model_dump() for edge in self._edges.values()],
            }
            return json.dumps(data, ensure_ascii=False, indent=2)
    
    def import_json(self, json_str: str):
        import json
        with self._lock:
            data = json.loads(json_str)
            for node_data in data.get("nodes", []):
                node = Node.from_dict(node_data)
                self.add_node(node)
            for edge_data in data.get("edges", []):
                edge = Edge.from_dict(edge_data)
                self.add_edge(edge)
    
    def degree_centrality(self) -> Dict[str, float]:
        import networkx as nx
        with self._lock:
            try:
                centrality = nx.degree_centrality(self._nx_graph)
                result = {}
                for node_id, score in centrality.items():
                    if node_id in self._nodes:
                        result[self._nodes[node_id].label] = score
                return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))
            except:
                return {}
    
    def betweenness_centrality(self) -> Dict[str, float]:
        import networkx as nx
        with self._lock:
            try:
                centrality = nx.betweenness_centrality(self._nx_graph)
                result = {}
                for node_id, score in centrality.items():
                    if node_id in self._nodes:
                        result[self._nodes[node_id].label] = score
                return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))
            except:
                return {}
    
    def closeness_centrality(self) -> Dict[str, float]:
        import networkx as nx
        with self._lock:
            try:
                centrality = nx.closeness_centrality(self._nx_graph)
                result = {}
                for node_id, score in centrality.items():
                    if node_id in self._nodes:
                        result[self._nodes[node_id].label] = score
                return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))
            except:
                return {}
    
    def eigenvector_centrality(self) -> Dict[str, float]:
        import networkx as nx
        with self._lock:
            n_nodes = len(self._nodes)
            if n_nodes == 0:
                return {}
            
            try:
                centrality = nx.eigenvector_centrality(self._nx_graph, max_iter=1000)
                result = {}
                for node_id, score in centrality.items():
                    if node_id in self._nodes:
                        result[self._nodes[node_id].label] = score
                return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))
            except:
                try:
                    dc = nx.degree_centrality(self._nx_graph)
                    total = sum(dc.values()) if sum(dc.values()) > 0 else n_nodes
                    result = {}
                    for node_id in self._nodes:
                        result[self._nodes[node_id].label] = (dc.get(node_id, 0.1) + 0.01) / total
                    return result
                except:
                    return {}
    
    def pagerank(self, alpha: float = 0.85) -> Dict[str, float]:
        import networkx as nx
        with self._lock:
            n_nodes = len(self._nodes)
            if n_nodes == 0:
                return {}
            
            try:
                pr = nx.pagerank(self._nx_graph, alpha=alpha)
            except:
                try:
                    pr = nx.pagerank(self._nx_graph, alpha=alpha, tol=1.0e-6, max_iter=1000)
                except:
                    dc = nx.degree_centrality(self._nx_graph)
                    total = sum(dc.values()) if sum(dc.values()) > 0 else n_nodes
                    pr = {nid: (dc.get(nid, 0.1) + 0.01) / total for nid in self._nodes}
            
            result = {}
            for node_id, score in pr.items():
                if node_id in self._nodes:
                    result[self._nodes[node_id].label] = score
            
            for node_id, node in self._nodes.items():
                if node.label not in result:
                    result[node.label] = 1.0 / n_nodes
            
            return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))
    
    def find_communities(self) -> List[List[str]]:
        import networkx as nx
        with self._lock:
            try:
                undirected = self._nx_graph.to_undirected()
                communities = nx.community.greedy_modularity_communities(undirected)
                result = []
                for community in communities:
                    labels = []
                    for node_id in community:
                        if node_id in self._nodes:
                            labels.append(self._nodes[node_id].label)
                    if labels:
                        result.append(labels)
                return result
            except:
                return []
    
    def get_similar_nodes(self, label: str, top_k: int = 5) -> List[str]:
        import networkx as nx
        with self._lock:
            nodes = self.search(label, k=1)
            if not nodes:
                return []
            target_id = nodes[0].id
            
            scores: Dict[str, float] = {}
            for node_id in self._nodes:
                if node_id != target_id:
                    try:
                        path_len = nx.shortest_path_length(self._nx_graph, target_id, node_id)
                        scores[node_id] = 1.0 / (path_len + 1)
                    except:
                        scores[node_id] = 0.0
            
            sorted_nodes = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
            return [self._nodes[nid].label for nid, _ in sorted_nodes if nid in self._nodes]


# ------------------------------
# 内存后端（高性能）
# ------------------------------

class MemoryBackend(GraphBackend):
    """纯内存图数据库后端 - 极高性能"""
    
    def __init__(self):
        self._nodes: Dict[str, Node] = {}
        self._edges: Dict[str, Edge] = {}
        self._adjacency: Dict[str, Dict[str, Edge]] = {}  # {source: {target: Edge}}
        self._reverse_adjacency: Dict[str, Dict[str, Edge]] = {}  # {target: {source: Edge}}
        self._label_index: Dict[str, Set[str]] = {}
        self._lock = Lock()
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
            return edge.id
    
    def get_node(self, node_id: str) -> Optional[Node]:
        with self._lock:
            return self._nodes.get(node_id)
    
    def get_edge(self, edge_id: str) -> Optional[Edge]:
        with self._lock:
            return self._edges.get(edge_id)
    
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
                for target in list(self._adjacency.get(node_id, {}).keys()):
                    edge = self._adjacency[node_id].pop(target)
                    if edge.id in self._edges:
                        del self._edges[edge.id]
                    self._reverse_adjacency[target].pop(node_id, None)
                for source in list(self._reverse_adjacency.get(node_id, {}).keys()):
                    edge = self._reverse_adjacency[node_id].pop(source)
                    if edge.id in self._edges:
                        del self._edges[edge.id]
                    self._adjacency[source].pop(node_id, None)
                self._adjacency.pop(node_id, None)
                self._reverse_adjacency.pop(node_id, None)
                for label_key in list(self._label_index.keys()):
                    self._label_index[label_key].discard(node_id)
                self._stats["nodes_deleted"] += 1
    
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
                                        "relation": edge.type.value,
                                        "depth": depth + 1,
                                        "weight": edge.weight,
                                    })
                                seen.add(neighbor_id)
                                queue.append((neighbor_id, depth + 1))
            
            return results
    
    def stats(self) -> Dict[str, Any]:
        with self._lock:
            n_nodes = len(self._nodes)
            n_edges = len(self._edges)
            density = 0.0
            if n_nodes > 1:
                density = n_edges / (n_nodes * (n_nodes - 1))
            
            return {
                "nodes": n_nodes,
                "edges": n_edges,
                "density": density,
                "connected_components": "N/A",
                "average_clustering": "N/A",
                "diameter": "N/A",
                **self._stats,
                "cache": {"note": "MemoryBackend has no cache"},
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
    
    def export_json(self) -> str:
        import json
        with self._lock:
            data = {
                "nodes": [node.model_dump() for node in self._nodes.values()],
                "edges": [edge.model_dump() for edge in self._edges.values()],
            }
            return json.dumps(data, ensure_ascii=False, indent=2)
    
    def import_json(self, json_str: str):
        import json
        with self._lock:
            data = json.loads(json_str)
            for node_data in data.get("nodes", []):
                node = Node.from_dict(node_data)
                self.add_node(node)
            for edge_data in data.get("edges", []):
                edge = Edge.from_dict(edge_data)
                self.add_edge(edge)
    
    def degree_centrality(self) -> Dict[str, float]:
        with self._lock:
            n_nodes = len(self._nodes)
            if n_nodes <= 1:
                return {}
            
            centrality = {}
            for node_id, node in self._nodes.items():
                degree = len(self._adjacency.get(node_id, {})) + len(self._reverse_adjacency.get(node_id, {}))
                centrality[node.label] = degree / (n_nodes - 1)
            
            return dict(sorted(centrality.items(), key=lambda x: x[1], reverse=True))
    
    def betweenness_centrality(self) -> Dict[str, float]:
        return {}
    
    def closeness_centrality(self) -> Dict[str, float]:
        return {}
    
    def pagerank(self, alpha: float = 0.85) -> Dict[str, float]:
        with self._lock:
            n_nodes = len(self._nodes)
            if n_nodes == 0:
                return {}
            result = {}
            for node in self._nodes.values():
                result[node.label] = 1.0 / n_nodes
            return result
    
    def find_communities(self) -> List[List[str]]:
        return []
    
    def get_similar_nodes(self, label: str, top_k: int = 5) -> List[str]:
        with self._lock:
            nodes = self.search(label, k=1)
            if not nodes:
                return []
            target_id = nodes[0].id
            
            candidates: List[Tuple[str, float]] = []
            for node_id, node in self._nodes.items():
                if node_id != target_id:
                    common = 0
                    if target_id in self._adjacency and node_id in self._adjacency:
                        common = len(set(self._adjacency[target_id].keys()) & set(self._adjacency[node_id].keys()))
                    candidates.append((node.label, common))
            
            candidates.sort(key=lambda x: x[1], reverse=True)
            return [label for label, _ in candidates[:top_k]]


# ------------------------------
# 后端工厂
# ------------------------------

class BackendType(str, Enum):
    NETWORKX = "networkx"
    MEMORY = "memory"
    NEO4J = "neo4j"


class GraphBackendFactory:
    """图后端工厂"""
    
    @staticmethod
    def create_backend(backend_type: BackendType, config: Optional[Dict[str, Any]] = None) -> GraphBackend:
        """创建后端实例"""
        config = config or {}
        
        if backend_type == BackendType.NETWORKX:
            return NetworkXBackend()
        elif backend_type == BackendType.MEMORY:
            return MemoryBackend()
        elif backend_type == BackendType.NEO4J:
            # Neo4j 后端可以后续实现
            return NetworkXBackend()  # 降级到 NetworkX
        else:
            return NetworkXBackend()


# ------------------------------
# 记忆系统
# ------------------------------

class MemorySystem:
    """增强版记忆系统 - 支持多后端"""
    
    def __init__(self, data_dir: str | Path = "./data_v5", backend_type: BackendType = BackendType.NETWORKX):
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)
        
        self._backend = GraphBackendFactory.create_backend(backend_type)
        self._keyword_index: Dict[str, List[str]] = {}
        self._lock = Lock()
        self._cache = LRUCache()
        
        self._graph_file = self._data_dir / "graph.json"
        self._index_file = self._data_dir / "keywords.json"
        
        self._load()
    
    def _extract_keywords(self, text: str) -> List[str]:
        """简单的关键词提取"""
        words = text.lower().split()
        words.extend([c for c in text.lower() if len(c) > 1])
        return list(set(words))[:5]
    
    def _load(self):
        import json
        if self._graph_file.exists():
            try:
                with open(self._graph_file, 'r', encoding='utf-8') as f:
                    self._backend.import_json(f.read())
            except Exception as e:
                print(f"Load graph error: {e}")
        
        if self._index_file.exists():
            try:
                with open(self._index_file, 'r', encoding='utf-8') as f:
                    self._keyword_index = json.load(f)
            except Exception as e:
                print(f"Load index error: {e}")
    
    def save(self):
        with self._lock:
            import json
            with open(self._graph_file, 'w', encoding='utf-8') as f:
                f.write(self._backend.export_json())
            with open(self._index_file, 'w', encoding='utf-8') as f:
                json.dump(self._keyword_index, f, ensure_ascii=False, indent=2)
    
    def clear(self):
        with self._lock:
            self._backend.clear()
            self._keyword_index.clear()
            self._cache.clear()
    
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
            
            rt_map = {e.value: e for e in EdgeType}
            rt = rt_map.get(relation, EdgeType.RELATED_TO)
            
            edge = Edge(
                source=source_node_id,
                target=target_node_id,
                type=rt,
                weight=weight,
            )
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
            
            if len(results) < k:
                q_keywords = self._extract_keywords(query)
                for kw in q_keywords:
                    kw = kw.lower()
                    for nid in self._keyword_index.get(kw, []):
                        if len(results) >= k:
                            break
                        node = self._backend.get_node(nid)
                        if node and node.id not in seen:
                            results.append(node.model_dump())
                            seen.add(node.id)
            
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
            if type == "degree":
                return self._backend.degree_centrality()
            elif type == "betweenness":
                return self._backend.betweenness_centrality()
            elif type == "closeness":
                return self._backend.closeness_centrality()
            return {}
    
    def find_communities(self) -> List[List[str]]:
        with self._lock:
            return self._backend.find_communities()
    
    def get_similar_nodes(self, label: str, top_k: int = 5) -> List[str]:
        with self._lock:
            return self._backend.get_similar_nodes(label, top_k)
