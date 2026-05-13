import re
import os
from pathlib import Path
from typing import List, Dict, Optional, Generator, Tuple, Set
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

from stage1.types import (
    CodeChunk, FileInfo, CodeSymbol, ChunkStrategy,
    BuildStats
)
from stage1.language_modes import (
    LANGUAGE_MODES, get_language_from_extension, get_language_mode
)


SKIP_DIRS = {
    'node_modules', '__pycache__', '.git', '.svn', '.hg', 'venv', 'env',
    '.venv', '.env', 'build', 'dist', 'target', 'out', '.idea', '.vscode',
    'vendor', 'packages', '.next', '.nuxt', '.pytest_cache', 'coverage',
    '.tox', '.mypy_cache', '.DS_Store', 'Thumbs.db', '_site', '.sass-cache',
    'bower_components', 'jspm_packages', '.npm', '.yarn', '.pnpm-store'
}

SKIP_FILES = {
    '.gitignore', '.gitattributes', '.dockerignore', '.editorconfig',
    '.prettierrc', '.eslintrc', '.babelrc', 'package-lock.json',
    'yarn.lock', 'pnpm-lock.yaml', 'Cargo.lock', 'go.sum', 'requirements.txt',
    'setup.py', 'pyproject.toml', 'Makefile', 'Dockerfile', '.dockerignore'
}


