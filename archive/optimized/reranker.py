import os
import re
import time
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import threading


class QueryIntent(Enum):
    EXACT_LINE = "exact_line"
    SYMBOL_SEARCH = "symbol_search"
    SEMANTIC = "semantic"
    MULTI_HOP = "multi_hop"
    CODE_EXPLANATION = "code_explanation"
    BUG_FINDING = "bug_finding"
    REFACTORING = "refactoring"
    IMPLEMENTATION = "implementation"


@dataclass
class RerankResult:
    chunk_id: str
    original_score: float
    rerank_score: float
    metadata: Dict = field(default_factory=dict)


@dataclass
class IntentResult:
    intent: QueryIntent
    confidence: float
    entities: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    filters: Dict = field(default_factory=dict)


class CrossEncoderReranker:
    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        device: str = "cpu",
        batch_size: int = 32
    ):
        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self.model = None
        self._lock = threading.Lock()

    def _load_model(self):
        if self.model is not None:
            return True

        with self._lock:
            if self.model is not None:
                return True

            try:
                from sentence_transformers import CrossEncoder
                self.model = CrossEncoder(
                    self.model_name,
                    max_length=512,
                    device=self.device
                )
                return True
            except ImportError:
                return False

    def rerank(
        self,
        query: str,
        candidates: List[Dict],
        top_k: int = 10
    ) -> List[Dict]:
        if not candidates:
            return []

        loaded = self._load_model()

        if not loaded:
            return self._fallback_rerank(query, candidates, top_k)

        pairs = [(query, c.get('content', '') or c.get('metadata', {}).get('content', ''))
                 for c in candidates]

        scores = self.model.predict(pairs, show_progress_bar=False)

        scored_results = []
        for i, candidate in enumerate(candidates):
            scored_results.append({
                **candidate,
                'rerank_score': float(scores[i]),
                'original_score': candidate.get('score', 0),
                'combined_score': float(scores[i]) * 0.7 + candidate.get('score', 0) * 0.3
            })

        scored_results.sort(key=lambda x: x['combined_score'], reverse=True)

        return scored_results[:top_k]

    def _fallback_rerank(
        self,
        query: str,
        candidates: List[Dict],
        top_k: int
    ) -> List[Dict]:
        query_terms = set(query.lower().split())

        for candidate in candidates:
            content = candidate.get('content', '') or candidate.get('metadata', {}).get('content', '')
            content_lower = content.lower()

            term_matches = sum(1 for term in query_terms if term in content_lower)
            candidate['rerank_score'] = term_matches / max(len(query_terms), 1)
            candidate['combined_score'] = (
                candidate['rerank_score'] * 0.7 +
                candidate.get('score', 0) * 0.3
            )

        candidates.sort(key=lambda x: x['combined_score'], reverse=True)
        return candidates[:top_k]


class BM25Reranker:
    def __init__(
        self,
        k1: float = 1.5,
        b: float = 0.75,
        avg_doc_len: float = 100
    ):
        self.k1 = k1
        self.b = b
        self.avg_doc_len = avg_doc_len
        self.corpus_size = 0
        self.avgdl = avg_doc_len
        self.doc_freqs = {}
        self.idf = {}
        self.doc_len = []

    def fit(self, documents: List[str]):
        self.corpus_size = len(documents)
        self.doc_len = []
        self.doc_freqs = {}

        for doc in documents:
            self.doc_len.append(len(doc.split()))

            freq = {}
            for word in doc.lower().split():
                freq[word] = freq.get(word, 0) + 1

            for word, count in freq.items():
                self.doc_freqs[word] = self.doc_freqs.get(word, 0) + 1

        self.avgdl = sum(self.doc_len) / max(self.corpus_size, 1)

        for word, freq in self.doc_freqs.items():
            self.idf[word] = np.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1)

    def score(self, query: str, doc_idx: int) -> float:
        doc = self.doc_len[doc_idx] if doc_idx < len(self.doc_len) else 0
        score = 0.0

        freq = {}
        for word in query.lower().split():
            freq[word] = freq.get(word, 0) + 1

        for word, term_freq in freq.items():
            if word in self.idf:
                idf = self.idf[word]
                tf = term_freq
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc / self.avgdl)
                score += idf * numerator / denominator

        return score

    def rerank(
        self,
        query: str,
        candidates: List[Dict],
        top_k: int = 10
    ) -> List[Dict]:
        if not candidates:
            return []

        docs = [c.get('content', '') or c.get('metadata', {}).get('content', '')
                for c in candidates]
        self.fit(docs)

        for i, candidate in enumerate(candidates):
            bm25_score = self.score(query, i)
            candidate['bm25_score'] = bm25_score
            candidate['combined_score'] = (
                bm25_score * 0.6 +
                candidate.get('score', 0) * 0.4
            )

        candidates.sort(key=lambda x: x['combined_score'], reverse=True)
        return candidates[:top_k]


