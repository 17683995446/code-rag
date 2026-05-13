import time
import numpy as np
from typing import List, Dict, Optional, Tuple, Callable
from dataclasses import dataclass

from stage2.types import SearchResult, SearchOptions, RetrievalType, RetrievalStats
from stage1.indexer import HybridSearchEngine


class MultiRetrieval:
    def __init__(
        self,
        hybrid_engine: HybridSearchEngine,
        keyword_searcher=None,
        symbol_searcher=None,
        exact_searcher=None
    ):
        self.hybrid_engine = hybrid_engine
        self.keyword_searcher = keyword_searcher
        self.symbol_searcher = symbol_searcher
        self.exact_searcher = exact_searcher
        self.stats = RetrievalStats()

    def retrieve(
        self,
        query: str,
        options: SearchOptions
    ) -> List[SearchResult]:
        results_by_type = {}
        retrieval_times = {}

        for retrieval_type in options.retrieval_types:
            start_time = time.time()
            try:
                if retrieval_type == RetrievalType.SEMANTIC:
                    results = self._semantic_search(query, options)
                elif retrieval_type == RetrievalType.KEYWORD:
                    results = self._keyword_search(query, options)
                elif retrieval_type == RetrievalType.EXACT:
                    results = self._exact_search(query, options)
                elif retrieval_type == RetrievalType.STRUCTURAL:
                    results = self._structural_search(query, options)
                elif retrieval_type == RetrievalType.CALL_GRAPH:
                    results = self._call_graph_search(query, options)
                else:
                    results = []

                elapsed = (time.time() - start_time) * 1000
                retrieval_times[retrieval_type.value] = elapsed
                results_by_type[retrieval_type.value] = results
            except Exception as e:
                results_by_type[retrieval_type.value] = []

        all_results = self._merge_results(results_by_type, options)

        if options.min_score > 0:
            all_results = [r for r in all_results if r.score >= options.min_score]

        self.stats = RetrievalStats(
            total_results=len(all_results),
            retrieval_times_ms=retrieval_times
        )

        return all_results

    def _semantic_search(
        self,
        query: str,
        options: SearchOptions
    ) -> List[SearchResult]:
        raw_results = self.hybrid_engine.search(query, top_k=options.top_k * 2)

        results = []
        for r in raw_results:
            result = SearchResult(
                chunk_id=r.get('chunk_id', ''),
                content=r.get('content', ''),
                file_path=r.get('file_path', ''),
                language=r.get('language', 'unknown'),
                start_line=r.get('start_line', 0),
                end_line=r.get('end_line', 0),
                chunk_type=r.get('chunk_type', 'unknown'),
                score=float(r.get('score', 0)),
                retrieval_type='semantic',
                symbols=r.get('symbols', [])
            )
            results.append(result)

        return results

    def _keyword_search(
        self,
        query: str,
        options: SearchOptions
    ) -> List[SearchResult]:
        if not self.keyword_searcher:
            return self._semantic_search(query, options)

        from stage2.searchers import QueryParser
        parser = QueryParser()
        intent = parser.parse(query)
        keywords = intent.keywords

        if not keywords:
            return []

        raw_results = self.keyword_searcher.search(keywords, top_k=options.top_k * 2)

        results = []
        for r, score in raw_results:
            result = SearchResult(
                chunk_id=r.get('chunk_id', ''),
                content=r.get('content', ''),
                file_path=r.get('file_path', ''),
                language=r.get('language', 'unknown'),
                start_line=r.get('start_line', 0),
                end_line=r.get('end_line', 0),
                chunk_type=r.get('chunk_type', 'unknown'),
                score=float(score),
                retrieval_type='keyword',
                symbols=r.get('symbols', [])
            )
            results.append(result)

        return results

    def _exact_search(
        self,
        query: str,
        options: SearchOptions
    ) -> List[SearchResult]:
        if not self.exact_searcher:
            return []

        from stage2.searchers import QueryParser
        parser = QueryParser()
        intent = parser.parse(query)

        if not intent.target_file:
            return []

        raw_results = self.exact_searcher.search_by_file_line(
            intent.target_file,
            intent.line_number,
            top_k=options.top_k
        )

        results = []
        for r in raw_results:
            result = SearchResult(
                chunk_id=r.get('chunk_id', ''),
                content=r.get('content', ''),
                file_path=r.get('file_path', ''),
                language=r.get('language', 'unknown'),
                start_line=r.get('start_line', 0),
                end_line=r.get('end_line', 0),
                chunk_type=r.get('chunk_type', 'unknown'),
                score=1.0,
                retrieval_type='exact',
                symbols=r.get('symbols', [])
            )
            results.append(result)

        return results

    def _structural_search(
        self,
        query: str,
        options: SearchOptions
    ) -> List[SearchResult]:
        if not self.symbol_searcher:
            return []

        from stage2.searchers import QueryParser
        parser = QueryParser()
        intent = parser.parse(query)

        if intent.target_symbol:
            raw_results = self.symbol_searcher.search_by_name(
                intent.target_symbol,
                top_k=options.top_k * 2
            )
        else:
            return []

        results = []
        for r in raw_results:
            result = SearchResult(
                chunk_id=r.get('chunk_id', ''),
                content=r.get('content', ''),
                file_path=r.get('file_path', ''),
                language=r.get('language', 'unknown'),
                start_line=r.get('start_line', 0),
                end_line=r.get('end_line', 0),
                chunk_type=r.get('chunk_type', 'unknown'),
                score=0.8,
                retrieval_type='structural',
                symbols=r.get('symbols', [])
            )
            results.append(result)

        return results

    def _call_graph_search(
        self,
        query: str,
        options: SearchOptions
    ) -> List[SearchResult]:
        return self._structural_search(query, options)

    def _merge_results(
        self,
        results_by_type: Dict[str, List[SearchResult]],
        options: SearchOptions
    ) -> List[SearchResult]:
        combined: Dict[str, SearchResult] = {}

        type_weights = {
            'semantic': 0.5,
            'keyword': 0.3,
            'exact': 1.0,
            'structural': 0.6,
            'call_graph': 0.4
        }

        for retrieval_type, results in results_by_type.items():
            weight = type_weights.get(retrieval_type, 0.5)

            for result in results:
                key = result.chunk_id
                if key not in combined:
                    combined[key] = result
                else:
                    combined[key].score = max(
                        combined[key].score,
                        result.score * weight
                    )
                    if result.retrieval_type == 'exact':
                        combined[key].retrieval_type = 'exact'

        sorted_results = sorted(
            combined.values(),
            key=lambda x: x.score,
            reverse=True
        )

        return sorted_results[:options.top_k]


