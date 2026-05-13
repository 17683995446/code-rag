import os
import re
import time
import json
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor

from optimized.reranker import (
    CrossEncoderReranker, BM25Reranker, HybridReranker,
    QueryIntentClassifier, QueryIntent, IntentResult,
    ResultDeduplicator, DiversitySampler, MMRSampler
)
from optimized.context import (
    ContextCompressor, ContextWindow, DynamicContextManager,
    TokenEstimator, QueryRelevanceFilter, RelevanceFeedback
)
from optimized.multilingual import (
    MultilingualEmbeddingEngine, LanguageDetector, CodeAwareEmbedder
)
from optimized.vector_db import FlatIndex, IVFIndex, HNSWIndex, VectorConfig
from optimized.cache import CacheFacade, CacheConfig
from optimized.storage import StorageFacade
from optimized.monitoring import MetricsCollector, PerformanceMonitor


class RetrievalStrategy(Enum):
    EXACT = "exact"
    KEYWORD = "keyword"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    MULTI_HOP = "multi_hop"


@dataclass
class RetrievalConfig:
    strategy: RetrievalStrategy = RetrievalStrategy.HYBRID
    top_k_initial: int = 50
    top_k_final: int = 10
    use_reranker: bool = True
    use_deduplication: bool = True
    use_diversity: bool = False
    max_context_tokens: int = 4000
    language: str = "auto"
    enable_multilingual: bool = True


@dataclass
class RetrievalResult:
    chunks: List[Dict]
    intent: IntentResult = None
    context_window: ContextWindow = None
    query: str = ""
    total_time_ms: float = 0
    metadata: Dict = field(default_factory=dict)


@dataclass
class PipelineStats:
    query_classification_ms: float = 0
    embedding_ms: float = 0
    vector_search_ms: float = 0
    rerank_ms: float = 0
    deduplication_ms: float = 0
    context_compression_ms: float = 0
    total_ms: float = 0
    cache_hits: int = 0
    chunks_before_filter: int = 0
    chunks_after_filter: int = 0


class QueryPreprocessor:
    def __init__(self):
        self.intent_classifier = QueryIntentClassifier()
        self.language_detector = LanguageDetector()

    def preprocess(self, query: str) -> Dict:
        query = self._clean_query(query)

        intent = self.intent_classifier.classify(query)

        language = self.language_detector.detect(query)

        expanded_query = self._expand_query(query, intent)

        return {
            "original": query,
            "cleaned": query,
            "expanded": expanded_query,
            "intent": intent,
            "language": language,
            "filters": intent.filters,
            "entities": intent.entities,
            "keywords": intent.keywords
        }

    def _clean_query(self, query: str) -> str:
        query = query.strip()

        query = re.sub(r'\s+', ' ', query)

        query = re.sub(r'[^\w\s\-:./\\@#$%&*()+=\[\]{}|,<>?\'\"]', '', query)

        return query

    def _expand_query(self, query: str, intent: IntentResult) -> str:
        expansions = []

        for entity in intent.entities:
            if len(entity) > 2:
                expansions.append(entity)

        for keyword in intent.keywords[:5]:
            if len(keyword) > 3:
                expansions.append(keyword)

        if intent.intent == QueryIntent.SYMBOL_SEARCH:
            for entity in intent.entities:
                snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', entity).lower()
                camel_case = ''.join(word.title() for word in re.split(r'[_\s]+', entity))
                expansions.extend([snake_case, camel_case])

        expanded = query
        if expansions:
            expanded = query + " " + " ".join(expansions)

        return expanded