class CodeParser:
    def __init__(
        self,
        strategy: ChunkStrategy = None,
        skip_dirs: Set[str] = None,
        skip_files: Set[str] = None,
        max_file_size: int = 10 * 1024 * 1024
    ):
        self.strategy = strategy or ChunkStrategy()
        self.skip_dirs = skip_dirs or SKIP_DIRS
        self.skip_files = skip_files or SKIP_FILES
        self.max_file_size = max_file_size

    def should_skip_path(self, path: Path) -> bool:
        name = path.name
        if name in self.skip_files:
            return True
        if any(part in self.skip_dirs for part in path.parts):
            return True
        return False

    def get_language(self, file_path: Path) -> Optional[str]:
        ext = file_path.suffix.lower()
        return get_language_from_extension(ext)

    def parse_file(self, path: Path, base_path: Optional[Path] = None) -> Optional[FileInfo]:
        if path.stat().st_size > self.max_file_size:
            return None

        try:
            content = path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            return None

        lines = content.split('\n')
        if len(lines) < 3:
            return None

        language = self.get_language(path)
        if not language:
            return None

        relative_path = str(path)
        if base_path:
            try:
                relative_path = str(path.relative_to(base_path))
            except ValueError:
                pass

        file_info = FileInfo(
            path=path,
            relative_path=relative_path,
            content=content,
            lines=lines,
            language=language,
            size=len(content)
        )

        symbols = self.extract_symbols(file_info)
        file_info.symbols = symbols
        file_info.imports = self.extract_imports(file_info)
        file_info.exports = self.extract_exports(file_info)
        file_info.docstring = self.extract_file_docstring(file_info)

        return file_info

    def extract_symbols(self, file_info: FileInfo) -> List[CodeSymbol]:
        symbols = []
        mode = get_language_mode(file_info.language)

        if not mode:
            return symbols

        content = file_info.content
        patterns = mode.get('symbol_patterns', {})

        for symbol_type, pattern in patterns.items():
            try:
                compiled = re.compile(pattern, re.MULTILINE)
            except re.error:
                continue

            for match in compiled.finditer(content):
                groups = match.groups()
                name = None

                if hasattr(match, 'groupdict') and match.groupdict():
                    for key, val in match.groupdict().items():
                        if val and key not in ('indent',):
                            name = val
                            break

                if not name and groups:
                    for g in groups:
                        if g:
                            name = g
                            break

                if not name:
                    continue

                start_pos = match.start()
                start_line = content[:start_pos].count('\n') + 1

                end_line = self._find_block_end(
                    content, start_pos, file_info.lines, file_info.language
                )

                visibility = 'public'
                if file_info.language == 'python':
                    if name.startswith('_') and not name.startswith('__'):
                        visibility = 'private'
                    elif name.startswith('__'):
                        visibility = 'public'
                    else:
                        visibility = 'public'
                elif file_info.language in ('javascript', 'typescript'):
                    if name.startswith('_'):
                        visibility = 'private'

                symbol = CodeSymbol(
                    name=name,
                    symbol_type=symbol_type,
                    start_line=start_line,
                    end_line=end_line,
                    visibility=visibility,
                    signature=self._extract_signature(content, start_pos, file_info.language)
                )

                docstring = self._extract_docstring(
                    content, start_pos, end_line, file_info.language
                )
                if docstring:
                    symbol.docstring = docstring

                symbols.append(symbol)

        symbols.sort(key=lambda s: s.start_line)
        return symbols

    def _find_block_end(
        self,
        content: str,
        start_pos: int,
        lines: List[str],
        language: str
    ) -> int:
        if language in ('python',):
            return self._find_python_block_end(content, start_pos, lines)
        elif language in ('javascript', 'typescript', 'java', 'csharp', 'go', 'rust', 'swift', 'kotlin'):
            return self._find_braces_block_end(content, start_pos)
        elif language in ('c', 'cpp'):
            return self._find_braces_block_end(content, start_pos)
        else:
            return self._find_braces_block_end(content, start_pos)

    def _find_python_block_end(self, content: str, start_pos: int, lines: List[str]) -> int:
        start_line = content[:start_pos].count('\n')
        if start_line >= len(lines):
            return start_line + 1

        first_line = lines[start_line]
        indent_match = re.match(r'^(\s*)', first_line)
        base_indent = len(indent_match.group(1)) if indent_match else 0

        for i in range(start_line + 1, len(lines)):
            line = lines[i]
            if line.strip() and not line.startswith(' ' * (base_indent + 1)):
                stripped = line.strip()
                if stripped and not stripped.startswith('#') and not stripped.startswith('"""') and not stripped.startswith("'''"):
                    return i
        return len(lines)

    def _find_braces_block_end(self, content: str, start_pos: int) -> int:
        brace_count = 0
        in_string = False
        string_char = None
        escaped = False

        for i in range(start_pos, len(content)):
            char = content[i]

            if escaped:
                escaped = False
                continue

            if char == '\\':
                escaped = True
                continue

            if char in ('"', "'", '`'):
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    in_string = False
                    string_char = None
                continue

            if in_string:
                continue

            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    return content[:i].count('\n') + 1

        return content.count('\n') + 1

    def _extract_signature(self, content: str, start_pos: int, language: str) -> str:
        if language == 'python':
            end = content.find('\n', start_pos)
            return content[start_pos:end].strip()
        else:
            paren_count = 0
            for i in range(start_pos, min(start_pos + 500, len(content))):
                if content[i] == '(':
                    paren_count += 1
                elif content[i] == ')':
                    paren_count -= 1
                    if paren_count == 0:
                        return content[start_pos:i+1].strip()
        return ""

    def _extract_docstring(
        self,
        content: str,
        start_pos: int,
        end_line: int,
        language: str
    ) -> str:
        if language == 'python':
            after_start = content[start_pos:start_pos + 500]
            triple_quote_match = re.search(r'"""\s*(.*?)"""', after_start, re.DOTALL)
            if triple_quote_match:
                return triple_quote_match.group(1).strip()[:200]
            single_quote_match = re.search(r"'''\s*(.*?)'''", after_start, re.DOTALL)
            if single_quote_match:
                return single_quote_match.group(1).strip()[:200]
        elif language in ('javascript', 'typescript'):
            after_start = content[start_pos:start_pos + 300]
            jsdoc_match = re.search(r'/\*\*\s*(.*?)\s*\*/', after_start, re.DOTALL)
            if jsdoc_match:
                doc = jsdoc_match.group(1)
                doc = re.sub(r'^\s*\*\s*', '', doc, flags=re.MULTILINE)
                return doc.strip()[:200]
        return ""

    def extract_imports(self, file_info: FileInfo) -> List[str]:
        imports = []
        mode = get_language_mode(file_info.language)
        if not mode:
            return imports

        for i, line in enumerate(file_info.lines[:20]):
            line = line.strip()

            import_pattern = mode.get('import_pattern')
            if import_pattern:
                match = re.match(import_pattern, line)
                if match:
                    imports.append(line)

            from_match = re.match(mode.get('from_import_pattern', r'' ), line)
            if from_match:
                imports.append(line)

            if not line.startswith(('import', 'from', 'require', 'use', '#include', 'using')):
                if not line.startswith(('#', '//')) and line:
                    break

        return imports

    def extract_exports(self, file_info: FileInfo) -> List[str]:
        exports = []
        content = file_info.content

        if file_info.language == 'python':
            for match in re.finditer(r'^__all__\s*=\s*\[(.*?)\]', content, re.MULTILINE | re.DOTALL):
                exports.append(match.group(0))
        elif file_info.language in ('javascript', 'typescript'):
            for match in re.finditer(r'export\s+(?:default\s+)?(?:const|let|var|function|class|interface|type)', content):
                exports.append(content[match.start():match.end()+50])

        return exports

    def extract_file_docstring(self, file_info: FileInfo) -> str:
        if file_info.language == 'python':
            first_lines = '\n'.join(file_info.lines[:5])
            triple_match = re.search(r'"""\s*(.*?)"""', first_lines, re.DOTALL)
            if triple_match:
                return triple_match.group(1).strip()[:300]
            single_match = re.search(r"'''\s*(.*?)'''", first_lines, re.DOTALL)
            if single_match:
                return single_match.group(1).strip()[:300]
        return ""


