"""
知识图谱记忆系统 - Web API和可视化
"""

from pathlib import Path
from typing import Any, Dict, List
import os

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

from kg_memory.core import MemorySystem


app = FastAPI(
    title="Knowledge Graph Memory System",
    description="Industrial-grade Knowledge Graph Memory System powered by NetworkX",
    version="4.0.0",
)

# 全局内存系统实例
g_memory_system = None


def get_memory_system() -> MemorySystem:
    global g_memory_system
    if g_memory_system is None:
        g_memory_system = MemorySystem("./data_web")
    return g_memory_system


# 挂载静态文件服务和主页
current_dir = Path(__file__).parent.parent.parent
if (current_dir / "final.html").exists():
    app.mount("/static", StaticFiles(directory=str(current_dir)), name="static")
    
    @app.get("/final.html")
    async def serve_final():
        return FileResponse(str(current_dir / "final.html"))


# Pydantic模型

class RememberRequest(BaseModel):
    knowledge: str
    properties: Dict[str, Any] = {}


class ConnectRequest(BaseModel):
    source: str
    target: str
    relation: str = "related_to"
    weight: float = 1.0


class RecallResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]


class StatsResponse(BaseModel):
    version: str
    backend: str
    nodes: int
    edges: int
    density: float
    connected_components: int


# 路由

@app.get("/", response_class=HTMLResponse)
def index():
    """主页"""
    html_path = Path(__file__).parent / "web" / "index.html"
    if not html_path.exists():
        return """
        <html>
        <head>
            <title>Knowledge Graph Memory</title>
            <style>
                body { font-family: system-ui, -apple-system, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
                h1 { color: #7c3aed; }
                .card { background: #f3f4f6; padding: 20px; border-radius: 10px; margin: 20px 0; }
                button { background: #7c3aed; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
                button:hover { background: #6d28d9; }
            </style>
        </head>
        <body>
            <h1>🧠 Knowledge Graph Memory System v4.0</h1>
            <div class="card">
                <h2>API Endpoints</h2>
                <ul>
                    <li><code>GET /stats</code> - System statistics</li>
                    <li><code>POST /remember</code> - Remember new knowledge</li>
                    <li><code>POST /connect</code> - Connect knowledge</li>
                    <li><code>GET /recall/{query}</code> - Recall knowledge</li>
                    <li><code>GET /infer/{concept}</code> - Knowledge inference</li>
                </ul>
            </div>
            <div class="card">
                <h2>Quick Start</h2>
                <a href="/docs"><button>Open API Documentation</button></a>
            </div>
        </body>
        </html>
        """
    return HTMLResponse(content=html_path.read_text())


@app.get("/stats", response_model=StatsResponse)
def get_stats():
    """获取系统统计"""
    ms = get_memory_system()
    stats = ms.stats()
    return StatsResponse(**stats)


@app.post("/remember")
def remember_knowledge(request: RememberRequest):
    """记住新知识"""
    ms = get_memory_system()
    node_id = ms.remember(request.knowledge, properties=request.properties)
    ms.save()
    return {"success": True, "node_id": node_id}


@app.post("/connect")
def connect_knowledge(request: ConnectRequest):
    """连接知识"""
    ms = get_memory_system()
    edge_id = ms.connect(request.source, request.target, relation=request.relation, weight=request.weight)
    ms.save()
    return {"success": True, "edge_id": edge_id}


@app.get("/recall/{query}", response_model=RecallResponse)
def recall_knowledge(query: str, k: int = 10):
    """回忆知识"""
    ms = get_memory_system()
    results = ms.recall(query, k=k)
    return RecallResponse(query=query, results=results)


@app.get("/infer/{concept}")
def infer_knowledge(concept: str, depth: int = 3):
    """知识推理"""
    ms = get_memory_system()
    results = ms.infer(concept, max_depth=depth)
    return {"concept": concept, "depth": depth, "results": results}


@app.get("/path/{source}/{target}")
def find_path(source: str, target: str):
    """查找最短路径"""
    ms = get_memory_system()
    path_result = ms.shortest_path(source, target)
    return {"source": source, "target": target, "path": path_result}


@app.get("/centrality/betweenness")
def get_betweenness_centrality():
    """获取介数中心性"""
    ms = get_memory_system()
    return ms.betweenness_centrality()


@app.get("/centrality/degree")
def get_degree_centrality():
    """获取度中心性"""
    ms = get_memory_system()
    return ms.degree_centrality()


@app.get("/centrality/closeness")
def get_closeness_centrality():
    """获取接近中心性"""
    ms = get_memory_system()
    return ms.closeness_centrality()


@app.get("/centrality/eigenvector")
def get_eigenvector_centrality():
    """获取特征向量中心性"""
    ms = get_memory_system()
    return ms.eigenvector_centrality()


@app.get("/pagerank")
def get_pagerank(alpha: float = 0.85):
    """获取PageRank"""
    ms = get_memory_system()
    return ms.pagerank(alpha)


@app.get("/communities")
def get_communities():
    """获取社区结构"""
    ms = get_memory_system()
    return {"communities": ms.find_communities()}


@app.get("/similar/{label}")
def get_similar_nodes(label: str, top_k: int = 5):
    """获取相似节点"""
    ms = get_memory_system()
    return {"label": label, "similar": ms.get_similar_nodes(label, top_k)}


@app.get("/visualize")
def visualize():
    """可视化数据"""
    ms = get_memory_system()
    
    # 导出为vis.js格式
    nodes = []
    edges = []
    
    stats = ms.stats()
    for node_dict in ms.recall("", k=stats['nodes']):
        nodes.append({
            "id": node_dict["id"],
            "label": node_dict["label"],
            "type": node_dict["type"]
        })
    
    # 简单边收集（演示目的）
    return {"nodes": nodes, "edges": edges}


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """运行服务器"""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
