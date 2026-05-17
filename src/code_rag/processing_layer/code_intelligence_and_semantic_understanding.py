"""
代码智能理解与语义分析模块
支持代码意图识别、标签生成、代码分类等高级功能
"""

import re
from typing import List, Dict, Optional, Set
from enum import Enum
from dataclasses import dataclass
from collections import Counter


class CodeIntent(Enum):
    """代码意图类型"""
    DATA_PROCESSING = "data_processing"
    BUSINESS_LOGIC = "business_logic"
    USER_INTERFACE = "user_interface"
    NETWORK_OPERATION = "network_operation"
    DATABASE_OPERATION = "database_operation"
    SECURITY = "security"
    UTILITY = "utility"
    CONFIGURATION = "configuration"
    TEST = "test"
    ERROR_HANDLING = "error_handling"
    INITIALIZATION = "initialization"
    VALIDATION = "validation"
    CACHING = "caching"
    LOGGING = "logging"
    ASYNC_OPERATION = "async_operation"


@dataclass
class CodeTag:
    """代码标签"""
    name: str
    category: str
    confidence: float
    keywords: List[str]


@dataclass
class CodeIntentResult:
    """代码意图识别结果"""
    primary_intent: CodeIntent
    secondary_intents: List[CodeIntent]
    confidence: float
    reasoning: str


@dataclass
class CodeSummary:
    """代码摘要"""
    short_summary: str
    long_summary: str
    key_operations: List[str]
    input_types: List[str]
    output_types: List[str]