class ChunkBuilder:
    def __init__(self, strategy: ChunkStrategy = None):
        self.strategy = strategy or ChunkStrategy()

    def build_chunks(self, file_info: FileInfo) -> List[CodeChunk]:
        if file_info.is_empty:
            return []

        chunks = []

        if self.strategy.split_by_symbol and file_info.symbols:
            symbol_chunks = self._build_symbol_chunks(file_info)
            chunks.extend(symbol_chunks)

        if not chunks or self.strategy.max_chunk_size < 100:
            remaining_chunks = self._build_line_chunks(file_info)
            chunks.extend(remaining_chunks)

        chunks = self._merge_small_chunks(chunks, file_info)

        for i, chunk in enumerate(chunks):
            chunk.chunk_id = f"{file_info.relative_path}:{chunk.start_line}-{chunk.end_line}:{i}"

        return chunks

    def _build_symbol_chunks(self, file_info: FileInfo) -> List[CodeChunk]:
        chunks = []
        lines = file_info.lines

        for symbol in file_info.symbols:
            if symbol.symbol_type not in ('class', 'function', 'method', 'interface', 'struct', 'trait', 'enum'):
                continue

            symbol_lines = lines[symbol.start_line-1:symbol.end_line]
            content = '\n'.join(symbol_lines)

            if len(symbol_lines) < 3:
                continue

            imports = self._find_relevant_imports(file_info.imports, symbol, file_info.language)

            chunk_symbols = [symbol]

            chunk = CodeChunk(
                chunk_id="",
                content=content,
                file_path=file_info.relative_path,
                language=file_info.language,
                start_line=symbol.start_line,
                end_line=symbol.end_line,
                chunk_type=symbol.symbol_type,
                parent_symbol=symbol,
                symbols=chunk_symbols,
                docstring=symbol.docstring,
                imports=imports,
                metadata={
                    'symbol_name': symbol.name,
                    'visibility': symbol.visibility,
                    'signature': symbol.signature
                }
            )
            chunks.append(chunk)

        return chunks

    def _build_line_chunks(self, file_info: FileInfo) -> List[CodeChunk]:
        chunks = []
        lines = file_info.lines
        total_lines = len(lines)

        for start in range(0, total_lines, self.strategy.max_chunk_size - self.strategy.chunk_overlap):
            end = min(start + self.strategy.max_chunk_size, total_lines)

            if end - start < self.strategy.min_chunk_size:
                if chunks:
                    last_chunk = chunks[-1]
                    overlap_lines = lines[last_chunk.end_line-1: last_chunk.end_line-1 + self.strategy.chunk_overlap]
                    if overlap_lines:
                        pass
                continue

            chunk_lines = lines[start:end]
            content = '\n'.join(chunk_lines)

            chunk = CodeChunk(
                chunk_id="",
                content=content,
                file_path=file_info.relative_path,
                language=file_info.language,
                start_line=start + 1,
                end_line=end,
                chunk_type='block',
                metadata={'chunk_method': 'line_based'}
            )
            chunks.append(chunk)

        return chunks

    def _merge_small_chunks(self, chunks: List[CodeChunk], file_info: FileInfo) -> List[CodeChunk]:
        if not chunks:
            return chunks

        merged = []
        current = None

        for chunk in chunks:
            if current is None:
                current = chunk
                continue

            current_size = len(current.content.split('\n'))
            combined_size = current_size + len(chunk.content.split('\n'))

            if combined_size <= self.strategy.max_chunk_size:
                current.content += '\n' + chunk.content
                current.end_line = chunk.end_line
                current.symbols.extend(chunk.symbols)
            else:
                merged.append(current)
                current = chunk

        if current:
            merged.append(current)

        return merged

    def _find_relevant_imports(self, imports: List[str], symbol: CodeSymbol, language: str) -> List[str]:
        relevant = []
        symbol_name_lower = symbol.name.lower()

        for imp in imports[:5]:
            if symbol_name_lower in imp.lower():
                relevant.append(imp)

        return relevant[:3]


