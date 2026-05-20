#!/usr/bin/env python3
"""
知识图谱记忆系统 v6.0 - REST API Server (企业级)
包含完整的REST API、文档和SDK示例
"""
import sys
import os
import json
import time
import uuid
import tempfile
from typing import Dict, List, Any, Optional
from datetime import datetime

# FastAPI imports
try:
    from fastapi import FastAPI, HTTPException, Query
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    from pydantic import BaseModel, Field
    import uvicorn
except ImportError:
    print("⚠️ FastAPI dependencies not found. Installing...")
    os.system(f"{sys.executable} -m pip install fastapi uvicorn pydantic")
    from fastapi import FastAPI, HTTPException, Query
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import HTMLResponse, JSONResponse
    from pydantic import BaseModel, Field
    import uvicorn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kg_memory_v6 import (
    MemorySystemV6,
    NodeType,
    EdgeType
)


# ============================================
# Pydantic Models for API
# ============================================

class NodeCreate(BaseModel):
    label: str = Field(..., description="节点标签/名称")
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict, description="节点属性")
    type: Optional[str] = Field(default="entity", description="节点类型")


class EdgeCreate(BaseModel):
    source: str = Field(..., description="源节点标签或ID")
    target: str = Field(..., description="目标节点标签或ID")
    relation: Optional[str] = Field(default="related_to", description="关系类型")
    weight: Optional[float] = Field(default=1.0, description="权重")
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict, description="边属性")


class RecallQuery(BaseModel):
    query: str = Field(..., description="搜索查询")
    k: Optional[int] = Field(default=20, ge=1, le=1000, description="返回结果数量")


class InferQuery(BaseModel):
    concept: str = Field(..., description="起始概念")
    max_depth: Optional[int] = Field(default=3, ge=1, le=10, description="最大深度")


# ============================================
# API Server
# ============================================

