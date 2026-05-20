#!/usr/bin/env python3
"""
知识图谱记忆系统 v6.0 - 核心架构与数据库层
创新点：SQLite/PostgreSQL持久化 + 高级图算法 + GNN集成
"""
from __future__ import annotations

import sys
import os
import json
import time
import uuid
import threading
import random
import tempfile
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from collections import OrderedDict, defaultdict
from enum import Enum
from abc import ABC, abstractmethod
from contextlib import contextmanager

# ============================================
# Enums and Base Types
# ============================================

class NodeType(str, Enum):
    ENTITY = "entity"
    CONCEPT = "concept"
    FACT = "fact"
    PROCESS = "process"
    DOCUMENT = "document"
    USER = "user"
    GROUP = "group"
    PROJECT = "project"


class EdgeType(str, Enum):
    RELATED_TO = "related_to"
    USES = "uses"
    PART_OF = "part_of"
    IS_A = "is_a"
    CREATED_BY = "created_by"
    REFERENCES = "references"
    SIMILAR_TO = "similar_to"
    DEPENDS_ON = "depends_on"
    LEADS_TO = "leads_to"


# ============================================
# Core Data Models (Optimized)
# ============================================

@dataclass(slots=True)
class NodeV6:
    id: str
    label: str
    node_type: NodeType
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "type": self.node_type.value,
            "properties": self.properties,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NodeV6':
        return cls(
            id=data["id"],
            label=data["label"],
            node_type=NodeType(data["type"]),
            properties=data.get("properties", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )


@dataclass(slots=True)
class EdgeV6:
    id: str
    source_id: str
    target_id: str
    edge_type: EdgeType
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "type": self.edge_type.value,
            "weight": self.weight,
            "properties": self.properties,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EdgeV6':
        return cls(
            id=data["id"],
            source_id=data["source_id"],
            target_id=data["target_id"],
            edge_type=EdgeType(data["type"]),
            weight=data.get("weight", 1.0),
            properties=data.get("properties", {}),
            created_at=datetime.fromisoformat(data["created_at"])
        )


# ============================================
# Smart LRU Cache
# ============================================

class SmartLRUCache:
    def __init__(self, capacity: int = 20000):
        self.capacity = capacity
        self.cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self.hits = 0
        self.misses = 0
        self._lock = threading.RLock()
        self.hit_count: Dict[str, int] = defaultdict(int)
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self.cache:
                value, _ = self.cache.pop(key)
                self.hits += 1
                self.hit_count[key] += 1
                self.cache[key] = (value, time.time())
                return value
            self.misses += 1
            return None
    
    def put(self, key: str, value: Any):
        with self._lock:
            if key in self.cache:
                self.cache.pop(key)
            elif len(self.cache) >= self.capacity:
                self._evict()
            self.cache[key] = (value, time.time())
    
    def _evict(self):
        if self.cache:
            lru_key = min(self.cache.keys(), key=lambda k: self.hit_count.get(k, 0))
            self.cache.pop(lru_key)
            if lru_key in self.hit_count:
                del self.hit_count[lru_key]
    
    def clear(self):
        with self._lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
            self.hit_count.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        total = self.hits + self.misses
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": (self.hits / total * 100) if total > 0 else 0,
            "size": len(self.cache),
            "capacity": self.capacity,
            "top_keys": sorted(self.hit_count.items(), key=lambda x: x[1], reverse=True)[:5]
        }


# ============================================
# Database Backend Interface
# ============================================

class DatabaseBackend(ABC):
    @abstractmethod
    def connect(self):
        pass
    
    @abstractmethod
    def disconnect(self):
        pass
    
    @abstractmethod
    def create_node(self, node: NodeV6) -> str:
        pass
    
    @abstractmethod
    def get_node(self, node_id: str) -> Optional[NodeV6]:
        pass
    
    @abstractmethod
    def search_nodes(self, query: str, limit: int = 100) -> List[NodeV6]:
        pass
    
    @abstractmethod
    def delete_node(self, node_id: str):
        pass
    
    @abstractmethod
    def create_edge(self, edge: EdgeV6) -> str:
        pass
    
    @abstractmethod
    def get_edges_from(self, node_id: str) -> List[EdgeV6]:
        pass
    
    @abstractmethod
    def get_edges_to(self, node_id: str) -> List[EdgeV6]:
        pass
    
    @abstractmethod
    def get_all_nodes(self) -> List[NodeV6]:
        pass
    
    @abstractmethod
    def get_all_edges(self) -> List[EdgeV6]:
        pass
    
    @abstractmethod
    def clear_all(self):
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        pass


