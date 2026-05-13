from stage4.types import (
    LLMConfig, LLMProvider, Message, ChatRequest, ChatResponse,
    CodeContext, QAResult, PromptTemplate
)
from stage4.llm_client import (
    LLMClient, MockLLMClient, OpenAIClient, OllamaClient, create_llm_client
)
from stage4.prompts import PromptBuilder, DEFAULT_TEMPLATES
from stage4.qa_engine import CodeQAEngine, RAGPipeline

__all__ = [
    'LLMConfig',
    'LLMProvider',
    'Message',
    'ChatRequest',
    'ChatResponse',
    'CodeContext',
    'QAResult',
    'PromptTemplate',
    'LLMClient',
    'MockLLMClient',
    'OpenAIClient',
    'OllamaClient',
    'create_llm_client',
    'PromptBuilder',
    'DEFAULT_TEMPLATES',
    'CodeQAEngine',
    'RAGPipeline',
]


def create_qa_engine(
    provider: str = "mock",
    model: str = "gpt-3.5-turbo",
    api_key: str = None,
    base_url: str = None
) -> CodeQAEngine:
    provider_map = {
        "mock": LLMProvider.MOCK,
        "openai": LLMProvider.OPENAI,
        "ollama": LLMProvider.OLLAMA,
        "local": LLMProvider.LOCAL,
    }

    config = LLMConfig(
        provider=provider_map.get(provider.lower(), LLMProvider.MOCK),
        model=model,
        api_key=api_key,
        base_url=base_url
    )

    return CodeQAEngine(llm_config=config)


def create_rag_pipeline(
    search_func: callable,
    provider: str = "mock",
    model: str = "gpt-3.5-turbo",
    enhance_func: callable = None
) -> RAGPipeline:
    qa_engine = create_qa_engine(provider, model)
    return RAGPipeline(
        search_func=search_func,
        qa_engine=qa_engine,
        enhance_func=enhance_func
    )
