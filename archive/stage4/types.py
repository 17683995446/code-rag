from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable
from enum import Enum
from abc import ABC, abstractmethod


class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    OLLAMA = "ollama"
    MOCK = "mock"


@dataclass
class LLMConfig:
    provider: LLMProvider = LLMProvider.MOCK
    model: str = "gpt-3.5-turbo"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 60
    retry_count: int = 3


@dataclass
class Message:
    role: str
    content: str


@dataclass
class ChatRequest:
    messages: List[Message]
    temperature: float = 0.7
    max_tokens: int = 2000
    stream: bool = False


@dataclass
class ChatResponse:
    content: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: str = ""


@dataclass
class CodeContext:
    query: str
    retrieved_chunks: List[Dict] = field(default_factory=list)
    enhanced_results: List[Any] = field(default_factory=list)
    language: str = "python"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QAResult:
    question: str
    answer: str
    sources: List[Dict] = field(default_factory=list)
    context_used: str = ""
    model: str = ""
    latency_ms: float = 0


@dataclass
class PromptTemplate:
    name: str
    system_prompt: str
    user_template: str

    def format(self, **kwargs) -> tuple[str, str]:
        system = self.system_prompt.format(**kwargs)
        user = self.user_template.format(**kwargs)
        return system, user
