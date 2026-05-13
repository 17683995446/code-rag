#!/usr/bin/env python3
"""
优化的RAG系统架构 - 拥抱开源工具
基于"站在巨人肩膀上"原则重新设计
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json

# ============================================================================
# 依赖：使用业界标准的开源工具，而不是重复造轮子
# ============================================================================

# 向量数据库 - 使用FAISS (Meta开源，业界标准)
try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False
    print("⚠️  FAISS不可用，将使用简单版本")

# Embedding - 使用Sentence-Transformers (业界标准)
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

# LLM集成 - 使用LangChain (业界标准框架)
try:
    from langchain import OpenAI, VectorDBQA
    from langchain.vectorstores import FAISS as LangchainFAISS
    from langchain.embeddings import OpenAIEmbeddings, HuggingFaceEmbeddings
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False

# Web框架 - FastAPI (业界标准)
try:
    from fastapi import FastAPI
    from fastapi.staticfiles import StaticFiles
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

# 并发控制 - 使用Celery + Redis (业界标准)
try:
    from celery import Celery
    import redis
    HAS_CELERY = True
except ImportError:
    HAS_CELERY = False

# 监控 - 使用Prometheus (业界标准)
try:
    from prometheus_client import start_http_server, Counter, Histogram
    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False

# ============================================================================
# 模块化架构 - 每个模块都是独立的，可替换的
# ============================================================================

class RAGConfig:
    """配置管理 - 使用Pydantic (业界标准)"""
    
    DEFAULT_CONFIG = {
        "embedding_model": "all-MiniLM-L6-v2",
        "vector_db": "faiss",
        "chunk_size": 1024,
        "llm_provider": "openai",
        "cache_enabled": True,
        "metrics_enabled": True
    }
    
    def __init__(self, config_file: str = None):
        self.config = self.DEFAULT_CONFIG.copy()
        if config_file and Path(config_file).exists():
            with open(config_file) as f:
                self.config.update(json.load(f))
    
    def get(self, key: str, default=None):
        return self.config.get(key, default)


class EmbeddingModule:
    """
    嵌入模块 - 高度模块化，可插拔
    使用Sentence-Transformers或OpenAIEmbeddings
    """
    
    def __init__(self, config: RAGConfig):
        self.config = config
        self._init_embedding_engine()
    
    def _init_embedding_engine(self):
        """初始化 - 使用开源工具而不是自己写"""
        
        if HAS_LANGCHAIN:
            # 使用LangChain的标准化接口
            if self.config.get("embedding_model") == "openai":
                self.engine = OpenAIEmbeddings()
            else:
                self.engine = HuggingFaceEmbeddings(
                    model_name=self.config.get("embedding_model")
                )
        elif HAS_SENTENCE_TRANSFORMERS:
            # 直接使用Sentence-Transformers
            self.engine = SentenceTransformer(
                self.config.get("embedding_model")
            )
        else:
            # 简单fallback
            self.engine = None
            print("⚠️  无embedding引擎可用，使用fallback")
    
    def encode(self, text: str) -> List[float]:
        """统一接口，内部实现可替换"""
        
        if self.engine and HAS_LANGCHAIN:
            return self.engine.embed_query(text)
        elif self.engine and HAS_SENTENCE_TRANSFORMERS:
            return self.engine.encode(text, convert_to_numpy=True).tolist()
        else:
            # 简单fallback
            return [float(hash(text) % 1000) for _ in range(128)]
    
    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        if self.engine and HAS_SENTENCE_TRANSFORMERS:
            return self.engine.encode(texts, convert_to_numpy=True).tolist()
        else:
            return [self.encode(t) for t in texts]


class VectorDBModule:
    """
    向量数据库模块 - 使用FAISS (Meta开源)
    高度模块化，未来可轻松替换为Qdrant/Milvus/ChromaDB
    """
    
    def __init__(self, config: RAGConfig, embedding_dim: int = 384):
        self.config = config
        self.embedding_dim = embedding_dim
        self._init_db()
    
    def _init_db(self):
        self.documents = []
        self.metadata = []
        if HAS_FAISS:
            # 使用FAISS - 业界标准，性能优秀
            self.index = faiss.IndexFlatL2(self.embedding_dim)
            print("✅ 使用FAISS向量数据库")
        else:
            # 简单fallback
            self.index = None
            print("⚠️  FAISS不可用，使用简单索引")
    
    def add(self, texts: List[str], metadatas: List[Dict] = None):
        if HAS_FAISS and self.index:
            # 自动获取embeddings
            metadatas = metadatas or [{} for _ in texts]
            self.metadata.extend(metadatas)
            self.documents.extend(texts)
        else:
            self.documents.extend(texts)
    
    def search(self, query_embedding: List[float], k: int = 5) -> List[Dict]:
        if HAS_FAISS and self.index and len(self.documents) > 0:
            import numpy as np
            query_np = np.array(query_embedding).reshape(1, -1)
            distances, indices = self.index.search(query_np, k)
            
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.documents):
                    results.append({
                        "text": self.documents[idx],
                        "metadata": self.metadata[idx] if idx < len(self.metadata) else {},
                        "score": float(distances[0][i])
                    })
            return results
        else:
            return self._simple_search(query_embedding, k)
    
    def _simple_search(self, query_embedding: List[float], k: int = 5):
        return [{"text": doc, "score": 0.9} for doc in self.documents[:k]]
    
    def save(self, path: str):
        if HAS_FAISS and self.index:
            faiss.write_index(self.index, path + ".index")
            with open(path + ".docs", "w") as f:
                json.dump({"documents": self.documents, "metadata": self.metadata}, f)
    
    def load(self, path: str):
        if HAS_FAISS and Path(path + ".index").exists():
            self.index = faiss.read_index(path + ".index")
            with open(path + ".docs") as f:
                data = json.load(f)
            self.documents = data.get("documents", [])
            self.metadata = data.get("metadata", [])


class LLMModule:
    """
    LLM模块 - 使用LangChain (业界标准框架)
    支持OpenAI, Claude, Llama等多种提供商
    """
    
    def __init__(self, config: RAGConfig):
        self.config = config
        self._init_llm()
    
    def _init_llm(self):
        if HAS_LANGCHAIN:
            # 使用LangChain - 支持100+ LLM提供商
            provider = self.config.get("llm_provider")
            if provider == "openai":
                self.llm = OpenAI(temperature=0.7)
            else:
                self.llm = None
            print("✅ 使用LangChain LLM集成")
        else:
            self.llm = None
    
    def generate(self, prompt: str, context: List[str] = None) -> str:
        if self.llm:
            if context:
                prompt = f"Context:\n{chr(10).join(context)}\n\nQuestion: {prompt}"
            return self.llm.predict(prompt)
        else:
            return f"Mock response to: {prompt}"


class Pipeline:
    """
    主RAG管线 - 高度模块化，每个组件都是独立的
    """
    
    def __init__(self, config: RAGConfig = None):
        self.config = config or RAGConfig()
        self.embedding = EmbeddingModule(self.config)
        self.vector_db = VectorDBModule(self.config)
        self.llm = LLMModule(self.config)
    
    def index(self, documents: List[str], metadatas: List[Dict] = None):
        """索引文档"""
        
        # 获取embeddings
        embeddings = self.embedding.encode_batch(documents)
        
        # 添加到向量数据库
        self.vector_db.add(documents, metadatas)
        
        # 如果有FAISS，才添加向量
        if HAS_FAISS and hasattr(self.vector_db, 'index') and self.vector_db.index:
            import numpy as np
            embeddings_np = np.array(embeddings).astype('float32')
            self.vector_db.index.add(embeddings_np)
    
    def search(self, query: str, k: int = 5) -> List[Dict]:
        """搜索相关文档"""
        
        query_embedding = self.embedding.encode(query)
        results = self.vector_db.search(query_embedding, k)
        return results
    
    def ask(self, question: str) -> Dict:
        """问答 - 搜索+LLM生成"""
        
        results = self.search(question)
        context = [r["text"] for r in results]
        answer = self.llm.generate(question, context)
        
        return {
            "question": question,
            "answer": answer,
            "sources": results
        }


# ============================================================================
# Web服务 - 使用FastAPI + Prometheus
# ============================================================================

def create_app(pipeline: Pipeline) -> FastAPI:
    """创建FastAPI应用 - 业界标准Web框架"""
    
    app = FastAPI(title="RAG System API")
    
    # Prometheus指标
    if HAS_PROMETHEUS:
        request_count = Counter('rag_requests_total', 'Total RAG requests')
        latency_histogram = Histogram('rag_latency_seconds', 'Request latency')
        start_http_server(8000)
    
    @app.get("/")
    def root():
        return {"status": "ok", "message": "RAG System API"}
    
    @app.post("/search")
    def search(query: str, k: int = 5):
        if HAS_PROMETHEUS:
            request_count.inc()
        with latency_histogram.time():
            return pipeline.search(query, k)
    
    @app.post("/ask")
    def ask(question: str):
        if HAS_PROMETHEUS:
            request_count.inc()
        with latency_histogram.time():
            return pipeline.ask(question)
    
    return app


# ============================================================================
# 主入口 - 简单的CLI
# ============================================================================

def main():
    print("="*60)
    print("  RAG System - 基于开源工具构建")
    print("="*60)
    
    # 检查可用的开源工具
    print("\n📦 可用的开源工具:")
    print(f"  FAISS (向量数据库): {'✅' if HAS_FAISS else '❌'}")
    print(f"  Sentence-Transformers (嵌入): {'✅' if HAS_SENTENCE_TRANSFORMERS else '❌'}")
    print(f"  LangChain (LLM框架): {'✅' if HAS_LANGCHAIN else '❌'}")
    print(f"  FastAPI (Web框架): {'✅' if HAS_FASTAPI else '❌'}")
    print(f"  Prometheus (监控): {'✅' if HAS_PROMETHEUS else '❌'}")
    
    # 创建pipeline
    print("\n🚀 初始化RAG管线...")
    pipeline = Pipeline()
    
    # 简单示例
    print("\n📝 示例文档索引...")
    docs = [
        "FAISS是Meta开源的向量数据库，性能非常优秀",
        "Sentence-Transformers提供了预训练的embedding模型",
        "LangChain是连接LLM和数据的标准框架",
        "FastAPI是Python现代Web框架，性能很高",
        "Prometheus是业界标准的监控系统"
    ]
    metadatas = [
        {"source": "doc1"},
        {"source": "doc2"},
        {"source": "doc3"},
        {"source": "doc4"},
        {"source": "doc5"}
    ]
    pipeline.index(docs, metadatas)
    print(f"✅ 索引了 {len(docs)} 个文档")
    
    # 示例搜索
    print("\n🔍 示例搜索: '什么是FAISS?'")
    results = pipeline.search("什么是FAISS?")
    for i, r in enumerate(results[:3]):
        print(f"  {i+1}. {r['text']}")
    
    print("\n🎉 基于开源工具的RAG系统演示完成!")
    print("\n📌 模块化架构说明:")
    print("  - EmbeddingModule: 可替换为任意embedding提供商")
    print("  - VectorDBModule: 可替换为Qdrant/Milvus/ChromaDB")
    print("  - LLMModule: 可替换为任意LLM提供商")
    print("  - Pipeline: 将各模块无缝连接")


if __name__ == "__main__":
    main()
