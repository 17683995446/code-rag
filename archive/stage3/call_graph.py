import re
from typing import List, Dict, Optional, Set, Tuple, Any
from collections import defaultdict

from stage3.types import CallGraph, CallNode


class CallGraphAnalyzer:
    def __init__(self, metadata: List[Dict]):
        self.metadata = metadata
        self.symbol_map = self._build_symbol_map()
        self.call_graph = self._build_call_graph()
        self.import_graph = self._build_import_graph()

    def _build_symbol_map(self) -> Dict[str, List[Dict]]:
        symbol_map = defaultdict(list)

        for chunk in self.metadata:
            file_path = chunk.get('file_path', '')
            for symbol in chunk.get('symbols', []):
                symbol_key = self._make_symbol_key(symbol.get('name', ''), file_path)
                symbol_map[symbol_key].append({
                    'file_path': file_path,
                    'line': symbol.get('start', 0),
                    'type': symbol.get('type', ''),
                    'signature': symbol.get('signature', '')
                })

        return dict(symbol_map)

    def _build_call_graph(self) -> CallGraph:
        graph = CallGraph()
        pattern_map = self._get_call_patterns()

        for chunk in self.metadata:
            file_path = chunk.get('file_path', '')
            content = chunk.get('content', '')
            symbols = chunk.get('symbols', [])

            for symbol in symbols:
                symbol_name = symbol.get('name', '')
                symbol_type = symbol.get('type', '')
                line = symbol.get('start', 0)

                if symbol_type in ('function', 'method', 'constructor'):
                    calls = self._extract_calls(content, pattern_map, file_path)

                    node_key = f"{file_path}:{symbol_name}"
                    node = CallNode(
                        symbol_name=symbol_name,
                        file_path=file_path,
                        line_number=line,
                        symbol_type=symbol_type,
                        calls=calls
                    )
                    graph.nodes[node_key] = node

                    for called_symbol in calls:
                        edge = (node_key, called_symbol)
                        if edge not in graph.edges:
                            graph.edges.append(edge)

        self._update_called_by(graph)

        return graph

    def _build_import_graph(self) -> Dict[str, List[str]]:
        import_graph = defaultdict(list)

        for chunk in self.metadata:
            file_path = chunk.get('file_path', '')
            imports = chunk.get('imports', [])

            for imp in imports:
                if isinstance(imp, str):
                    import_graph[file_path].append(imp)

        return dict(import_graph)

    def _get_call_patterns(self) -> Dict[str, re.Pattern]:
        patterns = {
            'python': [
                r'(\w+)\s*\(',
                r'(\w+)\.\w+\s*\(',
            ],
            'javascript': [
                r'(\w+)\s*\(',
                r'this\.(\w+)\s*\(',
            ],
            'typescript': [
                r'(\w+)\s*\(',
                r'this\.(\w+)\s*\(',
            ],
        }
        compiled = {}
        for lang, pats in patterns.items():
            compiled[lang] = [re.compile(p) for p in pats]
        return compiled

    def _extract_calls(
        self,
        content: str,
        patterns: Dict[str, List[re.Pattern]],
        current_file: str
    ) -> List[str]:
        calls = []
        seen = set()

        for lang, lang_patterns in patterns.items():
            for pattern in lang_patterns:
                for match in pattern.finditer(content):
                    func_name = match.group(1)
                    if func_name and func_name not in seen:
                        if not self._is_builtin(func_name):
                            seen.add(func_name)
                            calls.append(func_name)

        return list(seen)[:20]

    def _is_builtin(self, name: str) -> bool:
        builtins = {
            'print', 'len', 'str', 'int', 'float', 'bool', 'list', 'dict',
            'set', 'tuple', 'range', 'enumerate', 'zip', 'map', 'filter',
            'sum', 'min', 'max', 'abs', 'round', 'sorted', 'reversed',
            'isinstance', 'hasattr', 'getattr', 'setattr', 'delattr',
            'open', 'read', 'write', 'close', 'input', 'format', 'repr',
            'console.log', 'Math', 'Array', 'Object', 'Promise', 'require',
            'module', 'exports', 'process', 'setTimeout', 'setInterval'
        }
        return name in builtins

    def _update_called_by(self, graph: CallGraph):
        for node_key, node in graph.nodes.items():
            for called in node.calls:
                for target_key, target_node in graph.nodes.items():
                    if self._symbol_matches(called, target_key):
                        if node_key not in target_node.called_by:
                            target_node.called_by.append(node_key)

    def _symbol_matches(self, call_name: str, symbol_key: str) -> bool:
        parts = symbol_key.rsplit(':', 1)
        if len(parts) == 2:
            _, symbol_name = parts
            return call_name == symbol_name
        return call_name in symbol_key

    def _make_symbol_key(self, name: str, file_path: str) -> str:
        return f"{file_path}:{name}"

    def get_callers(self, symbol_name: str, file_path: str = None, max_depth: int = 1) -> List[Dict]:
        results = []
        visited = set()

        def _search(target_name: str, depth: int, path: List[str]):
            if depth > max_depth:
                return

            for node_key, node in self.call_graph.nodes.items():
                if target_name in node.calls:
                    if node_key not in visited:
                        visited.add(node_key)
                        results.append({
                            'symbol': node.symbol_name,
                            'file': node.file_path,
                            'line': node.line_number,
                            'type': node.symbol_type,
                            'depth': depth,
                            'path': path + [node_key]
                        })
                        _search(node.symbol_name, depth + 1, path + [node_key])

        _search(symbol_name, 0, [])
        return results[:20]

    def get_callees(self, symbol_name: str, file_path: str = None, max_depth: int = 1) -> List[Dict]:
        start_key = None
        for node_key, node in self.call_graph.nodes.items():
            if node.symbol_name == symbol_name:
                if file_path is None or node.file_path == file_path:
                    start_key = node_key
                    break

        if not start_key:
            return []

        results = []
        visited = set()

        def _search(key: str, depth: int, path: List[str]):
            if depth > max_depth or key in visited:
                return

            visited.add(key)
            node = self.call_graph.nodes.get(key)
            if not node:
                return

            for called in node.calls:
                results.append({
                    'symbol': called,
                    'depth': depth,
                    'path': path + [called]
                })
                _search(called, depth + 1, path + [called])

        _search(start_key, 0, [symbol_name])
        return results[:20]

    def get_symbol_context(self, symbol_name: str, file_path: str = None) -> Dict:
        for node_key, node in self.call_graph.nodes.items():
            if node.symbol_name == symbol_name:
                if file_path is None or node.file_path == file_path:
                    return {
                        'symbol': node.symbol_name,
                        'file': node.file_path,
                        'line': node.line_number,
                        'type': node.symbol_type,
                        'calls': node.calls[:10],
                        'called_by': [
                            self.call_graph.nodes.get(k, CallNode('','',0,''))
                            for k in node.called_by[:5]
                        ],
                        'imports': node.imports
                    }

        return {}

    def build_call_chain(
        self,
        start_symbol: str,
        end_symbol: str,
        max_depth: int = 5
    ) -> List[List[str]]:
        paths = []

        def dfs(current: str, target: str, path: List[str], visited: Set[str]):
            if current == target:
                paths.append(path.copy())
                return

            if len(path) > max_depth:
                return

            for node_key, node in self.call_graph.nodes.items():
                if node.symbol_name == current and node_key not in visited:
                    for called in node.calls:
                        if called not in visited or called == target:
                            visited.add(node_key)
                            dfs(called, target, path + [called], visited)
                            visited.discard(node_key)

        dfs(start_symbol, end_symbol, [start_symbol], set())
        return sorted(paths, key=len)[:5]
