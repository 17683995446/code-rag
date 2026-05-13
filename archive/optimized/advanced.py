import os
import json
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import threading


@dataclass
class FileState:
    path: str
    mtime: float
    size: int
    content_hash: str
    chunk_count: int = 0
    last_indexed: float = 0


@dataclass
class IndexState:
    files: Dict[str, FileState] = field(default_factory=dict)
    total_chunks: int = 0
    last_updated: float = 0
    version: str = "1.0"


class FileWatcher:
    def __init__(self, state_path: str = "./data/index_state.json"):
        self.state_path = Path(state_path)
        self.state = self._load_state()

    def _load_state(self) -> IndexState:
        if self.state_path.exists():
            try:
                with open(self.state_path) as f:
                    data = json.load(f)
                state = IndexState()
                for path, fs_data in data.get('files', {}).items():
                    state.files[path] = FileState(**fs_data)
                state.total_chunks = data.get('total_chunks', 0)
                state.last_updated = data.get('last_updated', 0)
                state.version = data.get('version', '1.0')
                return state
            except Exception:
                pass
        return IndexState()

    def _save_state(self):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            'files': {
                path: {
                    'path': fs.path,
                    'mtime': fs.mtime,
                    'size': fs.size,
                    'content_hash': fs.content_hash,
                    'chunk_count': fs.chunk_count,
                    'last_indexed': fs.last_indexed
                }
                for path, fs in self.state.files.items()
            },
            'total_chunks': self.state.total_chunks,
            'last_updated': self.state.last_updated,
            'version': self.state.version
        }
        with open(self.state_path, 'w') as f:
            json.dump(data, f, indent=2)

    def compute_hash(self, content: str) -> str:
        return hashlib.md5(content.encode()).hexdigest()

    def get_file_state(self, path: Path) -> Optional[FileState]:
        return self.state.files.get(str(path))

    def has_changed(self, path: Path) -> bool:
        if not path.exists():
            return False

        stat = path.stat()
        str_path = str(path)

        if str_path not in self.state.files:
            return True

        fs = self.state.files[str_path]
        if fs.mtime != stat.st_mtime or fs.size != stat.st_size:
            return True

        return False

    def update_file_state(self, path: Path, content: str, chunk_count: int):
        str_path = str(path)
        stat = path.stat()

        self.state.files[str_path] = FileState(
            path=str_path,
            mtime=stat.st_mtime,
            size=stat.st_size,
            content_hash=self.compute_hash(content),
            chunk_count=chunk_count,
            last_indexed=time.time()
        )
        self.state.last_updated = time.time()
        self._save_state()

    def remove_file_state(self, path: Path):
        str_path = str(path)
        if str_path in self.state.files:
            del self.state.files[str_path]
            self._save_state()

    def get_changed_files(self, directory: Path, extensions: Set[str]) -> Tuple[List[Path], List[Path], List[Path]]:
        added = []
        modified = []
        deleted = []

        current_files = set()
        for ext in extensions:
            for path in directory.rglob(f'*{ext}'):
                if self._should_skip(path):
                    continue
                current_files.add(path)

                if str(path) not in self.state.files:
                    added.append(path)
                elif self.has_changed(path):
                    modified.append(path)

        for path_str in self.state.files:
            if Path(path_str) not in current_files:
                deleted.append(Path(path_str))

        return added, modified, deleted

    def _should_skip(self, path: Path) -> bool:
        skip_dirs = {
            'node_modules', '__pycache__', '.git', '.svn', 'venv', 'env',
            'build', 'dist', 'target', '.idea', '.vscode', 'vendor'
        }
        return any(part in skip_dirs for part in path.parts)


class IncrementalIndexer:
    def __init__(
        self,
        storage,
        chunker,
        embedding_engine,
        state_path: str = "./data/index_state.json"
    ):
        self.storage = storage
        self.chunker = chunker
        self.embedding_engine = embedding_engine
        self.watcher = FileWatcher(state_path)

    def sync(
        self,
        directory: Path,
        extensions: Set[str],
        show_progress: bool = True
    ) -> Dict:
        added, modified, deleted = self.watcher.get_changed_files(directory, extensions)

        stats = {
            'added': len(added),
            'modified': len(modified),
            'deleted': len(deleted),
            'total_changes': len(added) + len(modified) + len(deleted)
        }

        if show_progress and stats['total_changes'] > 0:
            print(f"Changes detected: +{len(added)} ~{len(modified)} -{len(deleted)}")

        for path in deleted:
            self._remove_file_chunks(path)
            self.watcher.remove_file_state(path)

        for path in added + modified:
            self._index_file(path)

        return stats

    def _index_file(self, path: Path):
        try:
            content = path.read_text(encoding='utf-8', errors='ignore')
            chunks = self.chunker.chunk(content, str(path))

            self.storage.save_chunks(chunks)

            self.watcher.update_file_state(path, content, len(chunks))

        except Exception as e:
            print(f"Error indexing {path}: {e}")

    def _remove_file_chunks(self, path: Path):
        try:
            chunks = self.storage.get_by_file(str(path))
            for chunk in chunks:
                chunk_id = chunk.get('chunk_id', '')
        except Exception:
            pass


