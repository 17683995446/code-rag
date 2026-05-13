import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from stage2.types import QueryIntent, RetrievalType


class QueryParser:
    def __init__(self):
        self.line_pattern = re.compile(r'[:.](\d+)(?:[-~:](\d+))?')
        self.file_pattern = re.compile(r'(?:in|file|from)\s+([^\s]+(?:\.[a-zA-Z]+)?)')
        self.symbol_pattern = re.compile(r'(?:function|method|class|def)\s+(\w+)', re.IGNORECASE)
        self.language_pattern = re.compile(r'(?:lang|language)\s*[:=]\s*(\w+)', re.IGNORECASE)

        self.intent_keywords = {
            'exact': ['line', 'exact', 'precise', 'exact match'],
            'semantic': ['what', 'how', 'why', 'explain', 'understanding', 'find'],
            'structural': ['call', 'import', 'use', 'related', 'parent', 'child'],
            'call_graph': ['caller', 'callee', 'called by', 'who calls', 'dependencies'],
        }

    def parse(self, query: str) -> QueryIntent:
        intent = QueryIntent(query=query)
        query_lower = query.lower()

        intent.keywords = self._extract_keywords(query)
        intent.entities = self._extract_entities(query)

        line_match = self.line_pattern.search(query)
        if line_match:
            start = int(line_match.group(1))
            end = int(line_match.group(2)) if line_match.group(2) else start
            intent.line_number = start
            intent.intent_type = "exact"

        file_match = self.file_pattern.search(query)
        if file_match:
            intent.target_file = file_match.group(1)

        symbol_match = self.symbol_pattern.search(query)
        if symbol_match:
            intent.target_symbol = symbol_match.group(1)

        lang_match = self.language_pattern.search(query)
        if lang_match:
            intent.target_language = lang_match.group(1)

        if not intent.intent_type or intent.intent_type == "general":
            intent.intent_type = self._infer_intent_type(query_lower)

        return intent

    def _extract_keywords(self, query: str) -> List[str]:
        stop_words = {
            'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
            'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as',
            'into', 'through', 'during', 'before', 'after', 'above', 'below',
            'between', 'under', 'again', 'further', 'then', 'once', 'here',
            'there', 'when', 'where', 'why', 'how', 'all', 'each', 'few',
            'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
            'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just',
            'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while',
            'find', 'get', 'look', 'show', 'search', 'locate', 'see', 'know'
        }

        words = re.findall(r'\b[a-zA-Z_]\w*\b', query.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        return list(set(keywords))

    def _extract_entities(self, query: str) -> List[str]:
        entities = []
        camel_case = re.findall(r'[A-Z][a-z]+(?:[A-Z][a-z]+)+', query)
        entities.extend(camel_case)

        snake_case = re.findall(r'[a-z]+_[a-z]+', query)
        entities.extend([e for e in snake_case if '_' in e])

        file_refs = re.findall(r'[\w/]+\.[a-zA-Z]+', query)
        entities.extend(file_refs)

        return list(set(entities))

    def _infer_intent_type(self, query_lower: str) -> str:
        for intent_type, keywords in self.intent_keywords.items():
            if any(kw in query_lower for kw in keywords):
                return intent_type
        return "semantic"


class ExactLineSearcher:
    def __init__(self, metadata: List[Dict]):
        self.metadata = metadata
        self.file_index = self._build_file_index()
        self.line_index = self._build_line_index()

    def _build_file_index(self) -> Dict[str, List[int]]:
        file_index = {}
        for i, chunk in enumerate(self.metadata):
            fp = chunk.get('file_path', '')
            if fp not in file_index:
                file_index[fp] = []
            file_index[fp].append(i)
        return file_index

    def _build_line_index(self) -> Dict[str, Dict[int, int]]:
        line_index = {}
        for i, chunk in enumerate(self.metadata):
            fp = chunk.get('file_path', '')
            start = chunk.get('start_line', 0)
            end = chunk.get('end_line', start)
            if fp not in line_index:
                line_index[fp] = {}
            for line in range(start, end + 1):
                line_index[fp][line] = i
        return line_index

    def search_by_file_line(
        self,
        file_path: str,
        line: Optional[int] = None,
        range_: Optional[Tuple[int, int]] = None,
        top_k: int = 5
    ) -> List[Dict]:
        if line is not None:
            return self._search_single_line(file_path, line, top_k)
        elif range_ is not None:
            return self._search_line_range(file_path, range_[0], range_[1], top_k)
        else:
            return self._search_all_in_file(file_path, top_k)

    def _search_single_line(self, file_path: str, line: int, top_k: int) -> List[Dict]:
        fp = self._normalize_path(file_path)
        if fp in self.line_index and line in self.line_index[fp]:
            idx = self.line_index[fp][line]
            return [self.metadata[idx]]
        return []

    def _search_line_range(self, file_path: str, start: int, end: int, top_k: int) -> List[Dict]:
        fp = self._normalize_path(file_path)
        if fp not in self.line_index:
            return []

        matching_indices = set()
        for line in range(start, end + 1):
            if line in self.line_index[fp]:
                matching_indices.add(self.line_index[fp][line])

        results = [self.metadata[i] for i in matching_indices][:top_k]
        return results

    def _search_all_in_file(self, file_path: str, top_k: int) -> List[Dict]:
        fp = self._normalize_path(file_path)
        if fp in self.file_index:
            return [self.metadata[i] for i in self.file_index[fp][:top_k]]
        return []

    def _normalize_path(self, path: str) -> str:
        if path in self.file_index or path in self.line_index:
            return path
        return str(Path(path).resolve())


class KeywordSearcher:
    def __init__(self, metadata: List[Dict]):
        self.metadata = metadata

    def search(
        self,
        keywords: List[str],
        match_all: bool = False,
        top_k: int = 10
    ) -> List[Tuple[Dict, float]]:
        if not keywords:
            return []

        scores = {}
        for i, chunk in enumerate(self.metadata):
            content = chunk.get('content', '').lower()
            symbols = chunk.get('symbols', [])

            score = 0
            matched_keywords = 0

            for kw in keywords:
                kw_lower = kw.lower()

                if kw_lower in content:
                    count = content.count(kw_lower)
                    score += count * 1.0
                    matched_keywords += 1

                for sym in symbols:
                    sym_name = sym.get('name', '').lower()
                    if kw_lower in sym_name:
                        score += 5.0
                        matched_keywords += 1

            if matched_keywords > 0:
                if match_all and matched_keywords < len(keywords):
                    continue
                scores[i] = score

        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [(self.metadata[i], score) for i, score in sorted_results]


class SymbolSearcher:
    def __init__(self, metadata: List[Dict]):
        self.metadata = metadata
        self.symbol_index = self._build_symbol_index()

    def _build_symbol_index(self) -> Dict[str, List[int]]:
        symbol_index = {}
        for i, chunk in enumerate(self.metadata):
            for sym in chunk.get('symbols', []):
                name = sym.get('name', '')
                if name:
                    if name not in symbol_index:
                        symbol_index[name] = []
                    symbol_index[name].append(i)

                    name_lower = name.lower()
                    if name_lower not in symbol_index:
                        symbol_index[name_lower] = []
                    symbol_index[name_lower].append(i)
        return symbol_index

    def search_by_name(self, name: str, exact: bool = False, top_k: int = 5) -> List[Dict]:
        results = []
        seen = set()

        if exact:
            if name in self.symbol_index:
                for idx in self.symbol_index[name]:
                    if idx not in seen:
                        results.append(self.metadata[idx])
                        seen.add(idx)
        else:
            name_lower = name.lower()
            for sym_name, indices in self.symbol_index.items():
                if name_lower in sym_name.lower():
                    for idx in indices:
                        if idx not in seen:
                            results.append(self.metadata[idx])
                            seen.add(idx)

        return results[:top_k]

    def search_by_pattern(self, pattern: str, top_k: int = 5) -> List[Dict]:
        import re
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error:
            return []

        results = []
        seen = set()

        for i, chunk in enumerate(self.metadata):
            if i in seen:
                continue

            for sym in chunk.get('symbols', []):
                name = sym.get('name', '')
                if regex.search(name):
                    results.append(chunk)
                    seen.add(i)
                    break

        return results[:top_k]
