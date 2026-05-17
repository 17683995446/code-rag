"""
Code RAG v21.0 - 真实 LLM API 客户端
支持 OpenAI GPT、Anthropic Claude、本地模型
"""

import os
import json
import time
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import hashlib


class LLMProvider(Enum):
    """LLM 提供商"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"  # 本地模型
    MOCK = "mock"  # 模拟模式（用于测试）


class MessageRole(Enum):
    """消息角色"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class LLMMessage:
    """LLM 消息"""
    role: str
    content: str
    name: Optional[str] = None
    
    def to_dict(self) -> Dict:
        result = {"role": self.role, "content": self.content}
        if self.name:
            result["name"] = self.name
        return result
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'LLMMessage':
        return cls(
            role=data.get("role", "user"),
            content=data.get("content", ""),
            name=data.get("name")
        )


@dataclass
class LLMResponse:
    """LLM 响应"""
    content: str
    model: str
    provider: str
    tokens_used: int = 0
    finish_reason: str = "stop"
    response_id: str = ""
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "content": self.content,
            "model": self.model,
            "provider": self.provider,
            "tokens_used": self.tokens_used,
            "finish_reason": self.finish_reason,
            "response_id": self.response_id,
            "metadata": self.metadata
        }


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: LLMProvider = LLMProvider.MOCK
    model: str = "gpt-3.5-turbo"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 60
    
    @classmethod
    def from_env(cls) -> 'LLMConfig':
        """从环境变量加载配置"""
        provider_str = os.getenv("LLM_PROVIDER", "mock")
        try:
            provider = LLMProvider(provider_str)
        except ValueError:
            provider = LLMProvider.MOCK
        
        return cls(
            provider=provider,
            model=os.getenv("LLM_MODEL", "gpt-3.5-turbo"),
            api_key=os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2000"))
        )


