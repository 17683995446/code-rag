"""
Multi-Backend LLM Engine - 多后端LLM集成
支持OpenAI、Anthropic、本地模型、规则引擎等多种后端
"""

import os
import json
import re
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod
import hashlib

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


@dataclass
class LLMResponse:
    """LLM响应"""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    raw_response: Optional[Dict[str, Any]] = None


class BaseLLMBackend(ABC):
    """LLM后端基类"""
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """生成响应"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查是否可用"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """获取后端名称"""
        pass


class OpenAIBackend(BaseLLMBackend):
    """OpenAI后端"""
    
    def __init__(
        self,
        model: str = "gpt-3.5-turbo",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ):
        self.model = model
        self._available = False
        
        if not OPENAI_AVAILABLE:
            print("⚠️ OpenAI库未安装")
            return
        
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("⚠️ 未设置OpenAI API密钥")
            return
        
        try:
            if base_url:
                openai.api_base = base_url
            openai.api_key = api_key
            self._available = True
            print(f"✅ OpenAI后端已初始化: {model}")
        except Exception as e:
            print(f"⚠️ OpenAI初始化失败: {e}")
    
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """生成响应"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=self.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                finish_reason=response.choices[0].finish_reason,
                raw_response=response
            )
        except Exception as e:
            raise RuntimeError(f"OpenAI生成失败: {e}")
    
    def is_available(self) -> bool:
        return self._available
    
    def get_name(self) -> str:
        return f"OpenAI ({self.model})"


