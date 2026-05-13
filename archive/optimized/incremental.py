import os
import json
import hashlib
import time
import threading
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import queue


@dataclass
class FileChange:
    path: str
    change_type: str
    old_hash: str = ""
    new_hash: str = ""
    timestamp: float = 0
    size_diff: int = 0


@dataclass
class ChangeBatch:
    changes: List[FileChange] = field(default_factory=list)
    started_at: float = 0
    completed_at: float = 0
    stats: Dict = field(default_factory=dict)


@dataclass
class IncrementalConfig:
    watch_interval: float = 5.0
    batch_timeout: float = 2.0
    max_batch_size: int = 100
    debounce_ms: int = 500
    ignore_patterns: List[str] = field(default_factory=lambda: [
        '*.pyc', '*.pyo', '__pycache__', '.git', 'node_modules',
        '*.swp', '*.swo', '.DS_Store', 'Thumbs.db'
    ])


class FileHasher:
    def __init__(self, algorithm: str = "md5"):
        self.algorithm = algorithm

    def compute(self, content: str) -> str:
        if self.algorithm == "md5":
            return hashlib.md5(content.encode()).hexdigest()
        elif self.algorithm == "sha256":
            return hashlib.sha256(content.encode()).hexdigest()
        else:
            return hashlib.md5(content.encode()).hexdigest()

    def compute_file(self, path: Path) -> str:
        try:
            content = path.read_text(encoding='utf-8', errors='ignore')
            return self.compute(content)
        except Exception:
            return ""


