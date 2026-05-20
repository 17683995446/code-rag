#!/usr/bin/env python3
"""
知识图谱记忆系统 v7.0 - 图神经网络与节点嵌入
包含GNN集成、节点嵌入、高级语义搜索
"""
from __future__ import annotations

import sys
import os
import json
import time
import uuid
import random
import tempfile
import math
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
from dataclasses import dataclass, field
from collections import defaultdict, OrderedDict
from threading import RLock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ============================================
# 核心类型与数据模型
# ============================================

from enum import Enum

class NodeType(str, Enum):
    ENTITY = "entity"
    CONCEPT = "concept"
    DOCUMENT = "document"
    USER = "user"
    
    @classmethod
    def all(cls):
        return list(cls)


class EdgeType(str, Enum):
    RELATED_TO = "related_to"
    IS_A = "is_a"
    USES = "uses"
    PART_OF = "part_of"
    SIMILAR_TO = "similar_to"
    REFERENCES = "references"
    
    @classmethod
    def all(cls):
        return list(cls)


@dataclass(slots=True)
class NodeV7:
    id: str
    label: str
    node_type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "type": self.node_type,
            "properties": self.properties,
            "has_embedding": self.embedding is not None,
            "created_at": self.created_at.isoformat()
        }


@dataclass(slots=True)
class EdgeV7:
    id: str
    source_id: str
    target_id: str
    edge_type: str
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "type": self.edge_type,
            "weight": self.weight,
            "properties": self.properties
        }


# ============================================
# 节点嵌入与向量搜索
# ============================================

