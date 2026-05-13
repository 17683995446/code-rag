import os
import json
import time
import pickle
import heapq
import math
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import threading
import numpy as np


@dataclass
class VectorConfig:
    dimension: int = 384
    metric: str = "cosine"
    index_type: str = "flat"
    nlist: int = 100
    nprobe: int = 10
    m: int = 32
    ef_construction: int = 200
    ef_search: int = 50
    M: int = 16


class VectorIndex(ABC):
    @abstractmethod
    def add(self, vectors: np.ndarray, ids: List[str]):
        pass

    @abstractmethod
    def search(self, query: np.ndarray, k: int = 10) -> Tuple[List[List[str]], List[List[float]]]:
        pass

    @abstractmethod
    def delete(self, ids: List[str]):
        pass

    @abstractmethod
    def save(self, path: str):
        pass

    @abstractmethod
    def load(self, path: str):
        pass

    @abstractmethod
    def size(self) -> int:
        pass


class FlatIndex(VectorIndex):
    def __init__(self, config: VectorConfig = None):
        self.config = config or VectorConfig()
        self.vectors: Optional[np.ndarray] = None
        self.ids: List[str] = []
        self._id_to_idx: Dict[str, int] = {}

    def add(self, vectors: np.ndarray, ids: List[str]):
        if len(vectors) != len(ids):
            raise ValueError("Vectors and ids must have same length")

        if self.config.metric == "cosine":
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1, norms)
            vectors = vectors / norms

        if self.vectors is None:
            self.vectors = vectors.astype(np.float32)
            self.ids = list(ids)
        else:
            self.vectors = np.vstack([self.vectors, vectors.astype(np.float32)])
            self.ids.extend(ids)

        self._rebuild_id_map()

    def _rebuild_id_map(self):
        self._id_to_idx = {id_: idx for idx, id_ in enumerate(self.ids)}

    def search(self, query: np.ndarray, k: int = 10) -> Tuple[List[List[str]], List[List[float]]]:
        if self.vectors is None or len(self.vectors) == 0:
            return [[]], [[]]

        query = query.reshape(1, -1).astype(np.float32)

        if self.config.metric == "cosine":
            norm = np.linalg.norm(query)
            if norm > 0:
                query = query / norm
            scores = np.dot(self.vectors, query.T).flatten()
        elif self.config.metric == "l2":
            diff = self.vectors - query
            scores = -np.sum(diff * diff, axis=1)
        else:
            scores = np.dot(self.vectors, query.T).flatten()

        k = min(k, len(scores))
        top_k_indices = np.argsort(scores)[-k:][::-1]

        return [[self.ids[i] for i in top_k_indices]], [[float(scores[i]) for i in top_k_indices]]

    def delete(self, ids: List[str]):
        indices_to_remove = [self._id_to_idx[id_] for id_ in ids if id_ in self._id_to_idx]

        if indices_to_remove:
            mask = np.ones(len(self.ids), dtype=bool)
            mask[indices_to_remove] = False
            self.vectors = self.vectors[mask]
            self.ids = [self.ids[i] for i in range(len(self.ids)) if mask[i]]
            self._rebuild_id_map()

    def save(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        data = {
            'vectors': self.vectors,
            'ids': self.ids,
            'config': {
                'dimension': self.config.dimension,
                'metric': self.config.metric
            }
        }
        with open(path, 'wb') as f:
            pickle.dump(data, f)

    def load(self, path: str):
        if not Path(path).exists():
            return
        try:
            with open(path, 'rb') as f:
                data = pickle.load(f)
            self.vectors = data['vectors']
            self.ids = data['ids']
            self._rebuild_id_map()
        except Exception:
            pass

    def size(self) -> int:
        return len(self.ids)


class IVFIndex(VectorIndex):
    def __init__(self, config: VectorConfig = None):
        self.config = config or VectorConfig()
        self.centroids: Optional[np.ndarray] = None
        self.inverted_lists: Dict[int, List[Tuple[str, np.ndarray]]] = {}
        self.ids: List[str] = []
        self._id_to_cluster: Dict[str, int] = {}
        self._trained = False

    def _kmeans(self, vectors: np.ndarray, n_clusters: int, max_iter: int = 20) -> np.ndarray:
        n_samples = len(vectors)
        n_clusters = min(n_clusters, n_samples)

        indices = np.random.choice(n_samples, n_clusters, replace=False)
        centroids = vectors[indices].copy()

        for _ in range(max_iter):
            distances = np.dot(centroids, vectors.T)
            assignments = np.argmax(distances, axis=0)

            new_centroids = np.zeros_like(centroids)
            for i in range(n_clusters):
                mask = assignments == i
                if np.any(mask):
                    new_centroids[i] = vectors[mask].mean(axis=0)
                    norm = np.linalg.norm(new_centroids[i])
                    if norm > 0:
                        new_centroids[i] /= norm
                else:
                    new_centroids[i] = centroids[i]

            if np.allclose(centroids, new_centroids):
                break
            centroids = new_centroids

        return centroids

    def train(self, vectors: np.ndarray):
        nlist = min(self.config.nlist, len(vectors))
        self.centroids = self._kmeans(vectors, nlist)
        self._trained = True

    def add(self, vectors: np.ndarray, ids: List[str]):
        if not self._trained:
            self.train(vectors)

        if self.config.metric == "cosine":
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1, norms)
            vectors = vectors / norms

        for i, (vec, id_) in enumerate(zip(vectors, ids)):
            scores = np.dot(self.centroids, vec)
            cluster_id = int(np.argmax(scores))

            if cluster_id not in self.inverted_lists:
                self.inverted_lists[cluster_id] = []
            self.inverted_lists[cluster_id].append((id_, vec.astype(np.float32)))
            self.ids.append(id_)
            self._id_to_cluster[id_] = cluster_id

    def search(self, query: np.ndarray, k: int = 10) -> Tuple[List[List[str]], List[List[float]]]:
        if not self._trained or self.centroids is None:
            return [[]], [[]]

        query = query.reshape(1, -1).astype(np.float32)
        if self.config.metric == "cosine":
            norm = np.linalg.norm(query)
            if norm > 0:
                query = query / norm

        centroid_scores = np.dot(self.centroids, query.T).flatten()
        nprobe = min(self.config.nprobe, len(self.centroids))
        top_clusters = np.argsort(centroid_scores)[-nprobe:][::-1]

        candidates = []
        for cluster_id in top_clusters:
            cluster_id = int(cluster_id)
            if cluster_id in self.inverted_lists:
                for id_, vec in self.inverted_lists[cluster_id]:
                    score = float(np.dot(vec, query.flatten()))
                    candidates.append((id_, score))

        candidates.sort(key=lambda x: x[1], reverse=True)
        top_k = candidates[:k]

        return [[id_ for id_, _ in top_k]], [[score for _, score in top_k]]

    def delete(self, ids: List[str]):
        for id_ in ids:
            if id_ in self._id_to_cluster:
                cluster_id = self._id_to_cluster[id_]
                if cluster_id in self.inverted_lists:
                    self.inverted_lists[cluster_id] = [
                        (i, v) for i, v in self.inverted_lists[cluster_id] if i != id_
                    ]
                del self._id_to_cluster[id_]
        self.ids = [id_ for id_ in self.ids if id_ not in ids]

    def save(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        data = {
            'centroids': self.centroids,
            'inverted_lists': {k: [(id_, v.tolist()) for id_, v in vals]
                               for k, vals in self.inverted_lists.items()},
            'ids': self.ids,
            'config': {
                'dimension': self.config.dimension,
                'metric': self.config.metric,
                'nlist': self.config.nlist,
                'nprobe': self.config.nprobe
            }
        }
        with open(path, 'wb') as f:
            pickle.dump(data, f)

    def load(self, path: str):
        if not Path(path).exists():
            return
        try:
            with open(path, 'rb') as f:
                data = pickle.load(f)
            self.centroids = data['centroids']
            self.inverted_lists = {
                k: [(id_, np.array(v, dtype=np.float32)) for id_, v in vals]
                for k, vals in data['inverted_lists'].items()
            }
            self.ids = data['ids']
            self._id_to_cluster = {id_: cluster for cluster, vals in self.inverted_lists.items()
                                   for id_, _ in vals}
            self._trained = True
        except Exception:
            pass

    def size(self) -> int:
        return len(self.ids)


class HNSWIndex(VectorIndex):
    def __init__(self, config: VectorConfig = None):
        self.config = config or VectorConfig()
        self.M = config.M
        self.ef_construction = config.ef_construction
        self.ef_search = config.ef_search

        self.nodes: Dict[str, np.ndarray] = {}
        self.graphs: List[Dict[str, List[str]]] = []
        self.entry_point: Optional[str] = None
        self.max_level: int = 0
        self._level_mult = 1.0 / math.log(2)

    def _get_random_level(self) -> int:
        return int(-math.log(np.random.random()) * self._level_mult)

    def _distance(self, v1: np.ndarray, v2: np.ndarray) -> float:
        if self.config.metric == "cosine":
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            if norm1 > 0 and norm2 > 0:
                return 1.0 - np.dot(v1, v2) / (norm1 * norm2)
            return 1.0
        else:
            return float(np.linalg.norm(v1 - v2))

    def _search_layer(self, query: np.ndarray, entry_points: List[str], ef: int, level: int) -> List[Tuple[float, str]]:
        visited = set(entry_points)
        candidates = []
        results = []

        for ep in entry_points:
            if ep in self.nodes:
                dist = self._distance(query, self.nodes[ep])
                heapq.heappush(candidates, (dist, ep))
                heapq.heappush(results, (-dist, ep))

        while candidates:
            dist, node = heapq.heappop(candidates)

            worst_dist = -results[0][0] if results else float('inf')
            if dist > worst_dist:
                break

            if level < len(self.graphs) and node in self.graphs[level]:
                for neighbor in self.graphs[level][node]:
                    if neighbor not in visited and neighbor in self.nodes:
                        visited.add(neighbor)
                        neighbor_dist = self._distance(query, self.nodes[neighbor])

                        if len(results) < ef or neighbor_dist < -results[0][0]:
                            heapq.heappush(candidates, (neighbor_dist, neighbor))
                            heapq.heappush(results, (-neighbor_dist, neighbor))

                            if len(results) > ef:
                                heapq.heappop(results)

        return [(-d, n) for d, n in results]

    def _select_neighbors(self, candidates: List[Tuple[float, str]], M: int) -> List[str]:
        candidates.sort(key=lambda x: x[0])
        return [n for _, n in candidates[:M]]

    def add(self, vectors: np.ndarray, ids: List[str]):
        for vec, id_ in zip(vectors, ids):
            vec = vec.astype(np.float32)
            level = self._get_random_level()

            self.nodes[id_] = vec

            while len(self.graphs) <= level:
                self.graphs.append({})

            if self.entry_point is None:
                self.entry_point = id_
                self.max_level = level
                for l in range(level + 1):
                    self.graphs[l][id_] = []
                continue

            current_ep = [self.entry_point]

            for l in range(self.max_level, level, -1):
                results = self._search_layer(vec, current_ep, 1, l)
                if results:
                    current_ep = [results[0][1]]

            for l in range(min(level, self.max_level), -1, -1):
                results = self._search_layer(vec, current_ep, self.ef_construction, l)

                neighbors = self._select_neighbors(results, self.M)
                self.graphs[l][id_] = neighbors

                for neighbor in neighbors:
                    if neighbor in self.graphs[l]:
                        self.graphs[l][neighbor].append(id_)
                        if len(self.graphs[l][neighbor]) > self.M:
                            self.graphs[l][neighbor] = self.graphs[l][neighbor][-self.M:]

                current_ep = [n for _, n in results[:self.ef_construction]]

            if level > self.max_level:
                self.max_level = level
                self.entry_point = id_

    def search(self, query: np.ndarray, k: int = 10) -> Tuple[List[List[str]], List[List[float]]]:
        if not self.entry_point or not self.nodes:
            return [[]], [[]]

        query = query.reshape(1, -1).astype(np.float32)
        current_ep = [self.entry_point]

        for l in range(self.max_level, 0, -1):
            results = self._search_layer(query.flatten(), current_ep, 1, l)
            if results:
                current_ep = [results[0][1]]

        results = self._search_layer(query.flatten(), current_ep, max(self.ef_search, k), 0)
        results.sort(key=lambda x: x[0])

        top_k = results[:k]
        return [[n for _, n in top_k]], [[d for d, _ in top_k]]

    def delete(self, ids: List[str]):
        for id_ in ids:
            if id_ in self.nodes:
                del self.nodes[id_]
                for level in range(len(self.graphs)):
                    if id_ in self.graphs[level]:
                        for neighbor in self.graphs[level][id_]:
                            if neighbor in self.graphs[level]:
                                self.graphs[level][neighbor] = [
                                    n for n in self.graphs[level][neighbor] if n != id_
                                ]
                        del self.graphs[level][id_]

        if self.entry_point in ids:
            self.entry_point = next(iter(self.nodes), None)

    def save(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        data = {
            'nodes': {k: v.tolist() for k, v in self.nodes.items()},
            'graphs': self.graphs,
            'entry_point': self.entry_point,
            'max_level': self.max_level,
            'config': {
                'M': self.M,
                'ef_construction': self.ef_construction,
                'ef_search': self.ef_search,
                'metric': self.config.metric
            }
        }
        with open(path, 'wb') as f:
            pickle.dump(data, f)

    def load(self, path: str):
        if not Path(path).exists():
            return
        try:
            with open(path, 'rb') as f:
                data = pickle.load(f)
            self.nodes = {k: np.array(v, dtype=np.float32) for k, v in data['nodes'].items()}
            self.graphs = data['graphs']
            self.entry_point = data['entry_point']
            self.max_level = data['max_level']
        except Exception:
            pass

    def size(self) -> int:
        return len(self.nodes)


class ProductQuantizer:
    def __init__(self, n_subvectors: int = 8, n_centroids: int = 256):
        self.n_subvectors = n_subvectors
        self.n_centroids = n_centroids
        self.codebooks: Optional[np.ndarray] = None
        self.codes: Optional[np.ndarray] = None
        self.ids: List[str] = []
        self._dimension = None

    def train(self, vectors: np.ndarray):
        n_samples, dim = vectors.shape
        self._dimension = dim
        subvector_dim = dim // self.n_subvectors

        self.codebooks = np.zeros((self.n_subvectors, self.n_centroids, subvector_dim), dtype=np.float32)

        for m in range(self.n_subvectors):
            start = m * subvector_dim
            end = start + subvector_dim
            subvectors = vectors[:, start:end]

            indices = np.random.choice(n_samples, min(self.n_centroids, n_samples), replace=False)
            self.codebooks[m] = subvectors[indices]

            for _ in range(10):
                distances = np.sum((subvectors[:, None, :] - self.codebooks[m][None, :, :]) ** 2, axis=2)
                assignments = np.argmin(distances, axis=1)

                for c in range(self.n_centroids):
                    mask = assignments == c
                    if np.any(mask):
                        self.codebooks[m, c] = subvectors[mask].mean(axis=0)

    def encode(self, vectors: np.ndarray) -> np.ndarray:
        n_samples = len(vectors)
        subvector_dim = self._dimension // self.n_subvectors
        codes = np.zeros((n_samples, self.n_subvectors), dtype=np.uint8)

        for m in range(self.n_subvectors):
            start = m * subvector_dim
            end = start + subvector_dim
            subvectors = vectors[:, start:end]

            distances = np.sum((subvectors[:, None, :] - self.codebooks[m][None, :, :]) ** 2, axis=2)
            codes[:, m] = np.argmin(distances, axis=1)

        return codes

    def decode(self, codes: np.ndarray) -> np.ndarray:
        n_samples = len(codes)
        vectors = np.zeros((n_samples, self._dimension), dtype=np.float32)

        subvector_dim = self._dimension // self.n_subvectors
        for m in range(self.n_subvectors):
            start = m * subvector_dim
            end = start + subvector_dim
            vectors[:, start:end] = self.codebooks[m, codes[:, m]]

        return vectors

    def asymmetric_distance(self, query: np.ndarray, codes: np.ndarray) -> np.ndarray:
        subvector_dim = self._dimension // self.n_subvectors
        n_samples = len(codes)

        distance_tables = np.zeros((self.n_subvectors, self.n_centroids), dtype=np.float32)

        for m in range(self.n_subvectors):
            start = m * subvector_dim
            end = start + subvector_dim
            query_sub = query[start:end]

            distances = np.sum((self.codebooks[m] - query_sub) ** 2, axis=1)
            distance_tables[m] = distances

        distances = np.zeros(n_samples, dtype=np.float32)
        for m in range(self.n_subvectors):
            distances += distance_tables[m, codes[:, m]]

        return distances


class VectorStore:
    def __init__(self, config: VectorConfig = None, storage_path: str = "./data/vectors"):
        self.config = config or VectorConfig()
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self._index = self._create_index()
        self._lock = threading.Lock()

    def _create_index(self) -> VectorIndex:
        index_type = self.config.index_type.lower()

        if index_type == "flat":
            return FlatIndex(self.config)
        elif index_type == "ivf":
            return IVFIndex(self.config)
        elif index_type == "hnsw":
            return HNSWIndex(self.config)
        else:
            return FlatIndex(self.config)

    def add(self, vectors: np.ndarray, ids: List[str]):
        with self._lock:
            self._index.add(vectors, ids)

    def search(self, query: np.ndarray, k: int = 10) -> Tuple[List[str], List[float]]:
        with self._lock:
            ids, scores = self._index.search(query, k)
            return ids[0] if ids else [], scores[0] if scores else []

    def delete(self, ids: List[str]):
        with self._lock:
            self._index.delete(ids)

    def save(self):
        index_path = self.storage_path / "index.pkl"
        self._index.save(str(index_path))

    def load(self):
        index_path = self.storage_path / "index.pkl"
        self._index.load(str(index_path))

    def size(self) -> int:
        return self._index.size()

    def stats(self) -> Dict:
        return {
            "index_type": self.config.index_type,
            "dimension": self.config.dimension,
            "metric": self.config.metric,
            "size": self.size()
        }


class HybridVectorIndex:
    def __init__(self, config: VectorConfig = None, storage_path: str = "./data/vectors"):
        self.config = config or VectorConfig()
        self.storage_path = Path(storage_path)

        self.vector_store = VectorStore(config, storage_path)
        self.id_to_metadata: Dict[str, Dict] = {}
        self.file_to_ids: Dict[str, List[str]] = {}

    def add(self, vectors: np.ndarray, ids: List[str], metadata: List[Dict] = None):
        self.vector_store.add(vectors, ids)

        for i, id_ in enumerate(ids):
            meta = metadata[i] if metadata else {}
            self.id_to_metadata[id_] = meta

            file_path = meta.get('file_path', '')
            if file_path:
                if file_path not in self.file_to_ids:
                    self.file_to_ids[file_path] = []
                self.file_to_ids[file_path].append(id_)

    def search(
        self,
        query: np.ndarray,
        k: int = 10,
        filters: Dict = None
    ) -> List[Dict]:
        ids, scores = self.vector_store.search(query, k * 2)

        results = []
        for id_, score in zip(ids, scores):
            meta = self.id_to_metadata.get(id_, {})

            if filters and not self._match_filters(meta, filters):
                continue

            results.append({
                'id': id_,
                'score': score,
                'metadata': meta
            })

            if len(results) >= k:
                break

        return results

    def _match_filters(self, metadata: Dict, filters: Dict) -> bool:
        for key, value in filters.items():
            if key not in metadata:
                return False
            if isinstance(value, list):
                if metadata[key] not in value:
                    return False
            elif metadata[key] != value:
                return False
        return True

    def delete_by_file(self, file_path: str):
        if file_path in self.file_to_ids:
            ids = self.file_to_ids[file_path]
            self.vector_store.delete(ids)
            for id_ in ids:
                self.id_to_metadata.pop(id_, None)
            del self.file_to_ids[file_path]

    def delete(self, ids: List[str]):
        self.vector_store.delete(ids)
        for id_ in ids:
            meta = self.id_to_metadata.pop(id_, None)
            if meta:
                file_path = meta.get('file_path', '')
                if file_path in self.file_to_ids:
                    self.file_to_ids[file_path] = [
                        i for i in self.file_to_ids[file_path] if i != id_
                    ]

    def save(self):
        self.vector_store.save()

        meta_path = self.storage_path / "metadata.json"
        with open(meta_path, 'w') as f:
            json.dump({
                'id_to_metadata': self.id_to_metadata,
                'file_to_ids': self.file_to_ids
            }, f)

    def load(self):
        self.vector_store.load()

        meta_path = self.storage_path / "metadata.json"
        if meta_path.exists():
            with open(meta_path) as f:
                data = json.load(f)
            self.id_to_metadata = data.get('id_to_metadata', {})
            self.file_to_ids = data.get('file_to_ids', {})

    def stats(self) -> Dict:
        return {
            **self.vector_store.stats(),
            'total_metadata': len(self.id_to_metadata),
            'total_files': len(self.file_to_ids)
        }
