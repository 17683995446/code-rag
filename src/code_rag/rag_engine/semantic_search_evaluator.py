"""
增强的评估系统 - 支持语义相似度匹配
"""

import re
from typing import List, Dict, Any
from collections import Counter

try:
    from ..base_layer import get_logger
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)

logger = get_logger(__name__)


class SemanticEvaluator:
    """
    语义评估器
    支持多种相似度计算方式
    """

    def __init__(self):
        self.use_advanced = False

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算文本相似度
        尝试多种方法，从简单到复杂
        """
        # 1. 精确匹配
        if text1.lower() in text2.lower() or text2.lower() in text1.lower():
            return 0.9

        # 2. 关键词重叠
        keywords1 = self._extract_keywords(text1)
        keywords2 = self._extract_keywords(text2)
        keyword_sim = self._keyword_similarity(keywords1, keywords2)

        # 3. N-gram 相似度
        ngram_sim = self._ngram_similarity(text1, text2)

        # 4. 综合评分
        final_score = keyword_sim * 0.6 + ngram_sim * 0.4

        return final_score

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 转小写并清理
        text = text.lower()
        # 提取英文单词和中文
        words = re.findall(r'[a-zA-Z]{3,}|[\u4e00-\u9fff]+', text)

        # 停用词
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all',
            'can', 'had', 'her', 'was', 'one', 'our', 'out', 'has',
            'have', 'been', 'were', 'they', 'this', 'that', 'with',
            'from', 'your', 'what', 'when', 'where', 'which', 'their'
        }

        # 统计词频
        word_freq = Counter(words)
        # 选择有意义的词
        keywords = [w for w in words if w not in stop_words and word_freq[w] >= 1]

        return list(set(keywords))

    def _keyword_similarity(self, keywords1: List[str], keywords2: List[str]) -> float:
        """基于关键词的相似度"""
        if not keywords1 or not keywords2:
            return 0.0

        set1 = set(keywords1)
        set2 = set(keywords2)

        # Jaccard 相似度
        intersection = len(set1 & set2)
        union = len(set1 | set2)

        if union == 0:
            return 0.0

        return intersection / union

    def _ngram_similarity(self, text1: str, text2: str, n: int = 3) -> float:
        """N-gram 相似度"""
        # 清理文本
        text1 = re.sub(r'[^\w]', '', text1.lower())
        text2 = re.sub(r'[^\w]', '', text2.lower())

        if not text1 or not text2:
            return 0.0

        # 生成 n-grams
        def get_ngrams(text: str, n: int) -> set:
            return set(text[i:i+n] for i in range(len(text) - n + 1))

        ngrams1 = get_ngrams(text1, n)
        ngrams2 = get_ngrams(text2, n)

        if not ngrams1 or not ngrams2:
            return 0.0

        # Jaccard
        intersection = len(ngrams1 & ngrams2)
        union = len(ngrams1 | ngrams2)

        return intersection / union if union > 0 else 0.0

    def evaluate_retrieval(self, retrieved_docs: List[str],
                          expected_topics: List[str],
                          query: str) -> Dict[str, float]:
        """
        评估检索结果

        参数:
            retrieved_docs: 检索到的文档列表
            expected_topics: 期望的关键词列表
            query: 原始查询

        返回:
            包含各种评估指标的字典
        """
        metrics = {
            'precision': 0.0,
            'recall': 0.0,
            'f1': 0.0,
            'mrr': 0.0,
            'topic_coverage': 0.0,
            'semantic_score': 0.0
        }

        if not retrieved_docs or not expected_topics:
            return metrics

        # 计算每个检索文档的相关性
        relevance_scores = []
        for i, doc in enumerate(retrieved_docs):
            max_sim = 0.0
            for topic in expected_topics:
                sim = self.calculate_similarity(doc, topic)
                max_sim = max(max_sim, sim)

            # 排名折扣
            discount = 1.0 / (i + 1)
            relevance_scores.append(max_sim * discount)

            # 累积 MRR
            if i == 0 and max_sim > 0.3:
                metrics['mrr'] = 1.0
            elif i < len(retrieved_docs) and metrics['mrr'] == 0 and max_sim > 0.3:
                metrics['mrr'] = 1.0 / (i + 1)

        # 精确率：检索结果中相关的比例
        relevant_count = sum(1 for score in relevance_scores if score > 0.3)
        metrics['precision'] = relevant_count / len(retrieved_docs) if retrieved_docs else 0.0

        # 召回率：期望主题被检索到的比例
        matched_topics = set()
        for i, doc in enumerate(retrieved_docs):
            for topic in expected_topics:
                if self.calculate_similarity(doc, topic) > 0.3:
                    matched_topics.add(topic)

        metrics['recall'] = len(matched_topics) / len(expected_topics) if expected_topics else 0.0

        # F1
        if metrics['precision'] + metrics['recall'] > 0:
            metrics['f1'] = 2 * metrics['precision'] * metrics['recall'] / (metrics['precision'] + metrics['recall'])

        # 主题覆盖率
        metrics['topic_coverage'] = len(matched_topics) / len(expected_topics) if expected_topics else 0.0

        # 语义得分
        metrics['semantic_score'] = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.0

        return metrics


# 全局实例
_semantic_evaluator = None


def get_semantic_evaluator() -> SemanticEvaluator:
    """获取语义评估器实例"""
    global _semantic_evaluator
    if _semantic_evaluator is None:
        _semantic_evaluator = SemanticEvaluator()
    return _semantic_evaluator


def evaluate_retrieval_quick(retrieved_docs: List[str],
                             expected_keywords: List[str]) -> float:
    """
    快速评估检索结果
    返回综合得分 0-100
    """
    evaluator = get_semantic_evaluator()
    metrics = evaluator.evaluate_retrieval(retrieved_docs, expected_keywords, "")

    # 综合得分
    score = (
        metrics['precision'] * 30 +
        metrics['recall'] * 30 +
        metrics['f1'] * 25 +
        metrics['topic_coverage'] * 15
    )

    return min(100.0, score * 100)
