import re
from typing import List, Dict, Optional, Any
from pathlib import Path


class CodeSummarizer:
    def __init__(self, metadata: List[Dict] = None):
        self.metadata = metadata or []
        self.patterns = self._compile_patterns()

    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        return {
            'function_def': re.compile(r'def\s+(\w+)\s*\([^)]*\)(?:\s*->\s*[\w\[\]]+)?:'),
            'class_def': re.compile(r'class\s+(\w+)(?:\([^)]*\))?:'),
            'import': re.compile(r'(?:from\s+([\w.]+)\s+)?import\s+([\w.]+)'),
            'param': re.compile(r'([\w]+)\s*:\s*([\w\[\]<>]+)'),
            'return': re.compile(r'return\s+(.+)'),
            'async': re.compile(r'async\s+def'),
            'decorator': re.compile(r'@(\w+)'),
        }

    def summarize(self, chunk: Dict) -> str:
        content = chunk.get('content', '')
        symbols = chunk.get('symbols', [])
        docstring = chunk.get('docstring', '')
        chunk_type = chunk.get('chunk_type', 'unknown')

        if docstring:
            return self._summarize_from_docstring(docstring, chunk_type)

        if symbols:
            return self._summarize_from_symbols(symbols, content, chunk_type)

        return self._summarize_from_content(content, chunk_type)

    def _summarize_from_docstring(self, docstring: str, chunk_type: str) -> str:
        docstring = docstring.strip()
        if len(docstring) > 300:
            docstring = docstring[:300] + "..."
        return docstring

    def _summarize_from_symbols(self, symbols: List[Dict], content: str, chunk_type: str) -> str:
        summary_parts = []

        if chunk_type == 'class':
            class_name = next((s['name'] for s in symbols if s['type'] == 'class'), 'Unknown')
            methods = [s['name'] for s in symbols if s['type'] in ('method', 'function')][:5]
            summary_parts.append(f"Class {class_name}")
            if methods:
                summary_parts.append(f"with methods: {', '.join(methods)}")

        elif chunk_type in ('function', 'method'):
            func_name = next((s['name'] for s in symbols if s['type'] in ('function', 'method')), 'Unknown')
            signature = next((s.get('signature', '') for s in symbols if s['type'] in ('function', 'method')), '')
            summary_parts.append(f"Function {func_name}")
            if signature:
                summary_parts.append(f"Signature: {signature}")

        else:
            symbol_names = [s['name'] for s in symbols[:5]]
            summary_parts.append(f"Code block containing: {', '.join(symbol_names)}")

        if content:
            first_line = content.split('\n')[0].strip()
            if first_line and first_line not in summary_parts:
                summary_parts.append(f"Definition: {first_line}")

        return " | ".join(summary_parts) if summary_parts else "Code block"

    def _summarize_from_content(self, content: str, chunk_type: str) -> str:
        lines = content.split('\n')
        summary_lines = []

        for line in lines[:10]:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('//'):
                summary_lines.append(line)
                if len(summary_lines) >= 3:
                    break

        summary = ' '.join(summary_lines)
        if len(summary) > 200:
            summary = summary[:200] + "..."

        return summary or f"{chunk_type.capitalize()} code block"

    def batch_summarize(self, chunks: List[Dict]) -> Dict[str, str]:
        return {
            chunk.get('chunk_id', ''): self.summarize(chunk)
            for chunk in chunks
        }


