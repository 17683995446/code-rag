"""
FastAPI服务 - 产品级API
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from pathlib import Path

from src.core import (
    CodeRAG,
    get_settings,
    get_root_logger,
    log_context
)


# 初始化
app = FastAPI(title="Code RAG API", version="1.0.0")
logger = get_root_logger()

# RAG实例
_rag: Optional[CodeRAG] = None


def get_rag() -> CodeRAG:
    """获取RAG单例"""
    global _rag
    if _rag is None:
        _rag = CodeRAG()
    return _rag


# Pydantic模型
class SearchRequest(BaseModel):
    query: str = Field(..., description="搜索查询")
    k: int = Field(default=5, ge=1, le=100, description="返回结果数")


class SearchResult(BaseModel):
    text: str
    metadata: Dict[str, Any]
    score: float
    distance: Optional[float] = None


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total: int


class AskRequest(BaseModel):
    question: str = Field(..., description="问题")
    k: int = Field(default=5, ge=1, le=100, description="上下文文档数")


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: List[SearchResult]
    success: bool
    error: Optional[str] = None


class IndexRequest(BaseModel):
    directory: str = Field(..., description="要索引的目录路径")


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"


# 路由
@app.get("/health", response_model=HealthResponse)
def health():
    """健康检查"""
    return HealthResponse()


@app.post("/search", response_model=SearchResponse)
def search(request: SearchRequest, rag: CodeRAG = Depends(get_rag)):
    """搜索"""
    with log_context(f"API搜索: {request.query[:50]}"):
        try:
            results = rag.search(request.query, request.k)
            return SearchResponse(
                query=request.query,
                results=[SearchResult(
                    text=r.text,
                    metadata=r.metadata,
                    score=r.score,
                    distance=r.distance
                ) for r in results],
                total=len(results)
            )
        except Exception as e:
            logger.error(f"搜索失败: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest, rag: CodeRAG = Depends(get_rag)):
    """问答"""
    with log_context(f"API问答: {request.question[:50]}"):
        try:
            answer = rag.ask(request.question, request.k)
            return AskResponse(
                question=answer.question,
                answer=answer.answer,
                sources=[SearchResult(
                    text=s.text,
                    metadata=s.metadata,
                    score=s.score,
                    distance=s.distance
                ) for s in answer.sources],
                success=answer.success,
                error=answer.error
            )
        except Exception as e:
            logger.error(f"问答失败: {e}", exc_info=True)
            return AskResponse(
                question=request.question,
                answer=f"处理失败: {e}",
                sources=[],
                success=False,
                error=str(e)
            )


@app.post("/index")
def index(request: IndexRequest, rag: CodeRAG = Depends(get_rag)):
    """索引目录"""
    with log_context(f"API索引: {request.directory}"):
        try:
            rag.index(request.directory)
            return {"status": "success", "directory": request.directory}
        except Exception as e:
            logger.error(f"索引失败: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))


def start_api(host: str = "0.0.0.0", port: int = 8000):
    """启动API服务"""
    import uvicorn
    
    settings = get_settings()
    host = host or settings.api.host
    port = port or settings.api.port
    
    logger.info(f"启动API服务: {host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_api()
