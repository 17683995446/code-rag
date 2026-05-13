from stage1.storage import IndexBuilder, StorageManager, create_builder
from stage1.parser import CodeParser, DirectoryParser, ChunkBuilder
from stage1.indexer import (
    CodeIndexer, SimpleEmbeddingEngine, VectorIndex,
    BM25Index, HybridSearchEngine, Tokenizer
)
from stage1.types import (
    CodeChunk, FileInfo, CodeSymbol, ChunkStrategy,
    BuildStats, IndexConfig
)

__all__ = [
    'IndexBuilder',
    'StorageManager',
    'create_builder',
    'CodeParser',
    'DirectoryParser',
    'ChunkBuilder',
    'CodeIndexer',
    'SimpleEmbeddingEngine',
    'VectorIndex',
    'BM25Index',
    'HybridSearchEngine',
    'Tokenizer',
    'CodeChunk',
    'FileInfo',
    'CodeSymbol',
    'ChunkStrategy',
    'BuildStats',
    'IndexConfig',
]


def quick_build(source_path: str, storage_path: str = "./data", **kwargs):
    builder = create_builder(source_path, storage_path, **kwargs)
    return builder.build(source_path)


def quick_search(query: str, storage_path: str = "./data", top_k: int = 5):
    builder = IndexBuilder(storage_path=storage_path)
    indexer = builder.load(show_progress=False)

    search_engine = HybridSearchEngine(
        vector_index=indexer.vector_index,
        bm25_index=indexer.bm25_index,
        metadata=indexer.metadata,
        top_k=top_k
    )

    return search_engine.search(query)