class SimilarCodeFinder:
    def __init__(self, metadata: List[Dict] = None):
        self.metadata = metadata or []
        self.structure_cache = self._build_structure_cache()

    def _build_structure_cache(self) -> Dict[str, Dict]:
        cache = {}
        for chunk in self.metadata:
            chunk_id = chunk.get('chunk_id', '')
            structure = self._extract_structure(chunk)
            cache[chunk_id] = structure
        return cache

    def _extract_structure(self, chunk: Dict) -> Dict[str, Any]:
        content = chunk.get('content', '')
        symbols = chunk.get('symbols', [])
        chunk_type = chunk.get('chunk_type', '')

        structure = {
            'type': chunk_type,
            'num_symbols': len(symbols),
            'symbol_types': list(set(s.get('type', '') for s in symbols)),
            'has_return': bool(re.search(r'\breturn\b', content)),
            'has_loop': bool(re.search(r'\b(for|while)\b', content)),
            'has_condition': bool(re.search(r'\b(if|else|elif|switch)\b', content)),
            'has_async': bool(re.search(r'\basync\s+def\b', content)),
            'has_class': chunk_type == 'class',
            'has_import': bool(re.search(r'\b(import|from|require|include)\b', content)),
        }

        return structure

    def find_similar(
        self,
        chunk: Dict,
        top_k: int = 3,
        exclude_self: bool = True
    ) -> List[Dict]:
        target_structure = self._extract_structure(chunk)
        target_id = chunk.get('chunk_id', '')

        similarities = []
        for chunk_id, structure in self.structure_cache.items():
            if exclude_self and chunk_id == target_id:
                continue

            similarity = self._compute_similarity(target_structure, structure)
            if similarity > 0.3:
                for c in self.metadata:
                    if c.get('chunk_id', '') == chunk_id:
                        similarities.append({
                            'chunk': c,
                            'similarity': similarity,
                            'reason': self._explain_similarity(target_structure, structure)
                        })
                        break

        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:top_k]

    def _compute_similarity(self, s1: Dict, s2: Dict) -> float:
        score = 0.0
        weights = {
            'type': 0.2,
            'num_symbols': 0.1,
            'symbol_types': 0.15,
            'has_return': 0.05,
            'has_loop': 0.1,
            'has_condition': 0.1,
            'has_async': 0.1,
            'has_class': 0.1,
            'has_import': 0.1,
        }

        if s1.get('type') == s2.get('type'):
            score += weights['type']

        num_diff = abs(s1.get('num_symbols', 0) - s2.get('num_symbols', 0))
        if num_diff <= 2:
            score += weights['num_symbols'] * (1 - num_diff / 3)

        types1 = set(s1.get('symbol_types', []))
        types2 = set(s2.get('symbol_types', []))
        if types1 & types2:
            score += weights['symbol_types'] * len(types1 & types2) / max(len(types1 | types2), 1)

        for key in ['has_return', 'has_loop', 'has_condition', 'has_async', 'has_class', 'has_import']:
            if s1.get(key) == s2.get(key):
                score += weights.get(key, 0.05)

        return min(score, 1.0)

    def _explain_similarity(self, s1: Dict, s2: Dict) -> str:
        reasons = []

        if s1.get('type') == s2.get('type'):
            reasons.append(f"both are {s1['type']}")

        types1 = set(s1.get('symbol_types', []))
        types2 = set(s2.get('symbol_types', []))
        common_types = types1 & types2
        if common_types:
            reasons.append(f"share {', '.join(common_types)}")

        if s1.get('has_loop') and s2.get('has_loop'):
            reasons.append("both contain loops")

        if s1.get('has_condition') and s2.get('has_condition'):
            reasons.append("both have conditional logic")

        if s1.get('has_async') and s2.get('has_async'):
            reasons.append("both are async")

        return "; ".join(reasons) if reasons else "similar structure"


class UsageExampleFinder:
    def __init__(self, metadata: List[Dict] = None):
        self.metadata = metadata or []

    def find_usages(self, symbol_name: str, file_path: str = None) -> List[Dict]:
        usages = []

        for chunk in self.metadata:
            content = chunk.get('content', '')
            fp = chunk.get('file_path', '')
            chunk_symbols = chunk.get('symbols', [])

            if file_path and fp != file_path:
                continue

            chunk_name = next((s['name'] for s in chunk_symbols if s['name'] == symbol_name), None)
            if chunk_name:
                continue

            if f"({symbol_name}" in content or f".{symbol_name}(" in content:
                usages.append({
                    'file': fp,
                    'start_line': chunk.get('start_line', 0),
                    'content': content[:500],
                    'type': 'call'
                })

        return usages[:5]
