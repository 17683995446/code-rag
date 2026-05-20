#!/usr/bin/env python3
"""
可视化网站服务 - 自动监听文件变化并更新
"""
import os
import sys
import time
import json
import threading
import webbrowser
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.responses import FileResponse, HTMLResponse
    from fastapi.staticfiles import StaticFiles
    import uvicorn
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent
except ImportError:
    print("安装依赖中...")
    os.system("pip install fastapi uvicorn watchdog python-multipart")
    print("\n请重新运行此脚本")
    sys.exit(1)


# Initialize FastAPI app
app = FastAPI(title="知识图谱记忆系统 - 可视化", version="5.0")

# Store file modification times
file_timestamps: Dict[str, float] = {}

# WebSocket connections
active_connections: List[WebSocket] = []


class FileChangeHandler(FileSystemEventHandler):
    """文件变化监听器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.last_notification = 0
        self.notification_cooldown = 1.0
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        path = Path(event.src_path)
        
        # Ignore __pycache__, .pyc, etc.
        if any(part.startswith('.') or part.endswith('.pyc') or part == '__pycache__'
               for part in path.parts):
            return
        
        # Only watch relevant files
        if path.suffix not in ['.py', '.toml', '.html', '.css', '.js']:
            return
        
        relative_path = str(path.relative_to(self.project_root))
        current_time = time.time()
        
        # Update timestamp
        file_timestamps[relative_path] = current_time
        
        # Notify clients with cooldown
        if current_time - self.last_notification > self.notification_cooldown:
            self.last_notification = current_time
            print(f"\n🔄 文件变化: {relative_path}")
            self.notify_clients(relative_path)
    
    def notify_clients(self, changed_file: str):
        """通知所有连接的客户端"""
        message = {
            "type": "file_changed",
            "file": changed_file,
            "timestamp": datetime.now().isoformat(),
            "files": list(file_timestamps.keys())
        }
        
        for connection in active_connections.copy():
            try:
                import asyncio
                asyncio.create_task(connection.send_json(message))
            except Exception:
                active_connections.remove(connection)


def setup_file_watcher():
    """设置文件监听器"""
    project_root = Path(__file__).parent
    event_handler = FileChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, str(project_root), recursive=True)
    observer.start()
    return observer


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        # Send initial file list
        await websocket.send_json({
            "type": "init",
            "files": list(file_timestamps.keys()),
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)


# Visualization page
@app.get("/", response_class=HTMLResponse)
@app.get("/visualization", response_class=HTMLResponse)
async def get_visualization():
    html_path = Path(__file__).parent / "visualization.html"
    if html_path.exists():
        return FileResponse(str(html_path))
    return HTMLResponse("<h1>404 - 页面未找到</h1>")


# API endpoints
@app.get("/api/files")
async def get_files():
    """获取文件列表和修改时间"""
    project_root = Path(__file__).parent
    
    files_info = []
    for pattern in ["*.py", "src/**/*.py", "*.toml", "*.html", "*.md"]:
        for path in project_root.rglob(pattern):
            if "__pycache__" in path.parts:
                continue
            relative_path = str(path.relative_to(project_root))
            files_info.append({
                "path": relative_path,
                "size": path.stat().st_size,
                "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat()
            })
    
    return {
        "files": files_info,
        "total": len(files_info)
    }


@app.get("/api/stats")
async def get_stats():
    """获取系统统计信息"""
    try:
        from kg_memory.core import MemorySystem
        import tempfile
        
        ms = MemorySystem(tempfile.mkdtemp())
        stats = ms.stats()
        
        return {
            "status": "running",
            "timestamp": datetime.now().isoformat(),
            "stats": stats,
            "connections": len(active_connections)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


# Mount static files
static_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


def start_server():
    """启动服务器"""
    print("\n" + "="*80)
    print("🚀 知识图谱记忆系统 - 可视化服务")
    print("="*80)
    print("\n📡 服务已启动，正在监听文件变化...")
    print("\n🌐 访问地址:")
    print("   主页: http://localhost:8080/")
    print("   API文档: http://localhost:8080/docs")
    print("\n⌨️  按 Ctrl+C 停止服务\n")
    
    # Try to open browser
    try:
        time.sleep(1.5)
        webbrowser.open("http://localhost:8080/")
    except Exception:
        pass
    
    # Start file watcher
    observer = setup_file_watcher()
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
    except KeyboardInterrupt:
        print("\n👋 正在停止...")
        observer.stop()
        observer.join()


if __name__ == "__main__":
    start_server()
