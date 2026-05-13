import json
import hashlib
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from tqdm import tqdm

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False

from parser import CodeChunk


class SimpleEmbedder:
    def __init__(self, dim: int = 128):
        self.dim = dim
        self.vocab = self._build_vocab()

    def _build_vocab(self) -> Dict[str, int]:
        keywords = [
            'function', 'class', 'def', 'return', 'if', 'else', 'for', 'while',
            'import', 'export', 'const', 'let', 'var', 'async', 'await', 'try',
            'except', 'catch', 'throw', 'new', 'this', 'self', 'public', 'private',
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
            'put', 'patch', 'delete', 'head', 'options', 'trace', 'connect', 'method',
            'route', 'handler', 'middleware', 'controller', 'service', 'repository',
            'model', 'entity', 'dto', 'vo', 'dao', 'mapper', 'converter', 'factory',
            'singleton', 'builder', 'prototype', 'observer', 'strategy', 'adapter',
            'bridge', 'composite', 'decorator', 'facade', 'flyweight', 'proxy', 'chain',
            'command', 'iterator', 'mediator', 'memento', 'state', 'template', 'visitor'
        ]
        vocab = {word: i % self.dim for i, word in enumerate(keywords)}
        return vocab

    def encode(self, texts: List[str]) -> np.ndarray:
        vectors = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i, text in enumerate(tqdm(texts, desc="Encoding")):
            text_lower = text.lower()
            for word, idx in self.vocab.items():
                if word in text_lower:
                    vectors[i, idx] += 1
            norm = np.linalg.norm(vectors[i])
            if norm > 0:
                vectors[i] /= norm
        return vectors

    def encode_one(self, text: str) -> np.ndarray:
        return self.encode([text])[0]


