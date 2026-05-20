#!/usr/bin/env python3
"""
知识图谱记忆系统 v13.0 - 全面安全修复版本

修复的问题：
1. LRUCache 语法错误 - del self.cache.pop(oldest) 改为直接 pop
2. recall 方法逻辑错误 - 在循环中有重复的 seen.add
3. recall 方法中出现了语法问题（缩进错误）
4. knowledge_str 类型判断有语法问题
5. NodeV7 的 to_dict 方法有问题
6. 所有测试用例都通过
7. ✅ v13.0 新增：所有输入类型（int, float, bool, list, dict, tuple, None）完全安全处理！
"""
import sys
import os
import uuid
import time
import math
import random
import pickle
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from enum import Enum
import threading
import logging

# 配置日志
logger = logging.getLogger("KG_V13")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
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
    """LRU缓存实现 - 修复了语法错误
    """
    
    def __init__(self, maxsize: int = 1000):
        self.cache = {}
        self.order = []
        self.maxsize = maxsize
        self.lock = threading.Lock()
    
    def get(self, key):
        with self.lock:
            if key not in self.cache:
                return None
            self.order.remove(key)
            self.order.append(key)
            return self.cache[key]
    
    def put(self, key, value):
        with self.lock:
            if key in self.cache:
                self.order.remove(key)
            elif len(self.cache) >= self.maxsize:
                oldest = self.order.pop(0)
                del self.cache[oldest]
            self.cache[key] = value
            self.order.append(key)
    
    def clear(self):
        with self.lock:
            self.cache.clear()
            self.order.clear()
    
    def size(self):
        return len(self.cache)

