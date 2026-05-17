"""
RAG Engine Layer - Retrieval Augmented Generation Core
Provides RAG core, embedding, LLM, and evaluation
"""

from .rag_core_engine import (
    CodeRAG,
    RAGPipeline,
    RAGImplementation,
    EmbeddingEngine,
    VectorStore,
    SearchResultItem,
    RAGAnswer,
    EmbeddingResult
)

from .language_model_and_answer_generator import (
    LLMEngine,
    LLMResponse,
    get_llm_engine,
    has_llm,
    generate_rag_answer,
    SmartRuleEngine
)

from .semantic_search_evaluator import (
    SemanticEvaluator,
    get_semantic_evaluator,
    evaluate_retrieval_quick
)

from .test_data_and_evaluation_pairs import (
    get_test_documents,
    get_test_queries,
    get_evaluation_pairs
)

from .retrieval_pipeline_processor import (
    QueryPreprocessor,
    Reranker,
    MultiRetrieval,
    ContextWindow,
    RetrievalPipeline,
    get_retrieval_pipeline
)

from .embedding_production import (
    ProductionEmbeddingEngine,
    EmbeddingCache,
    CachedEmbeddingEngine,
    create_embedding_engine
)

from .vector_index_production import (
    ProductionVectorIndex,
    HybridVectorIndex,
    SearchResult,
    create_vector_index
)

from .llm_production import (
    MultiLLMEngine,
    BaseLLMBackend,
    OpenAIBackend,
    AnthropicBackend,
    LocalModelBackend,
    create_llm_engine
)

__all__ = [
    # 核心组件
    "CodeRAG",
    "RAGPipeline",
    "RAGImplementation",
    "EmbeddingEngine",
    "VectorStore",
    "SearchResultItem",
    "RAGAnswer",
    "EmbeddingResult",

    # LLM组件
    "LLMEngine",
    "LLMResponse",
    "get_llm_engine",
    "has_llm",
    "generate_rag_answer",
    "SmartRuleEngine",

    # 评估组件
    "SemanticEvaluator",
    "get_semantic_evaluator",
    "evaluate_retrieval_quick",

    # 测试数据
    "get_test_documents",
    "get_test_queries",
    "get_evaluation_pairs",

    # 检索管道
    "QueryPreprocessor",
    "Reranker",
    "MultiRetrieval",
    "ContextWindow",
    "RetrievalPipeline",
    "get_retrieval_pipeline",

    # 生产级Embedding
    "ProductionEmbeddingEngine",
    "EmbeddingCache",
    "CachedEmbeddingEngine",
    "create_embedding_engine",

    # 生产级向量索引
    "ProductionVectorIndex",
    "HybridVectorIndex",
    "SearchResult",
    "create_vector_index",

    # 生产级LLM
    "MultiLLMEngine",
    "BaseLLMBackend",
    "OpenAIBackend",
    "AnthropicBackend",
    "LocalModelBackend",
    "create_llm_engine"
]
