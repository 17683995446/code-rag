import os
import re
import json
import hashlib
from typing import List, Dict, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict
import threading


@dataclass
class CompressionResult:
    content: str
    original_length: int
    compressed_length: int
    compression_ratio: float
    tokens_estimate: int
    metadata: Dict = field(default_factory=dict)


@dataclass
class ContextWindow:
    chunks: List[Dict]
    total_tokens: int
    total_length: int
    sources: List[str] = field(default_factory=list)


class TokenEstimator:
    def __init__(self, model: str = "gpt-3.5"):
        self.model = model
        self.ratio = self._get_ratio(model)

    def _get_ratio(self, model: str) -> float:
        ratios = {
            "gpt-3.5": 4.0,
            "gpt-4": 3.5,
            "claude": 3.0,
            "default": 4.0
        }
        return ratios.get(model, 4.0)

    def estimate(self, text: str) -> int:
        if not text:
            return 0

        chars = len(text)
        tokens = int(chars / self.ratio)

        tokens += text.count('\n') * 0.5

        code_indicators = ['def ', 'class ', 'function ', 'const ', 'let ', 'var ', 'import ', 'export ']
        for indicator in code_indicators:
            tokens += text.count(indicator) * 2

        return max(tokens, 1)

    def estimate_chunks(self, chunks: List[Dict]) -> int:
        total = 0
        for chunk in chunks:
            content = chunk.get('content', '') or chunk.get('metadata', {}).get('content', '')
            total += self.estimate(content)
        return total


class QueryRelevanceFilter:
    def __init__(self, embedding_engine=None):
        self.embedding_engine = embedding_engine

    def score_relevance(self, query: str, chunk: Dict) -> float:
        content = chunk.get('content', '') or chunk.get('metadata', {}).get('content', '')

        query_terms = set(query.lower().split())
        content_terms = set(content.lower().split())

        overlap = query_terms & content_terms
        if not query_terms:
            return 0.0

        term_score = len(overlap) / len(query_terms)

        query_keywords = [t for t in query_terms if len(t) > 3]
        keyword_score = 0.0
        if query_keywords:
            keyword_matches = sum(1 for t in query_keywords if t in content_terms)
            keyword_score = keyword_matches / len(query_keywords)

        position_score = self._calculate_position_score(query, content)

        combined_score = (
            term_score * 0.4 +
            keyword_score * 0.4 +
            position_score * 0.2
        )

        return combined_score

    def _calculate_position_score(self, query: str, content: str) -> float:
        query_lower = query.lower()
        content_lower = content.lower()

        first_pos = content_lower.find(query_lower)
        if first_pos >= 0:
            position_ratio = first_pos / max(len(content), 1)
            return max(0.0, 1.0 - position_ratio)

        words = query_lower.split()
        if words:
            first_word_pos = content_lower.find(words[0])
            if first_word_pos >= 0:
                position_ratio = first_word_pos / max(len(content), 1)
                return max(0.0, 0.8 - position_ratio * 0.5)

        return 0.1

    def filter_and_rank(
        self,
        query: str,
        chunks: List[Dict],
        min_relevance: float = 0.1
    ) -> List[Dict]:
        scored = []
        for chunk in chunks:
            score = self.score_relevance(query, chunk)
            scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)

        filtered = [chunk for score, chunk in scored if score >= min_relevance]

        return filtered


