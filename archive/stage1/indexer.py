import hashlib
import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import asdict
import numpy as np


class Tokenizer:
    def __init__(self):
        self.code_keywords = {
            'python': {'def', 'class', 'if', 'else', 'elif', 'for', 'while', 'return',
                      'import', 'from', 'as', 'try', 'except', 'finally', 'with', 'lambda',
                      'yield', 'raise', 'pass', 'break', 'continue', 'async', 'await', 'self'},
            'javascript': {'function', 'const', 'let', 'var', 'if', 'else', 'for', 'while',
                         'return', 'import', 'export', 'class', 'extends', 'new', 'this',
                         'async', 'await', 'try', 'catch', 'throw', 'finally'},
            'typescript': {'function', 'const', 'let', 'var', 'interface', 'type', 'enum',
                         'implements', 'extends', 'public', 'private', 'protected', 'readonly'},
            'java': {'public', 'private', 'protected', 'class', 'interface', 'extends',
                    'implements', 'static', 'final', 'void', 'int', 'String', 'boolean',
                    'if', 'else', 'for', 'while', 'return', 'try', 'catch', 'throw'},
            'go': {'func', 'type', 'struct', 'interface', 'package', 'import', 'return',
                  'if', 'else', 'for', 'range', 'switch', 'case', 'default', 'defer', 'go'},
            'rust': {'fn', 'let', 'mut', 'const', 'struct', 'enum', 'impl', 'trait',
                    'pub', 'mod', 'use', 'self', 'Self', 'if', 'else', 'match', 'loop',
                    'return', 'async', 'await', 'impl', 'where'},
        }
        self.common_keywords = {
            'function', 'class', 'method', 'variable', 'constant', 'interface', 'type',
            'return', 'parameter', 'callback', 'handler', 'service', 'controller',
            'model', 'data', 'config', 'options', 'error', 'result', 'success', 'failure',
            'init', 'setup', 'create', 'update', 'delete', 'remove', 'add', 'get', 'set',
            'list', 'fetch', 'load', 'save', 'build', 'parse', 'validate', 'check', 'exists'
        }

    def tokenize(self, text: str) -> List[str]:
        tokens = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', text.lower())
        return tokens

    def extract_features(self, text: str, language: str = 'python') -> Dict[str, Any]:
        tokens = self.tokenize(text)
        lang_keywords = self.code_keywords.get(language, set())
        common_keywords = self.common_keywords

        feature_counts = {}
        for token in tokens:
            if token in lang_keywords or token in common_keywords or len(token) > 3:
                feature_counts[token] = feature_counts.get(token, 0) + 1

        return {
            'token_count': len(tokens),
            'unique_tokens': len(set(tokens)),
            'keyword_count': sum(1 for t in tokens if t in lang_keywords),
            'features': feature_counts,
            'length': len(text),
            'line_count': text.count('\n') + 1
        }


