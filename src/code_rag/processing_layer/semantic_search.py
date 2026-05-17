"""
Code RAG v21.0 - 语义搜索增强
基于 TF-IDF 和简单向量化的语义搜索能力
"""

import re
import math
from typing import List, Dict, Tuple, Optional, Set
from collections import Counter, defaultdict
from dataclasses import dataclass, field
import hashlib


@dataclass
class Document:
    """文档"""
    id: str
    content: str
    language: str = "python"
    metadata: Dict = field(default_factory=dict)
    
    def get_tokens(self) -> List[str]:
        """获取词元"""
        tokens = re.findall(r'\b\w+\b', self.content.lower())
        return [t for t in tokens if len(t) > 2]
    
    def get_ngrams(self, n: int = 2) -> List[str]:
        """获取 N-grams"""
        tokens = self.get_tokens()
        return [' '.join(tokens[i:i+n]) for i in range(len(tokens)-n+1)]


@dataclass
class SearchResult:
    """搜索结果"""
    document: Document
    score: float
    matches: List[str] = field(default_factory=list)
    highlights: List[str] = field(default_factory=list)


class TFIDFIndex:
    """TF-IDF 索引"""
    
    def __init__(self):
        self.documents: Dict[str, Document] = {}
        self.doc_term_freqs: Dict[str, Dict[str, int]] = {}
        self.idf_scores: Dict[str, float] = {}
        self.vocabulary: Set[str] = set()
    
    def add_document(self, doc: Document):
        """添加文档"""
        self.documents[doc.id] = doc
        
        tokens = doc.get_tokens()
        self.doc_term_freqs[doc.id] = Counter(tokens)
        self.vocabulary.update(tokens)
        
        self._update_idf()
    
    def _update_idf(self):
        """更新 IDF 分数"""
        num_docs = len(self.documents)
        if num_docs == 0:
            return
        
        doc_freq = defaultdict(int)
        for term_freqs in self.doc_term_freqs.values():
            for term in term_freqs:
                doc_freq[term] += 1
        
        for term in self.vocabulary:
            df = doc_freq.get(term, 0)
            self.idf_scores[term] = math.log(num_docs / (1 + df))
    
    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """搜索"""
        query_tokens = re.findall(r'\b\w+\b', query.lower())
        query_tokens = [t for t in query_tokens if len(t) > 2]
        
        if not query_tokens:
            return []
        
        results = []
        for doc_id, doc in self.documents.items():
            score = self._calculate_score(doc_id, query_tokens)
            if score > 0:
                matches = [t for t in query_tokens if t in doc.content.lower()]
                results.append(SearchResult(
                    document=doc,
                    score=score,
                    matches=matches
                ))
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def _calculate_score(self, doc_id: str, query_tokens: List[str]) -> float:
        """计算 TF-IDF 分数"""
        if doc_id not in self.doc_term_freqs:
            return 0.0
        
        term_freqs = self.doc_term_freqs[doc_id]
        score = 0.0
        
        for term in query_tokens:
            tf = term_freqs.get(term, 0)
            idf = self.idf_scores.get(term, 0)
            score += tf * idf
        
        doc_length = sum(term_freqs.values())
        if doc_length > 0:
            score = score / math.sqrt(doc_length)
        
        return score


