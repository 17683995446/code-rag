"""
Code RAG v17.0 - AI对话助手核心模块
多轮对话系统、上下文管理和智能问答
"""

import json
import time
import uuid
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict


class MessageRole(Enum):
    """消息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class Intent(Enum):
    """对话意图"""
    GREETING = "greeting"
    CODE_SEARCH = "code_search"
    CODE_EXPLANATION = "code_explanation"
    CODE_GENERATION = "code_generation"
    BUG_ANALYSIS = "bug_analysis"
    ARCHITECTURE_ADVICE = "architecture_advice"
    BEST_PRACTICES = "best_practices"
    REFACTORING = "refactoring"
    QUESTION = "question"
    UNKNOWN = "unknown"


@dataclass
class Message:
    """对话消息"""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationContext:
    """对话上下文"""
    session_id: str
    user_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    messages: List[Message] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    search_history: List[Dict] = field(default_factory=list)
    current_files: List[str] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationResponse:
    """对话响应"""
    message: str
    intent: Intent
    confidence: float
    suggestions: List[str] = field(default_factory=list)
    code_snippets: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConversationManager:
    """
    对话管理器
    管理多轮对话、上下文和状态
    """

    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self.conversations: Dict[str, ConversationContext] = {}
        self.intent_classifier = IntentClassifier()
        self.response_generator = ResponseGenerator()
        
        self._callbacks: Dict[str, Callable] = {}

    def create_session(self, user_id: Optional[str] = None) -> str:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        
        self.conversations[session_id] = ConversationContext(
            session_id=session_id,
            user_id=user_id,
            messages=[]
        )
        
        return session_id

    def get_session(self, session_id: str) -> Optional[ConversationContext]:
        """获取会话"""
        return self.conversations.get(session_id)

    def add_message(
        self,
        session_id: str,
        role: MessageRole,
        content: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """添加消息"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        
        session.messages.append(message)
        session.last_updated = datetime.now()
        
        if len(session.messages) > self.max_history:
            session.messages = session.messages[-self.max_history:]
        
        return True

    def get_recent_messages(
        self,
        session_id: str,
        count: int = 10
    ) -> List[Message]:
        """获取最近的消息"""
        session = self.get_session(session_id)
        if not session:
            return []
        
        return session.messages[-count:]

    def clear_session(self, session_id: str) -> bool:
        """清除会话"""
        if session_id in self.conversations:
            del self.conversations[session_id]
            return True
        return False

    def process_message(
        self,
        session_id: str,
        user_message: str
    ) -> ConversationResponse:
        """
        处理用户消息
        
        Args:
            session_id: 会话ID
            user_message: 用户消息
            
        Returns:
            对话响应
        """
        session = self.get_session(session_id)
        if not session:
            session_id = self.create_session()
            session = self.get_session(session_id)
        
        self.add_message(session_id, MessageRole.USER, user_message)
        
        intent_result = self.intent_classifier.classify(user_message, session)
        
        response = self.response_generator.generate(
            intent=intent_result['intent'],
            user_message=user_message,
            context=session,
            confidence=intent_result['confidence']
        )
        
        self.add_message(
            session_id,
            MessageRole.ASSISTANT,
            response.message,
            metadata={
                'intent': response.intent.value,
                'confidence': response.confidence
            }
        )
        
        return response

    def register_callback(self, event: str, callback: Callable):
        """注册回调"""
        self._callbacks[event] = callback

    def trigger_callback(self, event: str, *args, **kwargs):
        """触发回调"""
        if event in self._callbacks:
            self._callbacks[event](*args, **kwargs)


