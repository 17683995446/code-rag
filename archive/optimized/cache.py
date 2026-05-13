import os
import json
import time
import hashlib
import threading
import pickle
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
import sqlite3


@dataclass
class CacheEntry:
    key: str
    value: Any
    created_at: float
    expires_at: float
    hit_count: int = 0
    last_accessed: float = 0
    size_bytes: int = 0


@dataclass
class CacheConfig:
    max_size: int = 1000
    max_memory_mb: int = 512
    ttl_seconds: int = 3600
    eviction_policy: str = "lru"
    persistence_path: str = "./data/cache"
    enable_compression: bool = False


class LRUCache:
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if time.time() < entry.expires_at:
                    self._cache.move_to_end(key)
                    entry.hit_count += 1
                    entry.last_accessed = time.time()
                    self._hits += 1
                    return entry.value
                else:
                    del self._cache[key]

            self._misses += 1
            return None

    def put(self, key: str, value: Any, ttl_seconds: int = None):
        with self._lock:
            now = time.time()
            ttl = ttl_seconds or 3600

            entry = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                expires_at=now + ttl,
                last_accessed=now,
                size_bytes=self._estimate_size(value)
            )

            if key in self._cache:
                del self._cache[key]

            self._cache[key] = entry

            while len(self._cache) > self.max_size:
                self._cache.popitem(last=False)

    def _estimate_size(self, value: Any) -> int:
        try:
            return len(pickle.dumps(value))
        except Exception:
            return 0

    def delete(self, key: str):
        with self._lock:
            self._cache.pop(key, None)

    def clear(self):
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def stats(self) -> Dict:
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0
            total_size = sum(e.size_bytes for e in self._cache.values())

            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': hit_rate,
                'total_size_bytes': total_size,
                'total_size_mb': total_size / (1024 * 1024)
            }


class LFUCache:
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if time.time() < entry.expires_at:
                    entry.hit_count += 1
                    entry.last_accessed = time.time()
                    self._hits += 1
                    return entry.value
                else:
                    del self._cache[key]

            self._misses += 1
            return None

    def put(self, key: str, value: Any, ttl_seconds: int = None):
        with self._lock:
            now = time.time()
            ttl = ttl_seconds or 3600

            entry = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                expires_at=now + ttl,
                last_accessed=now
            )

            if key in self._cache:
                entry.hit_count = self._cache[key].hit_count
                del self._cache[key]

            self._cache[key] = entry

            while len(self._cache) > self.max_size:
                self._evict_lfu()

    def _evict_lfu(self):
        if not self._cache:
            return

        min_key = min(self._cache.keys(), key=lambda k: self._cache[k].hit_count)
        del self._cache[min_key]

    def delete(self, key: str):
        with self._lock:
            self._cache.pop(key, None)

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


