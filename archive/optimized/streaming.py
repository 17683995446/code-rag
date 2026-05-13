import os
import time
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Any, Iterator, Callable, Generator
from dataclasses import dataclass, field
from collections import deque
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import threading
import queue


@dataclass
class BatchResult:
    batch_id: str
    files_processed: int
    chunks_created: int
    embeddings_computed: int
    time_seconds: float
    errors: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


@dataclass
class IndexProgress:
    total_files: int = 0
    processed_files: int = 0
    total_chunks: int = 0
    failed_files: int = 0
    start_time: float = 0
    estimated_remaining: float = 0
    current_file: str = ""
    status: str = "idle"


class StreamingFileReader:
    def __init__(
        self,
        extensions: set = None,
        skip_dirs: set = None,
        max_file_size: int = 10 * 1024 * 1024
    ):
        self.extensions = extensions or {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp',
            '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala'
        }
        self.skip_dirs = skip_dirs or {
            'node_modules', '__pycache__', '.git', '.svn', 'venv', 'env',
            'build', 'dist', 'target', '.idea', '.vscode', 'vendor'
        }
        self.max_file_size = max_file_size

    def stream_files(self, root_path: Path) -> Generator[Path, None, None]:
        if not root_path.exists():
            return

        for path in root_path.rglob('*'):
            if not path.is_file():
                continue

            if not self._should_process(path):
                continue

            yield path

    def _should_process(self, path: Path) -> bool:
        if path.suffix not in self.extensions:
            return False

        for part in path.parts:
            if part in self.skip_dirs:
                return False

        try:
            if path.stat().st_size > self.max_file_size:
                return False
        except Exception:
            return False

        return True


class ChunkBuilder:
    def __init__(
        self,
        max_chunk_size: int = 512,
        overlap: int = 50,
        preserve_context: bool = True
    ):
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
        self.preserve_context = preserve_context

    def build_chunks(
        self,
        content: str,
        file_path: str,
        chunk_id_prefix: str = ""
    ) -> List[Dict]:
        chunks = []

        if self._is_code(content):
            chunks = self._chunk_by_language(content, file_path, chunk_id_prefix)
        else:
            chunks = self._chunk_by_lines(content, file_path, chunk_id_prefix)

        for i, chunk in enumerate(chunks):
            chunk['chunk_index'] = i
            chunk['total_chunks'] = len(chunks)

        return chunks

    def _is_code(self, content: str) -> bool:
        code_indicators = [
            'def ', 'class ', 'function ', 'const ', 'let ', 'var ',
            'import ', 'export ', 'return ', 'if (', 'for (', 'while (',
            'public ', 'private ', 'static ', 'void ', 'int ', 'string '
        ]

        indicator_count = sum(1 for ind in code_indicators if ind in content)
        return indicator_count >= 2

    def _chunk_by_language(self, content: str, file_path: str, prefix: str) -> List[Dict]:
        chunks = []
        lines = content.split('\n')

        current_chunk = []
        current_size = 0
        chunk_id = 0

        function_patterns = [
            r'^(def |class |function |async |public |private |static )',
            r'^(import |from |export |const |let |var )',
        ]

        import re
        function_import_lines = set()

        for i, line in enumerate(lines):
            is_function = any(re.match(p, line.strip()) for p in function_patterns)
            if is_function:
                function_import_lines.add(i)

        for i, line in enumerate(lines):
            line_size = len(line)

            if is_function and current_chunk:
                chunks.append(self._create_chunk(
                    current_chunk, file_path, prefix, chunk_id
                ))
                chunk_id += 1
                current_chunk = []
                current_size = 0

            current_chunk.append(line)
            current_size += line_size + 1

            if current_size >= self.max_chunk_size and current_chunk:
                chunks.append(self._create_chunk(
                    current_chunk, file_path, prefix, chunk_id
                ))
                chunk_id += 1

                overlap_lines = current_chunk[-self.overlap:] if self.overlap > 0 else []
                current_chunk = overlap_lines
                current_size = sum(len(l) for l in current_chunk) + len(current_chunk)

        if current_chunk:
            chunks.append(self._create_chunk(
                current_chunk, file_path, prefix, chunk_id
            ))

        return chunks

    def _chunk_by_lines(self, content: str, file_path: str, prefix: str) -> List[Dict]:
        chunks = []
        lines = content.split('\n')

        current_chunk = []
        current_size = 0
        chunk_id = 0

        for line in lines:
            line_size = len(line)

            if current_size + line_size > self.max_chunk_size and current_chunk:
                chunks.append(self._create_chunk(
                    current_chunk, file_path, prefix, chunk_id
                ))
                chunk_id += 1
                current_chunk = []
                current_size = 0

            current_chunk.append(line)
            current_size += line_size + 1

        if current_chunk:
            chunks.append(self._create_chunk(
                current_chunk, file_path, prefix, chunk_id
            ))

        return chunks

    def _create_chunk(
        self,
        lines: List[str],
        file_path: str,
        prefix: str,
        chunk_id: int
    ) -> Dict:
        content = '\n'.join(lines)

        file_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
        chunk_id_str = f"{prefix}{file_hash}_{chunk_id:04d}" if prefix else f"{file_hash}_{chunk_id:04d}"

        return {
            'chunk_id': chunk_id_str,
            'file_path': file_path,
            'content': content,
            'line_start': 0,
            'line_end': len(lines),
            'size': len(content)
        }


