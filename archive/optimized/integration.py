import os
import time
from pathlib import Path
from typing import List, Dict, Optional, Set, Any, Callable
from dataclasses import dataclass, field

from optimized.config import AppConfig, ConfigLoader, get_config
from optimized.vector_db import VectorConfig, VectorStore, HybridVectorIndex
from optimized.sharding import ShardingConfig, ShardingFacade, ShardManager
from optimized.cache import CacheConfig, CacheFacade, QueryCacheManager
from optimized.incremental import IncrementalConfig, IncrementalFacade, IncrementalUpdater
from optimized.monitoring import MetricsCollector, StructuredLogger, PerformanceMonitor, HealthChecker
from optimized.storage import StorageFacade
from optimized.chunker import SemanticChunker
from optimized.embedding import EmbeddingEngine


@dataclass
class SystemStats:
    total_files: int = 0
    total_chunks: int = 0
    index_size_mb: float = 0
    cache_hit_rate: float = 0
    shard_count: int = 0
    uptime_seconds: float = 0


class CodeRAGSystem:
    def __init__(self, config_path: str = None, storage_path: str = "./data"):
        self.config = get_config(config_path) if config_path else AppConfig()
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self._start_time = time.time()

        self.metrics = MetricsCollector("code_rag")
        self.logger = StructuredLogger("code_rag", str(self.storage_path / "logs" / "system.log"))
        self.monitor = PerformanceMonitor(self.metrics)

        self._init_components()

    def _init_components(self):
        self.logger.info("Initializing Code RAG System")

        self.storage = StorageFacade(str(self.storage_path))

        self.chunker = SemanticChunker(
            max_size=self.config.chunk.max_size,
            overlap=self.config.chunk.overlap
        )

        self.embedding_engine = EmbeddingEngine(
            model_name=self.config.embedding.model,
            device=self.config.embedding.device
        )

        vector_config = VectorConfig(
            dimension=self.config.embedding.dimension,
            metric="cosine",
            index_type=self.config.index.type,
            nlist=self.config.index.nlist,
            nprobe=self.config.index.nprobe
        )
        self.vector_store = HybridVectorIndex(
            config=vector_config,
            storage_path=str(self.storage_path / "vectors")
        )

        cache_config = CacheConfig(
            max_size=self.config.cache.max_size,
            ttl_seconds=self.config.cache.ttl_seconds,
            persistence_path=str(self.storage_path / "cache")
        )
        self.cache = CacheFacade(cache_config, self)

        sharding_config = ShardingConfig(
            max_shard_size=100 * 1024 * 1024,
            max_files_per_shard=1000
        )
        self.sharding = ShardingFacade(
            storage_path=str(self.storage_path / "shards"),
            config=sharding_config
        )

        incremental_config = IncrementalConfig(
            watch_interval=5.0,
            batch_timeout=2.0
        )
        self.incremental = IncrementalFacade(
            storage=self.storage,
            chunker=self.chunker,
            embedding_engine=self.embedding_engine,
            config=incremental_config
        )

        self.health_checker = HealthChecker()
        self.health_checker.register_check("storage", self._check_storage)
        self.health_checker.register_check("memory", self._check_memory)
        self.health_checker.register_check("disk", self._check_disk)

        self.logger.info("Code RAG System initialized successfully")

    def _check_storage(self) -> tuple:
        try:
            stats = self.storage.stats()
            return True, f"{stats.get('total_chunks', 0)} chunks indexed"
        except Exception as e:
            return False, str(e)

    def _check_memory(self) -> tuple:
        try:
            import psutil
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                return False, f"Memory usage high: {memory.percent}%"
            return True, f"Memory usage: {memory.percent}%"
        except ImportError:
            return True, "psutil not available"

    def _check_disk(self) -> tuple:
        try:
            import shutil
            total, used, free = shutil.disk_usage(self.storage_path)
            percent = (used / total) * 100
            if percent > 90:
                return False, f"Disk usage high: {percent:.1f}%"
            return True, f"Disk usage: {percent:.1f}%"
        except Exception as e:
            return True, f"Disk check skipped: {e}"

    def build_index(
        self,
        source_path: str,
        extensions: Set[str] = None,
        rebuild: bool = False,
        show_progress: bool = True
    ) -> Dict:
        with self.monitor.track_time("build_index"):
            source = Path(source_path).resolve()

            if not source.exists():
                raise ValueError(f"Source path does not exist: {source}")

            extensions = extensions or {
                '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp',
                '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala'
            }

            if rebuild:
                self.logger.info("Rebuilding index from scratch")
                self.storage.clear()
                self.vector_store.delete(list(self.vector_store.vector_store._index.ids))
                self.cache.invalidate()

            stats = self.incremental.sync(source, extensions)

            all_chunks = list(self.storage.sqlite.iter_chunks())

            if all_chunks:
                import numpy as np
                vectors = []
                ids = []
                metadata = []

                for chunk in all_chunks:
                    content = chunk.get('content', '')
                    vec = self.embedding_engine.encode(content, show_progress=False)
                    if isinstance(vec, list):
                        vec = np.array(vec)
                    vectors.append(vec)
                    ids.append(chunk.get('chunk_id', ''))
                    metadata.append(chunk)

                if vectors:
                    vectors = np.array(vectors)
                    self.vector_store.add(vectors, ids, metadata)

            self.logger.info("Index build completed", **stats)

            return {
                'files_added': stats.get('added', 0),
                'files_modified': stats.get('modified', 0),
                'files_deleted': stats.get('deleted', 0),
                'total_chunks': len(all_chunks),
                'time_elapsed': time.time() - self._start_time
            }

    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Dict = None,
        use_cache: bool = True
    ) -> List[Dict]:
        with self.monitor.track_time("search"):
            if use_cache:
                cached = self.cache.get(query, top_k, filters)
                if cached is not None:
                    self.metrics.counter("cache_hits")
                    return cached

            self.metrics.counter("cache_misses")

            import numpy as np
            query_vec = self.embedding_engine.encode(query, show_progress=False)
            if isinstance(query_vec, list):
                query_vec = np.array(query_vec)

            results = self.vector_store.search(query_vec, top_k, filters)

            if use_cache and results:
                self.cache.put(query, results, top_k, filters)

            return results

    def ask(self, question: str, context_chunks: int = 5) -> Dict:
        with self.monitor.track_time("ask"):
            results = self.search(question, top_k=context_chunks)

            context = "\n\n".join([
                f"File: {r.get('metadata', {}).get('file_path', 'unknown')}\n{r.get('metadata', {}).get('content', '')}"
                for r in results
            ])

            return {
                'question': question,
                'context': context,
                'sources': [r.get('metadata', {}).get('file_path', '') for r in results],
                'scores': [r.get('score', 0) for r in results]
            }

    def start_watching(self, source_path: str, extensions: Set[str] = None):
        source = Path(source_path).resolve()
        extensions = extensions or {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp',
            '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala'
        }

        self.incremental.start_watching(source, extensions)
        self.logger.info("Started watching for file changes", path=str(source))

    def stop_watching(self):
        self.incremental.stop_watching()
        self.logger.info("Stopped watching for file changes")

    def warmup_cache(self, queries: List[str] = None):
        popular = self.cache.get_popular_queries(limit=20)
        warmup_queries = queries or [q['query'] for q in popular]

        stats = self.cache.warmup(warmup_queries)
        self.logger.info("Cache warmup completed", **stats)
        return stats

    def health_check(self) -> Dict:
        return self.health_checker.run_checks()

    def stats(self) -> SystemStats:
        storage_stats = self.storage.stats()
        cache_stats = self.cache.stats()

        return SystemStats(
            total_files=storage_stats.get('total_files', 0),
            total_chunks=storage_stats.get('total_chunks', 0),
            index_size_mb=storage_stats.get('size_mb', 0),
            cache_hit_rate=cache_stats.get('memory_cache', {}).get('hit_rate', 0),
            shard_count=len(self.sharding.shard_manager.get_all_shards()),
            uptime_seconds=time.time() - self._start_time
        )

    def export_metrics(self) -> str:
        return self.metrics.export_prometheus()

    def save(self):
        self.vector_store.save()
        self.storage.sqlite.close()
        self.logger.info("System state saved")

    def close(self):
        self.stop_watching()
        self.save()
        self.logger.info("Code RAG System closed")


def create_system(
    config_path: str = None,
    storage_path: str = "./data",
    **kwargs
) -> CodeRAGSystem:
    return CodeRAGSystem(config_path=config_path, storage_path=storage_path)


def quick_search(
    source_path: str,
    query: str,
    top_k: int = 10
) -> List[Dict]:
    system = create_system(storage_path="./temp_data")

    try:
        system.build_index(source_path, show_progress=False)
        return system.search(query, top_k=top_k)
    finally:
        system.close()