# ============================================
# SQLite Database Backend (Primary)
# ============================================

class SQLiteBackend(DatabaseBackend):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self._lock = threading.RLock()
    
    def connect(self):
        import sqlite3
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._initialize_schema()
    
    def _initialize_schema(self):
        with self._lock:
            cursor = self.conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS nodes (
                    id TEXT PRIMARY KEY,
                    label TEXT NOT NULL,
                    type TEXT NOT NULL,
                    properties TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS edges (
                    id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    properties TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (source_id) REFERENCES nodes(id),
                    FOREIGN KEY (target_id) REFERENCES nodes(id)
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_node_label ON nodes(label)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_edge_source ON edges(source_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_edge_target ON edges(target_id)')
            
            self.conn.commit()
    
    def disconnect(self):
        if self.conn:
            self.conn.close()
    
    def create_node(self, node: NodeV6) -> str:
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO nodes 
                (id, label, type, properties, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                node.id,
                node.label,
                node.node_type.value,
                json.dumps(node.properties),
                node.created_at.isoformat(),
                node.updated_at.isoformat()
            ))
            self.conn.commit()
            return node.id
    
    def get_node(self, node_id: str) -> Optional[NodeV6]:
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM nodes WHERE id = ?', (node_id,))
            row = cursor.fetchone()
            if row:
                return NodeV6(
                    id=row[0],
                    label=row[1],
                    node_type=NodeType(row[2]),
                    properties=json.loads(row[3]) if row[3] else {},
                    created_at=datetime.fromisoformat(row[4]),
                    updated_at=datetime.fromisoformat(row[5])
                )
            return None
    
    def search_nodes(self, query: str, limit: int = 100) -> List[NodeV6]:
        with self._lock:
            cursor = self.conn.cursor()
            query_lower = f'%{query.lower()}%'
            cursor.execute('''
                SELECT * FROM nodes 
                WHERE LOWER(label) LIKE ? 
                LIMIT ?
            ''', (query_lower, limit))
            rows = cursor.fetchall()
            return [
                NodeV6(
                    id=row[0],
                    label=row[1],
                    node_type=NodeType(row[2]),
                    properties=json.loads(row[3]) if row[3] else {},
                    created_at=datetime.fromisoformat(row[4]),
                    updated_at=datetime.fromisoformat(row[5])
                )
                for row in rows
            ]
    
    def delete_node(self, node_id: str):
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM edges WHERE source_id = ? OR target_id = ?', (node_id, node_id))
            cursor.execute('DELETE FROM nodes WHERE id = ?', (node_id,))
            self.conn.commit()
    
    def create_edge(self, edge: EdgeV6) -> str:
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO edges 
                (id, source_id, target_id, type, weight, properties, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                edge.id,
                edge.source_id,
                edge.target_id,
                edge.edge_type.value,
                edge.weight,
                json.dumps(edge.properties),
                edge.created_at.isoformat()
            ))
            self.conn.commit()
            return edge.id
    
    def get_edges_from(self, node_id: str) -> List[EdgeV6]:
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM edges WHERE source_id = ?', (node_id,))
            rows = cursor.fetchall()
            return self._rows_to_edges(rows)
    
    def get_edges_to(self, node_id: str) -> List[EdgeV6]:
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM edges WHERE target_id = ?', (node_id,))
            rows = cursor.fetchall()
            return self._rows_to_edges(rows)
    
    def _rows_to_edges(self, rows) -> List[EdgeV6]:
        return [
            EdgeV6(
                id=row[0],
                source_id=row[1],
                target_id=row[2],
                edge_type=EdgeType(row[3]),
                weight=row[4],
                properties=json.loads(row[5]) if row[5] else {},
                created_at=datetime.fromisoformat(row[6])
            )
            for row in rows
        ]
    
    def get_all_nodes(self) -> List[NodeV6]:
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM nodes')
            rows = cursor.fetchall()
            return [
                NodeV6(
                    id=row[0],
                    label=row[1],
                    node_type=NodeType(row[2]),
                    properties=json.loads(row[3]) if row[3] else {},
                    created_at=datetime.fromisoformat(row[4]),
                    updated_at=datetime.fromisoformat(row[5])
                )
                for row in rows
            ]
    
    def get_all_edges(self) -> List[EdgeV6]:
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM edges')
            rows = cursor.fetchall()
            return self._rows_to_edges(rows)
    
    def clear_all(self):
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM edges')
            cursor.execute('DELETE FROM nodes')
            self.conn.commit()
    
    def get_statistics(self) -> Dict[str, Any]:
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM nodes')
            node_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM edges')
            edge_count = cursor.fetchone()[0]
            return {
                "nodes": node_count,
                "edges": edge_count
            }


# ============================================
# In-Memory Cache Layer (Hybrid)
# ============================================

class HybridMemoryLayer:
    def __init__(self, db: DatabaseBackend):
        self.db = db
        self._nodes: Dict[str, NodeV6] = {}
        self._edges: Dict[str, EdgeV6] = {}
        self._adjacency: Dict[str, Set[str]] = defaultdict(set)
        self._label_index: Dict[str, Set[str]] = defaultdict(set)
        self._lock = threading.RLock()
        self._dirty: Set[str] = set()
        self._auto_flush = True
    
    def load_from_db(self):
        with self._lock:
            nodes = self.db.get_all_nodes()
            edges = self.db.get_all_edges()
            
            for node in nodes:
                self._nodes[node.id] = node
                self._label_index[node.label.lower()].add(node.id)
            
            for edge in edges:
                self._edges[edge.id] = edge
                self._adjacency[edge.source_id].add(edge.target_id)
    
    def flush_to_db(self):
        with self._lock:
            for node_id in self._dirty:
                if node_id in self._nodes:
                    self.db.create_node(self._nodes[node_id])
            self._dirty.clear()
    
    def add_node(self, node: NodeV6) -> str:
        with self._lock:
            self._nodes[node.id] = node
            self._label_index[node.label.lower()].add(node.id)
            self._dirty.add(node.id)
            if self._auto_flush:
                self.db.create_node(node)
                self._dirty.remove(node.id)
            return node.id
    
    def add_edge(self, edge: EdgeV6) -> str:
        with self._lock:
            self._edges[edge.id] = edge
            self._adjacency[edge.source_id].add(edge.target_id)
            if self._auto_flush:
                self.db.create_edge(edge)
            return edge.id
    
    def get_node(self, node_id: str) -> Optional[NodeV6]:
        with self._lock:
            node = self._nodes.get(node_id)
            if node is None:
                node = self.db.get_node(node_id)
                if node:
                    self._nodes[node.id] = node
            return node
    
    def search_nodes(self, query: str, limit: int = 100) -> List[NodeV6]:
        with self._lock:
            query_lower = query.lower()
            results: List[NodeV6] = []
            seen: Set[str] = set()
            
            for label_key in self._label_index:
                if query_lower in label_key:
                    for node_id in self._label_index[label_key]:
                        if node_id in self._nodes and node_id not in seen:
                            results.append(self._nodes[node_id])
                            seen.add(node_id)
                            if len(results) >= limit:
                                break
                    if len(results) >= limit:
                        break
            
            if len(results) < limit:
                db_results = self.db.search_nodes(query, limit - len(results))
                for node in db_results:
                    if node.id not in seen:
                        results.append(node)
                        seen.add(node.id)
                        self._nodes[node.id] = node
            
            return results[:limit]
    
    def clear(self):
        with self._lock:
            self._nodes.clear()
            self._edges.clear()
            self._adjacency.clear()
            self._label_index.clear()
            self._dirty.clear()
            self.db.clear_all()


# ============================================
# Advanced Graph Analytics (v6.0)
# ============================================

class AdvancedGraphAnalytics:
    def __init__(self, memory_layer: HybridMemoryLayer):
        self.memory_layer = memory_layer
    
    def calculate_degree_centrality(self) -> Dict[str, float]:
        nodes = self.memory_layer._nodes
        adjacency = self.memory_layer._adjacency
        n = len(nodes)
        if n <= 1:
            return {}
        
        centrality = {}
        max_degree = 0
        
        for node_id in nodes:
            degree = len(adjacency.get(node_id, set()))
            centrality[node_id] = degree
            max_degree = max(max_degree, degree)
        
        result = {}
        for node_id, degree in centrality.items():
            node = self.memory_layer._nodes[node_id]
            result[node.label] = degree / (n - 1) if max_degree > 0 else 0
        
        return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))
    
    def find_communities(self, max_iter: int = 20) -> List[List[str]]:
        nodes = list(self.memory_layer._nodes.keys())
        adjacency = self.memory_layer._adjacency
        
        if len(nodes) < 2:
            return [[self.memory_layer._nodes[n].label for n in nodes]] if nodes else []
        
        communities = {node: idx for idx, node in enumerate(nodes)}
        
        for _ in range(max_iter):
            changed = False
            
            for node_id in nodes:
                neighbor_communities = defaultdict(int)
                for neighbor in adjacency.get(node_id, set()):
                    neighbor_communities[communities[neighbor]] += 1
                
                if neighbor_communities:
                    best_community = max(neighbor_communities.items(), key=lambda x: x[1])[0]
                    if best_community != communities[node_id]:
                        communities[node_id] = best_community
                        changed = True
            
            if not changed:
                break
        
        community_groups = defaultdict(list)
        for node_id, community_id in communities.items():
            community_groups[community_id].append(self.memory_layer._nodes[node_id].label)
        
        return list(community_groups.values())
    
    def pagerank(self, damping: float = 0.85, max_iter: int = 100, tol: float = 1e-6) -> Dict[str, float]:
        nodes = list(self.memory_layer._nodes.keys())
        adjacency = self.memory_layer._adjacency
        
        n = len(nodes)
        if n == 0:
            return {}
        
        rank = {node: 1.0 / n for node in nodes}
        out_degree = {node: len(adjacency.get(node, set())) for node in nodes}
        
        for _ in range(max_iter):
            new_rank = {}
            delta = 0
            
            for node_id in nodes:
                incoming = (1 - damping) / n
                for neighbor in nodes:
                    if node_id in adjacency.get(neighbor, set()):
                        if out_degree[neighbor] > 0:
                            incoming += damping * rank[neighbor] / out_degree[neighbor]
                
                new_rank[node_id] = incoming
                delta += abs(new_rank[node_id] - rank[node_id])
            
            rank = new_rank
            
            if delta < tol:
                break
        
        result = {}
        for node_id, score in rank.items():
            result[self.memory_layer._nodes[node_id].label] = score
        
        return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))
    
    def shortest_path(self, source_label: str, target_label: str, max_depth: int = 10) -> Optional[List[str]]:
        source_nodes = self.memory_layer.search_nodes(source_label, limit=1)
        target_nodes = self.memory_layer.search_nodes(target_label, limit=1)
        
        if not source_nodes or not target_nodes:
            return None
        
        source_id = source_nodes[0].id
        target_id = target_nodes[0].id
        
        adjacency = self.memory_layer._adjacency
        
        from collections import deque
        queue = deque([(source_id, [self.memory_layer._nodes[source_id].label])])
        visited = set([source_id])
        
        while queue:
            current_id, path = queue.popleft()
            
            if current_id == target_id:
                return path
            
            if len(path) > max_depth:
                continue
            
            for neighbor in adjacency.get(current_id, set()):
                if neighbor not in visited:
                    visited.add(neighbor)
                    new_path = path + [self.memory_layer._nodes[neighbor].label]
                    queue.append((neighbor, new_path))
        
        return None


