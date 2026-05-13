import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class IndexConfig:
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384
    chunk_size: int = 512
    chunk_overlap: int = 50
    index_type: str = "FlatIP"


@dataclass
class StorageConfig:
    index_path: str = "./data/index.faiss"
    metadata_path: str = "./data/metadata.json"
    bm25_path: str = "./data/bm25.pkl"


@dataclass
class SearchConfig:
    top_k: int = 10
    rerank_top_k: int = 5
    hybrid_alpha: float = 0.7


@dataclass
class Config:
    index: IndexConfig = field(default_factory=IndexConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    search: SearchConfig = field(default_factory=SearchConfig)

    @classmethod
    def load(cls, path: str = "config.yaml") -> "Config":
        config_file = Path(path)
        if config_file.exists():
            with open(path) as f:
                data = yaml.safe_load(f)
            return cls(
                index=IndexConfig(**data.get("index", {})),
                storage=StorageConfig(**data.get("storage", {})),
                search=SearchConfig(**data.get("search", {}))
            )
        return cls()


config = Config.load()
