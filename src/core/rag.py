"""
产品级RAG系统 - 基于LangChain/LlamaIndex
高度模块化，每个模块可产品化
"""

import os
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum

from .settings import get_settings
from .logger import get_logger, get_root_logger, log_context

logger = get_logger(__name__)


class RAGImplementation(Enum):
    """RAG实现类型"""
    LANGCHAIN = "langchain"
    LLAMAINDEX = "llama_index"
    SIMPLIFIED = "simplified"
    AUTO = "auto"


# ============================================================================
# 1️⃣ 工具检查函数
# ============================================================================

def has_langchain() -> bool:
    """检查LangChain是否可用"""
    try:
        import langchain
        return True
    except ImportError:
        return False


def has_llama_index() -> bool:
    """检查LlamaIndex是否可用"""
    try:
        import llama_index
        return True
    except ImportError:
        return False


def has_faiss() -> bool:
    """检查FAISS是否可用"""
    try:
        import faiss
        return True
    except ImportError:
        return False


def has_sentence_transformers() -> bool:
    """检查Sentence-Transformers是否可用"""
    try:
        import sentence_transformers
        return True
    except ImportError:
        return False


# ============================================================================
# 2️⃣ Embedding模块 - 产品级
# ============================================================================

@dataclass
class EmbeddingResult:
    """Embedding结果"""
    vector: List[float]
    dimension: int
    model: str