class Reranker:
    def __init__(self):
        self.features = ['keyword_match', 'symbol_match', 'length_penalty', 'recency']

    def rerank(
        self,
        results: List[SearchResult],
        query: str,
        top_k: int = 5
    ) -> List[SearchResult]:
        from stage2.searchers import QueryParser

        parser = QueryParser()
        intent = parser.parse(query)
        query_keywords = set(intent.keywords)
        query_entities = set(intent.entities)

        scored_results = []
        for result in results:
            score = self._compute_features(result, query, query_keywords, query_entities)
            scored_results.append((result, score))

        scored_results.sort(key=lambda x: x[1], reverse=True)

        return [r for r, _ in scored_results[:top_k]]

    def _compute_features(
        self,
        result: SearchResult,
        query: str,
        query_keywords: set,
        query_entities: set
    ) -> float:
        score = result.score

        content_lower = result.content.lower()
        query_lower = query.lower()

        keyword_score = sum(
            1 for kw in query_keywords
            if kw.lower() in content_lower
        ) / max(len(query_keywords), 1) * 0.3

        symbol_score = 0
        for sym in result.symbols:
            sym_name = sym.get('name', '').lower()
            if sym_name in query_lower:
                symbol_score += 0.5
            for entity in query_entities:
                if entity.lower() in sym_name:
                    symbol_score += 0.3

        length_score = 0
        content_len = len(result.content.split('\n'))
        if 10 <= content_len <= 100:
            length_score = 0.1
        elif content_len > 100:
            length_score = -0.05

        final_score = (
            score * 0.5 +
            keyword_score +
            symbol_score +
            length_score
        )

        return final_score


class ContextAugmenter:
    def __init__(self, chunks_storage: List[Dict] = None):
        self.chunks_storage = chunks_storage or []

    def add_context(
        self,
        result: SearchResult,
        context_lines: int = 5
    ) -> SearchResult:
        try:
            path = result.file_path
            lines = self._read_file_lines(path)

            if lines:
                start = max(0, result.start_line - context_lines - 1)
                result.context_before = '\n'.join(lines[start:result.start_line-1])

                end = min(len(lines), result.end_line + context_lines)
                result.context_after = '\n'.join(lines[result.end_line:end])

        except Exception:
            pass

        return result

    def _read_file_lines(self, path: str) -> List[str]:
        try:
            return Path(path).read_text(encoding='utf-8', errors='ignore').split('\n')
        except Exception:
            return []


from pathlib import Path