class BatchProcessor:
    def __init__(
        self,
        batch_size: int = 100,
        max_workers: int = 4,
        use_processes: bool = False
    ):
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.use_processes = use_processes

    def process_batch(
        self,
        items: List[Any],
        process_func: Callable
    ) -> List[Any]:
        results = []

        executor_class = ProcessPoolExecutor if self.use_processes else ThreadPoolExecutor

        with executor_class(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(process_func, item): i
                for i, item in enumerate(items)
            }

            results = [None] * len(items)

            for future in as_completed(futures):
                idx = futures[future]
                try:
                    result = future.result()
                    results[idx] = result
                except Exception as e:
                    results[idx] = {'error': str(e)}

        return results


class StreamingIndexer:
    def __init__(
        self,
        chunker: ChunkBuilder = None,
        batch_processor: BatchProcessor = None,
        storage = None,
        embedding_engine = None
    ):
        self.chunker = chunker or ChunkBuilder()
        self.batch_processor = batch_processor or BatchProcessor()
        self.storage = storage
        self.embedding_engine = embedding_engine

        self.progress = IndexProgress()
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._callbacks: List[Callable] = []

    def add_progress_callback(self, callback: Callable):
        self._callbacks.append(callback)

    def _notify_progress(self):
        for callback in self._callbacks:
            try:
                callback(self.progress)
            except Exception:
                pass

    def index_directory(
        self,
        root_path: Path,
        extensions: set = None,
        show_progress: bool = True
    ) -> Generator[BatchResult, None, None]:
        file_reader = StreamingFileReader(extensions=extensions)

        self.progress = IndexProgress()
        self.progress.start_time = time.time()
        self.progress.status = "scanning"

        files = list(file_reader.stream_files(root_path))
        self.progress.total_files = len(files)

        if show_progress:
            print(f"Found {len(files)} files to index")

        self.progress.status = "indexing"

        batch = []
        batch_id = 0

        for file_path in files:
            if self._stop_event.is_set():
                self.progress.status = "stopped"
                break

            self._pause_event.wait()

            self.progress.current_file = str(file_path)
            self._notify_progress()

            try:
                chunk_result = self._process_file(file_path)
                if chunk_result:
                    batch.extend(chunk_result)

                    self.progress.processed_files += 1
                    self.progress.total_chunks += len(chunk_result)

            except Exception as e:
                self.progress.failed_files += 1
                if show_progress:
                    print(f"Error processing {file_path}: {e}")

            if len(batch) >= self.batch_processor.batch_size:
                batch_result = self._flush_batch(batch, batch_id)
                yield batch_result
                batch = []
                batch_id += 1

            elapsed = time.time() - self.progress.start_time
            if self.progress.processed_files > 0:
                avg_time = elapsed / self.progress.processed_files
                remaining = (self.progress.total_files - self.progress.processed_files) * avg_time
                self.progress.estimated_remaining = remaining

            self._notify_progress()

        if batch:
            batch_result = self._flush_batch(batch, batch_id)
            yield batch_result

        self.progress.status = "completed"

    def _process_file(self, file_path: Path) -> List[Dict]:
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            chunks = self.chunker.build_chunks(content, str(file_path))

            for chunk in chunks:
                chunk['content_hash'] = hashlib.md5(chunk['content'].encode()).hexdigest()

            return chunks

        except Exception as e:
            return []

    def _flush_batch(self, batch: List[Dict], batch_id: int) -> BatchResult:
        start_time = time.time()
        errors = []

        try:
            if self.storage:
                self.storage.save_chunks(batch)

            if self.embedding_engine:
                embeddings = self._compute_embeddings(batch)
                if embeddings:
                    pass

        except Exception as e:
            errors.append(str(e))

        return BatchResult(
            batch_id=f"batch_{batch_id:04d}",
            files_processed=len(set(c.get('file_path') for c in batch)),
            chunks_created=len(batch),
            embeddings_computed=0,
            time_seconds=time.time() - start_time,
            errors=errors
        )

    def _compute_embeddings(self, chunks: List[Dict]) -> List[List[float]]:
        if not self.embedding_engine:
            return []

        contents = [c['content'] for c in chunks]

        try:
            embeddings = self.embedding_engine.encode(contents, show_progress=False)
            return embeddings
        except Exception:
            return []

    def stop(self):
        self._stop_event.set()

    def pause(self):
        self._pause_event.clear()

    def resume(self):
        self._pause_event.set()

    def get_progress(self) -> IndexProgress:
        return self.progress


