"""
增强的检索算法 - 产品级
支持查询预处理、重排序、多路召回
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

from .logger import get_logger
from .settings import get_settings

logger = get_logger(__name__)


class QueryPreprocessor:
    """
    查询预处理器
    支持拼写纠错、同义词扩展、查询改写
    """

    def __init__(self):
        self.settings = get_settings()
        self._synonym_dict = self._load_synonyms()

    def preprocess(self, query: str) -> Dict[str, Any]:
        """预处理查询"""
        # 分词
        tokens = self._tokenize(query)

        # 同义词扩展
        expanded_tokens = self._expand_synonyms(tokens)

        # 查询改写
        rewritten = self._rewrite_query(query, expanded_tokens)

        return {
            'original': query,
            'tokens': tokens,
            'expanded_tokens': expanded_tokens,
            'rewritten': rewritten,
            'filters': self._extract_filters(query)
        }

    def _tokenize(self, query: str) -> List[str]:
        """分词"""
        # 简单分词
        tokens = re.findall(r'\w+', query.lower())
        return [t for t in tokens if len(t) > 1]

    def _expand_synonyms(self, tokens: List[str]) -> List[str]:
        """同义词扩展"""
        expanded = list(tokens)

        synonym_map = {
            'vector': ['embedding', 'vectorization'],
            'db': ['database', 'datastore'],
            'rag': ['retrieval', 'rag system'],
            'code': ['source', 'programming'],
            'python': ['py', 'python3'],
            'js': ['javascript', 'node'],
            'ts': ['typescript', 'ts'],
        }

        for token in tokens:
            if token in synonym_map:
                expanded.extend(synonym_map[token])

        return list(set(expanded))

    def _rewrite_query(self, query: str, tokens: List[str]) -> str:
        """查询改写"""
        rewritten = query

        # 简单改写规则
        if 'what is' in query.lower():
            rewritten = rewritten.replace('what is', 'define')
        if 'how to' in query.lower():
            rewritten = rewritten.replace('how to', 'tutorial')

        return rewritten

    def _extract_filters(self, query: str) -> Dict[str, Any]:
        """提取过滤条件"""
        filters = {}

        # 语言过滤
        languages = ['python', 'javascript', 'java', 'c++', 'go', 'rust']
        for lang in languages:
            if lang in query.lower():
                filters['language'] = lang
                break

        # 文件类型过滤
        if '.py' in query:
            filters['extension'] = '.py'
        elif '.js' in query:
            filters['extension'] = '.js'

        return filters

    def _load_synonyms(self) -> Dict[str, List[str]]:
        """加载同义词词典"""
        return {
            'vector': ['embedding', 'vectorization', 'vec'],
            'search': ['query', 'find', 'lookup'],
            'database': ['db', 'datastore', 'storage'],
            'fast': ['quick', 'high-speed', 'efficient'],
            'ai': ['artificial intelligence', 'machine learning', 'ml'],
            'api': ['interface', 'endpoint', 'service'],
        }


class Reranker:
    """
    结果重排序器
    支持基于相关性的二次排序
    """

    def __init__(self, use_cross_encoder: bool = False):
        self.settings = get_settings()
        self.use_cross_encoder = use_cross_encoder
        self._use_fallback = True

    def rerank(self, query: str, results: List[Any],
              top_k: int = 5) -> List[Any]:
        """重排序结果"""
        if not results:
            return results

        # 计算相关性分数
        scored_results = []
        for result in results:
            score = self._calculate_relevance(query, result)
            scored_results.append((score, result))

        # 排序
        scored_results.sort(key=lambda x: x[0], reverse=True)

        # 返回top_k
        return [r for _, r in scored_results[:top_k]]

    def _calculate_relevance(self, query: str, result: Any) -> float:
        """计算相关性分数"""
        text = getattr(result, 'text', '') or ''

        # 词匹配分数
        query_words = set(query.lower().split())
        text_words = set(text.lower().split())
        match_score = len(query_words & text_words) / len(query_words) if query_words else 0

        # 位置分数（查询词在开头更重要）
        position_score = 0.0
        query_lower = query.lower()
        text_lower = text.lower()
        if query_lower in text_lower:
            position_score = 0.3
            # 查询在文本开头给更高分
            if text_lower.startswith(query_lower):
                position_score = 0.5

        # 长度惩罚（避免过长或过短的文本）
        length = len(text)
        length_score = 1.0
        if length < 50:
            length_score = 0.7
        elif length > 1000:
            length_score = 0.8

        # 综合分数
        relevance = (match_score * 0.4 +
                    position_score * 0.3 +
                    length_score * 0.3)

        return relevance


class MultiRetrieval:
    """
    多路召回
    结合向量搜索和关键词搜索
    """

    def __init__(self):
        self.settings = get_settings()
        self.vector_weight = 0.6
        self.keyword_weight = 0.4

    def retrieve(self, query: str,
               vector_results: List[Any],
               keyword_results: List[Any],
               top_k: int = 5) -> List[Any]:
        """多路召回融合"""
        if not vector_results and not keyword_results:
            return []

        # 创建结果映射
        result_map = {}

        # 添加向量搜索结果
        for i, result in enumerate(vector_results):
            doc_id = getattr(result, 'doc_id', i)
            result_map[doc_id] = {
                'result': result,
                'vector_score': getattr(result, 'score', 1.0 / (i + 1)),
                'keyword_score': 0.0
            }

        # 添加关键词搜索结果
        for i, result in enumerate(keyword_results):
            doc_id = getattr(result, 'doc_id', i)
            if doc_id in result_map:
                result_map[doc_id]['keyword_score'] = getattr(result, 'score', 1.0 / (i + 1))
            else:
                result_map[doc_id] = {
                    'result': result,
                    'vector_score': 0.0,
                    'keyword_score': getattr(result, 'score', 1.0 / (i + 1))
                }

        # 计算综合分数
        scored_results = []
        for doc_id, data in result_map.items():
            vector_score = data['vector_score']
            keyword_score = data['keyword_score']

            # 归一化
            max_vector = max(d['vector_score'] for d in result_map.values()) or 1.0
            max_keyword = max(d['keyword_score'] for d in result_map.values()) or 1.0

            norm_vector = vector_score / max_vector
            norm_keyword = keyword_score / max_keyword

            # 综合分数
            combined = (self.vector_weight * norm_vector +
                       self.keyword_weight * norm_keyword)

            scored_results.append((combined, data['result']))

        # 排序并返回
        scored_results.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored_results[:top_k]]


class ContextWindow:
    """
    上下文窗口
    增强检索结果的上下文感知能力
    """

    def __init__(self, window_size: int = 3):
        self.window_size = window_size
        self._context_cache = {}

    def enhance_results(self, results: List[Any],
                       all_documents: Dict[str, Any]) -> List[Any]:
        """增强结果，添加上下文"""
        enhanced_results = []

        for result in results:
            doc_id = getattr(result, 'doc_id', id(result))

            # 获取上下文
            context = self._get_context(doc_id, all_documents)

            # 创建增强结果
            enhanced = EnhancedSearchResult(
                original_result=result,
                context=context,
                relevance_score=getattr(result, 'score', 0.0)
            )
            enhanced_results.append(enhanced)

        return enhanced_results

    def _get_context(self, doc_id: str,
                    all_documents: Dict[str, Any]) -> Dict[str, Any]:
        """获取上下文"""
        if doc_id in self._context_cache:
            return self._context_cache[doc_id]

        context = {
            'before': [],
            'after': [],
            'related': []
        }

        # 简单的上下文获取
        doc_ids = list(all_documents.keys())
        if doc_id in doc_ids:
            idx = doc_ids.index(doc_id)

            # 前后文档
            start = max(0, idx - self.window_size)
            end = min(len(doc_ids), idx + self.window_size + 1)

            before_ids = doc_ids[start:idx]
            after_ids = doc_ids[idx+1:end]

            context['before'] = [all_documents.get(id_) for id_ in before_ids]
            context['after'] = [all_documents.get(id_) for id_ in after_ids]

        self._context_cache[doc_id] = context
        return context


class EnhancedSearchResult:
    """增强的搜索结果"""

    def __init__(self, original_result, context: Dict[str, Any],
                relevance_score: float):
        self.original_result = original_result
        self.context = context
        self.relevance_score = relevance_score
        self.text = getattr(original_result, 'text', '')
        self.metadata = getattr(original_result, 'metadata', {})
        self.score = relevance_score
        self.doc_id = getattr(original_result, 'doc_id', id(original_result))
        self.distance = getattr(original_result, 'distance', None)

    def __repr__(self):
        return f"<EnhancedResult: {self.text[:50]}... score={self.relevance_score:.3f}>"


class RetrievalPipeline:
    """
    检索流水线
    整合查询预处理、多路召回、重排序、上下文增强
    """

    def __init__(self):
        self.query_preprocessor = QueryPreprocessor()
        self.reranker = Reranker()
        self.multi_retrieval = MultiRetrieval()
        self.context_window = ContextWindow()

    def retrieve(self, query: str,
                vector_store,
                bm25_index=None,
                all_documents: Optional[Dict] = None,
                top_k: int = 5) -> List[Any]:
        """完整检索流程"""

        # 1. 查询预处理
        processed = self.query_preprocessor.preprocess(query)
        logger.debug(f"查询预处理: {processed}")

        # 2. 向量搜索
        vector_results = vector_store.search(
            self._get_query_vector(query),
            k=top_k * 2
        )

        # 3. 关键词搜索（如果有）
        keyword_results = []
        if bm25_index:
            keyword_results = bm25_index.search(
                query,
                k=top_k * 2
            )

        # 4. 多路召回融合
        if keyword_results:
            results = self.multi_retrieval.retrieve(
                query,
                vector_results,
                keyword_results,
                top_k
            )
        else:
            results = vector_results[:top_k]

        # 5. 重排序
        results = self.reranker.rerank(query, results, top_k)

        # 6. 上下文增强
        if all_documents:
            results = self.context_window.enhance_results(
                results,
                all_documents
            )

        return results

    def _get_query_vector(self, query: str):
        """获取查询向量（简化实现）"""
        # 使用简化的向量生成
        words = query.lower().split()
        dim = 384
        vec = [0.0] * dim
        for i, word in enumerate(words):
            for j, char in enumerate(word):
                if j < dim:
                    vec[j] += ord(char) / 255.0
        return vec


# 全局检索流水线实例
_retrieval_pipeline: Optional[RetrievalPipeline] = None


def get_retrieval_pipeline() -> RetrievalPipeline:
    """获取检索流水线"""
    global _retrieval_pipeline
    if _retrieval_pipeline is None:
        _retrieval_pipeline = RetrievalPipeline()
    return _retrieval_pipeline
