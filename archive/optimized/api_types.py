from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass
class SearchRequest:
    query: str
    top_k: int = 10
    language: Optional[str] = None
    file_pattern: Optional[str] = None
    chunk_type: Optional[str] = None


@dataclass
class SearchResponse:
    results: List[Dict]
    query: str
    total: int
    latency_ms: float


@dataclass
class QARequest:
    question: str
    context_chunks: List[Dict] = field(default_factory=list)
    template: str = "code_search"
    stream: bool = False


@dataclass
class QAResponse:
    answer: str
    sources: List[Dict]
    question: str
    model: str
    latency_ms: float


@dataclass
class BuildRequest:
    source_path: str
    chunk_size: int = 512
    chunk_overlap: int = 50
    embedding_model: str = "all-MiniLM-L6-v2"
    rebuild: bool = False


@dataclass
class BuildResponse:
    status: str
    files_processed: int
    chunks_created: int
    time_seconds: float
    index_size_mb: float


class ConfigManager:
    _instance = None
    _config: Dict = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self, config_path: str = "./config.json") -> Dict:
        path = Path(config_path)
        if path.exists():
            with open(path) as f:
                self._config = json.load(f)
        return self._config

    def save(self, config_path: str = "./config.json"):
        path = Path(config_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self._config, f, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        self._config[key] = value

    def update(self, updates: Dict):
        self._config.update(updates)


config_manager = ConfigManager()


def get_default_config() -> Dict:
    return {
        "embedding": {
            "model": "all-MiniLM-L6-v2",
            "dimension": 384,
            "device": "cpu",
            "batch_size": 32
        },
        "index": {
            "type": "FlatIP",
            "chunk_size": 512,
            "chunk_overlap": 50
        },
        "storage": {
            "type": "sqlite",
            "path": "./data",
            "cache_size": 10000
        },
        "llm": {
            "provider": "mock",
            "model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 2000
        },
        "search": {
            "top_k": 10,
            "rerank": True,
            "hybrid_alpha": 0.7
        }
    }


def init_config(config_path: str = "./config.json"):
    config = config_manager.load(config_path)
    if not config:
        config = get_default_config()
        config_manager._config = config
        config_manager.save(config_path)
    return config