app = FastAPI(
    title="知识图谱记忆系统 v6.0 API",
    description="企业级知识图谱平台 - 完整的REST API文档",
    version="6.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global memory system instance
db_path = os.path.join(tempfile.mkdtemp(), "kg_v6_api.db")
memory_system = MemorySystemV6(db_path)


# ============================================
# API Endpoints
# ============================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """主页 - API介绍"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>知识图谱记忆系统 v6.0 API</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-width: 900px;
                margin: 0 auto;
                padding: 40px 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container {
                background: white;
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }
            h1 {
                color: #2d3748;
                margin-bottom: 10px;
            }
            .version {
                color: #667eea;
                font-size: 24px;
                font-weight: bold;
            }
            .feature-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }
            .feature {
                background: #f7fafc;
                padding: 20px;
                border-radius: 10px;
                border-left: 4px solid #667eea;
            }
            .feature h3 {
                margin: 0 0 10px 0;
                color: #2d3748;
            }
            .cta-button {
                display: inline-block;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px 30px;
                border-radius: 10px;
                text-decoration: none;
                font-weight: bold;
                margin: 10px;
                transition: transform 0.2s;
            }
            .cta-button:hover {
                transform: translateY(-2px);
            }
            .stats {
                background: #edf2f7;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧠 知识图谱记忆系统</h1>
            <div class="version">v6.0 - 企业版</div>
            
            <div class="feature-grid">
                <div class="feature">
                    <h3>💾 数据库持久化</h3>
                    <p>SQLite 数据库支持，数据可靠持久化</p>
                </div>
                <div class="feature">
                    <h3>⚡ 高性能</h3>
                    <p>内存-数据库混合缓存，毫秒级响应</p>
                </div>
                <div class="feature">
                    <h3>🧠 高级分析</h3>
                    <p>PageRank, 社区发现, 中心性分析</p>
                </div>
                <div class="feature">
                    <h3>🔗 REST API</h3>
                    <p>完整的 REST API，易于集成</p>
                </div>
            </div>
            
            <div class="stats" id="stats">
                加载中...
            </div>
            
            <div style="text-align: center;">
                <a href="/docs" class="cta-button">📚 API 文档</a>
                <a href="/redoc" class="cta-button">📖 Redoc 文档</a>
            </div>
        </div>
        
        <script>
            async function loadStats() {
                try {
                    const response = await fetch('/stats');
                    const stats = await response.json();
                    document.getElementById('stats').innerHTML = `
                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; text-align: center;">
                            <div>
                                <div style="font-size: 36px; font-weight: bold; color: #667eea;">${stats.nodes}</div>
                                <div>节点</div>
                            </div>
                            <div>
                                <div style="font-size: 36px; font-weight: bold; color: #764ba2;">${stats.edges}</div>
                                <div>边</div>
                            </div>
                            <div>
                                <div style="font-size: 36px; font-weight: bold; color: #48bb78;">${stats.cache ? stats.cache.hit_rate.toFixed(1) : 0}%</div>
                                <div>缓存命中率</div>
                            </div>
                        </div>
                    `;
                } catch(e) {
                    console.error(e);
                }
            }
            loadStats();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/nodes", tags=["知识管理"])
async def create_node(node: NodeCreate):
    """创建新节点"""
    try:
        node_type = NodeType(node.type) if node.type in [e.value for e in NodeType] else NodeType.ENTITY
        node_id = memory_system.remember(node.label, node.properties, node_type)
        return {"success": True, "node_id": node_id, "label": node.label}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/edges", tags=["知识管理"])
async def create_edge(edge: EdgeCreate):
    """创建新的关系边"""
    try:
        edge_id = memory_system.connect(
            edge.source,
            edge.target,
            edge.relation,
            edge.weight
        )
        return {"success": True, "edge_id": edge_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/recall", tags=["知识检索"])
async def recall_knowledge(query: RecallQuery):
    """检索知识"""
    try:
        results = memory_system.recall(query.query, query.k)
        return {"success": True, "count": len(results), "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/recall/{query}", tags=["知识检索"])
async def recall_knowledge_get(query: str, k: int = 20):
    """检索知识 (GET 方法)"""
    try:
        results = memory_system.recall(query, k)
        return {"success": True, "count": len(results), "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/infer", tags=["知识推理"])
async def infer_knowledge(query: InferQuery):
    """基于图进行推理"""
    try:
        results = memory_system.infer(query.concept, query.max_depth)
        return {"success": True, "count": len(results), "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/infer/{concept}", tags=["知识推理"])
async def infer_knowledge_get(concept: str, max_depth: int = 3):
    """知识推理 (GET 方法)"""
    try:
        results = memory_system.infer(concept, max_depth)
        return {"success": True, "count": len(results), "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", tags=["系统信息"])
async def get_statistics():
    """获取系统统计信息"""
    try:
        stats = memory_system.get_statistics()
        return {"success": True, **stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics", tags=["高级分析"])
async def get_analytics():
    """获取高级图分析结果"""
    try:
        analytics = memory_system.get_analytics()
        return {"success": True, **analytics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/centrality", tags=["高级分析"])
async def get_centrality():
    """获取度中心性"""
    try:
        centrality = memory_system.analytics.calculate_degree_centrality()
        return {"success": True, "centrality": centrality}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/pagerank", tags=["高级分析"])
async def get_pagerank():
    """获取PageRank"""
    try:
        pagerank = memory_system.analytics.pagerank()
        return {"success": True, "pagerank": pagerank}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/communities", tags=["高级分析"])
async def get_communities():
    """获取社区发现"""
    try:
        communities = memory_system.analytics.find_communities()
        return {"success": True, "communities": communities}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/export", tags=["数据管理"])
async def export_graph():
    """导出知识图谱为JSON"""
    try:
        graph_json = memory_system.export_graph_json()
        return JSONResponse(content=json.loads(graph_json))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/clear", tags=["数据管理"])
async def clear_all():
    """清空所有数据（谨慎使用！）"""
    try:
        memory_system.clear()
        return {"success": True, "message": "All data cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/demo", tags=["演示"])
async def run_demo():
    """运行演示 - 创建示例知识图谱"""
    try:
        entities = ["Python", "JavaScript", "FastAPI", "Flask", "Django",
                   "React", "Vue", "Angular", "TypeScript", "Node.js",
                   "SQL", "MongoDB", "Redis", "PostgreSQL", "GraphQL"]
        
        for entity in entities:
            memory_system.remember(entity, {"category": "technology"})
        
        relations = [
            ("Python", "FastAPI", "related_to"),
            ("Python", "Flask", "related_to"),
            ("Python", "Django", "related_to"),
            ("JavaScript", "React", "related_to"),
            ("JavaScript", "Vue", "related_to"),
            ("TypeScript", "Angular", "related_to"),
            ("FastAPI", "SQL", "uses"),
            ("FastAPI", "MongoDB", "uses"),
            ("FastAPI", "GraphQL", "related_to"),
            ("React", "Node.js", "uses"),
            ("Vue", "Node.js", "uses")
        ]
        
        for source, target, rel in relations:
            memory_system.connect(source, target, rel)
        
        stats = memory_system.get_statistics()
        return {"success": True, "message": "Demo graph created", "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# SDK Example (Python)
# ============================================

class KGMemorySDK:
    """
    知识图谱记忆系统 v6.0 - Python SDK
    
    使用示例:
        sdk = KGMemorySDK("http://localhost:8000")
        sdk.create_node("Python")
        sdk.connect("Python", "FastAPI")
        results = sdk.recall("Python")
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def create_node(self, label: str, properties: Dict = None, node_type: str = "entity"):
        import requests
        response = requests.post(
            f"{self.base_url}/nodes",
            json={"label": label, "properties": properties or {}, "type": node_type}
        )
        return response.json()
    
    def connect(self, source: str, target: str, relation: str = "related_to", weight: float = 1.0):
        import requests
        response = requests.post(
            f"{self.base_url}/edges",
            json={"source": source, "target": target, "relation": relation, "weight": weight}
        )
        return response.json()
    
    def recall(self, query: str, k: int = 20):
        import requests
        response = requests.get(f"{self.base_url}/recall/{query}", params={"k": k})
        return response.json()
    
    def infer(self, concept: str, max_depth: int = 3):
        import requests
        response = requests.get(f"{self.base_url}/infer/{concept}", params={"max_depth": max_depth})
        return response.json()
    
    def get_stats(self):
        import requests
        response = requests.get(f"{self.base_url}/stats")
        return response.json()
    
    def get_analytics(self):
        import requests
        response = requests.get(f"{self.base_url}/analytics")
        return response.json()


# ============================================
# Main Server Runner
# ============================================

def main():
    print(f"\n{'='*80}")
    print(f"🚀 知识图谱记忆系统 v6.0 - API Server")
    print(f"{'='*80}")
    print(f"📚 API Docs: http://localhost:8000/docs")
    print(f"📖 Redoc: http://localhost:8000/redoc")
    print(f"🏠 Homepage: http://localhost:8000/")
    print(f"{'='*80}\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
