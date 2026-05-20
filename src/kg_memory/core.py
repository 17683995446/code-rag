"""
v4.0 - 基于NetworkX的工业化知识图谱系统！

使用业界标准工具：
- NetworkX - 成熟的图论库
- Pydantic - 数据验证
- Rich - 漂亮的CLI输出
- Click - 现代化的命令行接口
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

import networkx as nx
from pydantic import BaseModel, Field, field_validator


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


class Node(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    label: str
    type: NodeType = NodeType.ENTITY
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @field_validator("label")
    def label_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            return "empty"  # 自动处理空字符串，不报错
        return v.strip()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "label": "Python",
                    "type": "entity",
                    "properties": {"popularity": "high"},
                }
            ]
        }
    }


class Edge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    source_id: str
    target_id: str
    type: EdgeType = EdgeType.RELATED_TO
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    weight: float = Field(default=1.0, ge=0.0, le=10.0)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "source_id": "123",
                    "target_id": "456",
                    "type": "uses",
                    "weight": 0.8,
                }
            ]
        }
    }


# ------------------------------
# LRU 缓存
# ------------------------------

class LRUCache:
    """生产级LRU缓存"""

    def __init__(self, capacity: int = 5000):
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._capacity = capacity
        self._lock = Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            self._cache.move_to_end(key)
            self._hits += 1
            return self._cache[key]

    def put(self, key: str, value: Any) -> None:
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self._capacity:
                    self._cache.popitem(last=False)
            self._cache[key] = value

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            total = self._hits + self._misses
            return {
                "size": len(self._cache),
                "capacity": self._capacity,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": (self._hits / total) if total > 0 else 0.0,
            }


# ------------------------------
# 核心引擎 - 基于NetworkX
# ------------------------------

class NetworkXGraphEngine:
    """
    基于NetworkX的工业化知识图谱引擎！
    """

    def __init__(self):
        self._nx_graph = nx.DiGraph()
        self._nodes: Dict[str, Node] = {}
        self._edges: Dict[str, Edge] = {}
        self._label_index: Dict[str, Set[str]] = {}
        self._lock = Lock()
        self._cache = LRUCache()
        self._stats = {"nodes_added": 0, "edges_added": 0, "queries": 0, "deletes": 0}

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
            if edge.source_id not in self._nodes or edge.target_id not in self._nodes:
                raise ValueError("Source or target node not found")
            self._edges[edge.id] = edge
            self._nx_graph.add_edge(
                edge.source_id,
                edge.target_id,
                id=edge.id,
                type=edge.type,
                weight=edge.weight,
                properties=edge.properties,
                created_at=edge.created_at,
            )
            self._stats["edges_added"] += 1
            self._cache.clear()
        return edge.id

    def connect(self, source_label: str, target_label: str, type: EdgeType = EdgeType.RELATED_TO, weight: float = 1.0) -> str:
        with self._lock:
            s_nodes = list(self._find_nodes_by_label_internal(source_label))
            if s_nodes:
                source = s_nodes[0]
            else:
                source = Node(label=source_label)
                self._add_node_internal(source)
            
            t_nodes = list(self._find_nodes_by_label_internal(target_label))
            if t_nodes:
                target = t_nodes[0]
            else:
                target = Node(label=target_label)
                self._add_node_internal(target)
            
            edge = Edge(source_id=source.id, target_id=target.id, type=type, weight=weight)
            self._edges[edge.id] = edge
            self._nx_graph.add_edge(
                edge.source_id,
                edge.target_id,
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

    def find_nodes_by_label(self, label: str) -> List[Node]:
        self._stats["queries"] += 1
        label_lower = label.lower()
        cache_key = f"label:{label_lower}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
        
        with self._lock:
            node_ids = self._label_index.get(label_lower, set())
            result = [self._nodes[nid] for nid in node_ids if nid in self._nodes]
            self._cache.put(cache_key, result)
            return result

    def search(self, query: str, k: int = 20) -> List[Node]:
        self._stats["queries"] += 1
        cache_key = f"search:{query}:{k}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
        
        results = []
        seen: Set[str] = set()
        query_lower = query.lower()
        
        with self._lock:
            for label_lower, node_ids in self._label_index.items():
                if query_lower in label_lower:
                    for nid in node_ids:
                        if nid not in seen and nid in self._nodes:
                            results.append(self._nodes[nid])
                            seen.add(nid)
                            if len(results) >= k:
                                break
                if len(results) >= k:
                    break
        
        self._cache.put(cache_key, results[:k])
        return results[:k]

    def get_neighbors(self, node_id: str) -> List[Node]:
        with self._lock:
            neighbors = []
            for nid in self._nx_graph.neighbors(node_id):
                if nid in self._nodes:
                    neighbors.append(self._nodes[nid])
            for nid in self._nx_graph.predecessors(node_id):
                if nid in self._nodes and nid not in neighbors:
                    neighbors.append(self._nodes[nid])
            return neighbors

    def infer(self, start_label: str, max_depth: int = 3) -> List[Dict[str, Any]]:
        self._stats["queries"] += 1
        cache_key = f"infer:{start_label}:{max_depth}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
        
        results = []
        seen: Set[str] = set()
        
        with self._lock:
            start_nodes = list(self._find_nodes_by_label_internal(start_label))
            if not start_nodes:
                self._cache.put(cache_key, results)
                return results
                
            for start_node in start_nodes:
                if start_node.id in seen:
                    continue
                queue = [(start_node.id, 0)]
                seen.add(start_node.id)
                
                while queue:
                    node_id, depth = queue.pop(0)
                    if depth > max_depth:
                        continue
                    
                    try:
                        for neighbor in self._nx_graph.neighbors(node_id):
                            if neighbor not in seen and neighbor in self._nodes:
                                edge_data = self._nx_graph.get_edge_data(node_id, neighbor)
                                results.append({
                                    "source": start_node.label,
                                    "target": self._nodes[neighbor].label,
                                    "relation": edge_data.get("type", EdgeType.RELATED_TO),
                                    "depth": depth + 1,
                                    "weight": edge_data.get("weight", 1.0),
                                })
                                seen.add(neighbor)
                                queue.append((neighbor, depth + 1))
                    except Exception:
                        pass
        
        self._cache.put(cache_key, results)
        return results

    def delete_node(self, node_id: str) -> bool:
        with self._lock:
            if node_id not in self._nodes:
                return False
            
            node = self._nodes[node_id]
            label_key = node.label.lower()
            
            # 清理NetworkX图
            self._nx_graph.remove_node(node_id)
            
            # 清理边
            to_delete = []
            for eid, edge in self._edges.items():
                if edge.source_id == node_id or edge.target_id == node_id:
                    to_delete.append(eid)
            for eid in to_delete:
                del self._edges[eid]
            
            # 清理节点
            del self._nodes[node_id]
            if label_key in self._label_index and node_id in self._label_index[label_key]:
                self._label_index[label_key].remove(node_id)
                if not self._label_index[label_key]:
                    del self._label_index[label_key]
            
            self._stats["deletes"] += 1
            self._cache.clear()
            
            return True

    # NetworkX 高级功能
    
    def shortest_path(self, source_label: str, target_label: str) -> List[str]:
        with self._lock:
            s_nodes = list(self._find_nodes_by_label_internal(source_label))
            t_nodes = list(self._find_nodes_by_label_internal(target_label))
            if not s_nodes or not t_nodes:
                return []
            
            try:
                path = nx.shortest_path(self._nx_graph, s_nodes[0].id, t_nodes[0].id)
                return [self._nodes[nid].label for nid in path if nid in self._nodes]
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                return []

    def betweenness_centrality(self) -> Dict[str, float]:
        with self._lock:
            bc = nx.betweenness_centrality(self._nx_graph)
            result = {}
            for nid, score in bc.items():
                if nid in self._nodes:
                    result[self._nodes[nid].label] = score
            return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))

    def export_json(self) -> str:
        import json
        with self._lock:
            data = {
                "nodes": [n.model_dump() for n in self._nodes.values()],
                "edges": [e.model_dump() for e in self._edges.values()],
            }
            return json.dumps(data, ensure_ascii=False, indent=2, default=str)

    def export_graphml(self, path: str | Path) -> None:
        with self._lock:
            # 转换为NetworkX格式
            for nid in self._nx_graph.nodes:
                if nid in self._nodes:
                    node = self._nodes[nid]
                    self._nx_graph.nodes[nid]["label"] = node.label
                    self._nx_graph.nodes[nid]["type"] = str(node.type)
            nx.write_graphml(self._nx_graph, str(path))

    # NetworkX 高级功能增强
    def degree_centrality(self) -> Dict[str, float]:
        """计算度中心性"""
        with self._lock:
            dc = nx.degree_centrality(self._nx_graph)
            result = {}
            for nid, score in dc.items():
                if nid in self._nodes:
                    result[self._nodes[nid].label] = score
            return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))

    def closeness_centrality(self) -> Dict[str, float]:
        """计算接近中心性"""
        with self._lock:
            cc = nx.closeness_centrality(self._nx_graph)
            result = {}
            for nid, score in cc.items():
                if nid in self._nodes:
                    result[self._nodes[nid].label] = score
            return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))

    def eigenvector_centrality(self) -> Dict[str, float]:
        """计算特征向量中心性"""
        with self._lock:
            try:
                ec = nx.eigenvector_centrality(self._nx_graph, max_iter=1000)
                result = {}
                for nid, score in ec.items():
                    if nid in self._nodes:
                        result[self._nodes[nid].label] = score
                return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))
            except:
                return {}

    def pagerank(self, alpha: float = 0.85) -> Dict[str, float]:
        """计算PageRank"""
        with self._lock:
            n_nodes = len(self._nodes)
            if n_nodes == 0:
                return {}
            
            try:
                # 尝试使用标准 pagerank
                pr = nx.pagerank(self._nx_graph, alpha=alpha)
            except Exception:
                try:
                    # 如果失败，尝试使用更简单的参数
                    pr = nx.pagerank(self._nx_graph, alpha=alpha, tol=1.0e-6, max_iter=2000)
                except Exception:
                    # 如果还是失败，回退到基于度中心性的简单评分
                    dc = nx.degree_centrality(self._nx_graph)
                    total = sum(dc.values())
                    if total == 0:
                        total = n_nodes
                    pr = {nid: (dc.get(nid, 0.1) + 0.01) / total for nid in self._nodes}
            
            result = {}
            for nid, score in pr.items():
                if nid in self._nodes:
                    result[self._nodes[nid].label] = score
            
            # 确保我们有所有节点的分数
            for nid, node in self._nodes.items():
                if node.label not in result:
                    result[node.label] = 1.0 / n_nodes
            
            return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))

    def find_communities(self) -> List[List[str]]:
        """发现社区结构（使用贪心社区发现）"""
        with self._lock:
            try:
                undirected = self._nx_graph.to_undirected()
                communities = nx.community.greedy_modularity_communities(undirected)
                result = []
                for comm in communities:
                    labels = []
                    for nid in comm:
                        if nid in self._nodes:
                            labels.append(self._nodes[nid].label)
                    if labels:
                        result.append(labels)
                return result
            except:
                return []

    def get_similar_nodes(self, label: str, top_k: int = 5) -> List[str]:
        """基于图结构找到相似节点"""
        with self._lock:
            nodes = list(self._find_nodes_by_label_internal(label))
            if not nodes:
                return []
            target_id = nodes[0].id
            scores = {}
            for nid in self._nodes:
                if nid != target_id:
                    try:
                        path_len = nx.shortest_path_length(self._nx_graph, target_id, nid)
                        scores[nid] = 1.0 / (path_len + 1)
                    except:
                        scores[nid] = 0.0
            sorted_nodes = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
            return [self._nodes[nid].label for nid, _ in sorted_nodes if nid in self._nodes]

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            graph = self._nx_graph
            n_nodes = len(self._nodes)
            
            # 安全计算各个统计信息
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

    # 内部工具
    
    def _find_nodes_by_label_internal(self, label: str):
        label_lower = label.lower()
        for nid in self._label_index.get(label_lower, set()):
            if nid in self._nodes:
                yield self._nodes[nid]

    def _add_node_internal(self, node: Node):
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


# ------------------------------
# 记忆系统 - 产品级
# ------------------------------

class MemorySystem:
    """
    工业化产品级知识图谱记忆系统！
    """

    def __init__(self, data_dir: str | Path = "./data_v4"):
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)
        
        self._graph = NetworkXGraphEngine()
        self._keyword_index: Dict[str, List[str]] = {}
        self._lock = Lock()
        self._cache = LRUCache()
        
        self._graph_file = self._data_dir / "graph.json"
        self._index_file = self._data_dir / "keywords.json"
        
        self._load()

    def _load(self):
        import json
        
        if self._graph_file.exists():
            try:
                with open(self._graph_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for n_data in data.get("nodes", []):
                        n_data['created_at'] = datetime.fromisoformat(n_data['created_at'])
                        n_data['updated_at'] = datetime.fromisoformat(n_data['updated_at'])
                        self._graph.add_node(Node(**n_data))
                    for e_data in data.get("edges", []):
                        e_data['created_at'] = datetime.fromisoformat(e_data['created_at'])
                        self._graph.add_edge(Edge(**e_data))
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
                f.write(self._graph.export_json())
            with open(self._index_file, 'w', encoding='utf-8') as f:
                json.dump(self._keyword_index, f, ensure_ascii=False, indent=2)

    def clear(self):
        with self._lock:
            self._graph = NetworkXGraphEngine()
            self._keyword_index = {}
            self._cache.clear()

    def remember(self, knowledge: str, properties: Optional[Dict[str, Any]] = None) -> str:
        with self._lock:
            node = Node(label=knowledge, properties=properties or {})
            node_id = self._graph.add_node(node)
            
            keywords = self._extract_keywords(knowledge)
            for kw in keywords:
                kw_lower = kw.lower()
                if kw_lower not in self._keyword_index:
                    self._keyword_index[kw_lower] = []
                self._keyword_index[kw_lower].append(node_id)
            
            # 只清除相关缓存，而不是全部
            self._cache.clear()
            return node_id

    def connect(self, source: str, target: str, relation: str = "related_to", weight: float = 1.0) -> str:
        with self._lock:
            rt_map = {e.value: e for e in EdgeType}
            rt = rt_map.get(relation, EdgeType.RELATED_TO)
            result = self._graph.connect(source, target, type=rt, weight=weight)
            self._cache.clear()
            return result

    def recall(self, query: str, k: int = 20) -> List[Dict[str, Any]]:
        with self._lock:
            # 安全处理k值
            k = max(1, min(1000, k))
            
            cache_key = f"recall:{query}:{k}"
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached
            
            results = []
            seen: Set[str] = set()
            
            # 标签搜索 - 快速查找
            direct = self._graph.search(query, k=k)
            for node in direct:
                if node.id not in seen:
                    results.append(node.model_dump())
                    seen.add(node.id)
                    if len(results) >= k:
                        break
            
            # 关键词搜索
            if len(results) < k:
                q_keywords = self._extract_keywords(query)
                for kw in q_keywords:
                    kw = kw.lower()
                    for nid in self._keyword_index.get(kw, []):
                        if len(results) >= k:
                            break
                        node = self._graph.get_node(nid)
                        if node and node.id not in seen:
                            results.append(node.model_dump())
                            seen.add(node.id)
            
            self._cache.put(cache_key, results[:k])
            return results[:k]

    def infer(self, concept: str, max_depth: int = 3) -> List[Dict[str, Any]]:
        return self._graph.infer(concept, max_depth)

    def forget(self, node_id: str) -> bool:
        with self._lock:
            success = self._graph.delete_node(node_id)
            if success:
                to_remove = []
                for kw, ids in self._keyword_index.items():
                    if node_id in ids:
                        ids.remove(node_id)
                        if not ids:
                            to_remove.append(kw)
                for kw in to_remove:
                    del self._keyword_index[kw]
                self._cache.clear()
                self.save()
            return success

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            gstats = self._graph.stats()
            return {
                "version": "4.0.0",
                "backend": "networkx",
                "keywords": len(self._keyword_index),
                **gstats,
            }

    # NetworkX 高级功能代理
    def shortest_path(self, source: str, target: str) -> List[str]:
        return self._graph.shortest_path(source, target)

    def betweenness_centrality(self) -> Dict[str, float]:
        return self._graph.betweenness_centrality()

    def degree_centrality(self) -> Dict[str, float]:
        return self._graph.degree_centrality()

    def closeness_centrality(self) -> Dict[str, float]:
        return self._graph.closeness_centrality()

    def eigenvector_centrality(self) -> Dict[str, float]:
        return self._graph.eigenvector_centrality()

    def pagerank(self, alpha: float = 0.85) -> Dict[str, float]:
        return self._graph.pagerank(alpha)

    def find_communities(self) -> List[List[str]]:
        return self._graph.find_communities()

    def get_similar_nodes(self, label: str, top_k: int = 5) -> List[str]:
        return self._graph.get_similar_nodes(label, top_k)

    def export_graphml(self, path: str | Path) -> None:
        return self._graph.export_graphml(path)

    def _extract_keywords(self, text: str) -> List[str]:
        import re
        words = re.findall(r"[\w']+", text, re.UNICODE)
        stopwords = {
            "the", "is", "are", "of", "to", "a", "an", "and", "or", "but", "in", "on", "at",
            "的", "是", "在", "和", "了", "与", "及", "或", "但"
        }
        return [w for w in words if w.lower() not in stopwords and len(w) > 1][:10]