class RetrievalPipeline:
    def __init__(
        self,
        config: RetrievalConfig = None,
        storage: StorageFacade = None,
        embedding_engine = None
    ):
        self.config = config or RetrievalConfig()

        self.preprocessor = QueryPreprocessor()

        if embedding_engine:
            self.embedding_engine = embedding_engine
        else:
            if self.config.enable_multilingual:
                self.embedding_engine = MultilingualEmbeddingEngine()
            else:
                from optimized.embedding import EmbeddingEngine
                self.embedding_engine = EmbeddingEngine()

        self.vector_index = None
        self.storage = storage

        self.reranker = HybridReranker([
            CrossEncoderReranker(),
            BM25Reranker()
        ]) if self.config.use_reranker else None

        self.deduplicator = ResultDeduplicator() if self.config.use_deduplication else None

        self.diversity_sampler = DiversitySampler() if self.config.use_diversity else None

        self.mmr_sampler = MMRSampler(embedding_engine=self.embedding_engine)

        self.context_manager = DynamicContextManager(
            max_tokens=self.config.max_context_tokens
        )

        self.cache = None

        self.metrics = MetricsCollector("retrieval")
        self.monitor = PerformanceMonitor(self.metrics)

        self.stats = PipelineStats()

    def set_vector_index(self, index):
        self.vector_index = index

    def set_cache(self, cache: CacheFacade):
        self.cache = cache

    def retrieve(
        self,
        query: str,
        filters: Dict = None,
        top_k: int = None,
        return_context: bool = True
    ) -> RetrievalResult:
        start_time = time.time()

        top_k = top_k or self.config.top_k_final

        if self.cache:
            cached = self.cache.get(query, top_k, filters)
            if cached:
                self.stats.cache_hits += 1
                return RetrievalResult(
                    chunks=cached,
                    query=query,
                    total_time_ms=(time.time() - start_time) * 1000,
                    metadata={"cache_hit": True}
                )

        preproc_start = time.time()
        processed = self.preprocessor.preprocess(query)
        self.stats.query_classification_ms = (time.time() - preproc_start) * 1000

        embed_start = time.time()
        use_query = processed.get('expanded', query)
        query_embedding = self.embedding_engine.encode(use_query)
        self.stats.embedding_ms = (time.time() - embed_start) * 1000

        search_start = time.time()
        if self.vector_index:
            initial_results = self.vector_index.search(
                query_embedding,
                k=self.config.top_k_initial
            )
        else:
            initial_results = self._fallback_search(query, processed)
        self.stats.vector_search_ms = (time.time() - search_start) * 1000

        self.stats.chunks_before_filter = len(initial_results)

        if filters or processed.get('filters'):
            combined_filters = {**(filters or {}), **(processed.get('filters', {}))}
            initial_results = self._apply_filters(initial_results, combined_filters)

        rerank_start = time.time()
        if self.reranker and initial_results:
            initial_results = self.reranker.rerank(
                query,
                initial_results,
                top_k=self.config.top_k_initial
            )
        self.stats.rerank_ms = (time.time() - rerank_start) * 1000

        dedup_start = time.time()
        if self.deduplicator:
            initial_results = self.deduplicator.deduplicate(
                initial_results,
                top_k=self.config.top_k_initial
            )
        self.stats.deduplication_ms = (time.time() - dedup_start) * 1000

        self.stats.chunks_after_filter = len(initial_results)

        if self.config.use_diversity:
            final_results = self.diversity_sampler.sample(
                initial_results,
                top_k=top_k
            )
        else:
            final_results = initial_results[:top_k]

        context_window = None
        if return_context:
            compress_start = time.time()
            context_window = self.context_manager.compress(query, final_results)
            self.stats.context_compression_ms = (time.time() - compress_start) * 1000

        if self.cache and final_results:
            self.cache.put(query, final_results, top_k, filters)

        self.stats.total_ms = (time.time() - start_time) * 1000

        return RetrievalResult(
            chunks=final_results,
            intent=processed.get('intent'),
            context_window=context_window,
            query=query,
            total_time_ms=self.stats.total_ms,
            metadata={
                "cache_hit": False,
                "strategy": self.config.strategy.value,
                "language": processed.get('language'),
                "stats": {
                    "chunks_before_filter": self.stats.chunks_before_filter,
                    "chunks_after_filter": self.stats.chunks_after_filter,
                    "embedding_ms": self.stats.embedding_ms,
                    "search_ms": self.stats.vector_search_ms,
                    "rerank_ms": self.stats.rerank_ms
                }
            }
        )

    def _fallback_search(self, query: str, processed: Dict) -> List[Dict]:
        if not self.storage:
            return []

        keywords = processed.get('keywords', [])
        if not keywords:
            keywords = query.lower().split()

        all_chunks = list(self.storage.sqlite.iter_chunks())

        scored_chunks = []
        for chunk in all_chunks:
            content = (chunk.get('content', '') or chunk.get('metadata', {}).get('content', '')).lower()

            score = sum(1 for kw in keywords if kw in content)

            for entity in processed.get('entities', []):
                if entity.lower() in content:
                    score += 2

            if score > 0:
                chunk['score'] = score / max(len(keywords), 1)
                scored_chunks.append(chunk)

        scored_chunks.sort(key=lambda x: x.get('score', 0), reverse=True)

        return scored_chunks

    def _apply_filters(self, chunks: List[Dict], filters: Dict) -> List[Dict]:
        if not filters:
            return chunks

        filtered = []
        for chunk in chunks:
            meta = chunk.get('metadata', {})

            match = True
            for key, value in filters.items():
                if key not in meta:
                    if key == 'file_path' and 'file_path' not in chunk:
                        chunk_file = chunk.get('file_path', '')
                        if isinstance(value, list):
                            if not any(value_item in chunk_file for value_item in value):
                                match = False
                        elif value not in chunk_file:
                            match = False
                    else:
                        match = False

                if not match:
                    break

                chunk_value = meta.get(key)
                if isinstance(value, list):
                    if chunk_value not in value:
                        match = False
                elif chunk_value != value:
                    match = False

            if match:
                filtered.append(chunk)

        return filtered

    def get_stats(self) -> Dict:
        return {
            "query_classification_ms": self.stats.query_classification_ms,
            "embedding_ms": self.stats.embedding_ms,
            "vector_search_ms": self.stats.vector_search_ms,
            "rerank_ms": self.stats.rerank_ms,
            "deduplication_ms": self.stats.deduplication_ms,
            "context_compression_ms": self.stats.context_compression_ms,
            "total_ms": self.stats.total_ms,
            "cache_hits": self.stats.cache_hits,
            "chunks_before_filter": self.stats.chunks_before_filter,
            "chunks_after_filter": self.stats.chunks_after_filter
        }