class PersistentCache:
    def __init__(self, storage_path: str = "./data/cache"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._db_path = self.storage_path / "cache.db"
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    created_at REAL,
                    expires_at REAL,
                    hit_count INTEGER DEFAULT 0
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_expires ON cache(expires_at)")
            conn.commit()

    def get(self, key: str) -> Optional[Any]:
        try:
            with sqlite3.connect(self._db_path) as conn:
                cursor = conn.execute(
                    "SELECT value, expires_at FROM cache WHERE key = ?",
                    (key,)
                )
                row = cursor.fetchone()

                if row:
                    value_blob, expires_at = row
                    if time.time() < expires_at:
                        conn.execute(
                            "UPDATE cache SET hit_count = hit_count + 1 WHERE key = ?",
                            (key,)
                        )
                        conn.commit()
                        return pickle.loads(value_blob)
                    else:
                        conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                        conn.commit()

            return None
        except Exception:
            return None

    def put(self, key: str, value: Any, ttl_seconds: int = None):
        try:
            now = time.time()
            ttl = ttl_seconds or 3600
            value_blob = pickle.dumps(value)

            with sqlite3.connect(self._db_path) as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO cache
                       (key, value, created_at, expires_at, hit_count)
                       VALUES (?, ?, ?, ?, 0)""",
                    (key, value_blob, now, now + ttl)
                )
                conn.commit()
        except Exception:
            pass

    def delete(self, key: str):
        try:
            with sqlite3.connect(self._db_path) as conn:
                conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                conn.commit()
        except Exception:
            pass

    def clear(self):
        try:
            with sqlite3.connect(self._db_path) as conn:
                conn.execute("DELETE FROM cache")
                conn.commit()
        except Exception:
            pass

    def cleanup_expired(self):
        try:
            with sqlite3.connect(self._db_path) as conn:
                conn.execute("DELETE FROM cache WHERE expires_at < ?", (time.time(),))
                conn.commit()
        except Exception:
            pass

    def stats(self) -> Dict:
        try:
            with sqlite3.connect(self._db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM cache")
                count = cursor.fetchone()[0]

                cursor = conn.execute("SELECT SUM(LENGTH(value)) FROM cache")
                size = cursor.fetchone()[0] or 0

                return {
                    'size': count,
                    'total_size_bytes': size,
                    'total_size_mb': size / (1024 * 1024)
                }
        except Exception:
            return {'size': 0, 'total_size_bytes': 0, 'total_size_mb': 0}


class QueryCacheManager:
    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()

        if self.config.eviction_policy == "lfu":
            self._memory_cache = LFUCache(self.config.max_size)
        else:
            self._memory_cache = LRUCache(self.config.max_size)

        self._persistent_cache = PersistentCache(self.config.persistence_path)

        self._query_stats: Dict[str, Dict] = {}
        self._lock = threading.Lock()

    def _hash_query(self, query: str, top_k: int, filters: Dict = None) -> str:
        key_data = {
            'query': query.lower().strip(),
            'top_k': top_k,
            'filters': filters or {}
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, query: str, top_k: int = 10, filters: Dict = None) -> Optional[List]:
        key = self._hash_query(query, top_k, filters)

        result = self._memory_cache.get(key)
        if result is not None:
            self._record_hit(query)
            return result

        result = self._persistent_cache.get(key)
        if result is not None:
            self._memory_cache.put(key, result, self.config.ttl_seconds)
            self._record_hit(query)
            return result

        self._record_miss(query)
        return None

    def put(self, query: str, results: List, top_k: int = 10, filters: Dict = None):
        if not results:
            return

        key = self._hash_query(query, top_k, filters)

        self._memory_cache.put(key, results, self.config.ttl_seconds)

        try:
            self._persistent_cache.put(key, results, self.config.ttl_seconds)
        except Exception:
            pass

    def _record_hit(self, query: str):
        with self._lock:
            query_key = query.lower().strip()[:50]
            if query_key not in self._query_stats:
                self._query_stats[query_key] = {'hits': 0, 'misses': 0}
            self._query_stats[query_key]['hits'] += 1

    def _record_miss(self, query: str):
        with self._lock:
            query_key = query.lower().strip()[:50]
            if query_key not in self._query_stats:
                self._query_stats[query_key] = {'hits': 0, 'misses': 0}
            self._query_stats[query_key]['misses'] += 1

    def invalidate(self, query: str = None):
        if query:
            key = self._hash_query(query, 10)
            self._memory_cache.delete(key)
            self._persistent_cache.delete(key)
        else:
            self._memory_cache.clear()
            self._persistent_cache.clear()

    def get_popular_queries(self, limit: int = 10) -> List[Dict]:
        with self._lock:
            sorted_queries = sorted(
                self._query_stats.items(),
                key=lambda x: x[1]['hits'],
                reverse=True
            )

            return [
                {
                    'query': q,
                    'hits': stats['hits'],
                    'misses': stats['misses'],
                    'hit_rate': stats['hits'] / (stats['hits'] + stats['misses'])
                    if stats['hits'] + stats['misses'] > 0 else 0
                }
                for q, stats in sorted_queries[:limit]
            ]

    def stats(self) -> Dict:
        memory_stats = self._memory_cache.stats()
        persistent_stats = self._persistent_cache.stats()

        return {
            'memory_cache': memory_stats,
            'persistent_cache': persistent_stats,
            'query_stats_count': len(self._query_stats)
        }


class CacheWarmer:
    def __init__(self, cache_manager: QueryCacheManager, indexer):
        self.cache_manager = cache_manager
        self.indexer = indexer
        self._warmup_queries: List[str] = []
        self._executor = ThreadPoolExecutor(max_workers=2)

    def add_warmup_query(self, query: str):
        if query not in self._warmup_queries:
            self._warmup_queries.append(query)

    def add_warmup_queries(self, queries: List[str]):
        for query in queries:
            self.add_warmup_query(query)

    def warmup(self, queries: List[str] = None) -> Dict:
        target_queries = queries or self._warmup_queries

        stats = {
            'total_queries': len(target_queries),
            'successful': 0,
            'failed': 0,
            'time_seconds': 0
        }

        start_time = time.time()

        for query in target_queries:
            try:
                cached = self.cache_manager.get(query)
                if cached is None:
                    results = self.indexer.search(query, top_k=10)
                    if results:
                        self.cache_manager.put(query, results)
                stats['successful'] += 1
            except Exception:
                stats['failed'] += 1

        stats['time_seconds'] = time.time() - start_time
        return stats

    def warmup_async(self, queries: List[str] = None) -> threading.Thread:
        def _warmup():
            self.warmup(queries)

        thread = threading.Thread(target=_warmup, daemon=True)
        thread.start()
        return thread

    def schedule_warmup(self, interval_seconds: int = 3600):
        def _periodic_warmup():
            while True:
                time.sleep(interval_seconds)
                self.warmup()

        thread = threading.Thread(target=_periodic_warmup, daemon=True)
        thread.start()
        return thread


class CachePrefetcher:
    def __init__(self, cache_manager: QueryCacheManager):
        self.cache_manager = cache_manager
        self._prefetch_rules: List[Dict] = []

    def add_rule(self, trigger_query: str, prefetch_queries: List[str]):
        self._prefetch_rules.append({
            'trigger': trigger_query.lower().strip(),
            'prefetch': prefetch_queries
        })

    def on_query(self, query: str) -> List[str]:
        query_lower = query.lower().strip()
        to_prefetch = []

        for rule in self._prefetch_rules:
            if rule['trigger'] in query_lower or query_lower in rule['trigger']:
                to_prefetch.extend(rule['prefetch'])

        return list(set(to_prefetch))

    def get_related_queries(self, query: str) -> List[str]:
        words = query.lower().split()

        related = []
        for word in words:
            if len(word) > 3:
                related.append(word)
                related.append(f"def {word}")
                related.append(f"class {word}")

        return related


class CacheInvalidator:
    def __init__(self, cache_manager: QueryCacheManager):
        self.cache_manager = cache_manager
        self._file_patterns: Dict[str, List[str]] = {}

    def register_file_pattern(self, pattern: str, affected_queries: List[str]):
        self._file_patterns[pattern] = affected_queries

    def on_file_change(self, file_path: str):
        import fnmatch

        queries_to_invalidate = set()

        for pattern, queries in self._file_patterns.items():
            if fnmatch.fnmatch(file_path, pattern):
                queries_to_invalidate.update(queries)

        for query in queries_to_invalidate:
            self.cache_manager.invalidate(query)

    def on_index_rebuild(self):
        self.cache_manager.invalidate()


class CacheFacade:
    def __init__(self, config: CacheConfig = None, indexer=None):
        self.config = config or CacheConfig()
        self.cache_manager = QueryCacheManager(self.config)
        self.warmer = CacheWarmer(self.cache_manager, indexer) if indexer else None
        self.prefetcher = CachePrefetcher(self.cache_manager)
        self.invalidator = CacheInvalidator(self.cache_manager)

    def get(self, query: str, top_k: int = 10, filters: Dict = None) -> Optional[List]:
        return self.cache_manager.get(query, top_k, filters)

    def put(self, query: str, results: List, top_k: int = 10, filters: Dict = None):
        self.cache_manager.put(query, results, top_k, filters)

    def warmup(self, queries: List[str] = None) -> Dict:
        if self.warmer:
            return self.warmer.warmup(queries)
        return {'error': 'Warmer not initialized'}

    def invalidate(self, query: str = None):
        self.cache_manager.invalidate(query)

    def on_file_change(self, file_path: str):
        self.invalidator.on_file_change(file_path)

    def stats(self) -> Dict:
        return self.cache_manager.stats()

    def get_popular_queries(self, limit: int = 10) -> List[Dict]:
        return self.cache_manager.get_popular_queries(limit)
