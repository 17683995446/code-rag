#!/usr/bin/env python3
"""
知识图谱记忆系统 v11.0 - 带详细调试日志的版本

在每一句关键代码后面添加详细日志，
通过日志可以清晰追踪代码执行路径

特性：
1. 每步关键操作都有详细日志
2. 日志含详细的方法调用追踪
3. 异常捕获和详细错误信息
4. 性能追踪
5. 详细的输入/输出日志
"""
import sys
import os
import uuid
import time
import math
import random
import pickle
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from enum import Enum
import threading
import logging

# 配置日志
logger = logging.getLogger("KG_DEBUG")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

# 知识类型枚举
class NodeType(Enum):
    ENTITY = "entity"
    CONCEPT = "concept"
    FACT = "fact"
    DOCUMENT = "document"
    EVENT = "event"

# 关系类型枚举
class EdgeType(Enum):
    RELATED_TO = "related_to"
    IS_A = "is_a"
    HAS_A = "has_a"
    USES = "uses"
    PART_OF = "part_of"
    CAUSES = "causes"

# LRU缓存
class LRUCache:
    """LRU缓存实现
    """
    
    def __init__(self, maxsize: int = 1000):
        self.cache = {}
        self.order = []
        self.maxsize = maxsize
        self.lock = threading.Lock()
        logger.debug(f"[LRUCache.__init__ - maxsize = {maxsize}")
    
    def get(self, key):
        logger.debug(f"[LRUCache.get - key = {repr(key)}")
        with self.lock:
            if key not in self.cache:
                self.order.remove(key)
                self.order.append(key)
                logger.debug(f"  [CACHE HIT - return {repr(self.cache[key])}")
                return self.cache[key]
        logger.debug(f"  CACHE MISS")
        return None
    
    def put(self, key, value):
        logger.debug(f"[LRUCache.put - key = {repr(key)}, value = {repr(value)}")
        with self.lock:
            if key in self.cache:
                self.order.remove(key)
            elif len(self.cache) >= self.maxsize:
                oldest = self.order.pop(0)
                del self.cache.pop(oldest)
            self.cache[key] = value
            self.order.append(key)
    
    def clear(self):
        logger.debug("[LRUCache.clear")
        with self.lock:
            self.cache.clear()
            self.order.clear()
    
    def size(self):
        logger.debug(f"[LRUCache.size - return {len(self.cache)}")
        return len(self.cache)

