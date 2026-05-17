"""
Code RAG v18.0 - 上下文理解增强模块
实现多轮对话上下文管理和会话状态追踪
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class Message:
    """对话消息"""
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class ConversationContext:
    """对话上下文"""
    conversation_id: str
    topic: str = ""
    entities: List[str] = field(default_factory=list)
    code_snippets: List[str] = field(default_factory=list)
    intent_history: List[str] = field(default_factory=list)
    last_topic: str = ""
    turns_count: int = 0
    
    def add_turn(self, intent: str, topic: str = "", entities: List[str] = None):
        """添加对话轮次"""
        self.turns_count += 1
        self.intent_history.append(intent)
        if topic:
            self.last_topic = self.topic
            self.topic = topic
        if entities:
            self.entities.extend(entities)
    
    def add_code_snippet(self, code: str):
        """添加代码片段"""
        if code and code not in self.code_snippets:
            self.code_snippets.append(code)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'conversation_id': self.conversation_id,
            'topic': self.topic,
            'entities': self.entities,
            'code_snippets': self.code_snippets,
            'intent_history': self.intent_history,
            'last_topic': self.last_topic,
            'turns_count': self.turns_count
        }


class ContextManager:
    """上下文管理器"""
    
    def __init__(self, max_history: int = 20):
        self.max_history = max_history
        self.conversations: Dict[str, ConversationContext] = {}
        self.message_histories: Dict[str, List[Message]] = {}
    
    def create_conversation(self, conversation_id: str) -> ConversationContext:
        """创建新对话"""
        context = ConversationContext(conversation_id=conversation_id)
        self.conversations[conversation_id] = context
        self.message_histories[conversation_id] = []
        return context
    
    def get_context(self, conversation_id: str) -> Optional[ConversationContext]:
        """获取对话上下文"""
        return self.conversations.get(conversation_id)
    
    def add_message(self, conversation_id: str, role: str, content: str, 
                    metadata: Dict[str, Any] = None) -> Message:
        """添加消息"""
        if conversation_id not in self.conversations:
            self.create_conversation(conversation_id)
        
        message = Message(role=role, content=content, metadata=metadata or {})
        self.message_histories[conversation_id].append(message)
        
        if len(self.message_histories[conversation_id]) > self.max_history:
            self.message_histories[conversation_id] = \
                self.message_histories[conversation_id][-self.max_history:]
        
        return message
    
    def get_history(self, conversation_id: str, limit: int = None) -> List[Message]:
        """获取对话历史"""
        history = self.message_histories.get(conversation_id, [])
        if limit:
            return history[-limit:]
        return history
    
    def get_context_window(self, conversation_id: str, window_size: int = 5) -> List[Message]:
        """获取最近N轮对话"""
        return self.get_history(conversation_id, limit=window_size * 2)
    
    def extract_entities_from_context(self, conversation_id: str) -> List[str]:
        """从上下文中提取实体"""
        context = self.get_context(conversation_id)
        if not context:
            return []
        return list(set(context.entities))
    
    def extract_code_snippets(self, conversation_id: str) -> List[str]:
        """提取代码片段"""
        context = self.get_context(conversation_id)
        if not context:
            return []
        return context.code_snippets
    
    def update_topic(self, conversation_id: str, topic: str, entities: List[str] = None):
        """更新对话主题"""
        context = self.get_context(conversation_id)
        if context:
            context.add_turn(topic=topic, intent="topic_change", entities=entities)
    
    def get_conversation_summary(self, conversation_id: str) -> Dict[str, Any]:
        """获取对话摘要"""
        context = self.get_context(conversation_id)
        history = self.get_history(conversation_id)
        
        if not context:
            return {'exists': False}
        
        return {
            'exists': True,
            'conversation_id': conversation_id,
            'topic': context.topic,
            'turns_count': context.turns_count,
            'message_count': len(history),
            'entities': context.entities[-5:],
            'code_snippets_count': len(context.code_snippets),
            'recent_intents': context.intent_history[-3:],
            'first_message': history[0].to_dict() if history else None,
            'last_message': history[-1].to_dict() if history else None
        }
    
    def clear_conversation(self, conversation_id: str):
        """清除对话"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
        if conversation_id in self.message_histories:
            del self.message_histories[conversation_id]
    
    def export_conversation(self, conversation_id: str) -> Optional[str]:
        """导出对话为JSON"""
        context = self.get_context(conversation_id)
        history = self.get_history(conversation_id)
        
        if not context:
            return None
        
        export_data = {
            'context': context.to_dict(),
            'messages': [msg.to_dict() for msg in history]
        }
        
        return json.dumps(export_data, ensure_ascii=False, indent=2)
    
    def import_conversation(self, json_data: str) -> Optional[str]:
        """导入对话"""
        try:
            data = json.loads(json_data)
            context_data = data.get('context', {})
            conversation_id = context_data.get('conversation_id')
            
            if not conversation_id:
                return None
            
            context = ConversationContext(**context_data)
            self.conversations[conversation_id] = context
            
            messages = []
            for msg_data in data.get('messages', []):
                msg_data_copy = msg_data.copy()
                msg_data_copy['timestamp'] = datetime.fromisoformat(msg_data['timestamp'])
                messages.append(Message(**msg_data_copy))
            
            self.message_histories[conversation_id] = messages
            
            return conversation_id
        except Exception as e:
            print(f"导入对话失败: {e}")
            return None