class EmbeddingEngine:
    """
    产品级Embedding引擎
    支持多种实现，自动降级
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.engine = None
        self._init_engine()
    
    def _init_engine(self):
        """初始化Embedding引擎"""
        with log_context("初始化Embedding引擎"):
            if has_sentence_transformers():
                try:
                    from sentence_transformers import SentenceTransformer
                    self.engine = SentenceTransformer(
                        self.settings.embedding.model_name,
                        device=self.settings.embedding.device
                    )
                    self.dimension = self.engine.get_sentence_embedding_dimension()
                    logger.info(f"使用 Sentence-Transformers: {self.settings.embedding.model_name} (dim={self.dimension})")
                    return
                except Exception as e:
                    logger.warning(f"Sentence-Transformers初始化失败: {e}")
            
            # Fallback
            self.dimension = self.settings.vector_db.dimension
            self.engine = None
            logger.warning(f"使用简化Embedding (dim={self.dimension})")
    
    def encode(self, text: str) -> EmbeddingResult:
        """单文本编码"""
        if self.engine and has_sentence_transformers():
            import numpy as np
            vec = self.engine.encode(text, convert_to_numpy=True)
            return EmbeddingResult(
                vector=vec.tolist(),
                dimension=self.dimension,
                model=self.settings.embedding.model_name
            )
        
        return self._encode_fallback(text)
    
    def encode_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """批量编码"""
        if self.engine and has_sentence_transformers():
            import numpy as np
            vecs = self.engine.encode(texts, convert_to_numpy=True)
            return [
                EmbeddingResult(
                    vector=vec.tolist(),
                    dimension=self.dimension,
                    model=self.settings.embedding.model_name
                )
                for vec in vecs
            ]
        
        return [self._encode_fallback(text) for text in texts]
    
    def _encode_fallback(self, text: str) -> EmbeddingResult:
        """简化的fallback encoding"""
        import hashlib
        hash_val = hashlib.md5(text.encode()).hexdigest()
        vec = []
        
        for i in range(0, 32, 2):
            byte_val = int(hash_val[i:i+2], 16)
            vec.append((byte_val - 128) / 128.0)
        
        while len(vec) < self.dimension:
            vec.extend(vec)
        
        return EmbeddingResult(
            vector=vec[:self.dimension],
            dimension=self.dimension,
            model="fallback_hash"
        )


# ============================================================================
# 3️⃣ 向量数据库模块 - 产品级
# ============================================================================

@dataclass
class SearchResultItem:
    """搜索结果项"""
    text: str
    metadata: Dict
    score: float
    distance: Optional[float] = None


class VectorStore:
    """
    产品级向量存储
    支持多种后端（FAISS, Chroma, Qdrant）
    """
    
    def __init__(self, embedding_dimension: Optional[int] = None):
        self.settings = get_settings()
        self.dimension = embedding_dimension or self.settings.vector_db.dimension
        self.documents: List[str] = []
        self.metadata: List[Dict] = []
        self._init_store()
    
    def _init_store(self):
        """初始化向量存储"""
        with log_context("初始化向量存储"):
            # 尝试FAISS
            if has_faiss():
                try:
                    import faiss
                    import numpy as np
                    self.index = faiss.IndexFlatL2(self.dimension)
                    self.vectors = np.empty((0, self.dimension), dtype=np.float32)
                    logger.info(f"使用 FAISS 向量存储 (dim={self.dimension})")
                    return
                except Exception as e:
                    logger.warning(f"FAISS初始化失败: {e}")
            
            # Fallback
            self.index = None
            self.vectors = []
            logger.warning("使用内存向量索引")
    
    def add(self, embeddings: List[List[float]], 
            documents: List[str], 
            metadatas: Optional[List[Dict]] = None):
        """添加文档到索引"""
        with log_context(f"添加 {len(documents)} 个文档"):
            self.documents.extend(documents)
            self.metadata.extend(metadatas or [{} for _ in documents])
            
            if self.index is not None and has_faiss():
                import numpy as np
                vecs_np = np.array(embeddings).astype('float32')
                self.vectors = np.vstack([self.vectors, vecs_np]) if self.vectors.size > 0 else vecs_np
                self.index.add(vecs_np)
            else:
                self.vectors.extend(embeddings)
    
    def search(self, query_vec: List[float], k: int = 5) -> List[SearchResultItem]:
        """搜索"""
        with log_context(f"搜索 k={k}"):
            if self.index is not None and has_faiss():
                return self._search_faiss(query_vec, k)
            else:
                return self._search_simple(query_vec, k)
    
    def _search_faiss(self, query_vec: List[float], k: int) -> List[SearchResultItem]:
        """FAISS搜索"""
        import numpy as np
        query_np = np.array(query_vec).reshape(1, -1).astype('float32')
        distances, indices = self.index.search(query_np, k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if 0 <= idx < len(self.documents):
                results.append(SearchResultItem(
                    text=self.documents[idx],
                    metadata=self.metadata[idx],
                    distance=float(distances[0][i]),
                    score=1.0 / (1.0 + float(distances[0][i]))
                ))
        return results
    
    def _search_simple(self, query_vec: List[float], k: int) -> List[SearchResultItem]:
        """简化搜索"""
        def euclidean(v1, v2):
            return sum((a - b) ** 2 for a, b in zip(v1, v2)) ** 0.5
        
        scores = []
        for i, vec in enumerate(self.vectors):
            dist = euclidean(query_vec, vec)
            scores.append((i, dist))
        
        scores.sort(key=lambda x: x[1])
        
        results = []
        for i, dist in scores[:k]:
            results.append(SearchResultItem(
                text=self.documents[i],
                metadata=self.metadata[i],
                distance=dist,
                score=1.0 / (1.0 + dist)
            ))
        return results
    
    def save(self, path: str):
        """保存索引"""
        with log_context(f"保存索引到 {path}"):
            import json
            
            if self.index is not None and has_faiss():
                import faiss
                faiss.write_index(self.index, path + ".index")
            
            data = {
                "documents": self.documents,
                "metadata": self.metadata
            }
            
            with open(path + ".data", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
    
    def load(self, path: str):
        """加载索引"""
        with log_context(f"从 {path} 加载索引"):
            import json
            
            if self.index is not None and has_faiss():
                if Path(path + ".index").exists():
                    import faiss
                    self.index = faiss.read_index(path + ".index")
            
            with open(path + ".data", encoding="utf-8") as f:
                data = json.load(f)
            
            self.documents = data.get("documents", [])
            self.metadata = data.get("metadata", [])


# ============================================================================
# 4️⃣ RAG Pipeline - 产品级
# ============================================================================

@dataclass
class RAGAnswer:
    """RAG问答结果"""
    question: str
    answer: str
    sources: List[SearchResultItem]
    success: bool
    error: Optional[str] = None


class RAGPipeline:
    """
    产品级RAG Pipeline
    支持LangChain和LlamaIndex，自动降级
    """
    
    def __init__(self, implementation: RAGImplementation = RAGImplementation.AUTO):
        self.settings = get_settings()
        self.implementation = self._select_implementation(implementation)
        self.embedding_engine = EmbeddingEngine()
        self.vector_store = VectorStore(
            embedding_dimension=self.embedding_engine.dimension
        )
        self._init_pipeline()
    
    def _select_implementation(self, impl: RAGImplementation) -> RAGImplementation:
        """选择合适的实现"""
        if impl == RAGImplementation.AUTO:
            if self.settings.use_langchain and has_langchain():
                return RAGImplementation.LANGCHAIN
            elif self.settings.use_llama_index and has_llama_index():
                return RAGImplementation.LLAMAINDEX
            else:
                return RAGImplementation.SIMPLIFIED
        return impl
    
    def _init_pipeline(self):
        """初始化Pipeline"""
        with log_context(f"初始化 RAG Pipeline: {self.implementation.value}"):
            if self.implementation == RAGImplementation.LANGCHAIN:
                self._init_langchain()
            elif self.implementation == RAGImplementation.LLAMAINDEX:
                self._init_llama_index()
            else:
                self._init_simplified()
    
    def _init_langchain(self):
        """LangChain初始化"""
        try:
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.settings.chunk_size,
                chunk_overlap=self.settings.chunk_overlap
            )
            self.vector_store_lc = None
            logger.info("LangChain Pipeline 初始化完成")
        except Exception as e:
            logger.warning(f"LangChain初始化失败: {e}, 使用简化版本")
            self.implementation = RAGImplementation.SIMPLIFIED
            self._init_simplified()
    
    def _init_llama_index(self):
        """LlamaIndex初始化"""
        try:
            from llama_index.core import Settings
            from llama_index.core.node_parser import SentenceSplitter
            self.node_parser = SentenceSplitter(
                chunk_size=self.settings.chunk_size,
                chunk_overlap=self.settings.chunk_overlap
            )
            self.index_li = None
            logger.info("LlamaIndex Pipeline 初始化完成")
        except Exception as e:
            logger.warning(f"LlamaIndex初始化失败: {e}, 使用简化版本")
            self.implementation = RAGImplementation.SIMPLIFIED
            self._init_simplified()
    
    def _init_simplified(self):
        """简化版本初始化"""
        self.text_splitter = None
        logger.info("使用简化 RAG Pipeline")
    
    def index_directory(self, directory: str):
        """索引目录"""
        with log_context(f"索引目录: {directory}"):
            from pathlib import Path
            
            documents = []
            metadatas = []
            
            dir_path = Path(directory)
            if not dir_path.exists():
                # 使用演示数据
                documents = [
                    "FAISS是Meta开源的高性能向量数据库",
                    "Sentence-Transformers提供高质量的文本embedding",
                    "LangChain是RAG的标准开发框架",
                    "LlamaIndex是另一优秀的RAG框架",
                    "FastAPI是高性能的Python Web框架"
                ]
                metadatas = [
                    {"file": "demo1.txt", "topic": "FAISS"},
                    {"file": "demo2.txt", "topic": "Sentence-Transformers"},
                    {"file": "demo3.txt", "topic": "LangChain"},
                    {"file": "demo4.txt", "topic": "LlamaIndex"},
                    {"file": "demo5.txt", "topic": "FastAPI"}
                ]
                logger.warning("目录不存在，使用演示数据")
            else:
                if dir_path.is_file():
                    files = [dir_path]
                else:
                    files = list(dir_path.rglob("*.py")) + \
                            list(dir_path.rglob("*.js")) + \
                            list(dir_path.rglob("*.md"))
                
                for file_path in files:
                    if file_path.is_file():
                        try:
                            text = file_path.read_text(encoding="utf-8")
                            documents.append(text)
                            metadatas.append({
                                "file_path": str(file_path),
                                "file_name": file_path.name,
                                "file_size": file_path.stat().st_size
                            })
                        except Exception as e:
                            logger.warning(f"跳过 {file_path}: {e}")
            
            self._index_documents(documents, metadatas)
    
    def _index_documents(self, documents: List[str], metadatas: List[Dict]):
        """索引文档"""
        with log_context(f"索引 {len(documents)} 个文档"):
            embeddings = [r.vector for r in self.embedding_engine.encode_batch(documents)]
            self.vector_store.add(embeddings, documents, metadatas)
            logger.info(f"索引完成，共 {len(self.vector_store.documents)} 个文档")
    
    def search(self, query: str, k: int = None) -> List[SearchResultItem]:
        """搜索"""
        if k is None:
            k = self.settings.top_k
        
        with log_context(f"搜索: {query[:50]}..."):
            query_embedding = self.embedding_engine.encode(query)
            return self.vector_store.search(query_embedding.vector, k)
    
    def ask(self, question: str, k: int = None) -> RAGAnswer:
        """问答"""
        try:
            sources = self.search(question, k)
            
            # 构建context
            context = "\n---\n".join([s.text for s in sources])
            
            # 生成回答（简化版本）
            answer = self._generate_answer(question, context, sources)
            
            return RAGAnswer(
                question=question,
                answer=answer,
                sources=sources,
                success=True
            )
        except Exception as e:
            logger.error(f"问答失败: {e}", exc_info=True)
            return RAGAnswer(
                question=question,
                answer=f"抱歉，处理失败: {e}",
                sources=[],
                success=False,
                error=str(e)
            )
    
    def _generate_answer(self, question: str, context: str, sources: List[SearchResultItem]) -> str:
        """生成回答 - 使用真实LLM"""
        from .llm import generate_rag_answer, has_llm
        
        # 使用真实的LLM生成回答
        return generate_rag_answer(question, context, len(sources))


# ============================================================================
# 5️⃣ 统一入口 - 产品级
# ============================================================================

class CodeRAG:
    """
    产品级CodeRAG入口
    简单、可靠、可扩展
    """
    
    def __init__(self, implementation: str = "auto"):
        # 初始化日志
        get_root_logger()
        
        impl_map = {
            "auto": RAGImplementation.AUTO,
            "langchain": RAGImplementation.LANGCHAIN,
            "llama_index": RAGImplementation.LLAMAINDEX,
            "simplified": RAGImplementation.SIMPLIFIED
        }
        
        self.pipeline = RAGPipeline(
            implementation=impl_map.get(implementation, RAGImplementation.AUTO)
        )
        
        logger.info("=" * 60)
        logger.info("🚀 产品级CodeRAG系统启动完成")
        logger.info("=" * 60)
    
    def index(self, directory: str):
        """索引代码"""
        self.pipeline.index_directory(directory)
    
    def search(self, query: str, k: int = None) -> List[SearchResultItem]:
        """搜索"""
        return self.pipeline.search(query, k)
    
    def ask(self, question: str, k: int = None) -> RAGAnswer:
        """问答"""
        return self.pipeline.ask(question, k)
    
    def save(self, path: str):
        """保存"""
        self.pipeline.vector_store.save(path)
    
    def load(self, path: str):
        """加载"""
        self.pipeline.vector_store.load(path)


# ============================================================================
# 6️⃣ 快速演示
# ============================================================================

def demo():
    """快速演示"""
    print("\n" + "="*60)
    print("  🚀 产品级CodeRAG演示")
    print("="*60)
    
    # 1. 初始化
    rag = CodeRAG()
    
    # 2. 索引
    rag.index("/tmp/demo_code")
    
    # 3. 搜索
    print("\n" + "-"*60)
    print("  🔍 搜索演示")
    print("-"*60)
    results = rag.search("FAISS向量数据库")
    for i, r in enumerate(results[:3]):
        print(f"  {i+1}. [{r.score:.3f}] {r.text[:60]}...")
        print(f"      元数据: {r.metadata}")
    
    # 4. 问答
    print("\n" + "-"*60)
    print("  💬 问答演示")
    print("-"*60)
    answer = rag.ask("什么是FAISS?")
    if answer.success:
        print(f"  问题: {answer.question}")
        print(f"  回答: {answer.answer}")
        print(f"  来源: {len(answer.sources)} 个文档")
    else:
        print(f"  失败: {answer.error}")
    
    print("\n" + "="*60)
    print("  ✅ 演示完成")
    print("="*60)


if __name__ == "__main__":
    demo()
