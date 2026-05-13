import os
import json
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple, Any, Iterator
from dataclasses import dataclass, field
from collections import defaultdict
import threading


@dataclass
class ShardInfo:
    shard_id: str
    path: str
    file_count: int = 0
    chunk_count: int = 0
    size_bytes: int = 0
    last_updated: float = 0
    metadata: Dict = field(default_factory=dict)


@dataclass
class ShardingConfig:
    max_shard_size: int = 100 * 1024 * 1024
    max_files_per_shard: int = 1000
    max_chunks_per_shard: int = 50000
    strategy: str = "directory"
    target_shard_count: int = 10


class DirectoryAnalyzer:
    def __init__(self):
        self.skip_dirs = {
            'node_modules', '__pycache__', '.git', '.svn', 'venv', 'env',
            'build', 'dist', 'target', '.idea', '.vscode', 'vendor',
            '.tox', '.eggs', 'eggs', 'lib', 'libs', 'third_party'
        }

    def analyze(self, root_path: Path) -> Dict[str, Dict]:
        structure = {}
        root_path = root_path.resolve()

        for path in root_path.rglob('*'):
            if not path.is_file():
                continue

            rel_path = path.relative_to(root_path)
            parts = rel_path.parts

            if any(part in self.skip_dirs for part in parts):
                continue

            module_path = self._identify_module(root_path, path)
            if module_path not in structure:
                structure[module_path] = {
                    'files': [],
                    'total_size': 0,
                    'extensions': set()
                }

            stat = path.stat()
            structure[module_path]['files'].append(str(path))
            structure[module_path]['total_size'] += stat.st_size
            structure[module_path]['extensions'].add(path.suffix)

        for module in structure:
            structure[module]['extensions'] = list(structure[module]['extensions'])

        return structure

    def _identify_module(self, root: Path, file_path: Path) -> str:
        rel = file_path.relative_to(root)
        parts = list(rel.parts[:-1])

        module_markers = {
            '__init__.py', 'setup.py', 'pyproject.toml', 'package.json',
            'Cargo.toml', 'go.mod', 'pom.xml', 'build.gradle', 'Makefile'
        }

        current = file_path.parent
        while current != root:
            for marker in module_markers:
                if (current / marker).exists():
                    return str(current.relative_to(root))
            current = current.parent

        if parts:
            return parts[0]

        return 'root'


class ShardPlanner:
    def __init__(self, config: ShardingConfig = None):
        self.config = config or ShardingConfig()
        self.analyzer = DirectoryAnalyzer()

    def plan(self, root_path: Path) -> List[ShardInfo]:
        structure = self.analyzer.analyze(root_path)

        shards = []
        current_shard = None
        shard_idx = 0

        sorted_modules = sorted(structure.items(), key=lambda x: -x[1]['total_size'])

        for module_path, info in sorted_modules:
            if current_shard is None:
                current_shard = self._create_shard(shard_idx)
                shard_idx += 1

            if self._should_split(current_shard, info):
                shards.append(current_shard)
                current_shard = self._create_shard(shard_idx)
                shard_idx += 1

            current_shard.file_count += len(info['files'])
            current_shard.size_bytes += info['total_size']
            current_shard.metadata['modules'] = current_shard.metadata.get('modules', [])
            current_shard.metadata['modules'].append(module_path)
            current_shard.metadata['extensions'] = list(
                set(current_shard.metadata.get('extensions', [])) | set(info['extensions'])
            )

            for file_path in info['files']:
                current_shard.path = str(Path(file_path).parent)

        if current_shard and current_shard.file_count > 0:
            shards.append(current_shard)

        return shards

    def _create_shard(self, idx: int) -> ShardInfo:
        return ShardInfo(
            shard_id=f"shard_{idx:04d}",
            path="",
            file_count=0,
            chunk_count=0,
            size_bytes=0,
            last_updated=time.time()
        )

    def _should_split(self, shard: ShardInfo, module_info: Dict) -> bool:
        if shard.file_count == 0:
            return False

        if shard.file_count + len(module_info['files']) > self.config.max_files_per_shard:
            return True

        if shard.size_bytes + module_info['total_size'] > self.config.max_shard_size:
            return True

        return False


