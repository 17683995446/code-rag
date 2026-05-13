import os
import time
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum
import threading


class MessageRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    CONTEXT = "context"


@dataclass
class Message:
    role: str
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Message':
        return cls(
            role=data.get("role", "user"),
            content=data.get("content", ""),
            timestamp=data.get("timestamp", time.time()),
            metadata=data.get("metadata", {})
        )


@dataclass
class Conversation:
    conversation_id: str
    title: str = "New Conversation"
    messages: List[Message] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict = field(default_factory=dict)

    def add_message(self, role: str, content: str, metadata: Dict = None):
        msg = Message(role=role, content=content, metadata=metadata or {})
        self.messages.append(msg)
        self.updated_at = time.time()
        return msg

    def get_messages(self, limit: int = None) -> List[Message]:
        if limit:
            return self.messages[-limit:]
        return self.messages

    def to_dict(self) -> Dict:
        return {
            "conversation_id": self.conversation_id,
            "title": self.title,
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata
        }


class TokenBudget:
    def __init__(
        self,
        max_tokens: int = 6000,
        system_tokens: int = 500,
        user_tokens: int = 4000,
        assistant_tokens: int = 1500
    ):
        self.max_tokens = max_tokens
        self.system_tokens = system_tokens
        self.user_tokens = user_tokens
        self.assistant_tokens = assistant_tokens

    def estimate_messages_tokens(self, messages: List[Message]) -> int:
        total = 0
        for msg in messages:
            content_tokens = len(msg.content) // 4
            overhead = 4
            total += content_tokens + overhead
        return total

    def fits_in_budget(self, messages: List[Message]) -> bool:
        return self.estimate_messages_tokens(messages) <= self.max_tokens

    def get_truncation_point(
        self,
        messages: List[Message],
        preserve_recent: int = 5
    ) -> int:
        if self.fits_in_budget(messages):
            return len(messages)

        recent_messages = messages[-preserve_recent:] if preserve_recent else []
        older_messages = messages[:-preserve_recent] if preserve_recent else messages

        max_older_tokens = self.max_tokens - self.estimate_messages_tokens(recent_messages) - self.system_tokens

        kept_messages = []
        current_tokens = 0

        for msg in reversed(older_messages):
            msg_tokens = len(msg.content) // 4 + 4
            if current_tokens + msg_tokens <= max_older_tokens:
                kept_messages.insert(0, msg)
                current_tokens += msg_tokens
            else:
                break

        return len(kept_messages)


class ConversationManager:
    def __init__(
        self,
        storage_path: str = "./data/conversations",
        max_history: int = 50,
        max_conversations: int = 100
    ):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.max_history = max_history
        self.max_conversations = max_conversations

        self.conversations: Dict[str, Conversation] = {}
        self.active_conversation_id: Optional[str] = None

        self._lock = threading.Lock()
        self._load_conversations()

    def _load_conversations(self):
        index_file = self.storage_path / "index.json"
        if index_file.exists():
            try:
                with open(index_file) as f:
                    data = json.load(f)

                for conv_id in data.get("conversation_ids", []):
                    conv_file = self.storage_path / f"{conv_id}.json"
                    if conv_file.exists():
                        try:
                            with open(conv_file) as f:
                                conv_data = json.load(f)
                            conv = Conversation(
                                conversation_id=conv_data["conversation_id"],
                                title=conv_data.get("title", "Untitled"),
                                messages=[Message.from_dict(m) for m in conv_data.get("messages", [])],
                                created_at=conv_data.get("created_at", time.time()),
                                updated_at=conv_data.get("updated_at", time.time()),
                                metadata=conv_data.get("metadata", {})
                            )
                            self.conversations[conv_id] = conv
                        except Exception:
                            pass
            except Exception:
                pass

    def _save_conversation(self, conv: Conversation):
        conv_file = self.storage_path / f"{conv.conversation_id}.json"
        with open(conv_file, 'w') as f:
            json.dump(conv.to_dict(), f, indent=2)

        self._save_index()

    def _save_index(self):
        index_file = self.storage_path / "index.json"
        data = {
            "conversation_ids": list(self.conversations.keys()),
            "active_id": self.active_conversation_id
        }
        with open(index_file, 'w') as f:
            json.dump(data, f, indent=2)

    def create_conversation(self, title: str = None, metadata: Dict = None) -> Conversation:
        with self._lock:
            if len(self.conversations) >= self.max_conversations:
                oldest = min(self.conversations.items(), key=lambda x: x[1].updated_at)
                self.delete_conversation(oldest[0])

            conv_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:16]

            conv = Conversation(
                conversation_id=conv_id,
                title=title or f"Conversation {len(self.conversations) + 1}",
                metadata=metadata or {}
            )

            self.conversations[conv_id] = conv
            self.active_conversation_id = conv_id

            self._save_conversation(conv)

            return conv

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        return self.conversations.get(conversation_id)

    def get_active_conversation(self) -> Optional[Conversation]:
        if self.active_conversation_id:
            return self.conversations.get(self.active_conversation_id)
        return None

    def set_active_conversation(self, conversation_id: str):
        if conversation_id in self.conversations:
            self.active_conversation_id = conversation_id
            self._save_index()

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Dict = None
    ) -> Optional[Message]:
        conv = self.conversations.get(conversation_id)
        if not conv:
            return None

        msg = conv.add_message(role, content, metadata)

        if len(conv.messages) > self.max_history:
            conv.messages = conv.messages[-self.max_history:]

        self._save_conversation(conv)

        return msg

    def delete_conversation(self, conversation_id: str) -> bool:
        with self._lock:
            if conversation_id in self.conversations:
                del self.conversations[conversation_id]

                conv_file = self.storage_path / f"{conversation_id}.json"
                if conv_file.exists():
                    conv_file.unlink()

                if self.active_conversation_id == conversation_id:
                    self.active_conversation_id = None

                self._save_index()
                return True
        return False

    def list_conversations(self) -> List[Conversation]:
        return sorted(
            self.conversations.values(),
            key=lambda c: c.updated_at,
            reverse=True
        )

    def get_context_window(
        self,
        conversation_id: str,
        max_tokens: int = 6000,
        preserve_recent: int = 5
    ) -> List[Dict]:
        conv = self.conversations.get(conversation_id)
        if not conv:
            return []

        budget = TokenBudget(max_tokens=max_tokens)
        truncation_point = budget.get_truncation_point(conv.messages, preserve_recent)

        return [m.to_dict() for m in conv.messages[truncation_point:]]

    def summarize_conversation(self, conversation_id: str) -> str:
        conv = self.conversations.get(conversation_id)
        if not conv:
            return ""

        if len(conv.messages) <= 10:
            return ""

        summary_parts = [
            f"Conversation: {conv.title}",
            f"Total messages: {len(conv.messages)}",
            f"Duration: {time.strftime('%Y-%m-%d %H:%M', time.localtime(conv.created_at))} to {time.strftime('%Y-%m-%d %H:%M', time.localtime(conv.updated_at))}",
        ]

        topics = self._extract_topics(conv.messages)
        if topics:
            summary_parts.append(f"Topics: {', '.join(topics[:5])}")

        return "\n".join(summary_parts)

    def _extract_topics(self, messages: List[Message]) -> List[str]:
        topics = set()

        for msg in messages:
            content = msg.content.lower()

            import re
            functions = re.findall(r'def\s+(\w+)', content)
            topics.update(functions)

            classes = re.findall(r'class\s+(\w+)', content)
            topics.update(classes)

            files = re.findall(r'[\w/]+\.(py|js|ts|java|cpp|go|rs)', content)
            topics.update(files)

        return list(topics)