class SimpleEmbeddingEngine:
    def __init__(self, dim: int = 128):
        self.dim = dim
        self.vocab = self._build_vocab()
        self.tokenizer = Tokenizer()

    def _build_vocab(self) -> Dict[str, int]:
        keywords = [
            'function', 'class', 'def', 'return', 'if', 'else', 'for', 'while',
            'import', 'export', 'const', 'let', 'var', 'async', 'await', 'try',
            'catch', 'throw', 'new', 'this', 'self', 'public', 'private',
            'static', 'void', 'int', 'string', 'bool', 'float', 'list', 'dict',
            'map', 'set', 'array', 'object', 'interface', 'type', 'enum', 'struct',
            'fn', 'mut', 'impl', 'trait', 'pub', 'mod', 'use', 'crate', 'match',
            'loop', 'break', 'continue', 'yield', 'lambda', 'with', 'from', 'as',
            'in', 'out', 'ref', 'where', 'extends', 'implements', 'abstract',
            'virtual', 'override', 'final', 'case', 'switch', 'default', 'do',
            'null', 'none', 'nil', 'true', 'false', 'undefined', 'void', 'any',
            'db', 'query', 'select', 'insert', 'update', 'delete', 'create', 'drop',
            'table', 'index', 'view', 'join', 'inner', 'outer', 'left', 'right',
            'http', 'request', 'response', 'api', 'url', 'path', 'header', 'body',
            'json', 'xml', 'html', 'css', 'sql', 'redis', 'cache', 'session',
            'auth', 'login', 'logout', 'token', 'jwt', 'oauth', 'password', 'encrypt',
            'decrypt', 'hash', 'sign', 'verify', 'config', 'env', 'var', 'args',
            'error', 'exception', 'log', 'debug', 'info', 'warn', 'fatal', 'trace',
            'test', 'mock', 'assert', 'expect', 'describe', 'it', 'before', 'after',
            'init', 'setup', 'teardown', 'cleanup', 'run', 'execute', 'start', 'stop',
            'load', 'save', 'read', 'write', 'open', 'close', 'connect', 'disconnect',
            'send', 'receive', 'publish', 'subscribe', 'push', 'pull', 'get', 'post',
            'put', 'patch', 'head', 'options', 'trace', 'connect', 'method',
            'route', 'handler', 'middleware', 'controller', 'service', 'repository',
            'model', 'entity', 'dto', 'vo', 'dao', 'mapper', 'converter', 'factory',
            'singleton', 'builder', 'prototype', 'observer', 'strategy', 'adapter',
            'bridge', 'composite', 'decorator', 'facade', 'flyweight', 'proxy', 'chain',
            'command', 'iterator', 'mediator', 'memento', 'state', 'template', 'visitor',
            'parse', 'format', 'validate', 'sanitize', 'transform', 'convert', 'encode', 'decode',
            'render', 'draw', 'paint', 'update', 'refresh', 'invalidate', 'dispose', 'release'
        ]
        vocab = {word: i % self.dim for i, word in enumerate(keywords)}
        return vocab

    def encode(self, texts: List[str], languages: List[str] = None) -> np.ndarray:
        vectors = np.zeros((len(texts), self.dim), dtype=np.float32)

        for i, text in enumerate(texts):
            text_lower = text.lower()

            for word, idx in self.vocab.items():
                if word in text_lower:
                    vectors[i, idx] += 1

            ngrams = self._extract_ngrams(text_lower, 2)
            for ngram_str, idx in ngrams.items():
                if idx < self.dim:
                    vectors[i, idx] += 0.5

            numbers = [int(n) for n in text.split() if n.isdigit()][:10]
            for j, num in enumerate(numbers):
                vectors[i, j % min(self.dim, 50)] += (num % 100) / 100.0

            norm = np.linalg.norm(vectors[i])
            if norm > 0:
                vectors[i] /= norm

        return vectors

    def _extract_ngrams(self, text: str, n: int = 2) -> Dict[str, int]:
        words = text.split()
        ngrams = {}
        for i in range(len(words) - n + 1):
            ngram = ' '.join(words[i:i+n])
            if len(ngram) <= 20:
                hash_val = int(hashlib.md5(ngram.encode()).hexdigest()[:8], 16)
                ngrams[ngram] = hash_val % self.dim
        return ngrams

    def encode_one(self, text: str, language: str = 'python') -> np.ndarray:
        return self.encode([text], [language])[0]

    def get_dimension(self) -> int:
        return self.dim


class BM25Index:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus: List[str] = []
        self.term_freqs: List[Dict[str, int]] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_length: float = 0
        self.idf: Dict[str, float] = {}

    def build(self, chunks: List[Any]):
        self.corpus = [chunk.content for chunk in chunks]
        self.term_freqs = []
        self.doc_lengths = []

        for text in self.corpus:
            tokens = self._tokenize(text)
            tf = {}
            for token in tokens:
                tf[token] = tf.get(token, 0) + 1
            self.term_freqs.append(tf)
            self.doc_lengths.append(len(tokens))

        self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths) if self.doc_lengths else 1

        doc_freq = {}
        for tf in self.term_freqs:
            for token in tf:
                doc_freq[token] = doc_freq.get(token, 0) + 1

        N = len(self.corpus)
        for token, df in doc_freq.items():
            self.idf[token] = np.log((N - df + 0.5) / (df + 0.5) + 1)

    def _tokenize(self, text: str) -> List[str]:
        tokens = re.findall(r'[a-z0-9]{2,}', text.lower())
        return tokens

    def search(self, query: str, top_k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        query_tokens = self._tokenize(query)
        scores = np.zeros(len(self.corpus), dtype=np.float32)

        for i, tf in enumerate(self.term_freqs):
            score = 0
            doc_len = self.doc_lengths[i]
            for token in query_tokens:
                if token in tf:
                    tf_val = tf[token]
                    idf = self.idf.get(token, 0)
                    numerator = tf_val * (self.k1 + 1)
                    denominator = tf_val + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_length)
                    score += idf * numerator / denominator if denominator > 0 else 0
            scores[i] = score

        top_indices = np.argsort(scores)[::-1][:top_k]
        return top_indices.astype(np.int64), scores[top_indices].astype(np.float32)