class ShardManager:
    def __init__(self, storage_path: str = "./data/shards", config: ShardingConfig = None):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.config = config or ShardingConfig()
        self.planner = ShardPlanner(config)

        self.shards: Dict[str, ShardInfo] = {}
        self.file_to_shard: Dict[str, str] = {}
        self._lock = threading.Lock()

        self._load_shard_info()

    def _load_shard_info(self):
        info_path = self.storage_path / "shards.json"
        if info_path.exists():
            try:
                with open(info_path) as f:
                    data = json.load(f)
                for shard_id, shard_data in data.get('shards', {}).items():
                    self.shards[shard_id] = ShardInfo(
                        shard_id=shard_id,
                        path=shard_data.get('path', ''),
                        file_count=shard_data.get('file_count', 0),
                        chunk_count=shard_data.get('chunk_count', 0),
                        size_bytes=shard_data.get('size_bytes', 0),
                        last_updated=shard_data.get('last_updated', 0),
                        metadata=shard_data.get('metadata', {})
                    )
                self.file_to_shard = data.get('file_to_shard', {})
            except Exception:
                pass

    def _save_shard_info(self):
        info_path = self.storage_path / "shards.json"
        data = {
            'shards': {
                shard_id: {
                    'shard_id': info.shard_id,
                    'path': info.path,
                    'file_count': info.file_count,
                    'chunk_count': info.chunk_count,
                    'size_bytes': info.size_bytes,
                    'last_updated': info.last_updated,
                    'metadata': info.metadata
                }
                for shard_id, info in self.shards.items()
            },
            'file_to_shard': self.file_to_shard
        }
        with open(info_path, 'w') as f:
            json.dump(data, f, indent=2)

    def plan_shards(self, root_path: Path) -> List[ShardInfo]:
        return self.planner.plan(root_path)

    def assign_file(self, file_path: str, chunk_count: int = 1, size_bytes: int = 0) -> str:
        with self._lock:
            if file_path in self.file_to_shard:
                return self.file_to_shard[file_path]

            best_shard = self._find_best_shard()
            self.file_to_shard[file_path] = best_shard.shard_id

            best_shard.file_count += 1
            best_shard.chunk_count += chunk_count
            best_shard.size_bytes += size_bytes
            best_shard.last_updated = time.time()

            self._save_shard_info()
            return best_shard.shard_id

    def _find_best_shard(self) -> ShardInfo:
        if not self.shards:
            return self._create_shard()

        for shard in self.shards.values():
            if shard.chunk_count < self.config.max_chunks_per_shard:
                return shard

        return self._create_shard()

    def _create_shard(self) -> ShardInfo:
        idx = len(self.shards)
        shard = ShardInfo(
            shard_id=f"shard_{idx:04d}",
            path=str(self.storage_path / f"shard_{idx:04d}"),
            last_updated=time.time()
        )
        self.shards[shard.shard_id] = shard
        return shard

    def get_shard(self, shard_id: str) -> Optional[ShardInfo]:
        return self.shards.get(shard_id)

    def get_shard_for_file(self, file_path: str) -> Optional[str]:
        return self.file_to_shard.get(file_path)

    def get_all_shards(self) -> List[ShardInfo]:
        return list(self.shards.values())

    def remove_file(self, file_path: str):
        with self._lock:
            if file_path in self.file_to_shard:
                shard_id = self.file_to_shard[file_path]
                if shard_id in self.shards:
                    self.shards[shard_id].file_count = max(0, self.shards[shard_id].file_count - 1)
                del self.file_to_shard[file_path]
                self._save_shard_info()

    def stats(self) -> Dict:
        total_files = sum(s.file_count for s in self.shards.values())
        total_chunks = sum(s.chunk_count for s in self.shards.values())
        total_size = sum(s.size_bytes for s in self.shards.values())

        return {
            'shard_count': len(self.shards),
            'total_files': total_files,
            'total_chunks': total_chunks,
            'total_size_bytes': total_size,
            'shards': [
                {
                    'shard_id': s.shard_id,
                    'file_count': s.file_count,
                    'chunk_count': s.chunk_count,
                    'size_mb': s.size_bytes / (1024 * 1024)
                }
                for s in self.shards.values()
            ]
        }