class MultiTurnRAG:
    def __init__(
        self,
        conversation_manager: ConversationManager,
        retrieval_pipeline,
        context_manager,
        max_context_tokens: int = 4000
    ):
        self.conversation_manager = conversation_manager
        self.retrieval_pipeline = retrieval_pipeline
        self.context_manager = context_manager
        self.max_context_tokens = max_context_tokens

    def query(
        self,
        question: str,
        conversation_id: str = None,
        use_history: bool = True
    ) -> Dict:
        if not conversation_id:
            conv = self.conversation_manager.create_conversation()
            conversation_id = conv.conversation_id
        else:
            conv = self.conversation_manager.get_conversation(conversation_id)
            if not conv:
                conv = self.conversation_manager.create_conversation()
                conversation_id = conv.conversation_id

        self.conversation_manager.add_message(
            conversation_id,
            MessageRole.USER.value,
            question
        )

        context = []
        if use_history:
            history = self.conversation_manager.get_context_window(
                conversation_id,
                max_tokens=1000,
                preserve_recent=3
            )

            for msg in history:
                if msg["role"] == "user":
                    context.append(f"Previous question: {msg['content'][:200]}")
                elif msg["role"] == "assistant":
                    context.append(f"Previous answer: {msg['content'][:200]}")

        enhanced_question = question
        if context:
            context_str = "\n".join(context)
            enhanced_question = f"Conversation context:\n{context_str}\n\nCurrent question: {question}"

        result = self.retrieval_pipeline.retrieve(
            enhanced_question,
            return_context=True
        )

        self.conversation_manager.add_message(
            conversation_id,
            MessageRole.ASSISTANT.value,
            result.context_window.chunks[0].get('content', '')[:500] if result.chunks else "No relevant code found."
        )

        return {
            "conversation_id": conversation_id,
            "question": question,
            "answer": result,
            "sources": [c.get('metadata', {}).get('file_path', '') for c in result.chunks],
            "history": self.conversation_manager.get_context_window(conversation_id, preserve_recent=5)
        }

    def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 20
    ) -> List[Dict]:
        return self.conversation_manager.get_context_window(
            conversation_id,
            max_tokens=10000,
            preserve_recent=limit
        )


class StreamingConversationManager:
    def __init__(self, base_manager: ConversationManager):
        self.base_manager = base_manager
        self.active_streams: Dict[str, str] = {}

    def start_stream(
        self,
        conversation_id: str,
        content: str
    ) -> str:
        stream_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:16]
        self.active_streams[stream_id] = content
        return stream_id

    def append_to_stream(
        self,
        stream_id: str,
        content: str
    ):
        if stream_id in self.active_streams:
            self.active_streams[stream_id] += content

    def end_stream(
        self,
        stream_id: str,
        conversation_id: str,
        role: str = MessageRole.ASSISTANT.value
    ) -> Message:
        if stream_id in self.active_streams:
            content = self.active_streams[stream_id]
            del self.active_streams[stream_id]

            return self.base_manager.add_message(
                conversation_id,
                role,
                content
            )
        return None

    def cancel_stream(self, stream_id: str):
        if stream_id in self.active_streams:
            del self.active_streams[stream_id]
