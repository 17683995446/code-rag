import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


@dataclass
class EmbeddingConfig:
    model: str = "all-MiniLM-L6-v2"
    dimension: int = 384
    device: str = "cpu"
    batch_size: int = 32
    max_length: int = 512
    normalize: bool = True
    fallback_on_error: bool = True


@dataclass
class IndexConfig:
    type: str = "FlatIP"
    nlist: int = 100
    nprobe: int = 10
    quantize: bool = False
    compression_ratio: float = 0.1


@dataclass
class ChunkConfig:
    max_size: int = 512
    overlap: int = 50
    min_size: int = 10
    split_by_symbol: bool = True
    preserve_docstring: bool = True
    preserve_imports: bool = True


@dataclass
class StorageConfig:
    type: str = "sqlite"
    path: str = "./data"
    cache_size: int = 10000
    wal_mode: bool = True
    mmap_size: int = 268435456


@dataclass
class CacheConfig:
    enabled: bool = True
    max_size: int = 1000
    ttl_seconds: int = 3600
    backend: str = "memory"


@dataclass
class LLMConfig:
    provider: str = "mock"
    model: str = "gpt-3.5-turbo"
    api_key: str = ""
    base_url: str = ""
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 60
    retry_count: int = 3


@dataclass
class SearchConfig:
    top_k: int = 10
    rerank: bool = True
    hybrid_alpha: float = 0.7
    min_score: float = 0.0
    max_context_length: int = 8000


@dataclass
class ParallelConfig:
    max_workers: int = 4
    use_processes: bool = False
    batch_size: int = 32


@dataclass
class LoggingConfig:
    level: str = "INFO"
    format: str = "json"
    file: str = ""
    max_size_mb: int = 100
    backup_count: int = 5


