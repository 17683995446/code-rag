"""
Code RAG v14.0 - 增量索引与并行处理引擎
支持大规模代码库的快速索引和增量更新
"""

import os
import time
import hashlib
import json
import threading
import multiprocessing
from pathlib import Path
from typing import List, Dict, Set, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed


@dataclass
class IndexEntry:
    """索引条目"""
    file_path: str
    chunk_content: str
    chunk_hash: str
    line_start: int
    line_end: int
    indexed_at: datetime = field(default_factory=datetime.now)


@dataclass
class FileMetadata:
    """文件元数据"""
    file_path: str
    file_hash: str
    last_modified: float
    last_indexed: datetime
    chunk_count: int
    size: int


class IncrementalIndexEngine:
    """
    增量索引引擎
    支持文件变更检测和增量更新
    """

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".code_rag_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.index_state_file = self.cache_dir / "index_state.json"
        self.metadata_file = self.cache_dir / "metadata.json"
        
        self.index_state: Dict[str, str] = {}
        self.file_metadata: Dict[str, FileMetadata] = {}
        
        self._load_state()
        
        self._lock = threading.RLock()
        
        self._stats = {
            'total_files': 0,
            'total_chunks': 0,
            'incremental_updates': 0,
            'cache_hits': 0
        }

    def _load_state(self):
        """加载索引状态"""
        try:
            if self.index_state_file.exists():
                with open(self.index_state_file, 'r') as f:
                    self.index_state = json.load(f)
            
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    metadata_dict = json.load(f)
                    for path, data in metadata_dict.items():
                        self.file_metadata[path] = FileMetadata(**data)
        except Exception as e:
            print(f"  ⚠️ 加载索引状态失败: {e}")
            self.index_state = {}
            self.file_metadata = {}

    def _save_state(self):
        """保存索引状态"""
        try:
            with open(self.index_state_file, 'w') as f:
                json.dump(self.index_state, f)
            
            metadata_dict = {path: {
                'file_path': meta.file_path,
                'file_hash': meta.file_hash,
                'last_modified': meta.last_modified,
                'last_indexed': meta.last_indexed.isoformat(),
                'chunk_count': meta.chunk_count,
                'size': meta.size
            } for path, meta in self.file_metadata.items()}
            
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata_dict, f)
        except Exception as e:
            print(f"  ⚠️ 保存索引状态失败: {e}")

    def calculate_file_hash(self, file_path: str) -> str:
        """计算文件哈希"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return ""

    def needs_reindex(self, file_path: str) -> bool:
        """检查文件是否需要重新索引"""
        if not Path(file_path).exists():
            return False
        
        if file_path not in self.file_metadata:
            return True
        
        current_hash = self.calculate_file_hash(file_path)
        current_modified = os.path.getmtime(file_path)
        
        meta = self.file_metadata[file_path]
        
        return (current_hash != meta.file_hash or 
                current_modified != meta.last_modified)

    def get_changed_files(self, directory: str) -> Dict[str, Set[str]]:
        """
        获取变更的文件
        
        Returns:
            {
                'added': set of new files,
                'modified': set of changed files,
                'deleted': set of removed files
            }
        """
        added = set()
        modified = set()
        deleted = set()
        
        dir_path = Path(directory)
        current_files = set()
        
        for py_file in dir_path.rglob("*.py"):
            if any(skip in str(py_file) for skip in ['__pycache__', '.git', 'venv', 'test']):
                continue
            
            file_path = str(py_file)
            current_files.add(file_path)
            
            if file_path not in self.file_metadata:
                added.add(file_path)
            elif self.needs_reindex(file_path):
                modified.add(file_path)
        
        deleted = set(self.file_metadata.keys()) - current_files
        
        return {
            'added': added,
            'modified': modified,
            'deleted': deleted
        }

    def index_file(self, file_path: str, parser) -> List[IndexEntry]:
        """索引单个文件"""
        try:
            doc = parser.parse_file(file_path)
            
            entries = []
            for chunk in doc.chunks:
                if len(chunk.content) >= 30:
                    chunk_hash = hashlib.md5(chunk.content.encode()).hexdigest()
                    
                    entry = IndexEntry(
                        file_path=file_path,
                        chunk_content=chunk.content,
                        chunk_hash=chunk_hash,
                        line_start=chunk.line_start,
                        line_end=chunk.line_end
                    )
                    entries.append(entry)
            
            file_stat = os.stat(file_path)
            self.file_metadata[file_path] = FileMetadata(
                file_path=file_path,
                file_hash=self.calculate_file_hash(file_path),
                last_modified=file_stat.st_mtime,
                last_indexed=datetime.now(),
                chunk_count=len(entries),
                size=file_stat.st_size
            )
            
            return entries
            
        except Exception as e:
            return []

    def incremental_index(
        self, 
        directory: str, 
        parser,
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """
        增量索引目录
        
        Args:
            directory: 要索引的目录
            parser: 代码解析器
            progress_callback: 进度回调函数
            
        Returns:
            索引结果统计
        """
        print(f"\n🚀 增量索引引擎 v14.0")
        print(f"  目录: {directory}")
        
        start_time = time.time()
        
        changes = self.get_changed_files(directory)
        
        print(f"\n  📊 变更检测:")
        print(f"    新增文件: {len(changes['added'])}")
        print(f"    修改文件: {len(changes['modified'])}")
        print(f"    删除文件: {len(changes['deleted'])}")
        
        all_entries = []
        
        files_to_index = changes['added'] | changes['modified']
        
        if files_to_index:
            print(f"\n  ⏳ 正在索引 {len(files_to_index)} 个文件...")
            
            for i, file_path in enumerate(sorted(files_to_index), 1):
                entries = self.index_file(file_path, parser)
                all_entries.extend(entries)
                
                if progress_callback:
                    progress_callback(i, len(files_to_index), file_path)
                elif i % 10 == 0:
                    print(f"    进度: {i}/{len(files_to_index)}")
            
            self._stats['incremental_updates'] += len(files_to_index)
        
        for file_path in changes['deleted']:
            if file_path in self.file_metadata:
                del self.file_metadata[file_path]
            if file_path in self.index_state:
                del self.index_state[file_path]
        
        self._save_state()
        
        elapsed = time.time() - start_time
        
        result = {
            'success': True,
            'files_added': len(changes['added']),
            'files_modified': len(changes['modified']),
            'files_deleted': len(changes['deleted']),
            'total_entries': len(all_entries),
            'time_seconds': elapsed,
            'status': 'incremental' if (changes['added'] | changes['modified']) else 'up_to_date'
        }
        
        print(f"\n  ✅ 索引完成!")
        print(f"    处理文件: {len(files_to_index)}")
        print(f"    索引条目: {len(all_entries)}")
        print(f"    耗时: {elapsed:.2f}s")
        
        self._stats['total_files'] = len(self.file_metadata)
        self._stats['total_chunks'] = len(all_entries)
        
        return result

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return {
            **self._stats,
            'cached_files': len(self.file_metadata),
            'cache_size_mb': sum(m.size for m in self.file_metadata.values()) / (1024 * 1024)
        }


class ParallelProcessingEngine:
    """
    并行处理引擎
    支持多进程和多线程处理
    """

    def __init__(self, max_workers: Optional[int] = None):
        self.max_workers = max_workers or multiprocessing.cpu_count()
        
        self._process_pool: Optional[ProcessPoolExecutor] = None
        self._thread_pool: Optional[ThreadPoolExecutor] = None

    def parallel_index_files(
        self,
        file_paths: List[str],
        parser_factory: Callable,
        use_processes: bool = True
    ) -> List[Dict]:
        """
        并行索引多个文件
        
        Args:
            file_paths: 文件路径列表
            parser_factory: 解析器工厂函数
            use_processes: 使用进程还是线程
            
        Returns:
            索引结果列表
        """
        print(f"\n⚡ 并行处理引擎")
        print(f"  并行模式: {'多进程' if use_processes else '多线程'}")
        print(f"  工作进程: {self.max_workers}")
        print(f"  处理文件: {len(file_paths)}")
        
        start_time = time.time()
        
        if use_processes:
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(self._index_single_file, fp, parser_factory): fp 
                    for fp in file_paths
                }
                
                results = []
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        file_path = futures[future]
                        results.append({
                            'file_path': file_path,
                            'success': False,
                            'error': str(e)
                        })
        else:
            with ThreadPoolExecutor(max_workers=self.max_workers * 2) as executor:
                futures = {
                    executor.submit(self._index_single_file, fp, parser_factory): fp 
                    for fp in file_paths
                }
                
                results = []
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        file_path = futures[future]
                        results.append({
                            'file_path': file_path,
                            'success': False,
                            'error': str(e)
                        })
        
        elapsed = time.time() - start_time
        
        successful = sum(1 for r in results if r.get('success', False))
        
        print(f"\n  ✅ 并行处理完成!")
        print(f"    成功: {successful}/{len(file_paths)}")
        print(f"    耗时: {elapsed:.2f}s")
        print(f"    速度: {len(file_paths)/elapsed:.1f} 文件/秒")
        
        return results

    @staticmethod
    def _index_single_file(file_path: str, parser_factory: Callable) -> Dict:
        """索引单个文件（静态方法，可被多进程调用）"""
        try:
            parser = parser_factory()
            doc = parser.parse_file(file_path)
            
            chunks = [
                {
                    'content': chunk.content,
                    'line_start': chunk.line_start,
                    'line_end': chunk.line_end,
                    'chunk_type': chunk.chunk_type
                }
                for chunk in doc.chunks
                if len(chunk.content) >= 30
            ]
            
            return {
                'file_path': file_path,
                'success': True,
                'chunks': len(chunks),
                'entries': chunks
            }
        except Exception as e:
            return {
                'file_path': file_path,
                'success': False,
                'error': str(e)
            }


class SmartCacheManager:
    """
    智能缓存管理器
    LRU缓存 + TTL过期 + 预热机制
    """

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        
        self._cache: Dict[str, Dict] = {}
        self._access_order: List[str] = []
        self._lock = threading.RLock()
        
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0
        }

    def get(self, key: str) -> Optional[any]:
        """获取缓存值"""
        with self._lock:
            if key not in self._cache:
                self._stats['misses'] += 1
                return None
            
            entry = self._cache[key]
            
            if time.time() - entry['timestamp'] > self.ttl_seconds:
                del self._cache[key]
                self._access_order.remove(key)
                self._stats['expirations'] += 1
                self._stats['misses'] += 1
                return None
            
            self._access_order.remove(key)
            self._access_order.append(key)
            
            self._stats['hits'] += 1
            return entry['value']

    def set(self, key: str, value: any):
        """设置缓存值"""
        with self._lock:
            if key in self._cache:
                self._access_order.remove(key)
            elif len(self._cache) >= self.max_size:
                oldest = self._access_order.pop(0)
                del self._cache[oldest]
                self._stats['evictions'] += 1
            
            self._cache[key] = {
                'value': value,
                'timestamp': time.time()
            }
            self._access_order.append(key)

    def get_hit_rate(self) -> float:
        """获取缓存命中率"""
        total = self._stats['hits'] + self._stats['misses']
        return self._stats['hits'] / total if total > 0 else 0.0

    def get_statistics(self) -> Dict:
        """获取缓存统计"""
        return {
            **self._stats,
            'size': len(self._cache),
            'max_size': self.max_size,
            'hit_rate': self.get_hit_rate()
        }

    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()


def create_incremental_indexer(cache_dir: Optional[str] = None) -> IncrementalIndexEngine:
    """创建增量索引器"""
    return IncrementalIndexEngine(cache_dir)


def create_parallel_engine(max_workers: Optional[int] = None) -> ParallelProcessingEngine:
    """创建并行处理引擎"""
    return ParallelProcessingEngine(max_workers)


def create_cache_manager(max_size: int = 1000, ttl_seconds: int = 3600) -> SmartCacheManager:
    """创建缓存管理器"""
    return SmartCacheManager(max_size, ttl_seconds)
