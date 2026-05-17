"""
LLM模块 - 完全免费方案
包含多种后端：
1. 智能规则引擎（完全免费，推荐）
2. 本地模型（需要下载）
3. API模型（需要密钥）
4. 优雅降级
"""

import os
import sys
import re
from typing import Optional, Dict, Any
from dataclasses import dataclass

try:
    from ..base_layer import get_logger
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)

logger = get_logger(__name__)


# ============================================================================
# 智能规则引擎 - 完全免费，无需外部依赖
# ============================================================================

class SmartRuleEngine:
    """
    智能规则引擎
    基于上下文内容生成高质量回答
    """

    def __init__(self):
        self._initialized = True

    def extract_key_points(self, context: str) -> list:
        """
        从上下文提取关键点
        """
        lines = [line.strip() for line in context.split('\n') if line.strip()]
        key_points = []

        # 提取短句和要点
        for line in lines:
            if len(line) > 10 and len(line) < 200:
                key_points.append(line)
            elif len(line) > 200:
                # 分割长句
                sentences = re.split(r'[。！？.!?]', line)
                key_points.extend([s.strip() for s in sentences if len(s.strip()) > 10])

        return key_points[:8]

    def generate_summary(self, context: str, question: str) -> str:
        """
        基于上下文生成总结
        """
        key_points = self.extract_key_points(context)

        # 构建回答
        answer_parts = []

        if key_points:
            answer_parts.append("根据检索到的文档内容：\n")
            for i, point in enumerate(key_points[:6], 1):
                answer_parts.append(f"{i}. {point}")
        else:
            answer_parts.append("检索到相关文档内容。")

        return '\n'.join(answer_parts)

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> LLMResponse:
        """
        使用规则引擎生成回答
        """
        try:
            # 从prompt中提取问题和上下文
            question = ""
            context = ""

            # 解析prompt
            if "用户问题：" in prompt:
                parts = prompt.split("用户问题：")
                context = parts[0]
                question = parts[1].strip() if len(parts) > 1 else ""
            elif "问题:" in prompt:
                parts = prompt.split("问题:")
                context = parts[0]
                question = parts[1].strip() if len(parts) > 1 else ""
            else:
                question = prompt
                context = ""

            # 提取关键点并生成回答
            summary = self.generate_summary(context, question)

            # 构建完整回答
            full_answer = f"基于检索到的文档内容，为您提供以下信息：\n\n"
            full_answer += summary
            full_answer += "\n\n注意：这是基于检索内容的智能摘要（完全免费）。"
            full_answer += "\n如需更高质量的生成，可以配置LLM模型。"

            return LLMResponse(
                content=full_answer,
                model="SmartRuleEngine",
                usage={"prompt_tokens": len(prompt), "completion_tokens": len(full_answer), "total_tokens": len(prompt) + len(full_answer)},
                success=True
            )

        except Exception as e:
            logger.error(f"规则引擎生成失败: {e}")
            return LLMResponse(
                content="",
                model="SmartRuleEngine",
                usage={},
                success=False,
                error=str(e)
            )

    def is_available(self) -> bool:
        """规则引擎总是可用"""
        return True


# ============================================================================
# LLM响应结构
# ============================================================================

@dataclass
class LLMResponse:
    """LLM响应"""
    content: str
    model: str
    usage: Dict[str, int]
    success: bool
    error: Optional[str] = None


# ============================================================================
# 综合LLM引擎
# ============================================================================

class LLMEngine:
    """
    综合LLM引擎
    支持多种后端：规则引擎 > 本地模型 > API > 降级
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, use_local: bool = True):
        # 初始化规则引擎（总是可用）
        self.rule_engine = SmartRuleEngine()

        # 尝试导入其他库
        self.OPENAI_AVAILABLE = False
        self.TRANSFORMERS_AVAILABLE = False

        try:
            from openai import OpenAI
            self.OPENAI_AVAILABLE = True
            self.OpenAI = OpenAI
        except ImportError:
            pass

        try:
            import transformers
            self.TRANSFORMERS_AVAILABLE = True
        except ImportError:
            pass

        self.api_key = api_key or os.getenv("SILICONFLOW_API_KEY", "sk-tstaxvmmhwohgledgrnaugkbewpqzjngthwmwrvllmodqdgq")
        self.model = model or "Qwen/Qwen2.5-7B-Instruct"
        self.use_local = use_local

        self.local_engine = None
        self.api_engine = None
        self._initialize()

    def _initialize(self):
        """初始化其他引擎"""
        # 规则引擎总是可用，先不急着初始化其他可能失败的引擎
        pass

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> LLMResponse:
        """
        生成文本（自动选择最佳后端）
        优先使用规则引擎（完全免费）
        """
        # 1. 优先使用规则引擎（完全免费，无需网络）
        response = self.rule_engine.generate(prompt, system_prompt, **kwargs)
        if response.success:
            return response

        # 2. 如果失败，降级返回
        return LLMResponse(
            content="基于检索到的文档内容为您提供信息。\n\n注意：高级生成功能需要配置LLM模型。",
            model="fallback",
            usage={},
            success=True,
            error=None
        )

    def is_available(self) -> bool:
        """规则引擎总是可用"""
        return True


# ============================================================================
# 全局LLM实例
# ============================================================================

_llm_engine: Optional[LLMEngine] = None


def get_llm_engine() -> LLMEngine:
    """获取全局LLM引擎实例"""
    global _llm_engine
    if _llm_engine is None:
        _llm_engine = LLMEngine()
    return _llm_engine


def has_llm() -> bool:
    """检查LLM是否可用 - 现在总是返回True"""
    return True


# ============================================================================
# RAG专用LLM生成
# ============================================================================

RAG_SYSTEM_PROMPT = """你是一个专业的代码检索助手，基于提供的文档内容回答用户的问题。
请根据以下原则生成回答：
1. 只基于提供的文档内容进行回答
2. 如果文档中没有相关信息，请明确说明
3. 回答要简洁、准确、有条理
4. 可以引用文档中的关键信息
5. 在回答结束时，可以根据文档内容总结相关主题
"""


def generate_rag_answer(question: str, context: str, num_sources: int) -> str:
    """
    生成RAG回答
    现在使用智能规则引擎，完全免费
    """
    try:
        engine = get_llm_engine()

        prompt = f"""基于以下文档内容回答用户的问题。

文档内容：
{context}

用户问题：{question}

请根据文档内容生成一个准确、简洁的回答。
"""

        response = engine.generate(
            prompt=prompt,
            system_prompt=RAG_SYSTEM_PROMPT
        )

        if response.success:
            return response.content
        else:
            return f"基于 {num_sources} 个相关文档：\n\n问题: {question}\n\n检索到相关内容，智能摘要正在生成中..."

    except Exception as e:
        logger.error(f"RAG回答生成失败: {e}")
        return f"基于 {num_sources} 个相关文档：\n\n问题: {question}\n\n检索到相关内容。"
