import os
import time
import hashlib
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Iterator
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import threading


@dataclass
class EmbeddingConfig:
    model_name: str = "all-MiniLM-L6-v2"
    dimension: int = 384
    device: str = "cpu"
    batch_size: int = 32
    max_length: int = 512
    normalize: bool = True


class EmbeddingEngine:
    def __init__(self, config: EmbeddingConfig = None):
        self.config = config or EmbeddingConfig()
        self.model = None
        self._use_transformers = False
        self._lock = threading.Lock()

    def _load_model(self):
        if self.model is not None:
            return

        with self._lock:
            if self.model is not None:
                return

            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(
                    self.config.model_name,
                    device=self.config.device
                )
                self._use_transformers = True
            except ImportError:
                self.model = self._create_fallback_embedder()
                self._use_transformers = False

    def _create_fallback_embedder(self):
        keywords = [
            'function', 'class', 'def', 'return', 'if', 'else', 'for', 'while',
            'import', 'export', 'const', 'let', 'var', 'async', 'await', 'try',
            'catch', 'throw', 'new', 'this', 'self', 'public', 'private',
            'static', 'void', 'int', 'string', 'bool', 'float', 'list', 'dict',
            'map', 'set', 'array', 'object', 'interface', 'type', 'enum', 'struct',
            'fn', 'impl', 'trait', 'pub', 'mod', 'use', 'match', 'loop',
            'init', 'setup', 'run', 'execute', 'start', 'stop', 'load', 'save',
            'http', 'api', 'request', 'response', 'json', 'xml', 'sql', 'db',
            'auth', 'login', 'token', 'jwt', 'config', 'error', 'log', 'test',
            'model', 'service', 'controller', 'repository', 'handler', 'middleware',
            'parse', 'validate', 'format', 'transform', 'convert', 'encode', 'decode',
            'cache', 'redis', 'queue', 'message', 'event', 'stream', 'batch',
        ]
        return {'keywords': {w: i % self.config.dimension for i, w in enumerate(keywords)}}

    def encode(self, texts: List[str], show_progress: bool = True) -> np.ndarray:
        self._load_model()

        if self._use_transformers:
            return self._encode_transformers(texts, show_progress)
        else:
            return self._encode_fallback(texts)

    def _encode_transformers(self, texts: List[str], show_progress: bool) -> np.ndarray:
        embeddings = self.model.encode(
            texts,
            batch_size=self.config.batch_size,
            show_progress_bar=show_progress,
            normalize_embeddings=self.config.normalize,
            convert_to_numpy=True
        )
        return embeddings.astype(np.float32)

    def _encode_fallback(self, texts: List[str]) -> np.ndarray:
        keywords = self.model['keywords']
        dim = self.config.dimension
        vectors = np.zeros((len(texts), dim), dtype=np.float32)

        for i, text in enumerate(texts):
            text_lower = text.lower()
            for word, idx in keywords.items():
                if word in text_lower:
                    vectors[i, idx] += 1

            tokens = text.split()
            for j, token in enumerate(tokens[:20]):
                if len(token) > 3:
                    hash_val = int(hashlib.md5(token.encode()).hexdigest()[:4], 16)
                    vectors[i, hash_val % dim] += 1

        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1
        vectors = vectors / norms

        return vectors

    def encode_one(self, text: str) -> np.ndarray:
        return self.encode([text], show_progress=False)[0]