class CodeIntelligenceAnalyzer:
    """
    代码智能分析器
    理解代码语义，识别意图，生成标签
    """

    # 意图识别关键词
    INTENT_KEYWORDS = {
        CodeIntent.DATA_PROCESSING: [
            'parse', 'transform', 'convert', 'format', 'serialize', 
            'deserialize', 'encode', 'decode', 'map', 'filter', 'reduce'
        ],
        CodeIntent.BUSINESS_LOGIC: [
            'calculate', 'compute', 'process', 'handle', 'manage', 
            'execute', 'perform', 'workflow', 'validate', 'check'
        ],
        CodeIntent.USER_INTERFACE: [
            'render', 'display', 'show', 'hide', 'click', 'input',
            'output', 'draw', 'layout', 'view', 'template', 'html'
        ],
        CodeIntent.NETWORK_OPERATION: [
            'request', 'response', 'http', 'fetch', 'send', 'receive',
            'connect', 'socket', 'api', 'endpoint', 'client', 'server'
        ],
        CodeIntent.DATABASE_OPERATION: [
            'query', 'insert', 'update', 'delete', 'select', 'fetch',
            'save', 'load', 'table', 'index', 'transaction', 'sql'
        ],
        CodeIntent.SECURITY: [
            'authenticate', 'authorize', 'encrypt', 'decrypt', 'hash',
            'sign', 'verify', 'permission', 'access', 'token', 'secret'
        ],
        CodeIntent.UTILITY: [
            'util', 'helper', 'tool', 'format', 'parse', 'convert',
            'validate', 'normalize', 'escape', 'sanitize'
        ],
        CodeIntent.CONFIGURATION: [
            'config', 'settings', 'option', 'parameter', 'env', 'variable',
            'initialize', 'setup', 'default'
        ],
        CodeIntent.TEST: [
            'test', 'mock', 'assert', 'expect', 'verify', 'fixture',
            'case', 'suite', 'benchmark'
        ],
        CodeIntent.ERROR_HANDLING: [
            'try', 'catch', 'except', 'raise', 'error', 'exception',
            'fail', 'handle', 'retry', 'fallback'
        ],
        CodeIntent.INITIALIZATION: [
            'init', 'create', 'new', 'instantiate', 'setup', 'load',
            'register', 'bind', 'inject'
        ],
        CodeIntent.VALIDATION: [
            'validate', 'check', 'verify', 'ensure', 'is_valid',
            'assert', 'require', 'guard', 'schema'
        ],
        CodeIntent.CACHING: [
            'cache', 'memoize', 'store', 'get', 'set', 'invalidate',
            'evict', 'ttl', 'expire'
        ],
        CodeIntent.LOGGING: [
            'log', 'debug', 'info', 'warn', 'error', 'trace',
            'metric', 'monitor', 'report'
        ],
        CodeIntent.ASYNC_OPERATION: [
            'async', 'await', 'promise', 'callback', 'event',
            'stream', 'queue', 'worker', 'background'
        ]
    }

    # 编程语言特征
    LANGUAGE_PATTERNS = {
        'python': [r'def\s+\w+', r'class\s+\w+', r'import\s+\w+', r'from\s+\w+\s+import'],
        'javascript': [r'function\s+\w+', r'const\s+\w+\s*=', r'=>', r'export\s+'],
        'typescript': [r':\s*(string|number|boolean|any)\b', r'interface\s+\w+', r'type\s+\w+\s*='],
        'java': [r'public\s+(class|interface|enum)', r'private\s+\w+', r'System\.out\.'],
        'go': [r'func\s+\w+', r'package\s+\w+', r'import\s+\(',],
        'rust': [r'fn\s+\w+', r'let\s+mut', r'impl\s+\w+', r'use\s+\w+::']
    }

    def __init__(self):
        self.tag_cache: Dict[str, List[CodeTag]] = {}

    def analyze_intent(self, code: str) -> CodeIntentResult:
        """分析代码意图"""
        code_lower = code.lower()
        words = set(re.findall(r'\w+', code_lower))
        
        intent_scores = {}
        
        for intent, keywords in self.INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in words)
            if score > 0:
                intent_scores[intent] = score
        
        if not intent_scores:
            return CodeIntentResult(
                primary_intent=CodeIntent.UTILITY,
                secondary_intents=[],
                confidence=0.3,
                reasoning="未识别到特定意图，归类为工具函数"
            )
        
        sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)
        
        primary = sorted_intents[0][0]
        max_score = sorted_intents[0][1]
        confidence = min(max_score / 5.0, 1.0)
        
        secondary = [i[0] for i in sorted_intents[1:3]]
        
        return CodeIntentResult(
            primary_intent=primary,
            secondary_intents=secondary,
            confidence=confidence,
            reasoning=f"识别到 {len(intent_scores)} 种意图，主要为 {primary.value}"
        )

    def generate_tags(self, code: str, language: str = 'python') -> List[CodeTag]:
        """为代码生成标签"""
        cache_key = f"{hash(code)}:{language}"
        if cache_key in self.tag_cache:
            return self.tag_cache[cache_key]
        
        tags = []
        
        intent_result = self.analyze_intent(code)
        tags.append(CodeTag(
            name=intent_result.primary_intent.value,
            category="intent",
            confidence=intent_result.confidence,
            keywords=[]
        ))
        
        for keyword_list in self.INTENT_KEYWORDS.values():
            for kw in keyword_list:
                if kw in code.lower():
                    tag_name = kw.replace('_', ' ')
                    if not any(t.name == tag_name for t in tags):
                        tags.append(CodeTag(
                            name=tag_name,
                            category="keyword",
                            confidence=0.8,
                            keywords=[kw]
                        ))
        
        for pattern in self.LANGUAGE_PATTERNS.get(language, []):
            if re.search(pattern, code):
                tags.append(CodeTag(
                    name=language,
                    category="language",
                    confidence=0.9,
                    keywords=[]
                ))
                break
        
        func_names = re.findall(r'(?:def|function|func)\s+(\w+)', code)
        for name in func_names[:3]:
            tags.append(CodeTag(
                name=f"function:{name}",
                category="function",
                confidence=1.0,
                keywords=[name]
            ))
        
        class_names = re.findall(r'class\s+(\w+)', code)
        for name in class_names[:2]:
            tags.append(CodeTag(
                name=f"class:{name}",
                category="class",
                confidence=1.0,
                keywords=[name]
            ))
        
        import_patterns = [
            r'from\s+([\w.]+)\s+import',
            r'import\s+([\w.]+)',
            r'require\s*\(\s*[\'"]([^\'"]+)[\'"]'
        ]
        for pattern in import_patterns:
            matches = re.findall(pattern, code)
            for match in matches[:5]:
                if isinstance(match, tuple):
                    module = match[0].split('.')[0]
                else:
                    module = match.split('.')[0]
                tags.append(CodeTag(
                    name=f"dependency:{module}",
                    category="dependency",
                    confidence=0.9,
                    keywords=[module]
                ))
        
        self.tag_cache[cache_key] = tags
        return tags

    def detect_language(self, code: str) -> str:
        """检测代码语言"""
        scores = {}
        
        for lang, patterns in self.LANGUAGE_PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, code))
                score += matches
            if score > 0:
                scores[lang] = score
        
        if not scores:
            return 'unknown'
        
        return max(scores.items(), key=lambda x: x[1])[0]

    def extract_code_structure(self, code: str, language: str = 'python') -> Dict:
        """提取代码结构信息"""
        structure = {
            'functions': [],
            'classes': [],
            'imports': [],
            'complexity': 0,
            'lines_of_code': len(code.split('\n'))
        }
        
        if language == 'python':
            structure['functions'] = re.findall(r'def\s+(\w+)\s*\([^)]*\)\s*(?:->\s*\w+\s*)?:', code)
            structure['classes'] = re.findall(r'class\s+(\w+)(?:\([^)]*\))?\s*:', code)
            structure['imports'] = (
                re.findall(r'from\s+([\w.]+)\s+import', code) +
                re.findall(r'import\s+([\w.]+)', code)
            )
        elif language in ['javascript', 'typescript']:
            structure['functions'] = (
                re.findall(r'function\s+(\w+)\s*\(', code) +
                re.findall(r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>', code)
            )
            structure['classes'] = re.findall(r'class\s+(\w+)', code)
            structure['imports'] = re.findall(r'(?:import|from)\s+[\'"]([^\'"]+)[\'"]', code)
        
        complexity_indicators = [
            r'\bif\b.*\belse\b',
            r'\bfor\b.*\bfor\b',
            r'\bwhile\b',
            r'\btry\b.*\bexcept\b',
            r'\bexcept\b.*\bexcept\b'
        ]
        
        for pattern in complexity_indicators:
            structure['complexity'] += len(re.findall(pattern, code))
        
        return structure

    def generate_summary(self, code: str, language: str = 'python') -> CodeSummary:
        """生成代码摘要"""
        structure = self.extract_code_structure(code, language)
        intent_result = self.analyze_intent(code)
        
        func_names = structure['functions']
        class_names = structure['classes']
        
        if func_names:
            short_summary = f"包含 {len(func_names)} 个函数"
            if class_names:
                short_summary += f"，{len(class_names)} 个类"
        elif class_names:
            short_summary = f"包含 {len(class_names)} 个类"
        else:
            short_summary = "代码片段"
        
        operations = []
        for keyword_list in self.INTENT_KEYWORDS.values():
            for kw in keyword_list:
                if kw in code.lower():
                    operations.append(kw)
        
        operation_counts = Counter(operations)
        top_operations = [op for op, count in operation_counts.most_common(5)]
        
        return CodeSummary(
            short_summary=short_summary,
            long_summary=f"这是一个{intent_result.primary_intent.value.replace('_', ' ')}相关的代码，主要用于{intent_result.reasoning}",
            key_operations=top_operations,
            input_types=self._infer_types(code, 'input'),
            output_types=self._infer_types(code, 'output')
        )

    def _infer_types(self, code: str, direction: str = 'input') -> List[str]:
        """推断输入/输出类型"""
        types = []
        
        type_patterns = [
            (r'\b(str|string|Text)\b', 'string'),
            (r'\b(int|float|number|Numeric)\b', 'numeric'),
            (r'\b(bool|Boolean)\b', 'boolean'),
            (r'\b(list|array|Array)\b', 'array'),
            (r'\b(dict|object|Map|Object)\b', 'object'),
            (r'\b(file|File)\b', 'file'),
        ]
        
        for pattern, type_name in type_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                types.append(type_name)
        
        return list(set(types))


class CodeSimilarityAnalyzer:
    """代码相似度分析器"""

    def calculate_structural_similarity(self, code1: str, code2: str) -> float:
        """计算结构相似度"""
        try:
            analyzer1 = CodeIntelligenceAnalyzer()
            analyzer2 = CodeIntelligenceAnalyzer()
            
            struct1 = analyzer1.extract_code_structure(code1)
            struct2 = analyzer2.extract_code_structure(code2)
            
            func_sim = len(set(struct1['functions']) & set(struct2['functions'])) / max(len(set(struct1['functions']) | set(struct2['functions'])), 1)
            class_sim = len(set(struct1['classes']) & set(struct2['classes'])) / max(len(set(struct1['classes']) | set(struct2['classes'])), 1)
            
            return (func_sim * 0.6 + class_sim * 0.4)
        except:
            return 0.0

    def calculate_semantic_similarity(self, code1: str, code2: str) -> float:
        """计算语义相似度"""
        try:
            analyzer = CodeIntelligenceAnalyzer()
            
            tags1 = set(t.name for t in analyzer.generate_tags(code1))
            tags2 = set(t.name for t in analyzer.generate_tags(code2))
            
            if not tags1 or not tags2:
                return 0.0
            
            intersection = len(tags1 & tags2)
            union = len(tags1 | tags2)
            
            return intersection / union if union > 0 else 0.0
        except:
            return 0.0

    def calculate_lexical_similarity(self, code1: str, code2: str) -> float:
        """计算词汇相似度"""
        try:
            words1 = set(re.findall(r'\w+', code1.lower()))
            words2 = set(re.findall(r'\w+', code2.lower()))
            
            keywords_to_ignore = {
                'def', 'class', 'import', 'from', 'return', 'if', 'else',
                'for', 'while', 'try', 'except', 'finally', 'with', 'as',
                'in', 'out', 'the', 'a', 'an', 'and', 'or', 'not', 'is',
                'function', 'var', 'let', 'const', 'async', 'await'
            }
            
            words1 = words1 - keywords_to_ignore
            words2 = words2 - keywords_to_ignore
            
            if not words1 or not words2:
                return 0.0
            
            intersection = len(words1 & words2)
            union = len(words1 | words2)
            
            return intersection / union if union > 0 else 0.0
        except:
            return 0.0

    def calculate_overall_similarity(self, code1: str, code2: str) -> Dict[str, float]:
        """计算综合相似度"""
        structural = self.calculate_structural_similarity(code1, code2)
        semantic = self.calculate_semantic_similarity(code1, code2)
        lexical = self.calculate_lexical_similarity(code1, code2)
        
        weights = {
            'structural': 0.3,
            'semantic': 0.4,
            'lexical': 0.3
        }
        
        overall = (
            structural * weights['structural'] +
            semantic * weights['semantic'] +
            lexical * weights['lexical']
        )
        
        return {
            'structural': structural,
            'semantic': semantic,
            'lexical': lexical,
            'overall': overall
        }


def analyze_code_intelligence(code: str, language: str = 'python') -> Dict:
    """便捷函数：对代码进行智能分析"""
    analyzer = CodeIntelligenceAnalyzer()
    
    intent = analyzer.analyze_intent(code)
    tags = analyzer.generate_tags(code, language)
    structure = analyzer.extract_code_structure(code, language)
    summary = analyzer.generate_summary(code, language)
    
    return {
        'intent': {
            'primary': intent.primary_intent.value,
            'secondary': [i.value for i in intent.secondary_intents],
            'confidence': intent.confidence,
            'reasoning': intent.reasoning
        },
        'tags': [
            {'name': t.name, 'category': t.category, 'confidence': t.confidence}
            for t in tags
        ],
        'structure': structure,
        'summary': {
            'short': summary.short_summary,
            'long': summary.long_summary,
            'key_operations': summary.key_operations,
            'input_types': summary.input_types,
            'output_types': summary.output_types
        },
        'detected_language': analyzer.detect_language(code)
    }