class ContextCompressor:
    def __init__(
        self,
        max_tokens: int = 4000,
        model: str = "gpt-3.5",
        preserve_structure: bool = True
    ):
        self.max_tokens = max_tokens
        self.token_estimator = TokenEstimator(model)
        self.preserve_structure = preserve_structure

    def compress(
        self,
        query: str,
        chunks: List[Dict],
        strategy: str = "auto"
    ) -> ContextWindow:
        if not chunks:
            return ContextWindow(chunks=[], total_tokens=0, total_length=0)

        if strategy == "auto":
            strategy = self._select_strategy(query, chunks)

        if strategy == "relevance":
            compressed_chunks = self._compress_by_relevance(query, chunks)
        elif strategy == "summary":
            compressed_chunks = self._compress_by_summary(query, chunks)
        elif strategy == "hierarchical":
            compressed_chunks = self._compress_hierarchical(query, chunks)
        else:
            compressed_chunks = self._compress_truncation(chunks)

        sources = []
        for chunk in compressed_chunks:
            source = chunk.get('metadata', {}).get('file_path', 'unknown')
            if source not in sources:
                sources.append(source)

        total_tokens = self.token_estimator.estimate_chunks(compressed_chunks)
        total_length = sum(
            len(chunk.get('content', '') or chunk.get('metadata', {}).get('content', ''))
            for chunk in compressed_chunks
        )

        return ContextWindow(
            chunks=compressed_chunks,
            total_tokens=total_tokens,
            total_length=total_length,
            sources=sources
        )

    def _select_strategy(self, query: str, chunks: List[Dict]) -> str:
        query_lower = query.lower()

        if any(k in query_lower for k in ['explain', 'what is', 'how does', 'describe']):
            return "summary"

        if any(k in query_lower for k in ['find', 'where', 'all', 'every']):
            return "hierarchical"

        return "relevance"

    def _compress_by_relevance(
        self,
        query: str,
        chunks: List[Dict]
    ) -> List[Dict]:
        filter_ = QueryRelevanceFilter()
        ranked = filter_.filter_and_rank(query, chunks, min_relevance=0.1)

        compressed = []
        current_tokens = 0

        for chunk in ranked:
            content = chunk.get('content', '') or chunk.get('metadata', {}).get('content', '')
            chunk_tokens = self.token_estimator.estimate(content)

            if current_tokens + chunk_tokens <= self.max_tokens:
                compressed.append(chunk)
                current_tokens += chunk_tokens
            else:
                remaining = self.max_tokens - current_tokens
                if remaining > 100:
                    compressed.append(self._truncate_chunk(chunk, remaining))
                break

        return compressed

    def _compress_by_summary(
        self,
        query: str,
        chunks: List[Dict]
    ) -> List[Dict]:
        compressed = []
        current_tokens = 0

        summary_budget = self.max_tokens * 0.2
        chunks_budget = self.max_tokens * 0.8

        for chunk in chunks:
            content = chunk.get('content', '') or chunk.get('metadata', {}).get('content', '')
            chunk_tokens = self.token_estimator.estimate(content)

            if chunk_tokens <= chunks_budget / max(len(chunks), 1):
                compressed.append(chunk)
                current_tokens += chunk_tokens
            elif current_tokens < chunks_budget:
                ratio = (chunks_budget - current_tokens) / chunk_tokens
                if ratio > 0.3:
                    compressed.append(self._truncate_chunk(chunk, int(chunks_budget - current_tokens)))
                    current_tokens = chunks_budget
                break

        return compressed

    def _compress_hierarchical(
        self,
        query: str,
        chunks: List[Dict]
    ) -> List[Dict]:
        by_file = defaultdict(list)
        for chunk in chunks:
            file_path = chunk.get('metadata', {}).get('file_path', 'unknown')
            by_file[file_path].append(chunk)

        compressed = []
        current_tokens = 0
        tokens_per_file = self.max_tokens / max(len(by_file), 1)

        for file_path, file_chunks in by_file.items():
            file_content = '\n'.join(
                c.get('content', '') or c.get('metadata', {}).get('content', '')
                for c in file_chunks
            )
            file_tokens = self.token_estimator.estimate(file_content)

            if file_tokens <= tokens_per_file:
                compressed.extend(file_chunks)
                current_tokens += file_tokens
            else:
                ratio = tokens_per_file / file_tokens
                keep_count = max(1, int(len(file_chunks) * ratio))
                compressed.extend(file_chunks[:keep_count])
                current_tokens += tokens_per_file

            if current_tokens >= self.max_tokens:
                break

        return compressed

    def _compress_truncation(self, chunks: List[Dict]) -> List[Dict]:
        compressed = []
        current_tokens = 0

        for chunk in chunks:
            content = chunk.get('content', '') or chunk.get('metadata', {}).get('content', '')
            chunk_tokens = self.token_estimator.estimate(content)

            if current_tokens + chunk_tokens <= self.max_tokens:
                compressed.append(chunk)
                current_tokens += chunk_tokens
            else:
                remaining = self.max_tokens - current_tokens
                if remaining > 50:
                    compressed.append(self._truncate_chunk(chunk, remaining))
                break

        return compressed

    def _truncate_chunk(self, chunk: Dict, max_tokens: int) -> Dict:
        content = chunk.get('content', '') or chunk.get('metadata', {}).get('content', '')

        lines = content.split('\n')
        truncated_lines = []
        current_tokens = 0

        for line in lines:
            line_tokens = self.token_estimator.estimate(line)
            if current_tokens + line_tokens <= max_tokens:
                truncated_lines.append(line)
                current_tokens += line_tokens
            else:
                remaining = max_tokens - current_tokens
                if remaining > 20:
                    char_limit = int(remaining * self.token_estimator.ratio)
                    truncated_lines.append(line[:char_limit] + ' ... [truncated]')
                break

        truncated_content = '\n'.join(truncated_lines)

        new_chunk = chunk.copy()
        new_chunk['content'] = truncated_content
        if 'metadata' in new_chunk:
            new_chunk['metadata'] = new_chunk['metadata'].copy()
            new_chunk['metadata']['content'] = truncated_content
            new_chunk['metadata']['truncated'] = True

        return new_chunk