class IntentClassifier:
    """意图分类器"""

    def __init__(self):
        self.intent_patterns = {
            Intent.GREETING: [
                '你好', 'hi', 'hello', '嗨', 'hi there', 'hey',
                '早上好', '下午好', '晚上好'
            ],
            Intent.CODE_SEARCH: [
                '搜索', '查找', '找', 'search', 'find',
                '在哪里', '怎么实现', '有没有'
            ],
            Intent.CODE_EXPLANATION: [
                '解释', '说明', '讲解', 'explain', 'describe',
                '这是什么', '干嘛的', '有什么用'
            ],
            Intent.CODE_GENERATION: [
                '生成', '创建', '写', '生成代码', 'create',
                '帮我写', '写一个', '怎么写'
            ],
            Intent.BUG_ANALYSIS: [
                'bug', '错误', '修复', '问题', '报错',
                '出错了', '不对', '有bug'
            ],
            Intent.ARCHITECTURE_ADVICE: [
                '架构', '设计', '架构设计', 'architecture',
                '应该怎么组织', '推荐方案'
            ],
            Intent.BEST_PRACTICES: [
                '最佳实践', '规范', '标准', 'best practice',
                '应该怎样', '推荐'
            ],
            Intent.REFACTORING: [
                '重构', '优化', 'refactor', '重写',
                '改进', '改善', '怎么优化'
            ]
        }

    def classify(
        self,
        message: str,
        context: Optional[ConversationContext] = None
    ) -> Dict[str, Any]:
        """
        分类消息意图
        
        Returns:
            {
                'intent': Intent,
                'confidence': float,
                'keywords': List[str]
            }
        """
        message_lower = message.lower()
        
        scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = sum(1 for pattern in patterns if pattern in message_lower)
            if score > 0:
                scores[intent] = score
        
        if not scores:
            return {
                'intent': Intent.QUESTION,
                'confidence': 0.5,
                'keywords': []
            }
        
        best_intent = max(scores, key=scores.get)
        max_score = scores[best_intent]
        
        confidence = min(0.5 + (max_score * 0.1), 0.99)
        
        return {
            'intent': best_intent,
            'confidence': confidence,
            'keywords': [p for p in self.intent_patterns[best_intent] 
                        if p in message_lower]
        }