class MultiHopRetriever:
    def __init__(self, pipeline: RetrievalPipeline, max_hops: int = 2):
        self.pipeline = pipeline
        self.max_hops = max_hops

    def retrieve(
        self,
        question: str,
        top_k: int = 10
    ) -> RetrievalResult:
        first_hop = self.pipeline.retrieve(question, top_k=top_k)

        if not self._requires_multi_hop(question, first_hop):
            return first_hop

        expanded_entities = self._extract_entities(first_hop.chunks)

        expanded_query = self._build_expanded_query(question, expanded_entities)

        second_hop = self.pipeline.retrieve(
            expanded_query,
            top_k=top_k,
            return_context=False
        )

        combined_chunks = self._merge_results(
            first_hop.chunks,
            second_hop.chunks,
            top_k
        )

        context_window = self.pipeline.context_manager.compress(
            question,
            combined_chunks
        )

        return RetrievalResult(
            chunks=combined_chunks,
            intent=first_hop.intent,
            context_window=context_window,
            query=question,
            total_time_ms=first_hop.total_time_ms + second_hop.total_time_ms,
            metadata={
                "multi_hop": True,
                "hops": 2,
                "expanded_query": expanded_query
            }
        )

    def _requires_multi_hop(self, question: str, result: RetrievalResult) -> bool:
        question_lower = question.lower()

        multi_hop_patterns = [
            r'how.*use.*',
            r'.*call.*',
            r'.*depend.*',
            r'.*import.*',
            r'why.*',
            r'.*related.*',
        ]

        for pattern in multi_hop_patterns:
            if re.search(pattern, question_lower):
                return True

        if len(result.chunks) < 3:
            return True

        return False

    def _extract_entities(self, chunks: List[Dict]) -> List[str]:
        entities = set()

        for chunk in chunks:
            content = chunk.get('content', '') or chunk.get('metadata', {}).get('content', '')

            function_names = re.findall(r'(?:def|function|fn)\s+(\w+)', content)
            entities.update(function_names)

            class_names = re.findall(r'class\s+(\w+)', content)
            entities.update(class_names)

            imports = re.findall(r'(?:import|from)\s+([\w.]+)', content)
            entities.update(imports)

        return list(entities)[:20]

    def _build_expanded_query(self, question: str, entities: List[str]) -> str:
        return question + " " + " ".join(entities[:5])

    def _merge_results(
        self,
        hop1_chunks: List[Dict],
        hop2_chunks: List[Dict],
        top_k: int
    ) -> List[Dict]:
        seen_ids = set()
        merged = []

        for chunk in hop1_chunks:
            chunk_id = chunk.get('chunk_id', '')
            if chunk_id and chunk_id not in seen_ids:
                chunk['hop'] = 1
                merged.append(chunk)
                seen_ids.add(chunk_id)

        for chunk in hop2_chunks:
            chunk_id = chunk.get('chunk_id', '')
            if chunk_id and chunk_id not in seen_ids:
                chunk['hop'] = 2
                merged.append(chunk)
                seen_ids.add(chunk_id)

        merged.sort(key=lambda x: x.get('score', 0), reverse=True)

        return merged[:top_k]


