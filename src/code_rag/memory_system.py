"""
知识图谱记忆系统 - 存储引擎与记忆管理
"""

import json
import os
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict
from datetime import datetime, timedelta

from src.code_rag.knowledge_graph import (
    KnowledgeGraph, KnowledgeNode, KnowledgeEdge,
    MemorySession, KnowledgeType, RelationType
)


class KnowledgeStore:
    """知识图谱持久化存储引擎"""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.graph_file = self.data_dir / "knowledge_graph.json"
        self.sessions_file = self.data_dir / "sessions.pkl"
        self.memory_file = self.data_dir / "memory_index.json"
        
        self.graph = KnowledgeGraph()
        self.sessions: Dict[str, MemorySession] = {}
        self.memory_index: Dict[str, List[str]] = defaultdict(list)  # 关键词索引
        
        self._load()
    
    def _load(self):
        """从磁盘加载数据"""
        if self.graph_file.exists():
            try:
                with open(self.graph_file, 'r', encoding='utf-8') as f:
                    self.graph = KnowledgeGraph.from_json(f.read())
            except Exception as e:
                print(f"加载知识图谱失败: {e}")
        
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
        with open(self.graph_file, 'w', encoding='utf-8') as f:
            f.write(self.graph.to_json())
        
        with open(self.sessions_file, 'wb') as f:
            pickle.dump(self.sessions, f)
        
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(dict(self.memory_index), f, ensure_ascii=False, indent=2)
    
    def clear_all(self):
        """清空所有数据"""
        self.graph = KnowledgeGraph()
        self.sessions = {}
        self.memory_index = defaultdict(list)
        self.save()


class MemorySystem:
    """智能记忆系统 - 管理知识记忆与会话"""
    
    def __init__(self, data_dir: str = "./data"):
        self.store = KnowledgeStore(data_dir)
        self.current_session: Optional[MemorySession] = None
        self.recent_nodes: List[str] = []  # 最近访问的节点
        self.max_recent = 50
    
    def start_session(self, user_id: Optional[str] = None) -> str:
        """开始新会话"""
        session = MemorySession(user_id=user_id)
        self.store.sessions[session.id] = session
        self.current_session = session
        self.store.save()
        return session.id
    
    def remember(self, knowledge: str, metadata: Optional[Dict] = None) -> str:
        """记住知识"""
        if self.current_session is None:
            self.start_session()
        
        # 创建知识节点
        node = KnowledgeNode(
            knowledge,
            type=KnowledgeType.FACT,
            properties=metadata or {}
        )
        node_id = self.store.graph.add_node(node)
        
        # 更新索引
        keywords = self._extract_keywords(knowledge)
        for keyword in keywords:
            self.store.memory_index[keyword.lower()].append(node_id)
        
        # 关联到会话
        self.current_session.nodes.append(node_id)
        
        # 记录为最近节点
        self.recent_nodes.insert(0, node_id)
        if len(self.recent_nodes) > self.max_recent:
            self.recent_nodes.pop()
        
        self.store.save()
        return node_id
    
    def connect_knowledge(self, source: str, target: str, 
                         relation: str = "related_to") -> str:
        """连接两条知识"""
        relation_type_map = {rt.value: rt for rt in RelationType}
        rel_type = relation_type_map.get(relation, RelationType.RELATED_TO)
        return self.store.graph.connect(source, target, rel_type)
    
    def recall(self, query: str, k: int = 10) -> List[Dict]:
        """回忆相关知识"""
        query_lower = query.lower()
        
        # 1. 标签直接匹配
        direct_results = self.store.graph.search(query, k=k)
        
        # 2. 关键词匹配
        keyword_results = []
        query_keywords = self._extract_keywords(query)
        for keyword in query_keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in self.store.memory_index:
                for node_id in self.store.memory_index[keyword_lower]:
                    if node_id in self.store.graph.nodes:
                        keyword_results.append(self.store.graph.nodes[node_id])
        
        # 3. 最近记忆优先
        recent_results = []
        for node_id in self.recent_nodes:
            if node_id in self.store.graph.nodes:
                recent_results.append(self.store.graph.nodes[node_id])
        
        # 合并结果去重
        seen = set()
        all_results = []
        for results in [direct_results, keyword_results, recent_results]:
            for node in results:
                if node.id not in seen:
                    seen.add(node.id)
                    all_results.append(node)
        
        return [node.to_dict() for node in all_results[:k]]
    
    def get_context(self) -> List[Dict]:
        """获取当前会话上下文"""
        if self.current_session is None:
            return []
        
        context = []
        for node_id in self.current_session.nodes[-20:]:  # 最近20条
            if node_id in self.store.graph.nodes:
                context.append(self.store.graph.nodes[node_id].to_dict())
        
        return context
    
    def infer(self, concept: str) -> List[Dict]:
        """简单推理 - 查找相关概念"""
        nodes = self.store.graph.find_nodes_by_label(concept)
        if not nodes:
            return []
        
        results = []
        for node in nodes:
            # 获取邻居
            neighbors = self.store.graph.get_neighbors(node.id)
            for neighbor in neighbors:
                results.append({
                    "source": node.label,
                    "target": neighbor.label,
                    "relation": self._get_relation_type(node.id, neighbor.id)
                })
        
        return results
    
    def forget(self, knowledge_id: str) -> bool:
        """遗忘指定知识"""
        if knowledge_id in self.store.graph.nodes:
            del self.store.graph.nodes[knowledge_id]
            # 清理边
            to_delete = []
            for edge_id, edge in self.store.graph.edges.items():
                if edge.source_id == knowledge_id or edge.target_id == knowledge_id:
                    to_delete.append(edge_id)
            for edge_id in to_delete:
                del self.store.graph.edges[edge_id]
            
            # 清理索引
            for keyword, node_ids in self.store.memory_index.items():
                if knowledge_id in node_ids:
                    self.store.memory_index[keyword].remove(knowledge_id)
            
            self.store.save()
            return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取系统统计"""
        return {
            "total_nodes": len(self.store.graph.nodes),
            "total_edges": len(self.store.graph.edges),
            "total_sessions": len(self.store.sessions),
            "total_keywords": len(self.store.memory_index),
            "current_session": self.current_session.id if self.current_session else None,
            "recent_nodes": len(self.recent_nodes)
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """简单关键词提取"""
        stopwords = {'的', '是', '在', '和', '了', '着', '与', '及', '或', '但'}
        words = text.replace(',', ' ').replace('.', ' ').replace('，', ' ').replace('。', ' ').split()
        keywords = [w for w in words if w not in stopwords and len(w) > 1]
        return keywords[:10]
    
    def _get_relation_type(self, source_id: str, target_id: str) -> str:
        """查找两个节点间的关系"""
        for edge in self.store.graph.edges.values():
            if edge.source_id == source_id and edge.target_id == target_id:
                return edge.type.value
            if edge.target_id == source_id and edge.source_id == target_id:
                return f"reverse-{edge.type.value}"
        return "related_to"