class ContextualQAManager:
    """上下文感知问答管理器"""
    
    def __init__(self, context_manager: ContextManager = None):
        self.context_manager = context_manager or ContextManager()
        self.current_conversation_id: Optional[str] = None
    
    def start_conversation(self, conversation_id: str = None) -> str:
        """开始新对话"""
        if conversation_id is None:
            conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.context_manager.create_conversation(conversation_id)
        self.current_conversation_id = conversation_id
        return conversation_id
    
    def add_user_message(self, content: str, metadata: Dict[str, Any] = None):
        """添加用户消息"""
        if not self.current_conversation_id:
            self.start_conversation()
        
        return self.context_manager.add_message(
            self.current_conversation_id, 'user', content, metadata
        )
    
    def add_assistant_message(self, content: str, metadata: Dict[str, Any] = None):
        """添加助手消息"""
        if not self.current_conversation_id:
            self.start_conversation()
        
        return self.context_manager.add_message(
            self.current_conversation_id, 'assistant', content, metadata
        )
    
    def get_contextual_prompt(self, current_question: str, window_size: int = 5) -> str:
        """生成带上下文的提示"""
        if not self.current_conversation_id:
            return current_question
        
        context_window = self.context_manager.get_context_window(
            self.current_conversation_id, window_size
        )
        
        if not context_window:
            return current_question
        
        context_parts = []
        for msg in context_window[-window_size:]:
            role_label = "用户" if msg.role == "user" else "助手"
            context_parts.append(f"{role_label}: {msg.content}")
        
        return "\n".join([
            "对话历史:",
            "\n".join(context_parts),
            "",
            f"当前问题: {current_question}"
        ])
    
    def resolve_pronouns(self, text: str) -> str:
        """简单的代词解析"""
        replacements = {
            '它': '这个代码/函数',
            '这个': '之前提到的',
            '那个': '之前提到的',
            '这些': '之前提到的',
            '那些': '之前提到的'
        }
        
        resolved = text
        for pronoun, replacement in replacements.items():
            if pronoun in text:
                code_snippets = self.context_manager.extract_code_snippets(
                    self.current_conversation_id or ""
                )
                if code_snippets:
                    resolved = resolved.replace(pronoun, f"{replacement}的代码")
                else:
                    resolved = resolved.replace(pronoun, replacement)
        
        return resolved
    
    def is_follow_up_question(self, question: str) -> bool:
        """判断是否为后续问题"""
        follow_up_indicators = [
            '它', '这个', '那个', '这些', '那些',
            '为什么', '怎么', '如何', '什么意思',
            '再', '还', '继续', '还有'
        ]
        
        return any(indicator in question for indicator in follow_up_indicators)
    
    def get_conversation_state(self) -> Dict[str, Any]:
        """获取当前对话状态"""
        if not self.current_conversation_id:
            return {'active': False}
        
        return {
            'active': True,
            'conversation_id': self.current_conversation_id,
            'summary': self.context_manager.get_conversation_summary(
                self.current_conversation_id
            )
        }
    
    def end_conversation(self):
        """结束当前对话"""
        self.current_conversation_id = None