class StreamingPipeline:
    def __init__(self, pipeline: RetrievalPipeline, batch_size: int = 10):
        self.pipeline = pipeline
        self.batch_size = batch_size

    def retrieve_streaming(
        self,
        query: str,
        filters: Dict = None,
        top_k: int = 10,
        callback: Callable[[Dict], None] = None
    ) -> RetrievalResult:
        result = self.pipeline.retrieve(query, filters, top_k, return_context=False)

        if callback:
            for i, chunk in enumerate(result.chunks):
                chunk['result_index'] = i
                callback(chunk)

        context_window = self.pipeline.context_manager.compress(
            query,
            result.chunks
        )

        result.context_window = context_window

        return result


class AdaptivePipeline:
    def __init__(self):
        self.pipeline_cache: Dict[str, RetrievalPipeline] = {}
        self.default_pipeline = RetrievalPipeline()

    def get_pipeline(self, strategy: RetrievalStrategy) -> RetrievalPipeline:
        if strategy.value not in self.pipeline_cache:
            config = RetrievalConfig(strategy=strategy)
            self.pipeline_cache[strategy.value] = RetrievalPipeline(config)

        return self.pipeline_cache[strategy.value]

    def retrieve(
        self,
        query: str,
        filters: Dict = None,
        top_k: int = 10,
        strategy: RetrievalStrategy = None
    ) -> RetrievalResult:
        if strategy:
            pipeline = self.get_pipeline(strategy)
            return pipeline.retrieve(query, filters, top_k)

        processed = self.default_pipeline.preprocessor.preprocess(query)
        intent = processed.get('intent')

        if intent == QueryIntent.EXACT_LINE:
            strategy = RetrievalStrategy.EXACT
        elif intent == QueryIntent.SYMBOL_SEARCH:
            strategy = RetrievalStrategy.KEYWORD
        elif intent == QueryIntent.SEMANTIC:
            strategy = RetrievalStrategy.SEMANTIC
        elif intent == QueryIntent.MULTI_HOP:
            strategy = RetrievalStrategy.MULTI_HOP
        else:
            strategy = RetrievalStrategy.HYBRID

        pipeline = self.get_pipeline(strategy)

        return pipeline.retrieve(query, filters, top_k)