class DistributedIndexer:
    def __init__(self, shard_manager: ShardManager, embedding_engine, chunker):
        self.shard_manager = shard_manager
        self.embedding_engine = embedding_engine
        self.chunker = chunker

    def index_file(self, file_path: Path) -> Dict:
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            chunks = self.chunker.chunk(content, str(file_path))

            shard_id = self.shard_manager.assign_file(
                str(file_path),
                chunk_count=len(chunks),
                size_bytes=len(content.encode())
            )

            return {
                'file_path': str(file_path),
                'shard_id': shard_id,
                'chunk_count': len(chunks),
                'success': True
            }

        except Exception as e:
            return {
                'file_path': str(file_path),
                'error': str(e),
                'success': False
            }

    def index_directory(self, directory: Path, extensions: Set[str]) -> Dict:
        stats = {
            'files_processed': 0,
            'files_failed': 0,
            'total_chunks': 0,
            'shards_used': set()
        }

        for ext in extensions:
            for file_path in directory.rglob(f'*{ext}'):
                result = self.index_file(file_path)
                if result['success']:
                    stats['files_processed'] += 1
                    stats['total_chunks'] += result['chunk_count']
                    stats['shards_used'].add(result['shard_id'])
                else:
                    stats['files_failed'] += 1

        stats['shards_used'] = list(stats['shards_used'])
        return stats


class ShardQueryExecutor:
    def __init__(self, shard_manager: ShardManager):
        self.shard_manager = shard_manager

    def search(
        self,
        query: str,
        top_k: int = 10,
        shards: List[str] = None
    ) -> List[Dict]:
        target_shards = shards or [s.shard_id for s in self.shard_manager.get_all_shards()]

        all_results = []
        for shard_id in target_shards:
            shard_results = self._search_shard(shard_id, query, top_k)
            all_results.extend(shard_results)

        all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        return all_results[:top_k]

    def _search_shard(self, shard_id: str, query: str, k: int) -> List[Dict]:
        return []

    def search_by_file(self, file_path: str) -> List[Dict]:
        shard_id = self.shard_manager.get_shard_for_file(file_path)
        if not shard_id:
            return []

        return self._search_shard(shard_id, file_path, 100)


class ReplicationManager:
    def __init__(self, shard_manager: ShardManager, replication_factor: int = 2):
        self.shard_manager = shard_manager
        self.replication_factor = replication_factor
        self.replicas: Dict[str, List[str]] = {}

    def create_replicas(self, shard_id: str) -> List[str]:
        if shard_id not in self.replicas:
            self.replicas[shard_id] = []

        replica_ids = []
        for i in range(self.replication_factor - 1):
            replica_id = f"{shard_id}_replica_{i}"
            replica_ids.append(replica_id)
            self.replicas[shard_id].append(replica_id)

        return replica_ids

    def get_replicas(self, shard_id: str) -> List[str]:
        return self.replicas.get(shard_id, [])

    def remove_replicas(self, shard_id: str):
        if shard_id in self.replicas:
            del self.replicas[shard_id]


class LoadBalancer:
    def __init__(self, shard_manager: ShardManager):
        self.shard_manager = shard_manager
        self.query_counts: Dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()

    def get_shard_for_query(self) -> Optional[str]:
        with self._lock:
            shards = self.shard_manager.get_all_shards()
            if not shards:
                return None

            sorted_shards = sorted(shards, key=lambda s: self.query_counts.get(s.shard_id, 0))
            selected = sorted_shards[0].shard_id
            self.query_counts[selected] += 1
            return selected

    def record_query(self, shard_id: str):
        with self._lock:
            self.query_counts[shard_id] += 1

    def get_stats(self) -> Dict:
        with self._lock:
            return dict(self.query_counts)


class ShardingFacade:
    def __init__(
        self,
        storage_path: str = "./data/shards",
        config: ShardingConfig = None
    ):
        self.config = config or ShardingConfig()
        self.shard_manager = ShardManager(storage_path, self.config)
        self.query_executor = ShardQueryExecutor(self.shard_manager)
        self.load_balancer = LoadBalancer(self.shard_manager)
        self.replication_manager = ReplicationManager(self.shard_manager)

    def plan(self, root_path: Path) -> List[ShardInfo]:
        return self.shard_manager.plan_shards(root_path)

    def index_file(self, file_path: Path, chunker, embedding_engine) -> Dict:
        indexer = DistributedIndexer(self.shard_manager, embedding_engine, chunker)
        return indexer.index_file(file_path)

    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        return self.query_executor.search(query, top_k)

    def stats(self) -> Dict:
        return self.shard_manager.stats()

    def get_shard_for_file(self, file_path: str) -> Optional[str]:
        return self.shard_manager.get_shard_for_file(file_path)

    def remove_file(self, file_path: str):
        self.shard_manager.remove_file(file_path)