class MultiTurnDialogueManager:
    """多轮对话管理器"""
    
    def __init__(self):
        self.qa_manager = ContextualQAManager()
        self.dialogue_strategies = self._init_strategies()
    
    def _init_strategies(self) -> Dict[str, Any]:
        """初始化对话策略"""
        return {
            'clarification': self._handle_clarification,
            'elaboration': self._handle_elaboration,
            'follow_up': self._handle_follow_up,
            'summary': self._handle_summary,
            'code_generation': self._handle_code_generation
        }
    
    def process_input(self, user_input: str, intent: str = None) -> Dict[str, Any]:
        """处理用户输入"""
        is_follow_up = self.qa_manager.is_follow_up_question(user_input)
        
        if is_follow_up:
            resolved_input = self.qa_manager.resolve_pronouns(user_input)
        else:
            resolved_input = user_input
            self.qa_manager.start_conversation()
        
        self.qa_manager.add_user_message(user_input)
        
        strategy = self.dialogue_strategies.get(
            intent or ('follow_up' if is_follow_up else 'clarification'),
            self._handle_general
        )
        
        response = strategy(resolved_input, intent)
        
        self.qa_manager.add_assistant_message(response['answer'])
        
        return {
            'response': response,
            'conversation_state': self.qa_manager.get_conversation_state(),
            'is_follow_up': is_follow_up,
            'resolved_input': resolved_input if is_follow_up else None
        }
    
    def _handle_clarification(self, input_text: str, intent: str = None) -> Dict[str, str]:
        """处理澄清请求"""
        return {
            'strategy': 'clarification',
            'answer': f"我需要更多细节来准确回答您的问题。您能提供:\n1. 具体的代码或错误信息\n2. 您想要实现的目标\n3. 相关的上下文信息"
        }
    
    def _handle_elaboration(self, input_text: str, intent: str = None) -> Dict[str, str]:
        """处理详细解释请求"""
        return {
            'strategy': 'elaboration',
            'answer': f"让我详细解释:\n\n[这里应该集成代码解释器]\n\n您还想了解哪方面的细节?"
        }
    
    def _handle_follow_up(self, input_text: str, intent: str = None) -> Dict[str, str]:
        """处理后续问题"""
        return {
            'strategy': 'follow_up',
            'answer': f"基于我们之前的讨论:{input_text}\n\n您能具体说明想了解什么?"
        }
    
    def _handle_summary(self, input_text: str, intent: str = None) -> Dict[str, str]:
        """处理总结请求"""
        state = self.qa_manager.get_conversation_state()
        summary = state.get('summary', {})
        
        return {
            'strategy': 'summary',
            'answer': f"本次对话摘要:\n- 主题: {summary.get('topic', '未定义')}\n- 轮次: {summary.get('turns_count', 0)}\n- 涉及代码片段: {summary.get('code_snippets_count', 0)}"
        }
    
    def _handle_code_generation(self, input_text: str, intent: str = None) -> Dict[str, str]:
        """处理代码生成请求"""
        return {
            'strategy': 'code_generation',
            'answer': f"基于您的需求 '{input_text}', 我可以生成相应的代码示例。请稍等..."
        }
    
    def _handle_general(self, input_text: str, intent: str = None) -> Dict[str, str]:
        """处理一般输入"""
        return {
            'strategy': 'general',
            'answer': f"我收到了您的输入: {input_text}"
        }
    
    def export_current_conversation(self) -> Optional[str]:
        """导出当前对话"""
        return self.qa_manager.context_manager.export_conversation(
            self.qa_manager.current_conversation_id or ""
        )
    
    def import_conversation(self, json_data: str) -> bool:
        """导入对话"""
        conversation_id = self.qa_manager.context_manager.import_conversation(json_data)
        if conversation_id:
            self.qa_manager.current_conversation_id = conversation_id
            return True
        return False
