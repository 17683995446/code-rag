"""
Code RAG v19.0 - LLM集成框架
大语言模型抽象接口、代码生成、提示模板系统
"""

from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json


class LLMProvider(Enum):
    """LLM提供商"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"
    LOCAL = "local"
    CUSTOM = "custom"


@dataclass
class LLMMessage:
    """LLM消息"""
    role: str
    content: str
    metadata: Dict = field(default_factory=dict)


@dataclass
class LLMResponse:
    """LLM响应"""
    content: str
    role: str = "assistant"
    tokens_used: int = 0
    model: str = ""
    finish_reason: str = "stop"
    metadata: Dict = field(default_factory=dict)


@dataclass
class PromptTemplate:
    """提示模板"""
    name: str
    template: str
    description: str = ""
    variables: List[str] = field(default_factory=list)
    version: str = "1.0"


class BaseLLMClient:
    """LLM客户端抽象基类"""
    
    def __init__(self, provider: LLMProvider, model: str):
        self.provider = provider
        self.model = model
    
    def generate(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """生成响应"""
        raise NotImplementedError()
    
    def stream_generate(self, messages: List[LLMMessage], **kwargs):
        """流式生成"""
        raise NotImplementedError()


class SimpleLLMClient(BaseLLMClient):
    """简单LLM客户端（用于演示）"""
    
    def __init__(self, provider: LLMProvider = LLMProvider.LOCAL, model: str = "simple"):
        super().__init__(provider, model)
        self.prompt_templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, PromptTemplate]:
        """加载默认提示模板"""
        return {
            "code_explanation": PromptTemplate(
                name="code_explanation",
                template="Explain this code:\n\n{code}",
                description="解释代码",
                variables=["code"]
            ),
            "code_generation": PromptTemplate(
                name="code_generation",
                template="Generate code in {language} for: {requirement}",
                description="代码生成",
                variables=["language", "requirement"]
            ),
            "bug_fix": PromptTemplate(
                name="bug_fix",
                template="Fix the bug in this code:\n\n{code}\n\nError: {error}",
                description="修复bug",
                variables=["code", "error"]
            ),
            "code_review": PromptTemplate(
                name="code_review",
                template="Review this code:\n\n{code}",
                description="代码审查",
                variables=["code"]
            ),
        }
    
    def generate(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        """简单的模拟生成"""
        # 组合所有消息
        full_content = "\n".join([m.content for m in messages])
        
        # 简单的模拟响应
        response = f"[Simulated {self.model} response]\n"
        if "explain" in full_content.lower():
            response += "This code appears to be a standard implementation.\n"
        elif "fix" in full_content.lower():
            response += "Here's a suggested fix for the issue.\n"
        elif "generate" in full_content.lower():
            response += "Here is the generated code.\n"
        else:
            response += "Processing your request.\n"
        
        return LLMResponse(
            content=response,
            model=self.model,
            tokens_used=len(full_content.split()) // 4,
            finish_reason="stop"
        )


class PromptManager:
    """提示管理系统"""
    
    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self.default_templates = self._load_defaults()
    
    def _load_defaults(self):
        """加载默认模板"""
        return {
            "code_explanation": PromptTemplate(
                name="code_explanation",
                template="Explain this code:\n\n{code}",
                variables=["code"]
            ),
            "code_review": PromptTemplate(
                name="code_review",
                template="Review this {language} code:\n\n{code}",
                variables=["language", "code"]
            ),
            "bug_diagnosis": PromptTemplate(
                name="bug_diagnosis",
                template="Diagnose this error:\nCode: {code}\nError: {error}",
                variables=["code", "error"]
            ),
            "code_refactor": PromptTemplate(
                name="code_refactor",
                template="Refactor this {language} code to be better:\n\n{code}",
                variables=["language", "code"]
            ),
        }
    
    def render(self, template_name: str, **variables) -> str:
        """渲染提示模板"""
        if template_name in self.templates:
            template = self.templates[template_name]
        elif template_name in self.default_templates:
            template = self.default_templates[template_name]
        else:
            return f"Template not found: {template_name}"
        
        try:
            return template.template.format(**variables)
        except KeyError as e:
            return f"Missing variable: {e}"
    
    def add_template(self, template: PromptTemplate):
        """添加模板"""
        self.templates[template.name] = template


class CodeGenAssistant:
    """代码生成助手"""
    
    def __init__(self, llm_client: Optional[BaseLLMClient] = None):
        self.llm = llm_client or SimpleLLMClient()
        self.prompt_manager = PromptManager()
    
    def explain_code(self, code: str) -> LLMResponse:
        """解释代码"""
        prompt = self.prompt_manager.render("code_explanation", code=code)
        messages = [LLMMessage(role="user", content=prompt)]
        return self.llm.generate(messages)
    
    def generate_code(self, requirement: str, language: str = "python") -> LLMResponse:
        """生成代码"""
        prompt = self.prompt_manager.render("code_generation", language=language, requirement=requirement)
        messages = [LLMMessage(role="user", content=prompt)]
        return self.llm.generate(messages)
    
    def fix_bug(self, code: str, error: str) -> LLMResponse:
        """修复bug"""
        prompt = self.prompt_manager.render("bug_fix", code=code, error=error)
        messages = [LLMMessage(role="user", content=prompt)]
        return self.llm.generate(messages)
    
    def review_code(self, code: str, language: str = "python") -> LLMResponse:
        """审查代码"""
        prompt = self.prompt_manager.render("code_review", language=language, code=code)
        messages = [LLMMessage(role="user", content=prompt)]
        return self.llm.generate(messages)


def create_llm_service(provider: str = "local", model: str = "simple") -> CodeGenAssistant:
    """创建LLM服务"""
    provider_enum = LLMProvider(provider) if provider in [p.value for p in LLMProvider] else LLMProvider.LOCAL
    client = SimpleLLMClient(provider=provider_enum, model=model)
    return CodeGenAssistant(client)