class ChangeDetector:
    def __init__(self, state_path: str = "./data/file_state.json"):
        self.state_path = Path(state_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.hasher = FileHasher()
        self._state: Dict[str, Dict] = {}
        self._load_state()

    def _load_state(self):
        if self.state_path.exists():
            try:
                with open(self.state_path) as f:
                    self._state = json.load(f)
            except Exception:
                self._state = {}

    def _save_state(self):
        with open(self.state_path, 'w') as f:
            json.dump(self._state, f, indent=2)

    def get_file_state(self, path: Path) -> Optional[Dict]:
        return self._state.get(str(path))

    def has_changed(self, path: Path) -> Tuple[bool, str]:
        path_str = str(path)

        if not path.exists():
            return True, ""

        if path_str not in self._state:
            return True, ""

        current_hash = self.hasher.compute_file(path)
        stored_hash = self._state[path_str].get('hash', '')

        return current_hash != stored_hash, current_hash

    def detect_changes(
        self,
        directory: Path,
        extensions: Set[str],
        ignore_patterns: List[str] = None
    ) -> Tuple[List[Path], List[Path], List[Path]]:
        added = []
        modified = []
        deleted = []

        ignore_patterns = ignore_patterns or []
        current_files = set()

        for ext in extensions:
            for path in directory.rglob(f'*{ext}'):
                if self._should_ignore(path, ignore_patterns):
                    continue

                current_files.add(str(path))
                path_str = str(path)

                if path_str not in self._state:
                    added.append(path)
                else:
                    has_changed, _ = self.has_changed(path)
                    if has_changed:
                        modified.append(path)

        for path_str in list(self._state.keys()):
            if path_str not in current_files:
                deleted.append(Path(path_str))

        return added, modified, deleted

    def _should_ignore(self, path: Path, patterns: List[str]) -> bool:
        import fnmatch

        path_str = str(path)
        for pattern in patterns:
            if fnmatch.fnmatch(path_str, pattern):
                return True
            if fnmatch.fnmatch(path.name, pattern):
                return True
            for part in path.parts:
                if fnmatch.fnmatch(part, pattern):
                    return True
        return False

    def update_state(self, path: Path, content_hash: str, size: int = 0):
        path_str = str(path)
        self._state[path_str] = {
            'hash': content_hash,
            'size': size,
            'last_indexed': time.time(),
            'mtime': path.stat().st_mtime if path.exists() else 0
        }
        self._save_state()

    def remove_state(self, path: Path):
        path_str = str(path)
        if path_str in self._state:
            del self._state[path_str]
            self._save_state()

    def clear_state(self):
        self._state = {}
        self._save_state()


class ChangeBatcher:
    def __init__(self, config: IncrementalConfig = None):
        self.config = config or IncrementalConfig()
        self._pending: Dict[str, FileChange] = {}
        self._lock = threading.Lock()
        self._last_process_time = time.time()

    def add_change(self, change: FileChange):
        with self._lock:
            path = change.path

            if path in self._pending:
                existing = self._pending[path]
                if existing.change_type == 'added' and change.change_type == 'deleted':
                    del self._pending[path]
                elif existing.change_type == 'deleted' and change.change_type == 'added':
                    change.change_type = 'modified'
                    self._pending[path] = change
                else:
                    self._pending[path] = change
            else:
                self._pending[path] = change

    def get_batch(self) -> ChangeBatch:
        with self._lock:
            if not self._pending:
                return ChangeBatch()

            batch = ChangeBatch(
                changes=list(self._pending.values()),
                started_at=time.time()
            )
            self._pending = {}
            batch.completed_at = time.time()
            batch.stats = {
                'total': len(batch.changes),
                'added': sum(1 for c in batch.changes if c.change_type == 'added'),
                'modified': sum(1 for c in batch.changes if c.change_type == 'modified'),
                'deleted': sum(1 for c in batch.changes if c.change_type == 'deleted')
            }

            return batch

    def has_pending(self) -> bool:
        with self._lock:
            return len(self._pending) > 0

    def should_process(self) -> bool:
        if not self.has_pending():
            return False

        time_since_last = time.time() - self._last_process_time
        return time_since_last >= self.config.batch_timeout

    def mark_processed(self):
        self._last_process_time = time.time()


class FileWatcher:
    def __init__(self, config: IncrementalConfig = None):
        self.config = config or IncrementalConfig()
        self._watching = False
        self._watch_thread: Optional[threading.Thread] = None
        self._change_queue: queue.Queue = queue.Queue()
        self._callbacks: List[Callable] = []
        self._stop_event = threading.Event()

    def add_callback(self, callback: Callable):
        self._callbacks.append(callback)

    def start(self, directory: Path, extensions: Set[str]):
        if self._watching:
            return

        self._watching = True
        self._stop_event.clear()

        def _watch_loop():
            detector = ChangeDetector()
            last_check = time.time()

            while not self._stop_event.is_set():
                time.sleep(self.config.watch_interval)

                try:
                    added, modified, deleted = detector.detect_changes(
                        directory, extensions, self.config.ignore_patterns
                    )

                    now = time.time()
                    for path in added:
                        self._change_queue.put(FileChange(
                            path=str(path),
                            change_type='added',
                            timestamp=now
                        ))

                    for path in modified:
                        self._change_queue.put(FileChange(
                            path=str(path),
                            change_type='modified',
                            timestamp=now
                        ))

                    for path in deleted:
                        self._change_queue.put(FileChange(
                            path=str(path),
                            change_type='deleted',
                            timestamp=now
                        ))

                except Exception:
                    pass

        self._watch_thread = threading.Thread(target=_watch_loop, daemon=True)
        self._watch_thread.start()

    def stop(self):
        self._watching = False
        self._stop_event.set()
        if self._watch_thread:
            self._watch_thread.join(timeout=5)

    def get_changes(self, timeout: float = 0.1) -> List[FileChange]:
        changes = []
        try:
            while True:
                change = self._change_queue.get(timeout=timeout)
                changes.append(change)
        except queue.Empty:
            pass
        return changes


class IncrementalUpdater:
    def __init__(
        self,
        storage,
        chunker,
        embedding_engine,
        config: IncrementalConfig = None
    ):
        self.storage = storage
        self.chunker = chunker
        self.embedding_engine = embedding_engine
        self.config = config or IncrementalConfig()

        self.detector = ChangeDetector()
        self.batcher = ChangeBatcher(self.config)
        self.watcher = FileWatcher(self.config)

        self._update_callbacks: List[Callable] = []
        self._lock = threading.Lock()

    def add_update_callback(self, callback: Callable):
        self._update_callbacks.append(callback)

    def sync(self, directory: Path, extensions: Set[str]) -> Dict:
        added, modified, deleted = self.detector.detect_changes(
            directory, extensions, self.config.ignore_patterns
        )

        stats = {
            'added': 0,
            'modified': 0,
            'deleted': 0,
            'failed': 0,
            'chunks_added': 0,
            'chunks_removed': 0
        }

        for path in deleted:
            try:
                removed = self._remove_file(path)
                stats['deleted'] += 1
                stats['chunks_removed'] += removed
            except Exception:
                stats['failed'] += 1

        for path in added + modified:
            try:
                added_chunks = self._index_file(path)
                if path in added:
                    stats['added'] += 1
                else:
                    stats['modified'] += 1
                stats['chunks_added'] += added_chunks
            except Exception:
                stats['failed'] += 1

        self._notify_callbacks(stats)
        return stats

    def _index_file(self, path: Path) -> int:
        content = path.read_text(encoding='utf-8', errors='ignore')
        content_hash = self.detector.hasher.compute(content)

        chunks = self.chunker.chunk(content, str(path))

        self.storage.save_chunks(chunks)

        self.detector.update_state(path, content_hash, len(content))

        return len(chunks)

    def _remove_file(self, path: Path) -> int:
        chunks = self.storage.get_by_file(str(path))
        chunk_count = len(chunks)

        self.storage.delete_by_file(str(path))
        self.detector.remove_state(path)

        return chunk_count

    def start_watching(self, directory: Path, extensions: Set[str]):
        def _on_changes(changes: List[FileChange]):
            for change in changes:
                self.batcher.add_change(change)

            if self.batcher.should_process():
                batch = self.batcher.get_batch()
                self._process_batch(batch)

        self.watcher.add_callback(_on_changes)
        self.watcher.start(directory, extensions)

    def stop_watching(self):
        self.watcher.stop()

    def _process_batch(self, batch: ChangeBatch):
        for change in batch.changes:
            try:
                if change.change_type == 'deleted':
                    self._remove_file(Path(change.path))
                else:
                    self._index_file(Path(change.path))
            except Exception:
                pass

        self.batcher.mark_processed()

    def _notify_callbacks(self, stats: Dict):
        for callback in self._update_callbacks:
            try:
                callback(stats)
            except Exception:
                pass

    def get_pending_changes(self) -> List[FileChange]:
        batch = self.batcher.get_batch()
        return batch.changes


class DiffProcessor:
    def __init__(self):
        self._diff_cache: Dict[str, Dict] = {}

    def compute_diff(self, old_content: str, new_content: str) -> Dict:
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()

        old_set = set(enumerate(old_lines))
        new_set = set(enumerate(new_lines))

        removed = [(i, line) for i, line in old_set if line not in new_lines]
        added = [(i, line) for i, line in new_set if line not in old_lines]

        return {
            'removed_lines': len(removed),
            'added_lines': len(added),
            'removed': [line for _, line in removed[:100]],
            'added': [line for _, line in added[:100]]
        }

    def get_affected_chunks(self, diff: Dict, chunks: List[Dict]) -> List[Dict]:
        affected = []

        added_lines = set(diff.get('added', []))
        removed_lines = set(diff.get('removed', []))

        for chunk in chunks:
            content = chunk.get('content', '')
            chunk_lines = set(content.splitlines())

            if chunk_lines & added_lines or chunk_lines & removed_lines:
                affected.append(chunk)

        return affected


class UpdateScheduler:
    def __init__(self, updater: IncrementalUpdater):
        self.updater = updater
        self._scheduled_updates: List[Dict] = []
        self._running = False
        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def schedule_update(self, path: Path, delay_seconds: float = 0):
        self._scheduled_updates.append({
            'path': path,
            'scheduled_at': time.time(),
            'execute_at': time.time() + delay_seconds
        })

    def start(self):
        if self._running:
            return

        self._running = True
        self._stop_event.clear()

        def _scheduler_loop():
            while not self._stop_event.is_set():
                now = time.time()
                to_execute = [
                    u for u in self._scheduled_updates
                    if u['execute_at'] <= now
                ]

                for update in to_execute:
                    try:
                        self.updater._index_file(update['path'])
                    except Exception:
                        pass
                    self._scheduled_updates.remove(update)

                time.sleep(1)

        self._scheduler_thread = threading.Thread(target=_scheduler_loop, daemon=True)
        self._scheduler_thread.start()

    def stop(self):
        self._running = False
        self._stop_event.set()
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)


class IncrementalFacade:
    def __init__(
        self,
        storage,
        chunker,
        embedding_engine,
        config: IncrementalConfig = None
    ):
        self.config = config or IncrementalConfig()
        self.updater = IncrementalUpdater(storage, chunker, embedding_engine, config)
        self.diff_processor = DiffProcessor()
        self.scheduler = UpdateScheduler(self.updater)

    def sync(self, directory: Path, extensions: Set[str]) -> Dict:
        return self.updater.sync(directory, extensions)

    def start_watching(self, directory: Path, extensions: Set[str]):
        self.updater.start_watching(directory, extensions)
        self.scheduler.start()

    def stop_watching(self):
        self.updater.stop_watching()
        self.scheduler.stop()

    def get_state(self) -> Dict:
        return {
            'file_count': len(self.updater.detector._state),
            'pending_changes': len(self.updater.batcher.get_batch().changes)
        }

    def clear_state(self):
        self.updater.detector.clear_state()

    def on_file_change(self, callback: Callable):
        self.updater.add_update_callback(callback)
