"""
Production Embedding Engine - 真实Embedding模型集成
使用sentence-transformers库，支持多种预训练模型
"""

import hashlib
from typing import List, Optional, Dict, Any

# 尝试导入 numpy
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("⚠️ numpy not available, using fallback")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class ProductionEmbeddingEngine:
    """
    产品级Embedding引擎
    支持多种预训练模型，自动降级到简化版
    """
    
    SUPPORTED_MODELS = {
        "all-MiniLM-L6-v2": {
            "dimension": 384,
            "description": "轻量快速，适合大多数场景"
        },
        "all-mpnet-base-v2": {
            "dimension": 768,
            "description": "更高精度，更慢"
        },
        "paraphrase-multilingual-MiniLM-L12-v2": {
            "dimension": 384,
            "description": "多语言支持"
        }
    }
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: Optional[str] = None,
        normalize: bool = True
    ):
        """
        初始化Embedding引擎
        
        Args:
            model_name: 模型名称
            device: 设备 ('cpu', 'cuda', 或 None 自动选择)
            normalize: 是否归一化向量
        """
        self.model_name = model_name
        self.normalize = normalize
        self.model = None
        self.dimension = 384
        self._use_real_model = False
        
        if SENTENCE_TRANSFORMERS_AVAILABLE and NUMPY_AVAILABLE:
            try:
                self.model = SentenceTransformer(model_name, device=device)
                self.dimension = self.model.get_sentence_embedding_dimension()
                self._use_real_model = True
                print(f"✅ 使用真实模型: {model_name} (维度: {self.dimension})")
            except Exception as e:
                print(f"⚠️ 模型加载失败，使用简化版: {e}")
                self._init_fallback()
        else:
            print("⚠️ sentence-transformers或numpy未安装，使用简化版")
            self._init_fallback()
    
    def _init_fallback(self):
        """初始化简化版Fallback"""
        self.dimension = 384
        self._use_real_model = False
    
    def encode(self, text: str) -> Any:
        """
        编码单个文本
        
        Args:
            text: 输入文本
            
        Returns:
            文本向量
        """
        if self._use_real_model and NUMPY_AVAILABLE:
            embedding = self.model.encode(
                text,
                normalize_embeddings=self.normalize,
                convert_to_numpy=True
            )
        else:
            embedding = self._hash_embedding(text)
        
        return embedding
    
    def encode_batch(self, texts: List[str]) -> List[Any]:
        """
        批量编码文本
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表
        """
        if self._use_real_model and NUMPY_AVAILABLE:
            embeddings = self.model.encode(
                texts,
                normalize_embeddings=self.normalize,
                convert_to_numpy=True,
                show_progress_bar=len(texts) > 10
            )
            if len(texts) == 1:
                return [embeddings]
            return list(embeddings)
        else:
            return [self._hash_embedding(text) for text in texts]
    
    def _hash_embedding(self, text: str) -> Any:
        """
        简化版Embedding：基于hash的特征向量
        
        Args:
            text: 输入文本
            
        Returns:
            伪嵌入向量
        """
        if NUMPY_AVAILABLE:
            # 使用hash生成伪随机但一致的向量
            hash_value = int(hashlib.md5(text.encode()).hexdigest(), 16)
            
            # 生成伪随机向量
            np.random.seed(hash_value % (2**32))
            embedding = np.random.randn(self.dimension)
            
            # 归一化
            embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
            
            return embedding.astype(np.float32)
        else:
            # 最简单的fallback：返回一个列表
            hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
            vec = []
            for i in range(self.dimension):
                # 简单的伪随机
                seed = (hash_val + i * 1234567) % (2**31)
                # 转换到-1到1的范围
                val = ((seed / (2**31 - 1)) * 2) - 1
                vec.append(val)
            return vec
    
    def similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的相似度
        
        Args:
            text1: 文本1
            text2: 文本2
            
        Returns:
            相似度分数 (0-1)
        """
        emb1 = self.encode(text1)
        emb2 = self.encode(text2)
        
        if NUMPY_AVAILABLE:
            # 余弦相似度
            similarity = np.dot(emb1, emb2) / (
                np.linalg.norm(emb1) * np.linalg.norm(emb2) + 1e-8
            )
            return float(similarity)
        else:
            # 简单的fallback：计算两个hash
            h1 = int(hashlib.md5(text1.encode()).hexdigest(), 16)
            h2 = int(hashlib.md5(text2.encode()).hexdigest(), 16)
            # 计算汉明距离的反向
            distance = bin(h1 ^ h2).count('1')
            max_distance = 128  # 128位MD5
            return 1.0 - (distance / max_distance)
    
    def batch_similarity(
        self,
        query: str,
        texts: List[str]
    ) -> List[float]:
        """
        计算查询与多个文本的相似度
        
        Args:
            query: 查询文本
            texts: 文本列表
            
        Returns:
            相似度分数列表
        """
        return [self.similarity(query, text) for text in texts]
    
    def get_embedding_dimension(self) -> int:
        """获取向量维度"""
        return self.dimension
    
    def is_using_real_model(self) -> bool:
        """是否使用真实模型"""
        return self._use_real_model
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "model_name": self.model_name,
            "dimension": self.dimension,
            "use_real_model": self._use_real_model,
            "normalize": self.normalize,
            "supported_models": list(self.SUPPORTED_MODELS.keys())
        }


class EmbeddingCache:
    """
    Embedding缓存，使用LRU策略
    """
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.cache: Dict[str, Any] = {}
        self.access_order: List[str] = []
    
    def get(self, text: str) -> Optional[Any]:
        """获取缓存的embedding"""
        if text in self.cache:
            # 移到末尾（最近使用）
            self.access_order.remove(text)
            self.access_order.append(text)
            return self.cache[text]
        return None
    
    def set(self, text: str, embedding: Any):
        """设置缓存"""
        if text in self.cache:
            self.access_order.remove(text)
        elif len(self.cache) >= self.max_size:
            # 删除最旧的
            oldest = self.access_order.pop(0)
            del self.cache[oldest]
        
        self.cache[text] = embedding
        self.access_order.append(text)
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.access_order.clear()
    
    def size(self) -> int:
        """获取缓存大小"""
        return len(self.cache)


class CachedEmbeddingEngine(ProductionEmbeddingEngine):
    """
    带缓存的Embedding引擎
    """
    
    def __init__(self, cache_size: int = 10000, **kwargs):
        super().__init__(**kwargs)
        self.cache = EmbeddingCache(max_size=cache_size)
    
    def encode(self, text: str) -> Any:
        """带缓存的编码"""
        cached = self.cache.get(text)
        if cached is not None:
            return cached
        
        embedding = super().encode(text)
        self.cache.set(text, embedding)
        return embedding
    
    def encode_batch(self, texts: List[str]) -> List[Any]:
        """带缓存的批量编码"""
        results = []
        uncached = []
        uncached_indices = []
        
        for i, text in enumerate(texts):
            cached = self.cache.get(text)
            if cached is not None:
                results.append(cached)
            else:
                results.append(None)
                uncached.append(text)
                uncached_indices.append(i)
        
        if uncached:
            embeddings = super().encode_batch(uncached)
            for idx, emb in zip(uncached_indices, embeddings):
                results[idx] = emb
                self.cache.set(uncached[uncached_indices.index(idx)], emb)
        
        return results


def create_embedding_engine(
    model_name: str = "all-MiniLM-L6-v2",
    use_cache: bool = True,
    cache_size: int = 10000,
    **kwargs
) -> ProductionEmbeddingEngine:
    """
    创建Embedding引擎的工厂函数
    
    Args:
        model_name: 模型名称
        use_cache: 是否使用缓存
        cache_size: 缓存大小
        **kwargs: 其他参数
        
    Returns:
        Embedding引擎实例
    """
    if use_cache:
        return CachedEmbeddingEngine(
            model_name=model_name,
            cache_size=cache_size,
            **kwargs
        )
    return ProductionEmbeddingEngine(model_name=model_name, **kwargs)