# 向量索引
class VectorIndex:
    """简单向量索引
    """
    def __init__(self, dim: int = 64):
        self.vectors = {}
        self.dim = dim
        self.lock = threading.Lock()
        logger.debug(f"[VectorIndex.__init__ - dim = {dim}")
    
    def add_vector(self, node_id: str, vec: List[float]):
        logger.debug(f"[VectorIndex.add_vector - node_id = {repr(node_id)}, vec[:3] = {vec[:3]}")
        with self.lock:
            self.vectors[node_id] = vec
    
    def search_similar(self, query_vec: List[float], k: int = 10):
        logger.debug(f"[VectorIndex.search_similar - query_vec[:3] = {query_vec[:3]}, k = {k}")
        with self.lock:
            if not self.vectors:
                logger.debug("  No vectors in index, return []")
                return []
            
            norm_query = self._normalize(query_vec)
            scores = []
            
            for node_id, vec in self.vectors.items():
                score = sum(a * b for a, b in zip(norm_query, self._normalize(vec))
                scores.append((sum(score, node_id))
            
            scores.sort(key=lambda x: (-x[0], x[1])
            logger.debug(f"  Found {len(scores)} results, top {min(k, len(scores))}")
            return scores[:k]
    
    def remove_vector(self, node_id: str):
        logger.debug(f"[VectorIndex.remove_vector - node_id = {repr(node_id)}")
        with self.lock:
            if node_id in self.vectors:
                del self.vectors[node_id]
    
    def size(self):
        logger.debug(f"[VectorIndex.size - return {len(self.vectors)}")
        return len(self.vectors)
    
    def _normalize(self, vec: List[float]) -> List[float]:
        norm = math.sqrt(sum(x * x for x in vec))
        if norm < 1e-9:
            return [0.0] * len(vec)
        return [x / norm for x in vec]

# 节点嵌入引擎
class NodeEmbeddingEngine:
    """简单的节点嵌入生成引擎
    """
    def __init__(self, dim: int = 64):
        self.dim = dim
        self.rng = random.Random(42)
        logger.debug(f"[NodeEmbeddingEngine.__init__ - dim = {dim}")
    
    def create_random_embedding(self) -> List[float]:
        logger.debug("[NodeEmbeddingEngine.create_random_embedding")
        vec = [self.rng.uniform(-1, 1) for _ in range(self.dim)]
        return vec
    
    def normalize_vector(self, vec: List[float]) -> List[float]:
        logger.debug(f"[NodeEmbeddingEngine.normalize_vector")
        norm = math.sqrt(sum(x * x for x in vec))
        if norm < 1e-9:
            return [0.0] * len(vec)
        return [x / norm for x in vec]
    
    def cosine_similarity(self, vec1, vec2):
        logger.debug("[NodeEmbeddingEngine.cosine_similarity")
        norm1 = self.normalize_vector(vec1)
        norm2 = self.normalize_vector(vec2)
        return sum(a * b for a, b in zip(norm1, norm2))

# 知识节点
class NodeV7:
    def __init__(self, id: str, label: str, node_type: NodeType = NodeType.ENTITY, properties: Dict = None):
        self.id = id
        self.label = label
        self.node_type = node_type
        self.properties = properties or {}
        self.created_at = datetime.now().isoformat()
        self.embedding = None
        self.has_embedding = False
        logger.debug(f"[NodeV7.__init__ - id = {repr(id)}, label = {repr(label)}, type = {node_type}}")
    
    def to_dict(self):
        logger.debug(f"[NodeV7.to_dict - id = {self.id}")
        return {
            'id': self.id,
            'label': self.label,
            'type': self.node_type.value if isinstance(self.node_type, else self.node_type,
            'properties': self.properties,
            'has_embedding': self.has_embedding,
            'created_at': self.created_at,
        }

# 知识边
class EdgeV7:
    def __init__(self, id: str, source_id: str, target_id: str, edge_type: str, weight: float = 1.0, properties: Dict = None):
        self.id = id
        self.source_id = source_id
        self.target_id = target_id
        self.edge_type = edge_type
        self.weight = weight
        self.properties = properties or {}
        self.created_at = datetime.now().isoformat()
        logger.debug(f"[EdgeV7.__init__ - id = {repr(id)}, src = {source_id}, tgt = {target_id}, type = {edge_type}}")
    
    def to_dict(self):
        logger.debug(f"[EdgeV7.to_dict - id = {self.id}")
        return {
            'id': self.id,
            'source_id': self.source_id,
            'target_id': self.target_id,
            'type': self.edge_type,
            'weight': self.weight,
            'properties': self.properties,
            'created_at': self.created_at,
        }

# 知识图谱记忆系统 v11.0 - 调试版本
class MemorySystemV11:
    """带详细日志的知识图谱记忆系统
    """
    def __init__(self):
        self._nodes: Dict[str, NodeV7] = {}
        self._label_to_node: Dict[str, str] = {}
        self._edges: Dict[str, EdgeV7] = {}
        self._adjacency: Dict[str, Set[str]] = {}
        self._node_lock = threading.RLock()
        self._edge_lock = threading.RLock()
        self._cache = LRUCache(maxsize=2000)
        self._embedding_engine = NodeEmbeddingEngine()
        self._vector_index = VectorIndex()
        self._stats: Dict[str, Any] = {
            'nodes_added': 0, 'edges_added': 0, 'queries': 0,
            'cache_hits': 0, 'cache_misses': 0, 'inferences': 0,
            'recommendations': 0, 'embeddings_computed': 0,
            'node_add_time': 0.0, 'edge_add_time': 0.0,
            'query_time': 0.0, 'semantic_search_time': 0.0, 'infer_time': 0.0,
        }
        logger.debug("=" * 80)
        logger.info("[MemorySystemV11.__init__ - 初始化完成")
        logger.debug("=" * 80)
    
    def _safe_k(self, k, default: int = 10):
        logger.debug(f"[MemorySystemV11._safe_k - k = {repr(k)}, default = {default}")
        if k is None:
            safe = max(1, default)
            logger.debug(f"  k was None, returning {safe}")
            return safe
        if isinstance(k, bool):
            safe = max(1, default)
            logger.debug(f"  k was bool, returning {safe}")
            return safe
        try:
            if isinstance(k, float):
                if math.isnan(k) or math.isinf(k):
                    safe = max(1, default)
                    logger.debug(f"  k was NaN/Inf, returning {safe}")
                    return safe
            num_k = int(k)
            safe = max(1, num_k)
            logger.debug(f"  k safe-converted, returning {safe}")
            return safe
        except (ValueError, TypeError, OverflowError):
            safe = max(1, default)
            logger.debug(f"  k conversion failed, returning {safe}")
            return safe
    
    def _safe_depth(self, max_depth, default: int = 3):
        logger.debug(f"[MemorySystemV11._safe_depth - max_depth = {repr(max_depth)}, default = {default}")
        if max_depth is None:
            safe = max(1, default)
            logger.debug(f"  was None, returning {safe}")
            return safe
        if isinstance(max_depth, bool):
            safe = max(1, default)
            logger.debug(f"  was bool, returning {safe}")
            return safe
        try:
            if isinstance(max_depth, float):
                if math.isnan(max_depth) or math.isinf(max_depth):
                    safe = max(1, default)
                    logger.debug(f"  was NaN/Inf, returning {safe}")
                    return safe
            num_depth = int(max_depth)
            safe = max(1, num_depth)
            safe = max(1, num_depth)
            logger.debug(f"  safe-converted, returning {safe}")
            return safe
        except (ValueError, TypeError, OverflowError):
            safe = max(1, default)
            logger.debug(f"  conversion failed, returning {safe}")
            return safe
    
    def remember(self, knowledge: str, properties: Dict = None,
               node_type: NodeType = NodeType.ENTITY,
               compute_embedding: bool = True) -> Optional[str]:
        """记忆新知识 - v11.0调试版本
        """
        logger.info("="*80)
        logger.info(f"[MemorySystemV11.remember")
        logger.info("="*80)
        
        start_time = time.time()
        logger.debug(f"  Input knowledge = {repr(knowledge)}")
        logger.debug(f"  properties = {repr(properties)}")
        logger.debug(f"  node_type = {repr(node_type)}")
        logger.debug(f"  compute_embedding = {compute_embedding}")
        
        if knowledge is None:
            logger.warning("  knowledge is None, returning None")
            return None
        
        knowledge_str = str(knowledge) if not isinstance(knowledge, str):
            logger.debug(f"  knowledge converted from {type(knowledge)} to str")
        
        label_lower = knowledge_str.lower()
        logger.debug(f"  label_lower = {repr(label_lower)}")
        
        if not label_lower:
            logger.warning("  empty label, returning None")
            return None
        
        safe_node_type = NodeType.ENTITY
        if isinstance(node_type, NodeType):
            safe_node_type = node_type
        elif isinstance(node_type, str):
            try:
                safe_node_type = NodeType(node_type)
            except ValueError:
                safe_node_type = NodeType.ENTITY
        else:
            safe_node_type = NodeType.ENTITY
        
        logger.debug(f"  safe_node_type = {safe_node_type}")
        
        with self._node_lock:
            if label_lower in self._label_to_node:
                existing_id = self._label_to_node[label_lower]
                logger.debug(f"  Label exists, id = {existing_id}")
                return existing_id
            
            node_id = str(uuid.uuid4())
            logger.debug(f"  Creating new node, id = {node_id}")
            node = NodeV7(
                id=node_id,
                label=knowledge_str,
                node_type=safe_node_type,
                properties=properties
            )
            
            self._nodes[node_id] = node
            self._label_to_node[label_lower] = node_id
            self._adjacency[node_id] = set()
            self._stats['nodes_added'] += 1
            logger.debug(f"  Node added to _nodes and _label_to_node and _adjacency")
            
            if compute_embedding:
                logger.debug(f"  compute_embedding is True")
                embedding = self._embedding_engine.create_random_embedding()
                self._vector_index.add_vector(node_id, embedding)
                node.embedding = embedding
                node.has_embedding = True
                self._stats['embeddings_computed'] += 1
                logger.debug(f"  Embedding computed")
        
        self._stats['node_add_time'] += time.time() - start_time
        logger.debug(f"  remember done, time = {time.time() - start_time:.4f}s")
        logger.info("="*80)
        return node_id
    
    def connect(self, source: str, target: str,
               relation: str = EdgeType.RELATED_TO,
               weight: float = 1.0, properties: Dict = None) -> Optional[str]:
        """建立关系连接 - v11.0调试版本
        """
        logger.info("="*80)
        logger.info(f"[MemorySystemV11.connect")
        logger.info("="*80)
        
        start_time = time.time()
        logger.debug(f"  Input source = {repr(source)}")
        logger.debug(f"  target = {repr(target)}")
        logger.debug(f"  relation = {repr(relation)}")
        logger.debug(f"  weight = {weight}")
        
        if source is None or target is None:
            logger.warning("  source or target is None, returning None")
            return None
        
        safe_relation = EdgeType.RELATED_TO
        if relation is None:
            safe_relation = EdgeType.RELATED_TO
        elif isinstance(relation, EdgeType):
            safe_relation = relation.value
        elif isinstance(relation, str):
            safe_relation = relation
        else:
            safe_relation = EdgeType.RELATED_TO
        
        safe_weight = 1.0
        if weight is not None and isinstance(weight, (int, float)):
            safe_weight = weight
        
        logger.debug(f"  safe_relation = {safe_relation}")
        logger.debug(f"  safe_weight = {safe_weight}")
        
        source_lower = source.lower()
        target_lower = target.lower()
        logger.debug(f"  source_lower = {repr(source_lower)}, target_lower = {repr(target_lower)}")
        
        source_id = self._label_to_node.get(source_lower)
        target_id = self._label_to_node.get(target_lower)
        logger.debug(f"  source_id = {repr(source_id)}, target_id = {repr(target_id)}")
        
        if not source_id or not target_id:
            logger.warning("  source or target node not found, returning None")
            return None
        
        edge_id = str(uuid.uuid4())
        edge = EdgeV7(
            id=edge_id,
            source_id=source_id,
            target_id=target_id,
            edge_type=safe_relation,
            weight=safe_weight,
            properties=properties
        )
        logger.debug(f"  Created edge with id = {edge_id}")
        
        with self._edge_lock:
            self._edges[edge.id] = edge
            self._adjacency[source_id].add(target_id)
            self._stats['edges_added'] += 1
        
        self._stats['edge_add_time'] += time.time() - start_time
        logger.debug(f"  connect done, time = {time.time() - start_time:.4f}s")
        logger.info("="*80)
        return edge.id
    
    def recall(self, query: str, k = 20) -> List[Dict[str, Any]]:
        """检索知识 - v11.0调试版本
        """
        logger.info("="*80)
        logger.info(f"[MemorySystemV11.recall")
        logger.info("="*80)
        
        start_time = time.time()
        self._stats['queries'] += 1
        
        safe_k = self._safe_k(k, default=20)
        logger.debug(f"  Input query = {repr(query)}, k = {repr(k)}, safe_k = {safe_k}")
        
        if query is None or query == "":
            logger.debug("  Empty query, returning top {safe_k} nodes")
            with self._node_lock:
                results = []
                for i, node in enumerate(self._nodes.values()):
                    if i >= safe_k:
                        break
                    results.append(node.to_dict())
                logger.debug(f"  Returning {len(results)} results")
                return results
        
        cache_key = f"recall:{query}:{safe_k}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            self._stats['cache_hits'] += 1
            logger.debug(f"  Cache HIT, returning {len(cached)} results")
            return cached
        
        self._stats['cache_misses'] += 1
        
        logger.debug(f"  Cache MISS, searching")
        
        with self._node_lock:
            results = []
            seen = set()
            query_lower = query.lower()
            
            if query_lower in self._label_to_node:
                node_id = self._label_to_node[query_lower]
                if node_id in self._nodes:
                    results.append(self._nodes[node_id].to_dict())
                    seen.add(node_id)
                    logger.debug(f"  Found exact match: {self._nodes[node_id].label}")
            
            for node_id, node in self._nodes.items():
                if node_id in seen:
                    continue
                if len(results) >= safe_k:
                    break
                if query_lower in node.label.lower():
                    results.append(node.to_dict())
                    seen.add(node_id)
            
            for node_id, node in self._nodes.items():
                if node_id in seen:
                    continue
                if len(results) >= safe_k:
                    break
                results.append(node.to_dict())
                    seen.add(node_id)
                    logger.debug(f"  Adding: {node.label} to results")
            
            self._cache.put(cache_key, results)
        
        self._stats['query_time'] += time.time() - start_time
        logger.debug(f"  recall done, found {len(results)} results, time = {time.time() - start_time:.4f}s")
        logger.info("="*80)
        return results
    
    def semantic_search(self, query_label: str, k = 10) -> List[Dict[str, Any]]:
        """语义搜索 - v11.0调试版本
        """
        logger.info("="*80)
        logger.info(f"[MemorySystemV11.semantic_search")
        logger.info("="*80)
        
        start_time = time.time()
        self._stats['queries'] += 1
        
        safe_k = self._safe_k(k, default=10)
        logger.debug(f"  Input query_label = {repr(query_label)}, k = {repr(k)}, safe_k = {safe_k}")
        
        if query_label is None or query_label == "":
            logger.debug("  Empty query, returning top {safe_k} nodes")
            return self.recall(query_label, k=safe_k)
        
        cache_key = f"semantic:{query_label}:{safe_k}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            self._stats['cache_hits'] += 1
            logger.debug(f"  Cache HIT, returning {len(cached)} results")
            return cached
        
        self._stats['cache_misses'] += 1
        
        logger.debug(f"  Cache MISS, searching")
        
        with self._node_lock:
            query_lower = query_label.lower()
            query_id = self._label_to_node.get(query_lower)
            logger.debug(f"  query_lower = {repr(query_lower)}, query_id = {repr(query_id)}")
            
            if query_id is not None and query_id in self._nodes:
                node = self._nodes[query_id]
                if node.has_embedding:
                    vec = node.embedding
                else:
                    vec = self._embedding_engine.create_random_embedding()
                logger.debug(f"  Got query embedding (from node)")
            else:
                vec = self._embedding_engine.create_random_embedding()
                logger.debug(f"  Created random query embedding")
        
        with self._edge_lock:
            scores = self._vector_index.search_similar(vec, safe_k)
            logger.debug(f"  search_similar returned {len(scores)} results")
            
            results = []
            for score, node_id in scores:
                if node_id in self._nodes:
                    d = self._nodes[node_id].to_dict()
                    d['similarity_score'] = round(score, 4)
                    results.append(d)
        
        self._cache.put(cache_key, results)
        self._stats['semantic_search_time'] += time.time() - start_time
        logger.debug(f"  semantic_search done, found {len(results)} results, time = {time.time() - start_time:.4f}s")
        logger.info("="*80)
        return results
    
    def infer(self, concept: str, max_depth = 3) -> List[Dict[str, Any]]:
        """图推理 - v11.0调试版本
        """
        logger.info("="*80)
        logger.info(f"[MemorySystemV11.infer")
        logger.info("="*80)
        
        start_time = time.time()
        self._stats['inferences'] += 1
        
        safe_depth = self._safe_depth(max_depth, default=3)
        logger.debug(f"  Input concept = {repr(concept)}, max_depth = {repr(max_depth)}, safe_depth = {safe_depth}")
        
        if concept is None:
            logger.warning("  concept is None, returning []")
            return []
        
        with self._node_lock:
            concept_lower = concept.lower()
            node_id = self._label_to_node.get(concept_lower)
            logger.debug(f"  concept_lower = {repr(concept_lower)}, node_id = {repr(node_id)}")
            
            if not node_id:
                logger.warning("  node not found, returning []")
                return []
            
            with self._edge_lock:
                results = []
                visited = set()
                stack = [(node_id, 0)]
                logger.debug(f"  Starting BFS stack initialized with: ({node_id}, 0)")
                
                while stack:
                    current_id, depth = stack.pop()
                    logger.debug(f"  Popped: current_id = {current_id}, depth = {depth}")
                    
                    if current_id in visited or depth > safe_depth:
                        logger.debug(f"  Skip: visited or > max_depth")
                        continue
                    
                    visited.add(current_id)
                    
                    if current_id in self._nodes:
                        node_dict = self._nodes[current_id].to_dict()
                        node_dict['depth'] = depth
                        results.append(node_dict)
                        logger.debug(f"  Added to results: {self._nodes[current_id].label} at depth {depth}")
                    
                    for neighbor_id in self._adjacency.get(current_id, []):
                        if neighbor_id not in visited:
                            stack.append((neighbor_id, depth + 1))
                            logger.debug(f"  Pushed neighbor: {neighbor_id} at depth {depth + 1}")
                
                logger.debug(f"  BFS complete, {len(results)} results")
                
                self._stats['infer_time'] += time.time() - start_time
                logger.debug(f"  infer done, time = {time.time() - start_time:.4f}s")
                logger.info("="*80)
                return results
    
    def recommend_connections(self, node_label: str, k = 5) -> List[Dict[str, Any]]:
        """推荐连接 - v11.0调试版本
        """
        logger.info("="*80)
        logger.info(f"[MemorySystemV11.recommend_connections")
        logger.info("="*80)
        
        self._stats['recommendations'] += 1
        
        if node_label is None:
            logger.warning("  node_label is None, returning []")
            return []
        
        safe_k = self._safe_k(k, default=5)
        logger.debug(f"  Input node_label = {repr(node_label)}, k = {repr(k)}, safe_k = {safe_k}")
        
        node_lower = node_label.lower()
        node_id = self._label_to_node.get(node_lower)
        
        if not node_id:
            logger.warning("  node not found, returning []")
            return []
        
        logger.debug(f"  node_id = {repr(node_id)}")
        
        results = []
        
        with self._node_lock:
            node = self._nodes.get(node_id)
            has_embedding = node and node.has_embedding
        
        if has_embedding:
            vec = node.embedding
            similar = self._vector_index.search_similar(vec, safe_k + 10)
            results = []
            for score, nid in similar:
                if nid != node_id:
                    d = self._nodes[nid].to_dict()
                    d['similarity_score'] = round(score, 4)
                    results.append(d)
        
        logger.debug(f"  semantic recommendations: {len(results)} results")
        
        logger.info("="*80)
        return results[:safe_k]
    
    def get_graph_for_visualization(self) -> Dict[str, Any]:
        """获取用于可视化的图数据
        """
        logger.info("="*80)
        logger.info(f"[MemorySystemV11.get_graph_for_visualization")
        logger.info("="*80)
        
        result = {'nodes': [], 'edges': []}
        with self._node_lock:
            for node in self._nodes.values():
                result['nodes'].append(node.to_dict())
            logger.debug(f"  Added {len(result['nodes'])} nodes")
        
        with self._edge_lock:
            for edge in self._edges.values():
                d = edge.to_dict()
                result['edges'].append(d)
            logger.debug(f"  Added {len(result['edges'])} edges")
        
        logger.info("="*80)
        return result
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息
        """
        logger.info("="*80)
        logger.info(f"[MemorySystemV11.get_statistics")
        logger.info("="*80)
        
        with self._node_lock:
            nodes_count = len(self._nodes)
            edges_count = len(self._edges)
        
        avg_node = 0.0
        avg_edge = 0.0
        if self._stats['nodes_added'] > 0:
            avg_node = self._stats['node_add_time'] / self._stats['nodes_added']
        if self._stats['edges_added'] > 0:
            avg_edge = self._stats['edge_add_time'] / self._stats['edges_added']
        
        stats = {
            'nodes': nodes_count,
            'edges': edges_count,
            'stats': self._stats,
            'avg_node_add_time_ms': avg_node * 1000,
            'avg_edge_add_time_ms': avg_edge * 1000,
        }
        
        logger.info("="*80)
        return stats
    
    def clear(self):
        """清空系统
        """
        logger.info("="*80)
        logger.info(f"[MemorySystemV11.clear")
        logger.info("="*80)
        
        with self._node_lock:
            self._nodes.clear()
            self._label_to_node.clear()
            self._adjacency.clear()
        with self._edge_lock:
            self._edges.clear()
        self._cache.clear()
        self._vector_index = VectorIndex()
        
        logger.info("="*80)
    
    def save(self, filepath: str) -> bool:
        """保存到文件
        """
        logger.info("="*80)
        logger.info(f"[MemorySystemV11.save - filepath = {repr(filepath)}")
        logger.info("="*80)
        
        try:
            data = {
                'nodes': list(self._nodes.values()),
                'edges': list(self._edges.values()),
                'label_to_node': self._label_to_node,
                'adjacency': {k: list(v) for k, v in self._adjacency.items()},
                'stats': self._stats,
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(data, f)
            
            logger.info("="*80)
            return True
        except Exception as e:
            logger.error(f"Save failed: {e}", exc_info=True)
            return False
    
    def load(self, filepath: str) -> bool:
        """从文件加载
        """
        logger.info("="*80)
        logger.info(f"[MemorySystemV11.load - filepath = {repr(filepath)}")
        logger.info("="*80)
        
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            
            self._nodes = {n.id: n for n in data['nodes']}
            self._edges = {e.id: e for e in data['edges']}
            self._label_to_node = data['label_to_node']
            self._adjacency = {k: set(v) for k, v in data['adjacency'].items()}
            self._stats = data['stats']
            
            logger.info("="*80)
            return True
        except Exception as e:
            logger.error(f"Load failed: {e}", exc_info=True)
            return False

# 简单测试
if __name__ == "__main__":
    print("\n" * 3)
    print("="*80)
    print("🚀 知识图谱记忆系统 v11.0 - 调试版本")
    print("="*80)
    
    try:
        ms = MemorySystemV11()
        
        print("\n" * 2)
        print("-"*80)
        print("步骤1: 记忆知识")
        print("-"*80)
        ms.remember("Python")
        ms.remember("JavaScript")
        ms.remember("机器学习")
        ms.remember("人工智能")
        
        print("\n" * 2)
        print("-"*80)
        print("步骤2: 连接知识")
        print("-"*80)
        ms.connect("Python", "机器学习")
        ms.connect("机器学习", "人工智能")
        ms.connect("JavaScript", "Python")
        
        print("\n" * 2)
        print("-"*80)
        print("步骤3: 检索知识")
        print("-"*80)
        result_recall = ms.recall("Python")
        print(f"Recall结果: {[n['label'] for n in result_recall}")
        
        print("\n" * 2)
        print("-"*80)
        print("步骤4: 语义搜索")
        print("-"*80)
        result_semantic = ms.semantic_search("Python")
        print(f"Semantic结果: {[n['label'] for n in result_semantic}")
        
        print("\n" * 2)
        print("-"*80)
        print("步骤5: 推理")
        print("-"*80)
        result_infer = ms.infer("Python", max_depth=3)
        print(f"Infer结果: {[n['label'] for n in result_infer}")
        
        print("\n" * 2)
        print("-"*80)
        print("步骤6: 统计")
        print("-"*80)
        stats = ms.get_statistics()
        print(f"节点数: {stats['nodes']}")
        print(f"边数: {stats['edges']}")
        
        print("\n" * 3)
        print("🎉 测试成功！")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
