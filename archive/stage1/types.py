from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Any
from pathlib import Path
import hashlib
import json


@dataclass
class CodeSymbol:
    name: str
    symbol_type: str
    start_line: int
    end_line: int
    visibility: str = "public"
    signature: str = ""
    docstring: str = ""
    decorators: List[str] = field(default_factory=list)
    children: List['CodeSymbol'] = field(default_factory=list)


@dataclass
class CodeChunk:
    chunk_id: str
    content: str
    file_path: str
    language: str
    start_line: int
    end_line: int
    chunk_type: str
    parent_symbol: Optional[CodeSymbol] = None
    symbols: List[CodeSymbol] = field(default_factory=list)
    docstring: str = ""
    imports: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'chunk_id': self.chunk_id,
            'content': self.content,
            'file_path': self.file_path,
            'language': self.language,
            'start_line': self.start_line,
            'end_line': self.end_line,
            'chunk_type': self.chunk_type,
            'docstring': self.docstring,
            'imports': self.imports,
            'references': self.references,
            'metadata': self.metadata,
            'symbols': [
                {
                    'name': s.name,
                    'type': s.symbol_type,
                    'start': s.start_line,
                    'end': s.end_line,
                    'visibility': s.visibility,
                    'signature': s.signature
                }
                for s in self.symbols
            ]
        }

    @property
    def size(self) -> int:
        return len(self.content.split('\n'))

    @property
    def file_hash(self) -> str:
        content = f"{self.file_path}:{self.start_line}:{self.end_line}"
        return hashlib.md5(content.encode()).hexdigest()[:12]


@dataclass
class FileInfo:
    path: Path
    relative_path: str
    content: str
    lines: List[str]
    language: str
    size: int
    symbols: List[CodeSymbol] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    docstring: str = ""

    @property
    def line_count(self) -> int:
        return len(self.lines)

    @property
    def is_empty(self) -> bool:
        return self.line_count < 3 or self.size < 50


@dataclass
class BuildStats:
    total_files: int = 0
    processed_files: int = 0
    failed_files: int = 0
    total_chunks: int = 0
    total_symbols: int = 0
    total_lines: int = 0
    index_size_bytes: int = 0
    build_time_seconds: float = 0
    errors: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'total_files': self.total_files,
            'processed_files': self.processed_files,
            'failed_files': self.failed_files,
            'total_chunks': self.total_chunks,
            'total_symbols': self.total_symbols,
            'total_lines': self.total_lines,
            'index_size_mb': self.index_size_bytes / (1024 * 1024),
            'build_time_seconds': self.build_time_seconds,
            'errors': self.errors
        }


@dataclass
class ChunkStrategy:
    max_chunk_size: int = 512
    min_chunk_size: int = 10
    chunk_overlap: int = 50
    split_by_symbol: bool = True
    split_by_docstring: bool = True
    preserve_imports: bool = True
    preserve_context: bool = True
    max_symbol_children: int = 50


@dataclass
class IndexConfig:
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384
    vector_index_type: str = "FlatIP"
    hybrid_alpha: float = 0.7
    chunk_strategy: ChunkStrategy = field(default_factory=ChunkStrategy)
    storage_path: str = "./data"
    compression: bool = False