class QueryIntentClassifier:
    def __init__(self):
        self.patterns = {
            QueryIntent.EXACT_LINE: [
                r'^(\S+):(\d+)$',
                r'line\s+(\d+)',
                r':(\d+)',
            ],
            QueryIntent.SYMBOL_SEARCH: [
                r'^(?:def|class|function|interface|type)\s+(\w+)',
                r'where\s+(?:is|are)\s+(\w+)',
                r'find\s+(?:the\s+)?(?:definition|implementation)\s+of\s+(\w+)',
            ],
            QueryIntent.CODE_EXPLANATION: [
                r'(?:explain|what\s+does|how\s+does|describe|tell\s+me\s+about)',
                r'(?:what\s+is|what\s+are)\s+the\s+\w+',
            ],
            QueryIntent.BUG_FINDING: [
                r'(?:fix|bug|error|issue|problem|wrong|incorrect|broken)',
                r'(?:doesn\'t|does\s+not|won\'t)\s+work',
            ],
            QueryIntent.REFACTORING: [
                r'(?:refactor|optimize|improve|simplify|clean\s+up)',
                r'(?:better\s+way|alternative|reimplement)',
            ],
            QueryIntent.IMPLEMENTATION: [
                r'(?:implement|create|write|add|build|make)\s+(?:a|new|the\s+)?',
            ],
        }

        self.entity_patterns = {
            'file_path': r'(?:in|from)\s+([^\s]+\.(?:py|js|ts|java|cpp|c|go|rs))',
            'function_name': r'(?:function|method|def)\s+(\w+)',
            'class_name': r'class\s+(\w+)',
            'import': r'(?:import|from)\s+([\w.]+)',
        }

    def classify(self, query: str) -> IntentResult:
        query_lower = query.lower().strip()

        intent_scores = {}
        for intent, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    intent_scores[intent] = intent_scores.get(intent, 0) + 1

        if not intent_scores:
            intent = QueryIntent.SEMANTIC
            confidence = 0.5
        else:
            max_score = max(intent_scores.values())
            intent = max(intent_scores, key=intent_scores.get)
            confidence = min(max_score / len(self.patterns[intent]), 1.0)

        entities = self._extract_entities(query)
        keywords = self._extract_keywords(query)
        filters = self._build_filters(query, entities)

        return IntentResult(
            intent=intent,
            confidence=confidence,
            entities=entities,
            keywords=keywords,
            filters=filters
        )

    def _extract_entities(self, query: str) -> List[str]:
        entities = []

        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, query, re.IGNORECASE)
            entities.extend(matches)

        camel_case = re.findall(r'[A-Z][a-z]+(?:[A-Z][a-z]+)+', query)
        entities.extend(camel_case)

        snake_case = re.findall(r'[a-z]+_[a-z]+', query)
        entities.extend(snake_case)

        return list(set(entities))

    def _extract_keywords(self, query: str) -> List[str]:
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'shall',
            'can', 'need', 'to', 'of', 'in', 'for', 'on', 'with', 'at',
            'by', 'from', 'as', 'that', 'this', 'these', 'those', 'it',
            'its', 'and', 'or', 'but', 'not', 'no', 'what', 'which',
            'who', 'whom', 'how', 'where', 'when', 'why', 'find'
        }

        words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', query.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        return list(set(keywords))

    def _build_filters(self, query: str, entities: List[str]) -> Dict:
        filters = {}

        file_match = re.search(r'(?:in|from)\s+([^\s]+\.(?:py|js|ts|java|cpp|c|go|rs))', query)
        if file_match:
            filters['file_path'] = file_match.group(1)

        import_match = re.search(r'(?:import|from)\s+([\w.]+)', query)
        if import_match:
            filters['import'] = import_match.group(1)

        if 'test' in query.lower():
            filters['is_test'] = True

        return filters


class HybridReranker:
    def __init__(self, rerankers: List = None):
        self.rerankers = rerankers or [
            CrossEncoderReranker(),
            BM25Reranker(),
        ]
        self.weights = [0.6, 0.4]

    def rerank(
        self,
        query: str,
        candidates: List[Dict],
        top_k: int = 10
    ) -> List[Dict]:
        if not candidates:
            return []

        all_scores = []
        for reranker in self.rerankers:
            try:
                scored = reranker.rerank(query, candidates, top_k=len(candidates))
                all_scores.append(scored)
            except Exception:
                pass

        if not all_scores:
            return candidates[:top_k]

        for i, candidate in enumerate(candidates):
            total_score = 0
            for j, scores in enumerate(all_scores):
                if i < len(scores):
                    weight = self.weights[j] if j < len(self.weights) else 1.0 / len(all_scores)
                    total_score += weight * scores[i].get('combined_score', scores[i].get('score', 0))

            candidate['hybrid_score'] = total_score

        candidates.sort(key=lambda x: x.get('hybrid_score', x.get('score', 0)), reverse=True)

        return candidates[:top_k]


