"""
配置管理 - 产品级
支持无依赖运行
"""

from typing import Optional, List, Dict, Any
from pathlib import Path


class SimpleSettings:
    """简单配置 - 无依赖版本"""
    
    def __init__(self):
        # Embedding
        self.embedding = SimpleEmbeddingSettings()
        
        # Vector DB
        self.vector_db = SimpleVectorDBSettings()
        
        # LLM
        self.llm = SimpleLLMSettings()
        
        # Storage
        self.storage = SimpleStorageSettings()
        
        # Logging
        self.logging = SimpleLoggingSettings()
        
        # API
        self.api = SimpleAPISettings()
        
        # Global
        self.chunk_size = 1000
        self.chunk_overlap = 100
        self.top_k = 5
        
        # 兼容性（用于向后兼容）
        self.use_langchain = False
        self.use_llama_index = False


class SimpleEmbeddingSettings:
    """Embedding配置"""
    def __init__(self):
        self.model_name = "all-MiniLM-L6-v2"
        self.device = "cpu"
        self.cache_dir = None


class SimpleVectorDBSettings:
    """向量数据库配置"""
    def __init__(self):
        self.provider = "simple"
        self.index_path = None
        self.dimension = 384
        self.persist_directory = None


class SimpleLLMSettings:
    """LLM配置"""
    def __init__(self):
        self.provider = "simple"
        self.model = "gpt-3.5-turbo"
        self.api_key = None
        self.temperature = 0.7
        self.max_tokens = 1000


class SimpleStorageSettings:
    """存储配置"""
    def __init__(self):
        self.data_dir = Path("./data")
        self.index_dir = Path("./data/indexes")
        self.cache_dir = Path("./data/cache")
        
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self.index_dir.mkdir(exist_ok=True, parents=True)
        self.cache_dir.mkdir(exist_ok=True, parents=True)


class SimpleLoggingSettings:
    """日志配置"""
    def __init__(self):
        self.level = "INFO"
        self.format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        self.file = None


class SimpleAPISettings:
    """API配置"""
    def __init__(self):
        self.host = "0.0.0.0"
        self.port = 8000
        self.debug = False


# 单例
_settings: Optional[SimpleSettings] = None


def get_settings() -> SimpleSettings:
    """获取配置单例"""
    global _settings
    if _settings is None:
        _settings = SimpleSettings()
    return _settings


def set_settings(settings: SimpleSettings):
    """设置配置单例"""
    global _settings
    _settings = settings


# 类型别名（与之前保持兼容）
EmbeddingSettings = SimpleEmbeddingSettings
VectorDBSettings = SimpleVectorDBSettings
LLMSettings = SimpleLLMSettings
StorageSettings = SimpleStorageSettings
LoggingSettings = SimpleLoggingSettings
APISettings = SimpleAPISettings
RAGSettings = SimpleSettings
