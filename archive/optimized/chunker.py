import re
import ast
from typing import List, Dict, Optional, Tuple, Generator
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ChunkStrategy:
    max_tokens: int = 512
    overlap_tokens: int = 50
    split_by_symbol: bool = True
    preserve_docstring: bool = True
    preserve_imports: bool = True
    min_chunk_size: int = 10
    language_specific: bool = True


class PythonChunker:
    def __init__(self, strategy: ChunkStrategy = None):
        self.strategy = strategy or ChunkStrategy()

    def chunk(self, content: str, file_path: str = "") -> List[Dict]:
        chunks = []

        try:
            tree = ast.parse(content)
            symbols = self._extract_symbols(tree)
        except SyntaxError:
            symbols = []

        if self.strategy.split_by_symbol and symbols:
            symbol_chunks = self._chunk_by_symbols(content, symbols, file_path)
            chunks.extend(symbol_chunks)

        if not chunks:
            chunks = self._chunk_by_lines(content, file_path)

        return chunks

    def _extract_symbols(self, tree: ast.AST) -> List[Dict]:
        symbols = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                symbols.append({
                    'name': node.name,
                    'type': 'class' if isinstance(node, ast.ClassDef) else 'function',
                    'lineno': node.lineno,
                    'end_lineno': getattr(node, 'end_lineno', node.lineno),
                    'docstring': ast.get_docstring(node) or ""
                })

        return sorted(symbols, key=lambda x: x['lineno'])

    def _chunk_by_symbols(self, content: str, symbols: List[Dict], file_path: str) -> List[Dict]:
        chunks = []
        lines = content.split('\n')

        for i, sym in enumerate(symbols):
            start = sym['lineno'] - 1
            end = sym['end_lineno']

            if i + 1 < len(symbols):
                next_start = symbols[i + 1]['lineno'] - 1
            else:
                next_start = len(lines)

            chunk_lines = lines[start:min(end, next_start)]
            chunk_content = '\n'.join(chunk_lines)

            if len(chunk_lines) < self.strategy.min_chunk_size:
                continue

            chunk = {
                'chunk_id': f"{file_path}:{start+1}-{end}",
                'content': chunk_content.strip(),
                'file_path': file_path,
                'language': 'python',
                'start_line': start + 1,
                'end_line': end,
                'chunk_type': sym['type'],
                'symbols': [{
                    'name': sym['name'],
                    'type': sym['type'],
                    'start': sym['lineno'],
                    'end': sym['end_lineno'],
                    'signature': self._extract_signature(chunk_content, sym)
                }],
                'docstring': sym.get('docstring', '')
            }
            chunks.append(chunk)

        return chunks

    def _extract_signature(self, content: str, symbol: Dict) -> str:
        lines = content.split('\n')[:5]
        for line in lines:
            if f"def {symbol['name']}" in line or f"class {symbol['name']}" in line:
                return line.strip()
        return symbol['name']

    def _chunk_by_lines(self, content: str, file_path: str) -> List[Dict]:
        chunks = []
        lines = content.split('\n')
        total = len(lines)
        max_lines = self.strategy.max_tokens // 4

        for start in range(0, total, max_lines - self.strategy.overlap_tokens):
            end = min(start + max_lines, total)
            chunk_lines = lines[start:end]
            chunk_content = '\n'.join(chunk_lines)

            if len(chunk_lines) < self.strategy.min_chunk_size:
                continue

            chunks.append({
                'chunk_id': f"{file_path}:{start+1}-{end}",
                'content': chunk_content.strip(),
                'file_path': file_path,
                'language': 'python',
                'start_line': start + 1,
                'end_line': end,
                'chunk_type': 'block'
            })

        return chunks


