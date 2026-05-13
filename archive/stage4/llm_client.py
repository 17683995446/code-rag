import os
import time
import json
from typing import List, Optional, Iterator, Dict, Any
from abc import ABC, abstractmethod

from stage4.types import (
    LLMConfig, LLMProvider, Message, ChatRequest, ChatResponse
)


class LLMClient(ABC):
    @abstractmethod
    def chat(self, messages: List[Message], **kwargs) -> ChatResponse:
        pass

    @abstractmethod
    def chat_stream(self, messages: List[Message], **kwargs) -> Iterator[str]:
        pass

    def count_tokens(self, text: str) -> int:
        return len(text.split()) // 4


class MockLLMClient(LLMClient):
    def __init__(self, config: LLMConfig):
        self.config = config

    def chat(self, messages: List[Message], **kwargs) -> ChatResponse:
        last_message = messages[-1].content if messages else ""

        response = self._generate_mock_response(last_message, messages)

        return ChatResponse(
            content=response,
            model=self.config.model,
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            finish_reason="stop"
        )

    def chat_stream(self, messages: List[Message], **kwargs) -> Iterator[str]:
        response = self._generate_mock_response(messages[-1].content if messages else "", messages)
        for word in response.split():
            yield word + " "
            time.sleep(0.05)

    def _generate_mock_response(self, query: str, messages: List[Message]) -> str:
        query_lower = query.lower()

        if any(k in query_lower for k in ['what', 'how', 'explain']):
            return f"Based on the provided code context, here's an explanation:\n\nThe code you're asking about performs the requested operation. It uses standard programming patterns and best practices. The implementation handles various edge cases and provides efficient processing."
        elif any(k in query_lower for k in ['find', 'where', 'locate']):
            return "I found the relevant code sections in the codebase. The main implementation is located in the core modules, with supporting functions in utility files."
        elif any(k in query_lower for k in ['fix', 'bug', 'error']):
            return "Looking at the code, I can identify potential issues. Here are the problems and suggested fixes:\n\n1. Check input validation\n2. Add error handling\n3. Verify type consistency"
        elif any(k in query_lower for k in ['implement', 'create', 'write']):
            return "Here's a suggested implementation based on the code context:\n\n```python\n# Implementation would go here\ndef solution():\n    pass\n```"
        else:
            return f"I've analyzed the code related to your query. The implementation follows standard patterns. You can find the relevant code in the context provided above."


class OpenAIClient(LLMClient):
    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = None
        self._init_client()

    def _init_client(self):
        try:
            from openai import OpenAI
            api_key = self.config.api_key or os.environ.get("OPENAI_API_KEY")
            base_url = self.config.base_url

            if base_url:
                self.client = OpenAI(api_key=api_key, base_url=base_url)
            else:
                self.client = OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("OpenAI package not installed. Run: pip install openai")

    def chat(self, messages: List[Message], **kwargs) -> ChatResponse:
        start_time = time.time()

        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": m.role, "content": m.content} for m in messages],
                temperature=kwargs.get("temperature", self.config.temperature),
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens)
            )

            latency = (time.time() - start_time) * 1000

            return ChatResponse(
                content=response.choices[0].message.content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                finish_reason=response.choices[0].finish_reason
            )
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {e}")

    def chat_stream(self, messages: List[Message], **kwargs) -> Iterator[str]:
        try:
            stream = self.client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": m.role, "content": m.content} for m in messages],
                temperature=kwargs.get("temperature", self.config.temperature),
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                stream=True
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            raise RuntimeError(f"OpenAI API stream error: {e}")


class OllamaClient(LLMClient):
    def __init__(self, config: LLMConfig):
        self.config = config
        self.base_url = config.base_url or "http://localhost:11434"

    def chat(self, messages: List[Message], **kwargs) -> ChatResponse:
        start_time = time.time()

        try:
            import requests

            formatted_messages = [
                {"role": m.role, "content": m.content}
                for m in messages
            ]

            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.config.model,
                    "messages": formatted_messages,
                    "stream": False,
                    "options": {
                        "temperature": kwargs.get("temperature", self.config.temperature)
                    }
                },
                timeout=self.config.timeout
            )

            response.raise_for_status()
            data = response.json()

            latency = (time.time() - start_time) * 1000

            return ChatResponse(
                content=data.get("message", {}).get("content", ""),
                model=self.config.model,
                usage={"total_tokens": 0},
                finish_reason="stop"
            )

        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Make sure Ollama is running with: ollama serve"
            )
        except Exception as e:
            raise RuntimeError(f"Ollama API error: {e}")

    def chat_stream(self, messages: List[Message], **kwargs) -> Iterator[str]:
        try:
            import requests

            formatted_messages = [
                {"role": m.role, "content": m.content}
                for m in messages
            ]

            with requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.config.model,
                    "messages": formatted_messages,
                    "stream": True
                },
                stream=True,
                timeout=self.config.timeout
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]

        except Exception as e:
            raise RuntimeError(f"Ollama stream error: {e}")


def create_llm_client(config: LLMConfig) -> LLMClient:
    if config.provider == LLMProvider.MOCK:
        return MockLLMClient(config)
    elif config.provider == LLMProvider.OPENAI:
        return OpenAIClient(config)
    elif config.provider == LLMProvider.OLLAMA:
        return OllamaClient(config)
    elif config.provider == LLMProvider.LOCAL:
        return OllamaClient(config)
    else:
        return MockLLMClient(config)