class IncrementalStreamingIndexer(StreamingIndexer):
    def __init__(
        self,
        state_path: str = "./data/index_state.json",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.state_path = Path(state_path)
        self.state: Dict = {}
        self._load_state()

    def _load_state(self):
        if self.state_path.exists():
            try:
                with open(self.state_path) as f:
                    self.state = json.load(f)
            except Exception:
                self.state = {}

    def _save_state(self):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_path, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _should_index(self, file_path: Path) -> bool:
        path_str = str(file_path)

        if path_str not in self.state:
            return True

        try:
            current_mtime = file_path.stat().st_mtime
            current_size = file_path.stat().st_size

            stored = self.state.get(path_str, {})
            if stored.get('mtime') != current_mtime or stored.get('size') != current_size:
                return True

        except Exception:
            return True

        return False

    def index_directory(
        self,
        root_path: Path,
        extensions: set = None,
        show_progress: bool = True
    ) -> Generator[BatchResult, None, None]:
        file_reader = StreamingFileReader(extensions=extensions)

        self.progress = IndexProgress()
        self.progress.start_time = time.time()
        self.progress.status = "indexing"

        files_to_index = []
        files_to_remove = []

        for file_path in file_reader.stream_files(root_path):
            if self._should_index(file_path):
                files_to_index.append(file_path)
            else:
                files_to_index.append(file_path)

        all_indexed_files = set(str(f) for f in files_to_index)

        for indexed_file in list(self.state.keys()):
            if indexed_file not in all_indexed_files:
                files_to_remove.append(indexed_file)

        self.progress.total_files = len(files_to_index)

        if show_progress:
            print(f"Indexing {len(files_to_index)} files (incremental)")

        if files_to_remove:
            for file_path in files_to_remove:
                if file_path in self.state:
                    del self.state[file_path]
            self._save_state()
            if show_progress:
                print(f"Removed {len(files_to_remove)} deleted files from index")

        batch = []
        batch_id = 0

        for file_path in files_to_index:
            if self._stop_event.is_set():
                break

            self._pause_event.wait()

            self.progress.current_file = str(file_path)
            self._notify_progress()

            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                chunks = self.chunker.build_chunks(content, str(file_path))

                for chunk in chunks:
                    chunk['content_hash'] = hashlib.md5(chunk['content'].encode()).hexdigest()
                    batch.append(chunk)

                self.state[str(file_path)] = {
                    'mtime': file_path.stat().st_mtime,
                    'size': file_path.stat().st_size,
                    'chunk_count': len(chunks),
                    'indexed_at': time.time()
                }

                self.progress.processed_files += 1
                self.progress.total_chunks += len(chunks)

            except Exception as e:
                self.progress.failed_files += 1

            if len(batch) >= self.batch_processor.batch_size:
                batch_result = self._flush_batch(batch, batch_id)
                yield batch_result
                batch = []
                batch_id += 1

            self._notify_progress()

        if batch:
            batch_result = self._flush_batch(batch, batch_id)
            yield batch_result

        self._save_state()
        self.progress.status = "completed"


class ParallelStreamingIndexer(StreamingIndexer):
    def __init__(self, max_workers: int = 4, **kwargs):
        super().__init__(**kwargs)
        self.max_workers = max_workers
        self._executor: Optional[ThreadPoolExecutor] = None

    def index_directory(
        self,
        root_path: Path,
        extensions: set = None,
        show_progress: bool = True
    ) -> Generator[BatchResult, None, None]:
        file_reader = StreamingFileReader(extensions=extensions)

        self.progress = IndexProgress()
        self.progress.start_time = time.time()
        self.progress.status = "indexing"

        files = list(file_reader.stream_files(root_path))
        self.progress.total_files = len(files)

        if show_progress:
            print(f"Found {len(files)} files, indexing with {self.max_workers} workers")

        self._executor = ThreadPoolExecutor(max_workers=self.max_workers)

        batch_queue = queue.Queue()
        result_queue = queue.Queue()

        def file_processor(file_path: Path):
            try:
                chunks = self._process_file(file_path)
                return {'file': str(file_path), 'chunks': chunks, 'success': True}
            except Exception as e:
                return {'file': str(file_path), 'chunks': [], 'success': False, 'error': str(e)}

        futures = []
        for file_path in files:
            future = self._executor.submit(file_processor, file_path)
            futures.append(future)

        batch = []
        batch_id = 0

        for i, future in enumerate(as_completed(futures)):
            if self._stop_event.is_set():
                break

            result = future.result()

            if result['success']:
                batch.extend(result['chunks'])
                self.progress.processed_files += 1
                self.progress.total_chunks += len(result['chunks'])
            else:
                self.progress.failed_files += 1

            self.progress.current_file = result['file']
            self._notify_progress()

            if len(batch) >= self.batch_processor.batch_size:
                batch_result = self._flush_batch(batch, batch_id)
                yield batch_result
                batch = []
                batch_id += 1

        if batch:
            batch_result = self._flush_batch(batch, batch_id)
            yield batch_result

        if self._executor:
            self._executor.shutdown(wait=False)
            self._executor = None

        self.progress.status = "completed"