class VectorIndex:
    def __init__(
        self,
        dimension: int = 384,
        index_type: str = "FlatIP",
        metric: str = "ip"
    ):
        self.dimension = dimension
        self.index_type = index_type
        self.metric = metric
        self.index = None
        self.vectors = []
        self.use_faiss = False
        self._init_index()

    def _init_index(self):
        try:
            import faiss
            self.faiss = faiss
            self.use_faiss = True
            self._build_faiss_index()
        except ImportError:
            self.faiss = None
            self.use_faiss = False

    def _build_faiss_index(self):
        if not self.use_faiss:
            return

        if self.index_type == "FlatIP":
            self.index = self.faiss.IndexFlatIP(self.dimension)
        elif self.index_type == "FlatL2":
            self.index = self.faiss.IndexFlatL2(self.dimension)
        elif self.index_type == "IVF":
            quantizer = self.faiss.IndexFlatIP(self.dimension)
            self.index = self.faiss.IndexIVFFlat(
                quantizer, self.dimension, 100
            )
        elif self.index_type == "IVF-PQ":
            quantizer = self.faiss.IndexFlatIP(self.dimension)
            self.index = self.faiss.IndexIVFPQ(
                quantizer, self.dimension, 16, 8
            )
        else:
            self.index = self.faiss.IndexFlatIP(self.dimension)

    def add(self, vectors: np.ndarray):
        vectors = np.asarray(vectors, dtype=np.float32)
        if vectors.ndim == 1:
            vectors = vectors.reshape(1, -1)

        if self.use_faiss:
            if hasattr(self.index, 'is_trained') and not self.index.is_trained:
                self.index.train(vectors)
            self.index.add(vectors)
        else:
            self.vectors.extend(vectors.tolist())

    def search(self, query: np.ndarray, top_k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        query = np.asarray(query, dtype=np.float32)
        if query.ndim == 1:
            query = query.reshape(1, -1)

        if self.use_faiss:
            return self.index.search(query, top_k)
        else:
            scores = np.array([
                np.dot(query[0], v) for v in self.vectors
            ], dtype=np.float32)
            top_k = min(top_k, len(scores))
            top_indices = np.argsort(scores)[::-1][:top_k]
            return top_indices.astype(np.int64), scores[top_indices].astype(np.float32)

    def save(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        if self.use_faiss:
            self.faiss.write_index(self.index, path)
        else:
            np.save(path, np.array(self.vectors))

    def load(self, path: str):
        if self.use_faiss:
            self.index = self.faiss.read_index(path)
        else:
            self.vectors = np.load(path, allow_pickle=True).tolist()

    def get_memory_usage(self) -> int:
        if self.use_faiss:
            return self.index.ntotal * self.dimension * 4
        return len(self.vectors) * self.dimension * 4 if self.vectors else 0


@dataclass
class ChunkMetadata:
    chunk_id: str
    content: str
    file_path: str
    language: str
    start_line: int
    end_line: int
    chunk_type: str
    symbols: List[Dict] = field(default_factory=list)
    docstring: str = ""
    imports: List[str] = field(default_factory=list)
    embedding_hash: str = ""


class ChunkCache:
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self._cache: Dict[str, np.ndarray] = {}
        self._access_order: List[str] = []
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[np.ndarray]:
        with self._lock:
            if key in self._cache:
                self._access_order.remove(key)
                self._access_order.append(key)
                return self._cache[key]
        return None

    def put(self, key: str, value: np.ndarray):
        with self._lock:
            if key in self._cache:
                self._access_order.remove(key)
            elif len(self._cache) >= self.max_size:
                oldest = self._access_order.pop(0)
                del self._cache[oldest]

            self._cache[key] = value
            self._access_order.append(key)

    def clear(self):
        with self._lock:
            self._cache.clear()
            self._access_order.clear()


class OptimizedIndexer:
    def __init__(
        self,
        embedding_engine: EmbeddingEngine = None,
        vector_index: VectorIndex = None,
        config: Dict = None
    ):
        self.config = config or {}
        self.embedding_engine = embedding_engine or EmbeddingEngine()
        self.vector_index = vector_index or VectorIndex(
            dimension=self.embedding_engine.config.dimension
        )
        self.metadata: List[ChunkMetadata] = []
        self.chunk_cache = ChunkCache()

    def build_index(
        self,
        chunks: List[Dict],
        show_progress: bool = True,
        batch_size: int = 32
    ) -> int:
        self.metadata = []

        texts = []
        for chunk in chunks:
            meta = ChunkMetadata(
                chunk_id=chunk.get('chunk_id', ''),
                content=chunk.get('content', ''),
                file_path=chunk.get('file_path', ''),
                language=chunk.get('language', 'unknown'),
                start_line=chunk.get('start_line', 0),
                end_line=chunk.get('end_line', 0),
                chunk_type=chunk.get('chunk_type', 'unknown'),
                symbols=chunk.get('symbols', []),
                docstring=chunk.get('docstring', ''),
                imports=chunk.get('imports', [])
            )
            meta.embedding_hash = hashlib.md5(
                meta.content.encode()
            ).hexdigest()[:16]
            self.metadata.append(meta)
            texts.append(meta.content)

        embeddings = self.embedding_engine.encode(texts, show_progress)
        self.vector_index.add(embeddings)

        return len(chunks)

    def search(
        self,
        query: str,
        top_k: int = 10,
        filter_func=None
    ) -> List[Dict]:
        query_vec = self.embedding_engine.encode_one(query)
        indices, scores = self.vector_index.search(query_vec, top_k * 2)

        results = []
        for idx, score in zip(indices, scores):
            if idx < 0 or idx >= len(self.metadata):
                continue

            meta = self.metadata[idx]
            if filter_func and not filter_func(meta):
                continue

            results.append({
                'chunk_id': meta.chunk_id,
                'content': meta.content,
                'file_path': meta.file_path,
                'language': meta.language,
                'start_line': meta.start_line,
                'end_line': meta.end_line,
                'chunk_type': meta.chunk_type,
                'symbols': meta.symbols,
                'score': float(score)
            })

            if len(results) >= top_k:
                break

        return results

    def save(self, index_path: str, metadata_path: str):
        self.vector_index.save(index_path)

        import json
        data = [
            {
                'chunk_id': m.chunk_id,
                'content': m.content,
                'file_path': m.file_path,
                'language': m.language,
                'start_line': m.start_line,
                'end_line': m.end_line,
                'chunk_type': m.chunk_type,
                'symbols': m.symbols,
                'docstring': m.docstring,
                'imports': m.imports
            }
            for m in self.metadata
        ]
        Path(metadata_path).parent.mkdir(parents=True, exist_ok=True)
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, index_path: str, metadata_path: str):
        self.vector_index.load(index_path)

        import json
        with open(metadata_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.metadata = [
            ChunkMetadata(**item) for item in data
        ]
