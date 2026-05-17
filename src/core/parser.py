"""
代码解析器 - 产品级
支持多种编程语言的智能解析
"""

import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from .logger import get_logger
from .settings import get_settings

logger = get_logger(__name__)


class CodeLanguage(Enum):
    """编程语言类型"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CPP = "cpp"
    C = "c"
    GO = "go"
    RUST = "rust"
    MARKDOWN = "markdown"
    UNKNOWN = "unknown"


@dataclass
class CodeChunk:
    """代码块"""
    content: str
    chunk_type: str  # "function", "class", "module", "comment"
    name: Optional[str] = None
    line_start: int = 0
    line_end: int = 0
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ParsedDocument:
    """解析后的文档"""
    file_path: str
    language: CodeLanguage
    chunks: List[CodeChunk]
    raw_content: str
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class CodeParser:
    """
    产品级代码解析器
    支持多种编程语言，智能提取代码块
    """

    def __init__(self):
        self.settings = get_settings()

    def parse_file(self, file_path: str) -> ParsedDocument:
        """解析单个文件"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        content = path.read_text(encoding="utf-8")
        language = self._detect_language(path)

        chunks = self._parse_content(content, language)

        return ParsedDocument(
            file_path=str(path),
            language=language,
            chunks=chunks,
            raw_content=content,
            metadata={
                "file_name": path.name,
                "file_size": path.stat().st_size,
                "language": language.value
            }
        )

    def parse_directory(self, directory: str, 
                        extensions: Optional[List[str]] = None) -> List[ParsedDocument]:
        """解析目录中的所有文件"""
        dir_path = Path(directory)
        if not dir_path.exists():
            return []

        if extensions is None:
            extensions = [".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs", ".md"]

        documents = []
        files = []

        for ext in extensions:
            files.extend(dir_path.rglob(f"*{ext}"))

        for file_path in files:
            if file_path.is_file():
                try:
                    doc = self.parse_file(str(file_path))
                    documents.append(doc)
                    logger.debug(f"解析成功: {file_path}")
                except Exception as e:
                    logger.warning(f"解析失败 {file_path}: {e}")

        return documents

    def _detect_language(self, path: Path) -> CodeLanguage:
        """检测编程语言"""
        ext = path.suffix.lower()

        lang_map = {
            ".py": CodeLanguage.PYTHON,
            ".js": CodeLanguage.JAVASCRIPT,
            ".ts": CodeLanguage.TYPESCRIPT,
            ".java": CodeLanguage.JAVA,
            ".cpp": CodeLanguage.CPP,
            ".cc": CodeLanguage.CPP,
            ".cxx": CodeLanguage.CPP,
            ".c": CodeLanguage.C,
            ".go": CodeLanguage.GO,
            ".rs": CodeLanguage.RUST,
            ".md": CodeLanguage.MARKDOWN,
        }

        return lang_map.get(ext, CodeLanguage.UNKNOWN)

    def _parse_content(self, content: str, language: CodeLanguage) -> List[CodeChunk]:
        """解析内容"""
        if language == CodeLanguage.PYTHON:
            return self._parse_python(content)
        elif language in [CodeLanguage.JAVASCRIPT, CodeLanguage.TYPESCRIPT]:
            return self._parse_javascript(content)
        elif language == CodeLanguage.MARKDOWN:
            return self._parse_markdown(content)
        else:
            return self._parse_generic(content)

    def _parse_python(self, content: str) -> List[CodeChunk]:
        """解析Python代码"""
        chunks = []
        lines = content.split("\n")

        # 简单的函数/类提取
        class_pattern = re.compile(r'^\s*class\s+(\w+)')
        def_pattern = re.compile(r'^\s*def\s+(\w+)')

        current_chunk = None
        chunk_start = 0

        for i, line in enumerate(lines):
            # 检查类定义
            class_match = class_pattern.match(line)
            if class_match:
                if current_chunk:
                    chunks.append(self._create_chunk(
                        lines, chunk_start, i, current_chunk["type"], current_chunk["name"]
                    ))
                current_chunk = {"type": "class", "name": class_match.group(1)}
                chunk_start = i
                continue

            # 检查函数定义
            def_match = def_pattern.match(line)
            if def_match:
                if current_chunk:
                    chunks.append(self._create_chunk(
                        lines, chunk_start, i, current_chunk["type"], current_chunk["name"]
                    ))
                current_chunk = {"type": "function", "name": def_match.group(1)}
                chunk_start = i
                continue

        # 添加最后一个块
        if current_chunk:
            chunks.append(self._create_chunk(
                lines, chunk_start, len(lines), current_chunk["type"], current_chunk["name"]
            ))

        # 如果没有提取到任何块，添加整个文件
        if not chunks:
            chunks.append(CodeChunk(
                content=content,
                chunk_type="module",
                line_start=0,
                line_end=len(lines)
            ))

        return chunks

    def _parse_javascript(self, content: str) -> List[CodeChunk]:
        """解析JavaScript/TypeScript代码"""
        chunks = []
        lines = content.split("\n")

        # 简单的类/函数提取
        class_pattern = re.compile(r'^\s*class\s+(\w+)')
        func_pattern = re.compile(r'^\s*(?:async\s+)?(?:function\s+(\w+)|(\w+)\s*[:=]\s*(?:async\s+)?\()')

        current_chunk = None
        chunk_start = 0

        for i, line in enumerate(lines):
            class_match = class_pattern.match(line)
            if class_match:
                if current_chunk:
                    chunks.append(self._create_chunk(
                        lines, chunk_start, i, current_chunk["type"], current_chunk["name"]
                    ))
                current_chunk = {"type": "class", "name": class_match.group(1)}
                chunk_start = i
                continue

            func_match = func_pattern.match(line)
            if func_match:
                name = func_match.group(1) or func_match.group(2)
                if current_chunk:
                    chunks.append(self._create_chunk(
                        lines, chunk_start, i, current_chunk["type"], current_chunk["name"]
                    ))
                current_chunk = {"type": "function", "name": name}
                chunk_start = i
                continue

        if current_chunk:
            chunks.append(self._create_chunk(
                lines, chunk_start, len(lines), current_chunk["type"], current_chunk["name"]
            ))

        if not chunks:
            chunks.append(CodeChunk(
                content=content,
                chunk_type="module",
                line_start=0,
                line_end=len(lines)
            ))

        return chunks

    def _parse_markdown(self, content: str) -> List[CodeChunk]:
        """解析Markdown文件"""
        chunks = []
        lines = content.split("\n")

        header_pattern = re.compile(r'^(#{1,6})\s+(.+)$')

        current_section = None
        section_start = 0

        for i, line in enumerate(lines):
            header_match = header_pattern.match(line)
            if header_match:
                if current_section:
                    chunks.append(self._create_chunk(
                        lines, section_start, i, "section", current_section
                    ))
                current_section = header_match.group(2)
                section_start = i

        if current_section:
            chunks.append(self._create_chunk(
                lines, section_start, len(lines), "section", current_section
            ))

        if not chunks:
            chunks.append(CodeChunk(
                content=content,
                chunk_type="document",
                line_start=0,
                line_end=len(lines)
            ))

        return chunks

    def _parse_generic(self, content: str) -> List[CodeChunk]:
        """通用解析（简单分块）"""
        lines = content.split("\n")
        chunk_size = self.settings.chunk_size // 50  # 粗略估算行数

        chunks = []
        for i in range(0, len(lines), chunk_size):
            end = min(i + chunk_size, len(lines))
            chunks.append(CodeChunk(
                content="\n".join(lines[i:end]),
                chunk_type="chunk",
                line_start=i,
                line_end=end
            ))

        return chunks

    def _create_chunk(self, lines: List[str], start: int, end: int, 
                     chunk_type: str, name: Optional[str] = None) -> CodeChunk:
        """创建代码块"""
        content = "\n".join(lines[start:end])
        return CodeChunk(
            content=content,
            chunk_type=chunk_type,
            name=name,
            line_start=start + 1,
            line_end=end,
            metadata={
                "line_start": start + 1,
                "line_end": end
            }
        )


# 便捷函数
def parse_file(file_path: str) -> ParsedDocument:
    """便捷函数：解析单个文件"""
    parser = CodeParser()
    return parser.parse_file(file_path)


def parse_directory(directory: str, extensions: Optional[List[str]] = None) -> List[ParsedDocument]:
    """便捷函数：解析目录"""
    parser = CodeParser()
    return parser.parse_directory(directory, extensions)