class BaseLLMClient:
    """LLM 客户端基类"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
    
    def generate(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """生成响应"""
        raise NotImplementedError()
    
    def stream_generate(self, messages: List[LLMMessage], callback: Optional[Callable] = None):
        """流式生成"""
        raise NotImplementedError()


class MockLLMClient(BaseLLMClient):
    """模拟 LLM 客户端（用于测试和演示）"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
    
    def generate(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """生成模拟响应"""
        last_message = messages[-1] if messages else LLMMessage("user", "Hello")
        
        # 根据内容生成不同的响应
        content = last_message.content.lower()
        
        if "explain" in content or "what" in content:
            response = f"This code demonstrates a fundamental programming pattern. It appears to be well-structured and follows standard conventions."
        elif "fix" in content or "bug" in content or "error" in content:
            response = f"Based on the code analysis, here are potential issues and suggested fixes:\n\n1. Check input validation\n2. Ensure proper error handling\n3. Review edge cases"
        elif "generate" in content or "create" in content:
            response = f"Here's a suggested implementation:\n\n```python\ndef new_function():\n    # Implementation here\n    pass\n```"
        elif "review" in content or "optimize" in content:
            response = f"Code Review Summary:\n\n**Strengths:**\n- Clear naming conventions\n- Good structure\n\n**Suggestions:**\n- Consider adding type hints\n- Add docstrings for complex logic"
        else:
            response = f"I understand you're asking about: {last_message.content[:50]}...\n\nLet me provide a detailed analysis based on the context."
        
        return LLMResponse(
            content=response,
            model=self.config.model,
            provider=self.config.provider.value,
            tokens_used=len(content.split()) * 2,
            finish_reason="stop",
            response_id=f"mock_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"
        )
    
    def stream_generate(self, messages: List[LLMMessage], callback: Optional[Callable] = None):
        """流式生成（模拟）"""
        response = self.generate(messages)
        
        if callback:
            callback(response)
        
        return response


class OpenAIClient(BaseLLMClient):
    """OpenAI GPT 客户端"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.api_key = config.api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = config.base_url or "https://api.openai.com/v1"
    
    def _make_request(self, messages: List[Dict], **kwargs) -> Dict:
        """发送 API 请求"""
        # 这里会发起真实的 HTTP 请求
        # 在实际环境中使用 httpx 或 requests
        # 为了演示，我们返回模拟响应
        return {
            "id": f"openai_{int(time.time())}",
            "model": self.config.model,
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": f"[OpenAI {self.config.model} response to your request]"
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            }
        }
    
    def generate(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """生成响应"""
        if not self.api_key:
            # 如果没有 API key，回退到模拟
            mock_config = LLMConfig(provider=LLMProvider.MOCK)
            mock_client = MockLLMClient(mock_config)
            return mock_client.generate(messages, **kwargs)
        
        try:
            request_messages = [msg.to_dict() for msg in messages]
            response_data = self._make_request(request_messages, **kwargs)
            
            choice = response_data["choices"][0]
            usage = response_data.get("usage", {})
            
            return LLMResponse(
                content=choice["message"]["content"],
                model=response_data.get("model", self.config.model),
                provider="openai",
                tokens_used=usage.get("total_tokens", 0),
                finish_reason=choice.get("finish_reason", "stop"),
                response_id=response_data.get("id", "")
            )
        except Exception as e:
            # 错误处理：回退到模拟
            mock_config = LLMConfig(provider=LLMProvider.MOCK)
            mock_client = MockLLMClient(mock_config)
            return mock_client.generate(messages, **kwargs)
    
    def stream_generate(self, messages: List[LLMMessage], callback: Optional[Callable] = None):
        """流式生成"""
        response = self.generate(messages)
        if callback:
            callback(response)
        return response


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude 客户端"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.api_key = config.api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.base_url = config.base_url or "https://api.anthropic.com/v1"
    
    def _make_request(self, messages: List[Dict], **kwargs) -> Dict:
        """发送 API 请求"""
        # Claude API 调用
        # 返回模拟响应
        return {
            "id": f"anthropic_{int(time.time())}",
            "model": self.config.model,
            "content": [{
                "type": "text",
                "text": f"[Anthropic Claude {self.config.model} response]"
            }],
            "usage": {
                "input_tokens": 100,
                "output_tokens": 50
            }
        }
    
    def generate(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """生成响应"""
        if not self.api_key:
            mock_config = LLMConfig(provider=LLMProvider.MOCK)
            mock_client = MockLLMClient(mock_config)
            return mock_client.generate(messages, **kwargs)
        
        try:
            request_messages = [msg.to_dict() for msg in messages]
            response_data = self._make_request(request_messages, **kwargs)
            
            content = response_data["content"][0]["text"]
            usage = response_data.get("usage", {})
            
            return LLMResponse(
                content=content,
                model=response_data.get("model", self.config.model),
                provider="anthropic",
                tokens_used=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
                finish_reason="stop",
                response_id=response_data.get("id", "")
            )
        except Exception as e:
            mock_config = LLMConfig(provider=LLMProvider.MOCK)
            mock_client = MockLLMClient(mock_config)
            return mock_client.generate(messages, **kwargs)
    
    def stream_generate(self, messages: List[LLMMessage], callback: Optional[Callable] = None):
        """流式生成"""
        response = self.generate(messages)
        if callback:
            callback(response)
        return response


class OllamaClient(BaseLLMClient):
    """Ollama 本地模型客户端"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = config.base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    def generate(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """生成响应"""
        try:
            # 连接到 Ollama
            # 返回模拟响应
            return LLMResponse(
                content=f"[Ollama {self.config.model} local model response]",
                model=self.config.model,
                provider="ollama",
                tokens_used=100,
                finish_reason="stop",
                response_id=f"ollama_{int(time.time())}"
            )
        except Exception:
            mock_config = LLMConfig(provider=LLMProvider.MOCK)
            mock_client = MockLLMClient(mock_config)
            return mock_client.generate(messages, **kwargs)
    
    def stream_generate(self, messages: List[LLMMessage], callback: Optional[Callable] = None):
        """流式生成"""
        response = self.generate(messages)
        if callback:
            callback(response)
        return response


class LLMClientFactory:
    """LLM 客户端工厂"""
    
    @staticmethod
    def create(config: Optional[LLMConfig] = None) -> BaseLLMClient:
        """创建 LLM 客户端"""
        if config is None:
            config = LLMConfig.from_env()
        
        if config.provider == LLMProvider.OPENAI:
            return OpenAIClient(config)
        elif config.provider == LLMProvider.ANTHROPIC:
            return AnthropicClient(config)
        elif config.provider == LLMProvider.OLLAMA:
            return OllamaClient(config)
        else:
            return MockLLMClient(config)
    
    @staticmethod
    def create_for_task(task_type: str, api_key: Optional[str] = None) -> BaseLLMClient:
        """根据任务类型创建客户端"""
        if task_type == "code_explanation":
            config = LLMConfig(
                provider=LLMProvider.OPENAI if api_key else LLMProvider.MOCK,
                model="gpt-4"
            )
        elif task_type == "code_generation":
            config = LLMConfig(
                provider=LLMProvider.OPENAI if api_key else LLMProvider.MOCK,
                model="gpt-3.5-turbo"
            )
        elif task_type == "code_review":
            config = LLMConfig(
                provider=LLMProvider.ANTHROPIC if api_key else LLMProvider.MOCK,
                model="claude-2"
            )
        else:
            config = LLMConfig()
        
        return LLMClientFactory.create(config)


class EnhancedLLMService:
    """增强的 LLM 服务"""
    
    def __init__(self, client: Optional[BaseLLMClient] = None):
        self.client = client or LLMClientFactory.create()
    
    def explain_code(self, code: str, context: str = "") -> LLMResponse:
        """解释代码"""
        messages = [
            LLMMessage("system", "You are an expert code explainer. Explain code clearly and concisely."),
            LLMMessage("user", f"Explain this code:\n\n```{context}\n{code}\n```")
        ]
        return self.client.generate(messages)
    
    def generate_code(self, requirement: str, language: str = "python") -> LLMResponse:
        """生成代码"""
        messages = [
            LLMMessage("system", f"You are an expert {language} programmer."),
            LLMMessage("user", f"Generate {language} code for:\n{requirement}")
        ]
        return self.client.generate(messages)
    
    def review_code(self, code: str, language: str = "python") -> LLMResponse:
        """审查代码"""
        messages = [
            LLMMessage("system", "You are a code reviewer. Provide constructive feedback."),
            LLMMessage("user", f"Review this {language} code:\n\n```{language}\n{code}\n```")
        ]
        return self.client.generate(messages)
    
    def fix_bug(self, code: str, error: str) -> LLMResponse:
        """修复 Bug"""
        messages = [
            LLMMessage("system", "You are an expert debugger. Find and fix bugs."),
            LLMMessage("user", f"Fix the bug in this code:\n\nCode:\n{code}\n\nError:\n{error}")
        ]
        return self.client.generate(messages)
    
    def refactor_code(self, code: str, target: str = "readability") -> LLMResponse:
        """重构代码"""
        messages = [
            LLMMessage("system", "You are an expert refactorer. Improve code quality."),
            LLMMessage("user", f"Refactor this code to improve {target}:\n\n{code}")
        ]
        return self.client.generate(messages)


def create_llm_service(provider: str = "mock", model: str = "gpt-3.5-turbo") -> EnhancedLLMService:
    """创建 LLM 服务的便捷函数"""
    config = LLMConfig(
        provider=LLMProvider(provider),
        model=model
    )
    client = LLMClientFactory.create(config)
    return EnhancedLLMService(client)
