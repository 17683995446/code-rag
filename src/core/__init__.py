"""
Code RAG - 产品级
基于开源生态的统一RAG系统
"""

__version__ = "1.0.0"
__author__ = "Code RAG Team"

from .rag import (
    CodeRAG,
    RAGPipeline,
    RAGImplementation,
    EmbeddingEngine,
    VectorStore,
    SearchResultItem,
    RAGAnswer,
    EmbeddingResult
)
from .settings import (
    RAGSettings,
    get_settings,
    set_settings,
    EmbeddingSettings,
    VectorDBSettings,
    LLMSettings,
    StorageSettings,
    LoggingSettings,
    APISettings
)
from .logger import (
    get_logger,
    get_root_logger,
    setup_logging,
    log_context
)

__all__ = [
    # RAG
    "CodeRAG",
    "RAGPipeline",
    "RAGImplementation",
    "EmbeddingEngine",
    "VectorStore",
    "SearchResultItem",
    "RAGAnswer",
    "EmbeddingResult",
    
    # Settings
    "RAGSettings",
    "get_settings",
    "set_settings",
    "EmbeddingSettings",
    "VectorDBSettings",
    "LLMSettings",
    "StorageSettings",
    "LoggingSettings",
    "APISettings",
    
    # Logger
    "get_logger",
    "get_root_logger",
    "setup_logging",
    "log_context"
]