class SemanticMatcher:
    """语义匹配器"""
    
    def __init__(self):
        self.documents: Dict[str, Document] = {}
        self.keyword_index: Dict[str, List[str]] = defaultdict(list)
    
    def add_document(self, doc: Document):
        """添加文档"""
        self.documents[doc.id] = doc
        
        tokens = doc.get_tokens()
        for token in tokens:
            self.keyword_index[token].append(doc.id)
    
    def find_semantic_matches(self, query: str, threshold: float = 0.3) -> List[Tuple[Document, float]]:
        """查找语义匹配"""
        query_lower = query.lower()
        query_tokens = set(re.findall(r'\b\w+\b', query_lower))
        
        results = []
        for doc in self.documents.values():
            doc_tokens = set(doc.get_tokens())
            
            overlap = len(query_tokens & doc_tokens)
            union = len(query_tokens | doc_tokens)
            
            if union > 0:
                jaccard_score = overlap / union
                
                if jaccard_score >= threshold:
                    results.append((doc, jaccard_score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def suggest_related(self, term: str, limit: int = 5) -> List[str]:
        """建议相关术语"""
        term_lower = term.lower()
        suggestions = []
        
        for doc_term in self.keyword_index:
            if term_lower in doc_term or doc_term in term_lower:
                if doc_term != term_lower:
                    suggestions.append(doc_term)
        
        return suggestions[:limit]


class CodeSearchEngine:
    """代码搜索引擎"""
    
    def __init__(self):
        self.tfidf_index = TFIDFIndex()
        self.semantic_matcher = SemanticMatcher()
        self.entity_index: Dict[str, List[str]] = defaultdict(list)
    
    def index_code(self, code_id: str, content: str, language: str = "python", entities: List[Dict] = None):
        """索引代码"""
        doc = Document(
            id=code_id,
            content=content,
            language=language
        )
        
        self.tfidf_index.add_document(doc)
        self.semantic_matcher.add_document(doc)
        
        if entities:
            for entity in entities:
                entity_type = entity.get('type', 'unknown')
                self.entity_index[entity_type].append(code_id)
    
    def search_by_keyword(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """关键词搜索"""
        return self.tfidf_index.search(query, top_k)
    
    def search_by_semantics(self, query: str, threshold: float = 0.3) -> List[Tuple[Document, float]]:
        """语义搜索"""
        return self.semantic_matcher.find_semantic_matches(query, threshold)
    
    def search_entities(self, entity_type: str) -> List[str]:
        """搜索特定类型的实体"""
        return self.entity_index.get(entity_type, [])
    
    def combined_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """组合搜索"""
        tfidf_results = self.search_by_keyword(query, top_k * 2)
        semantic_results = self.search_by_semantics(query, 0.2)
        
        combined = {}
        
        for result in tfidf_results:
            combined[result.document.id] = {
                'document': result.document,
                'tfidf_score': result.score,
                'semantic_score': 0.0,
                'combined_score': result.score
            }
        
        for doc, score in semantic_results:
            if doc.id in combined:
                combined[doc.id]['semantic_score'] = score
                combined[doc.id]['combined_score'] += score
            else:
                combined[doc.id] = {
                    'document': doc,
                    'tfidf_score': 0.0,
                    'semantic_score': score,
                    'combined_score': score
                }
        
        sorted_results = sorted(combined.values(), key=lambda x: x['combined_score'], reverse=True)
        return sorted_results[:top_k]
    
    def get_statistics(self) -> Dict:
        """获取索引统计"""
        return {
            'total_documents': len(self.tfidf_index.documents),
            'vocabulary_size': len(self.tfidf_index.vocabulary),
            'entity_types': len(self.entity_index),
            'entities_by_type': {
                entity_type: len(doc_ids) 
                for entity_type, doc_ids in self.entity_index.items()
            }
        }


class QueryExpander:
    """查询扩展器"""
    
    def __init__(self):
        self.synonyms: Dict[str, List[str]] = {
            'function': ['method', 'procedure', 'routine'],
            'class': ['type', 'object', 'structure'],
            'variable': ['var', 'property', 'field', 'attribute'],
            'loop': ['iteration', 'iterate', 'for', 'while'],
            'return': ['output', 'result', 'yield'],
        }
    
    def expand_query(self, query: str) -> List[str]:
        """扩展查询"""
        tokens = re.findall(r'\b\w+\b', query.lower())
        expanded = [query.lower()]
        
        for token in tokens:
            if token in self.synonyms:
                for synonym in self.synonyms[token]:
                    expanded.append(query.lower().replace(token, synonym))
        
        return expanded
    
    def suggest_alternatives(self, query: str) -> List[str]:
        """建议替代查询"""
        tokens = re.findall(r'\b\w+\b', query.lower())
        suggestions = []
        
        for token in tokens:
            if token in self.synonyms:
                for synonym in self.synonyms[token]:
                    suggestion = query.lower().replace(token, synonym)
                    if suggestion != query.lower():
                        suggestions.append(suggestion)
        
        return suggestions[:3]


def create_search_engine() -> CodeSearchEngine:
    """创建搜索引擎实例"""
    return CodeSearchEngine()
