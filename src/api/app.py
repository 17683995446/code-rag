"""
FastAPI服务 - 产品级 (增强版)
支持监控、指标、健康检查
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from pathlib import Path
import time

from src.core import (
    CodeRAG,
    get_settings,
    get_root_logger,
    log_context,
    get_monitor,
    PerformanceMonitor,
    get_prometheus_metrics,
    PrometheusMetrics
)


app = FastAPI(
    title="Code RAG API",
    version="3.1.0",
    description="产品级代码检索增强生成系统"
)

logger = get_root_logger()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_rag: Optional[CodeRAG] = None
_monitor: Optional[PerformanceMonitor] = None
_prom: Optional[PrometheusMetrics] = None


def get_rag() -> CodeRAG:
    """获取RAG单例"""
    global _rag
    if _rag is None:
        _rag = CodeRAG()
    return _rag


def get_performance_monitor() -> PerformanceMonitor:
    """获取性能监控器"""
    global _monitor
    if _monitor is None:
        _monitor = get_monitor()
    return _monitor


def get_prom_metrics() -> PrometheusMetrics:
    """获取Prometheus指标"""
    global _prom
    if _prom is None:
        _prom = get_prometheus_metrics()
    return _prom


class SearchRequest(BaseModel):
    query: str = Field(..., description="搜索查询", min_length=1)
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
    duration_ms: float


class AskRequest(BaseModel):
    question: str = Field(..., description="问题", min_length=1)
    k: int = Field(default=5, ge=1, le=100, description="上下文文档数")


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: List[SearchResult]
    success: bool
    error: Optional[str] = None
    duration_ms: float


class IndexRequest(BaseModel):
    directory: str = Field(..., description="要索引的目录路径")


class IndexResponse(BaseModel):
    status: str
    directory: str
    duration_ms: float


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "3.0.0"
    timestamp: str


class MetricsResponse(BaseModel):
    timestamp: str
    system: Dict[str, Any]
    process: Dict[str, Any]
    operations: Dict[str, Any]


class PerformanceReportResponse(BaseModel):
    report: Dict[str, Any]


@app.get("/", response_model=Dict[str, str])
def root():
    """根路径"""
    return {
        "service": "Code RAG API",
        "version": "3.0.0",
        "status": "running"
    }


@app.get("/health", response_model=HealthResponse)
def health():
    """健康检查"""
    return HealthResponse(timestamp=time.strftime("%Y-%m-%d %H:%M:%S"))


@app.get("/metrics", response_model=MetricsResponse)
def metrics(monitor: PerformanceMonitor = Depends(get_performance_monitor)):
    """获取性能指标"""
    monitor.record_system_metrics()
    stats = monitor.metrics.get_all_stats()

    return MetricsResponse(
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        system={
            'cpu_percent': monitor.metrics.get_gauge('system.cpu.percent'),
            'memory_percent': monitor.metrics.get_gauge('system.memory.percent')
        },
        process={
            'cpu_user': monitor.metrics.get_gauge('process.cpu.user'),
            'cpu_system': monitor.metrics.get_gauge('process.cpu.system'),
            'memory_rss_mb': monitor.metrics.get_gauge('process.memory.rss_mb'),
            'threads': monitor.metrics.get_gauge('process.threads')
        },
        operations=stats['operations']
    )


@app.get("/performance", response_model=PerformanceReportResponse)
def performance_report(monitor: PerformanceMonitor = Depends(get_performance_monitor)):
    """获取性能报告"""
    report = monitor.get_performance_report()
    return PerformanceReportResponse(report=report)


@app.get("/prometheus")
def prometheus_metrics(prom: PrometheusMetrics = Depends(get_prom_metrics)):
    """获取Prometheus格式指标"""
    from fastapi.responses import PlainTextResponse
    metrics_text = prom.get_metrics_text()
    return PlainTextResponse(content=metrics_text, media_type="text/plain")


@app.post("/search", response_model=SearchResponse)
def search(request: SearchRequest, rag: CodeRAG = Depends(get_rag)):
    """搜索"""
    start_time = time.time()

    with log_context(f"API搜索: {request.query[:50]}"):
        try:
            results = rag.search(request.query, request.k)
            duration = (time.time() - start_time) * 1000

            return SearchResponse(
                query=request.query,
                results=[SearchResult(
                    text=r.text,
                    metadata=r.metadata,
                    score=r.score,
                    distance=r.distance
                ) for r in results],
                total=len(results),
                duration_ms=round(duration, 2)
            )
        except Exception as e:
            logger.error(f"搜索失败: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest, rag: CodeRAG = Depends(get_rag)):
    """问答"""
    start_time = time.time()

    with log_context(f"API问答: {request.question[:50]}"):
        try:
            answer = rag.ask(request.question, request.k)
            duration = (time.time() - start_time) * 1000

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
                error=answer.error,
                duration_ms=round(duration, 2)
            )
        except Exception as e:
            logger.error(f"问答失败: {e}", exc_info=True)
            return AskResponse(
                question=request.question,
                answer=f"处理失败: {e}",
                sources=[],
                success=False,
                error=str(e),
                duration_ms=round((time.time() - start_time) * 1000, 2)
            )


@app.post("/index", response_model=IndexResponse)
def index(request: IndexRequest, rag: CodeRAG = Depends(get_rag)):
    """索引目录"""
    start_time = time.time()

    with log_context(f"API索引: {request.directory}"):
        try:
            rag.index(request.directory)
            duration = (time.time() - start_time) * 1000

            return IndexResponse(
                status="success",
                directory=request.directory,
                duration_ms=round(duration, 2)
            )
        except Exception as e:
            logger.error(f"索引失败: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
def stats(monitor: PerformanceMonitor = Depends(get_performance_monitor)):
    """获取统计信息"""
    monitor.record_system_metrics()
    all_stats = monitor.metrics.get_all_stats()

    return {
        "counters": all_stats['counters'],
        "gauges": {
            k: v for k, v in all_stats['gauges'].items()
            if any(keyword in k for keyword in ['system', 'process'])
        }
    }


def start_api(host: str = "0.0.0.0", port: int = 8000):
    """启动API服务"""
    import uvicorn

    settings = get_settings()
    host = host or settings.api.host
    port = port or settings.api.port

    logger.info(f"启动API服务: {host}:{port}")
    logger.info(f"文档地址: http://{host}:{port}/docs")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    start_api()