class ResultDeduplicator:
    def __init__(
        self,
        similarity_threshold: float = 0.85,
        use_embedding: bool = False
    ):
        self.similarity_threshold = similarity_threshold
        self.use_embedding = use_embedding

    def deduplicate(
        self,
        results: List[Dict],
        top_k: int = 10
    ) -> List[Dict]:
        if not results:
            return []

        seen = []
        for result in results:
            content = result.get('content', '') or result.get('metadata', {}).get('content', '')

            is_dup = False
            for s in seen:
                s_content = s.get('content', '') or s.get('metadata', {}).get('content', '')
                sim = self._calculate_similarity(content, s_content)

                if sim > self.similarity_threshold:
                    is_dup = True
                    break

            if not is_dup:
                result['similarity_to_nearest'] = self._find_nearest_similarity(content, seen)
                seen.append(result)

        return seen[:top_k]

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        if not text1 or not text2:
            return 0.0

        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        jaccard = len(intersection) / len(union)

        common_lines = 0
        lines1 = set(text1.split('\n'))
        lines2 = set(text2.split('\n'))
        if lines1 and lines2:
            common_lines = len(lines1 & lines2) / max(len(lines1), len(lines2))

        return jaccard * 0.7 + common_lines * 0.3

    def _find_nearest_similarity(self, content: str, seen: List[Dict]) -> float:
        if not seen:
            return 0.0

        max_sim = 0.0
        for s in seen:
            s_content = s.get('content', '') or s.get('metadata', {}).get('content', '')
            sim = self._calculate_similarity(content, s_content)
            max_sim = max(max_sim, sim)

        return max_sim


class DiversitySampler:
    def __init__(
        self,
        diversity_weight: float = 0.3,
        relevance_weight: float = 0.7
    ):
        self.diversity_weight = diversity_weight
        self.relevance_weight = relevance_weight

    def sample(
        self,
        results: List[Dict],
        top_k: int = 10,
        min_diversity: float = 0.5
    ) -> List[Dict]:
        if len(results) <= top_k:
            return results

        selected = []
        remaining = list(results)

        if remaining:
            top = remaining.pop(0)
            top['diversity_score'] = 1.0
            selected.append(top)

        while len(selected) < top_k and remaining:
            best_score = -float('inf')
            best_idx = 0

            for i, candidate in enumerate(remaining):
                relevance = candidate.get('score', 0) or candidate.get('combined_score', 0)

                diversity = self._calculate_diversity(
                    candidate,
                    selected
                )

                combined = (
                    self.relevance_weight * relevance +
                    self.diversity_weight * diversity
                )

                if diversity < min_diversity:
                    combined *= 0.5

                if combined > best_score:
                    best_score = combined
                    best_idx = i

            if remaining:
                selected_candidate = remaining.pop(best_idx)
                selected_candidate['diversity_score'] = self._calculate_diversity(
                    selected_candidate, selected
                )
                selected.append(selected_candidate)

        return selected

    def _calculate_diversity(self, candidate: Dict, selected: List[Dict]) -> float:
        if not selected:
            return 1.0

        content = candidate.get('content', '') or candidate.get('metadata', {}).get('content', '')

        min_sim = float('inf')
        for s in selected:
            s_content = s.get('content', '') or s.get('metadata', {}).get('content', '')
            sim = self._jaccard_similarity(content, s_content)
            min_sim = min(min_sim, sim)

        return 1.0 - min_sim if min_sim != float('inf') else 1.0

    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)


class MMRSampler:
    def __init__(
        self,
        lambda_param: float = 0.5,
        embedding_engine=None
    ):
        self.lambda_param = lambda_param
        self.embedding_engine = embedding_engine

    def select(
        self,
        query: str,
        candidates: List[Dict],
        top_k: int = 10
    ) -> List[Dict]:
        selected = []
        remaining = list(candidates)

        query_embedding = None
        if self.embedding_engine:
            try:
                query_embedding = self.embedding_engine.encode([query], show_progress=False)[0]
            except Exception:
                pass

        while len(selected) < top_k and remaining:
            best_score = -float('inf')
            best_idx = 0

            for i, candidate in enumerate(remaining):
                relevance = candidate.get('score', 0) or candidate.get('combined_score', 0)

                diversity = 0.0
                if query_embedding and self.embedding_engine:
                    cand_embedding = candidate.get('embedding')
                    if cand_embedding is None:
                        try:
                            content = candidate.get('content', '') or candidate.get('metadata', {}).get('content', '')
                            cand_embedding = self.embedding_engine.encode([content], show_progress=False)[0]
                        except Exception:
                            cand_embedding = None

                    if cand_embedding is not None:
                        diversity = 1 - self._cosine_similarity(query_embedding, cand_embedding)

                elif selected:
                    content = candidate.get('content', '') or candidate.get('metadata', {}).get('content', '')
                    diversity = self._text_diversity(content, selected)

                mmr_score = self.lambda_param * relevance + (1 - self.lambda_param) * diversity

                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = i

            if remaining:
                selected.append(remaining.pop(best_idx))

        return selected

    def _cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        dot = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot / (norm1 * norm2)

    def _text_diversity(self, content: str, selected: List[Dict]) -> float:
        if not selected:
            return 1.0

        words = set(content.lower().split())
        max_novelty = 0.0

        for s in selected:
            s_content = s.get('content', '') or s.get('metadata', {}).get('content', '')
            s_words = set(s_content.lower().split())

            novelty = len(words - s_words) / max(len(words), 1)
            max_novelty = max(max_novelty, novelty)

        return max_novelty