class AnthropicBackend(BaseLLMBackend):
    """Anthropic (Claude) 后端"""
    
    def __init__(
        self,
        model: str = "claude-3-haiku-20240307",
        api_key: Optional[str] = None,
        **kwargs
    ):
        self.model = model
        self._available = False
        self.client = None
        
        if not ANTHROPIC_AVAILABLE:
            print("⚠️ Anthropic库未安装")
            return
        
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("⚠️ 未设置Anthropic API密钥")
            return
        
        try:
            self.client = anthropic.Anthropic(api_key=api_key)
            self._available = True
            print(f"✅ Anthropic后端已初始化: {model}")
        except Exception as e:
            print(f"⚠️ Anthropic初始化失败: {e}")
    
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """生成响应"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system or "",
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            
            return LLMResponse(
                content=response.content[0].text,
                model=self.model,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                },
                finish_reason=response.stop_reason,
                raw_response=response
            )
        except Exception as e:
            raise RuntimeError(f"Anthropic生成失败: {e}")
    
    def is_available(self) -> bool:
        return self._available
    
    def get_name(self) -> str:
        return f"Anthropic ({self.model})"


class LocalModelBackend(BaseLLMBackend):
    """本地模型后端（支持Ollama等）"""
    
    def __init__(
        self,
        model: str = "llama2",
        base_url: str = "http://localhost:11434",
        **kwargs
    ):
        self.model = model
        self.base_url = base_url.rstrip('/')
        self._available = False
        self._test_connection()
    
    def _test_connection(self):
        """测试连接"""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                self._available = True
                print(f"✅ 本地模型后端已初始化: {self.model}")
            else:
                print(f"⚠️ 本地模型服务不可用: {response.status_code}")
        except Exception as e:
            print(f"⚠️ 本地模型服务连接失败: {e}")
    
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """生成响应"""
        try:
            import requests
            
            full_prompt = f"{system}\n\n{prompt}" if system else prompt
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                return LLMResponse(
                    content=data.get("response", ""),
                    model=self.model,
                    usage={},
                    finish_reason="stop",
                    raw_response=data
                )
            else:
                raise RuntimeError(f"请求失败: {response.status_code}")
        except Exception as e:
            raise RuntimeError(f"本地模型生成失败: {e}")
    
    def is_available(self) -> bool:
        return self._available
    
    def get_name(self) -> str:
        return f"Local ({self.model})"


class SmartRuleEngine(BaseLLMBackend):
    """
    智能规则引擎 - 无需外部API的LLM替代方案
    基于关键词匹配、模板生成、语义分析的混合方案
    """
    
    def __init__(self, **kwargs):
        self.name = "SmartRuleEngine"
        self._init_templates()
        self._init_keywords()
        print("✅ 智能规则引擎已初始化")
    
    def _init_templates(self):
        """初始化问答模板"""
        self.templates = {
            "definition": [
                "{term}是一个{type}，主要用于{usage}。",
                "关于{term}：它是一种{type}，可以{action}。",
                "{term}的定义：{type}的一种，特点是可以{action}。"
            ],
            "how_to": [
                "要{goal}，可以按照以下步骤操作：\n{steps}",
                "{goal}的方法如下：\n{steps}",
                "关于如何{goal}，请参考以下步骤：\n{steps}"
            ],
            "why": [
                "{reason}",
                "这是因为{reason}。",
                "原因如下：{reason}"
            ],
            "comparison": [
                "{item1}和{item2}的主要区别在于：{differences}",
                "对比{item1}与{item2}：\n{differences}",
                "{item1}与{item2}的不同点：\n{differences}"
            ],
            "summary": [
                "总结：{content}",
                "综上所述，{content}",
                "要点总结：\n{content}"
            ],
            "default": [
                "根据您的问题，关于'{query}'，以下是相关信息：\n{relevant_info}",
                "关于'{query}'：\n{relevant_info}",
                "针对'{query}'的回答：\n{relevant_info}"
            ]
        }
    
    def _init_keywords(self):
        """初始化关键词库"""
        self.keyword_patterns = {
            "definition": ["什么是", "定义", "是什么", "什么叫", "含义"],
            "how_to": ["如何", "怎么", "怎样", "步骤", "方法", "教程"],
            "why": ["为什么", "为何", "原因", "原理"],
            "comparison": ["区别", "不同", "比较", "对比", "差异"],
            "summary": ["总结", "概括", "要点", "概述"]
        }
    
    def _classify_intent(self, query: str) -> str:
        """意图分类"""
        query_lower = query.lower()
        for intent, keywords in self.keyword_patterns.items():
            if any(kw in query_lower for kw in keywords):
                return intent
        return "default"
    
    def _extract_entities(self, query: str) -> Dict[str, Any]:
        """实体提取"""
        entities = {"term": "", "type": "", "action": "", "goal": ""}
        
        patterns = {
            "term": r"(?:什么是|关于|在.*中|的)\s*([^\s，。！？]+)",
            "type": r"是\s*([^\s，。！？]+)",
            "goal": r"如何\s*(.+?)(?:\?|。|$)"
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, query)
            if match:
                entities[key] = match.group(1).strip()
        
        return entities
    
    def _generate_from_template(
        self,
        intent: str,
        query: str,
        context: Optional[List[str]] = None
    ) -> str:
        """从模板生成答案"""
        import random
        
        if intent in self.templates:
            template = random.choice(self.templates[intent])
        else:
            template = random.choice(self.templates["default"])
        
        entities = self._extract_entities(query)
        relevant_info = ""
        
        if context:
            relevant_info = "\n".join(context[:3]) if context else "暂无相关信息"
        
        substitutions = {
            "term": entities.get("term", query),
            "type": entities.get("type", "技术/概念"),
            "action": entities.get("action", "实现特定功能"),
            "goal": entities.get("goal", "完成目标"),
            "steps": "1. 准备相关材料\n2. 按照流程操作\n3. 检查结果",
            "reason": "这是基于最佳实践和设计原则的推荐做法",
            "item1": "方案A",
            "item2": "方案B",
            "differences": "1. 性能：方案A更快\n2. 易用性：方案B更简单\n3. 适用场景：各有优势",
            "content": relevant_info or "相关内容已提供",
            "query": query,
            "relevant_info": relevant_info
        }
        
        for key, value in substitutions.items():
            template = template.replace(f"{{{key}}}", value)
        
        return template
    
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        context: Optional[List[str]] = None,
        **kwargs
    ) -> LLMResponse:
        """生成响应"""
        intent = self._classify_intent(prompt)
        answer = self._generate_from_template(intent, prompt, context)
        
        return LLMResponse(
            content=answer,
            model=self.name,
            usage={"prompt_tokens": len(prompt), "completion_tokens": len(answer)},
            finish_reason="stop"
        )
    
    def is_available(self) -> bool:
        return True
    
    def get_name(self) -> str:
        return "SmartRuleEngine"


class MultiLLMEngine:
    """
    多后端LLM引擎
    自动选择可用后端，支持回退
    """
    
    def __init__(
        self,
        preferred_backend: str = "auto",
        **kwargs
    ):
        self.backends: Dict[str, BaseLLMBackend] = {}
        self.current_backend: Optional[BaseLLMBackend] = None
        self.preferred_backend = preferred_backend
        
        self._init_backends(**kwargs)
        self._select_backend()
    
    def _init_backends(self, **kwargs):
        """初始化所有后端"""
        openai_backend = OpenAIBackend(**kwargs.get("openai", {}))
        if openai_backend.is_available():
            self.backends["openai"] = openai_backend
        
        anthropic_backend = AnthropicBackend(**kwargs.get("anthropic", {}))
        if anthropic_backend.is_available():
            self.backends["anthropic"] = anthropic_backend
        
        local_backend = LocalModelBackend(**kwargs.get("local", {}))
        if local_backend.is_available():
            self.backends["local"] = local_backend
        
        rule_backend = SmartRuleEngine(**kwargs.get("rule", {}))
        self.backends["rule"] = rule_backend
        
        print(f"📦 已初始化后端: {list(self.backends.keys())}")
    
    def _select_backend(self):
        """选择后端"""
        if self.preferred_backend == "auto":
            for name in ["openai", "anthropic", "local", "rule"]:
                if name in self.backends and self.backends[name].is_available():
                    self.current_backend = self.backends[name]
                    break
        elif self.preferred_backend in self.backends:
            self.current_backend = self.backends[self.preferred_backend]
        else:
            self.current_backend = self.backends.get("rule")
        
        if self.current_backend:
            print(f"🎯 当前使用后端: {self.current_backend.get_name()}")
    
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> LLMResponse:
        """生成响应"""
        if not self.current_backend:
            raise RuntimeError("没有可用的LLM后端")
        
        try:
            return self.current_backend.generate(
                prompt, system, max_tokens, temperature, **kwargs
            )
        except Exception as e:
            print(f"⚠️ {self.current_backend.get_name()} 生成失败: {e}")
            
            for name, backend in self.backends.items():
                if backend != self.current_backend and backend.is_available():
                    try:
                        self.current_backend = backend
                        print(f"🔄 切换到后端: {backend.get_name()}")
                        return backend.generate(
                            prompt, system, max_tokens, temperature, **kwargs
                        )
                    except:
                        continue
            
            raise RuntimeError("所有LLM后端都不可用")
    
    def set_backend(self, backend_name: str):
        """设置后端"""
        if backend_name in self.backends:
            self.current_backend = self.backends[backend_name]
            print(f"🎯 已切换到后端: {self.current_backend.get_name()}")
        else:
            raise ValueError(f"未知后端: {backend_name}")
    
    def get_available_backends(self) -> List[str]:
        """获取可用后端列表"""
        return [
            name for name, backend in self.backends.items()
            if backend.is_available()
        ]
    
    def get_current_backend_name(self) -> str:
        """获取当前后端名称"""
        return self.current_backend.get_name() if self.current_backend else "None"


def create_llm_engine(
    backend: str = "auto",
    **kwargs
) -> MultiLLMEngine:
    """
    创建LLM引擎的工厂函数
    
    Args:
        backend: 后端类型 ('auto', 'openai', 'anthropic', 'local', 'rule')
        **kwargs: 其他参数
        
    Returns:
        LLM引擎实例
    """
    return MultiLLMEngine(preferred_backend=backend, **kwargs)
