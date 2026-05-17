"""
Code RAG v16.0 - FastAPI Web应用
现代化Web界面后端
"""

import sys
import json
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# 导入核心模块
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code_rag.data_layer.code_parser_and_document_processor import CodeParser
from code_rag.search_layer.bm25_search_engine import BM25Index
from code_rag.processing_layer.code_intelligence_and_semantic_understanding import (
    analyze_code_intelligence
)
from code_rag.search_layer.nl2code_converter import nl2code
from code_rag.processing_layer.code_dependency_analyzer import analyze_dependencies


# ============= Pydantic 模型 =============

class IndexRequest(BaseModel):
    directory: str = Field(..., description="要索引的目录路径")


class SearchRequest(BaseModel):
    query: str = Field(..., description="搜索查询")
    top_k: int = Field(default=10, ge=1, le=50, description="返回结果数量")


class NL2CodeRequest(BaseModel):
    query: str = Field(..., description="自然语言查询")


class AnalyzeRequest(BaseModel):
    code: str = Field(..., description="要分析的代码")


class DependenciesRequest(BaseModel):
    directory: str = Field(..., description="要分析的目录")


# ============= Web App =============

app = FastAPI(
    title="Code RAG v16.0 - 智能代码检索系统",
    description="现代化Web界面，提供智能代码检索、分析和可视化",
    version="16.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============= 全局状态 =============

class AppState:
    def __init__(self):
        self.parser = CodeParser()
        self.search_index = BM25Index()
        self.is_indexed = False
        self.indexed_directory = ""
        self.index_stats = {}
        self.indexed_chunks = []
        
        self.index_time = None
        self.last_search_time = None
        self.search_history = []


state = AppState()


# ============= 路由 =============

@app.get("/")
async def root():
    """根路径，返回系统信息"""
    return {
        "name": "Code RAG v16.0 - 智能代码检索系统",
        "version": "16.0.0",
        "status": "online",
        "indexed": state.is_indexed,
        "indexed_directory": state.indexed_directory,
        "api_docs": "/docs"
    }


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "16.0.0"
    }


@app.get("/api/stats")
async def get_stats():
    """获取系统统计信息"""
    return {
        "indexed": state.is_indexed,
        "directory": state.indexed_directory,
        "stats": state.index_stats,
        "index_time": state.index_time.isoformat() if state.index_time else None,
        "total_chunks": len(state.indexed_chunks)
    }


@app.post("/api/index")
async def index_directory(request: IndexRequest):
    """索引代码目录"""
    start_time = time.time()
    
    directory = Path(request.directory)
    if not directory.exists():
        raise HTTPException(status_code=404, detail=f"目录不存在: {request.directory}")
    
    state.is_indexed = False
    state.indexed_chunks = []
    
    print(f"🚀 开始索引: {directory}")
    
    try:
        files_processed = 0
        all_chunks = []
        
        for py_file in directory.rglob("*.py"):
            if any(skip in str(py_file) for skip in ['__pycache__', '.git', 'venv', '.venv', 'test', 'tests']):
                continue
            
            try:
                doc = state.parser.parse_file(str(py_file))
                for chunk in doc.chunks:
                    if len(chunk.content) >= 30:
                        all_chunks.append(chunk.content)
                        state.indexed_chunks.append({
                            "content": chunk.content,
                            "file": str(py_file),
                            "type": chunk.chunk_type,
                            "start_line": chunk.line_start,
                            "end_line": chunk.line_end
                        })
                files_processed += 1
            except Exception as e:
                print(f"⚠️ 处理文件 {py_file} 失败: {e}")
        
        if all_chunks:
            state.search_index.add_documents(all_chunks)
            state.is_indexed = True
            state.indexed_directory = request.directory
            
            state.index_stats = {
                "files_processed": files_processed,
                "chunks_indexed": len(all_chunks),
                "total_files": len(list(directory.rglob("*.py"))),
                "elapsed_seconds": time.time() - start_time
            }
            state.index_time = datetime.now()
            
            print(f"✅ 索引完成: {files_processed} 文件, {len(all_chunks)} 代码块, 耗时 {state.index_stats['elapsed_seconds']:.2f}s")
            
            return {
                "success": True,
                "directory": request.directory,
                "files_processed": files_processed,
                "chunks_indexed": len(all_chunks),
                "elapsed_seconds": state.index_stats['elapsed_seconds']
            }
        else:
            raise HTTPException(status_code=400, detail="没有找到可索引的Python文件")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"索引失败: {str(e)}")


@app.post("/api/search")
async def search_code(request: SearchRequest):
    """搜索代码"""
    if not state.is_indexed:
        raise HTTPException(status_code=400, detail="请先索引代码目录")
    
    start_time = time.time()
    
    try:
        results = state.search_index.search(request.query, k=request.top_k)
        
        formatted_results = []
        for i, result in enumerate(results):
            chunk_info = state.indexed_chunks[i] if i < len(state.indexed_chunks) else {}
            formatted_results.append({
                "rank": i + 1,
                "score": float(result.get("score", 0.0)),
                "text": result.get("text", ""),
                "file": chunk_info.get("file", ""),
                "type": chunk_info.get("type", ""),
                "line_start": chunk_info.get("start_line", 0),
                "line_end": chunk_info.get("end_line", 0),
                "preview": result.get("text", "")[:300] + "..." if len(result.get("text", "")) > 300 else result.get("text", "")
            })
        
        state.last_search_time = datetime.now()
        state.search_history.append({
            "query": request.query,
            "timestamp": datetime.now().isoformat(),
            "results_count": len(formatted_results)
        })
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        return {
            "success": True,
            "query": request.query,
            "results": formatted_results,
            "total_results": len(formatted_results),
            "elapsed_ms": elapsed_ms
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@app.post("/api/nl2code")
async def nl2code_convert(request: NL2CodeRequest):
    """自然语言转代码搜索"""
    try:
        result = nl2code(request.query)
        
        return {
            "success": True,
            "query": request.query,
            "intent": result.get("intent", ""),
            "confidence": float(result.get("confidence", 0.0)),
            "search_queries": result.get("search_queries", []),
            "tags": result.get("tags", [])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NL2Code转换失败: {str(e)}")


@app.post("/api/analyze")
async def analyze_code(request: AnalyzeRequest):
    """分析代码"""
    try:
        result = analyze_code_intelligence(request.code)
        
        return {
            "success": True,
            "detected_language": result.get("detected_language", ""),
            "intent": result.get("intent", {}),
            "tags": result.get("tags", []),
            "summary": result.get("summary", {})
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"代码分析失败: {str(e)}")


@app.post("/api/dependencies")
async def get_dependencies(request: DependenciesRequest):
    """获取代码依赖分析"""
    try:
        result = analyze_dependencies(request.directory)
        
        return {
            "success": True,
            "directory": request.directory,
            "statistics": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"依赖分析失败: {str(e)}")


@app.get("/api/history")
async def get_search_history(limit: int = Query(default=20, ge=1, le=100)):
    """获取搜索历史"""
    return {
        "history": state.search_history[-limit:],
        "total": len(state.search_history)
    }


# ============= 启动服务器 =============

def run_server(host: str = "0.0.0.0", port: int = 8000):
    """运行Web服务器"""
    import uvicorn
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   🧠  Code RAG v16.0 - Web界面                            ║
║                                                           ║
║   服务器运行中: http://{host}:{port}                     ║
║   API文档: http://{host}:{port}/docs                     ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
