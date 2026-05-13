from optimized.embedding import (
    EmbeddingEngine, EmbeddingConfig, VectorIndex, OptimizedIndexer, ChunkMetadata
)
from optimized.chunker import SemanticChunker, ChunkStrategy
from optimized.storage import SQLiteStorage, StorageFacade, DBConfig
from optimized.api_types import (
    SearchRequest, SearchResponse, QARequest, QAResponse,
    BuildRequest, BuildResponse, ConfigManager, init_config
)
from optimized.config import (
    AppConfig, ConfigLoader, get_config,
    EmbeddingConfig as OptEmbeddingConfig,
    IndexConfig, ChunkConfig, StorageConfig,
    CacheConfig as OptCacheConfig, LLMConfig, SearchConfig,
    ParallelConfig, LoggingConfig
)
from optimized.vector_db import (
    VectorConfig, FlatIndex, IVFIndex, HNSWIndex,
    VectorStore, HybridVectorIndex, ProductQuantizer
)
from optimized.sharding import (
    ShardingConfig, ShardInfo, ShardManager, ShardPlanner,
    DirectoryAnalyzer, ShardingFacade
)
from optimized.cache import (
    CacheConfig, LRUCache, LFUCache, PersistentCache,
    QueryCacheManager, CacheFacade, CacheWarmer
)
from optimized.incremental import (
    IncrementalConfig, FileChange, ChangeDetector,
    IncrementalUpdater, IncrementalFacade
)
from optimized.monitoring import (
    MetricsCollector, StructuredLogger, PerformanceMonitor,
    HealthChecker, Tracer
)
from optimized.advanced import (
    FileWatcher, IncrementalIndexer, ParallelProcessor,
    QueryCache, QueryOptimizer, IndexManager
)
from optimized.reranker import (
    CrossEncoderReranker, BM25Reranker, HybridReranker,
    QueryIntentClassifier, QueryIntent, IntentResult,
    ResultDeduplicator, DiversitySampler, MMRSampler
)
from optimized.context import (
    ContextCompressor, ContextWindow, DynamicContextManager,
    TokenEstimator, QueryRelevanceFilter, RelevanceFeedback
)
from optimized.multilingual import (
    MultilingualEmbeddingEngine, LanguageDetector, ChineseTokenizer,
    CodeAwareEmbedder, EmbeddingEnsemble, EmbeddingCache
)
from optimized.pipeline import (
    RetrievalPipeline, RetrievalConfig, RetrievalResult, PipelineStats,
    QueryPreprocessor, MultiHopRetriever, AdaptivePipeline
)
from optimized.conversation import (
    ConversationManager, Conversation, Message, MessageRole,
    MultiTurnRAG, TokenBudget
)
from optimized.streaming import (
    StreamingIndexer, StreamingFileReader, ChunkBuilder,
    BatchProcessor, BatchResult, IndexProgress
)
from optimized.llm_optimizer import (
    AdvancedPromptBuilder, PromptTemplate, PromptStrategy,
    LLMChain, LLMOptimizer, PromptCache, ResponseValidator
)
from optimized.async_api import (
    AsyncTaskManager, AsyncRAGClient, AsyncAPI,
    AsyncCache, AsyncRateLimiter, AsyncCircuitBreaker
)

try:
    from optimized.api import CodeRAGAPI, create_app
    from optimized.integration import CodeRAGSystem, create_system, quick_search
    _API_AVAILABLE = True
except ImportError:
    _API_AVAILABLE = False

__all__ = [
    'EmbeddingEngine',
    'EmbeddingConfig',
    'VectorIndex',
    'OptimizedIndexer',
    'ChunkMetadata',
    'SemanticChunker',
    'ChunkStrategy',
    'SQLiteStorage',
    'StorageFacade',
    'DBConfig',
    'SearchRequest',
    'SearchResponse',
    'QARequest',
    'QAResponse',
    'BuildRequest',
    'BuildResponse',
    'ConfigManager',
    'init_config',
    'AppConfig',
    'ConfigLoader',
    'get_config',
    'OptEmbeddingConfig',
    'IndexConfig',
    'ChunkConfig',
    'StorageConfig',
    'OptCacheConfig',
    'LLMConfig',
    'SearchConfig',
    'ParallelConfig',
    'LoggingConfig',
    'VectorConfig',
    'FlatIndex',
    'IVFIndex',
    'HNSWIndex',
    'VectorStore',
    'HybridVectorIndex',
    'ProductQuantizer',
    'ShardingConfig',
    'ShardInfo',
    'ShardManager',
    'ShardPlanner',
    'DirectoryAnalyzer',
    'ShardingFacade',
    'CacheConfig',
    'LRUCache',
    'LFUCache',
    'PersistentCache',
    'QueryCacheManager',
    'CacheFacade',
    'CacheWarmer',
    'IncrementalConfig',
    'FileChange',
    'ChangeDetector',
    'IncrementalUpdater',
    'IncrementalFacade',
    'MetricsCollector',
    'StructuredLogger',
    'PerformanceMonitor',
    'HealthChecker',
    'Tracer',
    'FileWatcher',
    'IncrementalIndexer',
    'ParallelProcessor',
    'QueryCache',
    'QueryOptimizer',
    'IndexManager',
    'CrossEncoderReranker',
    'BM25Reranker',
    'HybridReranker',
    'QueryIntentClassifier',
    'QueryIntent',
    'IntentResult',
    'ResultDeduplicator',
    'DiversitySampler',
    'MMRSampler',
    'ContextCompressor',
    'ContextWindow',
    'DynamicContextManager',
    'TokenEstimator',
    'QueryRelevanceFilter',
    'RelevanceFeedback',
    'MultilingualEmbeddingEngine',
    'LanguageDetector',
    'ChineseTokenizer',
    'CodeAwareEmbedder',
    'EmbeddingEnsemble',
    'EmbeddingCache',
    'RetrievalPipeline',
    'RetrievalConfig',
    'RetrievalResult',
    'PipelineStats',
    'QueryPreprocessor',
    'MultiHopRetriever',
    'AdaptivePipeline',
    'ConversationManager',
    'Conversation',
    'Message',
    'MessageRole',
    'MultiTurnRAG',
    'TokenBudget',
    'StreamingIndexer',
    'StreamingFileReader',
    'ChunkBuilder',
    'BatchProcessor',
    'BatchResult',
    'IndexProgress',
    'AdvancedPromptBuilder',
    'PromptTemplate',
    'PromptStrategy',
    'LLMChain',
    'LLMOptimizer',
    'PromptCache',
    'ResponseValidator',
    'AsyncTaskManager',
    'AsyncRAGClient',
    'AsyncAPI',
    'AsyncCache',
    'AsyncRateLimiter',
    'AsyncCircuitBreaker',
]

if _API_AVAILABLE:
    __all__.extend([
        'CodeRAGAPI',
        'create_app',
        'CodeRAGSystem',
        'create_system',
        'quick_search',
    ])
