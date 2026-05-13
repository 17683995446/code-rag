import json
import pickle
import numpy as np
import faiss
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from rank_bm25 import BM25Okapi

from parser import CodeChunk


class EmbeddingEngine:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", device: str = "cpu"):
        self.model = SentenceTransformer(model_name, device=device)
        self.dimension = self.model.get_sentence_embedding_dimension()

    def encode(self, texts: List[str], show_progress: bool = True) -> np.ndarray:
        return self.model.encode(
            texts,
            show_progress_bar=show_progress,
            batch_size=32,
            convert_to_numpy=True,
            normalize_embeddings=True
        )


class BM25Index:
    def __init__(self):
        self.tokenized_corpus: List[List[str]] = []
        self.bm25: Optional[BM25Okapi] = None
        self.corpus: List[str] = []

    def build(self, chunks: List[CodeChunk]):
        self.corpus = [chunk.content for chunk in chunks]
        self.tokenized_corpus = [
            self._tokenize(text) for text in self.corpus
        ]
        self.bm25 = BM25Okapi(self.tokenized_corpus)

    def _tokenize(self, text: str) -> List[str]:
        text = text.lower()
        tokens = []
        current_token = []

        for char in text:
            if char.isalnum():
                current_token.append(char)
            else:
                if current_token:
                    tokens.append(''.join(current_token))
                    current_token = []
        if current_token:
            tokens.append(''.join(current_token))

        return tokens

    def search(self, query: str, top_k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)

        top_indices = np.argsort(scores)[::-1][:top_k]
        top_scores = scores[top_indices]

        return top_indices.astype(np.int64), top_scores.astype(np.float32)

    def save(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump({
                'tokenized_corpus': self.tokenized_corpus,
                'corpus': self.corpus
            }, f)

    def load(self, path: str):
        with open(path, 'rb') as f:
            data = pickle.load(f)
        self.tokenized_corpus = data['tokenized_corpus']
        self.corpus = data['corpus']
        self.bm25 = BM25Okapi(self.tokenized_corpus)


class VectorIndex:
    def __init__(self, dimension: int, index_type: str = "FlatIP"):
        self.dimension = dimension
        self.index_type = index_type
        self.index: Optional[faiss.Index] = None
        self._build_index()

    def _build_index(self):
        if self.index_type == "FlatIP":
            self.index = faiss.IndexFlatIP(self.dimension)
        elif self.index_type == "FlatL2":
            self.index = faiss.IndexFlatL2(self.dimension)
        elif self.index_type == "IVF":
            quantizer = faiss.IndexFlatIP(self.dimension)
            self.index = faiss.IndexIVFFlat(quantizer, self.dimension, 100)
        else:
            self.index = faiss.IndexFlatIP(self.dimension)

    def add(self, vectors: np.ndarray):
        if vectors.dtype != np.float32:
            vectors = vectors.astype(np.float32)
        self.index.add(vectors)

    def train(self, vectors: np.ndarray):
        if hasattr(self.index, 'train') and not self.index.is_trained:
            if vectors.dtype != np.float32:
                vectors = vectors.astype(np.float32)
            self.index.train(vectors)

    def search(self, query: np.ndarray, top_k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        if query.dtype != np.float32:
            query = query.astype(np.float32)
        if query.ndim == 1:
            query = query.reshape(1, -1)
        return self.index.search(query, top_k)

    def save(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, path)

    def load(self, path: str):
        self.index = faiss.read_index(path)


class CodeIndexer:
    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        embedding_dim: int = 384,
        index_type: str = "FlatIP",
        device: str = "cpu"
    ):
        self.embedding_engine = EmbeddingEngine(embedding_model, device)
        self.vector_index = VectorIndex(embedding_dim, index_type)
        self.bm25_index = BM25Index()
        self.chunks: List[CodeChunk] = []
        self.metadata: List[Dict] = []

    def build(
        self,
        chunks: List[CodeChunk],
        batch_size: int = 32,
        show_progress: bool = True
    ):
        self.chunks = chunks
        self.metadata = [chunk.to_dict() for chunk in chunks]

        texts = [chunk.content for chunk in chunks]

        if show_progress:
            print(f"Building BM25 index for {len(chunks)} chunks...")
        self.bm25_index.build(chunks)

        if show_progress:
            print(f"Generating embeddings for {len(chunks)} chunks...")
        embeddings = self.embedding_engine.encode(texts, show_progress)

        if show_progress:
            print(f"Building FAISS index...")
        if hasattr(self.vector_index.index, 'train') and not self.vector_index.index.is_trained:
            self.vector_index.train(embeddings)

        self.vector_index.add(embeddings)

        if show_progress:
            print(f"Indexing complete! Total chunks: {len(chunks)}")

    def save(self, index_path: str, metadata_path: str, bm25_path: str):
        self.vector_index.save(index_path)
        self.bm25_index.save(bm25_path)

        Path(metadata_path).parent.mkdir(parents=True, exist_ok=True)
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

    def load(self, index_path: str, metadata_path: str, bm25_path: str):
        self.vector_index.load(index_path)
        self.bm25_index.load(bm25_path)

        with open(metadata_path, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)


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

    def search(self, query: str, top_k: Optional[int] = None) -> List[Dict]:
        top_k = top_k or self.top_k

        vec_indices, vec_scores = self.vector_index.search(
            self.vector_index.embedding_engine.encode([query], show_progress=False)[0],
            top_k * 2
        )

        bm25_indices, bm25_scores = self.bm25_index.search(query, top_k * 2)

        vec_scores_norm = self._normalize_scores(vec_scores[vec_scores >= 0])
        bm25_scores_norm = self._normalize_scores(bm25_scores[bm25_scores >= 0])

        vec_indices = vec_indices[vec_scores >= 0]
        bm25_indices = bm25_indices[bm25_scores >= 0]

        combined_scores: Dict[int, float] = {}

        for idx, score in zip(vec_indices, vec_scores_norm):
            if idx not in combined_scores:
                combined_scores[idx] = 0
            combined_scores[idx] += self.hybrid_alpha * score

        for idx, score in zip(bm25_indices, bm25_scores_norm):
            if idx not in combined_scores:
                combined_scores[idx] = 0
            combined_scores[idx] += (1 - self.hybrid_alpha) * score

        ranked = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        results = []
        for idx, score in ranked:
            result = self.metadata[idx].copy()
            result['score'] = float(score)
            result['vec_score'] = float(vec_scores_norm[list(vec_indices).index(idx)]) if idx in vec_indices else 0
            result['bm25_score'] = float(bm25_scores_norm[list(bm25_indices).index(idx)]) if idx in bm25_indices else 0
            results.append(result)

        return results

    def _normalize_scores(self, scores: np.ndarray) -> np.ndarray:
        if len(scores) == 0:
            return scores
        min_s, max_s = scores.min(), scores.max()
        if max_s - min_s > 0:
            return (scores - min_s) / (max_s - min_s)
        return np.ones_like(scores) if len(scores) > 0 else scores


if __name__ == "__main__":
    from parser import CodeParser, CodeChunk
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test.py")
        with open(test_file, "w") as f:
            f.write("""
def hello_world():
    print("Hello, World!")

def add_numbers(a, b):
    return a + b

class Calculator:
    def __init__(self):
        self.result = 0

    def add(self, x):
        self.result += x
        return self.result
""")

        parser = CodeParser()
        parsed = parser.parse_file(Path(test_file))
        chunks = parser.get_all_chunks([parsed])

        print(f"Parsed {len(chunks)} chunks")

        indexer = CodeIndexer()
        indexer.build(chunks)

        results = HybridSearchEngine(
            indexer.vector_index,
            indexer.bm25_index,
            indexer.metadata
        ).search("calculator class")

        print(f"\nSearch results for 'calculator class':")
        for r in results[:3]:
            print(f"  Score: {r['score']:.3f} | {r['chunk_id']}")
