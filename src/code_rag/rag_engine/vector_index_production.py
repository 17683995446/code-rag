"""
Production Vector Index - 真实向量索引集成
使用FAISS库，支持多种索引类型，自动降级
"""

from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
import pickle
import os

# 尝试导入 numpy
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("⚠️ numpy not available, using fallback")

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False


@dataclass
class SearchResult:
    """搜索结果"""
    index: int
    distance: float
    metadata: Dict[str, Any]


class ProductionVectorIndex:
    """
    产品级向量索引
    支持多种FAISS索引类型
    """
    
    INDEX_TYPES = {
        "flat": "FlatL2 - 精确搜索，适合小数据集",
        "ivfflat": "IVFFlat - 近似搜索，适合大数据集",
        "hnsw": "HNSW - 图索引，高速近似搜索"
    }
    
    def __init__(
        self,
        dimension: int = 384,
        index_type: str = "flat",
        nlist: int = 100,
        nprobe: int = 10,
        metric: str = "l2"
    ):
        """
        初始化向量索引
        
        Args:
            dimension: 向量维度
            index_type: 索引类型 ('flat', 'ivfflat', 'hnsw')
            nlist: IVF索引的聚类数
            nprobe: IVF搜索的探针数
            metric: 距离度量 ('l2' 或 'ip' 内积)
        """
        self.dimension = dimension
        self.index_type = index_type
        self.metric = metric
        self.nlist = nlist
        self.nprobe = nprobe
        
        self.index = None
        self.metadata: List[Dict[str, Any]] = []
        self.ids: List[int] = []
        self._use_real_index = False
        
        if FAISS_AVAILABLE and NUMPY_AVAILABLE:
            self._init_faiss_index()
        else:
            self._init_fallback_index()
    
    def _init_faiss_index(self):
        """初始化FAISS索引"""
        try:
            if self.metric == "ip":
                # 内积度量需要归一化
                quantizer = faiss.IndexFlatIP(self.dimension)
            else:
                quantizer = faiss.IndexFlatL2(self.dimension)
            
            if self.index_type == "flat":
                self.index = quantizer
            elif self.index_type == "ivfflat":
                self.index = faiss.IndexIVFFlat(quantizer, self.dimension, self.nlist)
                self.index.nprobe = self.nprobe
            elif self.index_type == "hnsw":
                self.index = faiss.IndexHNSWFlat(self.dimension, 32)
            else:
                self.index = quantizer
            
            self._use_real_index = True
            print(f"✅ 使用真实FAISS索引: {self.index_type} (维度: {self.dimension})")
        except Exception as e:
            print(f"⚠️ FAISS索引初始化失败，使用内存索引: {e}")
            self._init_fallback_index()
    
    def _init_fallback_index(self):
        """初始化内存索引作为降级方案"""
        self._vectors: List[Any] = []
        self._use_real_index = False
        print("⚠️ 使用内存索引（非FAISS）")
    
    def is_trained(self) -> bool:
        """检查索引是否已训练"""
        if self._use_real_index:
            return not self.index.is_trained if hasattr(self.index, 'is_trained') else True
        return True
    
    def train(self, vectors: List[Any]):
        """
        训练索引（对于需要训练的索引如IVF）
        
        Args:
            vectors: 训练向量
        """
        if self._use_real_index and NUMPY_AVAILABLE and hasattr(self.index, 'train'):
            # 转换为numpy数组
            if not isinstance(vectors, np.ndarray):
                vectors = np.array(vectors, dtype=np.float32)
            if not self.index.is_trained:
                self.index.train(vectors)
                print("✅ 索引训练完成")
        # 内存索引不需要训练
    
    def add(self, vectors: List[Any], metadata: Optional[List[Dict[str, Any]]] = None):
        """
        添加向量到索引
        
        Args:
            vectors: 向量数组
            metadata: 对应的元数据列表
        """
        if self._use_real_index and NUMPY_AVAILABLE:
            if not isinstance(vectors, np.ndarray):
                vectors = np.array(vectors, dtype=np.float32)
            self.index.add(vectors)
        else:
            self._vectors.extend(vectors)
        
        # 添加元数据
        if metadata:
            self.metadata.extend(metadata)
        else:
            self.metadata.extend([{} for _ in range(len(vectors))])
        
        # 添加ID
        start_id = len(self.ids)
        self.ids.extend(range(start_id, start_id + len(vectors)))
    
    def search(self, query: Any, k: int = 5) -> List[SearchResult]:
        """
        搜索最近邻
        
        Args:
            query: 查询向量
            k: 返回的结果数量
            
        Returns:
            搜索结果列表
        """
        if self._use_real_index and NUMPY_AVAILABLE:
            if not isinstance(query, np.ndarray):
                query = np.array([query], dtype=np.float32)
            elif len(query.shape) == 1:
                query = query.reshape(1, -1)
            
            if self.metric == "ip":
                # 内积搜索
                distances, indices = self.index.search(query, k)
            else:
                distances, indices = self.index.search(query, k)
        else:
            # 内存索引搜索
            distances, indices = self._memory_search(query, k)
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx >= 0 and idx < len(self.metadata):
                result = SearchResult(
                    index=int(idx),
                    distance=float(dist),
                    metadata=self.metadata[int(idx)]
                )
                results.append(result)
        
        return results
    
    def _memory_search(self, query: Any, k: int) -> Tuple[List[float], List[int]]:
        """
        内存索引搜索（降级方案）
        """
        if not self._vectors:
            return [[float('inf')] * k], [[-1] * k]
        
        # 计算与所有向量的距离
        distances = []
        for i, vec in enumerate(self._vectors):
            if NUMPY_AVAILABLE:
                # 使用numpy计算L2距离
                if not isinstance(query, np.ndarray):
                    query_np = np.array(query)
                    vec_np = np.array(vec)
                else:
                    query_np = query
                    vec_np = np.array(vec)
                dist = np.linalg.norm(query_np - vec_np)
                distances.append((float(dist), i))
            else:
                # 简单的欧氏距离
                dist = 0.0
                for a, b in zip(query, vec):
                    dist += (a - b) ** 2
                distances.append((dist ** 0.5, i))
        
        # 排序并返回前k个
        distances.sort()
        top_k = distances[:k]
        dist_list = [d for d, _ in top_k]
        idx_list = [i for _, i in top_k]
        
        # 填充不足k个的情况
        while len(dist_list) < k:
            dist_list.append(float('inf'))
            idx_list.append(-1)
        
        return [dist_list], [idx_list]
    
    def save(self, path: str):
        """
        保存索引到磁盘
        
        Args:
            path: 保存路径
        """
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        
        if self._use_real_index and NUMPY_AVAILABLE:
            faiss.write_index(self.index, path + ".faiss")
        
        with open(path + ".meta", 'wb') as f:
            pickle.dump({
                'metadata': self.metadata,
                'ids': self.ids,
                'dimension': self.dimension,
                'index_type': self.index_type,
                'metric': self.metric,
                'vectors': self._vectors if not self._use_real_index else None
            }, f)
        
        print(f"✅ 索引已保存: {path}")
    
    def load(self, path: str):
        """
        从磁盘加载索引
        
        Args:
            path: 加载路径
        """
        if self._use_real_index and NUMPY_AVAILABLE and os.path.exists(path + ".faiss"):
            self.index = faiss.read_index(path + ".faiss")
        
        if os.path.exists(path + ".meta"):
            with open(path + ".meta", 'rb') as f:
                data = pickle.load(f)
                self.metadata = data['metadata']
                self.ids = data['ids']
                self.dimension = data['dimension']
                self.index_type = data['index_type']
                self.metric = data['metric']
                if not self._use_real_index and data.get('vectors'):
                    self._vectors = data['vectors']
        
        print(f"✅ 索引已加载: {path}")
    
    def get_size(self) -> int:
        """获取索引中的向量数量"""
        if self._use_real_index:
            return self.index.ntotal
        return len(self._vectors)
    
    def clear(self):
        """清空索引"""
        if self._use_real_index:
            # 重建索引
            self._init_faiss_index()
        self._vectors.clear()
        self.metadata.clear()
        self.ids.clear()
    
    def get_info(self) -> Dict[str, Any]:
        """获取索引信息"""
        return {
            'dimension': self.dimension,
            'index_type': self.index_type,
            'metric': self.metric,
            'size': self.get_size(),
            'use_real_index': self._use_real_index,
            'is_trained': self.is_trained()
        }


