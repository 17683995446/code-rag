from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Any, Tuple
from enum import Enum


class RetrievalType(Enum):
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    EXACT = "exact"
    STRUCTURAL = "structural"
    CALL_GRAPH = "call_graph"


@dataclass
class QueryIntent:
    query: str
    intent_type: str = "general"
    target_language: Optional[str] = None
    target_file: Optional[str] = None
    target_symbol: Optional[str] = None
    line_number: Optional[int] = None
    keywords: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)


@dataclass
class SearchOptions:
    top_k: int = 10
    retrieval_types: List[RetrievalType] = field(default_factory=lambda: [RetrievalType.SEMANTIC, RetrievalType.KEYWORD])
    languages: Optional[List[str]] = None
    file_patterns: Optional[List[str]] = None
    min_score: float = 0.0
    include_context: bool = True
    context_lines: int = 5
    rerank: bool = True
    hybrid_alpha: float = 0.7


@dataclass
class SearchResult:
    chunk_id: str
    content: str
    file_path: str
    language: str
    start_line: int
    end_line: int
    chunk_type: str
    score: float
    retrieval_type: str
    symbols: List[Dict] = field(default_factory=list)
    context_before: str = ""
    context_after: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'chunk_id': self.chunk_id,
            'content': self.content,
            'file_path': self.file_path,
            'language': self.language,
            'start_line': self.start_line,
            'end_line': self.end_line,
            'chunk_type': self.chunk_type,
            'score': self.score,
            'retrieval_type': self.retrieval_type,
            'symbols': self.symbols,
            'context_before': self.context_before,
            'context_after': self.context_after,
            'metadata': self.metadata
        }


@dataclass
class CallGraphNode:
    symbol_name: str
    file_path: str
    line_number: int
    calls: List[str] = field(default_factory=list)
    called_by: List[str] = field(default_factory=list)


@dataclass
class RetrievalStats:
    total_results: int = 0
    retrieval_times_ms: Dict[str, float] = field(default_factory=dict)
    cache_hits: int = 0
    rerank_time_ms: float = 0
