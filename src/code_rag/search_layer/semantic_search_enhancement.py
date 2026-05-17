"""
语义搜索增强模块
支持代码相似度搜索、自然语言查询、语义匹配等高级搜索功能
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class QueryType(Enum):
    """查询类型"""
    KEYWORD = "keyword"  # 关键词查询
    SEMANTIC = "semantic"  # 语义查询
    SIMILARITY = "similarity"  # 相似度查询
    NATURAL_LANGUAGE = "natural_language"  # 自然语言查询
    CODE_PATTERN = "code_pattern"  # 代码模式查询


@dataclass
class SearchQuery:
    """搜索查询"""
    original: str
    query_type: QueryType
    tokens: List[str]
    expanded_queries: List[str]
    intent: Optional[str] = None
    language: Optional[str] = None


@dataclass
class SearchResult:
    """搜索结果"""
    text: str
    score: float
    result_type: str
    relevance_factors: Dict
    highlights: List[str]


class SemanticSearchEnhancer:
    """
    语义搜索增强器
    将查询转换为语义表示，支持多种搜索模式
    """

    # 自然语言到代码的转换模式
    NL_TO_CODE_PATTERNS = {
        'find': ['search', 'query', 'filter', 'select', 'get'],
        'create': ['add', 'insert', 'new', 'make', 'generate'],
        'update': ['modify', 'edit', 'change', 'set', 'put'],
        'delete': ['remove', 'drop', 'erase', 'clear'],
        'validate': ['check', 'verify', 'ensure', 'test', 'assert'],
        'authenticate': ['login', 'sign_in', 'verify_identity'],
        'transform': ['convert', 'parse', 'format', 'encode', 'decode'],
        'calculate': ['compute', 'math', 'formula', 'sum', 'count'],
        'fetch': ['retrieve', 'load', 'read', 'pull', 'get'],
        'save': ['store', 'write', 'persist', 'commit', 'push'],
    }

    # 意图关键词
    INTENT_PATTERNS = {
        'implementation': ['how to', 'implement', 'example', 'code'],
        'explanation': ['what is', 'explain', 'understand', 'how does'],
        'comparison': ['compare', 'difference', 'vs', 'versus', 'better'],
        'troubleshooting': ['fix', 'error', 'bug', 'issue', 'problem'],
        'optimization': ['performance', 'optimize', 'fast', 'efficient'],
    }

    def __init__(self):
        self.query_cache: Dict[str, SearchQuery] = {}

    def analyze_query(self, query: str) -> SearchQuery:
        """
        分析查询类型和意图
        
        Args:
            query: 用户查询
            
        Returns:
            解析后的搜索查询
        """
        query_lower = query.lower()
        tokens = self._tokenize(query_lower)
        
        query_type = self._detect_query_type(query_lower, tokens)
        
        expanded_queries = self._expand_query(query_lower, query_type)
        
        intent = self._detect_intent(query_lower)
        
        language = self._detect_language(query_lower)
        
        return SearchQuery(
            original=query,
            query_type=query_type,
            tokens=tokens,
            expanded_queries=expanded_queries,
            intent=intent,
            language=language
        )

    def _tokenize(self, text: str) -> List[str]:
        """分词"""
        tokens = re.findall(r'\w+', text.lower())
        return [t for t in tokens if len(t) > 1]

    def _detect_query_type(self, query: str, tokens: List[str]) -> QueryType:
        """检测查询类型"""
        if any(word in query for word in ['how to', 'what is', 'why', 'when']):
            return QueryType.NATURAL_LANGUAGE
        
        if any(word in query for word in ['similar', 'like', 'same as', 'copy of']):
            return QueryType.SIMILARITY
        
        if any(word in query for word in ['function', 'class', 'def ', 'import']):
            return QueryType.CODE_PATTERN
        
        code_keywords = {'def', 'class', 'import', 'return', 'if', 'for', 'while'}
        if any(token in code_keywords for token in tokens):
            return QueryType.SEMANTIC
        
        return QueryType.KEYWORD

    def _expand_query(self, query: str, query_type: QueryType) -> List[str]:
        """扩展查询，生成多个搜索变体"""
        expanded = [query]
        
        if query_type == QueryType.NATURAL_LANGUAGE:
            expanded.extend(self._nl_to_code_variants(query))
        
        if query_type == QueryType.SIMILARITY:
            expanded.append(self._remove_similarity_keywords(query))
        
        expanded.extend(self._add_synonyms(query))
        
        return list(set(expanded))[:5]

    def _nl_to_code_variants(self, query: str) -> List[str]:
        """自然语言查询转换为代码相关查询"""
        variants = []
        query_lower = query.lower()
        
        for action, keywords in self.NL_TO_CODE_PATTERNS.items():
            if any(kw in query_lower for kw in keywords):
                variants.append(f"{action} code")
                variants.append(f"{action} implementation")
                variants.append(f"{action} function")
        
        return variants

    def _remove_similarity_keywords(self, query: str) -> str:
        """移除相似度关键词"""
        keywords_to_remove = ['similar', 'like', 'same as', 'copy of', 'resemble']
        result = query
        for kw in keywords_to_remove:
            result = result.replace(kw, '')
        return result.strip()

    def _add_synonyms(self, query: str) -> List[str]:
        """添加同义词"""
        synonyms = {
            'function': ['method', 'procedure', 'routine'],
            'class': ['object', 'type', 'entity'],
            'variable': ['var', 'parameter', 'argument'],
            'return': ['give back', 'output', 'result'],
            'create': ['make', 'generate', 'produce'],
        }
        
        variants = []
        query_tokens = set(self._tokenize(query))
        
        for word, syns in synonyms.items():
            if word in query_tokens:
                for syn in syns:
                    variant = query.replace(word, syn)
                    if variant != query:
                        variants.append(variant)
        
        return variants

    def _detect_intent(self, query: str) -> Optional[str]:
        """检测查询意图"""
        for intent, patterns in self.INTENT_PATTERNS.items():
            if any(pattern in query for pattern in patterns):
                return intent
        return None

    def _detect_language(self, query: str) -> Optional[str]:
        """检测查询中的编程语言"""
        languages = {
            'python': ['python', 'py', 'django', 'flask', 'pandas'],
            'javascript': ['javascript', 'js', 'node', 'react', 'vue', 'angular'],
            'java': ['java', 'spring', 'maven', 'gradle'],
            'go': ['golang', 'go ', ' go,'],
            'rust': ['rust', 'cargo'],
            'typescript': ['typescript', 'ts'],
            'c++': ['c++', 'cpp', 'cplusplus'],
            'csharp': ['c#', 'csharp', '.net'],
        }
        
        for lang, keywords in languages.items():
            if any(kw in query for kw in keywords):
                return lang
        
        return None

    def generate_search_queries(self, query: str, num_variants: int = 5) -> List[str]:
        """
        生成多个搜索查询变体
        
        Args:
            query: 原始查询
            num_variants: 生成的变体数量
            
        Returns:
            搜索查询列表
        """
        search_query = self.analyze_query(query)
        queries = search_query.expanded_queries.copy()
        
        if len(queries) < num_variants:
            queries.append(query)
        
        if search_query.language:
            lang_specific = f"{query} {search_query.language}"
            queries.append(lang_specific)
        
        return queries[:num_variants]


class CodePatternMatcher:
    """
    代码模式匹配器
    识别代码模式并生成对应的正则表达式
    """

    PATTERNS = {
        'function_definition': {
            'python': r'def\s+\w+\s*\([^)]*\)\s*(?:->\s*\w+)?\s*:',
            'javascript': r'function\s+\w+\s*\([^)]*\)\s*\{',
            'java': r'(?:public|private|protected)?\s*(?:static)?\s*\w+\s+\w+\s*\([^)]*\)\s*\{',
        },
        'class_definition': {
            'python': r'class\s+\w+(?:\([^)]*\))?\s*:',
            'javascript': r'class\s+\w+(?:\s+extends\s+\w+)?\s*\{',
            'java': r'class\s+\w+(?:\s+extends\s+\w+)?(?:\s+implements\s+\w+)?\s*\{',
        },
        'import_statement': {
            'python': r'(?:from\s+[\w.]+\s+)?import\s+[\w.,\s]+',
            'javascript': r'(?:import|require)\s*(?:\{[^}]+\}|[\w*]+)\s*(?:from\s+)?[\'"]([^\'"]+)[\'"]?',
        },
        'decorator': {
            'python': r'@\w+(?:\([^)]*\))?',
            'javascript': r'@\w+',
        },
        'async_function': {
            'python': r'async\s+def\s+\w+',
            'javascript': r'async\s+(?:function\s+)?\w*\s*\([^)]*\)\s*\{',
        },
    }

    def match_pattern(self, code: str, pattern_name: str, language: str = 'python') -> List[Dict]:
        """
        匹配代码模式
        
        Args:
            code: 代码文本
            pattern_name: 模式名称
            language: 编程语言
            
        Returns:
            匹配结果列表
        """
        if pattern_name not in self.PATTERNS:
            return []
        
        pattern = self.PATTERNS[pattern_name].get(language)
        if not pattern:
            return []
        
        matches = []
        for match in re.finditer(pattern, code, re.MULTILINE):
            start = match.start()
            end = match.end()
            
            lines = code[:start].count('\n') + 1
            line_end = lines + code[start:end].count('\n')
            
            matches.append({
                'pattern': pattern_name,
                'match': match.group(0),
                'start': start,
                'end': end,
                'line_start': lines,
                'line_end': line_end,
                'context': self._extract_context(code, start, end)
            })
        
        return matches

    def _extract_context(self, code: str, start: int, end: int, context_lines: int = 3) -> str:
        """提取匹配的上下文"""
        lines_before = code[:start].split('\n')[-context_lines:]
        lines_after = code[end:].split('\n')[:context_lines]
        
        return '\n'.join(['...'] if lines_before else []) + \
               '\n'.join(lines_before) + \
               code[start:end] + \
               '\n'.join(lines_after) + \
               '\n'.join(['...'] if lines_after else [])

    def find_all_patterns(self, code: str, language: str = 'python') -> Dict[str, List[Dict]]:
        """在代码中查找所有支持的模式"""
        results = {}
        
        for pattern_name in self.PATTERNS.keys():
            matches = self.match_pattern(code, pattern_name, language)
            if matches:
                results[pattern_name] = matches
        
        return results


class RelevanceRankingEngine:
    """
    相关性排序引擎
    根据多个维度对搜索结果进行排序
    """

    def __init__(self):
        self.weights = {
            'exact_match': 1.0,
            'keyword_match': 0.7,
            'semantic_match': 0.6,
            'recency': 0.1,
            'popularity': 0.2,
        }

    def calculate_relevance(
        self,
        query: SearchQuery,
        candidate: str,
        bm25_score: float = 0.0,
        semantic_score: float = 0.0,
        metadata: Optional[Dict] = None
    ) -> Tuple[float, Dict]:
        """
        计算查询与候选文档的相关性
        
        Args:
            query: 搜索查询
            candidate: 候选文档
            bm25_score: BM25分数
            semantic_score: 语义相似度分数
            metadata: 文档元数据
            
        Returns:
            (相关性分数, 分数详情)
        """
        factors = {}
        
        factors['bm25'] = bm25_score * self.weights['exact_match']
        
        if semantic_score > 0:
            factors['semantic'] = semantic_score * self.weights['semantic_match']
        else:
            factors['semantic'] = 0.0
        
        keyword_matches = self._count_keyword_matches(query.tokens, candidate)
        factors['keyword'] = (keyword_matches / len(query.tokens)) * self.weights['keyword_match'] if query.tokens else 0
        
        if metadata:
            if query.language and metadata.get('language') == query.language:
                factors['language_match'] = 0.3
            else:
                factors['language_match'] = 0.0
        else:
            factors['language_match'] = 0.0
        
        total_score = sum(factors.values())
        
        normalized_score = min(total_score, 1.0)
        
        return normalized_score, factors

    def _count_keyword_matches(self, tokens: List[str], text: str) -> int:
        """计算关键词匹配数"""
        text_lower = text.lower()
        matches = 0
        for token in tokens:
            if token in text_lower:
                matches += 1
        return matches

    def rerank_results(
        self,
        results: List[Dict],
        query: SearchQuery,
        diversity_weight: float = 0.1
    ) -> List[Dict]:
        """
        对搜索结果进行重排序
        
        Args:
            results: 初始搜索结果
            query: 搜索查询
            diversity_weight: 多样性权重
            
        Returns:
            重排序后的结果
        """
        for result in results:
            relevance, factors = self.calculate_relevance(
                query,
                result.get('text', ''),
                result.get('bm25_score', 0.0),
                result.get('semantic_score', 0.0),
                result.get('metadata')
            )
            result['relevance_score'] = relevance
            result['relevance_factors'] = factors
        
        sorted_results = sorted(results, key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return self._add_diversity(sorted_results, diversity_weight)

    def _add_diversity(self, results: List[Dict], weight: float) -> List[Dict]:
        """增加结果多样性"""
        if len(results) <= 1:
            return results
        
        seen_categories = set()
        diverse_results = []
        
        for result in results:
            category = result.get('metadata', {}).get('category', 'unknown')
            
            if category not in seen_categories or len(diverse_results) < 5:
                if category not in seen_categories:
                    seen_categories.add(category)
                    result['relevance_score'] += weight
            
            diverse_results.append(result)
        
        return sorted(diverse_results, key=lambda x: x.get('relevance_score', 0), reverse=True)


def enhance_search(query: str) -> Dict:
    """
    便捷函数：增强搜索查询
    
    Args:
        query: 用户查询
        
    Returns:
        增强后的查询信息
    """
    enhancer = SemanticSearchEnhancer()
    search_query = enhancer.analyze_query(query)
    
    return {
        'original': search_query.original,
        'type': search_query.query_type.value,
        'tokens': search_query.tokens,
        'expanded_queries': search_query.expanded_queries,
        'intent': search_query.intent,
        'language': search_query.language,
        'all_queries': enhancer.generate_search_queries(query)
    }