class HybridVectorIndex:
    """
    混合向量索引
    结合多种索引类型
    """
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.flat_index = ProductionVectorIndex(dimension, "flat")
        self.ivff_index = ProductionVectorIndex(dimension, "ivfflat")
        self._use_ivf = False
    
    def add(self, vectors: List[Any], metadata: Optional[List[Dict[str, Any]]] = None):
        """添加向量"""
        self.flat_index.add(vectors, metadata)
        
        if self._use_ivf:
            self.ivff_index.add(vectors, metadata)
    
    def search(self, query: Any, k: int = 5, use_approx: bool = False) -> List[SearchResult]:
        """搜索"""
        if use_approx and self._use_ivf:
            return self.ivff_index.search(query, k)
        return self.flat_index.search(query, k)
    
    def build_approx_index(self, vectors: List[Any]):
        """构建近似索引"""
        self._use_ivf = True
        self.ivff_index.train(vectors)
        self.ivff_index.add(vectors)
        print("✅ 近似索引构建完成")


def create_vector_index(
    dimension: int = 384,
    index_type: str = "flat",
    **kwargs
) -> ProductionVectorIndex:
    """
    创建向量索引的工厂函数
    
    Args:
        dimension: 向量维度
        index_type: 索引类型
        **kwargs: 其他参数
        
    Returns:
        向量索引实例
    """
    return ProductionVectorIndex(dimension=dimension, index_type=index_type, **kwargs)