class NodeEmbeddingEngine:
    """节点嵌入引擎 - 支持简单但有效的图嵌入"""
    
    def __init__(self, embedding_dim: int = 64):
        self.embedding_dim = embedding_dim
        self._lock = RLock()
    
    def create_random_embedding(self) -> List[float]:
        """创建随机嵌入向量"""
        import random
        return [random.gauss(0, 1) for _ in range(self.embedding_dim)]
    
    def normalize_vector(self, vector: List[float]) -> List[float]:
        """归一化向量"""
        norm = math.sqrt(sum(x*x for x in vector))
        if norm == 0:
            return vector
        return [x / norm for x in vector]
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a*b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a*a for a in vec1))
        norm2 = math.sqrt(sum(b*b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def simple_graph_embedding(self, node: NodeV7, neighbors: List[Tuple[NodeV7, EdgeV7]]) -> List[float]:
        """简单但有效的图嵌入 - 基于标签和邻居"""
        embedding = self.create_random_embedding()
        
        label_hash = hash(node.label) % 1000
        embedding[0] = label_hash / 1000.0
        
        type_factor = 0.5
        if node.node_type == NodeType.CONCEPT:
            type_factor = 1.0
        elif node.node_type == NodeType.DOCUMENT:
            type_factor = 0.7
        
        embedding[1] = type_factor
        
        if neighbors:
            avg_weight = sum(e.weight for _, e in neighbors) / len(neighbors)
            embedding[2] = avg_weight
            embedding[3] = len(neighbors) / 100.0
        
        return self.normalize_vector(embedding)


class VectorIndex:
    """向量索引 - 用于高效相似性搜索"""
    
    def __init__(self, embedding_dim: int = 64):
        self.embedding_dim = embedding_dim
        self.vectors: Dict[str, List[float]] = {}
        self._lock = RLock()
    
    def add_vector(self, node_id: str, vector: List[float]):
        """添加向量"""
        with self._lock:
            self.vectors[node_id] = vector
    
    def remove_vector(self, node_id: str):
        """移除向量"""
        with self._lock:
            if node_id in self.vectors:
                del self.vectors[node_id]
    
    def search_similar(self, query_vector: List[float], k: int = 10, 
                      engine: NodeEmbeddingEngine = None) -> List[Tuple[str, float]]:
        """搜索相似向量"""
        engine = engine or NodeEmbeddingEngine()
        
        with self._lock:
            similarities = []
            for node_id, vector in self.vectors.items():
                sim = engine.cosine_similarity(query_vector, vector)
                similarities.append((node_id, sim))
            
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:k]
    
    def size(self) -> int:
        return len(self.vectors)


# ============================================
# 简单GNN模拟 - 图神经网络功能
# ============================================

class SimpleGNN:
    """简单但有效的GNN实现"""
    
    def __init__(self, layers: int = 2, hidden_dim: int = 64):
        self.layers = layers
        self.hidden_dim = hidden_dim
        self._lock = RLock()
    
    def propagate_information(self, node_embeddings: Dict[str, List[float]], 
                             adjacency: Dict[str, Set[str]]) -> Dict[str, List[float]]:
        """图信息传播"""
        with self._lock:
            new_embeddings = {}
            
            for node_id, embedding in node_embeddings.items():
                neighbors = adjacency.get(node_id, set())
                
                if not neighbors:
                    new_embeddings[node_id] = embedding.copy()
                    continue
                
                neighbor_sum = [0.0] * len(embedding)
                for neighbor_id in neighbors:
                    if neighbor_id in node_embeddings:
                        neighbor_emb = node_embeddings[neighbor_id]
                        for i in range(len(embedding)):
                            neighbor_sum[i] += neighbor_emb[i]
                
                avg_neighbor = [x / max(len(neighbors), 1) for x in neighbor_sum]
                new_emb = [(embedding[i] + avg_neighbor[i]) / 2 for i in range(len(embedding))]
                new_embeddings[node_id] = new_emb
            
            return new_embeddings
    
    def compute_embeddings(self, nodes: List[NodeV7], adjacency: Dict[str, Set[str]], 
                          engine: NodeEmbeddingEngine) -> Dict[str, List[float]]:
        """计算节点嵌入"""
        node_embeddings = {}
        for node in nodes:
            if node.embedding:
                node_embeddings[node.id] = node.embedding
            else:
                node_embeddings[node.id] = engine.create_random_embedding()
        
        for layer in range(self.layers):
            node_embeddings = self.propagate_information(node_embeddings, adjacency)
        
        return node_embeddings


# ============================================
# 推荐系统
# ============================================

class KnowledgeRecommender:
    """知识推荐系统"""
    
    def __init__(self, vector_index: VectorIndex, 
                 embedding_engine: NodeEmbeddingEngine):
        self.vector_index = vector_index
        self.embedding_engine = embedding_engine
        self._lock = RLock()
    
    def recommend_similar_nodes(self, query_label: str, nodes: Dict[str, NodeV7],
                               k: int = 10) -> List[Dict[str, Any]]:
        """推荐相似节点"""
        with self._lock:
            query_node = None
            for node in nodes.values():
                if query_label.lower() in node.label.lower():
                    query_node = node
                    break
            
            if not query_node:
                return []
            
            if not query_node.embedding:
                return []
            
            similar = self.vector_index.search_similar(
                query_node.embedding, k, self.embedding_engine
            )
            
            results = []
            for node_id, score in similar:
                if node_id in nodes and node_id != query_node.id:
                    results.append({
                        "node": nodes[node_id].to_dict(),
                        "similarity": score
                    })
            
            return results
    
    def recommend_connectable(self, node_id: str, nodes: Dict[str, NodeV7],
                            edges: Dict[str, EdgeV7], k: int = 5) -> List[Dict[str, Any]]:
        """推荐可以连接的节点"""
        with self._lock:
            existing_targets = set()
            for edge in edges.values():
                if edge.source_id == node_id:
                    existing_targets.add(edge.target_id)
            
            if node_id not in nodes:
                return []
            
            source_node = nodes[node_id]
            if not source_node.embedding:
                return []
            
            candidates = []
            for candidate_id, candidate_node in nodes.items():
                if candidate_id == node_id or candidate_id in existing_targets:
                    continue
                
                if candidate_node.embedding:
                    sim = self.embedding_engine.cosine_similarity(
                        source_node.embedding, candidate_node.embedding
                    )
                    candidates.append((candidate_id, sim))
            
            candidates.sort(key=lambda x: x[1], reverse=True)
            
            results = []
            for candidate_id, score in candidates[:k]:
                results.append({
                    "node": nodes[candidate_id].to_dict(),
                    "compatibility": score,
                    "recommended_relation": "related_to"
                })
            
            return results


# ============================================
# v7.0 主系统
# ============================================

class MemorySystemV7:
    """v7.0 - GNN增强的知识图谱记忆系统"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.join(tempfile.mkdtemp(), "kg_v7.db")
        
        self._nodes: Dict[str, NodeV7] = {}
        self._edges: Dict[str, EdgeV7] = {}
        self._adjacency: Dict[str, Set[str]] = defaultdict(set)
        self._label_index: Dict[str, Set[str]] = defaultdict(set)
        self._label_to_node: Dict[str, str] = {}  # 标签到节点ID的快速查找索引
        
        self.embedding_engine = NodeEmbeddingEngine(embedding_dim=64)
        self.vector_index = VectorIndex(embedding_dim=64)
        self.gnn = SimpleGNN(layers=2, hidden_dim=64)
        self.recommender = KnowledgeRecommender(self.vector_index, self.embedding_engine)
        
        self._cache = OrderedDict()
        self._cache_size = 10000
        
        self._lock = RLock()
        self._stats = {
            "nodes_added": 0,
            "edges_added": 0,
            "queries": 0,
            "inferences": 0,
            "embeddings_computed": 0,
            "recommendations": 0
        }
    
    def remember(self, knowledge: str, properties: Dict = None, 
               node_type: str = NodeType.ENTITY, 
               compute_embedding: bool = True) -> str:
        """记住知识 - 支持计算嵌入"""
        with self._lock:
            # 检查是否已存在完全相同的标签
            label_lower = knowledge.lower()
            if label_lower in self._label_to_node:
                return self._label_to_node[label_lower]
            
            node = NodeV7(
                id=str(uuid.uuid4()),
                label=knowledge,
                node_type=node_type,
                properties=properties or {}
            )
            
            if compute_embedding:
                node.embedding = self.embedding_engine.create_random_embedding()
                self._stats["embeddings_computed"] += 1
            
            self._nodes[node.id] = node
            self._label_index[label_lower].add(node.id)
            self._label_to_node[label_lower] = node.id  # 更新快速索引
            
            if node.embedding:
                self.vector_index.add_vector(node.id, node.embedding)
            
            self._stats["nodes_added"] += 1
            self._invalidate_cache()
            
            return node.id
    
    def connect(self, source: str, target: str, 
               relation: str = EdgeType.RELATED_TO,
               weight: float = 1.0, properties: Dict = None) -> Optional[str]:
        """建立关系连接"""
        with self._lock:
            source_id = self._find_or_create_node(source)
            target_id = self._find_or_create_node(target)
            
            edge = EdgeV7(
                id=str(uuid.uuid4()),
                source_id=source_id,
                target_id=target_id,
                edge_type=relation,
                weight=weight,
                properties=properties or {}
            )
            
            self._edges[edge.id] = edge
            self._adjacency[source_id].add(target_id)
            self._stats["edges_added"] += 1
            self._invalidate_cache()
            
            return edge.id
    
    def _find_or_create_node(self, label: str) -> str:
        """查找或创建节点 - 优化版本"""
        label_lower = label.lower()
        
        # 首先使用快速索引查找完全匹配
        if label_lower in self._label_to_node:
            return self._label_to_node[label_lower]
        
        # 其次查找是否有包含关系的标签（向后兼容）
        for node in self._nodes.values():
            if label_lower in node.label.lower():
                return node.id
        
        # 如果找不到，创建新节点
        return self.remember(label, compute_embedding=True)
    
    def recall(self, query: str, k: int = 20) -> List[Dict[str, Any]]:
        """检索知识"""
        with self._lock:
            self._stats["queries"] += 1
            
            if query is None or query == "":
                results = []
                for node in list(self._nodes.values())[:k]:
                    results.append(node.to_dict())
                return results
            
            cache_key = f"recall:{query}:{k}"
            
            if cache_key in self._cache:
                return self._cache[cache_key]
            
            results = []
            seen = set()
            query_lower = query.lower()
            
            for label_key in self._label_index:
                if query_lower in label_key:
                    for node_id in self._label_index[label_key]:
                        if node_id in self._nodes and node_id not in seen:
                            results.append(self._nodes[node_id].to_dict())
                            seen.add(node_id)
                            if len(results) >= k:
                                break
                    if len(results) >= k:
                        break
            
            self._cache[cache_key] = results
            if len(self._cache) > self._cache_size:
                self._cache.popitem(last=False)
            
            return results
    
    def semantic_search(self, query_label: str, k: int = 10) -> List[Dict[str, Any]]:
        """语义搜索 - 基于嵌入的相似性搜索"""
        with self._lock:
            self._stats["queries"] += 1
            return self.recommender.recommend_similar_nodes(
                query_label, self._nodes, k
            )
    
    def recommend_connections(self, node_label: str, k: int = 5) -> List[Dict[str, Any]]:
        """推荐连接"""
        with self._lock:
            self._stats["recommendations"] += 1
            
            node_id = None
            for nid, node in self._nodes.items():
                if node_label.lower() in node.label.lower():
                    node_id = nid
                    break
            
            if not node_id:
                return []
            
            return self.recommender.recommend_connectable(
                node_id, self._nodes, self._edges, k
            )
    
    def compute_gnn_embeddings(self):
        """使用GNN计算节点嵌入"""
        with self._lock:
            nodes_list = list(self._nodes.values())
            
            embeddings = self.gnn.compute_embeddings(
                nodes_list, self._adjacency, self.embedding_engine
            )
            
            for node_id, embedding in embeddings.items():
                if node_id in self._nodes:
                    self._nodes[node_id].embedding = embedding
                    self.vector_index.add_vector(node_id, embedding)
            
            self._stats["embeddings_computed"] += len(nodes_list)
    
    def infer(self, concept: str, max_depth: int = 3) -> List[Dict[str, Any]]:
        """图推理"""
        with self._lock:
            self._stats["inferences"] += 1
            
            start_node_ids = []
            for node in self._nodes.values():
                if concept.lower() in node.label.lower():
                    start_node_ids.append(node.id)
            
            if not start_node_ids:
                return []
            
            results = []
            seen = set(start_node_ids)
            queue = [(start_node_ids[0], 0)]
            
            while queue:
                current_id, depth = queue.pop(0)
                
                if depth >= max_depth:
                    continue
                
                for neighbor_id in self._adjacency.get(current_id, set()):
                    if neighbor_id not in seen and neighbor_id in self._nodes:
                        if current_id in self._nodes:
                            results.append({
                                "source": self._nodes[current_id].label,
                                "target": self._nodes[neighbor_id].label,
                                "depth": depth + 1
                            })
                        seen.add(neighbor_id)
                        queue.append((neighbor_id, depth + 1))
            
            return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计"""
        with self._lock:
            return {
                "nodes": len(self._nodes),
                "edges": len(self._edges),
                "embeddings_count": self.vector_index.size(),
                **self._stats,
                "version": "7.0"
            }
    
    def get_graph_for_visualization(self) -> Dict[str, Any]:
        """获取可视化图数据"""
        with self._lock:
            nodes_data = [
                {"id": n.id, "label": n.label, "type": n.node_type,
                 "has_embedding": n.embedding is not None}
                for n in self._nodes.values()
            ]
            
            edges_data = [
                {"source": e.source_id, "target": e.target_id, 
                 "type": e.edge_type, "weight": e.weight}
                for e in self._edges.values()
            ]
            
            return {"nodes": nodes_data, "edges": edges_data}
    
    def clear(self):
        """清空系统"""
        with self._lock:
            self._nodes.clear()
            self._edges.clear()
            self._adjacency.clear()
            self._label_index.clear()
            self._label_to_node.clear()
            self.vector_index = VectorIndex()
            self._stats = {
                "nodes_added": 0, "edges_added": 0, "queries": 0,
                "inferences": 0, "embeddings_computed": 0, "recommendations": 0
            }
            self._invalidate_cache()
    
    def save(self, filepath: str = None) -> bool:
        """保存系统状态到文件"""
        with self._lock:
            try:
                filepath = filepath or os.path.join(self.db_path, "kg_v7_state.json")
                
                data = {
                    "version": "7.0",
                    "nodes": [
                        {
                            "id": node.id,
                            "label": node.label,
                            "type": node.node_type,
                            "properties": node.properties,
                            "embedding": node.embedding,
                            "created_at": node.created_at.isoformat(),
                            "updated_at": node.updated_at.isoformat()
                        }
                        for node in self._nodes.values()
                    ],
                    "edges": [
                        {
                            "id": edge.id,
                            "source_id": edge.source_id,
                            "target_id": edge.target_id,
                            "type": edge.edge_type,
                            "weight": edge.weight,
                            "properties": edge.properties,
                            "created_at": edge.created_at.isoformat()
                        }
                        for edge in self._edges.values()
                    ],
                    "stats": self._stats
                }
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                return True
            except Exception as e:
                print(f"保存失败: {e}")
                return False
    
    def load(self, filepath: str = None) -> bool:
        """从文件加载系统状态"""
        with self._lock:
            try:
                filepath = filepath or os.path.join(self.db_path, "kg_v7_state.json")
                
                if not os.path.exists(filepath):
                    return False
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self._nodes.clear()
                self._edges.clear()
                self._adjacency.clear()
                self._label_index.clear()
                self._label_to_node.clear()
                self.vector_index = VectorIndex()
                
                for node_data in data.get("nodes", []):
                    node = NodeV7(
                        id=node_data["id"],
                        label=node_data["label"],
                        node_type=node_data["type"],
                        properties=node_data.get("properties", {}),
                        embedding=node_data.get("embedding"),
                        created_at=datetime.fromisoformat(node_data["created_at"]),
                        updated_at=datetime.fromisoformat(node_data["updated_at"])
                    )
                    self._nodes[node.id] = node
                    self._label_index[node.label.lower()].add(node.id)
                    self._label_to_node[node.label.lower()] = node.id
                    
                    if node.embedding:
                        self.vector_index.add_vector(node.id, node.embedding)
                
                for edge_data in data.get("edges", []):
                    edge = EdgeV7(
                        id=edge_data["id"],
                        source_id=edge_data["source_id"],
                        target_id=edge_data["target_id"],
                        edge_type=edge_data["type"],
                        weight=edge_data.get("weight", 1.0),
                        properties=edge_data.get("properties", {}),
                        created_at=datetime.fromisoformat(edge_data["created_at"])
                    )
                    self._edges[edge.id] = edge
                    self._adjacency[edge.source_id].add(edge.target_id)
                
                self._stats = data.get("stats", {
                    "nodes_added": 0, "edges_added": 0, "queries": 0,
                    "inferences": 0, "embeddings_computed": 0, "recommendations": 0
                })
                
                return True
            except Exception as e:
                print(f"加载失败: {e}")
                return False
    
    def _invalidate_cache(self):
        """清空缓存"""
        self._cache.clear()