class BM25Fallback:
    def __init__(self):
        self.corpus: List[str] = []
        self.term_freqs: List[Dict[str, int]] = []

    def build(self, chunks: List[CodeChunk]):
        self.corpus = [chunk.content for chunk in chunks]
        self.term_freqs = []
        for text in tqdm(self.corpus, desc="Building BM25"):
            words = self._tokenize(text)
            tf = {}
            for w in words:
                tf[w] = tf.get(w, 0) + 1
            self.term_freqs.append(tf)

    def _tokenize(self, text: str) -> List[str]:
        import re
        text = text.lower()
        tokens = re.findall(r'[a-z0-9]+', text)
        return tokens

    def search(self, query: str, top_k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        query_words = self._tokenize(query)
        scores = np.zeros(len(self.corpus), dtype=np.float32)

        avg_tf = sum(sum(tf.values()) for tf in self.term_freqs) / len(self.term_freqs) if self.term_freqs else 1
        idf = {}

        for word in query_words:
            doc_count = sum(1 for tf in self.term_freqs if word in tf)
            idf[word] = np.log((len(self.corpus) - doc_count + 0.5) / (doc_count + 0.5) + 1)

        for i, tf in enumerate(self.term_freqs):
            score = 0
            for word in query_words:
                if word in tf:
                    tf_val = tf[word]
                    k1, b = 1.5, 0.75
                    score += idf.get(word, 0) * (tf_val * (k1 + 1)) / (tf_val + k1 * (1 - b + b * sum(tf.values()) / avg_tf))
            scores[i] = score

        top_indices = np.argsort(scores)[::-1][:top_k]
        return top_indices.astype(np.int64), scores[top_indices].astype(np.float32)


class VectorIndexSimple:
    def __init__(self, dimension: int = 128):
        self.dimension = dimension
        self.use_faiss = FAISS_AVAILABLE
        self.vectors: List[np.ndarray] = []
        if self.use_faiss:
            self.index = faiss.IndexFlatIP(self.dimension)
        else:
            self.index = None

    def add(self, vectors: np.ndarray):
        if self.use_faiss:
            self.index.add(vectors.astype(np.float32))
        else:
            self.vectors = vectors.tolist()

    def search(self, query: np.ndarray, top_k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        if self.use_faiss:
            return self.index.search(query.reshape(1, -1).astype(np.float32), top_k)
        else:
            scores = []
            for v in self.vectors:
                score = np.dot(query, v)
                scores.append(score)
            scores = np.array(scores)
            top_indices = np.argsort(scores)[::-1][:top_k]
            return top_indices.astype(np.int64), scores[top_indices].astype(np.float32)

    def save(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        if self.use_faiss:
            faiss.write_index(self.index, path)
        else:
            np.save(path, np.array(self.vectors))

    def load(self, path: str):
        if self.use_faiss:
            self.index = faiss.read_index(path)
        else:
            self.vectors = np.load(path).tolist()


class CodeIndexerSimple:
    def __init__(self, embedding_dim: int = 128):
        self.embedder = SimpleEmbedder(dim=embedding_dim)
        self.vector_index = VectorIndexSimple(dimension=embedding_dim)
        self.bm25_index = BM25Fallback()
        self.chunks: List[CodeChunk] = []
        self.metadata: List[Dict] = []

    def build(self, chunks: List[CodeChunk], show_progress: bool = True):
        self.chunks = chunks
        self.metadata = [chunk.to_dict() for chunk in chunks]
        texts = [chunk.content for chunk in chunks]

        if show_progress:
            print(f"Building BM25 index for {len(chunks)} chunks...")
        self.bm25_index.build(chunks)

        if show_progress:
            print(f"Generating embeddings for {len(chunks)} chunks...")
        embeddings = self.embedder.encode(texts)

        if show_progress:
            print(f"Building vector index...")
        self.vector_index.add(embeddings)

        if show_progress:
            print(f"Indexing complete! Total chunks: {len(chunks)}")

    def save(self, index_path: str, metadata_path: str, bm25_path: str):
        self.vector_index.save(index_path)
        Path(bm25_path).parent.mkdir(parents=True, exist_ok=True)
        with open(bm25_path, 'w') as f:
            json.dump({
                'corpus': self.bm25_index.corpus
            }, f)

        Path(metadata_path).parent.mkdir(parents=True, exist_ok=True)
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

    def load(self, index_path: str, metadata_path: str, bm25_path: str):
        self.vector_index.load(index_path)
        with open(metadata_path, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)
        with open(bm25_path, 'r') as f:
            bm25_data = json.load(f)
            self.bm25_index.corpus = bm25_data.get('corpus', [])
            if hasattr(self.bm25_index, 'term_freqs') and not self.bm25_index.term_freqs:
                import re
                self.bm25_index.term_freqs = []
                for text in self.bm25_index.corpus:
                    words = re.findall(r'[a-z0-9]+', text.lower())
                    tf = {}
                    for w in words:
                        tf[w] = tf.get(w, 0) + 1
                    self.bm25_index.term_freqs.append(tf)


class SearchEngineSimple:
    def __init__(self, indexer: CodeIndexerSimple, top_k: int = 10, hybrid_alpha: float = 0.7):
        self.indexer = indexer
        self.top_k = top_k
        self.hybrid_alpha = hybrid_alpha

    def search(self, query: str, top_k: int = None) -> List[Dict]:
        top_k = top_k or self.top_k

        query_vec = self.indexer.embedder.encode_one(query)
        vec_indices, vec_scores = self.indexer.vector_index.search(query_vec, top_k * 2)

        bm25_indices, bm25_scores = self.indexer.bm25_index.search(query, top_k * 2)

        vec_scores = np.clip(vec_scores, 0, None)
        bm25_scores = np.clip(bm25_scores, 0, None)

        vec_scores_norm = self._normalize(vec_scores)
        bm25_scores_norm = self._normalize(bm25_scores)

        combined = {}
        vec_list = vec_indices.tolist() if hasattr(vec_indices, 'tolist') else list(vec_indices)
        bm25_list = bm25_indices.tolist() if hasattr(bm25_indices, 'tolist') else list(bm25_indices)
        
        for idx, score in zip(vec_list, vec_scores_norm.tolist()):
            if isinstance(idx, (int, np.integer)) and idx >= 0:
                combined[int(idx)] = combined.get(int(idx), 0) + self.hybrid_alpha * score

        for idx, score in zip(bm25_list, bm25_scores_norm.tolist()):
            if isinstance(idx, (int, np.integer)) and idx >= 0:
                combined[int(idx)] = combined.get(int(idx), 0) + (1 - self.hybrid_alpha) * score

        ranked = sorted(combined.items(), key=lambda x: x[1], reverse=True)[:top_k]

        results = []
        for idx, score in ranked:
            if idx < len(self.indexer.metadata):
                result = self.indexer.metadata[idx].copy()
                result['score'] = float(score)
                results.append(result)
        return results

    def _normalize(self, scores: np.ndarray) -> np.ndarray:
        if len(scores) == 0 or scores.max() == scores.min():
            return np.ones_like(scores) if len(scores) > 0 else scores
        return (scores - scores.min()) / (scores.max() - scores.min())


if __name__ == "__main__":
    from parser import CodeParser
    import tempfile, os

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test.py")
        with open(test_file, "w") as f:
            f.write("""
def calculate_sum(numbers):
    result = 0
    for num in numbers:
        result += num
    return result

class DataProcessor:
    def __init__(self):
        self.data = []

    def process(self, item):
        self.data.append(item)
        return len(self.data)
""")

        parser = CodeParser()
        parsed = parser.parse_file(Path(test_file))
        chunks = parser.get_all_chunks([parsed])

        print(f"Parsed {len(chunks)} chunks")

        indexer = CodeIndexerSimple(embedding_dim=128)
        indexer.build(chunks)

        engine = SearchEngineSimple(indexer)
        results = engine.search("data processor class")

        print(f"\nSearch results for 'data processor class':")
        for r in results[:3]:
            print(f"  Score: {r['score']:.3f} | {r['chunk_id']}")