class DynamicContextManager:
    def __init__(
        self,
        max_tokens: int = 4000,
        overlap_tokens: int = 200,
        model: str = "gpt-3.5"
    ):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.token_estimator = TokenEstimator(model)
        self.compressor = ContextCompressor(max_tokens, model)

    def build_context(
        self,
        query: str,
        chunks: List[Dict],
        include_metadata: bool = True
    ) -> str:
        context_window = self.compressor.compress(query, chunks)

        parts = []
        for i, chunk in enumerate(context_window.chunks):
            content = chunk.get('content', '') or chunk.get('metadata', {}).get('content', '')

            if include_metadata:
                metadata = chunk.get('metadata', {})
                file_path = metadata.get('file_path', 'unknown')
                chunk_id = metadata.get('chunk_id', f'chunk_{i}')

                header = f"--- {file_path} ({chunk_id}) ---"
                parts.append(f"{header}\n{content}\n")
            else:
                parts.append(content)

        return '\n'.join(parts)

    def estimate_context_cost(self, chunks: List[Dict]) -> Dict:
        total_tokens = self.token_estimator.estimate_chunks(chunks)
        within_limit = total_tokens <= self.max_tokens
        overflow = max(0, total_tokens - self.max_tokens)

        return {
            'total_tokens': total_tokens,
            'max_tokens': self.max_tokens,
            'within_limit': within_limit,
            'overflow_tokens': overflow,
            'chunk_count': len(chunks)
        }


class SummaryGenerator:
    def __init__(self):
        self.cache = {}
        self._lock = threading.Lock()

    def generate_summary(
        self,
        content: str,
        max_length: int = 500,
        use_cache: bool = True
    ) -> str:
        cache_key = hashlib.md5(content.encode()).hexdigest()

        if use_cache:
            with self._lock:
                if cache_key in self.cache:
                    return self.cache[cache_key]

        summary = self._extract_key_sentences(content, max_length)

        if use_cache:
            with self._lock:
                self.cache[cache_key] = summary

        return summary

    def _extract_key_sentences(self, content: str, max_length: int) -> str:
        lines = content.split('\n')
        important_lines = []

        keywords = ['def ', 'class ', 'function ', 'return', 'import ', 'export ',
                    'const ', 'let ', 'async ', 'await ', 'try:', 'except:', 'if ', 'for ']

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if any(line.startswith(kw) for kw in keywords):
                important_lines.append(line)
            elif len(line) > 20 and any(c.isupper() for c in line[:10]):
                important_lines.append(line)

        summary_lines = []
        current_length = 0

        for line in important_lines:
            line_length = len(line)
            if current_length + line_length <= max_length:
                summary_lines.append(line)
                current_length += line_length
            elif summary_lines:
                break

        if not summary_lines and lines:
            summary_lines = lines[:10]

        return '\n'.join(summary_lines[:20])

    def clear_cache(self):
        with self._lock:
            self.cache.clear()


class RelevanceFeedback:
    def __init__(self):
        self.positive_examples: List[str] = []
        self.negative_examples: List[str] = []
        self._lock = threading.Lock()

    def add_positive(self, chunk: Dict):
        content = chunk.get('content', '') or chunk.get('metadata', {}).get('content', '')
        with self._lock:
            if content not in self.positive_examples:
                self.positive_examples.append(content)

    def add_negative(self, chunk: Dict):
        content = chunk.get('content', '') or chunk.get('metadata', {}).get('content', '')
        with self._lock:
            if content not in self.negative_examples:
                self.negative_examples.append(content)

    def get_expanded_query_terms(self) -> List[str]:
        with self._lock:
            positive_terms = set()
            for content in self.positive_examples:
                words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', content.lower())
                positive_terms.update(w for w in words if len(w) > 3)

            negative_terms = set()
            for content in self.negative_examples:
                words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', content.lower())
                negative_terms.update(w for w in words if len(w) > 3)

            expanded = list(positive_terms - negative_terms)
            return expanded[:20]

    def clear(self):
        with self._lock:
            self.positive_examples.clear()
            self.negative_examples.clear()
