"""
Code RAG v20.0 - WebSocket 实时通信桥
用于连接 VS Code 扩展前端与后端服务
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading
import time


class MessageType(Enum):
    """消息类型"""
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    DOCUMENT_OPEN = "document_open"
    DOCUMENT_CHANGE = "document_change"
    DOCUMENT_CLOSE = "document_close"
    DIAGNOSTICS = "diagnostics"
    CODE_ACTION = "code_action"
    CODE_EXPLANATION = "code_explanation"
    CODE_GENERATION = "code_generation"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"


@dataclass
class WSMessage:
    """WebSocket 消息"""
    type: str
    id: str
    data: Dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        return {
            "type": self.type,
            "id": self.id,
            "data": self.data,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'WSMessage':
        return cls(
            type=data.get("type"),
            id=data.get("id"),
            data=data.get("data", {}),
            timestamp=data.get("timestamp", time.time())
        )


class MessageHandler:
    """消息处理器基类"""
    
    def __init__(self):
        self.handlers: Dict[str, Callable] = {}
    
    def register(self, msg_type: str, handler: Callable):
        self.handlers[msg_type] = handler
    
    async def handle(self, message: WSMessage, connection) -> Optional[WSMessage]:
        if message.type in self.handlers:
            return await self.handlers[message.type](message, connection)
        return None


class ClientConnection:
    """客户端连接表示"""
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.connected: bool = True
        self.session_data: Dict = {}
        self.last_active: float = time.time()
    
    def ping(self):
        self.last_active = time.time()


class WebSocketServer:
    """WebSocket 服务器"""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Dict[str, ClientConnection] = {}
        self.message_handler = MessageHandler()
        self._running = False
        self._server_task = None
        
        # 注册默认处理器
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        self.message_handler.register(MessageType.PING.value, self._handle_ping)
        self.message_handler.register(MessageType.CONNECT.value, self._handle_connect)
        self.message_handler.register(MessageType.DISCONNECT.value, self._handle_disconnect)
    
    async def _handle_ping(self, message: WSMessage, connection) -> WSMessage:
        connection.ping()
        return WSMessage(
            type=MessageType.PONG.value,
            id=f"pong_{message.id}",
            data={}
        )
    
    async def _handle_connect(self, message: WSMessage, connection) -> WSMessage:
        connection.session_data.update(message.data)
        print(f"Client connected: {connection.client_id}")
        return WSMessage(
            type="connected",
            id=message.id,
            data={"status": "ok", "server_version": "20.0.0"}
        )
    
    async def _handle_disconnect(self, message: WSMessage, connection) -> WSMessage:
        print(f"Client disconnected: {connection.client_id}")
        return WSMessage(
            type="disconnected",
            id=message.id,
            data={"status": "ok"}
        )
    
    def register_handler(self, msg_type: str, handler: Callable):
        self.message_handler.register(msg_type, handler)
    
    async def send_to_client(self, client_id: str, message: WSMessage):
        if client_id in self.clients:
            print(f"Sending to {client_id}: {message.type}")
    
    async def broadcast(self, message: WSMessage):
        for client_id in self.clients:
            await self.send_to_client(client_id, message)
    
    def start(self):
        self._running = True
        print(f"WebSocket server starting on {self.host}:{self.port}")
        
        async def dummy_server():
            while self._running:
                await asyncio.sleep(0.1)
        
        self._server_task = asyncio.create_task(dummy_server())
        print("WebSocket server started (simulated mode)")
    
    def stop(self):
        self._running = False
        if self._server_task:
            self._server_task.cancel()
        print("WebSocket server stopped")
    
    def simulate_client_connect(self, client_id: str) -> ClientConnection:
        """模拟客户端连接（用于测试）"""
        conn = ClientConnection(client_id)
        self.clients[client_id] = conn
        return conn
    
    async def simulate_message(self, client_id: str, message: WSMessage) -> Optional[WSMessage]:
        """模拟接收消息（用于测试）"""
        if client_id in self.clients:
            conn = self.clients[client_id]
            return await self.message_handler.handle(message, conn)
        return None


class CodeRAGWebSocketBridge:
    """Code RAG WebSocket 桥接"""
    
    def __init__(self, ws_server: Optional[WebSocketServer] = None):
        self.ws_server = ws_server or WebSocketServer()
        self._register_code_rag_handlers()
    
    def _register_code_rag_handlers(self):
        from code_rag.middleware_layer.vscode_extension import create_vscode_service
        from code_rag.service_layer.llm_integration import create_llm_service
        
        self.vscode_service = create_vscode_service()
        self.llm_service = create_llm_service()
        
        self.ws_server.register_handler(
            MessageType.DOCUMENT_OPEN.value, 
            self._handle_document_open
        )
        self.ws_server.register_handler(
            MessageType.DOCUMENT_CHANGE.value, 
            self._handle_document_change
        )
        self.ws_server.register_handler(
            MessageType.CODE_EXPLANATION.value, 
            self._handle_code_explanation
        )
        self.ws_server.register_handler(
            MessageType.CODE_ACTION.value, 
            self._handle_code_action
        )
    
    async def _handle_document_open(self, message: WSMessage, connection) -> WSMessage:
        file_path = message.data.get("file_path", "")
        content = message.data.get("content", "")
        language = message.data.get("language", "python")
        
        result = self.vscode_service.open_document(file_path, content, language)
        
        return WSMessage(
            type=MessageType.DIAGNOSTICS.value,
            id=message.id,
            data=result
        )
    
    async def _handle_document_change(self, message: WSMessage, connection) -> WSMessage:
        file_path = message.data.get("file_path", "")
        content = message.data.get("content", "")
        
        result = self.vscode_service.update_document(file_path, content)
        
        return WSMessage(
            type=MessageType.DIAGNOSTICS.value,
            id=message.id,
            data=result
        )
    
    async def _handle_code_explanation(self, message: WSMessage, connection) -> WSMessage:
        code = message.data.get("code", "")
        
        result = self.llm_service.explain_code(code)
        
        return WSMessage(
            type=MessageType.CODE_EXPLANATION.value,
            id=message.id,
            data={"explanation": result.content}
        )
    
    async def _handle_code_action(self, message: WSMessage, connection) -> WSMessage:
        file_path = message.data.get("file_path", "")
        line = message.data.get("line", 0)
        
        result = self.vscode_service.get_code_actions(file_path, line)
        
        return WSMessage(
            type=MessageType.CODE_ACTION.value,
            id=message.id,
            data=result
        )
    
    def start(self):
        self.ws_server.start()
    
    def stop(self):
        self.ws_server.stop()


def create_websocket_bridge(host: str = "localhost", port: int = 8765) -> CodeRAGWebSocketBridge:
    """创建 WebSocket 桥接实例"""
    server = WebSocketServer(host=host, port=port)
    return CodeRAGWebSocketBridge(server)
