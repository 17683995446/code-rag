"""
REST API Endpoints Module
Provides comprehensive REST API endpoints for Code RAG
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

# 尝试导入 fastapi
try:
    from fastapi import FastAPI, HTTPException, Request, status
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    # 提供备用类
    class BaseModel:
        pass
    
    def Field(*args, **kwargs):
        return None

# 尝试导入 uvicorn
try:
    import uvicorn
    UVICORN_AVAILABLE = True
except ImportError:
    UVICORN_AVAILABLE = False

try:
    from ..base_layer import get_logger
    from ..rag_engine import CodeRAG, get_test_documents
    from ..observability_layer import get_prometheus_metrics
    logger = get_logger("api")
except ImportError:
    import logging
    logger = logging.getLogger("api")


class QueryRequest(BaseModel):
    """Query request model"""
    if FASTAPI_AVAILABLE:
        query: str = Field(..., description="Search query text")
        top_k: int = Field(default=5, ge=1, le=20, description="Number of results to return")
        include_sources: bool = Field(default=True, description="Include source metadata")
        include_embeddings: bool = Field(default=False, description="Include embedding vectors")
    else:
        # 备用实现
        def __init__(self, query: str, top_k: int = 5, **kwargs):
            self.query = query
            self.top_k = top_k
            self.include_sources = kwargs.get('include_sources', True)
            self.include_embeddings = kwargs.get('include_embeddings', False)


class QueryResponse(BaseModel):
    """Query response model"""
    if FASTAPI_AVAILABLE:
        query: str
        answers: List[Dict[str, Any]]
        sources: List[Dict[str, Any]]
        performance: Dict[str, float]
        timestamp: datetime
    else:
        # 备用实现
        def __init__(self, query: str, answers: List[Dict[str, Any]], 
                     sources: List[Dict[str, Any]], performance: Dict[str, float],
                     timestamp: datetime):
            self.query = query
            self.answers = answers
            self.sources = sources
            self.performance = performance
            self.timestamp = timestamp


class DocumentAddRequest(BaseModel):
    """Document add request model"""
    if FASTAPI_AVAILABLE:
        content: str = Field(..., description="Document content")
        metadata: Optional[Dict[str, Any]] = Field(default=None, description="Document metadata")
    else:
        # 备用实现
        def __init__(self, content: str, metadata: Optional[Dict[str, Any]] = None):
            self.content = content
            self.metadata = metadata or {}


class DocumentAddResponse(BaseModel):
    """Document add response model"""
    if FASTAPI_AVAILABLE:
        document_id: str
        chunks: int
        timestamp: datetime
        success: bool
    else:
        # 备用实现
        def __init__(self, document_id: str, chunks: int, 
                     timestamp: datetime, success: bool):
            self.document_id = document_id
            self.chunks = chunks
            self.timestamp = timestamp
            self.success = success


class HealthResponse(BaseModel):
    """Health check response model"""
    if FASTAPI_AVAILABLE:
        status: str
        version: str
        timestamp: datetime
        uptime: float
        modules: List[str]
    else:
        # 备用实现
        def __init__(self, status: str, version: str, 
                     timestamp: datetime, uptime: float,
                     modules: List[str]):
            self.status = status
            self.version = version
            self.timestamp = timestamp
            self.uptime = uptime
            self.modules = modules


class StatsResponse(BaseModel):
    """Statistics response model"""
    if FASTAPI_AVAILABLE:
        total_documents: int
        total_chunks: int
        total_queries: int
        avg_response_time: float
        success_rate: float
        cache_hit_rate: float
    else:
        # 备用实现
        def __init__(self, total_documents: int, total_chunks: int, 
                     total_queries: int, avg_response_time: float,
                     success_rate: float, cache_hit_rate: float):
            self.total_documents = total_documents
            self.total_chunks = total_chunks
            self.total_queries = total_queries
            self.avg_response_time = avg_response_time
            self.success_rate = success_rate
            self.cache_hit_rate = cache_hit_rate


def create_rest_api_app(rag: Optional[CodeRAG] = None) -> Any:
    """Create REST API application"""
    if not FASTAPI_AVAILABLE:
        print("⚠️ fastapi not available, returning None")
        return None
    
    app = FastAPI(
        title="Code RAG API",
        description="Production-ready Retrieval Augmented Generation System",
        version="5.0.0"
    )
    
    if rag is None:
        rag = CodeRAG()
        rag.add_documents(get_test_documents())
    
    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint"""
        return {
            "name": "Code RAG API",
            "version": "5.0.0",
            "status": "running",
            "endpoints": [
                "/health",
                "/stats",
                "/query",
                "/documents",
                "/docs"
            ]
        }
    
    @app.get("/health", response_model=HealthResponse, tags=["health"])
    async def health():
        """Health check endpoint"""
        uptime = 0.0
        modules = ["base_layer", "data_layer", "search_layer", 
                  "rag_engine", "service_layer", "middleware_layer",
                  "observability_layer", "api_layer"]
        return HealthResponse(
            status="healthy",
            version="5.0.0",
            timestamp=datetime.now(),
            uptime=uptime,
            modules=modules
        )
    
    @app.get("/stats", response_model=StatsResponse, tags=["stats"])
    async def stats():
        """Statistics endpoint"""
        return StatsResponse(
            total_documents=len(rag.documents) if hasattr(rag, 'documents') else 0,
            total_chunks=0,
            total_queries=0,
            avg_response_time=0.0,
            success_rate=1.0,
            cache_hit_rate=0.0
        )
    
    @app.post("/query", response_model=QueryResponse, tags=["query"])
    async def query(request: QueryRequest):
        """Query endpoint"""
        import time
        start_time = time.time()
        results = rag.search(request.query, request.top_k)
        answer = rag.query(request.query, request.top_k)
        
        sources = []
        answers = []
        
        if hasattr(answer, '__str__'):
            answers.append({"text": str(answer), "score": 1.0})
        
        performance = {
            "response_time": time.time() - start_time,
            "sources_count": len(results)
        }
        
        return QueryResponse(
            query=request.query,
            answers=answers,
            sources=sources,
            performance=performance,
            timestamp=datetime.now()
        )
    
    @app.post("/documents", response_model=DocumentAddResponse, tags=["documents"])
    async def add_document(request: DocumentAddRequest):
        """Add document endpoint"""
        doc_id = str(len(rag.documents) if hasattr(rag, 'documents') else 0)
        rag.add_documents([request.content])
        
        return DocumentAddResponse(
            document_id=doc_id,
            chunks=1,
            timestamp=datetime.now(),
            success=True
        )
    
    return app


def run_rest_api(host: str = "0.0.0.0", port: int = 8000):
    """Run REST API server"""
    if not FASTAPI_AVAILABLE:
        print("❌ fastapi not available, cannot start server")
        return False
    
    if not UVICORN_AVAILABLE:
        print("❌ uvicorn not available, cannot start server")
        return False
    
    app = create_rest_api_app()
    if app is None:
        return False
    
    print(f"🚀 Starting API server at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)
    return True