@dataclass
class AppConfig:
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    index: IndexConfig = field(default_factory=IndexConfig)
    chunk: ChunkConfig = field(default_factory=ChunkConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    parallel: ParallelConfig = field(default_factory=ParallelConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    def to_dict(self) -> Dict:
        return {
            'embedding': asdict(self.embedding),
            'index': asdict(self.index),
            'chunk': asdict(self.chunk),
            'storage': asdict(self.storage),
            'cache': asdict(self.cache),
            'llm': asdict(self.llm),
            'search': asdict(self.search),
            'parallel': asdict(self.parallel),
            'logging': asdict(self.logging)
        }


class ConfigLoader:
    ENV_PREFIX = "CODE_RAG_"

    def __init__(self, config_path: str = None):
        self.config_path = Path(config_path) if config_path else None
        self.config = AppConfig()

    def load(self) -> AppConfig:
        if self.config_path and self.config_path.exists():
            self._load_from_file()

        self._load_from_env()

        return self.config

    def _load_from_file(self):
        content = self.config_path.read_text()

        if self.config_path.suffix in ('.yaml', '.yml'):
            if not YAML_AVAILABLE:
                return
            data = yaml.safe_load(content)
        elif self.config_path.suffix == '.json':
            data = json.loads(content)
        else:
            return

        if 'embedding' in data:
            self.config.embedding = EmbeddingConfig(**{
                **asdict(self.config.embedding),
                **data['embedding']
            })

        if 'index' in data:
            self.config.index = IndexConfig(**{
                **asdict(self.config.index),
                **data['index']
            })

        if 'chunk' in data:
            self.config.chunk = ChunkConfig(**{
                **asdict(self.config.chunk),
                **data['chunk']
            })

        if 'storage' in data:
            self.config.storage = StorageConfig(**{
                **asdict(self.config.storage),
                **data['storage']
            })

        if 'cache' in data:
            self.config.cache = CacheConfig(**{
                **asdict(self.config.cache),
                **data['cache']
            })

        if 'llm' in data:
            self.config.llm = LLMConfig(**{
                **asdict(self.config.llm),
                **data['llm']
            })

        if 'search' in data:
            self.config.search = SearchConfig(**{
                **asdict(self.config.search),
                **data['search']
            })

        if 'parallel' in data:
            self.config.parallel = ParallelConfig(**{
                **asdict(self.config.parallel),
                **data['parallel']
            })

        if 'logging' in data:
            self.config.logging = LoggingConfig(**{
                **asdict(self.config.logging),
                **data['logging']
            })

    def _load_from_env(self):
        env_mappings = {
            'EMBEDDING_MODEL': ('embedding', 'model'),
            'EMBEDDING_DEVICE': ('embedding', 'device'),
            'EMBEDDING_BATCH_SIZE': ('embedding', 'batch_size'),
            'INDEX_TYPE': ('index', 'type'),
            'CHUNK_MAX_SIZE': ('chunk', 'max_size'),
            'CHUNK_OVERLAP': ('chunk', 'overlap'),
            'STORAGE_PATH': ('storage', 'path'),
            'CACHE_MAX_SIZE': ('cache', 'max_size'),
            'CACHE_TTL': ('cache', 'ttl_seconds'),
            'LLM_PROVIDER': ('llm', 'provider'),
            'LLM_MODEL': ('llm', 'model'),
            'LLM_API_KEY': ('llm', 'api_key'),
            'LLM_BASE_URL': ('llm', 'base_url'),
            'LLM_TEMPERATURE': ('llm', 'temperature'),
            'SEARCH_TOP_K': ('search', 'top_k'),
            'PARALLEL_MAX_WORKERS': ('parallel', 'max_workers'),
            'LOG_LEVEL': ('logging', 'level'),
        }

        for env_key, (section, attr) in env_mappings.items():
            full_key = f"{self.ENV_PREFIX}{env_key}"
            value = os.environ.get(full_key)

            if value is not None:
                section_obj = getattr(self.config, section)
                current_value = getattr(section_obj, attr)

                if isinstance(current_value, bool):
                    value = value.lower() in ('true', '1', 'yes')
                elif isinstance(current_value, int):
                    value = int(value)
                elif isinstance(current_value, float):
                    value = float(value)

                setattr(section_obj, attr, value)

    def save(self, path: str = None):
        save_path = Path(path) if path else self.config_path
        if not save_path:
            save_path = Path("config.yaml")

        save_path.parent.mkdir(parents=True, exist_ok=True)

        data = self.config.to_dict()

        if save_path.suffix in ('.yaml', '.yml'):
            if YAML_AVAILABLE:
                with open(save_path, 'w') as f:
                    yaml.dump(data, f, default_flow_style=False)
            else:
                save_path = save_path.with_suffix('.json')
                with open(save_path, 'w') as f:
                    json.dump(data, f, indent=2)
        else:
            with open(save_path, 'w') as f:
                json.dump(data, f, indent=2)

    @staticmethod
    def from_env() -> AppConfig:
        loader = ConfigLoader()
        return loader.load()

    @staticmethod
    def from_file(path: str) -> AppConfig:
        loader = ConfigLoader(path)
        return loader.load()


def get_config(config_path: str = None) -> AppConfig:
    if config_path:
        return ConfigLoader.from_file(config_path)
    return ConfigLoader.from_env()


DEFAULT_CONFIG_YAML = """
embedding:
  model: all-MiniLM-L6-v2
  dimension: 384
  device: cpu
  batch_size: 32

index:
  type: FlatIP
  nlist: 100
  quantize: false

chunk:
  max_size: 512
  overlap: 50
  split_by_symbol: true

storage:
  type: sqlite
  path: ./data
  cache_size: 10000

cache:
  enabled: true
  max_size: 1000
  ttl_seconds: 3600

llm:
  provider: mock
  model: gpt-3.5-turbo
  temperature: 0.7
  max_tokens: 2000

search:
  top_k: 10
  rerank: true
  hybrid_alpha: 0.7

parallel:
  max_workers: 4

logging:
  level: INFO
  format: json
"""


def create_default_config(path: str = "config.yaml"):
    Path(path).write_text(DEFAULT_CONFIG_YAML.strip())
