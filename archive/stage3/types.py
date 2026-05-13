from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Any, Tuple
from enum import Enum


class EnhancementType(Enum):
    CALL_GRAPH = "call_graph"
    SIMILAR_CODE = "similar_code"
    CODE_SUMMARY = "code_summary"
    USAGE_EXAMPLES = "usage_examples"
    DEPENDENCIES = "dependencies"


@dataclass
class CallGraph:
    nodes: Dict[str, 'CallNode'] = field(default_factory=dict)
    edges: List[Tuple[str, str]] = field(default_factory=list)


@dataclass
class CallNode:
    symbol_name: str
    file_path: str
    line_number: int
    symbol_type: str
    calls: List[str] = field(default_factory=list)
    called_by: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    docstring: str = ""


@dataclass
class EnhancedResult:
    original_result: Dict
    enhancements: Dict[str, Any] = field(default_factory=dict)
    call_graph: Optional[CallGraph] = None
    similar_codes: List[Dict] = field(default_factory=list)
    summary: str = ""
    usage_examples: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class EnhancementConfig:
    enable_call_graph: bool = True
    enable_similar_code: bool = True
    enable_summary: bool = True
    enable_usage_examples: bool = False
    max_call_depth: int = 2
    max_similar_results: int = 3
    max_examples: int = 2


@dataclass
class EnhancementStats:
    total_enhanced: int = 0
    call_graph_time_ms: float = 0
    similar_code_time_ms: float = 0
    summary_time_ms: float = 0
    total_time_ms: float = 0
