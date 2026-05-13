import json
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import asdict

from stage1.types import BuildStats, CodeChunk


class StorageManager:
    def __init__(self, storage_path: str = "./data"):
        self.storage_path = Path(storage_path)
        self.index_file = self.storage_path / "index.npy"
        self.metadata_file = self.storage_path / "metadata.json"
        self.bm25_file = self.storage_path / "bm25.json"
        self.stats_file = self.storage_path / "stats.json"
        self.chunks_file = self.storage_path / "chunks.json"

    def ensure_storage(self):
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def save_chunks(self, chunks: List[Any]):
        chunks_data = []
        for chunk in chunks:
            if hasattr(chunk, 'to_dict'):
                chunks_data.append(chunk.to_dict())
            elif isinstance(chunk, dict):
                chunks_data.append(chunk)
            else:
                chunks_data.append({'content': str(chunk)})

        with open(self.chunks_file, 'w', encoding='utf-8') as f:
            json.dump(chunks_data, f, ensure_ascii=False, indent=2)

    def load_chunks(self) -> List[Dict]:
        if not self.chunks_file.exists():
            return []
        with open(self.chunks_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_stats(self, stats: BuildStats):
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats.to_dict(), f, ensure_ascii=False, indent=2)

    def load_stats(self) -> Optional[Dict]:
        if not self.stats_file.exists():
            return None
        with open(self.stats_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_config(self, config: Dict):
        config_file = self.storage_path / "config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def load_config(self) -> Optional[Dict]:
        config_file = self.storage_path / "config.json"
        if not config_file.exists():
            return None
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def exists(self) -> bool:
        return self.metadata_file.exists() or self.chunks_file.exists()

    def delete(self):
        if self.storage_path.exists():
            shutil.rmtree(self.storage_path)

    def get_size(self) -> int:
        total = 0
        for file in self.storage_path.glob("*"):
            if file.is_file():
                total += file.stat().st_size
        return total

    def get_file_info(self) -> Dict[str, int]:
        info = {}
        for file in self.storage_path.glob("*"):
            if file.is_file():
                info[file.name] = file.stat().st_size
        return info


class IndexBuilder:
    def __init__(
        self,
        parser=None,
        chunk_builder=None,
        indexer=None,
        storage=None,
        storage_path: str = "./data"
    ):
        from stage1.parser import CodeParser, DirectoryParser, ChunkBuilder
        from stage1.indexer import CodeIndexer

        self.parser = parser or CodeParser()
        self.directory_parser = DirectoryParser(parser=self.parser)
        self.chunk_builder = chunk_builder or ChunkBuilder()
        self.indexer = indexer or CodeIndexer()
        self.storage = storage or StorageManager(storage_path)
        self.stats = BuildStats()

    def build(
        self,
        source_path: str,
        show_progress: bool = True,
        rebuild: bool = False
    ) -> BuildStats:
        import time
        start_time = time.time()

        source = Path(source_path).resolve()

        if not rebuild and self.storage.exists():
            if show_progress:
                print(f"Index already exists at {self.storage.storage_path}")
                print("Use --rebuild to force rebuild")
            existing_stats = self.storage.load_stats()
            if existing_stats:
                self.stats = BuildStats(**{
                    k: v for k, v in existing_stats.items()
                    if hasattr(self.stats, k)
                })
            return self.stats

        self.storage.ensure_storage()

        if rebuild:
            self.storage.delete()
            self.storage.ensure_storage()

        if show_progress:
            print(f"Building index from: {source}")
            print("-" * 50)

        if show_progress:
            print("[1/4] Parsing directory...")
        file_infos, chunks, parse_stats = self.directory_parser.parse_directory(
            source, show_progress=show_progress
        )
        self.stats = parse_stats

        if show_progress:
            print(f"   Found {len(file_infos)} files, {len(chunks)} chunks")

        if show_progress:
            print("[2/4] Saving chunks...")
        self.storage.save_chunks(chunks)

        if show_progress:
            print("[3/4] Building search index...")
        self.indexer.build(chunks, show_progress=False)

        if show_progress:
            print("[4/4] Saving index to disk...")
        self.indexer.save(
            str(self.storage.index_file),
            str(self.storage.metadata_file),
            str(self.storage.bm25_file)
        )

        self.stats.build_time_seconds = time.time() - start_time
        self.stats.index_size_bytes = self.storage.get_size()
        self.storage.save_stats(self.stats)

        if show_progress:
            print("-" * 50)
            print(f"Build complete in {self.stats.build_time_seconds:.2f}s")
            print(f"  Files: {self.stats.processed_files}")
            print(f"  Chunks: {self.stats.total_chunks}")
            print(f"  Symbols: {self.stats.total_symbols}")
            print(f"  Index size: {self.stats.index_size_bytes / (1024*1024):.2f} MB")

        return self.stats

    def load(self, show_progress: bool = True):
        if not self.storage.exists():
            raise FileNotFoundError("Index not found. Run build first.")

        self.indexer.load(
            str(self.storage.index_file),
            str(self.storage.metadata_file),
            str(self.storage.bm25_file)
        )

        stats = self.storage.load_stats()
        if stats:
            self.stats = BuildStats(**{
                k: v for k, v in stats.items()
                if hasattr(self.stats, k)
            })

        if show_progress:
            print(f"Loaded index with {len(self.indexer.metadata)} chunks")

        return self.indexer

    def get_stats(self) -> Dict:
        stats = self.storage.load_stats()
        if stats:
            info = self.storage.get_file_info()
            stats['files'] = info
        return stats or {}

    def incremental_update(self, source_path: str, show_progress: bool = True):
        pass


def create_builder(
    source_path: str,
    storage_path: str = "./data",
    embedding_dim: int = 128,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    rebuild: bool = False
) -> IndexBuilder:
    from stage1.types import ChunkStrategy
    from stage1.parser import CodeParser, ChunkBuilder
    from stage1.indexer import CodeIndexer, SimpleEmbeddingEngine, VectorIndex

    strategy = ChunkStrategy(
        max_chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        split_by_symbol=True
    )

    parser = CodeParser(strategy=strategy)
    chunk_builder = ChunkBuilder(strategy=strategy)
    embedding = SimpleEmbeddingEngine(dim=embedding_dim)
    vector_index = VectorIndex(dimension=embedding_dim)
    indexer = CodeIndexer(embedding_engine=embedding, vector_index=vector_index)

    builder = IndexBuilder(
        parser=parser,
        chunk_builder=chunk_builder,
        indexer=indexer,
        storage_path=storage_path
    )

    return builder