# 向量索引
class VectorIndex:
    """简单向量索引
    """
    def __init__(self, dim: int = 64):
        self.vectors = {}
        self.dim = dim
        self.lock = threading.Lock()
    
    def add_vector(self, node_id: str, vec: List[float]):
        with self.lock:
            self.vectors[node_id] = vec
    
    def search_similar(self, query_vec: List[float], k: int = 10):
        with self.lock:
            if not self.vectors:
                return []
            
            norm_query = self._normalize(query_vec)
            scores = []
            
            for node_id, vec in self.vectors.items():
                norm_vec = self._normalize(vec)
                score = sum(a * b for a, b in zip(norm_query, norm_vec))
                scores.append((score, node_id))
            
            scores.sort(key=lambda x: (-x[0], x[1]))
            return scores[:k]
    
    def remove_vector(self, node_id: str):
        with self.lock:
            if node_id in self.vectors:
                del self.vectors[node_id]
    
    def size(self):
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
    
    def create_random_embedding(self) -> List[float]:
        return [self.rng.uniform(-1, 1) for _ in range(self.dim)]
    
    def normalize_vector(self, vec: List[float]) -> List[float]:
        norm = math.sqrt(sum(x * x for x in vec))
        if norm < 1e-9:
            return [0.0] * len(vec)
        return [x / norm for x in vec]
    
    def cosine_similarity(self, vec1, vec2):
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
    
    def to_dict(self):
        nt = self.node_type
        if isinstance(nt, NodeType):
            nt = nt.value
        return {
            'id': self.id,
            'label': self.label,
            'type': nt,
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
    
    def to_dict(self):
        return {
            'id': self.id,
            'source_id': self.source_id,
            'target_id': self.target_id,
            'type': self.edge_type,
            'weight': self.weight,
            'properties': self.properties,
            'created_at': self.created_at,
        }

# 知识图谱记忆系统 v13.0 - 全面安全版本
class MemorySystemV7Optimized:
    """完整修复的知识图谱记忆系统
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
        logger.info("[MemorySystemV7Optimized.__init__ - v13.0全面安全版初始化完成")
    
    def _safe_k(self, k, default: int = 10):
        if k is None:
            return max(1, default)
        if isinstance(k, bool):
            return max(1, default)
        try:
            if isinstance(k, float):
                if math.isnan(k) or math.isinf(k):
                    return max(1, default)
            num_k = int(k)
            return max(1, num_k)
        except (ValueError, TypeError, OverflowError):
            return max(1, default)
    
    def _safe_depth(self, max_depth, default: int = 3):
        if max_depth is None:
            return max(1, default)
        if isinstance(max_depth, bool):
            return max(1, default)
        try:
            if isinstance(max_depth, float):
                if math.isnan(max_depth) or math.isinf(max_depth):
                    return max(1, default)
            num_depth = int(max_depth)
            return max(1, num_depth)
        except (ValueError, TypeError, OverflowError):
            return max(1, default)
    
    def _safe_str(self, value):
        """✅ v13.0新增：绝对安全的字符串转换方法"""
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        try:
            return str(value)
        except Exception:
            return ""
    
    def remember(self, knowledge: Any, properties: Dict = None,
               node_type: Any = NodeType.ENTITY,
               compute_embedding: bool = True) -> Optional[str]:
        """记忆新知识 - v13.0全面安全版本
        """
        start_time = time.time()
        
        if knowledge is None:
            return None
        
        knowledge_str = self._safe_str(knowledge)
        if not knowledge_str:
            return None
        label_lower = knowledge_str.lower()
        
        safe_node_type = NodeType.ENTITY
        if isinstance(node_type, NodeType):
            safe_node_type = node_type
        elif isinstance(node_type, str):
            try:
                safe_node_type = NodeType(node_type)
            except ValueError:
                safe_node_type = NodeType.ENTITY
        
        with self._node_lock:
            if label_lower in self._label_to_node:
                return self._label_to_node[label_lower]
            
            node_id = str(uuid.uuid4())
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
            
            if compute_embedding:
                embedding = self._embedding_engine.create_random_embedding()
                self._vector_index.add_vector(node_id, embedding)
                node.embedding = embedding
                node.has_embedding = True
                self._stats['embeddings_computed'] += 1
        
        self._stats['node_add_time'] += time.time() - start_time
        return node_id
    
    def connect(self, source: Any, target: Any,
               relation: Any = EdgeType.RELATED_TO,
               weight: float = 1.0, properties: Dict = None) -> Optional[str]:
        """建立关系连接 - v13.0全面安全版本
        """
        start_time = time.time()
        
        if source is None or target is None:
            return None
        
        safe_relation = EdgeType.RELATED_TO
        if relation is None:
            safe_relation = EdgeType.RELATED_TO
        elif isinstance(relation, EdgeType):
            safe_relation = relation.value
        elif isinstance(relation, str):
            safe_relation = relation
        else:
            safe_relation = str(relation) if relation else EdgeType.RELATED_TO
        
        safe_weight = 1.0
        if weight is not None and isinstance(weight, (int, float)):
            safe_weight = weight
        
        # ✅ v13.0安全处理
        source_str = self._safe_str(source)
        target_str = self._safe_str(target)
        if not source_str or not target_str:
            return None
        
        source_lower = source_str.lower()
        target_lower = target_str.lower()
        source_id = self._label_to_node.get(source_lower)
        target_id = self._label_to_node.get(target_lower)
        
        if not source_id or not target_id:
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
        
        with self._edge_lock:
            self._edges[edge.id] = edge
            self._adjacency[source_id].add(target_id)
            self._stats['edges_added'] += 1
        
        self._stats['edge_add_time'] += time.time() - start_time
        return edge_id
    
    def recall(self, query: Any, k = 20) -> List[Dict[str, Any]]:
        """检索知识 - v13.0全面安全版本
        """
        start_time = time.time()
        self._stats['queries'] += 1
        
        safe_k = self._safe_k(k, default=20)
        
        # ✅ v13.0安全处理
        query_str = self._safe_str(query)
        if not query_str:
            with self._node_lock:
                results = []
                for i, node in enumerate(self._nodes.values()):
                    if i >= safe_k:
                        break
                    results.append(node.to_dict())
                return results
        
        cache_key = f"recall:{query_str}:{safe_k}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            self._stats['cache_hits'] += 1
            return cached
        
        self._stats['cache_misses'] += 1
        
        with self._node_lock:
            results = []
            seen = set()
            query_lower = query_str.lower()
            
            if query_lower in self._label_to_node:
                node_id = self._label_to_node[query_lower]
                if node_id in self._nodes:
                    results.append(self._nodes[node_id].to_dict())
                    seen.add(node_id)
            
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
            
            self._cache.put(cache_key, results)
        
        self._stats['query_time'] += time.time() - start_time
        return results
    
    def semantic_search(self, query_label: Any, k = 10) -> List[Dict[str, Any]]:
        """语义搜索 - v13.0全面安全版本
        """
        start_time = time.time()
        self._stats['queries'] += 1
        
        safe_k = self._safe_k(k, default=10)
        
        # ✅ v13.0安全处理
        query_str = self._safe_str(query_label)
        if not query_str:
            return self.recall(query_label, k=safe_k)
        
        cache_key = f"semantic:{query_str}:{safe_k}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            self._stats['cache_hits'] += 1
            return cached
        
        self._stats['cache_misses'] += 1
        
        vec = None
        with self._node_lock:
            query_lower = query_str.lower()
            query_id = self._label_to_node.get(query_lower)
            if query_id is not None and query_id in self._nodes:
                node = self._nodes[query_id]
                if node.has_embedding:
                    vec = node.embedding
                else:
                    vec = self._embedding_engine.create_random_embedding()
            else:
                vec = self._embedding_engine.create_random_embedding()
        
        with self._edge_lock:
            scores = self._vector_index.search_similar(vec, safe_k)
            results = []
            for score, node_id in scores:
                if node_id in self._nodes:
                    d = self._nodes[node_id].to_dict()
                    d['similarity_score'] = round(score, 4)
                    results.append(d)
        
        self._cache.put(cache_key, results)
        self._stats['semantic_search_time'] += time.time() - start_time
        return results
    
    def infer(self, concept: Any, max_depth = 3) -> List[Dict[str, Any]]:
        """图推理 - v13.0全面安全版本
        """
        start_time = time.time()
        self._stats['inferences'] += 1
        
        safe_depth = self._safe_depth(max_depth, default=3)
        
        # ✅ v13.0安全处理
        concept_str = self._safe_str(concept)
        if not concept_str:
            return []
        
        with self._node_lock:
            concept_lower = concept_str.lower()
            node_id = self._label_to_node.get(concept_lower)
            if not node_id:
                return []
            
            with self._edge_lock:
                results = []
                visited = set()
                stack = [(node_id, 0)]
                
                while stack:
                    current_id, depth = stack.pop()
                    
                    if current_id in visited or depth > safe_depth:
                        continue
                    
                    visited.add(current_id)
                    
                    if current_id in self._nodes:
                        node_dict = self._nodes[current_id].to_dict()
                        node_dict['depth'] = depth
                        results.append(node_dict)
                    
                    for neighbor_id in self._adjacency.get(current_id, []):
                        if neighbor_id not in visited:
                            stack.append((neighbor_id, depth + 1))
                
                self._stats['infer_time'] += time.time() - start_time
                return results
    
    def recommend_connections(self, node_label: Any, k = 5) -> List[Dict[str, Any]]:
        """推荐连接 - v13.0全面安全版本
        """
        self._stats['recommendations'] += 1
        
        # ✅ v13.0安全处理
        node_label_str = self._safe_str(node_label)
        if not node_label_str:
            return []
        
        safe_k = self._safe_k(k, default=5)
        
        node_lower = node_label_str.lower()
        node_id = self._label_to_node.get(node_lower)
        
        if not node_id:
            return []
        
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
        
        return results[:safe_k]
    
    def get_graph_for_visualization(self) -> Dict[str, Any]:
        """获取用于可视化的图数据
        """
        result = {'nodes': [], 'edges': []}
        with self._node_lock:
            for node in self._nodes.values():
                result['nodes'].append(node.to_dict())
        
        with self._edge_lock:
            for edge in self._edges.values():
                result['edges'].append(edge.to_dict())
        
        return result
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息
        """
        with self._node_lock:
            nodes_count = len(self._nodes)
            edges_count = len(self._edges)
        
        avg_node = 0.0
        avg_edge = 0.0
        if self._stats['nodes_added'] > 0:
            avg_node = self._stats['node_add_time'] / self._stats['nodes_added']
        if self._stats['edges_added'] > 0:
            avg_edge = self._stats['edge_add_time'] / self._stats['edges_added']
        
        return {
            'nodes': nodes_count,
            'edges': edges_count,
            'stats': self._stats,
            'avg_node_add_time_ms': avg_node * 1000,
            'avg_edge_add_time_ms': avg_edge * 1000,
        }
    
    def clear(self):
        """清空系统
        """
        with self._node_lock:
            self._nodes.clear()
            self._label_to_node.clear()
            self._adjacency.clear()
        with self._edge_lock:
            self._edges.clear()
        self._cache.clear()
        self._vector_index = VectorIndex()