class VectorIndex:
    def __init__(self, dimension: int, index_type: str = "FlatIP", embedding_engine=None):
        self.dimension = dimension
        self.index_type = index_type
        self.vectors: List[np.ndarray] = []
        self.use_faiss = False
        self.faiss = None
        self.index = None
        self.embedding_engine = embedding_engine

        try:
            import faiss
            self.faiss = faiss
            self.use_faiss = True
            self._build_faiss_index()
        except ImportError:
            pass

    def _build_faiss_index(self):
        if self.use_faiss:
            if self.index_type == "FlatIP":
                self.index = self.faiss.IndexFlatIP(self.dimension)
            elif self.index_type == "FlatL2":
                self.index = self.faiss.IndexFlatL2(self.dimension)
            elif self.index_type == "IVF":
                quantizer = self.faiss.IndexFlatIP(self.dimension)
                self.index = self.faiss.IndexIVFFlat(quantizer, self.dimension, 100)
            else:
                self.index = self.faiss.IndexFlatIP(self.dimension)

    def add(self, vectors: np.ndarray):
        if self.use_faiss:
            self.index.add(vectors.astype(np.float32))
        else:
            self.vectors.extend(vectors.tolist())

    def train(self, vectors: np.ndarray):
        if self.use_faiss and hasattr(self.index, 'train') and not self.index.is_trained:
            self.index.train(vectors.astype(np.float32))

    def search(self, query: np.ndarray, top_k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        if self.use_faiss:
            return self.index.search(query.reshape(1, -1).astype(np.float32), top_k)
        else:
            scores = np.array([np.dot(query, v) for v in self.vectors], dtype=np.float32)
            top_indices = np.argsort(scores)[::-1][:top_k]
            return top_indices.astype(np.int64), scores[top_indices].astype(np.float32)

    def save(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        if self.use_faiss:
            self.faiss.write_index(self.index, path)
        else:
            np.save(path, np.array(self.vectors))

    def load(self, path: str):
        path_obj = Path(path)
        if path_obj.suffix == '.pkl':
            import pickle
            with open(path, 'rb') as f:
                self.vectors = pickle.load(f)
        elif self.use_faiss:
            self.index = self.faiss.read_index(path)
        else:
            try:
                self.vectors = np.load(path, allow_pickle=True).tolist()
            except Exception:
                import pickle
                with open(path, 'rb') as f:
                    self.vectors = pickle.load(f)


class HybridSearchEngine:
    def __init__(
        self,
        vector_index: VectorIndex,
        bm25_index: BM25Index,
        metadata: List[Dict],
        top_k: int = 10,
        hybrid_alpha: float = 0.7
    ):
        self.vector_index = vector_index
        self.bm25_index = bm25_index
        self.metadata = metadata
        self.top_k = top_k
        self.hybrid_alpha = hybrid_alpha

    def search(self, query: str, top_k: int = None, filter_fn=None) -> List[Dict]:
        top_k = top_k or self.top_k

        query_vec = self.vector_index.embedding_engine.encode_one(query)
        vec_indices, vec_scores = self.vector_index.search(query_vec, top_k * 3)
        bm25_indices, bm25_scores = self.bm25_index.search(query, top_k * 3)

        vec_scores = np.clip(vec_scores, 0, None)
        bm25_scores = np.clip(bm25_scores, 0, None)

        vec_scores_norm = self._normalize(vec_scores)
        bm25_scores_norm = self._normalize(bm25_scores)

        combined: Dict[int, float] = {}

        vec_list = vec_indices.tolist() if hasattr(vec_indices, 'tolist') else list(vec_indices)
        for idx, score in zip(vec_list, vec_scores_norm.tolist()):
            if isinstance(idx, (int, np.integer)) and idx >= 0:
                combined[int(idx)] = combined.get(int(idx), 0) + self.hybrid_alpha * score

        bm25_list = bm25_indices.tolist() if hasattr(bm25_indices, 'tolist') else list(bm25_indices)
        for idx, score in zip(bm25_list, bm25_scores_norm.tolist()):
            if isinstance(idx, (int, np.integer)) and idx >= 0:
                combined[int(idx)] = combined.get(int(idx), 0) + (1 - self.hybrid_alpha) * score

        ranked = sorted(combined.items(), key=lambda x: x[1], reverse=True)[:top_k]

        results = []
        for idx, score in ranked:
            if idx < len(self.metadata):
                result = self.metadata[idx].copy()
                result['score'] = float(score)
                if filter_fn is None or filter_fn(result):
                    results.append(result)

        return results

    def _normalize(self, scores: np.ndarray) -> np.ndarray:
        if len(scores) == 0:
            return scores
        min_s, max_s = scores.min(), scores.max()
        if max_s - min_s > 1e-6:
            return (scores - min_s) / (max_s - min_s)
        return np.ones_like(scores) if len(scores) > 0 else scores


class CodeIndexer:
    def __init__(
        self,
        embedding_engine: SimpleEmbeddingEngine = None,
        vector_index: VectorIndex = None,
        bm25_index: BM25Index = None,
        embedding_dim: int = 128,
        vector_index_type: str = "FlatIP"
    ):
        self.embedding_engine = embedding_engine or SimpleEmbeddingEngine(dim=embedding_dim)
        self.vector_index = vector_index or VectorIndex(embedding_dim, vector_index_type, self.embedding_engine)
        self.bm25_index = bm25_index or BM25Index()
        self.chunks = []
        self.metadata: List[Dict] = []
        self.embedding_dim = embedding_dim

    def build(self, chunks: List[Any], show_progress: bool = True):
        try:
            from tqdm import tqdm
            has_tqdm = True
        except ImportError:
            has_tqdm = False

        self.chunks = chunks
        self.metadata = [chunk.to_dict() if hasattr(chunk, 'to_dict') else chunk for chunk in chunks]
        texts = [chunk.content if hasattr(chunk, 'content') else str(chunk) for chunk in chunks]

        if show_progress:
            print(f"Building BM25 index for {len(chunks)} chunks...")
        self.bm25_index.build(chunks)

        if show_progress:
            print(f"Generating embeddings for {len(chunks)} chunks...")
        embeddings = self.embedding_engine.encode(texts)

        if show_progress:
            print(f"Building vector index...")
        if hasattr(self.vector_index, 'index') and self.vector_index.index and hasattr(self.vector_index.index, 'train') and not self.vector_index.index.is_trained:
            self.vector_index.train(embeddings)
        self.vector_index.add(embeddings)

        if show_progress:
            print(f"Indexing complete! Total chunks: {len(chunks)}")

    def save(self, index_path: str, metadata_path: str, bm25_path: str):
        self.vector_index.save(index_path)

        Path(metadata_path).parent.mkdir(parents=True, exist_ok=True)
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

        bm25_data = {
            'corpus': self.bm25_index.corpus,
            'doc_lengths': self.bm25_index.doc_lengths,
            'avg_doc_length': self.bm25_index.avg_doc_length,
            'idf': self.bm25_index.idf
        }
        Path(bm25_path).parent.mkdir(parents=True, exist_ok=True)
        with open(bm25_path, 'w', encoding='utf-8') as f:
            json.dump(bm25_data, f, ensure_ascii=False, indent=2)

    def load(self, index_path: str, metadata_path: str, bm25_path: str):
        self.vector_index.load(index_path)

        with open(metadata_path, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)

        with open(bm25_path, 'r', encoding='utf-8') as f:
            bm25_data = json.load(f)
            self.bm25_index.corpus = bm25_data.get('corpus', [])
            self.bm25_index.doc_lengths = bm25_data.get('doc_lengths', [])
            self.bm25_index.avg_doc_length = bm25_data.get('avg_doc_length', 1)
            self.bm25_index.idf = bm25_data.get('idf', {})

            if not self.bm25_index.term_freqs:
                self.bm25_index.term_freqs = []
                for text in self.bm25_index.corpus:
                    tokens = re.findall(r'[a-z0-9]{2,}', text.lower())
                    tf = {}
                    for token in tokens:
                        tf[token] = tf.get(token, 0) + 1
                    self.bm25_index.term_freqs.append(tf)
