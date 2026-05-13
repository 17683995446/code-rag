import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Generator
from concurrent.futures import ThreadPoolExecutor, as_completed


SUPPORTED_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp',
    '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.cs', '.vue',
    '.svelte', '.sh', '.bash', '.zsh', '.sql', '.yaml', '.yml', '.json',
    '.xml', '.md', '.txt', '.css', '.scss', '.less'
}

SKIP_DIRS = {
    'node_modules', '__pycache__', '.git', '.svn', '.hg', 'venv', 'env',
    '.venv', '.env', 'build', 'dist', 'target', 'out', '.idea', '.vscode',
    'vendor', 'packages', '.next', '.nuxt', '__pycache__', '.pytest_cache',
    'coverage', '.tox', '.mypy_cache', '.DS_Store', 'Thumbs.db'
}


@dataclass
class CodeChunk:
    content: str
    file_path: str
    start_line: int
    end_line: int
    chunk_id: str
    language: str = "unknown"
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    docstring: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            'content': self.content,
            'file_path': self.file_path,
            'start_line': self.start_line,
            'end_line': self.end_line,
            'chunk_id': self.chunk_id,
            'language': self.language,
            'function_name': self.function_name,
            'class_name': self.class_name,
            'docstring': self.docstring
        }


@dataclass
class ParsedFile:
    path: Path
    content: str
    lines: List[str]
    language: str
    size: int
    chunks: List[CodeChunk] = field(default_factory=list)


LANGUAGE_MAP = {
    '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
    '.jsx': 'javascript', '.tsx': 'typescript', '.java': 'java',
    '.c': 'c', '.cpp': 'cpp', '.h': 'c', '.hpp': 'cpp',
    '.go': 'go', '.rs': 'rust', '.rb': 'ruby', '.php': 'php',
    '.swift': 'swift', '.kt': 'kotlin', '.scala': 'scala',
    '.cs': 'csharp', '.vue': 'vue', '.svelte': 'svelte',
    '.sh': 'bash', '.bash': 'bash', '.zsh': 'bash',
    '.sql': 'sql', '.yaml': 'yaml', '.yml': 'yaml',
    '.json': 'json', '.xml': 'xml', '.md': 'markdown',
    '.css': 'css', '.scss': 'scss', '.less': 'less'
}


def get_language(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    return LANGUAGE_MAP.get(ext, 'unknown')


def should_skip_path(path: Path) -> bool:
    name = path.name
    if name in SKIP_DIRS:
        return True
    if any(part in SKIP_DIRS for part in path.parts):
        return True
    return False


def normalize_whitespace(text: str) -> str:
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def split_into_chunks(content: str, chunk_size: int = 512, overlap: int = 50) -> Generator[tuple, None, None]:
    lines = content.split('\n')
    total_lines = len(lines)

    for i in range(0, total_lines, chunk_size - overlap):
        chunk_lines = lines[i:i + chunk_size]
        if len(chunk_lines) < 3:
            continue

        chunk_content = '\n'.join(chunk_lines)
        start_line = i + 1
        end_line = min(i + chunk_size, total_lines)

        yield chunk_content, start_line, end_line


def extract_simple_context(content: str, language: str) -> tuple[Optional[str], Optional[str]]:
    function_match = None
    class_match = None

    patterns = {
        'python': {
            'class': r'class\s+(\w+)',
            'function': r'def\s+(\w+)\s*\('
        },
        'javascript': {
            'class': r'class\s+(\w+)',
            'function': r'(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s*)?\(|(\w+)\s*\([^)]*\)\s*\{)'
        },
        'java': {
            'class': r'(?:public|private|protected)?\s*class\s+(\w+)',
            'function': r'(?:public|private|protected)?\s*(?:static)?\s*\w+\s+(\w+)\s*\('
        },
        'go': {
            'class': None,
            'function': r'func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\('
        },
        'rust': {
            'class': r'(?:pub\s+)?(?:struct|enum)\s+(\w+)',
            'function': r'(?:pub\s+)?fn\s+(\w+)'
        }
    }

    lang_patterns = patterns.get(language, patterns['python'])

    if lang_patterns.get('class'):
        match = re.search(lang_patterns['class'], content)
        if match:
            class_match = match.group(1)

    if lang_patterns.get('function'):
        match = re.search(lang_patterns['function'], content)
        if match:
            for g in match.groups():
                if g:
                    function_match = g
                    break

    return function_match, class_match


class CodeParser:
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        supported_extensions: set = None,
        skip_dirs: set = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.supported_extensions = supported_extensions or SUPPORTED_EXTENSIONS
        self.skip_dirs = skip_dirs or SKIP_DIRS

    def is_supported_file(self, path: Path) -> bool:
        if path.suffix.lower() not in self.supported_extensions:
            return False
        if should_skip_path(path):
            return False
        return True

    def parse_file(self, path: Path) -> Optional[ParsedFile]:
        try:
            content = path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            return None

        lines = content.split('\n')
        if len(lines) < 3:
            return None

        language = get_language(str(path))

        chunks = []
        chunk_counter = 0

        for chunk_content, start_line, end_line in split_into_chunks(
            content, self.chunk_size, self.chunk_overlap
        ):
            function_name, class_name = extract_simple_context(chunk_content, language)

            chunk_id = f"{path}:{start_line}-{end_line}"

            chunk = CodeChunk(
                content=normalize_whitespace(chunk_content),
                file_path=str(path),
                start_line=start_line,
                end_line=end_line,
                chunk_id=chunk_id,
                language=language,
                function_name=function_name,
                class_name=class_name
            )
            chunks.append(chunk)
            chunk_counter += 1

        return ParsedFile(
            path=path,
            content=content,
            lines=lines,
            language=language,
            size=len(content),
            chunks=chunks
        )

    def parse_directory(self, root_path: Path, max_workers: int = 4) -> List[ParsedFile]:
        files = []
        for path in root_path.rglob('*'):
            if path.is_file() and self.is_supported_file(path):
                files.append(path)

        parsed_files = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_path = {
                executor.submit(self.parse_file, path): path
                for path in files
            }

            for future in as_completed(future_to_path):
                result = future.result()
                if result:
                    parsed_files.append(result)

        return parsed_files

    def get_all_chunks(self, parsed_files: List[ParsedFile]) -> List[CodeChunk]:
        all_chunks = []
        for pf in parsed_files:
            all_chunks.extend(pf.chunks)
        return all_chunks


if __name__ == "__main__":
    parser = CodeParser(chunk_size=512, chunk_overlap=50)
    test_file = Path(__file__)
    result = parser.parse_file(test_file)
    if result:
        print(f"Parsed: {result.path}")
        print(f"Chunks: {len(result.chunks)}")
        for chunk in result.chunks[:2]:
            print(f"  - {chunk.chunk_id}: {chunk.function_name or chunk.class_name or 'N/A'}")