# ============================================
# v6.0 Memory System Core
# ============================================

class MemorySystemV6:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(tempfile.mkdtemp(), "kg_memory_v6.db")
        
        self.db = SQLiteBackend(db_path)
        self.db.connect()
        
        self.memory_layer = HybridMemoryLayer(self.db)
        self.memory_layer.load_from_db()
        
        self.cache = SmartLRUCache(25000)
        self.analytics = AdvancedGraphAnalytics(self.memory_layer)
        
        self._lock = threading.RLock()
        self._stats = {
            "nodes_added": 0,
            "edges_added": 0,
            "queries": 0,
            "inferences": 0
        }
    
    def remember(self, knowledge: str, properties: Dict = None, node_type: NodeType = NodeType.ENTITY) -> str:
        with self._lock:
            node = NodeV6(
                id=str(uuid.uuid4()),
                label=knowledge,
                node_type=node_type,
                properties=properties or {}
            )
            node_id = self.memory_layer.add_node(node)
            self._stats["nodes_added"] += 1
            self._invalidate_cache(knowledge)
            return node_id
    
    def connect(self, source: str, target: str, relation: str = "related_to", weight: float = 1.0) -> Optional[str]:
        with self._lock:
            source_nodes = self.memory_layer.search_nodes(source, limit=1)
            target_nodes = self.memory_layer.search_nodes(target, limit=1)
            
            if not source_nodes:
                source_id = self.remember(source)
                source_node = self.memory_layer.get_node(source_id)
            else:
                source_node = source_nodes[0]
                source_id = source_node.id
            
            if not target_nodes:
                target_id = self.remember(target)
                target_node = self.memory_layer.get_node(target_id)
            else:
                target_node = target_nodes[0]
                target_id = target_node.id
            
            edge = EdgeV6(
                id=str(uuid.uuid4()),
                source_id=source_id,
                target_id=target_id,
                edge_type=EdgeType(relation) if relation in [e.value for e in EdgeType] else EdgeType.RELATED_TO,
                weight=weight
            )
            
            edge_id = self.memory_layer.add_edge(edge)
            self._stats["edges_added"] += 1
            self._invalidate_cache(source)
            self._invalidate_cache(target)
            return edge_id
    
    def recall(self, query: str, k: int = 20) -> List[Dict[str, Any]]:
        with self._lock:
            self._stats["queries"] += 1
            k = max(1, min(1000, k))
            cache_key = f"recall:{query}:{k}"
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached
            
            nodes = self.memory_layer.search_nodes(query, limit=k)
            results = [node.to_dict() for node in nodes]
            self.cache.put(cache_key, results)
            return results
    
    def infer(self, concept: str, max_depth: int = 3) -> List[Dict[str, Any]]:
        with self._lock:
            self._stats["inferences"] += 1
            cache_key = f"infer:{concept}:{max_depth}"
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached
            
            start_nodes = self.memory_layer.search_nodes(concept, limit=1)
            if not start_nodes:
                return []
            
            start_id = start_nodes[0].id
            start_label = start_nodes[0].label
            
            adjacency = self.memory_layer._adjacency
            results = []
            seen = set([start_id])
            queue = [(start_id, 0)]
            
            while queue:
                current_id, depth = queue.pop(0)
                
                if depth >= max_depth:
                    continue
                
                for neighbor in adjacency.get(current_id, set()):
                    if neighbor not in seen and neighbor in self.memory_layer._nodes:
                        neighbor_node = self.memory_layer._nodes[neighbor]
                        results.append({
                            "source": start_label,
                            "target": neighbor_node.label,
                            "depth": depth + 1
                        })
                        seen.add(neighbor)
                        queue.append((neighbor, depth + 1))
            
            self.cache.put(cache_key, results)
            return results
    
    def _invalidate_cache(self, label: str):
        keys_to_remove = []
        for key in self.cache.cache:
            if label.lower() in key.lower():
                keys_to_remove.append(key)
        for key in keys_to_remove:
            if key in self.cache.cache:
                del self.cache.cache[key]
    
    def get_statistics(self) -> Dict[str, Any]:
        with self._lock:
            db_stats = self.db.get_statistics()
            return {
                **db_stats,
                **self._stats,
                "cache": self.cache.get_stats(),
                "version": "v6.0"
            }
    
    def get_analytics(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "degree_centrality": self.analytics.calculate_degree_centrality(),
                "pagerank": self.analytics.pagerank(),
                "communities": self.analytics.find_communities()
            }
    
    def clear(self):
        with self._lock:
            self.memory_layer.clear()
            self.cache.clear()
            self._stats = {
                "nodes_added": 0,
                "edges_added": 0,
                "queries": 0,
                "inferences": 0
            }
    
    def export_graph_json(self) -> str:
        with self._lock:
            nodes = self.memory_layer.db.get_all_nodes()
            edges = self.memory_layer.db.get_all_edges()
            return json.dumps({
                "nodes": [n.to_dict() for n in nodes],
                "edges": [e.to_dict() for e in edges]
            }, ensure_ascii=False, indent=2)