class ResponseGenerator:
    """响应生成器"""

    def __init__(self):
        self.intent_templates = {
            Intent.GREETING: [
                "你好！我是 Code RAG AI 助手。我可以帮助你：\n"
                "• 搜索和分析代码\n"
                "• 解释代码功能\n"
                "• 生成代码片段\n"
                "• 分析 Bug\n"
                "• 提供架构建议\n"
                "有什么我可以帮助你的吗？",
                
                "嗨！👋 欢迎使用 Code RAG AI 助手！\n"
                "你可以问我关于代码的任何问题，比如：\n"
                "• 怎么实现用户认证？\n"
                "• 这个函数是做什么的？\n"
                "• 帮我写一个数据库连接类\n"
                "开始吧！"
            ],
            
            Intent.CODE_SEARCH: [
                "好的，我来帮你搜索相关代码。\n"
                "你可以告诉我更具体的关键词，比如：\n"
                "• 功能名称 (如: 用户认证)\n"
                "• 技术栈 (如: Django, React)\n"
                "• 文件类型 (如: API, Model)\n"
                "我会帮你找到最相关的代码。"
            ],
            
            Intent.CODE_EXPLANATION: [
                "好的，让我帮你解释这段代码。\n"
                "请提供具体的代码内容或文件路径，"
                "我会详细解释：\n"
                "• 代码的功能\n"
                "• 关键逻辑\n"
                "• 输入输出\n"
                "• 依赖关系"
            ],
            
            Intent.CODE_GENERATION: [
                "好的，我可以帮你生成代码！\n"
                "请告诉我：\n"
                "• 需要实现什么功能\n"
                "• 使用的编程语言\n"
                "• 框架或库\n"
                "• 具体的约束条件\n"
                "我会生成符合最佳实践的代码。"
            ],
            
            Intent.BUG_ANALYSIS: [
                "让我帮你分析这个 Bug。\n"
                "请提供：\n"
                "• 完整的错误信息\n"
                "• 相关代码\n"
                "• 错误出现的场景\n"
                "我会帮你定位问题并提供解决方案。"
            ],
            
            Intent.ARCHITECTURE_ADVICE: [
                "好的，关于架构设计，我来给你建议。\n"
                "请告诉我：\n"
                "• 项目类型和规模\n"
                "• 现有技术栈\n"
                "• 业务需求\n"
                "• 性能要求\n"
                "我会根据最佳实践给出架构建议。"
            ],
            
            Intent.BEST_PRACTICES: [
                "好的，关于最佳实践，我来给你建议。\n"
                "我会考虑：\n"
                "• 代码可读性\n"
                "• 性能优化\n"
                "• 安全最佳实践\n"
                "• 维护性\n"
                "• 可扩展性"
            ],
            
            Intent.REFACTORING: [
                "好的，我可以帮你重构和优化代码。\n"
                "请提供需要重构的代码，"
                "我会分析：\n"
                "• 代码质量问题\n"
                "• 性能瓶颈\n"
                "• 设计模式应用\n"
                "• 优化建议"
            ],
            
            Intent.QUESTION: [
                "好的，我理解你的问题。\n"
                "让我帮你分析和解答。\n"
                "你可以提供更多细节，这样我可以给你更准确的答案。"
            ],
            
            Intent.UNKNOWN: [
                "抱歉，我没有完全理解你的意思。\n"
                "你可以：\n"
                "• 换一个说法\n"
                "• 提供更多细节\n"
                "• 使用具体的关键词\n"
                "我会尽力帮助你！"
            ]
        }

    def generate(
        self,
        intent: Intent,
        user_message: str,
        context: ConversationContext,
        confidence: float
    ) -> ConversationResponse:
        """生成响应"""
        import random
        
        templates = self.intent_templates.get(
            intent,
            self.intent_templates[Intent.QUESTION]
        )
        
        base_message = random.choice(templates)
        
        suggestions = self._get_suggestions(intent)
        
        return ConversationResponse(
            message=base_message,
            intent=intent,
            confidence=confidence,
            suggestions=suggestions,
            code_snippets=[],
            actions=self._get_actions(intent),
            metadata={
                'intent_name': intent.value,
                'context_length': len(context.messages) if context else 0
            }
        )

    def _get_suggestions(self, intent: Intent) -> List[str]:
        """获取建议"""
        suggestions_map = {
            Intent.GREETING: [
                "帮我搜索用户认证代码",
                "解释这个函数的用途",
                "生成一个API接口",
                "分析这个Bug"
            ],
            Intent.CODE_SEARCH: [
                "搜索数据库连接代码",
                "查找API路由实现",
                "搜索异常处理代码"
            ],
            Intent.CODE_EXPLANATION: [
                "解释用户认证模块",
                "说明数据验证逻辑",
                "讲解API设计"
            ],
            Intent.CODE_GENERATION: [
                "生成CRUD接口",
                "创建数据模型",
                "写单元测试"
            ],
            Intent.BUG_ANALYSIS: [
                "分析空指针异常",
                "排查性能问题",
                "修复并发Bug"
            ],
            Intent.ARCHITECTURE_ADVICE: [
                "微服务架构建议",
                "前后端分离设计",
                "数据库设计建议"
            ],
            Intent.BEST_PRACTICES: [
                "Python代码规范",
                "API设计最佳实践",
                "安全编程建议"
            ],
            Intent.REFACTORING: [
                "优化数据库查询",
                "重构业务逻辑",
                "改进代码结构"
            ]
        }
        
        return suggestions_map.get(intent, [])

    def _get_actions(self, intent: Intent) -> List[str]:
        """获取可执行动作"""
        actions_map = {
            Intent.CODE_SEARCH: ["search", "filter", "analyze"],
            Intent.CODE_GENERATION: ["generate", "validate", "format"],
            Intent.BUG_ANALYSIS: ["debug", "trace", "fix"]
        }
        
        return actions_map.get(intent, [])


def create_conversation_manager() -> ConversationManager:
    """创建对话管理器"""
    return ConversationManager()