class ParallelProcessor:
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or os.cpu_count() or 4

    def process_files(
        self,
        files: List[Path],
        process_func,
        use_processes: bool = False
    ) -> List:
        results = []

        executor_class = ProcessPoolExecutor if use_processes else ThreadPoolExecutor

        with executor_class(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(process_func, f): f
                for f in files
            }

            for future in as_completed(future_to_file):
                file = future_to_file[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    print(f"Error processing {file}: {e}")

        return results

    def batch_embed(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List:
        from optimized.embedding import EmbeddingEngine

        engine = EmbeddingEngine()
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = engine.encode(batch, show_progress=False)
            all_embeddings.extend(embeddings)

        return all_embeddings


class QueryCache:
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Tuple[List, float]] = {}
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def _hash_query(self, query: str, top_k: int, filters: Dict = None) -> str:
        key = f"{query}:{top_k}:{json.dumps(filters or {}, sort_keys=True)}"
        return hashlib.md5(key.encode()).hexdigest()

    def get(self, query: str, top_k: int, filters: Dict = None) -> Optional[List]:
        key = self._hash_query(query, top_k, filters)

        with self._lock:
            if key in self._cache:
                results, timestamp = self._cache[key]
                if time.time() - timestamp < self.ttl_seconds:
                    self._hits += 1
                    return results
                else:
                    del self._cache[key]

            self._misses += 1
            return None

    def put(self, query: str, top_k: int, results: List, filters: Dict = None):
        key = self._hash_query(query, top_k, filters)

        with self._lock:
            if len(self._cache) >= self.max_size:
                self._evict_oldest()

            self._cache[key] = (results, time.time())

    def _evict_oldest(self):
        if not self._cache:
            return

        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
        del self._cache[oldest_key]

    def clear(self):
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def stats(self) -> Dict:
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': hit_rate
            }


class QueryOptimizer:
    def __init__(self):
        self.query_patterns = {
            'exact_line': r'^(\S+):(\d+)(?:-(\d+))?$',
            'symbol': r'^(?:def|class|function)\s+(\w+)$',
            'file': r'^(?:in|file)\s+(\S+)$',
            'keyword': r'^\w+(?:\s+\w+)*$'
        }

    def analyze_query(self, query: str) -> Dict:
        import re

        analysis = {
            'type': 'semantic',
            'patterns': [],
            'entities': [],
            'keywords': []
        }

        for pattern_name, pattern in self.query_patterns.items():
            match = re.match(pattern, query.strip())
            if match:
                analysis['patterns'].append(pattern_name)
                analysis['type'] = pattern_name

        words = re.findall(r'\b\w+\b', query.lower())
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare', 'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as'}

        analysis['keywords'] = [w for w in words if w not in stop_words and len(w) > 2]

        camel_case = re.findall(r'[A-Z][a-z]+(?:[A-Z][a-z]+)+', query)
        analysis['entities'].extend(camel_case)

        return analysis

    def optimize_search(self, query: str, indexer, cache: QueryCache = None) -> List:
        analysis = self.analyze_query(query)

        if cache:
            cached = cache.get(query, 10)
            if cached:
                return cached

        results = []

        if analysis['type'] == 'exact_line':
            match = re.match(self.query_patterns['exact_line'], query.strip())
            if match:
                file_path = match.group(1)
                line = int(match.group(2))
                results = indexer.search_by_file_line(file_path, line)

        elif analysis['type'] == 'symbol':
            match = re.match(self.query_patterns['symbol'], query.strip())
            if match:
                symbol_name = match.group(1)
                results = indexer.search_by_symbol(symbol_name)

        else:
            results = indexer.search(query, top_k=10)

        if cache and results:
            cache.put(query, 10, results)

        return results


class IndexManager:
    def __init__(
        self,
        storage_path: str = "./data",
        max_workers: int = 4,
        cache_size: int = 1000
    ):
        from optimized.storage import StorageFacade
        from optimized.chunker import SemanticChunker
        from optimized.embedding import EmbeddingEngine, OptimizedIndexer

        self.storage = StorageFacade(storage_path)
        self.chunker = SemanticChunker()
        self.embedding_engine = EmbeddingEngine()
        self.indexer = OptimizedIndexer(embedding_engine=self.embedding_engine)

        self.incremental = IncrementalIndexer(
            self.storage, self.chunker, self.embedding_engine,
            state_path=f"{storage_path}/index_state.json"
        )

        self.parallel = ParallelProcessor(max_workers)
        self.cache = QueryCache(max_size=cache_size)
        self.optimizer = QueryOptimizer()

        self.extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp',
            '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala'
        }

    def build(self, source_path: str, rebuild: bool = False) -> Dict:
        start_time = time.time()

        source = Path(source_path).resolve()

        if rebuild:
            self.storage.clear()
            self.cache.clear()

        stats = self.incremental.sync(source, self.extensions)

        all_chunks = list(self.storage.sqlite.iter_chunks())
        self.indexer.build_index(all_chunks, show_progress=False)

        elapsed = time.time() - start_time

        return {
            'files_added': stats['added'],
            'files_modified': stats['modified'],
            'files_deleted': stats['deleted'],
            'total_chunks': len(all_chunks),
            'time_seconds': elapsed
        }

    def search(self, query: str, top_k: int = 10) -> List:
        return self.optimizer.optimize_search(query, self.indexer, self.cache)

    def stats(self) -> Dict:
        storage_stats = self.storage.stats()
        cache_stats = self.cache.stats()

        return {
            **storage_stats,
            'cache': cache_stats
        }
