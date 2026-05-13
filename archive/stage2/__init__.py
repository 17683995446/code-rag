from stage2.retrieval import MultiRetrieval, Reranker, ContextAugmenter
from stage2.searchers import QueryParser, ExactLineSearcher, KeywordSearcher, SymbolSearcher
from stage2.types import (
    SearchResult, SearchOptions, RetrievalType,
    QueryIntent, RetrievalStats
)

__all__ = [
    'MultiRetrieval',
    'Reranker',
    'ContextAugmenter',
    'QueryParser',
    'ExactLineSearcher',
    'KeywordSearcher',
    'SymbolSearcher',
    'SearchResult',
    'SearchOptions',
    'RetrievalType',
    'QueryIntent',
    'RetrievalStats',
]


def create_retriever(indexer=None, metadata: list = None) -> MultiRetrieval:
    from stage1.indexer import HybridSearchEngine

    if metadata is None:
        if indexer is not None and hasattr(indexer, 'metadata'):
            metadata = indexer.metadata
        else:
            raise ValueError("Must provide metadata or indexer with metadata")

    vector_index = None
    bm25_index = None

    if indexer is not None:
        if hasattr(indexer, 'vector_index'):
            vector_index = indexer.vector_index
        if hasattr(indexer, 'bm25_index'):
            bm25_index = indexer.bm25_index

    if vector_index is None:
        vector_index = MetadataVectorIndex(metadata)

    if bm25_index is None:
        bm25_index = MetadataBM25Index(metadata)

    hybrid_engine = HybridSearchEngine(
        vector_index=vector_index,
        bm25_index=bm25_index,
        metadata=metadata
    )

    keyword_searcher = KeywordSearcher(metadata)
    symbol_searcher = SymbolSearcher(metadata)
    exact_searcher = ExactLineSearcher(metadata)

    return MultiRetrieval(
        hybrid_engine=hybrid_engine,
        keyword_searcher=keyword_searcher,
        symbol_searcher=symbol_searcher,
        exact_searcher=exact_searcher
    )


class MetadataVectorIndex:
    def __init__(self, metadata: list):
        self.metadata = metadata

    def search(self, query_vec, top_k: int = 10):
        return [], []


class MetadataBM25Index:
    def __init__(self, metadata: list):
        self.metadata = metadata

    def search(self, query: str, top_k: int = 10):
        return [], []


def quick_search(
    query: str,
    indexer=None,
    metadata: list = None,
    top_k: int = 5,
    rerank: bool = True
) -> list:
    if indexer is None and metadata is None:
        raise ValueError("Must provide either indexer or metadata")

    if metadata is None:
        metadata = indexer.metadata

    retriever = create_retriever(indexer, metadata)

    options = SearchOptions(
        top_k=top_k,
        rerank=rerank,
        retrieval_types=[RetrievalType.SEMANTIC, RetrievalType.KEYWORD]
    )

    results = retriever.retrieve(query, options)

    if rerank:
        reranker = Reranker()
        results = reranker.rerank(results, query, top_k)

    return [r.to_dict() for r in results]