class DirectoryParser:
    def __init__(
        self,
        parser: CodeParser = None,
        chunk_builder: ChunkBuilder = None,
        max_workers: int = 4
    ):
        self.parser = parser or CodeParser()
        self.chunk_builder = chunk_builder or ChunkBuilder()
        self.max_workers = max_workers

    def scan_directory(self, root_path: Path) -> List[Path]:
        files = []
        for path in root_path.rglob('*'):
            if path.is_file() and not self.parser.should_skip_path(path):
                if path.suffix.lower() in self._get_supported_extensions():
                    files.append(path)
        return files

    def _get_supported_extensions(self) -> Set[str]:
        extensions = set()
        for mode in LANGUAGE_MODES.values():
            extensions.update(mode['extensions'])
        return extensions

    def parse_directory(
        self,
        root_path: Path,
        show_progress: bool = True
    ) -> Tuple[List[FileInfo], List[CodeChunk], BuildStats]:
        root_path = Path(root_path).resolve()

        if not root_path.exists():
            raise ValueError(f"Path does not exist: {root_path}")

        files = self.scan_directory(root_path)

        stats = BuildStats(total_files=len(files))
        file_infos: List[FileInfo] = []
        all_chunks: List[CodeChunk] = []

        if self.max_workers > 1:
            file_infos, all_chunks, stats = self._parse_parallel(files, root_path, stats, show_progress)
        else:
            file_infos, all_chunks, stats = self._parse_sequential(files, root_path, stats, show_progress)

        return file_infos, all_chunks, stats

    def _parse_sequential(
        self,
        files: List[Path],
        root_path: Path,
        stats: BuildStats,
        show_progress: bool
    ) -> Tuple[List[FileInfo], List[CodeChunk], BuildStats]:
        file_infos = []

        for i, file_path in enumerate(files):
            if show_progress and i % 100 == 0:
                print(f"Processing: {i}/{len(files)} files...")

            try:
                file_info = self.parser.parse_file(file_path, root_path)
                if file_info:
                    file_infos.append(file_info)
                    chunks = self.chunk_builder.build_chunks(file_info)
                    all_chunks.extend(chunks)
                    stats.processed_files += 1
                    stats.total_lines += file_info.line_count
            except Exception as e:
                stats.failed_files += 1
                stats.errors.append({
                    'file': str(file_path),
                    'error': str(e)
                })

        stats.total_chunks = len(all_chunks)
        stats.total_symbols = sum(len(fi.symbols) for fi in file_infos)

        return file_infos, all_chunks, stats

    def _parse_parallel(
        self,
        files: List[Path],
        root_path: Path,
        stats: BuildStats,
        show_progress: bool
    ) -> Tuple[List[FileInfo], List[CodeChunk], BuildStats]:
        file_infos = []
        all_chunks = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_path = {
                executor.submit(self.parser.parse_file, path, root_path): path
                for path in files
            }

            completed = 0
            for future in as_completed(future_to_path):
                completed += 1
                if show_progress and completed % 100 == 0:
                    print(f"Processed: {completed}/{len(files)} files...")

                try:
                    file_info = future.result()
                    if file_info:
                        file_infos.append(file_info)
                        chunks = self.chunk_builder.build_chunks(file_info)
                        all_chunks.extend(chunks)
                        stats.processed_files += 1
                        stats.total_lines += file_info.line_count
                except Exception as e:
                    stats.failed_files += 1
                    stats.errors.append({
                        'file': str(future_to_path[future]),
                        'error': str(e)
                    })

        stats.total_chunks = len(all_chunks)
        stats.total_symbols = sum(len(fi.symbols) for fi in file_infos)

        return file_infos, all_chunks, stats