class JavaScriptChunker:
    def __init__(self, strategy: ChunkStrategy = None):
        self.strategy = strategy or ChunkStrategy()

    def chunk(self, content: str, file_path: str = "") -> List[Dict]:
        chunks = []
        symbols = self._extract_symbols(content)

        if self.strategy.split_by_symbol and symbols:
            chunks.extend(self._chunk_by_symbols(content, symbols, file_path))

        if not chunks:
            chunks = self._chunk_by_lines(content, file_path)

        return chunks

    def _extract_symbols(self, content: str) -> List[Dict]:
        symbols = []

        class_pattern = r'class\s+(\w+)(?:\s+extends\s+\w+)?\s*\{'
        for match in re.finditer(class_pattern, content):
            symbols.append({
                'name': match.group(1),
                'type': 'class',
                'start': match.start(),
                'end': self._find_brace_end(content, match.end() - 1)
            })

        func_pattern = r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\('
        for match in re.finditer(func_pattern, content):
            end = content.find('{', match.end())
            symbols.append({
                'name': match.group(1),
                'type': 'function',
                'start': match.start(),
                'end': self._find_brace_end(content, end) if end > 0 else match.end() + 100
            })

        const_pattern = r'const\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>'
        for match in re.finditer(const_pattern, content):
            end = content.find('{', match.end())
            symbols.append({
                'name': match.group(1),
                'type': 'function',
                'start': match.start(),
                'end': self._find_brace_end(content, end) if end > 0 else match.end() + 100
            })

        return sorted(symbols, key=lambda x: x['start'])

    def _find_brace_end(self, content: str, start: int) -> int:
        count = 0
        for i in range(start, len(content)):
            if content[i] == '{':
                count += 1
            elif content[i] == '}':
                count -= 1
                if count == 0:
                    return content[:i].count('\n') + 1
        return content.count('\n') + 1

    def _chunk_by_symbols(self, content: str, symbols: List[Dict], file_path: str) -> List[Dict]:
        chunks = []
        lines = content.split('\n')

        for i, sym in enumerate(symbols):
            start_line = lines[:sym['start']].count('\n') + 1
            end_line = sym['end']

            next_start = symbols[i + 1]['start'] if i + 1 < len(symbols) else len(content)
            next_line = lines[:next_start].count('\n')

            chunk_lines = lines[start_line - 1:next_line]
            chunk_content = '\n'.join(chunk_lines)

            if len(chunk_lines) < 3:
                continue

            chunks.append({
                'chunk_id': f"{file_path}:{start_line}-{end_line}",
                'content': chunk_content.strip(),
                'file_path': file_path,
                'language': 'javascript',
                'start_line': start_line,
                'end_line': next_line,
                'chunk_type': sym['type'],
                'symbols': [{'name': sym['name'], 'type': sym['type']}]
            })

        return chunks

    def _chunk_by_lines(self, content: str, file_path: str) -> List[Dict]:
        chunks = []
        lines = content.split('\n')
        total = len(lines)
        max_lines = self.strategy.max_tokens // 4

        for start in range(0, total, max_lines - self.strategy.overlap_tokens):
            end = min(start + max_lines, total)
            chunk_content = '\n'.join(lines[start:end])

            chunks.append({
                'chunk_id': f"{file_path}:{start+1}-{end}",
                'content': chunk_content.strip(),
                'file_path': file_path,
                'language': 'javascript',
                'start_line': start + 1,
                'end_line': end,
                'chunk_type': 'block'
            })

        return chunks


class GenericChunker:
    def __init__(self, strategy: ChunkStrategy = None):
        self.strategy = strategy or ChunkStrategy()

    def chunk(self, content: str, file_path: str = "") -> List[Dict]:
        return self._chunk_by_lines(content, file_path)

    def _chunk_by_lines(self, content: str, file_path: str) -> List[Dict]:
        chunks = []
        lines = content.split('\n')
        total = len(lines)
        max_lines = self.strategy.max_tokens // 4

        for start in range(0, total, max_lines - self.strategy.overlap_tokens):
            end = min(start + max_lines, total)
            chunk_lines = lines[start:end]

            if len(chunk_lines) < self.strategy.min_chunk_size:
                continue

            ext = Path(file_path).suffix.lower()
            lang_map = {
                '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
                '.java': 'java', '.go': 'go', '.rs': 'rust', '.cpp': 'cpp'
            }

            chunks.append({
                'chunk_id': f"{file_path}:{start+1}-{end}",
                'content': '\n'.join(chunk_lines).strip(),
                'file_path': file_path,
                'language': lang_map.get(ext, 'text'),
                'start_line': start + 1,
                'end_line': end,
                'chunk_type': 'block'
            })

        return chunks


class SemanticChunker:
    def __init__(self, strategy: ChunkStrategy = None):
        self.strategy = strategy or ChunkStrategy()
        self.chunkers = {
            'python': PythonChunker(strategy),
            'javascript': JavaScriptChunker(strategy),
            'typescript': JavaScriptChunker(strategy),
        }
        self.generic = GenericChunker(strategy)

    def chunk(self, content: str, file_path: str = "", language: str = "") -> List[Dict]:
        if not language:
            ext = Path(file_path).suffix.lower()
            lang_map = {
                '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
                '.tsx': 'typescript', '.jsx': 'javascript', '.java': 'java',
                '.go': 'go', '.rs': 'rust', '.cpp': 'cpp', '.c': 'c'
            }
            language = lang_map.get(ext, '')

        chunker = self.chunkers.get(language, self.generic)
        return chunker.chunk(content, file_path)
